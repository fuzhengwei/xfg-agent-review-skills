"""Official benchmark metadata and lightweight environment checks."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .runner import utc_now

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "registry" / "benchmarks.json"


def discover_benchmarks() -> list[dict[str, Any]]:
    with REGISTRY_PATH.open(encoding="utf-8") as handle:
        registry = json.load(handle)
    benchmarks = registry.get("benchmarks")
    if not isinstance(benchmarks, list) or not benchmarks:
        raise ValueError("benchmark registry is empty or malformed")
    return benchmarks


def command_available(command: str) -> bool:
    return shutil.which(command) is not None


def module_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def check_prerequisite(prerequisite: str) -> tuple[bool, str]:
    if prerequisite.startswith("python>="):
        try:
            completed = subprocess.run(
                ["python3", "--version"], capture_output=True, text=True, check=True
            )
            version = completed.stdout.strip().split()[-1]
            required_minor = int(prerequisite.split("python>=")[1].split(".")[1])
            current_minor = int(version.split(".")[1])
            return current_minor >= required_minor, version
        except Exception as exc:
            return False, str(exc)
    if prerequisite == "network-access":
        return True, "assumed available when cloud agents are used"
    if prerequisite == "display-server":
        return True, "must be provided by the OSWorld environment"
    if prerequisite == "compose":
        return command_available("docker-compose"), "docker-compose"
    if prerequisite == "browser":
        return any(command_available(name) for name in ["google-chrome", "chromium", "firefox"]), "chrome/chromium/firefox"
    if prerequisite == "android-emulator":
        return command_available("emulator"), "android emulator"
    if prerequisite == "kaggle-credentials":
        return bool(os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")) or command_available("kaggle"), "KAGGLE_USERNAME/KAGGLE_KEY or kaggle CLI"
    if prerequisite == "huggingface-cli":
        return command_available("huggingface-cli"), "huggingface-cli"
    if prerequisite == "docker":
        return command_available("docker"), "docker"
    if prerequisite in {"swebench", "tb", "bfcl"}:
        return command_available(prerequisite) or module_available(prerequisite.replace("-", "_")), prerequisite
    return False, prerequisite


def doctor(output_path: Path | None = None) -> dict[str, Any]:
    records = []
    for benchmark in discover_benchmarks():
        checks = []
        for prerequisite in benchmark["prerequisites"]:
            passed, detail = check_prerequisite(prerequisite)
            checks.append({"prerequisite": prerequisite, "passed": passed, "detail": detail})
        records.append(
            {
                "id": benchmark["id"],
                "ready": all(check["passed"] for check in checks),
                "prerequisites": checks,
            }
        )
    report = {
        "schema_version": 1,
        "report_type": "agent-review-doctor",
        "generated_at": utc_now(),
        "benchmarks": records,
    }
    output_path = output_path or Path.cwd() / "benchmark-doctor.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
