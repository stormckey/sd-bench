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


# Test on 4/20/2026
## WMT14 Benchmark Comparison

### Experiment Setup

- **Model:** `Qwen/Qwen3-8B`
- **Dataset:** `wmt14`
- **GPU:** `L40S`
- **Prompts:** `10`

### Results

| Method | Tokens | Tok/s | Latency (s) | Peak Mem (MB) | Draft Acc | Wall Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| vanilla | 10,240 | 38.3 | 267.25 | 15,795 | - | 311.0 |
| draft-spec (`Qwen3-0.6B`) | 9,674 | 34.2 | 283.18 | 17,112 | 46.4% | 344.6 |
| prompt-lookup | 10,244 | 67.2 | 152.35 | 15,821 | - | 176.6 |
| suffix_speculative | 10,240 | 77.6 | 132.00 | 15,828 | 20.0% | 152.0 |

| Method | Steps | Prop/Step | Acc/Step | AccFrac | E2E Tok/s |
|---|---:|---:|---:|---:|---:|
| draft-spec (`Qwen3-0.6B`) | 1,590 | 11.0 | 5.1 | 83.6% | 28.1 |
| suffix_speculative | 3,429 | 8.8 | 1.8 | 59.0% | 67.4 |

### Speedup vs. Vanilla

| Method | Speedup |
|---|---:|
| draft-spec (`Qwen3-0.6B`) | 0.89× |
| prompt-lookup | 1.75× |
| suffix_speculative | 2.02× |

### Summary

- **suffix_speculative** achieved the best overall performance at **77.6 tok/s**, delivering a **2.02× speedup** over vanilla.
- **prompt-lookup** also showed strong gains, reaching **67.2 tok/s** with a **1.75× speedup**.
- **draft-spec (`Qwen3-0.6B`)** slightly underperformed vanilla on this benchmark, reaching **34.2 tok/s** and **0.89×** relative speed.
- **draft-spec** achieved a higher **draft accuracy** of **46.4%**, compared with **20.0%** for **suffix_speculative**, but this did not translate into better end-to-end throughput.
- In speculation details:
  - **draft-spec** achieved **83.6% accepted fraction** with **28.1 E2E tok/s**
  - **suffix_speculative** achieved **59.0% accepted fraction** with **67.4 E2E tok/s**
- For **WMT14 (`--limit 10`)**, **suffix_speculative** appears to provide the best practical tradeoff among the tested methods.

---

## WildChat Translate Benchmark Comparison

### Experiment Setup

- **Model:** `Qwen/Qwen3-8B`
- **Dataset:** `allenai/WildChat`
- **GPU:** `L40S`
- **Prompts:** `10`
- **Task:** `translate`

### Results

| Method | Tokens | Tok/s | Latency (s) | Peak Mem (MB) | Draft Acc | Wall Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| vanilla | 1,237 | 25.3 | 48.83 | 15,780 | - | 112.1 |
| draft-spec (`Qwen3-0.6B`) | 758 | 30.5 | 24.87 | 16,985 | 43.9% | 92.3 |
| prompt-lookup | 1,249 | 86.4 | 14.45 | 15,804 | - | 78.6 |
| suffix_speculative | 1,237 | 111.5 | 11.10 | 15,811 | 61.9% | 55.0 |

| Method | Steps | Prop/Step | Acc/Step | AccFrac | E2E Tok/s |
|---|---:|---:|---:|---:|---:|
| draft-spec (`Qwen3-0.6B`) | 166 | 8.1 | 3.6 | 78.1% | 8.2 |
| suffix_speculative | 171 | 8.3 | 5.1 | 71.1% | 22.5 |

### Speedup vs. Vanilla

| Method | Speedup |
|---|---:|
| draft-spec (`Qwen3-0.6B`) | 1.20× |
| prompt-lookup | 3.41× |
| suffix_speculative | 4.40× |

