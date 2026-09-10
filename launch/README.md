# Early-public-launch candidate

The September 13–19 window is conditional, not a promised publication date. September 17 is a decision checkpoint after evidence is available. No automatic release, store submission, outreach, paid campaign or benchmark spend is scheduled by this file.

## Release conditions

1. The owner chooses the license scope. Until then the existing personal-use-only LICENSE governs every surface.
2. The candidate passes the deterministic gate and browser checks; PDF, manifests, archive and signed release use the same final version.
3. Every advertised host has the fresh-session/lifecycle receipt in [COMPATIBILITY.md](../COMPATIBILITY.md), or the claim explicitly remains unverified.
4. At least one independent participant in each of four audience groups completes a useful task. Maintainer examples do not satisfy this criterion.
5. The owner approves the concrete repository commits and website publication. Store submission is a separate externally visible step.

## Submission packet

The distribution archive contains the plugin and its required files. [Acceptance cases](acceptance-cases.json) provide five positive and three negative scenarios with reproducible fixture requirements. [Examples](../examples/README.md), [Quickstart](../QUICKSTART.md), [claims](../CLAIMS.md) and [support](../SUPPORT.md) supply the product evidence and user path.

Proposed listing: **Fabius — task guidance for your existing AI assistant.** Description: “Fifteen coordinated skills help turn tasks into checkable drafts, files and code. Start with meeting notes, a short video brief, a CSV summary or a bug fix. Tools and model access come from your host.” Do not select countries, make legal attestations or claim verified status on the owner's behalf.

The website's support/privacy/terms pages must actually be deployed before their URLs are submitted. Capture screenshots of real examples and install controls, not invented product UI. The GitHub social preview is a separate setting from the site's Open Graph image; verify it explicitly at publication.

## Build and inspect the distribution

From a committed checkout, choose a new output directory outside any Git checkout:

```sh
python3 -B scripts/distribution.py check
python3 -B scripts/distribution.py build --output-dir /tmp/fabius-candidate-package
python3 -B scripts/distribution.py verify /tmp/fabius-candidate-package/fabius-2.8.3-claude-plugin.zip
```

The builder includes tracked files, required attribution and all fifteen root skills. It rejects missing authored resource links, escaping symlinks, selected secrets and concurrent source changes. Two builds of identical source bytes produce identical ZIP bytes. The embedded manifest records the commit, selected source hashes, archive hashes and any dirty paths; it is not a signature or store approval. Untracked files require explicit `--include-file` arguments. Existing archives are never overwritten.

The local upstream inventory preserves all 18 registry entries and leaves 11 unknown historical revisions as null. Bundled LICENSE/NOTICE files and local bytes are checked; that does not recover historical import commits. The archive also inventories 359 unresolved links in preserved reference corpora. Those historical examples remain reference data, not certified runnable packages. Required authored links pass the narrower resource check; arbitrary imports, remote URLs and host loading require separate verification.

Primary requirements checked 2026-09-09: [OpenAI submission](https://developers.openai.com/plugins/deploy/submission) asks for five positive and three negative cases; [direct Claude archive import](https://developers.openai.com/plugins/guides/submit-claude-plugin) converts a qualifying skills archive and still requires testing the imported tree. [Anthropic submission](https://claude.com/docs/plugins/submit) distinguishes community directory access from additional verification. None of these mechanisms guarantees approval or a review date.

## Human pilot

[Natural-language task suite](task-suite.json) supplies 24 prepared cases: four audiences, each with simple, ambiguous, multistep, missing-tool, recovery and Hebrew scenarios. It leaves every observed route and outcome empty. Run `node launch/validate-tasks.mjs --self-test` to validate the specification; this does not execute the tasks. Candidate-host receipts must retain the loaded version, observed skills, tools, permissions and actual outputs. Synthetic fixtures cannot count as host or independent-user evidence. This suite is separate from the fixed 100-task FBS and the five-positive/three-negative store packet.

Recruit 8–12 volunteers, 2–3 each for personal planning, creative work, development and business-shaped practice. Participation is opt-in; use synthetic inputs and offer withdrawal. Ask each person to install from the public instructions, complete one task without coaching, inspect the result and attempt a second use later. Record the exact version and distinguish independent completion from assisted completion. The owner chooses participants and authorizes contact; none have been contacted or enrolled by this work.

Use [pilot-ledger.csv](pilot-ledger.csv) privately; do not commit participant identities or transcripts. Measure time to first usable artifact, independent completion, blockers and voluntary return. Empty rows are absence of evidence, never zero success. The initial target is at least one independent completion in each group, followed by a seven-day follow-up after consent. Expansion to 20 users happens only after the initial problems are repaired.

## Organic launch drafts

Draft for a permitted personal social channel, after publication:

> I built Fabius as a set of operating rules for different AI models. It gives recurring tasks a written process: understand the input, choose the relevant skill, produce something you can inspect, and check it. You use the rules with your chosen model through a compatible agent app. The repository includes four starter examples and the limits of its historical evaluations. Try one task and tell me where the instructions or result break: https://github.com/shear559/fabius

Draft for an opt-in pilot invitation, to send only with owner approval:

> Would you try one small task with Fabius and report where you got stuck? Use synthetic notes, a CSV or a short coding example. I want the first result you can actually use, including failures; no star, testimonial or public post is required.

These drafts require final license/availability review before sending. Do not mass-post or contact strangers. For Hacker News, the owner must write the submission independently: its [current guidelines](https://news.ycombinator.com/newsguidelines.html) prohibit generated or AI-edited text. No HN submission text is supplied here. Product Hunt is optional and is not a release dependency.

## Measurement

A read-only GitHub baseline is kept with the private task outputs. GitHub Traffic uses a moving window; timestamp snapshots and avoid adding overlapping unique counts. Clones are not installations, stars are not active users, and PDF downloads are not task completions. The website adds no tracking pixels or form. Use the opt-in pilot ledger first; paid traffic and new product scope wait for actual usage evidence.
