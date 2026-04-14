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
from bench.datasets import load_jsonl_prompts, load_wildchat_hf_prompts
from bench.runner import run_generation_batches, write_result_bundle

APP_NAME = "llm-serving-bench"
HF_CACHE_DIR = "/cache/hf"
RESULTS_DIR = "/results"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "accelerate>=1.10.0",
        "datasets>=4.4.0",
        "sentencepiece>=0.2.0",
        "torch>=2.8.0",
        "transformers>=4.57.0",
    )
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
        self.loaded_key: tuple[str, str | None, str] | None = None
        self.tokenizer = None
        self.model = None
        self.draft_model = None

    def _ensure_models(self, config: ExperimentConfig) -> float:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        load_key = (config.target_model, config.draft_model, config.torch_dtype)
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
            device_map="auto",
        )
        self.model.eval()

        self.draft_model = None
        if config.method == "draft_speculative":
            if not config.draft_model:
                raise ValueError("draft_model must be set for draft_speculative runs")
            self.draft_model = AutoModelForCausalLM.from_pretrained(
                config.draft_model,
                cache_dir=HF_CACHE_DIR,
                token=token,
                dtype=torch_dtype,
                device_map="auto",
            )
            self.draft_model.eval()

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
            draft_model=self.draft_model,
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
            )
        raise ValueError(f"Unsupported prompt_source: {config.prompt_source}")


@app.local_entrypoint()
def main(
    config_path: str = "configs/smoke_gpt2.json",
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
