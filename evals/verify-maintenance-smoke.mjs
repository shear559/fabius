#!/usr/bin/env node
// Maintenance-smoke receipt freshness — the rule in evals/maintenance-smoke/README.md made mechanical.
//
// A receipt (evals/maintenance-smoke/<date>[-v<release>].json) records, per run, the exact
// input files the responding context read (`input_files[].sha256`) and the case ids it
// answered. A case's receipt is valid only while every listed input still hashes identically
// in the working tree; a case whose input changed after its last run is STALE and must be
// rerun before the next release; a case that no receipt reports is UNRUN; a receipt id that
// cases.json no longer lists is an ORPHAN.
//
//   node evals/verify-maintenance-smoke.mjs                 # dev: unrun/orphan FAIL, stale is a NOTE
//   node evals/verify-maintenance-smoke.mjs --mode=release  # release / proof-upgrade: stale FAILs too
//
// Two ways a run can bind the case prompt: `prompt_sha256` on the response (sha256 of that
// case's `prompt` string — appending an unrelated case then invalidates nothing), or the
// whole-file hash of cases.json in `input_files` (older receipts; any edit to the file counts).
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";

const ROOT = process.env.FABIUS_VERIFY_ROOT
  ? resolve(process.env.FABIUS_VERIFY_ROOT)
  : join(dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const mode = args.find((a) => a.startsWith("--mode="))?.split("=")[1] || "dev";
if (!["dev", "release", "proof-upgrade"].includes(mode)) {
  throw new Error("usage: node evals/verify-maintenance-smoke.mjs [--mode=dev|release|proof-upgrade]");
}
const strict = mode !== "dev";
const DIR = "evals/maintenance-smoke";
const CASES = `${DIR}/cases.json`;
const SCHEMA = "fabius-maintenance-smoke/v1";
const sha256hex = (b) => createHash("sha256").update(b).digest("hex");
const checks = [];
const check = (name, pass, detail = "") => checks.push({ name, pass: !!pass, detail });

const cases = JSON.parse(readFileSync(join(ROOT, CASES), "utf8")).cases || [];
const caseIds = cases.map((c) => c.id);
const promptHash = new Map(cases.map((c) => [c.id, sha256hex(Buffer.from(String(c.prompt ?? ""), "utf8"))]));
check("cases.json lists unique case ids", new Set(caseIds).size === caseIds.length && caseIds.length > 0, `${caseIds.length} cases`);

const receiptFiles = readdirSync(join(ROOT, DIR))
  .filter((f) => f.endsWith(".json") && f !== "cases.json").sort();
const receipts = receiptFiles.map((f) => ({ file: f, ...JSON.parse(readFileSync(join(ROOT, DIR, f), "utf8")) }));
const badSchema = receipts.filter((r) => r.schema !== SCHEMA || !Array.isArray(r.runs)).map((r) => r.file);
check(`every receipt declares ${SCHEMA} with a runs array`, badSchema.length === 0,
  badSchema.length ? `malformed: ${badSchema.join(", ")}` : `${receipts.length} receipts`);

// latest run per case id: receipts are date-named and sorted ascending, later run wins
const latest = new Map();
const reported = new Set();
for (const r of receipts) {
  for (const run of r.runs || []) {
    for (const resp of run.responses || []) {
      if (!resp?.id) continue;
      reported.add(resp.id);
      latest.set(resp.id, { receipt: r.file, date: r.date || "", run, resp });
    }
  }
}

const unrun = caseIds.filter((id) => !reported.has(id));
check("every cases.json id is reported by at least one receipt", unrun.length === 0,
  unrun.length ? `unrun: ${unrun.join(", ")}` : `${caseIds.length}/${caseIds.length} reported`);
const orphans = [...reported].filter((id) => !caseIds.includes(id)).sort();
check("every receipt id is a case in cases.json", orphans.length === 0,
  orphans.length ? `orphans: ${orphans.join(", ")}` : `${reported.size} ids, all listed`);

// freshness: every input the latest run listed must hash identically today
const hashNow = new Map();
const currentHash = (p) => {
  if (!hashNow.has(p)) hashNow.set(p, existsSync(join(ROOT, p)) ? sha256hex(readFileSync(join(ROOT, p))) : "MISSING");
  return hashNow.get(p);
};
const fresh = [], stale = [];
for (const id of caseIds) {
  const l = latest.get(id);
  if (!l) continue;
  const changed = [];
  for (const input of l.run.input_files || []) {
    if (!input?.path) continue;
    if (input.path === CASES && l.resp.prompt_sha256) {
      if (l.resp.prompt_sha256 !== promptHash.get(id)) changed.push(`${CASES} (prompt)`);
      continue;
    }
    if (currentHash(input.path) !== input.sha256) changed.push(input.path);
  }
  if (l.resp.prompt_sha256 && !(l.run.input_files || []).some((i) => i?.path === CASES)
      && l.resp.prompt_sha256 !== promptHash.get(id)) changed.push(`${CASES} (prompt)`);
  if ((l.run.input_files || []).length === 0) changed.push("(no input_files recorded)");
  (changed.length ? stale : fresh).push({ id, date: l.date, receipt: l.receipt, changed });
}
const total = caseIds.length;
const staleDetail = stale.map((s) => `${s.id} [${s.date || s.receipt}: ${s.changed.join(", ")}]`).join("; ");
const summary = `fresh ${fresh.length}/${total} · stale ${stale.length}/${total}` + (stale.length ? ` (${stale.map((s) => s.id).join(", ")})` : "");
check(strict
  ? "every case's latest receipt still hashes to its recorded inputs (release requires a fresh rerun)"
  : "receipt freshness measured (stale receipts are a NOTE in dev mode, a FAIL in release)",
  strict ? stale.length === 0 : true, summary);

console.log(`== fabius maintenance-smoke receipts (${mode}) ==\n`);
for (const c of checks) console.log(`  ${c.pass ? "PASS" : "FAIL"}  ${c.name}${c.detail ? ` — ${c.detail}` : ""}`);
const failed = checks.filter((c) => !c.pass).length;
console.log(`\n== ${checks.length - failed} passed · ${failed} failed ==`);
console.log(`  ${summary}`);
if (stale.length) {
  console.log(`  ${strict ? "FAIL" : "NOTE"}  stale inputs — ${staleDetail}`);
  if (!strict) console.log("  NOTE  dev mode reports stale receipts; --mode=release requires every stale case rerun and a new receipt committed.");
}
process.exitCode = failed ? 1 : 0;
