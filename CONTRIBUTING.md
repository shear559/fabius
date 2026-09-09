# Contributing

fabius is proprietary — the [LICENSE](LICENSE) grants personal, non-commercial use of the published plugin and nothing beyond it. That shapes what contribution means here: **this project takes reports, questions and corrections, not code.**

## What is welcome

- **Bug reports.** The runtime has an offline regression suite and releases are sealed, and things still break. A report that names the command, platform, expected behavior, and observed behavior is actionable. Open an issue.
- **Questions.** [Discussions](https://github.com/shear559/fabius/discussions) — the install thread and the sealing thread already answer the two most common ones.
- **Corrections.** The documentation makes measured claims — benchmark figures, test counts, model rosters, proof classifications. If one of them is wrong, that is the most valuable issue you can open. Three versions of the provenance paper were corrected by exactly this kind of outside reading.
- **Security reports.** Privately, please — see [SECURITY.md](SECURITY.md). Not as a public issue.

## What cannot be accepted

Unsolicited pull requests that add or modify the Software. This is the maintainer’s contribution policy under the current license; cryptographic sealing does not inherently prevent accepting reviewed contributions.

If you want to build something on fabius, [open an issue and ask](https://github.com/shear559/fabius/issues/new/choose). Written permission is how the LICENSE says yes, and an answer is not guaranteed.

## The bar for reports

The project's own standard is that claims carry receipts. A report meets the same bar with three things: what you ran, what you expected, what happened. Include the host name/version and the plugin version shown by its plugin manager. If using the optional runner from a full checkout, include `node runtime/fabius.mjs --version`. Review every shared log manually for private information; automatic redaction is not a guarantee.
