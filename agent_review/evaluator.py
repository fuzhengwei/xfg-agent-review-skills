"""Deterministic scoring for the local readiness suite."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any


class EvaluatorError(ValueError):
    pass


def _file_checks(workspace: Path, checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for check in checks:
        path = workspace / check["path"]
        if not path.is_file():
            results.append({"name": f"file:{check['path']}", "passed": False, "detail": "missing"})
            continue
        content = path.read_text(encoding="utf-8")
        if "contains" in check and check["contains"] not in content:
            results.append({"name": f"file:{check['path']}:contains", "passed": False, "detail": "text absent"})
        elif "regex" in check and not re.search(check["regex"], content, re.MULTILINE):
            results.append({"name": f"file:{check['path']}:regex", "passed": False, "detail": "pattern absent"})
        else:
            results.append({"name": f"file:{check['path']}", "passed": True, "detail": "matched"})
    return results


def _validate_manifest(manifest: dict[str, Any]) -> None:
    task_id = manifest.get("id")
    if not isinstance(task_id, str) or not task_id:
        raise EvaluatorError("task.id is required")
    if not isinstance(manifest.get("prompt"), str) or not manifest["prompt"].strip():
        raise EvaluatorError(f"task {task_id}.prompt is required")
    validator = manifest.get("validator")
    if not isinstance(validator, dict):
        raise EvaluatorError(f"task {task_id}.validator is required")
    validator_type = validator.get("type")
    if validator_type not in {"files", "command", "both"}:
        raise EvaluatorError(f"task {task_id}.validator.type must be files, command, or both")
    if validator_type in {"files", "both"} and not isinstance(validator.get("files"), list):
        raise EvaluatorError(f"task {task_id}.validator.files is required")
    if validator_type in {"command", "both"}:
        command = validator.get("command")
        if not isinstance(command, list) or not command:
            raise EvaluatorError(f"task {task_id}.validator.command must be a non-empty list")


def evaluate_task(
    manifest: dict[str, Any],
    workspace: Path,
    command_timeout_seconds: int = 120,
) -> tuple[bool, list[dict[str, Any]]]:
    _validate_manifest(manifest)
    checks: list[dict[str, Any]] = []
    validator = manifest["validator"]
    validator_type = validator["type"]

    if validator_type in {"files", "both"}:
        checks.extend(_file_checks(workspace, validator["files"]))

    if validator_type in {"command", "both"}:
        try:
            completed = subprocess.run(
                validator["command"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=command_timeout_seconds,
                check=False,
            )
            passed = completed.returncode == 0
            detail = completed.stderr.strip() or completed.stdout.strip()
            detail = (detail + "\n" if detail else "") + f"exit code {completed.returncode}"
            detail = detail.strip()[:2000]
        except FileNotFoundError as exc:
            passed = False
            detail = str(exc)
        except subprocess.TimeoutExpired:
            passed = False
            detail = f"validator timed out after {command_timeout_seconds}s"
        checks.append({"name": "validator:command", "passed": passed, "detail": detail})

    return bool(checks) and all(check["passed"] for check in checks), checks
