# Project Finish Plan

Based on the proposal, the project scope is:

- Extend `transformers` with two speculative decoding variants
- Benchmark them against existing baselines
- Turn the results into a poster and final report

The repo currently only contains the proposal, so this plan assumes implementation starts from zero.

## 1. Lock Scope

Define the final required methods:

- Autoregressive decoding baseline
- Built-in `transformers` draft-model speculative decoding
- Prompt-lookup / n-gram speculation baseline
- Suffix speculative decoding
- Tree-based speculative decoding

Treat `vLLM` comparison as optional. It is useful if time permits, but it should not block the core project.

## 2. Build Benchmark Infrastructure First

Before implementing new methods, create a reproducible benchmark harness that can:

- Load one target model and one draft model
- Run generation on fixed prompt sets
- Record latency, TTFT, throughput, acceptance rate, and GPU memory
- Save outputs to CSV or JSON for later analysis

This is the foundation for fair comparisons.

## 3. Reproduce Existing Baselines

Get the following working end-to-end before adding new algorithms:

- Standard autoregressive generation
- Existing `transformers` speculative decoding
- Prompt-lookup or n-gram style speculation if available

Do not begin suffix or tree variants until these baselines are stable and measurable.

## 4. Implement Suffix Speculative Decoding

Add a candidate generator that proposes tokens from suffix matches in the prompt and recent generation history.

Requirements:

- Integrates cleanly into the same generation and benchmark pipeline
- Produces correct outputs first
- Exposes tunable parameters such as match length and speculation depth

Only optimize performance after correctness is verified.

## 5. Implement Tree-Based Speculative Decoding

Start with a bounded and simplified version:

- Small tree width
- Small tree depth
- Shared verification logic where possible

The goal is to validate multiple candidate branches in one verification step. If the full design is too large, ship a smaller prototype rather than missing the deadline.

## 6. Define the Evaluation Matrix Early

Choose a small but meaningful sweep:

- Short prompts vs. long prompts
- Small batch size vs. medium batch size
- Short outputs vs. long outputs
- Easier prompts vs. harder prompts if that distinction can be defined consistently

Keep the matrix small enough that experiments can finish on available hardware.

## 7. Run Experiments in Two Passes

Pass 1: correctness and smoke tests

- Tiny prompt subset
- Short outputs
- Check output validity, acceptance statistics, runtime stability, and logging

Pass 2: full benchmark sweep

- Freeze code before the full run
- Run all baselines and new methods on the same prompt sets
- Export raw results and aggregated summaries

## 8. Focus Analysis on Tradeoffs

Do not report only average speedups. Analyze:

- When suffix speculation improves acceptance rate
- When suffix matching fails or adds overhead
- When tree verification improves throughput
- When tree overhead outweighs benefits
- How gains change with prompt length, output length, and batch size

This analysis is necessary for a strong MLSys final report.

## 9. Prepare Final Deliverables

Produce the following:

- One main figure for latency or speedup
- One figure for acceptance rate or throughput
- One table comparing methods and tradeoffs
- Poster
- Final report
- Optional demo script if presentation format benefits from it

## Recommended Team Split

- Person 1: `transformers` integration and suffix speculative decoding
- Person 2: tree-based speculative decoding
- Person 3: benchmark harness, experiment automation, plotting, and report integration

## Minimum Viable Success

If time becomes limited, the minimum strong outcome is:

- Stable benchmark harness
- Working autoregressive and built-in speculative baselines
- Fully implemented and evaluated suffix speculative decoding
- Simplified tree-based prototype with honest discussion of limits

This is better than attempting a full tree system and failing to finish evaluation.

## Suggested Milestones

- Week 1: environment setup, model loading, dataset selection, benchmark harness, autoregressive baseline
- Week 2: built-in speculative baseline and prompt-lookup baseline
- Week 3: suffix speculative decoding complete
- Week 4: tree-based prototype complete
- Week 5: full experiments and plots
- Week 6: poster and final report

## Immediate Next Steps

- Create the experiment harness and result schema
- Confirm the exact target and draft models that fit available hardware
- Pick the prompt datasets and sample sizes
- Reproduce baseline `transformers` decoding numbers before writing new decoding logic
