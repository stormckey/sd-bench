from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bench.datasets import _sample_records, load_jsonl_prompts


class DatasetSamplingTests(unittest.TestCase):
    def test_jsonl_sampling_is_seeded_and_not_prefix_based(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "prompts.jsonl"
            records = [
                {"id": f"prompt-{idx}", "prompt": f"Prompt {idx}"}
                for idx in range(20)
            ]
            path.write_text(
                "\n".join(json.dumps(record) for record in records),
                encoding="utf-8",
            )

            sampled_a = load_jsonl_prompts(path, limit=5, seed=1234)
            sampled_b = load_jsonl_prompts(path, limit=5, seed=1234)
            sampled_c = load_jsonl_prompts(path, limit=5, seed=4321)

            ids_a = [record["id"] for record in sampled_a]
            ids_b = [record["id"] for record in sampled_b]
            ids_c = [record["id"] for record in sampled_c]

            self.assertEqual(ids_a, ids_b)
            self.assertNotEqual(ids_a, [f"prompt-{idx}" for idx in range(5)])
            self.assertNotEqual(ids_a, ids_c)

    def test_sample_records_uses_stable_shuffled_prefixes(self):
        prompts = [
            {"id": f"prompt-{idx}", "prompt": f"Prompt {idx}"}
            for idx in range(40)
        ]

        sampled_10 = _sample_records(prompts, limit=10, seed=1234)
        sampled_15 = _sample_records(prompts, limit=15, seed=1234)
        sampled_20 = _sample_records(prompts, limit=20, seed=1234)

        ids_10 = [record["id"] for record in sampled_10]
        ids_15 = [record["id"] for record in sampled_15]
        ids_20 = [record["id"] for record in sampled_20]

        self.assertEqual(ids_10, ids_15[:10])
        self.assertEqual(ids_15, ids_20[:15])


if __name__ == "__main__":
    unittest.main()
