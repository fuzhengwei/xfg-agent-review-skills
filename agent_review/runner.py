"""Run readiness or recorded official-benchmark evaluations."""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .agent import AgentProtocolError, invoke_agent
from .evaluator import evaluate_task
from .model_config import resolve_model_profile
from .scoring import BENCHMARKS_BY_CAPABILITY, RECOMMENDATIONS, score_report


ROOT = Path(__file__).resolve().parent.parent


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def write_setup_files(workspace: Path, files: dict[str, str]) -> None:
    for relative_path, content in files.items():
        destination = workspace / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


def _workspace_file_manifest(workspace: Path) -> list[str]:
    return sorted(
        str(path.relative_to(workspace))
        for path in workspace.rglob("*")
        if path.is_file() and not path.is_symlink()
    )


def run_readiness(
    agent_command: str,
    suite_path: Path = ROOT / "suites" / "readiness.json",
    output_path: Path | None = None,
    timeout_seconds: int | None = None,
    model_config_path: Path | None = None,
    model_profile_id: str | None = None,
    screenshot_command: str | None = None,
    review_command: str | None = None,
) -> dict[str, Any]:
    model_profile = resolve_model_profile(model_config_path, model_profile_id)
    suite = load_json(suite_path)
    if suite.get("suite") != "readiness":
        raise ValueError("suite file must use suite=readiness")
    tasks = suite.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("suite must contain at least one task")

    effective_timeout = int(timeout_seconds or suite.get("timeout_seconds", 600))
    output_path = output_path or Path.cwd() / "agent-review-report.json"
    artifacts = output_path.parent / f"{output_path.stem}-artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    screenshot_argv = shlex.split(screenshot_command) if screenshot_command else None
    review_argv = shlex.split(review_command) if review_command else None

    records: list[dict[str, Any]] = []
    started_at = utc_now()
    for task in tasks:
        task_id = str(task.get("id", "unnamed"))
        task_workspace = artifacts / "workspaces" / task_id
        if task_workspace.exists():
            shutil.rmtree(task_workspace)
        task_workspace.mkdir(parents=True)
        write_setup_files(task_workspace, task.get("setup_files", {}))

        record: dict[str, Any] = {
            "task_id": task_id,
            "capability": task.get("capability", "general"),
            "status": "failed",
            "started_at": utc_now(),
        }
        task_started = time.perf_counter()
        try:
            agent_result = invoke_agent(
                command=agent_command,
                prompt=task["prompt"],
                workspace=task_workspace,
                timeout_seconds=effective_timeout,
                model_profile=model_profile,
            )
            record["agent_exit_code"] = agent_result.exit_code
            record["agent_protocol"] = asdict(agent_result)
            if agent_result.exit_code != 0:
                record["failure_reason"] = "agent command returned a non-zero exit code"
                record["checks"] = []
            else:
                passed, checks = evaluate_task(task, task_workspace)
                record["status"] = "passed" if passed else "failed"
                record["checks"] = checks
                if not passed:
                    record["failure_reason"] = "validator failed"
        except AgentProtocolError as exc:
            record["agent_exit_code"] = None
            record["failure_reason"] = str(exc)
            record["checks"] = []
        record["finished_at"] = utc_now()
        record["duration_ms"] = round((time.perf_counter() - task_started) * 1000, 1)
        record["workspace_files"] = _workspace_file_manifest(task_workspace)
        record["evidence_mode"] = "workspace-only"
        record["screenshots"] = []

        if screenshot_argv:
            evidence_dir = task_workspace / "evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = evidence_dir / "screenshot.png"
            capture_command = [
                part.replace("{output}", str(screenshot_path))
                .replace("{workspace}", str(task_workspace))
                .replace("{task_id}", task_id)
                for part in screenshot_argv
            ]
            screenshot_started = time.perf_counter()
            try:
                capture_result = subprocess.run(
                    capture_command,
                    cwd=task_workspace,
                    capture_output=True,
                    text=True,
                    timeout=min(30, effective_timeout),
                    check=False,
                )
                if capture_result.returncode == 0 and screenshot_path.is_file():
                    record["screenshots"] = [str(screenshot_path)]
                    record["evidence_mode"] = "screenshot+workspace"
                    record["screenshot_capture"] = {
                        "exit_code": 0,
                        "duration_ms": round((time.perf_counter() - screenshot_started) * 1000, 1),
                    }
                else:
                    record["screenshots"] = []
                    record["screenshot_capture"] = {
                        "exit_code": capture_result.returncode,
                        "duration_ms": round((time.perf_counter() - screenshot_started) * 1000, 1),
                        "error": (capture_result.stderr or capture_result.stdout or "screenshot file was not created")[:2000],
                    }
            except (OSError, subprocess.TimeoutExpired) as exc:
                record["screenshots"] = []
                record["screenshot_capture"] = {"exit_code": None, "error": str(exc)}

        if review_argv:
            review_started = time.perf_counter()
            review_request = {
                "task_id": task_id,
                "capability": record["capability"],
                "prompt": task["prompt"],
                "workspace": str(task_workspace),
                "screenshots": record["screenshots"],
                "workspace_files": record["workspace_files"],
                "agent_stdout": record.get("agent_protocol", {}).get("stdout", ""),
                "agent_stderr": record.get("agent_protocol", {}).get("stderr", ""),
                "checks": record.get("checks", []),
            }
            try:
                review_result = subprocess.run(
                    review_argv,
                    input=json.dumps(review_request, ensure_ascii=False),
                    text=True,
                    cwd=task_workspace,
                    capture_output=True,
                    timeout=min(120, effective_timeout),
                    check=False,
                )
                review_payload = None
                if review_result.stdout.strip():
                    try:
                        decoded = json.loads(review_result.stdout)
                        if not isinstance(decoded, dict):
                            raise ValueError("review command stdout must be a JSON object")
                        review_payload = decoded
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"invalid review JSON: {exc}") from exc
                record["visual_review"] = {
                    "exit_code": review_result.returncode,
                    "duration_ms": round((time.perf_counter() - review_started) * 1000, 1),
                    "payload": review_payload,
                    "stdout": review_result.stdout,
                    "stderr": review_result.stderr,
                }
            except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
                record["visual_review"] = {
                    "exit_code": None,
                    "duration_ms": round((time.perf_counter() - review_started) * 1000, 1),
                    "error": str(exc),
                }

        records.append(record)

    passed_count = sum(record["status"] == "passed" for record in records)
    scoring = score_report({"tasks": records})
    recommendations: list[dict[str, str]] = []
    for capability in scoring["capability_scores"]:
        if capability["failed"] == 0 and capability["score"] >= 90:
            continue
        detail = RECOMMENDATIONS.get(capability["capability"], RECOMMENDATIONS["general"])
        if capability["failed_task_ids"]:
            detail += f" Reproduce and fix: {', '.join(map(str, capability['failed_task_ids']))}."
        recommendations.append(
            {
                "capability": capability["capability"],
                "score": capability["score"],
                "action": detail,
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "capability": "benchmark-coverage",
                "score": scoring["overall_score"],
                "action": "Run SWE-bench Verified and Terminal-Bench for code-agent claims; add BFCL v3 for tool-calling claims.",
            }
        )
    recommendations.append(
        {
            "capability": "efficiency",
            "score": None,
            "action": "Add token, tool-call, step-count, recovery, and cost telemetry before release comparisons.",
        }
    )
    benchmark_ids = sorted(
        {
            benchmark
            for item in scoring["capability_scores"]
            for benchmark in BENCHMARKS_BY_CAPABILITY.get(item["capability"], [])
        }
    )
    scoring["optimization_plan"] = recommendations
    scoring["recommended_external_benchmarks"] = benchmark_ids or ["SWE-bench Verified", "Terminal-Bench"]
    report = {
        "schema_version": 1,
        "report_type": "agent-review-readiness",
        "started_at": started_at,
        "finished_at": utc_now(),
        "agent_command": agent_command,
        "model_profile": model_profile,
        "evidence_mode": "screenshot+workspace" if any(task.get("screenshots") for task in records) else "workspace-only",
        "screenshot_command": screenshot_command,
        "review_command": review_command,
        "suite": str(suite_path),
        "timeout_seconds_per_task": effective_timeout,
        "summary": {
            "tasks": len(records),
            "passed": passed_count,
            "failed": len(records) - passed_count,
            "success_rate": round(passed_count / len(records), 4),
        },
        "scoring": scoring,
        "tasks": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def summarize_official_benchmarks(
    status_by_benchmark: dict[str, str] | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    from .benchmarks import discover_benchmarks

    records = []
    status_by_benchmark = status_by_benchmark or {}
    for benchmark in discover_benchmarks():
        records.append(
            {
                "id": benchmark["id"],
                "title": benchmark["title"],
                "capability": benchmark["capability"],
                "source": benchmark["source"],
                "metric": benchmark["metric"],
                "status": status_by_benchmark.get(benchmark["id"], "not_run"),
            }
        )
    report = {
        "schema_version": 1,
        "report_type": "agent-review-official-benchmarks",
        "generated_at": utc_now(),
        "summary": {
            "benchmarks": len(records),
            "run": sum(item["status"] == "passed" for item in records),
            "not_run": sum(item["status"] != "passed" for item in records),
        },
        "benchmarks": records,
    }
    output_path = output_path or Path.cwd() / "official-benchmark-report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
