"""Render stable human-readable summaries."""

from __future__ import annotations

import json
import html
import base64
import mimetypes
from pathlib import Path
from typing import Any


def _cell(value: Any) -> str:
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def render_readiness_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    scoring = report["scoring"]
    level = scoring["readiness_level"]
    model_profile = report.get("model_profile")
    model_label = "agent default" if not model_profile else f"{model_profile.get('provider')}/{model_profile.get('model')}"
    lines = [
        "# Agent Review Readiness Report",
        "",
        f"- Agent: `{report['agent_command']}`",
        f"- Model/channel: `{model_label}`",
        f"- Evidence mode: `{report.get('evidence_mode', 'workspace-only')}`",
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
        if task.get("screenshots"):
            lines.append(f"  - Screenshot: `{task['screenshots'][0]}`")
        if task.get("visual_review"):
            lines.append("  - Visual/conversation review attached in JSON report")
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


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _task_detail(task: dict[str, Any]) -> str:
    protocol = task.get("agent_protocol") or {}
    checks = task.get("checks") or []
    screenshot_parts: list[str] = []
    for screenshot in task.get("screenshots", []):
        screenshot_path = Path(screenshot)
        if screenshot_path.is_file():
            media_type = mimetypes.guess_type(screenshot_path)[0] or "image/png"
            encoded = base64.b64encode(screenshot_path.read_bytes()).decode("ascii")
            screenshot_parts.append(
                f"<img class='screenshot' src='data:{media_type};base64,{encoded}' alt='Task screenshot'>"
            )
    visual_review = task.get("visual_review") or {}
    rows = [
        "<div class='task-detail'>",
        f"<div><strong>Exit code:</strong> {_esc(task.get('agent_exit_code'))}</div>",
        f"<div><strong>Duration:</strong> {_esc(task.get('duration_ms', 0))} ms</div>",
        "<details><summary>Checks</summary><pre>" + _esc(json.dumps(checks, indent=2, ensure_ascii=False)) + "</pre></details>",
    ]
    if screenshot_parts:
        rows.append("<div class='screenshots'>" + "".join(screenshot_parts) + "</div>")
    if visual_review:
        rows.append(
            "<details open><summary>Visual / conversation review</summary><pre>"
            + _esc(json.dumps(visual_review, indent=2, ensure_ascii=False))
            + "</pre></details>"
        )
    if protocol.get("stdout"):
        rows.append(
            "<details><summary>Agent stdout</summary><pre>"
            + _esc(protocol["stdout"])
            + "</pre></details>"
        )
    if protocol.get("stderr"):
        rows.append(
            "<details><summary>Agent stderr</summary><pre>"
            + _esc(protocol["stderr"])
            + "</pre></details>"
        )
    rows.append("</div>")
    return "".join(rows)


def render_readiness_html(report: dict[str, Any]) -> str:
    """Render a self-contained HTML readiness report."""

    summary = report["summary"]
    scoring = report["scoring"]
    model_profile = report.get("model_profile") or {}
    model_label = (
        f"{model_profile.get('provider')}/{model_profile.get('model')}"
        if model_profile
        else "agent default"
    )

    capability_rows = "".join(
        f"""
        <tr>
          <td>{_esc(item['capability'])}</td>
          <td class='score'>{_esc(item['score'])}</td>
          <td><span class='badge level-{_esc(item['level'])}'>{_esc(item['level'].upper())}</span></td>
          <td>{item['passed']}/{item['tasks']}</td>
          <td>{item['failed']}</td>
        </tr>
        """
        for item in scoring["capability_scores"]
    )

    task_rows = "".join(
        f"""
        <tr>
          <td>{_esc(task['task_id'])}</td>
          <td>{_esc(task['capability'])}</td>
          <td><span class='badge status-{_esc(task['status'])}'>{_esc(task['status'].upper())}</span></td>
          <td>{_esc(task.get('failure_reason') or 'passed')}</td>
          <td>{_esc(task.get('duration_ms', 0))}</td>
        </tr>
        """
        for task in report["tasks"]
    )

    task_details = "".join(
        f"""
        <details>
          <summary>{_esc(task['task_id'])}</summary>
          {_task_detail(task)}
        </details>
        """
        for task in report["tasks"]
    )

    optimization_items = "".join(
        f"""
        <li>
          <strong>{_esc(item['capability'])}</strong>
          <span class='muted'>({_esc(item.get('score') if item.get('score') is not None else 'not measured')})</span>
          <div>{_esc(item['action'])}</div>
        </li>
        """
        for item in scoring["optimization_plan"]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent Review Readiness Report</title>
  <style>
    :root {{ color-scheme: light dark; --border:#d8dee9; --muted:#667085; --bg:#f7f8fa; --card:#ffffff; --accent:#2563eb; }}
    @media (prefers-color-scheme: dark) {{ :root {{ --border:#30363d; --muted:#9ca3af; --bg:#0d1117; --card:#161b22; --accent:#58a6ff; }} }}
    body {{ margin:0; padding:24px; background:var(--bg); color:inherit; font:14px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    main {{ max-width:1080px; margin:0 auto; }}
    header {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:20px; }}
    h1 {{ margin:0 0 8px; font-size:22px; }}
    h2 {{ font-size:18px; margin:28px 0 12px; }}
    .meta {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:10px; margin-top:14px; }}
    .meta div {{ background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:10px; }}
    .small {{ color:var(--muted); font-size:12px; }}
    .card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:18px; }}
    table {{ width:100%; border-collapse:collapse; }}
    th, td {{ text-align:left; border-bottom:1px solid var(--border); padding:10px 8px; vertical-align:top; }}
    th {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.04em; }}
    td.score {{ font-weight:700; }}
    .badge {{ display:inline-block; padding:2px 7px; border-radius:999px; font-size:11px; font-weight:700; }}
    .status-passed {{ background:#dcfce7; color:#166534; }}
    .status-failed {{ background:#fee2e2; color:#991b1b; }}
    .level-strong {{ background:#dbeafe; color:#1e40af; }}
    .level-supervised {{ background:#ffedd5; color:#9a3412; }}
    .level-prototype, .level-not-ready {{ background:#fee2e2; color:#991b1b; }}
    details {{ border:1px solid var(--border); border-radius:8px; padding:10px; margin-top:8px; }}
    pre {{ white-space:pre-wrap; overflow-wrap:anywhere; max-height:280px; overflow:auto; background:var(--bg); padding:10px; border-radius:6px; }}
    ul {{ padding-left:20px; }}
    li {{ margin-bottom:10px; }}
    .muted {{ color:var(--muted); }}
    .screenshots {{ display:flex; gap:10px; margin:10px 0; overflow:auto; }}
    .screenshot {{ max-width:420px; max-height:240px; border:1px solid var(--border); border-radius:6px; }}
    footer {{ margin-top:28px; color:var(--muted); font-size:12px; }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Agent Review Readiness Report</h1>
      <p><strong>{_esc(summary['passed'])}/{_esc(summary['tasks'])} passed · {_esc(f"{summary['success_rate']:.1%}")}</strong></p>
      <p>Overall score: <strong>{_esc(scoring['overall_score'])}/100 · {_esc(scoring['readiness_level'].upper())}</strong></p>
      <div class="meta">
        <div><div class="small">Agent</div><div>{_esc(report['agent_command'])}</div></div>
        <div><div class="small">Model / channel</div><div>{_esc(model_label)}</div></div>
        <div><div class="small">Evidence mode</div><div>{_esc(report.get('evidence_mode', 'workspace-only'))}</div></div>
        <div><div class="small">Started</div><div>{_esc(report['started_at'])}</div></div>
        <div><div class="small">Finished</div><div>{_esc(report['finished_at'])}</div></div>
      </div>
      <p class="small">{_esc(scoring['method'])}</p>
    </header>

    <section>
      <h2>Capability Scorecard</h2>
      <div class="card">
        <table>
          <thead><tr><th>Capability</th><th>Score</th><th>Level</th><th>Passed</th><th>Failed</th></tr></thead>
          <tbody>{capability_rows}</tbody>
        </table>
      </div>
    </section>

    <section>
      <h2>Task Evidence</h2>
      <div class="card">
        <table>
          <thead><tr><th>Task</th><th>Capability</th><th>Status</th><th>Failure / detail</th><th>Duration (ms)</th></tr></thead>
          <tbody>{task_rows}</tbody>
        </table>
        {task_details}
      </div>
    </section>

    <section>
      <h2>Optimization Plan</h2>
      <div class="card"><ul>{optimization_items}</ul></div>
    </section>

    <section>
      <h2>Recommended External Benchmarks</h2>
      <div class="card"><p>{_esc(', '.join(scoring['recommended_external_benchmarks']))}</p></div>
    </section>

    <section>
      <h2>Readiness Bands</h2>
      <div class="card">
        <ul>
          <li><strong>90–100 / strong</strong> — suitable for supervised autonomous use in the tested scope; validate with official benchmarks before broad claims.</li>
          <li><strong>70–89 / supervised</strong> — useful, but every failure needs diagnosis and a regression test.</li>
          <li><strong>40–69 / prototype</strong> — do not advertise autonomy.</li>
          <li><strong>0–39 / not-ready</strong> — not suitable for the tested scope.</li>
          <li>A safety failure caps the verdict at <strong>not-ready</strong> even when the numeric score is higher.</li>
        </ul>
      </div>
    </section>

    <footer>
      This is a readiness regression report, not proof of production readiness. Full capability claims require one or more official benchmarks.
    </footer>
  </main>
</body>
</html>
"""
