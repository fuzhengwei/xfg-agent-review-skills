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

When `--model-config` is supplied, the wrapper also receives:

```text
AGENT_REVIEW_PROFILE_ID
AGENT_REVIEW_PROVIDER
AGENT_REVIEW_MODEL
AGENT_REVIEW_BASE_URL
AGENT_REVIEW_REQUEST
```

The runner does not call the provider itself. The wrapper decides whether to use OpenAI, Anthropic, Kimi, GLM, DeepSeek, another OpenAI-compatible endpoint, or a local model. If no model config is supplied, keep the wrapper's existing default.

The optional reviewer command receives a JSON object from stdin. In addition to screenshots, it includes `workspace`, `workspace_files`, `agent_stdout`, `agent_stderr`, and `checks`, so it can continue reviewing artifacts and conversation quality when screenshots are unavailable.
