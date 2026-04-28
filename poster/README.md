# Poster Workspace

This directory contains a standalone HTML/CSS poster scaffold for the project.

## Files

- `index.html`: main 2:3 portrait poster layout
- `styles.css`: poster styling, print sizing, and placeholder chart visuals
- `script.js`: `debug` and `export` mode toggle

## Design choices

- Uses the final report in `mlsys2025style/final_report.tex` as the source of truth for completed claims
- Keeps tree-based attention / verification clearly separated as `WIP`
- Reserves space for:
  - `1` architecture figure
  - `4` result-analysis charts

## Preview

Open `index.html` in a browser.

- Default mode: normal poster preview
- `index.html?mode=debug`: outlines major layout blocks
- `index.html?mode=export`: hides preview-only framing

## Print / export

The on-screen preview scales responsively, and print mode targets a `24 x 36 in` poster page.

Recommended browser print settings:

- portrait orientation
- background graphics enabled
- margins set to none or minimum
- single page only

## Placeholder chart plan

The results block intentionally uses placeholder panels for now. Each panel includes:

- the fixed final title
- the intended source asset path
- the one-sentence takeaway the final chart must support

This lets the team swap in updated figures later without changing the poster structure.
