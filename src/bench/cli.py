from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
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
    compare_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print full subprocess output (progress bars, logs, etc.).",
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


def _format_command(command: list[str]) -> str:
    return " ".join(command)


def _extract_json_result(output: str) -> dict | None:
    """Extract the last JSON object from subprocess output."""
    # Find JSON blocks in the output (the result is printed as a JSON object)
    brace_depth = 0
    json_start = None
    last_json = None

    for i, ch in enumerate(output):
        if ch == "{":
            if brace_depth == 0:
                json_start = i
            brace_depth += 1
        elif ch == "}":
            brace_depth -= 1
            if brace_depth == 0 and json_start is not None:
                candidate = output[json_start : i + 1]
                try:
                    last_json = json.loads(candidate)
                except json.JSONDecodeError:
                    pass
                json_start = None

    return last_json


def _short_method(method: str) -> str:
    """Return a compact display name for a method."""
    return {
        "autoregressive": "vanilla",
        "draft_speculative": "draft-spec",
        "prompt_lookup": "prompt-lookup",
    }.get(method, method)


def _method_label(config: dict) -> str:
    """Return a readable method label, including suffix source-mode ablations."""
    method = _short_method(config.get("method", "?"))
    draft = config.get("draft_model")
    if draft:
        method += f" ({draft.split('/')[-1]})"

    if config.get("method") == "suffix_speculative":
        source_mode = (
            config.get("method_options", {}) or {}
        ).get("suffix_decoding_source_mode", "local_and_global")
        suffix_mode_label = {
            "local_only": " [local]",
            "global_only": " [global]",
            "local_and_global": " [local+global]",
        }.get(source_mode, f" [{source_mode}]")
        method += suffix_mode_label

    return method


_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def _print_table(results: list[dict], config_paths: list[Path]) -> None:
    """Print a clean comparison table from collected results."""
    if not results:
        return

    # Sort results to match the original config order
    # Config stems use underscores, experiment names use hyphens — normalize both
    config_order = {p.stem.replace("_", "-"): i for i, p in enumerate(config_paths)}
    results.sort(
        key=lambda r: config_order.get(
            r.get("config", {}).get("experiment_name", ""), 999
        )
    )

    # ── Header info ──
    first_cfg = results[0].get("config", {})
    model = first_cfg.get("target_model", "?")
    dataset = first_cfg.get("dataset_name", "?")
    limit = first_cfg.get("limit", "?")
    gpu = first_cfg.get("gpu", "?")
    print()
    print(f"  Model: {model}   Dataset: {dataset}   GPU: {gpu}   Prompts: {limit}")
    print()

    # ── Rows ──
    # Columns: Method | Tokens | Tok/s | Latency | Mem (MB) | Draft Acc | Wall (s)
    headers = ["Method", "Tokens", "Tok/s", "Latency", "Peak Mem", "Draft Acc", "Wall"]
    rows: list[list[str]] = []
    for r in results:
        cfg = r.get("config", {})
        s = r.get("summary", {})
        method = _method_label(cfg)

        tokens = s.get("total_generated_tokens", "-")
        tps = s.get("overall_tokens_per_second")
        latency = s.get("total_latency_seconds")
        mem = s.get("peak_memory_allocated_mb")
        acc = s.get("acceptance_rate")
        wall = r.get("client_wall_seconds")

        rows.append([
            method,
            str(tokens) if tokens != "-" else "-",
            f"{tps:.1f}" if isinstance(tps, (int, float)) else "-",
            f"{latency:.2f}s" if isinstance(latency, (int, float)) else "-",
            f"{mem:,.0f} MB" if isinstance(mem, (int, float)) else "-",
            f"{acc:.1%}" if isinstance(acc, (int, float)) else "-",
            f"{wall:.1f}s" if isinstance(wall, (int, float)) else "-",
        ])

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    # Print
    header_line = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    sep_line = "  ".join("─" * col_widths[i] for i in range(len(headers)))
    print(f"  {header_line}")
    print(f"  {sep_line}")
    for row in rows:
        line = "  ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row))
        print(f"  {line}")

    # ── Speedup vs baseline (vanilla / autoregressive) ──
    baseline_tps = None
    for r in results:
        cfg = r.get("config", {})
        if cfg.get("method") == "autoregressive":
            baseline_tps = r.get("summary", {}).get("overall_tokens_per_second")
            break
    # Fallback: use first result as baseline
    if baseline_tps is None:
        baseline_tps = results[0].get("summary", {}).get("overall_tokens_per_second")

    if isinstance(baseline_tps, (int, float)) and baseline_tps > 0 and len(results) > 1:
        print()
        print("  Speedup vs vanilla:")
        for r in results:
            cfg = r.get("config", {})
            if cfg.get("method") == "autoregressive":
                continue
            s = r.get("summary", {})
            method = _method_label(cfg)
            tps = s.get("overall_tokens_per_second")
            if isinstance(tps, (int, float)):
                speedup = tps / baseline_tps
                print(f"    {method}: {speedup:.2f}x")

    speculative_rows: list[list[str]] = []
    speculative_headers = [
        "Method",
        "Steps",
        "Prop/Step",
        "Acc/Step",
        "AccFrac",
        "E2E Tok/s",
    ]
    for r in results:
        cfg = r.get("config", {})
        s = r.get("summary", {})
        steps = s.get("speculation_steps")
        if not isinstance(steps, int) or steps <= 0:
            continue

        method = _method_label(cfg)

        proposed_per_step = s.get("mean_proposed_tokens_per_step")
        accepted_per_step = s.get("mean_accepted_tokens_per_step")
        accepted_fraction = s.get("accepted_tokens_fraction")
        end_to_end_tps = s.get("end_to_end_tokens_per_second")

        speculative_rows.append([
            method,
            str(steps),
            f"{proposed_per_step:.1f}" if isinstance(proposed_per_step, (int, float)) else "-",
            f"{accepted_per_step:.1f}" if isinstance(accepted_per_step, (int, float)) else "-",
            f"{accepted_fraction:.1%}" if isinstance(accepted_fraction, (int, float)) else "-",
            f"{end_to_end_tps:.1f}" if isinstance(end_to_end_tps, (int, float)) else "-",
        ])

    if speculative_rows:
        print()
        print("  Speculation details:")
        spec_col_widths = [len(h) for h in speculative_headers]
        for row in speculative_rows:
            for i, cell in enumerate(row):
                spec_col_widths[i] = max(spec_col_widths[i], len(cell))
        spec_header_line = "  ".join(
            h.ljust(spec_col_widths[i]) for i, h in enumerate(speculative_headers)
        )
        spec_sep_line = "  ".join(
            "─" * spec_col_widths[i] for i in range(len(speculative_headers))
        )
        print(f"  {spec_header_line}")
        print(f"  {spec_sep_line}")
        for row in speculative_rows:
            line = "  ".join(
                cell.ljust(spec_col_widths[i]) for i, cell in enumerate(row)
            )
            print(f"  {line}")

    print()


