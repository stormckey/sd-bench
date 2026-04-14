#set page(width: 8.5in, height: 11in, margin: (x: 0.65in, y: 0.65in))
#set text(font: "Libertinus Serif", size: 10pt)
#set par(justify: true, leading: 0.55em)
#set heading(numbering: none)

#align(center)[
  #text(13pt, weight: "bold")[Optimizing LLM Serving with Speculative Decoding]

  Chenhao Gao
  (#link("mailto:cgao3@andrew.cmu.edu")[cgao3\@andrew.cmu.edu])

  Yuchen Zhou
  (#link("mailto:yuchenz8@andrew.cmu.edu")[yuchenz8\@andrew.cmu.edu])

  Zihao Du
  (#link("mailto:zihaodu@andrew.cmu.edu")[zihaodu\@andrew.cmu.edu])
]

= Introduction

LLM inference is slow and expensive because generation is autoregressive: each new token requires a forward pass through a large target model. Speculative decoding reduces this cost by using a cheaper mechanism to propose several tokens and then letting the target model verify them in parallel. This idea is already important in practice, and systems such as `vLLM` support several advanced speculative decoding variants. In contrast, Hugging Face `transformers` currently provides standard speculative decoding but does not offer built-in support for two methods we want to study: suffix speculative decoding and tree-based speculative decoding. Our project is therefore a `transformers` systems project: we will implement these two methods in `transformers` and evaluate them in a unified benchmark setting.

= Problem

We study how to improve LLM serving efficiency through better speculative decoding, and ask:
+ Can suffix speculative decoding improve acceptance rate and end-to-end latency over existing linear speculative decoding
+ Can tree-based speculative verification further improve throughput by validating multiple candidate branches at once
+ Under what conditions do these methods help most: short vs. long prompts, small vs. large batch sizes, and easy vs. difficult next-token distributions
+ How do our implementations compare against existing speculative decoding methods in `transformers`, and against `vLLM` baselines when comparable implementations are available?

= Status Quo

Speculative decoding has been studied extensively as a way to reduce the number of expensive target-model forward passes without changing the target model's output distribution. Existing work includes draft-model speculation, prompt-lookup and n-gram methods, dynamic speculation schedules, Medusa-style multi-token heads, and tree-based verification schemes. Production-oriented serving frameworks such as `vLLM` already implement some of these techniques, so the core ideas are not new. However, Hugging Face `transformers` remains one of the most widely used research and deployment libraries, and its support is more limited: standard speculative decoding exists, but suffix speculative decoding and tree-based speculative decoding are not first-class features. This creates a clear systems gap. Our goal is to close part of that gap by adding these methods to `transformers` and then benchmarking them against existing `transformers` baselines and, where possible, against `vLLM`.

= High-Level Implementation Plan

We will implement both methods in the Hugging Face `transformers` generation stack. Suffix speculative decoding will be added as a candidate generator that proposes continuations by matching suffixes from the prompt and recent generation history. Tree-based speculative decoding will be added as a branching verification path that evaluates multiple candidate continuations together instead of a single linear candidate chain. The primary implementation target is therefore `transformers`, while `vLLM` serves as an external comparison point rather than the platform we are extending.

Our experiments will use a Qwen3 target model and a smaller Qwen3 draft model from the same family. Concretely, we plan to use `Qwen/Qwen3-4B-Instruct-2507` as the target model and `Qwen/Qwen3-1.7B` as the draft model, since this gives us a recent yet still architecturally simple dense text-model pair that works well in `transformers`. We will compare:
+ autoregressive decoding
+ existing `transformers` speculative decoding with a draft model
+ prompt lookup / n-gram style speculation
+ our suffix speculative decoding implementation
+ our tree-based speculative decoding implementation
+ if feasible, comparable `vLLM` baselines such as draft-model speculation or MTP/Eagle-style serving

We will evaluate these methods on chat and long-context prompts drawn from datasets such as ShareGPT, WildChat, and Arena-Hard. Our main metrics are end-to-end latency, time to first token, tokens-per-second throughput, speculative acceptance rate, and GPU memory usage. We will also sweep speculation depth, output length, and batch size to understand where each method helps or hurts. This evaluation is important for our project because it lets us measure the practical tradeoffs of these methods in a consistent setting and compare them fairly against simpler baselines and other serving frameworks.
