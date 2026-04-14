from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from bench.suites import ROOT, list_builtin_suites, resolve_suite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare_parser = subparsers.add_parser(
        "compare",
        help="Run a named benchmark suite or an explicit list of config files.",
    )
    compare_parser.add_argument(
        "targets",
        nargs="*",
        help="Suite name such as 'wmt14' or explicit config paths.",
    )
    compare_parser.add_argument(
        "--gpu",
        default="L40S",
        help="GPU type to pass through to modal_app.py.",
    )
    compare_parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Override the prompt limit for each config. Use 0 to keep config defaults.",
    )
    compare_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved Modal commands without running them.",
    )
    compare_parser.add_argument(
        "--list",
        action="store_true",
        help="List the built-in benchmark suites.",
    )

    return parser


def resolve_targets(targets: list[str]) -> list[Path]:
    if not targets:
        return resolve_suite("default")

    if len(targets) == 1 and targets[0] in list_builtin_suites():
        return resolve_suite(targets[0])

    resolved: list[Path] = []
    for target in targets:
        path = Path(target)
        if not path.is_absolute():
            path = (ROOT / path).resolve()
        if not path.exists():
            available = ", ".join(sorted(list_builtin_suites()))
            raise FileNotFoundError(
                f"Unknown config or suite '{target}'. Known suites: {available}"
            )
        resolved.append(path)
    return resolved


def modal_executable() -> list[str]:
    modal_path = shutil.which("modal")
    if modal_path:
        return [modal_path]
    return [sys.executable, "-m", "modal"]


def run_compare(args: argparse.Namespace) -> int:
    if args.list:
        for name, configs in sorted(list_builtin_suites().items()):
            print(f"{name}:")
            for config in configs:
                print(f"  {config}")
        return 0

    config_paths = resolve_targets(args.targets)

    commands: list[list[str]] = []
    for config_path in config_paths:
        command = [
            *modal_executable(),
            "run",
            str(ROOT / "modal_app.py"),
            "--config-path",
            str(config_path),
            "--gpu",
            args.gpu,
        ]
        if args.limit > 0:
            command.extend(["--limit", str(args.limit)])
        commands.append(command)

    for index, command in enumerate(commands, start=1):
        print(f"[{index}/{len(commands)}] {' '.join(command)}")
        if args.dry_run:
            continue
        completed = subprocess.run(command, cwd=ROOT)
        if completed.returncode != 0:
            return completed.returncode

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "compare":
        return run_compare(args)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
