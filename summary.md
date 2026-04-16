# Benchmark Summary

## Current usable result

Use the completed 2026-04-16 `./scripts/bench compare default` run as the main reported result.

- Date: 2026-04-16
- GPU: L40S
- Workload: WMT14 French-to-English translation slice, 50 prompts
- Model: `Qwen/Qwen3-8B`

## Ranking

1. `prompt_lookup`: 67.29 tokens/s, 737.57 s total latency
2. `autoregressive`: 38.27 tokens/s, 1322.38 s total latency
3. `draft_speculative`: 16.99 tokens/s, 2893.79 s total latency, 47.83% draft-token acceptance

## Important takeaways

- Prompt lookup is the clear winner on the default suite, at about 1.76x the throughput of vanilla decoding.
- Draft-model speculation is substantially worse than vanilla on this run, at about 0.44x vanilla throughput.
- Peak GPU memory stayed in the same range for all three runs, roughly 15.8 GB to 17.4 GB.

## Secondary result

WildChat translation run on 2026-04-16 with `limit=50`.

- GPU: L40S
- Workload: WildChat translation slice, 50 prompts
- Model: `Qwen/Qwen3-8B`

### Ranking

1. `prompt_lookup`: 54.46 tokens/s, 137.05 s total latency
2. `autoregressive`: 25.77 tokens/s, 272.76 s total latency
3. `draft_speculative`: 13.92 tokens/s, 454.98 s total latency, 36.47% draft-token acceptance

### Important takeaways

- Prompt lookup is the clear winner on WildChat too, at about 2.11x the throughput of vanilla decoding.
- Draft-model speculation is worse than vanilla on this run, at about 0.54x vanilla throughput.
