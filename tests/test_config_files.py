from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bench.config import load_config


class CheckedInConfigTests(unittest.TestCase):
    def test_all_checked_in_configs_validate(self):
        config_paths = sorted((ROOT / "configs").glob("*.json"))

        self.assertTrue(config_paths, "expected at least one checked-in config")
        for config_path in config_paths:
            with self.subTest(config=config_path.name):
                load_config(config_path)


if __name__ == "__main__":
    unittest.main()
