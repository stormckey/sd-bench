"""Generate poster figures from Final Data: All Methods Local-Only Limit-10 Sweep."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ── Data ──────────────────────────────────────────────────────────────────────
workloads = ["WMT14", "WildChat\nTranslate", "WildChat\nCode", "SWE-bench", "Spider", "Terminal\nBench"]
workloads_short = ["WMT14", "WildChat Translate", "WildChat Code", "SWE-bench", "Spider", "TerminalBench"]

# tok/s per method (vanilla first, then speculative)
vanilla   = [33.8, 34.8, 26.0, 37.5, 41.0, 37.8]
draft     = [17.6, 19.9, 22.3, 23.8, 25.4, 27.4]
lookup    = [35.4, 39.8, 43.9, 45.2, 41.9, 43.6]
suffix    = [40.1, 40.8, 45.3, 45.5, 41.2, 49.9]
treespec  = [32.4, 40.2, 44.6, 48.8, 40.0, 43.6]

# draft acceptance % (speculative methods only; vanilla/lookup = N/A)
draft_acc   = [28.7, 31.4, 34.6, 36.7, 40.1, 37.3]
suffix_acc  = [ 8.8,  9.6,  9.3,  9.4,  7.5,  8.8]
treespec_acc= [10.2,  7.0, 10.1, 10.2,  8.4,  9.5]

# acc/step
draft_acc_step   = [3.5, 2.1, 2.7, 2.4, 4.8, 3.3]
suffix_acc_step  = [0.5, 0.7, 0.7, 0.7, 0.6, 0.7]
treespec_acc_step= [0.6, 0.5, 0.8, 0.8, 0.7, 0.7]

# prop/step
draft_prop   = [12.3, 6.8, 7.7, 6.5, 11.8, 8.8]
suffix_prop  = [ 5.7, 7.6, 7.7, 7.8,  7.6, 7.6]
treespec_prop= [ 5.8, 7.2, 7.6, 8.0,  7.9, 7.7]

n = len(workloads)
x = np.arange(n)

# ── Style ─────────────────────────────────────────────────────────────────────
COLORS = {
    "draft":    "#E07B39",   # orange
    "lookup":   "#5B8DB8",   # blue
    "suffix":   "#4DA167",   # green
    "treespec": "#9B5DE5",   # purple
}
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
})

# ── Figure 1: Speedup vs Vanilla ───────────────────────────────────────────────
def speedup(method_tokps):
    return [m / v for m, v in zip(method_tokps, vanilla)]

sp_draft    = speedup(draft)
sp_lookup   = speedup(lookup)
sp_suffix   = speedup(suffix)
sp_treespec = speedup(treespec)

fig, ax = plt.subplots(figsize=(11, 5))
width = 0.2
offsets = [-1.5, -0.5, 0.5, 1.5]
bars = [
    (sp_draft,    "draft-spec",       COLORS["draft"],    offsets[0]),
    (sp_lookup,   "prompt-lookup",    COLORS["lookup"],   offsets[1]),
    (sp_suffix,   "suffix [local]",   COLORS["suffix"],   offsets[2]),
    (sp_treespec, "tree-spec [local]",COLORS["treespec"], offsets[3]),
]
for vals, label, color, off in bars:
    ax.bar(x + off * width, vals, width, label=label, color=color, alpha=0.88, zorder=3)

ax.axhline(1.0, color="#555", linewidth=1.2, linestyle="--", zorder=2, label="vanilla (1×)")
ax.set_xticks(x)
ax.set_xticklabels(workloads, fontsize=10)
ax.set_ylabel("Speedup vs Vanilla", fontsize=11)
ax.set_title("Speculative Speedup Across Tasks (Local-Only, Limit 10)", fontsize=13, fontweight="bold", pad=12)
ax.legend(loc="upper right", fontsize=9, framealpha=0.85)
ax.set_ylim(0, 2.1)
fig.tight_layout()
fig.savefig("speculative_speedup_final.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved speculative_speedup_final.png")

# ── Figure 2: Proposed vs Accepted Tokens per Step ────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Left: accepted tokens per step grouped by workload
ax = axes[0]
offsets2 = [-1, 0, 1]
bars2 = [
    (draft_acc_step,    "draft-spec",       COLORS["draft"]),
    (suffix_acc_step,   "suffix [local]",   COLORS["suffix"]),
    (treespec_acc_step, "tree-spec [local]",COLORS["treespec"]),
]
width2 = 0.25
for i, (vals, label, color) in enumerate(bars2):
    ax.bar(x + offsets2[i] * width2, vals, width2, label=label, color=color, alpha=0.88, zorder=3)
ax.set_xticks(x)
ax.set_xticklabels(workloads, fontsize=9)
ax.set_ylabel("Accepted tokens / step", fontsize=11)
ax.set_title("Accepted Tokens per Step", fontsize=12, fontweight="bold")
ax.legend(fontsize=9, framealpha=0.85)
ax.set_ylim(0, 6)

# Right: proposed tokens per step grouped by workload
ax = axes[1]
bars3 = [
    (draft_prop,    "draft-spec",       COLORS["draft"]),
    (suffix_prop,   "suffix [local]",   COLORS["suffix"]),
    (treespec_prop, "tree-spec [local]",COLORS["treespec"]),
]
for i, (vals, label, color) in enumerate(bars3):
    ax.bar(x + offsets2[i] * width2, vals, width2, label=label, color=color, alpha=0.88, zorder=3)
ax.set_xticks(x)
ax.set_xticklabels(workloads, fontsize=9)
ax.set_ylabel("Proposed tokens / step", fontsize=11)
ax.set_title("Proposed Tokens per Step", fontsize=12, fontweight="bold")
ax.legend(fontsize=9, framealpha=0.85)
ax.set_ylim(0, 16)

fig.suptitle("Proposal Quality vs Acceptance (Local-Only, Limit 10)", fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig("proposal_vs_accept_final.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved proposal_vs_accept_final.png")

# ── Figure 3: Draft Acceptance Rate ───────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 4.5))
offsets3 = [-1, 0, 1]
bars4 = [
    (draft_acc,    "draft-spec",       COLORS["draft"]),
    (suffix_acc,   "suffix [local]",   COLORS["suffix"]),
    (treespec_acc, "tree-spec [local]",COLORS["treespec"]),
]
width3 = 0.25
for i, (vals, label, color) in enumerate(bars4):
    ax.bar(x + offsets3[i] * width3, vals, width3, label=label, color=color, alpha=0.88, zorder=3)
ax.set_xticks(x)
ax.set_xticklabels(workloads, fontsize=10)
ax.set_ylabel("Draft Acceptance (%)", fontsize=11)
ax.set_title("Draft Token Acceptance Rate (Local-Only, Limit 10)", fontsize=13, fontweight="bold", pad=12)
ax.legend(fontsize=9, framealpha=0.85)
ax.set_ylim(0, 55)
fig.tight_layout()
fig.savefig("draft_acceptance_final.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved draft_acceptance_final.png")