### Summary

- **suffix_speculative** achieved the best overall performance at **111.5 tok/s**, delivering a **4.40× speedup** over vanilla.
- **prompt-lookup** also performed strongly at **86.4 tok/s**, with a **3.41× speedup**.
- **draft-spec (`Qwen3-0.6B`)** improved over vanilla on this benchmark, reaching **30.5 tok/s** and **1.20×** relative speed.
- **suffix_speculative** also achieved the highest **draft accuracy** among speculative methods at **61.9%**, compared with **43.9%** for **draft-spec**.
- In speculation details:
  - **draft-spec** achieved **78.1% accepted fraction** with **8.2 E2E tok/s**
  - **suffix_speculative** achieved **71.1% accepted fraction** with **22.5 E2E tok/s**
- For **WildChat translate (`--limit 10`)**, **suffix_speculative** delivers the strongest speedup and the best practical overall performance.

---

## WildChat Code Benchmark Comparison

### Experiment Setup

- **Model:** `Qwen/Qwen3-8B`
- **Dataset:** `allenai/WildChat`
- **GPU:** `L40S`
- **Prompts:** `10`
- **Task:** `code`

### Results

| Method | Tokens | Tok/s | Latency (s) | Peak Mem (MB) | Draft Acc | Wall Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| vanilla | 8,724 | 38.3 | 228.07 | 15,794 | - | 257.1 |
| draft-spec (`Qwen3-0.6B`) | 9,059 | 14.0 | 645.45 | 17,109 | 39.9% | 692.0 |
| prompt-lookup | 8,972 | 52.9 | 169.60 | 15,820 | - | 191.5 |
| suffix_speculative | 8,892 | 46.8 | 189.89 | 15,827 | 7.6% | 216.3 |

| Method | Steps | Prop/Step | Acc/Step | AccFrac | E2E Tok/s |
|---|---:|---:|---:|---:|---:|
| draft-spec (`Qwen3-0.6B`) | 2,073 | 8.4 | 3.4 | 77.1% | 13.1 |
| suffix_speculative | 4,285 | 8.3 | 0.6 | 30.3% | 41.1 |

### Speedup vs. Vanilla

| Method | Speedup |
|---|---:|
| draft-spec (`Qwen3-0.6B`) | 0.37× |
| prompt-lookup | 1.38× |
| suffix_speculative | 1.22× |

### Summary

- **prompt-lookup** achieved the best overall performance at **52.9 tok/s**, delivering a **1.38× speedup** over vanilla.
- **suffix_speculative** provided a smaller improvement to **46.8 tok/s**, corresponding to a **1.22× speedup**.
- **draft-spec (`Qwen3-0.6B`)** significantly underperformed vanilla on this benchmark, reaching only **14.0 tok/s** and **0.37×** relative speed.
- Although **draft-spec** achieved a moderate **draft accuracy** of **39.9%**, its overhead was too high to produce end-to-end gains.
- In speculation details:
  - **draft-spec** achieved **77.1% accepted fraction** with **13.1 E2E tok/s**
  - **suffix_speculative** achieved **30.3% accepted fraction** with **41.1 E2E tok/s**
- For **WildChat code (`--limit 10`)**, **prompt-lookup** appears to offer the best practical tradeoff among the tested methods.

---

## SWE-bench Benchmark Comparison

**Command**
```bash
PYTHONPATH=src python -m bench.cli compare swebench --limit 10
```

### Experiment Setup

- **Model:** `Qwen/Qwen3-8B`
- **Dataset:** `princeton-nlp/SWE-bench`
- **GPU:** `L40S`
- **Prompts:** `10`

### Results

