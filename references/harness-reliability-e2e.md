# Harness Reliability E2E Testing

Methodology for evaluating whether an agent harness (tool layer, guards, transport) stays reliable in real, long conversations — not just in happy-path demos. Distilled from a production hardening cycle on a desktop coding agent (Tauri + TypeScript) where the failure modes were transport truncation, model memory drift, and guard gaps.

## 1. Classify failures before fixing or reporting

Every anomalous tool error belongs to exactly one of three layers. Diagnose the layer first; the fix and the test differ per layer.

| Layer | Signature | Typical evidence |
|---|---|---|
| L1 Transport | JSON cut mid-token yet syntactically "complete" args after structural completion; errors cluster in bursts; gateway sends `[DONE]` early or swallows the tail | burst pattern across unrelated tools; identical payload succeeds on retry; raw SSE tail missing |
| L2 Model behavior | Path typos on plausible-but-wrong directories; `old_string` with truncated identifiers and drifted indentation; empty/placeholder tool args; the model "reconstructs" content it saw many rounds ago | the wrong payload is internally coherent (a summary, not noise); failure only appears when the original observation is far away or compressed |
| L3 Harness | Correct guard missing; error message is a dead-end one-liner; a tool succeeds without recording evidence; state silently degrades to in-memory | the same L2 mistake is recoverable in one round under a good harness, irrecoverable under a bad one |

Reporting rule: never attribute to "the model" what a missing guard turned into an unrecoverable failure, and never attribute to the harness a payload the transport corrupted.

## 2. Test through the production channel

- Drive the agent through the **same gateway/relay it uses in production** (including local gateways), not a direct vendor API. Transport-layer defects only reproduce on the real channel.
- If the gateway is suspected of corrupting streams, prove it with a stress script that replays many requests and counts truncated/early-`[DONE]` responses. Intermittency (e.g. 1 in 10) is a finding, not noise — report the measured rate.
- Keep one record of gateway version/restart state: a gateway fix that requires a restart is "pending", not "done".

## 3. Five-phase E2E script pattern

Run one scripted session against a disposable project, in phases. Phases A–C are deterministic (script drives the harness directly, no model IQ involved); phase D uses a real model; phase E checks cross-session side effects.

- **A — Guard determinism.** Provoke each guard with a crafted bad payload and assert the exact structural refusal: unobserved-file edit → rejected with a "read first" directive; memory-reconstructed `old_string` (truncated token + drifted indentation) → rejected with the *real* lines quoted plus remedies. The file must be byte-identical after refusal.
- **B — External interference.** Have the host modify a file after the agent observed it; the next edit must be refused as stale, never applied blindly.
- **C — Normal flow + ledger fidelity.** Perform a legitimate read→edit; verify success, and verify any persistence (state ledger, journal) landed with a fingerprint the host independently recomputes.
- **D — Natural agent flow under a real model.** Give the agent a realistic multi-step task (e.g. "analyze this project and fix X") through the production channel. Count tool calls per tool from the transport log; assert zero guard false-positives, zero unrecovered tool failures, and that the final artifact is correct.
- **E — Global side effects.** Verify cross-session artifacts (model statistics, path registers) were written and increment correctly.

Assertions must run on the host (filesystem, independent recomputation), never only inside the page under test.

## 4. Evidence: trust the transport log, not the page

- Instrument the single funnel where every tool call passes (an IPC bridge, a proxy, a request interceptor). Log timestamp, tool name, args length, and outcome for every call.
- In-page console/diag output is secondary evidence: page-level writers can silently fail (unsupported plugin commands, sandboxing). When page diag and transport log disagree, the transport log wins.
- Derive counts (reads, writes, guard triggers) by filtering the transport log with **UTC** timestamps; local/UTC mixups silently produce empty forensic windows.
- A page-level feature that "works on desktop but silently no-ops in the browserized E2E" is itself a finding: it means the feature bypassed the abstraction layer. Fix the layering, not the test.

## 5. Known traps (each one burned a real session)

1. Attach console/page-error listeners **after** page creation; before it, they throw and kill the harness script.
2. Never edit the same file with parallel tool calls — last write wins and the earlier edit is silently lost. Edit serially; let the compiler/tests catch what you missed.
3. Persistence services must go through the project's storage abstraction, not platform plugin APIs directly, or browserized E2E degrades them to memory-only without an error.
4. Host-side reads racing debounced writes produce false "not persisted" failures. Poll with a deadline instead of reading once.
5. When a sub-check fails, reproduce it in a minimal probe before blaming the product — a one-file probe isolates timing/module-transform artifacts from real defects.
6. Suites that import the app must use the same runtime/package versions as the app, or failures are environment noise.

## 6. Guard design principles being verified

The E2E phases above verify guards that follow these rules (from production hardening, aligned with DeepSeek-Harness practice):

1. **Observe-before-mutate**: rejecting an edit to an unobserved file is cheaper than repairing a blind edit.
2. **Errors must be executable**: every refusal names the remedy ("re-read the file, then retry") and, where possible, quotes the real content with line numbers.
3. **Escalating reminders beat silent loops**: repeated identical calls get progressively stronger reminders (observe-and-enrich), and only terminate after a hard threshold — a reminder round is a recoverable round.
4. **Short anchors over long quotes**: the discipline "old_string must be short but unique, copied verbatim from the most recent tool result" removes most memory-drift failures before any guard fires.
5. **Freshness is a fact, not a memory**: fingerprint observed files; stale cognition is detectable deterministically.
6. **A failed rescue attempt is data**: record model error rates per model (validation failures, empty args) so weak-model classification becomes measurement instead of name matching.

## 7. Honest reporting checklist

- State which guards/features were **not actually triggered** by the natural-flow phase (e.g. the model used correct absolute paths throughout), and note which diag counters will prove them in daily use.
- Separate test-harness failures from product failures explicitly (re-run after fixing the harness; do not silently convert a harness bug into a pass).
- List known gaps left open (e.g. `multi_edit` path without guards, path-register not yet wired into rescue) rather than implying full coverage.
- Keep the regression baseline visible: unit tests total, type-check status of touched files, and the E2E phase table side by side.
