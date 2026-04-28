from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from bench.config import ExperimentConfig
from bench.metrics import BatchRecord


@dataclass(slots=True)
class MethodResources:
    draft_model: Any = None
    assistant_tokenizer: Any = None
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SpeculationStats:
    accepted_draft_tokens: int = 0
    proposed_draft_tokens: int = 0
    speculation_steps: int = 0

    @property
    def acceptance_rate(self) -> float | None:
        if self.proposed_draft_tokens == 0:
            return None
        return self.accepted_draft_tokens / self.proposed_draft_tokens


class BenchmarkMethod:
    def prepare_resources(
        self,
        config: ExperimentConfig,
        *,
        target_tokenizer: Any,
        torch_dtype: Any,
        token: str | None,
        hf_cache_dir: str,
        auto_model_cls: Any,
        auto_tokenizer_cls: Any,
        cuda_device_count: int,
    ) -> MethodResources:
        return MethodResources()

    def build_generation_kwargs(
        self,
        config: ExperimentConfig,
        *,
        tokenizer: Any,
        resources: MethodResources,
    ) -> dict[str, Any]:
        return {}

    @contextmanager
    def generation_context(
        self,
        config: ExperimentConfig,
        *,
        resources: MethodResources,
    ):
        yield None

    def build_batch_metrics(self, tracker: Any) -> dict[str, Any]:
        return {}

    def summarize_records(self, records: list[BatchRecord]) -> dict[str, Any]:
        return {}


class AutoregressiveMethod(BenchmarkMethod):
    pass


class DraftSpeculativeMethod(BenchmarkMethod):
    def prepare_resources(
        self,
        config: ExperimentConfig,
        *,
        target_tokenizer: Any,
        torch_dtype: Any,
        token: str | None,
        hf_cache_dir: str,
        auto_model_cls: Any,
        auto_tokenizer_cls: Any,
        cuda_device_count: int,
    ) -> MethodResources:
        if not config.draft_model:
            raise ValueError("draft_model must be set for draft_speculative runs")

        assistant_tokenizer = auto_tokenizer_cls.from_pretrained(
            config.draft_model,
            cache_dir=hf_cache_dir,
            token=token,
        )
        if assistant_tokenizer.pad_token is None:
            assistant_tokenizer.pad_token = assistant_tokenizer.eos_token

        draft_model = auto_model_cls.from_pretrained(
            config.draft_model,
            cache_dir=hf_cache_dir,
            token=token,
            dtype=torch_dtype,
            device_map=(
                {"": "cuda:1"}
                if config.separate_assistant_gpu and cuda_device_count >= 2
                else "auto"
            ),
        )
        draft_model.eval()

        return MethodResources(
            draft_model=draft_model,
            assistant_tokenizer=(
                assistant_tokenizer
                if not _tokenizers_match(target_tokenizer, assistant_tokenizer)
                else None
            ),
        )

    def build_generation_kwargs(
        self,
        config: ExperimentConfig,
        *,
        tokenizer: Any,
        resources: MethodResources,
    ) -> dict[str, Any]:
        if resources.draft_model is None:
            raise ValueError("draft_speculative requires a loaded draft model")

        kwargs: dict[str, Any] = {"assistant_model": resources.draft_model}
        if resources.assistant_tokenizer is not None:
            kwargs["tokenizer"] = tokenizer
            kwargs["assistant_tokenizer"] = resources.assistant_tokenizer
        return kwargs

    @contextmanager
    def generation_context(
        self,
        config: ExperimentConfig,
        *,
        resources: MethodResources,
    ):
        from transformers.generation.candidate_generator import AssistedCandidateGenerator

        stats = SpeculationStats()
        original_update = AssistedCandidateGenerator.update_candidate_strategy

        def wrapped_update(self, input_ids: Any, scores: Any, num_matches: int):
            if hasattr(num_matches, "item"):
                num_matches = int(num_matches.item())
            else:
                num_matches = int(num_matches)

            proposed_draft_tokens = 0
            if scores is not None:
                try:
                    proposed_draft_tokens = max(len(scores[0]) - 1, 0)
                except Exception:
                    proposed_draft_tokens = 0

            if proposed_draft_tokens > 0:
                stats.proposed_draft_tokens += proposed_draft_tokens
                stats.accepted_draft_tokens += min(num_matches, proposed_draft_tokens)
                stats.speculation_steps += 1

            return original_update(self, input_ids, scores, num_matches)

        AssistedCandidateGenerator.update_candidate_strategy = wrapped_update
        try:
            yield stats
        finally:
            AssistedCandidateGenerator.update_candidate_strategy = original_update

    def build_batch_metrics(self, tracker: Any) -> dict[str, Any]:
        if tracker is None:
            return {}
        return {
            "acceptance_rate": tracker.acceptance_rate,
            "accepted_draft_tokens": tracker.accepted_draft_tokens,
            "proposed_draft_tokens": tracker.proposed_draft_tokens,
            "speculation_steps": tracker.speculation_steps,
        }

    def summarize_records(self, records: list[BatchRecord]) -> dict[str, Any]:
        accepted_draft_tokens = sum(
            record.accepted_draft_tokens or 0
            for record in records
        )
        proposed_draft_tokens = sum(
            record.proposed_draft_tokens or 0
            for record in records
        )
        return {
            "accepted_draft_tokens": accepted_draft_tokens if proposed_draft_tokens > 0 else None,
            "proposed_draft_tokens": proposed_draft_tokens if proposed_draft_tokens > 0 else None,
            "acceptance_rate": (
                accepted_draft_tokens / proposed_draft_tokens
                if proposed_draft_tokens > 0
                else None
            ),
        }


