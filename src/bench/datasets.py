from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


def load_jsonl_prompts(
    path: str | Path,
    limit: int | None = None,
    seed: int = 1234,
) -> list[dict[str, Any]]:
    prompts: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            prompt_id = record.get("id") or f"prompt-{line_number}"
            prompt = record.get("prompt")
            messages = record.get("messages")
            if isinstance(prompt, str) and prompt.strip():
                prompts.append({"id": str(prompt_id), "prompt": prompt})
            elif _is_valid_message_list(messages):
                prompts.append({"id": str(prompt_id), "messages": messages})
            else:
                raise ValueError(f"Invalid prompt record at line {line_number} in {path}")
    prompts = _sample_records(prompts, limit=limit, seed=seed)
    if not prompts:
        raise ValueError(f"No prompts loaded from {path}")
    return prompts


def _is_valid_message_list(messages: Any) -> bool:
    if not isinstance(messages, list) or not messages:
        return False
    for item in messages:
        if not isinstance(item, dict):
            return False
        if item.get("role") not in {"system", "user", "assistant"}:
            return False
        if not isinstance(item.get("content"), str) or not item["content"].strip():
            return False
    return True


def load_wildchat_hf_prompts(
    dataset_name: str,
    split: str = "train",
    limit: int | None = None,
    seed: int = 1234,
    language: str | None = "English",
    streaming: bool = True,
    max_messages: int | None = None,
    min_user_chars: int | None = None,
    max_user_chars: int | None = None,
    include_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    prompts = _reservoir_sample_filtered_dataset(
        dataset_name=dataset_name,
        split=split,
        streaming=streaming,
        limit=limit,
        seed=seed,
        row_builder=lambda record, row_index: _wildchat_prompt_record(
            record,
            row_index=row_index,
            language=language,
            max_messages=max_messages,
            min_user_chars=min_user_chars,
            max_user_chars=max_user_chars,
            include_keywords=include_keywords,
            exclude_keywords=exclude_keywords,
        ),
    )

    if not prompts:
        raise ValueError(
            f"No prompts loaded from dataset={dataset_name!r}, split={split!r}"
        )
    return prompts


def load_alpaca_hf_prompts(
    dataset_name: str,
    split: str = "train",
    limit: int | None = None,
    seed: int = 1234,
    streaming: bool = True,
    min_user_chars: int | None = None,
    max_user_chars: int | None = None,
    include_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    from datasets import load_dataset

    prompts = _reservoir_sample_filtered_dataset(
        dataset_name=dataset_name,
        split=split,
        streaming=streaming,
        limit=limit,
        seed=seed,
        row_builder=lambda record, row_index: _alpaca_prompt_record(
            record,
            row_index=row_index,
            min_user_chars=min_user_chars,
            max_user_chars=max_user_chars,
            include_keywords=include_keywords,
            exclude_keywords=exclude_keywords,
        ),
    )

    if not prompts:
        raise ValueError(
            f"No prompts loaded from dataset={dataset_name!r}, split={split!r}"
        )
    return prompts


def load_spider_hf_prompts(
    dataset_name: str,
    split: str = "validation",
    limit: int | None = None,
    seed: int = 1234,
    streaming: bool = True,
) -> list[dict[str, Any]]:
    prompts = _reservoir_sample_filtered_dataset(
        dataset_name=dataset_name,
        split=split,
        streaming=streaming,
        limit=limit,
        seed=seed,
        row_builder=lambda record, row_index: _spider_prompt_record(record, row_index),
    )

    if not prompts:
        raise ValueError(
            f"No prompts loaded from dataset={dataset_name!r}, split={split!r}"
        )
    return prompts


def load_swebench_hf_prompts(
    dataset_name: str,
    split: str = "test",
    limit: int | None = None,
    seed: int = 1234,
    streaming: bool = True,
) -> list[dict[str, Any]]:
    prompts = _reservoir_sample_filtered_dataset(
        dataset_name=dataset_name,
        split=split,
        streaming=streaming,
        limit=limit,
        seed=seed,
        row_builder=lambda record, row_index: _swebench_prompt_record(record, row_index),
    )

    if not prompts:
        raise ValueError(
            f"No prompts loaded from dataset={dataset_name!r}, split={split!r}"
        )
    return prompts


def load_terminalbench_hf_prompts(
    dataset_name: str,
    split: str = "test",
    limit: int | None = None,
    seed: int = 1234,
    streaming: bool = True,
) -> list[dict[str, Any]]:
    prompts = _reservoir_sample_filtered_dataset(
        dataset_name=dataset_name,
        split=split,
        streaming=streaming,
        limit=limit,
        seed=seed,
        row_builder=lambda record, row_index: _terminalbench_prompt_record(record, row_index),
    )

    if not prompts:
        raise ValueError(
            f"No prompts loaded from dataset={dataset_name!r}, split={split!r}"
        )
    return prompts


def load_xsum_hf_prompts(
    dataset_name: str,
    split: str = "test",
    limit: int | None = None,
    seed: int = 1234,
    streaming: bool = True,
    min_document_chars: int | None = None,
    max_document_chars: int | None = None,
) -> list[dict[str, Any]]:
    prompts = _reservoir_sample_filtered_dataset(
        dataset_name=dataset_name,
        split=split,
        streaming=streaming,
        limit=limit,
        seed=seed,
        row_builder=lambda record, row_index: _xsum_prompt_record(
            record,
            row_index=row_index,
            min_document_chars=min_document_chars,
            max_document_chars=max_document_chars,
        ),
    )

    if not prompts:
        raise ValueError(
            f"No prompts loaded from dataset={dataset_name!r}, split={split!r}"
        )
    return prompts


def load_translation_hf_prompts(
    dataset_name: str,
    config_name: str,
    source_language: str,
    target_language: str,
    split: str = "test",
    limit: int | None = None,
    seed: int = 1234,
    streaming: bool = True,
    min_source_chars: int | None = None,
    max_source_chars: int | None = None,
) -> list[dict[str, Any]]:
    source_label = _language_display_name(source_language)
    target_label = _language_display_name(target_language)
    prompts = _reservoir_sample_filtered_dataset(
        dataset_name=dataset_name,
        split=split,
        streaming=streaming,
        limit=limit,
        seed=seed,
        config_name=config_name,
        row_builder=lambda record, row_index: _translation_prompt_record(
            record,
            row_index=row_index,
            source_language=source_language,
            target_language=target_language,
            source_label=source_label,
            target_label=target_label,
            min_source_chars=min_source_chars,
            max_source_chars=max_source_chars,
        ),
    )

    if not prompts:
        raise ValueError(
            f"No prompts loaded from dataset={dataset_name!r}, config={config_name!r}, split={split!r}"
        )
    return prompts


def _sample_records(
    prompts: list[dict[str, Any]],
    *,
    limit: int | None,
    seed: int,
) -> list[dict[str, Any]]:
    if limit is None or len(prompts) <= limit:
        return prompts
    rng = random.Random(seed)
    sampled = list(prompts)
    rng.shuffle(sampled)
    return sampled[:limit]


def _reservoir_sample_filtered_dataset(
    *,
    dataset_name: str,
    split: str,
    streaming: bool,
    limit: int | None,
    seed: int,
    row_builder: Any,
    config_name: str | None = None,
) -> list[dict[str, Any]]:
    from datasets import load_dataset

    if config_name is None:
        dataset = load_dataset(dataset_name, split=split, streaming=streaming)
    else:
        dataset = load_dataset(
            dataset_name,
            config_name,
            split=split,
            streaming=streaming,
        )

    prompts: list[dict[str, Any]] = []

    for row_index, record in enumerate(dataset, start=1):
        prompt_record = row_builder(record, row_index)
        if prompt_record is None:
            continue
        prompts.append(prompt_record)

    return _sample_records(prompts, limit=limit, seed=seed)


def _wildchat_prompt_record(
    record: dict[str, Any],
    *,
    row_index: int,
    language: str | None,
    max_messages: int | None,
    min_user_chars: int | None,
    max_user_chars: int | None,
    include_keywords: list[str] | None,
    exclude_keywords: list[str] | None,
) -> dict[str, Any] | None:
    if language is not None and record.get("language") != language:
        return None
    if record.get("redacted") is True:
        return None

    messages = _wildchat_messages_for_generation(record)
    if messages is None:
        return None
    if not _wildchat_matches_filters(
        messages,
        max_messages=max_messages,
        min_user_chars=min_user_chars,
        max_user_chars=max_user_chars,
        include_keywords=include_keywords,
        exclude_keywords=exclude_keywords,
    ):
        return None

    prompt_id = record.get("conversation_id") or f"wildchat-{row_index}"
    return {"id": str(prompt_id), "messages": messages}


def _alpaca_prompt_record(
    record: dict[str, Any],
    *,
    row_index: int,
    min_user_chars: int | None,
    max_user_chars: int | None,
    include_keywords: list[str] | None,
    exclude_keywords: list[str] | None,
) -> dict[str, Any] | None:
    messages = _alpaca_messages_for_generation(record)
    if messages is None:
        return None
    if not _wildchat_matches_filters(
        messages,
        max_messages=1,
        min_user_chars=min_user_chars,
        max_user_chars=max_user_chars,
        include_keywords=include_keywords,
        exclude_keywords=exclude_keywords,
    ):
        return None

    prompt_id = record.get("instruction") or f"alpaca-{row_index}"
    return {"id": str(prompt_id), "messages": messages}


def _spider_prompt_record(record: dict[str, Any], row_index: int) -> dict[str, Any] | None:
    prompt = _spider_prompt_for_generation(record)
    if prompt is None:
        return None
    prompt_id = record.get("db_id") or record.get("id") or f"spider-{row_index}"
    return {"id": str(prompt_id), "prompt": prompt}


def _swebench_prompt_record(record: dict[str, Any], row_index: int) -> dict[str, Any] | None:
    problem = record.get("problem_statement")
    if not isinstance(problem, str) or not problem.strip():
        return None
    prompt_id = record.get("instance_id") or f"swebench-{row_index}"
    return {"id": str(prompt_id), "prompt": problem.strip()}


def _terminalbench_prompt_record(record: dict[str, Any], row_index: int) -> dict[str, Any] | None:
    description = record.get("base_description")
    if not isinstance(description, str) or not description.strip():
        return None
    prompt_id = record.get("task_id") or f"terminalbench-{row_index}"
    return {"id": str(prompt_id), "prompt": description.strip()}


def _xsum_prompt_record(
    record: dict[str, Any],
    *,
    row_index: int,
    min_document_chars: int | None,
    max_document_chars: int | None,
) -> dict[str, Any] | None:
    document = record.get("document")
    if not isinstance(document, str):
        return None
    document = document.strip()
    if not document:
        return None
    if min_document_chars is not None and len(document) < min_document_chars:
        return None
    if max_document_chars is not None and len(document) > max_document_chars:
        return None

    prompt = (
        "Summarize the following article in 1-3 sentences.\n\n"
        f"Article:\n{document}\n\nSummary:"
    )
    prompt_id = record.get("id") or f"xsum-{row_index}"
    return {"id": str(prompt_id), "prompt": prompt}


def _translation_prompt_record(
    record: dict[str, Any],
    *,
    row_index: int,
    source_language: str,
    target_language: str,
    source_label: str,
    target_label: str,
    min_source_chars: int | None,
    max_source_chars: int | None,
) -> dict[str, Any] | None:
    translation = record.get("translation")
    if not isinstance(translation, dict):
        return None
    source_text = translation.get(source_language)
    target_text = translation.get(target_language)
    if not isinstance(source_text, str) or not isinstance(target_text, str):
        return None
    source_text = source_text.strip()
    if not source_text:
        return None
    if min_source_chars is not None and len(source_text) < min_source_chars:
        return None
    if max_source_chars is not None and len(source_text) > max_source_chars:
        return None

    prompt_id = record.get("id") or f"translation-{row_index}"
    messages = [
        {
            "role": "system",
            "content": (
                f"You are a translation assistant. Translate {source_label} text into "
                f"{target_label}. Return only the translation."
            ),
        },
        {
            "role": "user",
            "content": f"{source_label}:\n{source_text}",
        },
    ]
    return {"id": str(prompt_id), "messages": messages}


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


def _alpaca_messages_for_generation(
    record: dict[str, Any],
) -> list[dict[str, str]] | None:
    instruction = record.get("instruction")
    if not isinstance(instruction, str) or not instruction.strip():
        return None

    input_text = record.get("input")
    content = instruction.strip()
    if isinstance(input_text, str):
        normalized_input = input_text.strip()
        if normalized_input and normalized_input.casefold() not in {
            "<noinput>",
            "no input",
            "noinput",
        }:
            content = f"{content}\n\nInput:\n{normalized_input}"

    return [{"role": "user", "content": content}]


def _spider_prompt_for_generation(record: dict[str, Any]) -> str | None:
    instruction = record.get("input")
    if isinstance(instruction, str) and instruction.strip():
        return instruction.strip()

    question = record.get("question")
    schema = (
        record.get("schema")
        or record.get("serialized_schema")
        or record.get("context")
    )
    if not isinstance(question, str) or not question.strip():
        return None
    if not isinstance(schema, str) or not schema.strip():
        return None

    return (
        "You are given a database schema and a natural-language question. "
        "Write a SQL query that answers the question. Return only the SQL query.\n\n"
        f"Schema:\n{schema.strip()}\n\n"
        f"Question:\n{question.strip()}\n\n"
        "SQL:"
    )


def _language_display_name(code: str) -> str:
    mapping = {
        "en": "English",
        "fr": "French",
        "de": "German",
        "es": "Spanish",
        "it": "Italian",
        "pt": "Portuguese",
        "nl": "Dutch",
    }
    return mapping.get(code, code)


def _wildchat_matches_filters(
    messages: list[dict[str, str]],
    max_messages: int | None,
    min_user_chars: int | None,
    max_user_chars: int | None,
    include_keywords: list[str] | None,
    exclude_keywords: list[str] | None,
) -> bool:
    if max_messages is not None and len(messages) > max_messages:
        return False

    user_text = messages[-1]["content"].strip()
    normalized = user_text.casefold()

    if min_user_chars is not None and len(user_text) < min_user_chars:
        return False
    if max_user_chars is not None and len(user_text) > max_user_chars:
        return False

    if include_keywords:
        normalized_keywords = [keyword.casefold() for keyword in include_keywords]
        if not any(keyword in normalized for keyword in normalized_keywords):
            return False

    if exclude_keywords:
        normalized_keywords = [keyword.casefold() for keyword in exclude_keywords]
        if any(keyword in normalized for keyword in normalized_keywords):
            return False

    return True
