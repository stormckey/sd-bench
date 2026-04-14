from __future__ import annotations

import json
from pathlib import Path


def load_jsonl_prompts(
    path: str | Path,
    limit: int | None = None,
) -> list[dict[str, str]]:
    prompts: list[dict[str, str]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            prompt = record.get("prompt")
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError(f"Invalid prompt at line {line_number} in {path}")
            prompt_id = record.get("id") or f"prompt-{line_number}"
            prompts.append({"id": str(prompt_id), "prompt": prompt})
            if limit is not None and len(prompts) >= limit:
                break
    if not prompts:
        raise ValueError(f"No prompts loaded from {path}")
    return prompts