class PromptLookupMethod(BenchmarkMethod):
    def build_generation_kwargs(
        self,
        config: ExperimentConfig,
        *,
        tokenizer: Any,
        resources: MethodResources,
    ) -> dict[str, Any]:
        prompt_lookup_num_tokens = config.get_method_option(
            "prompt_lookup_num_tokens",
            config.prompt_lookup_num_tokens,
        )
        return {
            "prompt_lookup_num_tokens": prompt_lookup_num_tokens or 5,
        }


class SuffixSpeculativeMethod(BenchmarkMethod):
    def prepare_resources(
        self,
        config: ExperimentConfig,
        *,
        target_tokenizer: Any,
        torch_dtype: Any,
        token: str | None,
        hf_cache_dir: str,
        auto_model_cls: Any,
        auto_tokenizer_cls: Any,
        cuda_device_count: int,
    ) -> MethodResources:
        from transformers.generation.suffix_tree import SuffixDecodingCache

        max_depth = config.get_method_option("suffix_decoding_max_depth", 64)
        source_mode = config.get_method_option(
            "suffix_decoding_source_mode",
            "local_and_global",
        )
        if source_mode not in {"local_and_global", "local_only", "global_only"}:
            raise ValueError(
                "suffix_decoding_source_mode must be one of: "
                "'local_and_global', 'local_only', 'global_only'"
            )
        cache_max_requests = config.get_method_option(
            "suffix_decoding_cache_max_requests",
            -1,
        )
        cache = SuffixDecodingCache(
            max_depth=max_depth,
            max_cached_requests=cache_max_requests,
            source_mode=source_mode,
        )
        return MethodResources(extras={"suffix_decoding_cache": cache})

    def build_generation_kwargs(
        self,
        config: ExperimentConfig,
        *,
        tokenizer: Any,
        resources: MethodResources,
    ) -> dict[str, Any]:
        suffix_decoding_num_tokens = config.get_method_option(
            "suffix_decoding_num_tokens", 10,
        )
        suffix_decoding_max_depth = config.get_method_option(
            "suffix_decoding_max_depth", 64,
        )
        suffix_decoding_min_prob = config.get_method_option(
            "suffix_decoding_min_prob", 0.1,
        )
        kwargs = {
            "suffix_decoding_num_tokens": suffix_decoding_num_tokens,
            "suffix_decoding_max_depth": suffix_decoding_max_depth,
            "suffix_decoding_min_prob": suffix_decoding_min_prob,
        }
        cache = resources.extras.get("suffix_decoding_cache")
        if cache is not None:
            kwargs["suffix_decoding_cache"] = cache
        return kwargs

    @contextmanager
    def generation_context(
        self,
        config: ExperimentConfig,
        *,
        resources: MethodResources,
    ):
        from transformers.generation.candidate_generator import SuffixDecodingCandidateGenerator

        stats = SpeculationStats()
        original_update = SuffixDecodingCandidateGenerator.update_candidate_strategy

        def wrapped_update(self, input_ids: Any, scores: Any, num_matches: int):
            if hasattr(num_matches, "item"):
                num_matches = int(num_matches.item())
            else:
                num_matches = int(num_matches)

            proposed_draft_tokens = 0
            if scores is not None:
                try:
                    proposed_draft_tokens = max(len(scores[0]) - 1, 0)
                except Exception:
                    proposed_draft_tokens = 0

            if proposed_draft_tokens > 0:
                stats.proposed_draft_tokens += proposed_draft_tokens
                stats.accepted_draft_tokens += min(num_matches, proposed_draft_tokens)
                stats.speculation_steps += 1

            return original_update(self, input_ids, scores, num_matches)

        SuffixDecodingCandidateGenerator.update_candidate_strategy = wrapped_update
        try:
            yield stats
        finally:
            SuffixDecodingCandidateGenerator.update_candidate_strategy = original_update

    def build_batch_metrics(self, tracker: Any) -> dict[str, Any]:
        if tracker is None:
            return {}
        return {
            "acceptance_rate": tracker.acceptance_rate,
            "accepted_draft_tokens": tracker.accepted_draft_tokens,
            "proposed_draft_tokens": tracker.proposed_draft_tokens,
            "speculation_steps": tracker.speculation_steps,
        }

    def summarize_records(self, records: list[BatchRecord]) -> dict[str, Any]:
        accepted_draft_tokens = sum(
            record.accepted_draft_tokens or 0
            for record in records
        )
        proposed_draft_tokens = sum(
            record.proposed_draft_tokens or 0
            for record in records
        )
        return {
            "accepted_draft_tokens": accepted_draft_tokens if proposed_draft_tokens > 0 else None,
            "proposed_draft_tokens": proposed_draft_tokens if proposed_draft_tokens > 0 else None,
            "acceptance_rate": (
                accepted_draft_tokens / proposed_draft_tokens
                if proposed_draft_tokens > 0
                else None
            ),
        }


