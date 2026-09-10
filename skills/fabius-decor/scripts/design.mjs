#!/usr/bin/env node
// Original Fabius design kit. No downloaded templates, assets or runtime packages.
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const colors = ['canvas', 'surface', 'text', 'muted', 'border', 'accent', 'onAccent', 'focus'];
const hex = /^#[0-9a-f]{6}$/i;
const escapeHTML = value => value.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const channels = color => {
  if (typeof color !== 'string' || !hex.test(color)) throw new Error('Color must be a six-digit hex value');
  return [1, 3, 5].map(i => parseInt(color.slice(i, i + 2), 16));
};
const luminance = color => channels(color).map(c => c / 255).map(c => c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4).reduce((sum, c, i) => sum + c * [0.2126, 0.7152, 0.0722][i], 0);
export function contrast(a, b) {
  const x = luminance(a), y = luminance(b);
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}
function shape(value, keys, path, issues) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) { issues.push({ path, message: 'Expected an object' }); return false; }
  for (const key of keys) if (!Object.hasOwn(value, key)) issues.push({ path: `${path}.${key}`, message: 'Required field' });
  for (const key of Object.keys(value)) if (!keys.includes(key)) issues.push({ path: `${path}.${key}`, message: 'Unsupported field' });
  return true;
}
function bounded(value, min, max, path, issues, integer = false) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < min || value > max || (integer && !Number.isInteger(value))) issues.push({ path, message: `Expected ${integer ? 'integer' : 'number'} from ${min} to ${max}` });
}
export function validateTokens(value) {
  const issues = [], ratios = [];
  if (!shape(value, ['schema', 'color', 'focus', 'motion'], 'tokens', issues)) return { valid: false, issues, contrast: ratios };
  if (value.schema !== 'fabius-design/v1') issues.push({ path: 'schema', message: 'Expected fabius-design/v1' });
  if (shape(value.color, colors, 'color', issues)) {
    for (const role of colors) {
      const c = value.color[role];
      if (typeof c !== 'string' || !hex.test(c)) { issues.push({ path: `color.${role}`, message: 'Expected six-digit hex color' }); continue; }
      const [r, g, b] = channels(c);
      if (!['accent', 'focus'].includes(role) && (r !== g || g !== b)) issues.push({ path: `color.${role}`, message: 'Functional palette uses neutral grays plus one accent' });
      if (role === 'focus' && !(r === g && g === b) && c.toLowerCase() !== (typeof value.color.accent === 'string' ? value.color.accent.toLowerCase() : '')) issues.push({ path: 'color.focus', message: 'Focus must use the accent or a neutral gray' });
    }
    for (const [front, back, minimum] of [
      ['text', 'canvas', 4.5], ['text', 'surface', 4.5], ['muted', 'canvas', 4.5], ['muted', 'surface', 4.5],
      ['onAccent', 'accent', 4.5], ['border', 'canvas', 3], ['border', 'surface', 3], ['focus', 'canvas', 3], ['focus', 'surface', 3],
    ]) {
      if (![value.color[front], value.color[back]].every(c => typeof c === 'string' && hex.test(c))) continue;
      const ratio = contrast(value.color[front], value.color[back]);
      ratios.push({ foreground: front, background: back, ratio, minimum });
      if (ratio < minimum) issues.push({ path: `color.${front}`, message: `Contrast against ${back} is ${ratio.toFixed(2)}; needs ${minimum}` });
    }
  }
  if (shape(value.focus, ['widthPx', 'offsetPx'], 'focus', issues)) {
    bounded(value.focus.widthPx, 2, 8, 'focus.widthPx', issues, true);
    bounded(value.focus.offsetPx, 2, 8, 'focus.offsetPx', issues, true);
  }
  if (shape(value.motion, ['durationMs', 'distancePx', 'reducedMotion', 'autoplay'], 'motion', issues)) {
    bounded(value.motion.durationMs, 0, 500, 'motion.durationMs', issues, true);
    bounded(value.motion.distancePx, 0, 24, 'motion.distancePx', issues, true);
    if (value.motion.reducedMotion !== 'static') issues.push({ path: 'motion.reducedMotion', message: 'Reduced motion must be static' });
    if (value.motion.autoplay !== false) issues.push({ path: 'motion.autoplay', message: 'Autoplay is not supported' });
  }
  return { valid: issues.length === 0, issues, contrast: ratios };
}
export function tokensCSS(tokens) {
  const result = validateTokens(tokens);
  if (!result.valid) throw new Error(`Invalid design tokens: ${JSON.stringify(result.issues)}`);
  return `:root {\n${colors.map(key => `  --color-${key}: ${tokens.color[key]};`).join('\n')}
  --focus-width: ${tokens.focus.widthPx}px;
  --focus-offset: ${tokens.focus.offsetPx}px;
  --motion-duration: ${tokens.motion.durationMs}ms;
  --motion-distance: ${tokens.motion.distancePx}px;
  --space-small: .75rem;
  --space-medium: 1.5rem;
  --space-large: 3rem;
  --radius-control: .5rem;
  --font-body: system-ui, sans-serif;
}\n`;
}
export function validateStoryboard(board) {
  const issues = [];
  if (!shape(board, ['schema', 'title', 'description', 'lang', 'dir', 'tokens', 'scenes'], 'storyboard', issues)) return { valid: false, issues };
  if (board.schema !== 'fabius-storyboard/v1') issues.push({ path: 'schema', message: 'Expected fabius-storyboard/v1' });
  const string = (value, max, path) => { if (typeof value !== 'string' || !value.trim() || value.length > max) issues.push({ path, message: `Expected nonempty text up to ${max} characters` }); };
  string(board.title, 120, 'title'); string(board.description, 500, 'description');
  if (typeof board.lang !== 'string' || !/^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$/.test(board.lang)) issues.push({ path: 'lang', message: 'Expected a language tag such as en or he-IL' });
  if (!['ltr', 'rtl'].includes(board.dir)) issues.push({ path: 'dir', message: 'Expected ltr or rtl' });
  issues.push(...validateTokens(board.tokens).issues.map(i => ({ ...i, path: `tokens.${i.path}` })));
  if (!Array.isArray(board.scenes) || board.scenes.length < 1 || board.scenes.length > 12) issues.push({ path: 'scenes', message: 'Expected 1 to 12 scenes' });
  else {
    const ids = new Set();
    board.scenes.forEach((scene, i) => {
      const path = `scenes[${i}]`;
      if (!shape(scene, ['id', 'label', 'title', 'body', 'durationSeconds'], path, issues)) return;
      if (typeof scene.id !== 'string' || !/^[a-z][a-z0-9-]{0,39}$/.test(scene.id) || ids.has(scene.id)) issues.push({ path: `${path}.id`, message: 'Expected unique lowercase identifier' });
      ids.add(scene.id);
      string(scene.label, 40, `${path}.label`); string(scene.title, 120, `${path}.title`); string(scene.body, 600, `${path}.body`);
      bounded(scene.durationSeconds, 1, 60, `${path}.durationSeconds`, issues);
    });
  }
  return { valid: issues.length === 0, issues };
}
export async function renderScene(board) {
  const result = validateStoryboard(board);
  if (!result.valid) throw new Error(`Invalid storyboard: ${JSON.stringify(result.issues)}`);
  const template = name => readFile(new URL(`../templates/${name}`, import.meta.url), 'utf8');
  const total = board.scenes.reduce((sum, scene) => sum + scene.durationSeconds, 0);
  const sceneHTML = board.scenes.map((scene, i) => `<article class="scene" data-scene="${i}"${i ? ' hidden' : ''} aria-labelledby="title-${scene.id}">
      <p class="eyebrow"><bdi>${escapeHTML(scene.label)}</bdi></p>
      <h2 id="title-${scene.id}"><bdi>${escapeHTML(scene.title)}</bdi></h2>
      <p class="body-copy"><bdi>${escapeHTML(scene.body)}</bdi></p>
    </article>`).join('\n');
  const html = `<!doctype html>
<html lang="${board.lang}" dir="${board.dir}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escapeHTML(board.title)}</title><meta name="description" content="${escapeHTML(board.description)}">
<link rel="icon" href="data:,"><link rel="stylesheet" href="./scene.css"><script type="module" src="./scene.mjs"></script></head>
<body><main class="shell">
  <header class="masthead"><h1><bdi>${escapeHTML(board.title)}</bdi></h1><p><bdi>${escapeHTML(board.description)}</bdi></p></header>
  <section class="stage" aria-label="Storyboard scene">${sceneHTML}</section>
  <form class="transport" aria-label="Storyboard controls">
    <div class="transport-heading"><label for="time">Timeline</label><output id="time-label" for="time" dir="ltr">0.00 / ${total.toFixed(2)} s</output></div>
    <input id="time" type="range" min="0" max="${total}" step="0.01" value="0" aria-label="Timeline in seconds">
    <div class="transport-actions"><button type="button" id="previous">Previous scene</button><button type="button" id="next">Next scene</button><label class="static-control"><input type="checkbox" id="static"> Static view</label></div>
    <p id="status" role="status" aria-live="polite">${escapeHTML(board.scenes[0].label)}</p>
  </form>
  <details class="transcript"><summary>Read all scenes</summary>${board.scenes.map(scene => `<section><h2><bdi>${escapeHTML(scene.title)}</bdi></h2><p><bdi>${escapeHTML(scene.body)}</bdi></p></section>`).join('')}</details>
</main></body></html>\n`;
  return {
    'index.html': html,
    'scene.css': tokensCSS(board.tokens) + await template('scene.css'),
    'timeline.mjs': await template('timeline.mjs'),
    'scene.mjs': `import { mount } from './timeline.mjs';\nmount(${JSON.stringify(board).replace(/</g, '\\u003c').replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029')});\n`,
    'storyboard.json': JSON.stringify(board, null, 2) + '\n',
  };
}
async function main(args) {
  const [command, input, flag, output, ...extra] = args;
  if (!['check', 'css', 'scene'].includes(command) || !input || extra.length || (command === 'check' ? flag !== undefined : flag !== '--out' || !output)) throw new Error('Usage: design.mjs check tokens.json | css tokens.json --out new.css | scene storyboard.json --out new-directory');
  const value = JSON.parse(await readFile(resolve(input), 'utf8'));
  if (command === 'check') {
    const result = validateTokens(value); console.log(JSON.stringify(result, null, 2));
    if (!result.valid) process.exitCode = 1;
  } else if (command === 'css') {
    const css = tokensCSS(value); await writeFile(resolve(output), css, { flag: 'wx' }); console.log(`Wrote ${resolve(output)}`);
  } else {
    const files = await renderScene(value);
    await mkdir(resolve(output)); // Exclusive directory creation: existing output belongs to its owner.
    for (const [name, content] of Object.entries(files)) await writeFile(join(resolve(output), name), content, { flag: 'wx' });
    console.log(`Wrote ${Object.keys(files).length} files to ${resolve(output)}`);
  }
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main(process.argv.slice(2)).catch(error => { console.error(error.message); process.exitCode = 1; });
