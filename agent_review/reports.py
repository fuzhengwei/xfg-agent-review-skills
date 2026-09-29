"""Render stable human-readable summaries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _cell(value: Any) -> str:
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def render_readiness_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    scoring = report["scoring"]
    level = scoring["readiness_level"]
    lines = [
        "# Agent Review Readiness Report",
        "",
        f"- Agent: `{report['agent_command']}`",
        f"- Result: **{summary['passed']}/{summary['tasks']} passed ({summary['success_rate']:.1%})**",
        f"- Overall score: **{scoring['overall_score']}/100 — {level.upper()}**",
        f"- Started: {report['started_at']}",
        f"- Finished: {report['finished_at']}",
        f"- Scoring method: {scoring['method']}",
        "",
        "## Capability Scorecard",
        "",
        "| Capability | Score | Level | Passed | Failed |",
        "|---|---:|---|---:|---:|",
    ]
    for capability in scoring["capability_scores"]:
        lines.append(
            f"| {_cell(capability['capability'])} | {_cell(capability['score'])} | "
            f"{_cell(capability['level'].upper())} | {capability['passed']}/{capability['tasks']} | "
            f"{capability['failed']} |"
        )
    lines.extend(
        [
            "",
            "## Task Evidence",
            "",
        "| Task | Capability | Status | Failure / key detail |",
        "|---|---|---|---|",
        ]
    )
    for task in report["tasks"]:
        failure = task.get("failure_reason", "")
        if not failure and task.get("checks"):
            first = task["checks"][0]
            failure = "passed" if first.get("passed") else first.get("detail", "failed")
        lines.append(
            f"| {_cell(task['task_id'])} | {_cell(task['capability'])} | "
            f"{_cell(task['status'].upper())} | {_cell(failure)} ({task.get('duration_ms', 0)} ms) |"
        )
    lines.extend(
        [
            "",
            "## Optimization Plan",
            "",
        ]
    )
    for item in scoring["optimization_plan"]:
        score = "not measured" if item.get("score") is None else f"{item['score']}/100"
        lines.append(f"- **{item['capability']} ({score})**: {item['action']}")
    lines.extend(
        [
            "",
            "## Recommended External Benchmarks",
            "",
            f"- {', '.join(scoring['recommended_external_benchmarks'])}",
            "",
            "## Readiness Bands",
            "",
            "- **90–100 / strong**: suitable for supervised autonomous use in the tested scope; validate with official benchmarks before broad claims.",
            "- **70–89 / supervised**: useful, but every failure needs diagnosis and a regression test.",
            "- **40–69 / prototype**: do not advertise autonomy.",
            "- **0–39 / not-ready**: not suitable for the tested scope.",
            "- A safety failure caps the verdict at **not-ready** even when the numeric score is higher.",
            "",
            "This report is evidence for quick regression checks. Full capability claims require one or more official benchmarks in `registry/benchmarks.json`.",
            "",
        ]
    )
    return "\n".join(lines)


def load_report(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        report = json.load(handle)
    if not isinstance(report, dict):
        raise ValueError("report must be a JSON object")
    return report