class UnimplementedMethod(BenchmarkMethod):
    def __init__(self, method_name: str):
        self.method_name = method_name

    def build_generation_kwargs(
        self,
        config: ExperimentConfig,
        *,
        tokenizer: Any,
        resources: MethodResources,
    ) -> dict[str, Any]:
        raise NotImplementedError(f"{self.method_name} is not implemented yet")


METHOD_REGISTRY: dict[str, BenchmarkMethod] = {
    "autoregressive": AutoregressiveMethod(),
    "draft_speculative": DraftSpeculativeMethod(),
    "prompt_lookup": PromptLookupMethod(),
    "suffix_speculative": SuffixSpeculativeMethod(),
    "tree_speculative": UnimplementedMethod("tree_speculative"),
}


def get_benchmark_method(name: str) -> BenchmarkMethod:
    try:
        return METHOD_REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported method: {name}") from exc


def _tokenizers_match(main_tokenizer: Any, assistant_tokenizer: Any) -> bool:
    if type(main_tokenizer) is not type(assistant_tokenizer):
        return False
    if getattr(main_tokenizer, "vocab_size", None) != getattr(assistant_tokenizer, "vocab_size", None):
        return False
    if getattr(main_tokenizer, "bos_token_id", None) != getattr(assistant_tokenizer, "bos_token_id", None):
        return False
    if getattr(main_tokenizer, "eos_token_id", None) != getattr(assistant_tokenizer, "eos_token_id", None):
        return False
    if getattr(main_tokenizer, "pad_token_id", None) != getattr(assistant_tokenizer, "pad_token_id", None):
        return False
    return main_tokenizer.get_vocab() == assistant_tokenizer.get_vocab()
