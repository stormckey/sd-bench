from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIGS_DIR = ROOT / "configs"


BUILTIN_SUITES: dict[str, list[str]] = {
    "default": [
        "configs/wmt14_qwen8b_vanilla_fr_en.json",
        "configs/wmt14_qwen8b_draft_fr_en.json",
        "configs/wmt14_qwen8b_prompt_lookup_fr_en.json",
        "configs/wmt14_qwen8b_suffix_fr_en.json",
    ],
    "wmt14": [
        "configs/wmt14_qwen8b_vanilla_fr_en.json",
        "configs/wmt14_qwen8b_draft_fr_en.json",
        "configs/wmt14_qwen8b_prompt_lookup_fr_en.json",
        "configs/wmt14_qwen8b_suffix_fr_en.json",
    ],
    "wildchat": [
        "configs/wildchat_qwen8b_vanilla_translate.json",
        "configs/wildchat_qwen8b_draft_translate.json",
        "configs/wildchat_qwen8b_prompt_lookup_translate.json",
        "configs/wildchat_qwen8b_suffix_translate.json",
    ],
    "wildchat-code": [
        "configs/wildchat_qwen8b_vanilla_code.json",
        "configs/wildchat_qwen8b_draft_code.json",
        "configs/wildchat_qwen8b_prompt_lookup_code.json",
        "configs/wildchat_qwen8b_suffix_code.json",
    ],
    "swebench": [
        "configs/swebench_qwen8b_vanilla.json",
        "configs/swebench_qwen8b_draft.json",
        "configs/swebench_qwen8b_prompt_lookup.json",
        "configs/swebench_qwen8b_suffix.json",
    ],
    "terminalbench": [
        "configs/terminalbench_qwen8b_vanilla.json",
        "configs/terminalbench_qwen8b_draft.json",
        "configs/terminalbench_qwen8b_prompt_lookup.json",
        "configs/terminalbench_qwen8b_suffix.json",
    ],
}


def list_builtin_suites() -> dict[str, list[str]]:
    return BUILTIN_SUITES.copy()


def resolve_suite(name: str) -> list[Path]:
    try:
        paths = BUILTIN_SUITES[name]
    except KeyError as exc:
        raise KeyError(f"Unknown suite: {name}") from exc
    return [ROOT / path for path in paths]
