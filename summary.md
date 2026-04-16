# Benchmark Summary

## Current usable result

Use the completed 2026-04-16 `./scripts/bench compare default` run as the main reported result.

- Date: 2026-04-16
- GPU: L40S
- Workload: WMT14 French-to-English translation slice, 50 prompts
- Model: `Qwen/Qwen3-8B`

## Ranking

1. `suffix_speculative`: 55.00 tokens/s, 883.29 s total latency
2. `prompt_lookup`: 45.00 tokens/s, 1104.04 s total latency
3. `autoregressive`: 25.70 tokens/s, 1967.46 s total latency
4. `draft_speculative`: 17.30 tokens/s, 2841.71 s total latency, 47.8% draft-token acceptance

## Important takeaways

- Suffix decoding is the clear winner on the default suite, at about 2.14x the throughput of vanilla decoding.
- Suffix decoding outperforms prompt lookup by about 22% on throughput (55.0 vs 45.0 tok/s).
- Prompt lookup remains strong at about 1.75x vanilla throughput.
- Draft-model speculation is substantially worse than vanilla on this run, at about 0.67x vanilla throughput.
- Peak GPU memory stayed in the same range for all methods, roughly 15.8 GB to 17.1 GB.

## Secondary result

WildChat translation run on 2026-04-16 with `limit=50`.

- GPU: L40S
- Workload: WildChat translation slice, 50 prompts
- Model: `Qwen/Qwen3-8B`

### Ranking

1. `suffix_speculative`: 64.70 tokens/s, 121.37 s total latency, 25.5% draft-token acceptance
2. `prompt_lookup`: 60.20 tokens/s, 123.98 s total latency
3. `autoregressive`: 26.00 tokens/s, 270.45 s total latency
4. `draft_speculative`: 25.50 tokens/s, 248.01 s total latency, 36.5% draft-token acceptance

### Important takeaways

- Suffix decoding is the winner on WildChat too, at about 2.49x the throughput of vanilla decoding.
- Suffix decoding edges out prompt lookup (64.7 vs 60.2 tok/s, about 7% faster).
- Draft-model speculation is roughly on par with vanilla on this run, at about 0.98x vanilla throughput.

## Tertiary result

WildChat code run on 2026-04-16 with `limit=50`.

- GPU: L40S
- Workload: WildChat coding prompts slice, 50 prompts
- Model: `Qwen/Qwen3-8B`

### Ranking

1. `suffix_speculative`: 46.60 tokens/s, 966.63 s total latency, 9.0% draft-token acceptance
2. `prompt_lookup`: 45.00 tokens/s, 1004.81 s total latency
3. `autoregressive`: 38.20 tokens/s, 1167.45 s total latency
4. `draft_speculative`: 13.70 tokens/s, 3288.46 s total latency, 38.1% draft-token acceptance

### Important takeaways

- Suffix decoding still wins on code prompts, but the margin narrows: 1.22x vs vanilla.
- Prompt lookup is close behind at 1.18x vs vanilla.
- Code generation has less repetition than translation, reducing the advantage of suffix-based methods.
- Draft-model speculation performs worst here at 0.36x vanilla throughput.
