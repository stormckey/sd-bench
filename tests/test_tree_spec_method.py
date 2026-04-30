from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bench.config import ExperimentConfig
from bench.methods import MethodResources, TreeSpeculativeMethod, get_benchmark_method


class FakeSuffixDecodingCache:
    def __init__(self, max_depth: int, max_cached_requests: int, source_mode: str):
        self.max_depth = max_depth
        self.max_cached_requests = max_cached_requests
        self.source_mode = source_mode


class FakeTreeSpecDecodingCandidateGenerator:
    last_call = None

    def update_candidate_strategy(self, input_ids, scores, num_matches):
        FakeTreeSpecDecodingCandidateGenerator.last_call = {
            "input_ids": input_ids,
            "scores": scores,
            "num_matches": num_matches,
        }
        return FakeTreeSpecDecodingCandidateGenerator.last_call


class TreeSpecMethodTests(unittest.TestCase):
    def test_method_registry_returns_tree_spec_method(self):
        method = get_benchmark_method("tree_speculative")
        self.assertIsInstance(method, TreeSpeculativeMethod)

    def test_build_generation_kwargs_uses_tree_spec_options(self):
        config = ExperimentConfig.from_dict(
            {
                "experiment_name": "tree-spec-test",
                "method": "tree_speculative",
                "method_options": {
                    "tree_spec_decoding_num_tokens": 12,
                    "tree_spec_decoding_max_depth": 40,
                    "tree_spec_decoding_min_prob": 0.25,
                    "tree_spec_decoding_branch_factor": 3,
                },
            }
        )
        resources = MethodResources(extras={"suffix_decoding_cache": object()})

        kwargs = TreeSpeculativeMethod().build_generation_kwargs(
            config,
            tokenizer=object(),
            resources=resources,
        )

        self.assertEqual(kwargs["tree_spec_decoding_num_tokens"], 12)
        self.assertEqual(kwargs["tree_spec_decoding_max_depth"], 40)
        self.assertEqual(kwargs["tree_spec_decoding_min_prob"], 0.25)
        self.assertEqual(kwargs["tree_spec_decoding_branch_factor"], 3)
        self.assertIn("tree_spec_decoding_cache", kwargs)
        self.assertNotIn("assistant_model", kwargs)

    def test_prepare_resources_builds_tree_spec_cache(self):
        config = ExperimentConfig.from_dict(
            {
                "experiment_name": "tree-spec-cache-test",
                "method": "tree_speculative",
                "method_options": {
                    "tree_spec_decoding_max_depth": 48,
                    "tree_spec_decoding_source_mode": "global_only",
                    "tree_spec_decoding_cache_max_requests": 7,
                },
            }
        )

        with patch(
            "transformers.generation.suffix_tree.SuffixDecodingCache",
            FakeSuffixDecodingCache,
        ):
            resources = TreeSpeculativeMethod().prepare_resources(
                config,
                target_tokenizer=None,
                torch_dtype=None,
                token=None,
                hf_cache_dir="/tmp/hf",
                auto_model_cls=None,
                auto_tokenizer_cls=None,
                cuda_device_count=1,
            )

        cache = resources.extras["suffix_decoding_cache"]
        self.assertEqual(cache.max_depth, 48)
        self.assertEqual(cache.max_cached_requests, 7)
        self.assertEqual(cache.source_mode, "global_only")

    def test_prepare_resources_rejects_invalid_source_mode(self):
        config = ExperimentConfig.from_dict(
            {
                "experiment_name": "tree-spec-invalid-source-mode",
                "method": "tree_speculative",
                "method_options": {
                    "tree_spec_decoding_source_mode": "bad_mode",
                },
            }
        )

        with self.assertRaisesRegex(ValueError, "tree_spec_decoding_source_mode"):
            TreeSpeculativeMethod().prepare_resources(
                config,
                target_tokenizer=None,
                torch_dtype=None,
                token=None,
                hf_cache_dir="/tmp/hf",
                auto_model_cls=None,
                auto_tokenizer_cls=None,
                cuda_device_count=1,
            )

    def test_generation_context_counts_tree_draft_tokens(self):
        method = TreeSpeculativeMethod()
        config = ExperimentConfig.from_dict(
            {
                "experiment_name": "tree-spec-context-test",
                "method": "tree_speculative",
            }
        )

        with patch(
            "transformers.generation.candidate_generator.TreeSpecDecodingCandidateGenerator",
            FakeTreeSpecDecodingCandidateGenerator,
        ):
            with method.generation_context(config, resources=MethodResources()) as tracker:
                generator = FakeTreeSpecDecodingCandidateGenerator()
                generator.tree_draft = SimpleNamespace(token_ids=[11, 12, 13, 14])
                result = generator.update_candidate_strategy(None, None, 3)

                self.assertEqual(tracker.proposed_draft_tokens, 4)
                self.assertEqual(tracker.accepted_draft_tokens, 3)
                self.assertEqual(tracker.speculation_steps, 1)
                self.assertEqual(tracker.acceptance_rate, 0.75)
                self.assertEqual(result["num_matches"], 3)


if __name__ == "__main__":
    unittest.main()
