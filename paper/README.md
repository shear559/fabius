<!-- © 2026 shear559 · fabius · provenance fab1-6bbf82d118bce2cee9d7ac71f034fa26 · release evidence: PROVENANCE.md · github.com/shear559/fabius -->
# The whitepaper

**[fabius-as-a-system.pdf](fabius-as-a-system.pdf)** — *Fabius — one set of operating rules across supported agent harnesses (v2.8.1).* The canonical, full whitepaper: the fifteen-skill architecture (the *praetorium* router that dispatches by layer + machinery + model-tier, four engineering specialists, nine domain verticals, on the always-on lean core), **twenty-two core routing rules**, represented by **twenty-six formal blocks** (twenty-two conditional mathematical arguments and four qualitative rules), and a composition analysis that states its assumptions and exceptions, and one dated benchmark in four panels. Panel A improved three of four measured Claude tiers while shortening all four; Panel B's historical model-operated executed-code score records tied while its model-graded checklist scores rose; Panel C retains only aggregate cross-family demo scores; Panel D prints both gains and regressions. The score receipts do not retain the original answer text, Panel B artifacts, or Panel C raw run, so those historical results cannot be independently re-judged. The composition analysis concerns an abstract routing model. New verticals must preserve the ownership and execution assumptions; correctness, measured routing accuracy, and host compliance require separate verification.

## Mathematical scope and review history

The proofs were not hand-written and waved through. The historical record contains 26 blocks: 22 mathematical arguments and 4 qualitative rules. It records an authoring pass and an **independent adversarial review**; that history is not machine-checked verification or proof of model behavior. That pass corrected ten of them — including a cap that should round to 4 not 3, a value-of-information attribution, a missing completeness hypothesis, and a linearity-vs-independence slip — before anything reached the page. A final auditor checked the whole set for cross-consistency and drafted the coherence capstone. The verified proof content lives in [`proofs.json`](proofs.json) and [`coherence.html`](coherence.html).

The honesty bar is the same as the rest of the project: measured, not claimed. Each block is classed **real-math** for a conditional mathematical argument, or **qualitative** for a control-flow or tuning rule without a proof claim — **22 real-math · 4 qualitative**, the class recorded per block in `proofs.json`. Every rule is fabius's own — derived and adversarially verified; the few operational heuristics are labelled as such, carry no proof claim, and never govern a route the way the mathematical gates do.

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
| `proofs.json` | the 26 adversarially-verified proof blocks (22 real-math · 4 qualitative) |
| `coherence.html` | the coherence capstone theorem |
| `build.sh` | one-command reproduce |

The figures and the benchmark's numbers are the same ones used in [`../RESEARCH.md`](../RESEARCH.md) and [`../BENCHMARKS.md`](../BENCHMARKS.md) — one benchmark, four panels, canonical receipt `../evals/results.benchmark.json`; the paper collects them with the formal assumptions and empirical limits made explicit.

The September 2026 accuracy pass distinguishes the parent-rule count from the block count, scopes the composition argument to its assumptions, and corrects local statement boundaries. Review annotations remain in `proofs.json`; updated prose does not turn historical review metadata into a new independent certification.