| Method | Tokens | Tok/s | Latency (s) | Peak Mem (MB) | Draft Acc | Wall Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| vanilla | 20,480 | 37.3 | 549.74 | 16,733 | - | 588.4 |
| draft-spec (`Qwen3-0.6B`) | 20,480 | 27.2 | 753.25 | 18,561 | 83.6% | 790.0 |
| prompt-lookup | 20,492 | 46.1 | 444.58 | 16,734 | - | 467.5 |
| suffix_speculative | 20,480 | 92.0 | 222.69 | 16,735 | 29.5% | 246.4 |

| Method | Steps | Prop/Step | Acc/Step | AccFrac | E2E Tok/s |
|---|---:|---:|---:|---:|---:|
| draft-spec (`Qwen3-0.6B`) | 2,073 | 10.6 | 8.9 | 89.9% | 25.9 |
| suffix_speculative | 5,417 | 9.0 | 2.7 | 70.3% | 83.1 |

### Speedup vs. Vanilla

| Method | Speedup |
|---|---:|
| draft-spec (`Qwen3-0.6B`) | 0.73× |
| prompt-lookup | 1.24× |
| suffix_speculative | 2.47× |

---

## Tree-Spec Benchmark Sweep

### Experiment Setup

- **Date:** `2026-04-28`
- **Method:** `tree-spec [local+global]`
- **Model:** `Qwen/Qwen3-8B`
- **GPU:** `L40S`
- **Prompts per config:** `50`
- **Branch factor:** `2`

### Results

