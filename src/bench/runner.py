from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bench.config import ExperimentConfig
from bench.methods import MethodResources, get_benchmark_method
from bench.metrics import BatchRecord, summarize_records


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "run"


def _count_generated_tokens(
    sequence: Any,
    prompt_length: int,
    eos_token_id: int | None,
    pad_token_id: int | None,
) -> int:
    continuation = sequence[prompt_length:].tolist()
    if eos_token_id is not None and eos_token_id in continuation:
        return continuation.index(eos_token_id) + 1
    if pad_token_id is not None and pad_token_id in continuation:
        return continuation.index(pad_token_id)
    return len(continuation)


def _decode_generated_text(
    sequence: Any,
    prompt_length: int,
    total_new_tokens: int,
    tokenizer: Any,
) -> str:
    continuation_ids = sequence[prompt_length : prompt_length + total_new_tokens]
    return tokenizer.decode(
        continuation_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    )


def _build_generation_kwargs(
    config: ExperimentConfig,
    tokenizer: Any,
    method_resources: MethodResources,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "max_new_tokens": config.max_new_tokens,
        "pad_token_id": tokenizer.pad_token_id,
        "use_cache": True,
    }
    if config.do_sample:
        kwargs["do_sample"] = True
        kwargs["temperature"] = config.temperature
        kwargs["top_p"] = config.top_p
    else:
        kwargs["do_sample"] = False

    method = get_benchmark_method(config.method)
    kwargs.update(
        method.build_generation_kwargs(
            config,
            tokenizer=tokenizer,
            resources=method_resources,
        )
    )
    return kwargs


def _render_prompt_text(
    prompt_record: dict[str, Any],
    tokenizer: Any,
    config: ExperimentConfig,
) -> str:
    prompt = prompt_record.get("prompt")
    if isinstance(prompt, str):
        return prompt

    messages = prompt_record.get("messages")
    if isinstance(messages, list):
        if hasattr(tokenizer, "apply_chat_template"):
            kwargs: dict[str, Any] = {
                "tokenize": False,
                "add_generation_prompt": True,
            }
            if config.enable_thinking is not None:
                kwargs["enable_thinking"] = config.enable_thinking
            return tokenizer.apply_chat_template(messages, **kwargs)
        rendered: list[str] = []
        for item in messages:
            role = item["role"].capitalize()
            rendered.append(f"{role}: {item['content']}")
        rendered.append("Assistant:")
        return "\n".join(rendered)

    raise ValueError("Prompt record must contain either 'prompt' or 'messages'")

def run_generation_batches(
    config: ExperimentConfig,
    prompts: list[dict[str, str]],
    model: Any,
    tokenizer: Any,
    method_resources: MethodResources | None = None,
) -> tuple[list[BatchRecord], dict[str, Any]]:
    import torch

    method = get_benchmark_method(config.method)
    method_resources = method_resources or MethodResources()
    generation_kwargs = _build_generation_kwargs(
        config,
        tokenizer,
        method_resources,
    )
    records: list[BatchRecord] = []

    for batch_index, offset in enumerate(range(0, len(prompts), config.batch_size)):
        batch = prompts[offset : offset + config.batch_size]
        texts = [_render_prompt_text(item, tokenizer, config) for item in batch]
        prompt_ids = [item["id"] for item in batch]

        inputs = tokenizer(texts, return_tensors="pt", padding=True)
        input_lengths = inputs["attention_mask"].sum(dim=1).tolist()
        inputs = inputs.to(model.device)

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()

        with method.generation_context(
            config,
            resources=method_resources,
        ) as tracker:
            started = time.perf_counter()
            outputs = model.generate(**inputs, **generation_kwargs)
            latency = time.perf_counter() - started

        sequences = outputs.sequences if hasattr(outputs, "sequences") else outputs

        total_new_tokens = 0
        generated_texts: list[str] = []
        for row_index in range(len(batch)):
            new_tokens = _count_generated_tokens(
                sequences[row_index],
                int(input_lengths[row_index]),
                tokenizer.eos_token_id,
                tokenizer.pad_token_id,
            )
            total_new_tokens += new_tokens
            generated_texts.append(
                _decode_generated_text(
                    sequences[row_index],
                    int(input_lengths[row_index]),
                    new_tokens,
                    tokenizer,
                )
            )

        max_allocated_mb = None
        max_reserved_mb = None
        if torch.cuda.is_available():
            max_allocated_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)
            max_reserved_mb = torch.cuda.max_memory_reserved() / (1024 * 1024)

        method_metrics = method.build_batch_metrics(tracker)
        tokens_per_second = total_new_tokens / latency if latency > 0 else 0.0
        records.append(
            BatchRecord(
                batch_index=batch_index,
                prompt_ids=prompt_ids,
                prompt_texts=texts,
                generated_texts=generated_texts,
                batch_size=len(batch),
                batch_latency_seconds=latency,
                total_new_tokens=total_new_tokens,
                tokens_per_second=tokens_per_second,
                ttft_seconds=None,
                acceptance_rate=method_metrics.get("acceptance_rate"),
                accepted_draft_tokens=method_metrics.get("accepted_draft_tokens"),
                proposed_draft_tokens=method_metrics.get("proposed_draft_tokens"),
                speculation_steps=method_metrics.get("speculation_steps"),
                method_metrics=method_metrics or None,
                max_memory_allocated_mb=max_allocated_mb,
                max_memory_reserved_mb=max_reserved_mb,
            )
        )

    summary = summarize_records(records)
    summary.update(method.summarize_records(records))
    return records, summary


def write_result_bundle(
    results_root: Path,
    config: ExperimentConfig,
    raw_records: list[BatchRecord],
    summary: dict[str, Any],
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = (
        results_root
        / _slugify(config.experiment_name)
        / _slugify(config.method)
        / timestamp
    )
    run_dir.mkdir(parents=True, exist_ok=True)

    raw_path = run_dir / "raw.jsonl"
    with raw_path.open("w", encoding="utf-8") as handle:
        for record in raw_records:
            handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")

    summary_payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": config.to_dict(),
        "summary": summary,
    }
    summary_path = run_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary_payload, handle, indent=2, sort_keys=True)

    return {
        "run_dir": str(run_dir),
        "raw_path": str(raw_path),
        "summary_path": str(summary_path),
        "config": config.to_dict(),
        "summary": summary,
    }
