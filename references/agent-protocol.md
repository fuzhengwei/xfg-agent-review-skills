# Agent Protocol

The invocation contract is intentionally simple and transport-neutral.

```json
{
  "task_id": "tool-selection",
  "prompt": "Complete the requested task.",
  "workspace": "/absolute/path/to/task/workspace"
}
```

Rules:

- stdin is the only prompt channel; do not parse shell arguments for task content.
- the process starts with `workspace` as its working directory.
- exit code zero means the agent considers its work complete; validators still decide success.
- non-empty stdout must be one JSON object. Recommended fields are `status`, `summary`, `tool_calls`, and `error`.
- stderr may contain logs but must not be treated as task output.
- the agent may create files, run local tests, and install project dependencies only when the task authorizes that action.
- a wrapper may call an LLM, CLI, SDK, or another process, but it must return one final protocol response.

Example wrapper command:

```bash
python3 /absolute/path/to/agent-wrapper.py --model gpt-5 --workspace-dir /tmp/xfg-review
```

The wrapper reads the JSON request from stdin, invokes the agent, and writes one JSON result to stdout.