| Workload | Tokens | Tok/s | Latency (s) | Peak Mem (MB) | Draft Acc | Steps | Prop/Step | Acc/Step | AccFrac | E2E Tok/s | Wall Time (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| WMT14 | 51,200 | 67.0 | 764.48 | 15,889 | 18.7% | 17,862 | 9.8 | 1.8 | 63.8% | 64.8 | 790.0 |
| WildChat translate | 38,070 | 63.9 | 596.11 | 15,834 | 17.8% | 13,644 | 9.8 | 1.7 | 62.5% | 54.2 | 702.0 |
| WildChat code | 51,200 | 62.8 | 815.19 | 15,845 | 18.5% | 17,964 | 9.8 | 1.8 | 63.5% | 59.7 | 858.0 |
| SWE-bench | 102,400 | 155.5 | 658.36 | 17,477 | 71.5% | 12,738 | 9.8 | 7.0 | 87.2% | 147.9 | 692.3 |
| Spider | 25,600 | 64.3 | 398.37 | 15,952 | 12.7% | 11,355 | 9.6 | 1.2 | 53.8% | 58.0 | 441.7 |
| TerminalBench | 51,200 | 59.2 | 865.39 | 17,383 | 16.0% | 19,790 | 9.9 | 1.6 | 60.8% | 57.9 | 885.0 |

### Summary

- At `limit: 50`, tree-spec no longer shows the very high throughput from the earlier short smoke runs on most workloads. **SWE-bench** is now the clear best case at **155.5 tok/s**, while the other five workloads cluster much lower around **59.2 to 67.0 tok/s**.
- **SWE-bench** is also the only workload with genuinely strong speculative efficiency in the longer runs, reaching **71.5% draft acceptance**, **7.0 accepted tokens per step**, and **87.2% accepted-token fraction**.
- The other workloads all settle into a similar low-acceptance regime: roughly **12.7% to 18.7% draft acceptance**, about **1.2 to 1.8 accepted tokens per step**, and only **53.8% to 63.8% accepted-token fraction**.
- **Spider** remains the weakest case by acceptance quality at **12.7% draft acceptance** and **1.2 accepted tokens per step**, though its raw throughput (**64.3 tok/s**) ends up similar to WMT14 and WildChat once the prompt count is larger.
- Peak memory stays near **15.8 GB** for WMT14, WildChat translate, WildChat code, and Spider, but rises substantially for **SWE-bench** (**17.5 GB**) and **TerminalBench** (**17.4 GB**) in the longer runs.

### Summary

- **suffix_speculative** achieved the best overall performance at **92.0 tok/s**, delivering a **2.47× speedup** over vanilla.
- **prompt-lookup** provided a moderate improvement to **46.1 tok/s**, with a **1.24× speedup**.
- **draft-spec (`Qwen3-0.6B`)** underperformed vanilla on this benchmark, reaching **27.2 tok/s** and only **0.73×** relative speed.
- **draft-spec** had the highest **draft accuracy** at **83.6%**, but this did not translate into end-to-end throughput gains.
- In speculation details:
  - **draft-spec** achieved **89.9% accepted fraction** with **25.9 E2E tok/s**
  - **suffix_speculative** achieved **70.3% accepted fraction** with **83.1 E2E tok/s**
- **suffix_speculative** appears to provide the best practical tradeoff for SWE-bench among the tested methods.

---

## Spider Benchmark Comparison

**Command**
```bash
PYTHONPATH=src python -m bench.cli compare spider --limit 10
```

### Experiment Setup

- **Model:** `Qwen/Qwen3-8B`
- **Dataset:** `lamini/spider_text_to_sql`
- **GPU:** `L40S`
- **Prompts:** `10`

### Results

| Method | Tokens | Tok/s | Latency (s) | Peak Mem (MB) | Draft Acc | Wall Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| vanilla | 5,120 | 38.2 | 133.86 | 15,738 | - | 156.1 |
| draft-spec (`Qwen3-0.6B`) | 5,120 | 20.8 | 246.10 | 17,018 | 26.9% | 274.7 |
| prompt-lookup | 5,123 | 44.5 | 115.17 | 15,762 | - | 145.4 |
| suffix_speculative | 5,120 | 53.2 | 96.21 | 15,765 | 9.4% | 120.2 |

| Method | Steps | Proposed / Step | Accepted / Step | Acceptance Fraction | E2E Tok/s |
|---|---:|---:|---:|---:|---:|
| draft-spec (`Qwen3-0.6B`) | 1,334 | 10.5 | 2.8 | 73.9% | 18.6 |
| suffix_speculative | 2,584 | 8.6 | 0.8 | 40.9% | 42.6 |

### Speedup vs. Vanilla

| Method | Speedup |
|---|---:|
| draft-spec (`Qwen3-0.6B`) | 0.54× |
| prompt-lookup | 1.16× |
| suffix_speculative | 1.39× |

### Summary

- **suffix_speculative** delivered the best performance on Spider, reaching **53.2 tok/s** with a **1.39× speedup** over vanilla.
- **prompt-lookup** provided a smaller but consistent gain, achieving **44.5 tok/s** and **1.16× speedup**.
- **draft-spec (`Qwen3-0.6B`)** underperformed the baseline, dropping to **20.8 tok/s** with only **0.54×** of vanilla speed.
- In speculative decoding metrics:
  - **draft-spec** had **26.9% draft accuracy** and **73.9% acceptance fraction**
  - **suffix_speculative** had **9.4% draft accuracy** and **40.9% acceptance fraction**
- Despite lower draft accuracy, **suffix_speculative** still achieved the highest end-to-end throughput (**42.6 E2E tok/s**) among speculative methods.

---

## TerminalBench Benchmark Comparison

**Command**
```bash
PYTHONPATH=src python -m bench.cli compare terminalbench --limit 10
```

### Experiment Setup

- **Model:** `Qwen/Qwen3-8B`
- **Dataset:** `ia03/terminal-bench`
- **GPU:** `L40S`
- **Prompts:** `10`

### Results

| Method | Tokens | Tok/s | Latency (s) | Peak Mem (MB) | Draft Acc | Wall Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| vanilla | 10,240 | 38.0 | 269.14 | 15,916 | - | 360.6 |
| draft-spec (`Qwen3-0.6B`) | 10,240 | 35.0 | 292.24 | 17,331 | 52.8% | 336.9 |
| prompt-lookup | 10,248 | 43.2 | 237.11 | 15,955 | - | 299.2 |
| suffix_speculative | 10,240 | 59.6 | 171.88 | 15,960 | 13.1% | 264.5 |

| Method | Steps | Prop/Step | Acc/Step | AccFrac | E2E Tok/s |
|---|---:|---:|---:|---:|---:|
| draft-spec (`Qwen3-0.6B`) | 1,917 | 8.2 | 4.3 | 81.3% | 30.4 |
| suffix_speculative | 4,443 | 8.6 | 1.1 | 48.8% | 38.7 |

### Speedup vs. Vanilla

| Method | Speedup |
|---|---:|
| draft-spec (`Qwen3-0.6B`) | 0.92× |
| prompt-lookup | 1.14× |
| suffix_speculative | 1.57× |


### Summary

- **suffix_speculative** achieved the best performance, reaching **59.6 tok/s** with a **1.57× speedup** over vanilla.
- **prompt-lookup** provided a modest improvement to **43.2 tok/s**, corresponding to a **1.14× speedup**.
- **draft-spec (`Qwen3-0.6B`)** underperformed compared with vanilla at **35.0 tok/s**, for a **0.92× speedup**, while also using the highest peak memory (**17,331 MB**).
- In speculation quality:
  - **draft-spec** had higher **draft accuracy (52.8%)** and **AccFrac (81.3%)**
  - **suffix_speculative** had lower acceptance quality overall, but much higher end-to-end throughput
- On this workload, **suffix_speculative** offered the strongest practical latency and throughput gains.

---

## WMT14 Suffix Matching Ablation

**Command**
```bash
PYTHONPATH=src python -m bench.cli compare wmt14 --limit 10
```

### Experiment Setup

- **Model:** `Qwen/Qwen3-8B`
- **Dataset:** `wmt14`
- **GPU:** `L40S`
- **Prompts:** `10`

### Results

| Method | Tokens | Tok/s | Latency (s) | Peak Mem (MB) | Draft Acc | Wall Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| suffix_speculative [local] | 10,240 | 71.8 | 142.70 | 15,827 | 22.9% | 166.1 |
| suffix_speculative [local+global] | 10,240 | 77.3 | 132.44 | 15,828 | 20.0% | 175.6 |
| suffix_speculative [global] | 10,240 | 39.5 | 258.94 | 15,827 | 4.2% | 297.4 |

| Method | Steps | Prop/Step | Acc/Step | AccFrac | E2E Tok/s |
|---|---:|---:|---:|---:|---:|
| suffix_speculative [local] | 3,030 | 8.0 | 1.8 | 54.2% | 61.6 |
| suffix_speculative [local+global] | 3,429 | 8.8 | 1.8 | 59.0% | 58.3 |
| suffix_speculative [global] | 4,193 | 8.3 | 0.3 | 14.1% | 34.4 |

### Speedup vs. Local

| Method | Speedup |
|---|---:|
| suffix_speculative [local] | 1.00× |
| suffix_speculative [local+global] | 1.08× |
| suffix_speculative [global] | 0.55× |

### Summary

- **suffix_speculative [local+global]** achieved the best overall throughput at **77.3 tok/s**, slightly outperforming **[local]** at **71.8 tok/s**.
- **suffix_speculative [global]** performed much worse at **39.5 tok/s**, reaching only **0.55×** relative speed compared with the **[local]** baseline.
- In matching quality:
  - **[local]** achieved the highest **draft accuracy (22.9%)**
  - **[local+global]** achieved the highest **AccFrac (59.0%)**
  - **[global]** remained ineffective with only **4.2% draft accuracy** and **14.1% AccFrac**
- Although **local+global** slightly improved top-line decoding speed over **local**, the gain was modest.
- On this workload, **local matching** carried most of the benefit, while **global matching alone** was not effective.

---

## WildChat Translate Suffix Matching Ablation

**Command**
```bash
PYTHONPATH=src python -m bench.cli compare wildchat --limit 10
```

### Experiment Setup

- **Model:** `Qwen/Qwen3-8B`
- **Dataset:** `allenai/WildChat`
- **GPU:** `L40S`
- **Prompts:** `10`

### Results

| Method | Tokens | Tok/s | Latency (s) | Peak Mem (MB) | Draft Acc | Wall Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| suffix_speculative [global] | 1,249 | 40.5 | 30.81 | 15,781 | 1.0% | 74.6 |
| suffix_speculative [local] | 1,237 | 111.2 | 11.12 | 15,811 | 71.5% | 79.9 |
| suffix_speculative [local+global] | 1,237 | 111.1 | 11.13 | 15,811 | 61.9% | 82.7 |

| Method | Steps | Prop/Step | Acc/Step | AccFrac | E2E Tok/s |
|---|---:|---:|---:|---:|---:|
| suffix_speculative [global] | 48 | 8.1 | 0.1 | 0.3% | 16.7 |
| suffix_speculative [local] | 148 | 8.3 | 5.9 | 71.0% | 15.5 |
| suffix_speculative [local+global] | 171 | 8.3 | 5.1 | 71.1% | 15.0 |

### Speedup vs. Global

| Method | Speedup |
|---|---:|
| suffix_speculative [global] | 1.00× |
| suffix_speculative [local] | 2.74× |
| suffix_speculative [local+global] | 2.74× |

### Summary

- **suffix_speculative [local]** and **[local+global]** achieved nearly identical throughput, reaching **111.2 tok/s** and **111.1 tok/s**, respectively.
- **suffix_speculative [global]** was far slower at **40.5 tok/s**, showing that global-only matching was not competitive on this workload.
- In matching quality:
  - **[local]** achieved the highest **draft accuracy (71.5%)**
  - **[local+global]** had nearly identical **AccFrac (71.1%)** to **[local] (71.0%)**
  - **[global]** had essentially no useful matches, with only **1.0% draft accuracy** and **0.3% AccFrac**
- Adding global matching on top of local matching produced almost no measurable gain.
- On this workload, the performance improvement came almost entirely from **local matching**, with **global matching contributing little to no additional benefit**.

---

## WildChat Code Suffix Matching Ablation

**Command**
```bash
PYTHONPATH=src python -m bench.cli compare wildchat-code --limit 10
```

### Experiment Setup

- **Model:** `Qwen/Qwen3-8B`
- **Dataset:** `allenai/WildChat`
- **GPU:** `L40S`
- **Prompts:** `10`

### Results

| Method | Tokens | Tok/s | Latency (s) | Peak Mem (MB) | Draft Acc | Wall Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| suffix_speculative [local] | 8,988 | 56.1 | 160.11 | 15,827 | 11.7% | 179.0 |
| suffix_speculative [global] | 9,210 | 40.0 | 230.41 | 15,822 | 1.5% | 251.0 |
| suffix_speculative [local+global] | 8,892 | 34.0 | 261.84 | 15,827 | 7.6% | 290.2 |

| Method | Steps | Prop/Step | Acc/Step | AccFrac | E2E Tok/s |
|---|---:|---:|---:|---:|---:|
| suffix_speculative [local] | 3,383 | 7.8 | 0.9 | 34.4% | 50.2 |
| suffix_speculative [global] | 3,594 | 8.1 | 0.1 | 4.6% | 36.7 |
| suffix_speculative [local+global] | 4,285 | 8.3 | 0.6 | 30.3% | 30.6 |

### Speedup vs. Local

| Method | Speedup |
|---|---:|
| suffix_speculative [local] | 1.00× |
| suffix_speculative [global] | 0.71× |
| suffix_speculative [local+global] | 0.60× |

### Summary

- **suffix_speculative [local]** achieved the best performance at **56.1 tok/s**, clearly outperforming **[global]** at **40.0 tok/s** and **[local+global]** at **34.0 tok/s**.
- **suffix_speculative [local+global]** was actually the slowest variant, dropping to **0.60×** relative speed compared with the **[local]** baseline.
- In matching quality:
  - **[local]** achieved the highest **draft accuracy (11.7%)**
  - **[local+global]** reached **30.3% AccFrac**, lower than **[local]** at **34.4%**
  - **[global]** remained ineffective with only **1.5% draft accuracy**
- Unlike the translation workload, adding global matching here introduced overhead without improving acceptance quality enough to compensate.
- On this workload, **local matching alone** was clearly the best choice, and **global matching hurt performance** whether used alone or combined with local matching.

---

## SWE-bench Suffix Matching Ablation

**Command**
```bash
PYTHONPATH=src python -m bench.cli compare swebench --limit 10
```

### Experiment Setup

- **Model:** `Qwen/Qwen3-8B`
- **Dataset:** `princeton-nlp/SWE-bench`
- **GPU:** `L40S`
- **Prompts:** `10`

### Results

| Method | Tokens | Tok/s | Latency (s) | Peak Mem (MB) | Draft Acc | Wall Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| suffix_speculative [local] | 20,480 | 104.5 | 195.91 | 16,735 | 41.5% | 227.9 |
| suffix_speculative [local+global] | 20,480 | 91.9 | 222.79 | 16,735 | 29.5% | 245.6 |
| suffix_speculative [global] | 20,480 | 34.4 | 596.18 | 16,733 | 2.6% | 613.7 |

| Method | Steps | Prop/Step | Acc/Step | AccFrac | E2E Tok/s |
|---|---:|---:|---:|---:|---:|
| suffix_speculative [local] | 4,396 | 8.2 | 3.4 | 73.1% | 89.9 |
| suffix_speculative [local+global] | 5,417 | 9.0 | 2.7 | 70.3% | 83.4 |
| suffix_speculative [global] | 10,767 | 8.5 | 0.2 | 11.7% | 33.4 |

### Speedup vs. Local

| Method | Speedup |
|---|---:|
| suffix_speculative [local] | 1.00× |
| suffix_speculative [local+global] | 0.88× |
| suffix_speculative [global] | 0.33× |

### Summary

- **suffix_speculative [local]** achieved the best overall throughput at **104.5 tok/s**, outperforming **[local+global]** at **91.9 tok/s** and greatly surpassing **[global]** at **34.4 tok/s**.
- **suffix_speculative [local+global]** retained strong performance, but still fell to **0.88×** relative speed compared with **[local]**.
- In matching quality:
  - **[local]** achieved the highest **draft accuracy (41.5%)**
  - **[local]** also achieved the highest **E2E Tok/s (89.9)**
  - **[global]** again contributed very little, with only **2.6% draft accuracy** and **11.7% AccFrac**
- Although **local+global** remained reasonably effective, it did not improve over **local-only** matching.
- On this workload, **local matching was the dominant source of speedup**, while **global matching reduced efficiency rather than helping**.

---

## TerminalBench Suffix Matching Ablation

**Command**
```bash
PYTHONPATH=src python -m bench.cli compare terminalbench --limit 10
```

### Experiment Setup

- **Model:** `Qwen/Qwen3-8B`
- **Dataset:** `ia03/terminal-bench`
- **GPU:** `L40S`
- **Prompts:** `10`

### Results

| Method | Tokens | Tok/s | Latency (s) | Peak Mem (MB) | Draft Acc | Wall Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| suffix_speculative [local+global] | 10,240 | 59.3 | 172.78 | 15,960 | 13.1% | 208.2 |
| suffix_speculative [local] | 10,240 | 55.6 | 184.11 | 15,960 | 24.4% | 211.1 |
| suffix_speculative [global] | 10,240 | 34.8 | 294.01 | 15,950 | 1.3% | 313.5 |

| Method | Steps | Prop/Step | Acc/Step | AccFrac | E2E Tok/s |
|---|---:|---:|---:|---:|---:|
| suffix_speculative [local+global] | 4,443 | 8.6 | 1.1 | 48.8% | 49.2 |
| suffix_speculative [local] | 3,168 | 7.8 | 1.9 | 58.7% | 48.5 |
| suffix_speculative [global] | 5,191 | 8.3 | 0.1 | 5.3% | 32.7 |

### Speedup vs. Local+Global

| Method | Speedup |
|---|---:|
| suffix_speculative [local+global] | 1.00× |
| suffix_speculative [local] | 0.94× |
| suffix_speculative [global] | 0.59× |

### Summary

- **suffix_speculative [local+global]** achieved the best top-line throughput at **59.3 tok/s**, narrowly ahead of **[local]** at **55.6 tok/s**.
- **suffix_speculative [global]** was much slower at **34.8 tok/s**, reaching only **0.59×** relative speed compared with the **[local+global]** baseline.
- In matching quality:
  - **[local]** achieved the highest **draft accuracy (24.4%)**
  - **[local]** also achieved the highest **AccFrac (58.7%)**
  - **[local+global]** still produced the best overall throughput despite lower acceptance quality
- This suggests that **local+global** offered a slightly better end-to-end decoding tradeoff even though its raw acceptance metrics were not the strongest.
- On this workload, **both local and local+global were effective**, but **global-only matching remained clearly inferior**.

---

## Spider Suffix Matching Ablation

**Command**
```bash
PYTHONPATH=src python -m bench.cli compare spider --limit 10
```

### Experiment Setup

- **Model:** `Qwen/Qwen3-8B`
- **Dataset:** `lamini/spider_text_to_sql`
- **GPU:** `L40S`
- **Prompts:** `10`

### Results

| Method | Tokens | Tok/s | Latency (s) | Peak Mem (MB) | Draft Acc | Wall Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| suffix_speculative [local] | 5,055 | 44.6 | 113.22 | 15,765 | 7.5% | 172.4 |
| suffix_speculative [global] | 5,120 | 33.2 | 154.38 | 15,764 | 9.4% | 204.5 |
| suffix_speculative [local+global] | 5,120 | 35.8 | 143.18 | 15,765 | 9.4% | 234.7 |

| Method | Steps | Prop/Step | Acc/Step | AccFrac | E2E Tok/s |
|---|---:|---:|---:|---:|---:|
| suffix_speculative [local] | 2,355 | 7.6 | 0.6 | 26.5% | 29.3 |
| suffix_speculative [global] | 2,291 | 8.1 | 0.8 | 33.8% | 25.0 |
| suffix_speculative [local+global] | 2,584 | 8.6 | 0.8 | 40.9% | 21.8 |

### Speedup vs. Local

| Method | Speedup |
|---|---:|
| suffix_speculative [local] | 1.00× |
| suffix_speculative [global] | 0.74× |
| suffix_speculative [local+global] | 0.80× |

### Summary

- **suffix_speculative [local]** achieved the best overall throughput at **44.6 tok/s**, outperforming **[local+global]** at **35.8 tok/s** and **[global]** at **33.2 tok/s**.
- Both **[global]** and **[local+global]** underperformed relative to **[local]**, reaching only **0.74×** and **0.80×** of the **[local]** baseline, respectively.
- In matching quality:
  - **[global]** and **[local+global]** both reported slightly higher **draft accuracy (9.4%)** than **[local] (7.5%)**
  - **[local+global]** also achieved the highest **AccFrac (40.9%)**
  - However, these acceptance improvements did not translate into better throughput
- This indicates that higher acceptance statistics from broader matching were offset by additional overhead.
- On this workload, **local matching alone** provided the best practical decoding speed, while **global components were not beneficial end-to-end**.
