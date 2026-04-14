from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class BatchRecord:
    batch_index: int
    prompt_ids: list[str]
    batch_size: int
    batch_latency_seconds: float
    total_new_tokens: int
    tokens_per_second: float
    ttft_seconds: float | None
    acceptance_rate: float | None
    accepted_draft_tokens: int | None
    proposed_draft_tokens: int | None
    max_memory_allocated_mb: float | None
    max_memory_reserved_mb: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def summarize_records(records: list[BatchRecord]) -> dict[str, Any]:
    total_batches = len(records)
    total_prompts = sum(record.batch_size for record in records)
    total_latency = sum(record.batch_latency_seconds for record in records)
    total_new_tokens = sum(record.total_new_tokens for record in records)
    peak_allocated = [
        record.max_memory_allocated_mb
        for record in records
        if record.max_memory_allocated_mb is not None
    ]
    peak_reserved = [
        record.max_memory_reserved_mb
        for record in records
        if record.max_memory_reserved_mb is not None
    ]
    accepted_draft_tokens = sum(
        record.accepted_draft_tokens or 0
        for record in records
    )
    proposed_draft_tokens = sum(
        record.proposed_draft_tokens or 0
        for record in records
    )

    return {
        "num_batches": total_batches,
        "num_prompts": total_prompts,
        "total_latency_seconds": total_latency,
        "mean_batch_latency_seconds": (
            statistics.mean(record.batch_latency_seconds for record in records)
            if records
            else 0.0
        ),
        "total_generated_tokens": total_new_tokens,
        "overall_tokens_per_second": (
            total_new_tokens / total_latency if total_latency > 0 else 0.0
        ),
        "peak_memory_allocated_mb": max(peak_allocated) if peak_allocated else None,
        "peak_memory_reserved_mb": max(peak_reserved) if peak_reserved else None,
        "accepted_draft_tokens": accepted_draft_tokens if proposed_draft_tokens > 0 else None,
        "proposed_draft_tokens": proposed_draft_tokens if proposed_draft_tokens > 0 else None,
        "acceptance_rate": (
            accepted_draft_tokens / proposed_draft_tokens
            if proposed_draft_tokens > 0
            else None
        ),
        "ttft_supported": False,
    }
