from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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


def load_wildchat_hf_prompts(
    dataset_name: str,
    split: str = "train",
    limit: int | None = None,
    language: str | None = "English",
    streaming: bool = True,
) -> list[dict[str, Any]]:
    from datasets import load_dataset

    prompts: list[dict[str, Any]] = []
    dataset = load_dataset(dataset_name, split=split, streaming=streaming)

    for row_index, record in enumerate(dataset, start=1):
        if language is not None and record.get("language") != language:
            continue
        if record.get("redacted") is True:
            continue

        messages = _wildchat_messages_for_generation(record)
        if messages is None:
            continue

        prompt_id = record.get("conversation_id") or f"wildchat-{row_index}"
        prompts.append({"id": str(prompt_id), "messages": messages})
        if limit is not None and len(prompts) >= limit:
            break

    if not prompts:
        raise ValueError(
            f"No prompts loaded from dataset={dataset_name!r}, split={split!r}"
        )
    return prompts


def _wildchat_messages_for_generation(
    record: dict[str, Any],
) -> list[dict[str, str]] | None:
    conversation = record.get("conversation")
    if not isinstance(conversation, list) or not conversation:
        return None

    messages: list[dict[str, str]] = []
    for turn in conversation:
        role = turn.get("role")
        content = turn.get("content")
        if role not in {"system", "user", "assistant"}:
            continue
        if not isinstance(content, str):
            continue
        content = content.strip()
        if not content:
            continue
        messages.append({"role": role, "content": content})

    if not messages:
        return None

    # Convert a full chat log into a prompt that asks the model for the next
    # assistant turn. If the conversation ends with an assistant message, drop it.
    if messages[-1]["role"] == "assistant":
        messages = messages[:-1]

    if not messages or messages[-1]["role"] != "user":
        return None

    return messages
