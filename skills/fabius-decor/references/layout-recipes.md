# Original composition recipes

Choose the structure from the content and the action. These compact recipes are authored for Fabius; they are not extracts from the removed template galleries. Load the CSS emitted by `design.mjs css` first.

## Reading surface

Use for an explanation, changelog or release note. Keep prose at a readable measure; separate sections with headings and space. Render real evidence immediately beside the claim it supports. A heading and an honest paragraph beat a row of empty decorative cards.

```css
.reading { max-inline-size: 65ch; margin-inline: auto; padding: var(--space-medium); }
.reading > * + * { margin-block-start: var(--space-medium); }
.reading p { line-height: 1.6; }
.reading a { color: var(--color-text); text-decoration: underline; text-underline-offset: .2em; }
.reading :focus-visible { outline: var(--focus-width) solid var(--color-focus); outline-offset: var(--focus-offset); }
```

Use `main`, one `h1`, meaningful `h2` headings, real links, and the document language. Avoid enforcing a height on prose. Inspect the longest heading and a narrow viewport before shipping.

## Primary content with supporting evidence

Use for a project description with an image, reproducible artifact, or quoted source. On mobile, the explanation precedes its evidence. On a wider viewport, let both remain visible together. Do not add a fake product screen merely to fill the evidence column.

```css
.evidence-layout { display: grid; gap: var(--space-medium); align-items: start; }
.evidence-layout > * { min-inline-size: 0; }
.evidence-layout img, .evidence-layout svg { display: block; max-inline-size: 100%; block-size: auto; }
@media (min-width: 48rem) {
  .evidence-layout { grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: var(--space-large); }
}
```

Use a real `figure` and caption when the media explains the text. Give informative images an accurate alternative. Decorative atmosphere can use the existing accent in a gradient moment around the media; keep text on a validated solid surface. Do not make controls into a color display.

## Action and feedback

Use a native form and one primary action. A field has an explicit label, instructions before input, and an error attached to the field. Preserve entered data after a recoverable error. A success message states the actual completed action; it cannot imply a server write that never happened.

```html
<label for="title">Scene title</label>
<p id="title-help">Use the supplied claim or a descriptive sentence.</p>
<input id="title" name="title" type="text" required maxlength="120" aria-describedby="title-help title-error">
<p id="title-error" hidden></p>
<button type="submit">Save title</button>
<p role="status" aria-live="polite"></p>
```

```css
input[type="text"], button {
  font: inherit; min-block-size: 44px; padding: .65rem 1rem;
  color: var(--color-text); background: var(--color-surface);
  border: 1px solid var(--color-border); border-radius: var(--radius-control);
}
input[type="text"] { inline-size: 100%; }
button { cursor: pointer; touch-action: manipulation; }
button:active { color: var(--color-surface); background: var(--color-text); }
:focus-visible { outline: var(--focus-width) solid var(--color-focus); outline-offset: var(--focus-offset); }
[hidden] { display: none; }
```

This is a markup recipe, not a working save backend. Wire its submit handler to the actual operation, set `aria-invalid` only on an invalid field, place the error text in `title-error`, and move focus when necessary. Test empty, valid, failed and retry paths. The included storyboard's working controls demonstrate a narrower local state change; they do not claim remote persistence.

## Data and direction

Use the existing [Figura method](visualization.md) for measured data. Supply values and units; leave missing data visibly missing. Use logical CSS properties and isolate embedded direction changes; see [RTL/Bidi](rtl-bidi.md). Do not mirror a chart's time axis accidentally when adapting layout direction.
