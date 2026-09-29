"""Agent process contract used by every benchmark adapter."""

from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class AgentProtocolError(RuntimeError):
    pass


@dataclass
class AgentResult:
    exit_code: int
    stdout: str
    stderr: str
    payload: dict[str, Any] | None = None


def invoke_agent(
    command: str,
    prompt: str,
    workspace: Path,
    timeout_seconds: int,
) -> AgentResult:
    """Invoke an agent using the xAgent JSON stdin/stdout protocol."""

    request = {
        "task_id": workspace.name,
        "prompt": prompt,
        "workspace": str(workspace.resolve()),
    }
    try:
        completed = subprocess.run(
            shlex.split(command),
            input=json.dumps(request, ensure_ascii=False),
            text=True,
            cwd=workspace,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise AgentProtocolError(f"agent command not found: {command}") from exc
    except subprocess.TimeoutExpired as exc:
        raise AgentProtocolError(
            f"agent timed out after {timeout_seconds}s; partial stdout/stderr preserved"
        ) from exc

    payload = None
    if completed.stdout.strip():
        try:
            decoded = json.loads(completed.stdout)
            if not isinstance(decoded, dict):
                raise AgentProtocolError("agent JSON stdout must be an object")
            payload = decoded
        except json.JSONDecodeError as exc:
            raise AgentProtocolError(
                "agent must emit valid JSON on stdout when stdout is non-empty"
            ) from exc
    return AgentResult(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        payload=payload,
    )
