# Fabius Decor: original design kit

The kit turns a small design contract into CSS and an inspectable storyboard. It is original Fabius code: no bundled component gallery, animation framework, font, icon set, or media library.

## Run the useful path

From the repository root, with Node 22 or newer:

```sh
node skills/fabius-decor/scripts/design.mjs check skills/fabius-decor/examples/tokens.json
node skills/fabius-decor/scripts/design.mjs css skills/fabius-decor/examples/tokens.json --out /tmp/fabius-tokens.css
node skills/fabius-decor/scripts/design.mjs scene skills/fabius-decor/examples/storyboard.json --out /tmp/fabius-scene
python3 -m http.server 8876 --bind 127.0.0.1 --directory /tmp/fabius-scene
```

Open the served scene. These output paths must be unused: the CLI refuses to overwrite existing files or directories. `check` prints measured ratios and issues, exiting 1 on an invalid contract. `css` and `scene` validate before writing. A filesystem failure during scene output can leave a partial directory; inspect it before removing your own failed output.

The scene contains actual supplied copy, a keyboard-operable timeline, previous/next controls, a static-view control, and a readable transcript. It does not simulate a product dashboard or invent performance figures. Edit `examples/storyboard.json` into your own input file; keep factual claims tied to real evidence.

## Choose the smallest artifact

| Need | Original path | Verification |
|---|---|---|
| Consistent palette and controls | [Token contract](design-tokens.md) and `scripts/design.mjs check` | Explicit color-pair ratios; inspect the actual page afterward |
| A page or component composition | [Layout recipes](layout-recipes.md) | Mobile content flow, labels, errors, keyboard focus |
| An explainer or static scene | Storyboard JSON → `scripts/design.mjs scene` | Render at a fixed viewport and seek to named times |
| Repeated video frames | [Capture contract](motion-libraries.md) | Same seek input gives the same rendered scene; inspect encoded output |
| A chart from real data | Existing [Figura guidance](visualization.md), repository `assets/charts/svgplot.py` | Check data, labels and the rendered SVG |

The chart helper stays in its existing owner directory; this kit does not duplicate it. Native markup, CSS and browser controls supply the platform behavior. Those platforms remain external implementations, not Fabius-owned technology.

## Scope and proof

The validator supports an opaque sRGB palette expressed as six-digit hex, neutral functional colors and one accent, explicit focus tokens, and a bounded motion policy. It checks the named pairs, not arbitrary DOM styles, composited transparency, imagery, gradients, high-contrast modes or whole-page accessibility. Focus can still be clipped or obscured in an embedding page. Verify the actual surface with keyboard navigation and a real browser.

The storyboard supports 1–12 text scenes with durations of 1–60 seconds, a static transcript, and a finite vertical entrance. It has no autoplay, asset loading, audio, arbitrary HTML, video encoding, animation editor, 3D pipeline, framework adapter, or imported component catalog. Control labels are English; `lang` and `dir` describe the supplied content, not a full localization system. Pixel reproducibility requires the same browser build, operating-system fonts, viewport, scale, and capture setup.

Tests: `node --test skills/fabius-decor/scripts/*.test.mjs`. Source APIs: `contrast`, `validateTokens`, `tokensCSS`, `validateStoryboard`, `renderScene` in `scripts/design.mjs`; `stateAt` in `templates/timeline.mjs` takes already validated scenes and motion tokens. The browser exposes `window.__seek(seconds)` and read-only duration/count metadata in `window.__storyboard`.

Review guidance remains separate: [design critique](design-critique.md), [RTL/Bidi](rtl-bidi.md), [platform baseline](platform-baseline.md), [external materials](design-assets.md), and [icons](icons.md). Listing an external tool or asset is not permission to redistribute it; verify the selected version and asset terms.