def run_compare(args: argparse.Namespace) -> int:
    if args.list:
        for name, configs in sorted(list_builtin_suites().items()):
            print(f"{name}:")
            for config in configs:
                print(f"  {config}")
        return 0

    config_paths = resolve_targets(args.targets)
    verbose = getattr(args, "verbose", False)

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

    if args.dry_run:
        for index, command in enumerate(commands, start=1):
            print(f"[{index}/{len(commands)}] {_format_command(command)}")
        return 0

    total = len(commands)
    print(f"Launching {total} benchmark{'s' if total > 1 else ''}...")
    print()

    running: list[dict[str, object]] = []
    failures: list[tuple[int, list[str], int, str]] = []
    collected_results: list[dict] = []

    for index, command in enumerate(commands, start=1):
        log_file = tempfile.TemporaryFile(mode="w+t", encoding="utf-8")
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )
        # Read config to show a nice name
        config_path = config_paths[index - 1]
        try:
            cfg = json.loads(config_path.read_text())
            label = _method_label(cfg)
        except Exception:
            label = config_path.stem

        print(f"  [{index}/{total}] ⏳ {label}")
        running.append(
            {
                "index": index,
                "command": command,
                "process": process,
                "log_file": log_file,
                "label": label,
            }
        )

    print()
    spinner_idx = 0
    pending = running[:]
    while pending:
        still_pending: list[dict[str, object]] = []
        for item in pending:
            process = item["process"]
            assert isinstance(process, subprocess.Popen)
            returncode = process.poll()
            if returncode is None:
                still_pending.append(item)
                continue

            log_file = item["log_file"]
            log_file.seek(0)
            output = log_file.read().rstrip()
            index = int(item["index"])
            command = item["command"]
            label = item["label"]
            assert isinstance(command, list)
            assert isinstance(label, str)

            if returncode == 0:
                print(f"  [{index}/{total}] ✅ {label}")
                result = _extract_json_result(output)
                if result:
                    collected_results.append(result)
                if verbose:
                    print(output)
            else:
                print(f"  [{index}/{total}] ❌ {label} (exit {returncode})")
                failures.append((index, command, returncode, output))
                # Always show output on failure
                print(output)

            log_file.close()

        pending = still_pending
        if pending:
            frame = _SPINNER_FRAMES[spinner_idx % len(_SPINNER_FRAMES)]
            waiting = [str(item["index"]) for item in pending]
            sys.stdout.write(f"\r  {frame} Waiting for run{'s' if len(pending) > 1 else ''} {', '.join(waiting)}...")
            sys.stdout.flush()
            spinner_idx += 1
            time.sleep(0.2)

    # Clear spinner line
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

    # ── Summary table ──
    if collected_results:
        _print_table(collected_results, config_paths)

    if failures:
        print("Failures:", file=sys.stderr)
        for index, command, returncode, output in failures:
            print(
                f"  [{index}/{total}] {_format_command(command)} (exit {returncode})",
                file=sys.stderr,
            )
        return failures[0][2]

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
