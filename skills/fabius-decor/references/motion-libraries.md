# Original scene and capture contract

Use a static layout unless time communicates something. For a small state change, native CSS or the browser's Web Animations API can be enough. For reproducible text scenes, use the original kit here; no animation engine is bundled.

## Storyboard input

`examples/storyboard.json` contains `schema: "fabius-storyboard/v1"`, `title`, `description`, `lang`, `dir`, a complete `tokens` object, and `scenes`. Each scene has a unique lowercase `id`, a short `label`, `title`, `body`, and `durationSeconds` between 1 and 60. There must be 1–12 scenes. Fields are closed. Text is escaped; arbitrary HTML, scripts and asset URLs are unsupported.

`design.mjs scene` writes five files to a new directory: `index.html`, `scene.css`, `scene.mjs`, `timeline.mjs`, and the exact parsed input as `storyboard.json`. Serve the directory over HTTP because the page uses JavaScript modules. It makes no external requests. Scripts are external; no inline script permission is needed. The seek function updates element style attributes, so an embedding CSP must permit those style updates or adapt the renderer.

## State is a function of time

`window.__seek(seconds)` computes scene visibility and translation from the supplied time. Negative times clamp to the beginning, times past the duration clamp to the end, and an exact boundary selects the next scene. Non-finite values throw. No requestAnimationFrame, timers, randomness, clock, or autoplay drives the result. Repeating the same time produces the same DOM state under the same preference settings. Text remains fully opaque to retain its validated contrast.

`window.__storyboard.duration` and `.sceneCount` provide capture metadata. `__seek` returns the clamped time, current index, scene start, elapsed time, offset and reduced-motion state. The OS [reduced-motion preference](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion) or the user's Static view checkbox removes translation immediately. Changing the preference recomputes the current state. Keyboard controls and the transcript work independently of any capture tool.

## Capture only what was rendered

Use an already installed, authorized browser renderer such as Playwright with Chromium or WebKit. These are external tools; Fabius does not include them. Keep one browser context and a fixed viewport/device scale. Wait for the module and `document.fonts.ready`, seek each frame, then capture the `.stage` element. Inspect the first, middle and last frame before encoding.

```js
// Inside an existing browser automation script; page is an authorized browser page.
await page.goto(sceneURL);
await page.waitForFunction(() => typeof window.__seek === 'function');
await page.evaluate(() => document.fonts.ready);
const duration = await page.evaluate(() => window.__storyboard.duration);
for (let frame = 0; frame < Math.ceil(duration * 25); frame++) {
  await page.evaluate(t => window.__seek(t), frame / 25);
  await page.locator('.stage').screenshot({ path: `frames/f${String(frame).padStart(4, '0')}.png` });
}
```

Create `frames/` before the loop. Pin the browser version, OS font environment, viewport and scale for pixel comparisons. Fix the stage dimensions for a video cut and prove that the longest scene fits; a responsive text layout can otherwise change height between scenes. A screenshot taken before paint settles can capture the previous scene; verify repeatability in the actual renderer, not only numeric state.

If FFmpeg is already installed and authorized, encode the verified frames separately:

```sh
ffmpeg -framerate 25 -i frames/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 21 -movflags +faststart -an scene.mp4
```

FFmpeg and its selected codec are external software with their own terms. This command requires even frame dimensions and a build with `libx264`; no encoder is installed or invoked by the kit. Inspect the resulting video for content, size, duration, clipping and readable text. Encoding a file does not establish that the intended frames were rendered.

For authored illustrations, audio, footage, fonts, complex 3D or a full video editor, choose a separately approved renderer and assets, document provenance, and check their current terms. The old imported framework recipes are intentionally absent. The new capability is a bounded, inspectable text storyboard, not replacement coverage for every former effect or framework.
