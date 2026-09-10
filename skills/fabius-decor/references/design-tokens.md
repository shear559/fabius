# Original token contract

`examples/tokens.json` is a complete `fabius-design/v1` input. Fields are closed: unknown or missing keys fail validation. All color values are opaque six-digit sRGB hex. There is no CSS expression, selector, URL, script, or file path in the schema.

| Field | Meaning | Automated check |
|---|---|---|
| `color.canvas`, `color.surface` | Page and content backgrounds | Neutral gray; paired with text, muted, border and focus |
| `color.text`, `color.muted` | Body and secondary text | Neutral gray; at least 4.5:1 against both backgrounds |
| `color.accent`, `color.onAccent` | One emphasis color and its text | `onAccent` neutral; at least 4.5:1 against accent |
| `color.border` | Visible control boundary | Neutral gray; at least 3:1 against both backgrounds |
| `color.focus` | Keyboard focus outline | Accent or neutral; at least 3:1 against both backgrounds |
| `focus.widthPx`, `focus.offsetPx` | Outline width and separation | Integers 2–8 |
| `motion.durationMs` | Entrance duration | Integer 0–500; 0 is static |
| `motion.distancePx` | Maximum entrance translation | Integer 0–24 |
| `motion.reducedMotion` | OS preference behavior | Exactly `static` |
| `motion.autoplay` | Playback policy | Exactly `false` |

The text and non-text contrast thresholds are drawn from W3C [Contrast Minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) and [Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html). The validator compares unrounded ratios. It deliberately uses 4.5:1 even for large text and checks declared control boundaries, rather than trying to infer every WCAG exception.

The monochrome policy, numeric focus dimensions, 500 ms ceiling, 24 px ceiling and no-autoplay rule are **Fabius house constraints**, not a claim that WCAG prescribes those exact values. A token file cannot establish that focus remains visible and unobscured in an actual page: inspect [Focus Not Obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html) behavior in the rendered context.

`tokensCSS` emits the color, focus and motion variables plus a small fixed spacing, radius and system-font vocabulary. The generated scene uses those names; an integrating project can map them to its existing semantic names. Validate each theme separately. This version does not generate a theme switcher or validate CSS `color-mix()`, alpha blending, perceptual color spaces, data palettes or gradient backgrounds.

The original example's accent is a local design choice, not a copied brand palette. Keep real project identity in the token input. Choosing a new accent requires recalculating its foreground and focus pairings; a visually attractive hue alone is insufficient.
