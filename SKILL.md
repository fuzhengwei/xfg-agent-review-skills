---
name: xfg-agent-review-skills
description: Evaluate coding, tool-calling, terminal, browser, desktop, and long-horizon agent capability with a reproducible readiness suite and standard external benchmarks.
metadata:
  short-description: Run standardized agent capability reviews
---

# XFG Agent Review

Use this skill when the user asks to evaluate, benchmark, compare, regression-test, or qualify an agent. It supports local reproducible scoring and evidence collection for selected external benchmarks. It is not a model-knowledge exam and does not infer ability from a conversation alone.

## Required workflow

1. First analyze the request. Do not start a benchmark, run commands, create reports, or collect screenshots yet.
2. Produce a short evaluation plan containing:
   - objective;
   - agent command or wrapper;
   - model/channel configuration (default, or explicit profile);
   - suite/tasks and official benchmarks to run;
   - evidence to collect;
   - pass/fail criteria;
   - estimated runtime, cost, and risks;
   - what will not be tested.
3. Ask the user for explicit confirmation, for example: “确认执行后我再开始测评。”
4. Wait for an affirmative confirmation such as “确认执行”, “开始”, or “批准”. If the user asks to change scope, update the plan and confirm again.
5. After confirmation, run `python3 /path/to/xfg-agent-review-skills/scripts/agent_review.py validate`.
6. Run readiness with an absolute agent command:
   `python3 /path/to/xfg-agent-review-skills/scripts/agent_review.py run --agent-command '<absolute-agent-command>' --output agent-review-report.json --markdown`
7. If the user asks to compare model providers or models, pass `--model-config` and `--profile`. If they do not ask, keep the agent wrapper's default configuration.
8. If the request involves real UI, screenshots, conversation quality, or runtime behavior, run with `--screenshot-command` and a JSON `--review-command` when available. If screenshot capture is unavailable or fails, continue with workspace files, transcript, logs, and deterministic validators; do not abort the evaluation solely because a screenshot is missing.
9. Review task-level checks, artifacts, timing, and failures. Never replace a failed task with a narrative explanation.
10. For deeper qualification, run the external benchmark selected from `registry/benchmarks.json` in its official repository and retain the official result file. Record `passed` only with immutable official evidence.
11. For a comparison or release decision, combine the readiness score with official benchmark scores and report token cost, wall time, tool-call count, recovery rate, and safety violations when available.

## Agent protocol

The target agent command must read this JSON object from stdin and execute inside the provided workspace:

```json
{"task_id": "...", "prompt": "...", "workspace": "..."}
```

It must exit zero only when it believes the task is complete. Non-empty stdout must be a JSON object; stderr is reserved for diagnostics. The command is invoked with the task workspace as its working directory. Wrappers that require repository-relative files must use absolute paths.

Read `references/evaluation-standards.md` before assigning capability levels. Read `references/benchmark-catalog.md` when selecting an external benchmark. Read `references/official-benchmark-runbook.md` for source-level execution guidance.

## Harness reliability scenarios

When the goal is to qualify an agent **harness** (tool layer, guards, transport) rather than raw task completion — e.g. after a hardening change, or when the user reports intermittent tool errors, empty tool args, wrong paths, or "memory drift" in long conversations — read `references/harness-reliability-e2e.md` and:

1. Classify the reported failure into transport, model-behavior, or harness layers before proposing tests; the layer decides the test design.
2. Run the `suites/harness-reliability.json` suite (via `--suite`) for deterministic probes: memory-drift recovery, short-anchor editing, wrong-path rescue, long-context recall, and tool-call observability.
3. For full verification, run the five-phase E2E pattern from the reference (guard determinism → external interference → normal flow + ledger fidelity → natural agent flow on the production channel → global side effects), asserting on host-side evidence and transport logs, never on in-page diagnostics alone.
4. Validate suites with `validate --suite <path>` before running; report which guards were provably triggered and which were not exercised.

## Reporting rules

- Report the exact readiness success rate, not a qualitative upgrade.
- Use the generated `scoring` object: report every capability score, the 0–100 overall score, the readiness level, and every optimization action.
- Quote failed task IDs before recommending changes. Do not turn a failed validator into a vague qualitative comment.
- Include failed task IDs and validator messages.
- Do not claim external benchmark results unless the official benchmark was run and its output is retained.
- Treat a changed prompt, model, tools, configuration, workspace, or dataset version as a new evaluation.
- Preserve generated artifacts under `<output-stem>-artifacts` for auditability.
