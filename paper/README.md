<!-- © 2026 shear559 · fabius · provenance fab1-6bbf82d118bce2cee9d7ac71f034fa26 · release evidence: PROVENANCE.md · github.com/shear559/fabius -->
# The whitepaper

**[fabius-as-a-system.pdf](fabius-as-a-system.pdf)** — *Fabius — one set of rules above every model (v3.0.1).* The canonical, full whitepaper: the fifteen-skill architecture (the *praetorium* router that dispatches by layer + machinery + model-tier, four engineering specialists, nine domain verticals, on the always-on lean core), **twenty-two core routing rules**, represented by **twenty-six formal blocks** (twenty-two conditional mathematical arguments and four qualitative rules), and a composition analysis that states its assumptions and exceptions, and one dated benchmark in four panels. Panel A improved three of four measured Claude tiers while shortening all four; Panel B's historical model-operated executed-code score records tied while its model-graded checklist scores rose; Panel C retains only aggregate cross-family demo scores; Panel D prints both gains and regressions. The score receipts do not retain the original answer text, Panel B artifacts, or Panel C raw run, so those historical results cannot be independently re-judged. The composition analysis concerns an abstract routing model. New verticals must preserve the ownership and execution assumptions; correctness, measured routing accuracy, and host compliance require separate verification.

## Mathematical scope and review history

The historical record contains 26 blocks: 22 mathematical arguments and 4 qualitative rules. It records an authoring pass and an **independent adversarial review**; that history is not machine-checked verification or proof of model behavior. That pass recorded ten corrections, including a cap rounding boundary, a value-of-information attribution, a missing completeness hypothesis, and a linearity-vs-independence error. The historical cross-consistency review produced the coherence capstone. The statements and review history live in [`proofs.json`](proofs.json) and [`coherence.html`](coherence.html); later corrections below supersede the affected statements.

Each block is classed **real-math** for a conditional mathematical argument, or **qualitative** for a control-flow or tuning rule without a proof claim — **22 real-math · 4 qualitative**, the class recorded per block in `proofs.json`. The historical review does not certify all current statements. Qualitative rules carry no proof claim but can still impose mandatory admissibility conditions, such as R5 grounding.

## Reproduce the PDF

```bash
bash paper/build.sh
```

This self-hosts MathJax, recomputes the figures (`numpy` → SVG), assembles the HTML, and renders the PDF with headless Chrome.

## Files

| File | Role |
|---|---|
| `fabius-as-a-system.pdf` | the rendered paper (the deliverable) |
| `template.html` | the prose, tables, and layout (print CSS + MathJax) |
| `build.py` | assembler — inlines figures, math-safes + injects the proofs |
| `proofs.json` | the 26 formal blocks and their review history (22 real-math · 4 qualitative) |
| `coherence.html` | the coherence capstone theorem |
| `build.sh` | one-command reproduce |

The figures and the benchmark's numbers are the same ones used in [`../RESEARCH.md`](../RESEARCH.md) and [`../BENCHMARKS.md`](../BENCHMARKS.md) — one benchmark, four panels, canonical receipt `../evals/results.benchmark.json`; the paper collects them with the formal assumptions and empirical limits made explicit.

The September 2026 accuracy pass distinguishes the parent-rule count from the block count, scopes the composition argument to its assumptions, and corrects local statement boundaries. Review annotations remain in `proofs.json`; updated prose does not turn historical review metadata into a new independent certification.

## Focused R5/M4 correction — September 2026

The September 9 pass removes R5’s scalar-impossibility claim, specifies a fixed bounded-response window and terminal semantics, and corrects M4’s equality, zero-gain, and retry-index boundaries. It also distinguishes a myopic retry-value comparison from repeated-cause and retry-budget heuristics. This is a focused correction, not a claim that all 26 blocks were re-proven; earlier review notes remain in `proofs.json` with the superseding correction appended.

Run `node evals/proof-boundaries.mjs` from the repository root for source-bound checks and independent counterexamples. These checks cover the named examples and boundary conditions; they do not formally verify every argument or establish host behavior. Historical benchmark receipts are unchanged. Safety/liveness terminology follows [Alpern and Schneider, *Defining Liveness* (1985)](https://www.cs.cornell.edu/fbs/publications/DefLiveness.pdf).

The PDF rendering pass also converts escaped Markdown stars inside TeX into supported mathematical star commands and keeps rule headings with their bodies. `python3 -B paper/test_rendering.py` checks the conversion boundary; the rebuilt PDF was visually inspected at the changed proof pages.
