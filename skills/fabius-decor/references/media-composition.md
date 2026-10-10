<!-- © 2026 shear559 · fabius · reference depth for skills/fabius-decor/SKILL.md -->

# Direct a scene and a voice before rendering

Loaded on demand by `fabius-decor` when a generated image, sequence or narration needs controlled composition and continuity. [`generative-imagery.md`](generative-imagery.md) owns still prompting; [`generative-media.md`](generative-media.md) owns source modes, paid preflight and result provenance. This file adds the editable scene and speech production decisions that a prompt alone leaves unresolved. Interactive voice-agent behavior belongs to `fabius-cohors`, not this production workflow.

## 1 · Turn the brief into controllable state

State the deliverable's aspect ratio, duration where applicable, intended viewing size and what must remain recognisable. Separate source roles: identity reference, environment, starting frame, pose guide, mask, voice reference. One asset may serve several roles only when that is explicit. Check what the selected tool can actually constrain; unsupported camera, pose or identity controls remain limitations, not promises hidden in adjectives.

For spatially precise work, establish the layout before generation:

- Put subjects and props into foreground, middle and background with relative position, scale and intended overlaps.
- Choose the camera, crop and perspective; decide which face, label or gesture must remain readable.
- Specify pose and light direction, then identify the regions allowed to change and the elements to preserve.
- Save that state separately from the flattened preview. A prompt cannot recover editable layers, object transforms or the chosen camera after they have been discarded.

Use the simplest available representation that resolves the uncertainty: a layer composite, rough blocking image or existing scene editor. Do not require a 3D stack to answer a 2D arrangement question. Product interface mockups use the actual interface and its design tokens; generative imagery cannot supply proof of working UI.

## 2 · Review the frame, then revise one constraint

Preview at the delivery crop before a costly render. Inspect subject separation, occlusion, visible hands/props, perspective and readable essentials. Approve the composition using the actual preview. Keep the accepted source state and the preview together; record the camera/framing and source-asset versions.

For a revision, name the changed constraint and the invariants. A local mask guides where editing happens; inspect the supposedly preserved region afterward as well. A generated result can drift beyond the requested edit. If the tool cannot preserve an invariant, say which and choose an authorized approximation rather than claim exact control.

For several shots, keep a continuity record: subject references, environment, wardrobe/props, light direction and accepted source frame per shot. Reuse the scene and change the intended camera or action. Compare adjacent shots against that record before rendering the whole sequence. Saved inputs make revisions traceable; a fixed prompt, seed or scene does not prove pixel-identical stochastic output.

## 3 · Treat narration as a produced asset

First fix the approved script, spoken language, speaker count, duration window and output channel. Use existing voice/likeness rights checks in [`design-assets.md`](design-assets.md) and [the person-bearing media boundary](../../fabius-praesidium/references/supply-chain-and-ai-artifacts.md). An accessible voice sample does not establish permission to clone it. Keep reference audio and its verified transcript paired; mixed speakers, background music or inconsistent delivery are reasons to replace the reference before tuning generation.

Keep readable script text separate from synthesis tags. Record the selected model, voice/reference revision, delivery settings and pronunciation-rule version. Provider and SDK defaults may differ; resolve their actual schema before calling. For repeated names, acronyms or ambiguous words, keep narrow contextual pronunciation rules and audition them before fixing a version for the batch.

**Audition the difficult passage first** *(ours)*: names, numerals, code-switching and the strongest delivery change. Listen for meaning, pronunciation, pace and voice suitability; a successful API response verifies none of those. Choose a file-generation path for a finished narration; real-time transport is useful only when the delivery needs it.

For long narration, divide at semantic boundaries within declared limits. Keep segment IDs, script ranges, consistent voice/settings and completed outputs so a retry replaces only the failed segment. Match format, sample rate and channels before stitching; check every join for clipped words, doubled phrases, abrupt ambience and timing drift. Streaming chunks are transport pieces, not automatically valid standalone audio files.

## 4 · Verify and hand over the authored result

Review the final encoded media, not only a preview. Compare scenes with the approved composition and continuity record. Listen to narration against the script, including beginnings, endings and joins; check missing/repeated words, speaker continuity, pauses and clipping. An automatic transcript can flag mismatches but does not replace listening or establish voice quality. Captions follow the final waveform rather than estimated script timing.

Retain the editable source, approved script and final output when the task requires later revision. Add scene/reference and pronunciation versions to the existing provenance row in [`generative-media.md`](generative-media.md), without creating a second ledger. If the host cannot render, listen or inspect the required modality, report that exact verification gap; a storyboard or script is not a produced video or audio file.

Studied (2026-10-10): a hosted speech service's public text-to-speech, reference-audio and pronunciation-dictionary documentation (a commercial product; nothing carried) — observed for separate script/reference roles, explicit model choice, auditioned pronunciation rules and versioned batch continuity. The audition, stitching and final-media review procedure above is Fabius's own synthesis, not a measured service guarantee.

Informed by **ArtCraft** (storytold / ArtCraft Team and contributors, MIT option of its MIT OR Apache-2.0 licence), revision `8abde75133d2d66fe73b8184eaec8372efae2abf`, inspected 2026-10-10 — studied scene/layer composition and the implemented persistence of object transforms, rig data, cameras and timeline state, re-expressed for Fabius's existing media owner; no source files, assets or trademarks bundled. The supplied organization URL was resolved to this pinned lead repository only; its NOTICE excludes specified third-party assets from the licence grant. See credits/README.md.
