# Granular product design

Use for a requested illustrated product site or system whose brief calls for tactile grain, precise geometry and polished explanatory motion. This is an optional Decor recipe, not a new skill or a universal visual default. A current brief and the project's visual-system record determine whether it fits.

## Establish one system

Aim for an advanced, coherent product through legible behavior, precise spacing and consistent materials. Give each section a job before styling it. Carry the same palette, outline weight, type hierarchy, control states and motion language through the hero, capabilities, system explanation, research, installation and closing action. Change density to suit each section; do not repeat the same card grid throughout.

Keep the page focused. A new illustration does not justify extra demo galleries, counters or duplicate explanations. Preserve existing useful content and controls unless removal is requested. Treat “advanced” as a craft direction, never as evidence for a performance or market-leadership claim.

## Record the palette by role

The approved Fabius example uses the following values. Translate these roles into the current project's tokens; another brand does not inherit Fabius green, its typeface or its beetles by default.

| Token / example | Role | Never |
| --- | --- | --- |
| Primary `#76b900`, light `#9ade2b`, strong `#5e9400` | Granular green material, primary actions, execution | Small green text on an unchecked pale surface; several competing primary actions |
| Ink `#0d1504` | Text and precise outlines on light/painted surfaces | A low-contrast pairing hidden by a gradient or grain layer |
| Paper `#f4f7ed` | Reading areas and breathing room | A compulsory tinted box around every paragraph |
| Olive `#101708` | Dense system diagrams and technical bands | Full-page darkness regardless of the content |
| Sky `#a9d8e5`, light `#e0eff2` | Context, connected capabilities, selected illustration panels | An arbitrary second CTA color or unlabeled data encoding |
| Apricot `#f2b998`, light `#f8e0cf` | Design, checks and result details | A claim that something passed when no check actually ran |

Keep one dominant accent. Repeat the supporting colors in small, recognizable roles across sections so they feel intentional. Use text, shape or labels alongside color. Choose focus and text colors by measured contrast against the final rendered surface; a palette table alone is not an accessibility result.

## Make the material tactile and readable

Use a restrained, locally supplied grain tile over selected painted bands and illustration panels. Keep body text on calm reading surfaces. A gentle green ramp can add depth without metallic gloss, luminous haze or a generic neon dashboard treatment.

Use thin dark outlines, compact corner radii and occasional crisp offset shadows on illustrations. Keep these shadows out of charts and ordinary reading blocks. Let type, spacing and section backgrounds carry hierarchy. Match the grain scale and strength between sections and inspect the composited result on a phone.

## Build original illustrations

Prefer native SVG/CSS for precise geometric artwork: a central brand motif, document/result panels, connecting paths, orbital rings, an isometric cube or a four-point spark. Use one outline family, consistent depth and a clear visual center. Give objects a reason to be connected instead of filling every empty corner.

Study a reference's composition and visual principles without copying its characters, logos, source, assets or text. Use the current product's own identity. Keep illustration labels and important explanations in accessible HTML where possible; mark purely decorative SVG as hidden from assistive technology.

## Give the main animation its own stage

Place the explanatory animation in normal document flow as a bounded foreground scene with a title, concise explanation and visible pause/resume control. Keep it distinct from a decorative page background. Show an understandable sequence such as context → relevant skills → execution → checked handoff, with visible labels and manual inspection where the sequence teaches a process.

Compose a few coordinated layers: slow orbital movement, gentle central lift, a moving path signal and a small secondary object. Use transform/opacity animation and native SVG paths before adding an animation library. Give each layer a different purpose and a calm cadence. Avoid unrelated objects all moving at once, flashing, continuous scale pulses or motion that competes with text.

Use pointer response only for decoration on precise pointers, with a small range and a stable resting state. Keep the scene understandable when stationary. An illustration of execution is not a live agent run: label illustrative routing, and do not fabricate progress, latency, throughput or verification telemetry.

## Keep background motifs optional

The approved Fabius design includes subtle wandering beetles behind the hero and core band, alongside the independent foreground scene. This is a brand-specific, explicitly requested layer. For another project, choose no background motion unless the brief supports it.

Keep background motifs low-contrast, behind the content, clipped to their region, non-interactive and away from text focus. Vary scale and speed sparingly. Do not turn the main explanatory scene into a background merely because decorative motifs are allowed.

## Make motion behave as one system

- Respect `prefers-reduced-motion`: supply a complete static composition and retain all essential information and controls.
- Synchronize all page pause controls, including any marquee, foreground scene and decorative background. Pause native SVG timelines as well as CSS/JS animation clocks.
- Pause expensive work when a region is offscreen or the document is hidden. Resume without a burst of queued transitions.
- Keep essential content available immediately. Never gate reading, navigation or installation on animation completion.
- Keep real interactive states separate from decorative motion. A paused illustration must not disable task selection or page navigation.

## Verify the whole page

Inspect a narrow phone, a typical phone, tablet and wide desktop. Keep the main scene legible, touch controls reachable and navigation clear of section headings. Simplify or crop decorative geometry on small screens; never crop an essential label, control or explanation. Avoid horizontal page overflow and oversized desktop headlines surrounded by empty space.

Exercise pause/resume, reduced-motion behavior, offscreen suspension, keyboard focus, task selectors, navigation and installation controls. Check real failures, missing assets and contrast after compositing grain. Capture the rendered result. Report browser/device coverage honestly; do not imply a physical iPhone or Safari check from a desktop viewport alone.

## Origin and scope

Original recipe distilled from the user-approved Fabius landing-page design on 2026-10-24. Implementation evidence: [Fabius landing at the approved revision](https://github.com/shear559/fabius-landing/tree/5e6e150c99cd3b71b6ff98ca2a323678d4ca6bff), especially its design record, foreground SVG, material CSS and motion controls. The [live site](https://fabius-landing.vercel.app/) may evolve. No third-party artwork or source is bundled by this recipe. These are transferable design choices, not measured claims about model or product performance.
