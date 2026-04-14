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

Run the full default comparison set:

```bash
modal run modal_app.py --config-path configs/wmt14_qwen8b_vanilla_fr_en.json --gpu L40S
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

Observed behavior:

- prompt lookup is currently the clearest win on the retained benchmark sets
- draft-model speculation is supported, but can be slower than vanilla for the current model pairs and prompts

## How To Run Each Mode

Autoregressive baseline:

```bash
modal run modal_app.py --config-path configs/wmt14_qwen8b_vanilla_fr_en.json --gpu L40S
```

Draft-model speculation:

```bash
modal run modal_app.py --config-path configs/wmt14_qwen8b_draft_fr_en.json --gpu L40S
```

Prompt lookup:

```bash
modal run modal_app.py --config-path configs/wmt14_qwen8b_prompt_lookup_fr_en.json --gpu L40S
```

Override the prompt count for a quick smoke run:

```bash
modal run modal_app.py --config-path configs/wmt14_qwen8b_vanilla_fr_en.json --gpu L40S --limit 1
```

## How To Change Experiments

The benchmark entrypoint is always `modal_app.py`, and nearly all experiment changes should be made in a JSON config under `configs/`.

Fields you will usually edit:

- `method`: `autoregressive`, `draft_speculative`, or `prompt_lookup`
- `target_model`: base model to benchmark
- `draft_model`: assistant model for `draft_speculative`
- `prompt_source`: `translation_hf`, `wildchat_hf`, `alpaca_hf`, `xsum_hf`, or `local_jsonl`
- `dataset_name`, `dataset_config_name`, `dataset_split`: Hugging Face dataset selection
- `dataset_source_language`, `dataset_target_language`: required for `translation_hf`
- `dataset_min_user_chars`, `dataset_max_user_chars`, `dataset_max_messages`: prompt filtering
- `max_new_tokens`: decode length cap
- `limit`: number of prompts to run
- `prompt_lookup_num_tokens`: lookup window size for `prompt_lookup`
- `torch_dtype`: `float16`, `bfloat16`, or `float32`
- `gpu`: intended Modal GPU type recorded in the config metadata
- `enable_thinking`: disable this for cleaner latency comparisons on Qwen runs

Rules worth keeping in mind:

- `draft_speculative` requires `draft_model`
- `translation_hf` requires both `dataset_source_language` and `dataset_target_language`
- keep `batch_size=1` for draft-model speculative decoding
- use `separate_assistant_gpu=true` only when you intentionally want the draft model on a second GPU

## Recommended Workflows

To compare decoding methods fairly:

- keep the same prompt slice, `limit`, `max_new_tokens`, and `torch_dtype`
- run vanilla first, then draft or prompt lookup with the matching dataset config
- compare methods using the `summary.json` files written under the same benchmark family

For the current project target, the cleanest comparison is:

```bash
modal run modal_app.py --config-path configs/wmt14_qwen8b_vanilla_fr_en.json --gpu L40S
modal run modal_app.py --config-path configs/wmt14_qwen8b_draft_fr_en.json --gpu L40S
modal run modal_app.py --config-path configs/wmt14_qwen8b_prompt_lookup_fr_en.json --gpu L40S
```

## Result Format

Each run writes:

- `raw.jsonl`: one record per processed batch
- `summary.json`: aggregate metrics and config metadata

Results are stored on the mounted Modal results volume under:

`/results/{experiment_name}/{method}/{timestamp}`

The CLI prints a JSON object with the resolved config, summary metrics, and the result directory.

Metrics to watch:

- `overall_tokens_per_second`: primary throughput metric from `summary.json`
- `total_latency_seconds`: end-to-end generation time across all batches
- `total_generated_tokens`: total generated tokens
- `acceptance_rate`: only meaningful for `draft_speculative`; higher is usually better, but it does not guarantee a speedup

To inspect a stored result locally through Modal:

```bash
modal volume get llm-bench-results /results/<experiment>/<method>/<timestamp>/summary.json
```

## Next Implementation Steps

- Add a local script to fetch or inspect result bundles from the Modal volume
- Implement suffix speculative decoding and tree-based speculative decoding behind the same method interface
