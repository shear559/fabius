# Fabius diagnosis and evidence examples

These hypothetical examples explain a method; their numbers and outcomes are not measurements of Fabius or another product.

## Shared state disguised as a logout bug

Suppose switching accounts exposes the previous account's cart. Preserve the two-session sequence and capture which identity each request resolves to. Reduce the case to requests only after confirming that doing so retains the symptom.

A stale cookie, an incorrect server-side identity and a response cache shared between users make different predictions. Compare the authenticated identity, the cache key and the response owner at the boundary. If the cache key omits the user, test the corrected key with two accounts, a logout and a repeated read. Do not log session credentials to gather that evidence.

The regression oracle should fail when the cache key is changed back. Also check that anonymous reads cannot reach an authenticated response. Clearing the cache may hide the symptom temporarily; it does not establish correct isolation.

## Latency without a stack trace

A page loads slowly. First hold browser, viewport, network profile, cache state and interaction constant. Gather enough repeated runs to see variability. Then remove or defer one suspected resource in a controlled variant and compare the same observation, such as the time at which the primary content becomes usable.

A smaller image is useful only if it improves the measured path without harming the visual requirement. A faster warm-cache run is not a cold-load improvement. After a code change, repeat the relevant observation against the deployed build and record the conditions with the result.

## An oracle that checks the wrong thing

A test asserts that a save function was called. The application still writes the wrong record. Replace or supplement that assertion with a read of the resulting record and its expected identity and fields. Keep an isolated adapter test for serialization if it serves a separate failure mode.

Similar traps include checking that an element has a `hidden` property while CSS still renders it, checking an HTTP success while the body contains an application error, and counting generated files without opening the requested artifact. Choose the assertion at the boundary where the user's requirement becomes observable.

## Bounded review of competing designs

A service might benefit from a queue. Compare its current failure behavior with a queue-backed alternative using actual retry, ordering, latency and recovery requirements. If the deciding uncertainty is idempotency after a crash, prototype that failure boundary first. A diagram showing an extra queue is not evidence that duplicate work is safe.

Review findings should identify the input, path, consequence and fix. Treat a counterexample or an existing control as evidence against the finding. Keep speculative improvements distinct from defects that prevent the requested behavior.

## Connect the instruction to the check

For a helper that maps a change plan to recorded tests, useful checks include an uncovered source, a missing check, a changed source hash, a changed acceptance condition and a failed or skipped test. These are exercised by [evidence.test.mjs](../scripts/evidence.test.mjs). They show which inconsistencies the ledger can detect; they do not prove the tests named by an arbitrary caller are adequate.

For new behavior, prefer a test through the real input/output seam. A mock returning the fixture value proves the mock was configured. Tests that assert exact headings or prose generally protect wording rather than behavior. Use such checks only where the wording itself is a protocol or user requirement.
