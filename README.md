# LLM Serving Benchmark

A Modal-based benchmark harness for comparing autoregressive decoding, prompt lookup, draft-model speculation, and suffix/tree speculative decoding on realistic language-model workloads.

- **Transformers implementation:** [`stormckey/transformers`](https://github.com/stormckey/transformers/tree/suffix-decoding)
- **Detailed historical results:** [`summary.md`](summary.md)
- **Project poster:** [`assets/index.pdf`](assets/index.pdf)

## What It Evaluates

The harness provides a common configuration, dataset, execution, and metrics layer for:

- `autoregressive`
- `draft_speculative`
- `prompt_lookup`
- `suffix_speculative`
- `tree_speculative`

Runs execute on Modal GPUs, load prompts from Hugging Face datasets or local JSONL, and write per-batch `raw.jsonl` records plus an aggregate `summary.json`. The primary throughput metric is `overall_tokens_per_second`; speculative methods also report proposed and accepted draft tokens.

## Reproducible Transformers Revisions

The benchmark installs the local checkout at `./transformers`, rather than the PyPI release. Use the setup helper to select the implementation required by an experiment:

| Profile | Branch | Pinned revision | Scope |
|---|---|---|---|
| `suffix` | [`suffix-decoding`](https://github.com/stormckey/transformers/tree/suffix-decoding) | [`76d60fa`](https://github.com/stormckey/transformers/commit/76d60fa5751e4d66423523b9d78680743ff666fd) | Suffix tree, candidate generator, generation integration, and cross-request cache |
| `tree-spec` | [`tree-spec-decoding`](https://github.com/stormckey/transformers/tree/tree-spec-decoding) | [`c66e13b`](https://github.com/stormckey/transformers/commit/c66e13b7ee10b7d630c4d5e2319b1f382e00cd2a) | Team-attributed tree-spec extension and incremental verifier |

```bash
# Default suffix-decoding experiments
./scripts/setup_transformers suffix

# Tree-spec experiments instead
./scripts/setup_transformers tree-spec
```

The helper clones the selected branch and checks out the exact detached revision. It refuses to overwrite an existing `./transformers` directory.

## Historical Benchmark Snapshot

The strongest directly comparable retained run is the April 16, 2026 default suite on an NVIDIA L40S using `Qwen/Qwen3-8B` and 50 WMT14 French-to-English prompts:

| Method | Throughput | Speedup vs. autoregressive |
|---|---:|---:|
| `autoregressive` | 25.7 tok/s | 1.00× |
| `draft_speculative` | 17.3 tok/s | 0.67× |
| `prompt_lookup` | 45.0 tok/s | 1.75× |
| `suffix_speculative` | **55.0 tok/s** | **2.14×** |

These are historical project results transcribed from [`summary.md`](summary.md), not a fresh rerun. The original raw Modal artifacts were not committed, so this table should not be treated as independently reproduced. The repository retains larger sweeps, cache-mode ablations, acceptance metrics, memory measurements, and workload-specific results in the detailed summary.

## Quick Start

Requirements:

- Python 3.11+
- Git
- A Modal account for GPU runs

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
./scripts/setup_transformers suffix
modal setup
```

Optional for gated Hugging Face models:

```bash
export HF_TOKEN=...
```

Run the default comparison suite on an L40S:

```bash
./scripts/bench compare default
```

Run one configuration directly:

```bash
modal run modal_app.py \
  --config-path configs/wmt14_qwen8b_suffix_fr_en.json \
  --gpu L40S
```

> Modal commands provision remote GPU resources and may incur charges. The local checks below do not run a model or require a GPU.

## No-GPU Validation

Validate all checked-in experiment configs and the deterministic dataset sampling logic:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The adapter tests inject minimal mock Transformers modules, so this suite does not install the model library, download weights, or require CUDA. It validates configuration loading, deterministic dataset sampling, method registration, generation arguments, cache construction, and speculation accounting; it does not perform inference or verify the reported throughput.

## Comparison Suites

```bash
# Default WMT14 comparison
./scripts/bench compare default

# One-prompt smoke test of a suite
./scripts/bench compare wildchat --limit 1

# List all built-in suites
./scripts/bench compare --list
```

Built-in suites cover:

- WMT14 French-to-English translation
- WildChat translation and code prompts
- SWE-bench code-generation tasks
- Spider text-to-SQL
- TerminalBench command-line tasks

Example configurations live in [`configs/`](configs/). Most experiment changes only require editing a JSON file; common fields include `method`, `target_model`, `draft_model`, `prompt_source`, `max_new_tokens`, `limit`, `torch_dtype`, and method-specific options.

## Outputs

Each run writes:

- `raw.jsonl`: per-batch latency, token, memory, and speculation records
- `summary.json`: aggregate metrics and resolved configuration

Modal stores results under:

```text
/results/{experiment_name}/{method}/{timestamp}
```

For comparisons, retain the raw artifacts alongside the exact Transformers revision, configuration, GPU type, prompt seed, and prompt limit.

## Repository Layout

- `modal_app.py`: Modal entrypoint and remote environment
- `configs/`: experiment configurations
- `src/bench/`: configuration, datasets, method adapters, runner, and metrics
- `scripts/bench`: comparison CLI wrapper
- `tests/`: no-GPU config, dataset, and adapter tests
- `summary.md`: historical experiment notes and result tables
- `assets/`, `figures/`, `poster/`: project presentation artifacts

## Attribution

The Git history preserves individual authorship across the benchmark harness, poster work, suffix-decoding implementation, and team tree-spec extension. The personal Transformers fork mirrors team-authored branches without rewriting their commits; the project README distinguishes Chenhao Gao's suffix-decoding implementation history from later team contributions.
