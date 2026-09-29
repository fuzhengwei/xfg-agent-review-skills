---
name: xfg-agent-review-skills
description: Evaluate coding, tool-calling, terminal, browser, desktop, and long-horizon agent capability with a reproducible readiness suite and standard external benchmarks.
metadata:
  short-description: Run standardized agent capability reviews
---

# XFG Agent Review

Use this skill when the user asks to evaluate, benchmark, compare, regression-test, or qualify an agent. It supports local reproducible scoring and evidence collection for selected external benchmarks. It is not a model-knowledge exam and does not infer ability from a conversation alone.

## Required workflow

1. Confirm the target agent invocation and the capability to evaluate. If unspecified, run the full readiness suite first.
2. Run `python3 /path/to/xfg-agent-review-skills/scripts/agent_review.py validate`.
3. Run readiness with an absolute agent command:
   `python3 /path/to/xfg-agent-review-skills/scripts/agent_review.py run --agent-command '<absolute-agent-command>' --output agent-review-report.json --markdown`
4. If the user asks to compare model providers or models, pass `--model-config` and `--profile`. If they do not ask, keep the agent wrapper's default configuration.
5. If the request involves real UI, screenshots, conversation quality, or runtime behavior, run with `--screenshot-command` and a JSON `--review-command` when available. If screenshot capture is unavailable or fails, continue with workspace files, transcript, logs, and deterministic validators; do not abort the evaluation solely because a screenshot is missing.
6. Review task-level checks, artifacts, timing, and failures. Never replace a failed task with a narrative explanation.
7. For deeper qualification, run the external benchmark selected from `registry/benchmarks.json` in its official repository and retain the official result file. Record `passed` only with immutable official evidence.
8. For a comparison or release decision, combine the readiness score with official benchmark scores and report token cost, wall time, tool-call count, recovery rate, and safety violations when available.

## Agent protocol

The target agent command must read this JSON object from stdin and execute inside the provided workspace:

```json
{"task_id": "...", "prompt": "...", "workspace": "..."}
```

It must exit zero only when it believes the task is complete. Non-empty stdout must be a JSON object; stderr is reserved for diagnostics. The command is invoked with the task workspace as its working directory. Wrappers that require repository-relative files must use absolute paths.

Read `references/evaluation-standards.md` before assigning capability levels. Read `references/benchmark-catalog.md` when selecting an external benchmark. Read `references/official-benchmark-runbook.md` for source-level execution guidance.

## Reporting rules

- Report the exact readiness success rate, not a qualitative upgrade.
- Use the generated `scoring` object: report every capability score, the 0–100 overall score, the readiness level, and every optimization action.
- Quote failed task IDs before recommending changes. Do not turn a failed validator into a vague qualitative comment.
- Include failed task IDs and validator messages.
- Do not claim external benchmark results unless the official benchmark was run and its output is retained.
- Treat a changed prompt, model, tools, configuration, workspace, or dataset version as a new evaluation.
- Preserve generated artifacts under `<output-stem>-artifacts` for auditability.
