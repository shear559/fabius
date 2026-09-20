<!-- © 2026 shear559 · fabius · reference depth for skills/fabius-parcus/SKILL.md -->

# Fabius Nuntius — reporting shape for a reader who must act

Load when the reply is a report its reader will act on: a failure, a job spanning turns, a long
list, a side finding, a set of options. Opening order, channel fit and the never-trim floor stay
in [SKILL.md](../SKILL.md); this file adds only the shape.

## 1 · Failure reports — the unknown cause is a legal value

A required slot can pull a guess into it (a plausible failure mode), so each one has a stated
value for absent evidence.

- **Cause** comes only from evidence supplied or observed this session. Otherwise write
  `cause not identified` plus the one check that separates the candidates (disciplina's
  [diagnose step](../../fabius-disciplina/SKILL.md)). No fix for an unevidenced cause.
- Test a shape change on partly succeeded work with no cause in the prompt; pass =
  `cause not identified` and no fix.

## 2 · Position line and the close

Applies when work spans turns and the reader acts or decides between them.

- One position line per turn, directly under the result line:
  `done 4/9 · holds: <what now works> · then: <step>`. The reader never holds the plan
  off-screen. When the next step is the reader's, `then:` moves to the close: write it once,
  last.
- Where the host has a plan or task tool, it carries the state; prose does not repeat the plan.
- Numbered steps sit inside the complete-prose rule for order-sensitive procedures: number
  them, keep every sentence whole.
- **Close.** When something remains open, the last line is exactly ONE named action the reader
  can start at once — never an open invitation. The first line stays result-or-failure.
- **Two-line test.** Read the first and last lines alone: they must say what happened and what
  to do next. Reorder if not.

## 3 · Lists, side findings, depth and options

- **Shortened list.** State the count withheld; the rest stays available on request. A display
  limit never bounds the investigation or what is retained. Where completeness is the
  deliverable (audit, inventory, findings), group and rank — never truncate. No fixed size
  here; interface chunking is decor's
  ([design-critique.md](../../fabius-decor/references/design-critique.md)).
- **Side finding.** A discovery outside the requested scope is reported after the requested
  work, once, as a separate offer the reader can decline. Exception: security, data loss, or a
  loss you caused — stated at once and first, with its own ask: it never rides the §2 close,
  whose one action stays the requested work's.
- **Depth requested.** Removes the length limit and nothing else: the first line is still the
  result, the §2 close still ends it, and headings mark where a reader can come back in.
- **Options asked.** Keep the alternatives: rank them, lead with the pick, and give each the
  single trade-off that would change the choice.
- **Conversational message.** A brief natural reply; no invented task structure.

## 4 · Wording pass

- **Hedge (qualifier) keep-test.** A qualifier stays only if you can name what is uncertain,
  and then it says so: `probably fixed` → `fixed for CSV; XLSX not run`. Otherwise delete it.
  Mercatus applies the same test to a user's draft
  ([prose-tell-lint.md](../../fabius-mercatus/references/prose-tell-lint.md)).
- **Effort estimate** names units, the switching condition, who executes, and its basis:
  `1 h for you if the migration reverses cleanly, a day if not — basis: this repo's last two`.
  No basis → `not estimated`.

Informed by **i-have-adhd** (ayghri, MIT) — studied for report shape for a reader who must act; and **no-ai-slop** (petergyang, MIT) — studied for the qualifier keep-condition; re-expressed in fabius's own voice; no upstream files bundled. See credits/README.md.
