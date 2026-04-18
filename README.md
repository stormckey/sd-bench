# LLM Serving Benchmark

Run Modal-based benchmarks for LLM decoding methods and compare throughput across configs.

Supported methods:

- `autoregressive`
- `draft_speculative`
- `prompt_lookup`
- `suffix`

The benchmark runner executes on Modal GPUs, reads prompts from Hugging Face datasets or local JSONL, and writes `raw.jsonl` plus `summary.json` for each run.

## Quick Start

Place the Transformers fork at `./transformers` before running benchmarks. `modal_app.py` mounts that exact repo-root directory into the Modal image and installs it from there.

Current test checkout:

```bash
git clone https://github.com/ErwinZhou/transformers.git transformers
cd transformers
git checkout suffix-feat
cd ..
```

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
modal setup
```

Optional for gated Hugging Face models:

```bash
export HF_TOKEN=...
```

Run the default benchmark:

```bash
modal run modal_app.py --gpu L40S
```

This prints a JSON result with the resolved config, summary metrics, and result directory.

## Common Commands

Run the default comparison suite:

```bash
./scripts/bench compare default
```

Run only the WMT14 comparison:

```bash
./scripts/bench compare wmt14
```

Smoke-test a suite on one prompt:

```bash
./scripts/bench compare wildchat --limit 1
```

List built-in suites:

```bash
./scripts/bench compare --list
```

Run one config directly:

```bash
modal run modal_app.py --config-path configs/wmt14_qwen8b_draft_fr_en.json --gpu L40S
```

## Built-In Suites

- `default` / `wmt14`: WMT14 French-to-English configs
- `wildchat`: WildChat translation slice
- `swebench`: SWE-bench code generation tasks
- `terminalbench`: TerminalBench command-line tasks

Example configs live in `configs/`.

## Editing Experiments

Most changes happen in a JSON config under `configs/`.

Fields you will usually care about:

- `method`
- `target_model`
- `draft_model` for `draft_speculative`
- `prompt_source`
- `max_new_tokens`
- `limit`
- `torch_dtype`
- dataset fields such as `dataset_name`, `dataset_split`, and translation languages

Useful rules:

- `draft_speculative` requires `draft_model`
- `translation_hf` requires source and target languages
- keep `batch_size=1` for `draft_speculative`

## Results

Each run writes:

- `raw.jsonl`: per-batch records
- `summary.json`: aggregate metrics and config metadata

Results are stored on the Modal results volume under:

```text
/results/{experiment_name}/{method}/{timestamp}
```

The main metric to compare is `overall_tokens_per_second`.

## Files You'll Touch

- `modal_app.py`: Modal entrypoint
- `configs/`: experiment configs
- `src/bench/`: config loading, datasets, methods, runner, metrics
- `data/prompts/`: local prompt files for smoke tests

## Notes

- Benchmark workers install the vendored local checkout at `./transformers`, not PyPI.
- The current test checkout tracks `https://github.com/ErwinZhou/transformers.git` on branch `suffix-feat` at commit `acc6fa047f42551cbc9ee8a22629b532608fd7fa`.
- Prompt lookup currently shows the clearest speedup on the retained benchmark sets
- Draft-model speculation is supported, but may be slower than vanilla for some model pairs
