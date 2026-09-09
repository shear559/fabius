# Four checkable starting points

These synthetic examples were prepared by the maintainer in a Codex desktop session with Fabius 2.8.1 loaded. They demonstrate artifacts and verification, not a clean-install study, independent customer use or a comparison against a bare model. The follow-up release changes evaluation infrastructure and research; do not attribute a measured improvement to it.

Professional or client use requires permission under the current [LICENSE](../LICENSE). Business-shaped inputs here are fictional practice data.

| Audience / task | Input | Artifact | Verification |
|---|---|---|---|
| Personal planning | [Meeting notes and prompt](meeting-input.md) | [Action summary](meeting-output.md) | Every date/owner comes from input; budget and launch approval unresolved |
| Creator | [Video brief prompt](video-input.md) | [Shot list](video-output.md) | 30 seconds; only supplied props; no rendered-video claim |
| Developer | [Bug and prompt](average-input.md) | [Fixed Python](average.py) | Execute the included boundary tests |
| Business practice | [Sales CSV](sales.csv) | [Calculated summary](sales-output.json) | Decimal arithmetic; no currency invention |

Reproduce the deterministic checks from the full repository:

```sh
python3 examples/verify.py
```

The script checks the two executable artifacts. Editorial checks for meeting/video are stated below each output; they are not scored by that script. The prompts can be copied into a fresh host session to test discovery and behavior separately. Preserve the prompt, host/version, loaded contract hashes, raw response, actual artifacts and observed failures before calling a host acceptance test complete.
