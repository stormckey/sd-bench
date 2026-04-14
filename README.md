# LLM Serving Benchmark

This repository is the implementation scaffold for the course project on speculative decoding in `transformers`, with Modal providing GPU hardware.

## Current Scope

The repository currently covers target 2 from the project plan:

- Modal-based benchmark infrastructure
- Persistent model cache and result storage on Modal Volumes
- A baseline autoregressive decoding path
- A working Hugging Face draft-model speculative decoding path
- Config-driven experiment runs with JSON results
- Open-corpus prompt loading from Hugging Face datasets

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
pip install git+https://github.com/ErwinZhou/transformers.git
```

This project uses a custom `transformers` fork for benchmark runs:

- `https://github.com/ErwinZhou/transformers`

2. Authenticate Modal:

```bash
modal setup
```

3. Optionally set a Hugging Face token for gated models:

```bash
export HF_TOKEN=...
```

## Default Benchmark

Run the default baseline benchmark on Modal:

```bash
modal run modal_app.py --gpu L40S
```

The command prints a JSON blob containing:

- the resolved config
- summary metrics
- the result directory written on the Modal results volume

Current default baseline:

- target model: `Qwen/Qwen3-8B`
- prompt source: `wmt14` French-to-English
- config: `configs/wmt14_qwen8b_vanilla_fr_en.json`

Recommended real-data comparisons:

```bash
modal run modal_app.py --config-path configs/wmt14_qwen8b_draft_fr_en.json --gpu L40S
modal run modal_app.py --config-path configs/wmt14_qwen8b_prompt_lookup_fr_en.json --gpu L40S
```

## Additional Examples

Run the WildChat translation slice:

```bash
modal run modal_app.py --config-path configs/wildchat_qwen8b_vanilla_translate.json --limit 1
```

Run draft-model speculation on the same slice:

```bash
modal run modal_app.py --config-path configs/wildchat_qwen8b_draft_translate.json --limit 1
```

Run prompt lookup on the same slice:

```bash
modal run modal_app.py --config-path configs/wildchat_qwen8b_prompt_lookup_translate.json --limit 1
```

Run the synthetic repetition prompts:

```bash
modal run modal_app.py --config-path configs/easy_qwen8b_vanilla_obvious_long.json --limit 1
modal run modal_app.py --config-path configs/easy_qwen8b_draft_obvious_long.json --limit 1
modal run modal_app.py --config-path configs/easy_qwen8b_prompt_lookup_obvious_long.json --limit 1
```

Current comparison target:

- target model: `Qwen/Qwen3-8B`
- draft model: `Qwen/Qwen3-0.6B`
- prompt source: `wmt14` French-to-English
- supported benchmark sets:
  - `wmt14` vanilla / draft / prompt lookup
  - WildChat translation vanilla / draft / prompt lookup
  - easy repetition vanilla / draft / prompt lookup

Current limitation:

- keep `batch_size=1` for draft-model speculative decoding

## Result Format

Each run writes:

- `raw.jsonl`: one record per processed batch
- `summary.json`: aggregate metrics and config metadata

Results are stored on the mounted Modal results volume under:

`/results/{experiment_name}/{method}/{timestamp}`

## Next Implementation Steps

- Add a local script to fetch or inspect result bundles from the Modal volume
- Implement suffix speculative decoding and tree-based speculative decoding behind the same method interface
