# LLM Serving Benchmark

This repository is the implementation scaffold for the course project on speculative decoding in `transformers`, with Modal providing GPU hardware.

## Current Scope

The repository currently covers target 2 from the project plan:

- Modal-based benchmark infrastructure
- Persistent model cache and result storage on Modal Volumes
- A baseline autoregressive decoding path
- A hook for Hugging Face draft-model speculative decoding
- Config-driven experiment runs with JSON results

Suffix speculative decoding and tree-based speculative decoding are not implemented yet.

## Repository Layout

- `modal_app.py`: Modal app, GPU worker, and CLI entrypoint
- `src/bench/config.py`: experiment config parsing
- `src/bench/datasets.py`: prompt loading
- `src/bench/metrics.py`: raw-record and summary aggregation
- `src/bench/runner.py`: generation loop and result writing
- `configs/`: example experiment configs
- `data/prompts/`: prompt files for smoke tests

## Local Setup

1. Create a virtual environment and install the local dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Authenticate Modal:

```bash
modal setup
```

3. Optionally set a Hugging Face token for gated models:

```bash
export HF_TOKEN=...
```

## Smoke Test

Run the baseline benchmark on Modal:

```bash
modal run modal_app.py --config-path configs/smoke_gpt2.json --gpu L40S
```

The command prints a JSON blob containing:

- the resolved config
- summary metrics
- the result directory written on the Modal results volume

## Result Format

Each run writes:

- `raw.jsonl`: one record per processed batch
- `summary.json`: aggregate metrics and config metadata

Results are stored on the mounted Modal results volume under:

`/results/{experiment_name}/{method}/{timestamp}`

## Next Implementation Steps

- Add a stable built-in speculative decoding baseline run
- Replace smoke-test prompts with curated benchmark prompt shards
- Add a local script to fetch or inspect result bundles from the Modal volume
- Implement suffix speculative decoding and tree-based speculative decoding behind the same method interface

