#!/usr/bin/env node
// Imported nested contracts were retired; enforce the reviewed discovery surface.
import { readdirSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = join(dirname(fileURLToPath(import.meta.url)), '..', 'skills');
const failures = [];
let skills = 0;
function walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isSymbolicLink()) { failures.push(`${relative(root, path)}: symlink in skill content`); continue; }
    if (entry.isDirectory()) { walk(path); continue; }
    if (entry.name === 'REFERENCE.md') failures.push(`${relative(root, path)}: retired nested contract`);
    if (entry.name === 'SKILL.md') {
      skills++;
      if (relative(root, path).split('/').length !== 2) failures.push(`${relative(root, path)}: nested discoverable skill`);
    }
  }
}
walk(root);
if (skills !== 15) failures.push(`expected 15 reviewed public skills, found ${skills}`);
for (const failure of failures) console.error(`FAIL ${failure}`);
console.log(`${failures.length ? 'FAIL' : 'PASS'} reference boundary: ${skills} public contracts, ${failures.length} errors`);
process.exitCode = failures.length ? 1 : 0;
