from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SUPPORTED_METHODS = {
    "autoregressive",
    "draft_speculative",
    "suffix_speculative",
    "tree_speculative",
}


@dataclass(slots=True)
class ExperimentConfig:
    experiment_name: str
    method: str = "autoregressive"
    target_model: str = "gpt2"
    draft_model: str | None = None
    prompt_path: str = "data/prompts/sample_prompts.jsonl"
    batch_size: int = 1
    max_new_tokens: int = 64
    do_sample: bool = False
    temperature: float = 0.0
    top_p: float = 1.0
    torch_dtype: str = "float16"
    gpu: str = "L40S"
    seed: int = 1234
    limit: int | None = 4
    notes: str = ""

    def validate(self) -> None:
        if self.method not in SUPPORTED_METHODS:
            raise ValueError(f"Unsupported method: {self.method}")
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        if self.max_new_tokens < 1:
            raise ValueError("max_new_tokens must be at least 1")
        if self.torch_dtype not in {"float16", "bfloat16", "float32"}:
            raise ValueError(f"Unsupported torch_dtype: {self.torch_dtype}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentConfig":
        config = cls(**data)
        config.validate()
        return config


def load_config(path: str | Path) -> ExperimentConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return ExperimentConfig.from_dict(data)

