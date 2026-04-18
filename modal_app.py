from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import modal

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bench.config import ExperimentConfig, load_config
from bench.datasets import (
    load_alpaca_hf_prompts,
    load_jsonl_prompts,
    load_swebench_hf_prompts,
    load_terminalbench_hf_prompts,
    load_translation_hf_prompts,
    load_wildchat_hf_prompts,
    load_xsum_hf_prompts,
)
from bench.methods import MethodResources, get_benchmark_method
from bench.runner import run_generation_batches, write_result_bundle

APP_NAME = "llm-serving-bench"
HF_CACHE_DIR = "/cache/hf"
RESULTS_DIR = "/results"
TRANSFORMERS_LOCAL_DIR = ROOT / "transformers"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .pip_install(
        "accelerate>=1.10.0",
        "datasets>=4.4.0",
        "sentencepiece>=0.2.0",
        "torch>=2.8.0",
    )
    .add_local_dir(
        str(TRANSFORMERS_LOCAL_DIR),
        remote_path="/root/transformers",
        copy=True,
        ignore=[".git", "tests", "docs", "examples", "docker", "notebooks", "__pycache__"],
    )
    .run_commands("pip install /root/transformers")
    .add_local_dir(SRC, remote_path="/root/src")
)

app = modal.App(APP_NAME, image=image)

hf_cache_volume = modal.Volume.from_name(
    "llm-bench-hf-cache",
    create_if_missing=True,
    version=2,
)
results_volume = modal.Volume.from_name(
    "llm-bench-results",
    create_if_missing=True,
    version=2,
)

if modal.is_local() and os.environ.get("HF_TOKEN"):
    hf_secret = modal.Secret.from_dict({"HF_TOKEN": os.environ["HF_TOKEN"]})
else:
    hf_secret = modal.Secret.from_dict({})


def _resolve_prompt_path(prompt_path: str) -> Path:
    path = Path(prompt_path)
    if path.is_absolute():
        return path
    return ROOT / path


