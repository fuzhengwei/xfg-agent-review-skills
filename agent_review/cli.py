"""Command-line interface for xfg-agent-review-skills."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .benchmarks import discover_benchmarks, doctor
from .evaluator import EvaluatorError, evaluate_task
from .reports import load_report, render_readiness_html, render_readiness_markdown
from .runner import load_json, run_readiness, summarize_official_benchmarks


def _validate_suite(path: Path) -> None:
    suite = load_json(path)
    tasks = suite.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("suite must contain tasks")
    for task in tasks:
        # evaluate_task performs schema validation without creating files here.
        evaluate_task(task, Path(__file__).resolve().parent)
    print(f"OK suite: {path} ({len(tasks)} tasks)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-review",
        description="Evaluate coding, tool, terminal, web, desktop, and long-horizon agent capabilities.",
    )
    parser.add_argument("--version", action="version", version="xfg-agent-review-skills 1.0.0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a readiness evaluation")
    run_parser.add_argument("--agent-command", required=True, help="Shell command implementing the JSON agent protocol")
    run_parser.add_argument("--suite", default="suites/readiness.json", help="Readiness suite JSON")
    run_parser.add_argument("--output", default="agent-review-report.json", help="JSON output path")
    run_parser.add_argument("--markdown", action="store_true", help="Also write a sibling Markdown report")
    run_parser.add_argument("--html", action="store_true", help="Also write a sibling HTML report")
    run_parser.add_argument("--timeout", type=int, help="Override per-task timeout in seconds")
    run_parser.add_argument("--model-config", help="Optional JSON file with model/channel profiles")
    run_parser.add_argument("--profile", help="Profile id inside --model-config")

    doctor_parser = subparsers.add_parser("doctor", help="Check official benchmark prerequisites")
    doctor_parser.add_argument("--output", default="benchmark-doctor.json", help="JSON output path")

    external_parser = subparsers.add_parser("external", help="Create or merge official benchmark evidence")
    external_parser.add_argument("--status", action="append", default=[], help="id=passed|failed|not_run")
    external_parser.add_argument("--output", default="official-benchmark-report.json", help="JSON output path")

    report_parser = subparsers.add_parser("report", help="Render an existing JSON report")
    report_parser.add_argument("input", help="Readiness JSON report")
    report_parser.add_argument("--output", required=True, help="Markdown output path")

    list_parser = subparsers.add_parser("list", help="List registered official benchmarks")

    validate_parser = subparsers.add_parser("validate", help="Validate registry and suite schema")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    try:
        if args.command == "run":
            suite_path = Path(args.suite)
            if not suite_path.is_absolute():
                suite_path = root / suite_path
            output = Path(args.output)
            report = run_readiness(
                agent_command=args.agent_command,
                suite_path=suite_path,
                output_path=output,
                timeout_seconds=args.timeout,
                model_config_path=Path(args.model_config) if args.model_config else None,
                model_profile_id=args.profile,
            )
            if args.markdown:
                markdown_path = output.with_suffix(".md")
                markdown_path.write_text(render_readiness_markdown(report), encoding="utf-8")
            if args.html:
                html_path = output.with_suffix(".html")
                html_path.write_text(render_readiness_html(report), encoding="utf-8")
            summary = report["summary"]
            print(
                f"readiness: {summary['passed']}/{summary['tasks']} passed "
                f"({summary['success_rate']:.1%}); report={output}"
            )
            return 0
        if args.command == "doctor":
            doctor(Path(args.output))
            print(f"doctor report={args.output}")
            return 0
        if args.command == "external":
            statuses = {}
            for item in args.status:
                if "=" not in item:
                    raise ValueError("--status must use benchmark_id=passed|failed|not_run")
                benchmark_id, status = item.split("=", 1)
                if status not in {"passed", "failed", "not_run"}:
                    raise ValueError("status must be passed, failed, or not_run")
                if benchmark_id not in {benchmark["id"] for benchmark in discover_benchmarks()}:
                    raise ValueError(f"unknown benchmark: {benchmark_id}")
                statuses[benchmark_id] = status
            summarize_official_benchmarks(statuses, Path(args.output))
            print(f"official evidence report={args.output}")
            return 0
        if args.command == "report":
            report = load_report(Path(args.input))
            if report.get("report_type") != "agent-review-readiness":
                raise ValueError("report input is not a readiness report")
            output = Path(args.output)
            if output.suffix.lower() == ".html":
                output.write_text(render_readiness_html(report), encoding="utf-8")
                print(f"html={output}")
                return 0
            output.write_text(render_readiness_markdown(report), encoding="utf-8")
            print(f"markdown={args.output}")
            return 0
        if args.command == "list":
            for benchmark in discover_benchmarks():
                print(f"{benchmark['id']:<24} {benchmark['capability']:<28} {benchmark['title']}")
            return 0
        if args.command == "validate":
            with (root / "registry" / "benchmarks.json").open(encoding="utf-8") as handle:
                registry = json.load(handle)
            benchmark_ids = {item["id"] for item in registry["benchmarks"]}
            print(f"OK registry: {len(benchmark_ids)} benchmarks")
            _validate_suite(root / "suites" / "readiness.json")
            return 0
    except (ValueError, EvaluatorError, json.JSONDecodeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
