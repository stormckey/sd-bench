from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_jsonl_prompts(
    path: str | Path,
    limit: int | None = None,
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
            if limit is not None and len(prompts) >= limit:
                break
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
    language: str | None = "English",
    streaming: bool = True,
    max_messages: int | None = None,
    min_user_chars: int | None = None,
    max_user_chars: int | None = None,
    include_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
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
        if not _wildchat_matches_filters(
            messages,
            max_messages=max_messages,
            min_user_chars=min_user_chars,
            max_user_chars=max_user_chars,
            include_keywords=include_keywords,
            exclude_keywords=exclude_keywords,
        ):
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


def load_alpaca_hf_prompts(
    dataset_name: str,
    split: str = "train",
    limit: int | None = None,
    streaming: bool = True,
    min_user_chars: int | None = None,
    max_user_chars: int | None = None,
    include_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    from datasets import load_dataset

    prompts: list[dict[str, Any]] = []
    dataset = load_dataset(dataset_name, split=split, streaming=streaming)

    for row_index, record in enumerate(dataset, start=1):
        messages = _alpaca_messages_for_generation(record)
        if messages is None:
            continue
        if not _wildchat_matches_filters(
            messages,
            max_messages=1,
            min_user_chars=min_user_chars,
            max_user_chars=max_user_chars,
            include_keywords=include_keywords,
            exclude_keywords=exclude_keywords,
        ):
            continue

        prompt_id = record.get("instruction") or f"alpaca-{row_index}"
        prompts.append({"id": str(prompt_id), "messages": messages})
        if limit is not None and len(prompts) >= limit:
            break

    if not prompts:
        raise ValueError(
            f"No prompts loaded from dataset={dataset_name!r}, split={split!r}"
        )
    return prompts


def load_spider_hf_prompts(
    dataset_name: str,
    split: str = "validation",
    limit: int | None = None,
    streaming: bool = True,
) -> list[dict[str, Any]]:
    from datasets import load_dataset

    prompts: list[dict[str, Any]] = []
    dataset = load_dataset(dataset_name, split=split, streaming=streaming)

    for row_index, record in enumerate(dataset, start=1):
        prompt = _spider_prompt_for_generation(record)
        if prompt is None:
            continue

        prompt_id = (
            record.get("db_id")
            or record.get("id")
            or f"spider-{row_index}"
        )
        prompts.append({"id": str(prompt_id), "prompt": prompt})
        if limit is not None and len(prompts) >= limit:
            break

    if not prompts:
        raise ValueError(
            f"No prompts loaded from dataset={dataset_name!r}, split={split!r}"
        )
    return prompts


def load_swebench_hf_prompts(
    dataset_name: str,
    split: str = "test",
    limit: int | None = None,
    streaming: bool = True,
) -> list[dict[str, Any]]:
    from datasets import load_dataset

    prompts: list[dict[str, Any]] = []
    dataset = load_dataset(dataset_name, split=split, streaming=streaming)

    for row_index, record in enumerate(dataset, start=1):
        problem = record.get("problem_statement")
        if not isinstance(problem, str) or not problem.strip():
            continue
        prompt_id = record.get("instance_id") or f"swebench-{row_index}"
        prompts.append({"id": str(prompt_id), "prompt": problem.strip()})
        if limit is not None and len(prompts) >= limit:
            break

    if not prompts:
        raise ValueError(
            f"No prompts loaded from dataset={dataset_name!r}, split={split!r}"
        )
    return prompts


def load_terminalbench_hf_prompts(
    dataset_name: str,
    split: str = "test",
    limit: int | None = None,
    streaming: bool = True,
) -> list[dict[str, Any]]:
    from datasets import load_dataset

    prompts: list[dict[str, Any]] = []
    dataset = load_dataset(dataset_name, split=split, streaming=streaming)

    for row_index, record in enumerate(dataset, start=1):
        description = record.get("base_description")
        if not isinstance(description, str) or not description.strip():
            continue
        prompt_id = record.get("task_id") or f"terminalbench-{row_index}"
        prompts.append({"id": str(prompt_id), "prompt": description.strip()})
        if limit is not None and len(prompts) >= limit:
            break

    if not prompts:
        raise ValueError(
            f"No prompts loaded from dataset={dataset_name!r}, split={split!r}"
        )
    return prompts


def load_xsum_hf_prompts(
    dataset_name: str,
    split: str = "test",
    limit: int | None = None,
    streaming: bool = True,
    min_document_chars: int | None = None,
    max_document_chars: int | None = None,
) -> list[dict[str, Any]]:
    from datasets import load_dataset

    prompts: list[dict[str, Any]] = []
    dataset = load_dataset(dataset_name, split=split, streaming=streaming)

    for row_index, record in enumerate(dataset, start=1):
        document = record.get("document")
        if not isinstance(document, str):
            continue
        document = document.strip()
        if not document:
            continue
        if min_document_chars is not None and len(document) < min_document_chars:
            continue
        if max_document_chars is not None and len(document) > max_document_chars:
            continue

        prompt = (
            "Summarize the following article in 1-3 sentences.\n\n"
            f"Article:\n{document}\n\nSummary:"
        )
        prompt_id = record.get("id") or f"xsum-{row_index}"
        prompts.append({"id": str(prompt_id), "prompt": prompt})
        if limit is not None and len(prompts) >= limit:
            break

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
    streaming: bool = True,
    min_source_chars: int | None = None,
    max_source_chars: int | None = None,
) -> list[dict[str, Any]]:
    from datasets import load_dataset

    prompts: list[dict[str, Any]] = []
    dataset = load_dataset(
        dataset_name,
        config_name,
        split=split,
        streaming=streaming,
    )

    source_label = _language_display_name(source_language)
    target_label = _language_display_name(target_language)

    for row_index, record in enumerate(dataset, start=1):
        translation = record.get("translation")
        if not isinstance(translation, dict):
            continue
        source_text = translation.get(source_language)
        target_text = translation.get(target_language)
        if not isinstance(source_text, str) or not isinstance(target_text, str):
            continue
        source_text = source_text.strip()
        if not source_text:
            continue
        if min_source_chars is not None and len(source_text) < min_source_chars:
            continue
        if max_source_chars is not None and len(source_text) > max_source_chars:
            continue

        prompt = (
            f"Translate the following text from {source_label} to {target_label}. "
            "Return only the translation.\n\n"
            f"{source_label}:\n{source_text}\n\n{target_label}:"
        )
        prompt_id = record.get("id") or f"translation-{row_index}"
        prompts.append({"id": str(prompt_id), "prompt": prompt})
        if limit is not None and len(prompts) >= limit:
            break

    if not prompts:
        raise ValueError(
            f"No prompts loaded from dataset={dataset_name!r}, config={config_name!r}, split={split!r}"
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