@app.cls(
    cpu=8,
    memory=32768,
    gpu="L40S",
    timeout=60 * 60,
    volumes={
        HF_CACHE_DIR: hf_cache_volume,
        RESULTS_DIR: results_volume,
    },
    secrets=[hf_secret],
)
class BenchmarkWorker:
    @modal.enter()
    def enter(self) -> None:
        self.container_started_at = time.perf_counter()
        self.loaded_key: tuple[str, str, str | None, str, str, bool, int] | None = None
        self.tokenizer = None
        self.model = None
        self.method_resources = MethodResources()

    def _ensure_models(self, config: ExperimentConfig) -> float:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        method = get_benchmark_method(config.method)
        load_key = (
            config.method,
            config.target_model,
            config.draft_model,
            config.torch_dtype,
            json.dumps(config.method_options, sort_keys=True),
            config.separate_assistant_gpu,
            torch.cuda.device_count(),
        )
        if self.loaded_key == load_key:
            return 0.0

        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }
        torch_dtype = dtype_map[config.torch_dtype]
        token = os.environ.get("HF_TOKEN") or None

        started = time.perf_counter()

        self.tokenizer = AutoTokenizer.from_pretrained(
            config.target_model,
            cache_dir=HF_CACHE_DIR,
            token=token,
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            config.target_model,
            cache_dir=HF_CACHE_DIR,
            token=token,
            dtype=torch_dtype,
            device_map=(
                {"": "cuda:0"}
                if config.separate_assistant_gpu and torch.cuda.device_count() >= 2
                else "auto"
            ),
        )
        self.model.eval()

        self.method_resources = method.prepare_resources(
            config,
            target_tokenizer=self.tokenizer,
            torch_dtype=torch_dtype,
            token=token,
            hf_cache_dir=HF_CACHE_DIR,
            auto_model_cls=AutoModelForCausalLM,
            auto_tokenizer_cls=AutoTokenizer,
            cuda_device_count=torch.cuda.device_count(),
        )

        self.loaded_key = load_key
        return time.perf_counter() - started

    @modal.method()
    def run_experiment(
        self,
        config_dict: dict[str, Any],
        prompts: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        config = ExperimentConfig.from_dict(config_dict)
        if prompts is None:
            prompts = self._load_prompts(config)
        model_load_seconds = self._ensure_models(config)
        run_started = time.perf_counter()

        raw_records, summary = run_generation_batches(
            config=config,
            prompts=prompts,
            model=self.model,
            tokenizer=self.tokenizer,
            method_resources=self.method_resources,
        )

        summary["model_load_seconds"] = model_load_seconds
        summary["container_uptime_seconds"] = time.perf_counter() - self.container_started_at
        summary["remote_run_seconds"] = time.perf_counter() - run_started

        result = write_result_bundle(
            results_root=Path(RESULTS_DIR),
            config=config,
            raw_records=raw_records,
            summary=summary,
        )

        results_volume.commit()
        return result

    def _load_prompts(self, config: ExperimentConfig) -> list[dict[str, Any]]:
        if config.prompt_source == "local_jsonl":
            return load_jsonl_prompts(
                _resolve_prompt_path(config.prompt_path),
                limit=config.limit,
            )
        if config.prompt_source == "wildchat_hf":
            return load_wildchat_hf_prompts(
                dataset_name=config.dataset_name or "allenai/WildChat",
                split=config.dataset_split,
                limit=config.limit,
                language=config.dataset_language,
                streaming=config.dataset_streaming,
                max_messages=config.dataset_max_messages,
                min_user_chars=config.dataset_min_user_chars,
                max_user_chars=config.dataset_max_user_chars,
                include_keywords=config.dataset_include_keywords,
                exclude_keywords=config.dataset_exclude_keywords,
            )
        if config.prompt_source == "alpaca_hf":
            return load_alpaca_hf_prompts(
                dataset_name=config.dataset_name or "yahma/alpaca-cleaned",
                split=config.dataset_split,
                limit=config.limit,
                streaming=config.dataset_streaming,
                min_user_chars=config.dataset_min_user_chars,
                max_user_chars=config.dataset_max_user_chars,
                include_keywords=config.dataset_include_keywords,
                exclude_keywords=config.dataset_exclude_keywords,
            )
        if config.prompt_source == "xsum_hf":
            return load_xsum_hf_prompts(
                dataset_name=config.dataset_name or "EdinburghNLP/xsum",
                split=config.dataset_split,
                limit=config.limit,
                streaming=config.dataset_streaming,
                min_document_chars=config.dataset_min_user_chars,
                max_document_chars=config.dataset_max_user_chars,
            )
        if config.prompt_source == "translation_hf":
            return load_translation_hf_prompts(
                dataset_name=config.dataset_name or "wmt14",
                config_name=config.dataset_config_name or "fr-en",
                source_language=config.dataset_source_language or "fr",
                target_language=config.dataset_target_language or "en",
                split=config.dataset_split,
                limit=config.limit,
                streaming=config.dataset_streaming,
                min_source_chars=config.dataset_min_user_chars,
                max_source_chars=config.dataset_max_user_chars,
            )
        if config.prompt_source == "swebench_hf":
            return load_swebench_hf_prompts(
                dataset_name=config.dataset_name or "princeton-nlp/SWE-bench",
                split=config.dataset_split,
                limit=config.limit,
                streaming=config.dataset_streaming,
            )
        if config.prompt_source == "terminalbench_hf":
            return load_terminalbench_hf_prompts(
                dataset_name=config.dataset_name or "ia03/terminal-bench",
                split=config.dataset_split,
                limit=config.limit,
                streaming=config.dataset_streaming,
            )
        raise ValueError(f"Unsupported prompt_source: {config.prompt_source}")


@app.local_entrypoint()
def main(
    config_path: str = "configs/wmt14_qwen8b_vanilla_fr_en.json",
    gpu: str = "L40S",
    limit: int = 0,
) -> None:
    resolved_config_path = _resolve_prompt_path(config_path)
    config = load_config(resolved_config_path)
    if limit > 0:
        config.limit = limit
    config.gpu = gpu

    prompts: list[dict[str, Any]] | None
    if config.prompt_source == "local_jsonl":
        prompts = load_jsonl_prompts(
            _resolve_prompt_path(config.prompt_path),
            limit=config.limit,
        )
    else:
        prompts = None

    worker_cls = BenchmarkWorker.with_options(gpu=gpu)

    started = time.perf_counter()
    result = worker_cls().run_experiment.remote(config.to_dict(), prompts)
    result["client_wall_seconds"] = time.perf_counter() - started

    print(json.dumps(result, indent=2, sort_keys=True))
