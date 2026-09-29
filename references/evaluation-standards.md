# Evaluation Standards

## Capability dimensions

| Dimension | Question | Primary evidence |
|---|---|---|
| Instruction following | Did it deliver exactly what was requested? | artifact/schema validator |
| Planning | Did it use an ordered, verifiable plan? | plan artifact or action trace |
| Tool selection | Did it choose the correct tool and arguments? | protocol/tool trace |
| Multi-step state | Did it preserve state across dependent calls? | intermediate artifacts |
| Terminal | Can it inspect, repair, and verify? | shell command and exit codes |
| Code engineering | Can it fix behavior and pass tests? | test result plus diff |
| Browser/desktop | Can it operate an external UI and verify state? | DOM, screenshot, database, or file state |
| Error recovery | Can it diagnose and recover without abandoning the task? | before/after trace |
| Safety | Did it avoid destructive, leaking, or out-of-scope actions? | guard validator and trace |
| Efficiency | What did success cost? | steps, tool calls, tokens, wall time |

Extended checks for production or security review:

| Extended dimension | Question | Primary evidence |
|---|---|---|
| Long-term memory | Does state survive across sessions without leaking stale data? | memory key, retrieval trace, task state |
| Security | Does it resist prompt injection and tool misuse? | attack success rate, denied actions, audit log |
| Multi-agent collaboration | Are handoffs, permissions, and ownership correct? | role trace, approval record, final artifact |
| Robustness | Does success hold under prompt, tool, or environment perturbation? | repeated runs with changed input and tool failures |

## Required metrics

For every report:

- `passed`: number of tasks meeting all validators.
- `success_rate`: `passed / tasks`.
- `steps_to_success`: steps, turns, or agent messages.
- `tool_calls`: total calls and invalid calls.
- `recovery_rate`: recovered / encountered recoverable failures.
- `token_cost`: prompt plus completion tokens when available.
- `wall_time`: total and median per successful task.
- `safety_violations`: destructive/out-of-scope actions, always non-zero-blocking.
- `partial_score`: optional but deterministic rubric score.

## Scoring rubric

| Readiness success rate | Interpretation |
|---|---|
| 90–100% | Strong for autonomous use in the tested scope; still require one official benchmark for a broad capability claim. |
| 70–89% | Useful but needs supervision; inspect every failed task. |
| 40–69% | Prototype; do not advertise autonomy. |
| 0–39% | Not ready for the tested scope. |

No readiness grade can override safety. A safety failure caps the overall result at `not ready`.

## Evidence rules

1. Pin model identifier/version, temperature/sampling settings, tool versions, system prompt hash, dataset revision, and runner commit.
2. Run each task in a clean workspace; do not reuse state unless isolation is the tested behavior.
3. Record every validator check, not only aggregate success.
4. Preserve official outputs for external benchmarks.
5. Run at least two seeds for stochastic agents and report mean, standard deviation, and `pass@1`.
6. Use the same timeout and hardware profile when comparing agents.
7. Store raw logs before deriving scores. A score without evidence is not auditable.

## Contamination and fairness

- Do not allow the agent under test to retrieve benchmark answers or public patches during execution.
- Disable memory/context that can leak prior runs unless the benchmark explicitly permits it.
- Do not inspect hidden tests in SWE-bench tasks.
- Keep prompt templates constant within a comparison.
- Report skipped tasks; do not silently remove difficult failures.
- Separate benchmark performance from business/tool availability. A missing API is an integration failure, not model intelligence.
