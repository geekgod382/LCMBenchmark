"""Score translated programs against task input/output examples."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def load_tasks(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as task_file:
        tasks = [json.loads(line) for line in task_file if line.strip()]
    if not tasks:
        raise ValueError("The task file contains no tasks.")
    task_ids = [task["task_id"] for task in tasks]
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("Task IDs must be unique.")
    return tasks


def load_submission(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as submission_file:
        reader = csv.DictReader(submission_file)
        required_columns = {"task_id", "translated_code"}
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            raise ValueError("Submission CSV must have task_id and translated_code columns.")
        rows = list(reader)

    submissions: dict[str, str] = {}
    for row in rows:
        task_id = row["task_id"]
        if task_id in submissions:
            raise ValueError(f"Duplicate submission for task {task_id!r}.")
        submissions[task_id] = row["translated_code"] or ""
    return submissions


def _build_command(
    target_language: str, code: str, directory: Path, timeout: float
) -> list[str]:
    if target_language == "python":
        source_path = directory / "translated.py"
        source_path.write_text(code, encoding="utf-8")
        return [sys.executable, str(source_path)]

    if target_language == "rust":
        compiler = shutil.which("rustc")
        if compiler is None:
            raise RuntimeError("rustc is required to score Rust-target tasks.")
        source_path = directory / "translated.rs"
        executable_path = directory / "translated"
        source_path.write_text(code, encoding="utf-8")
        compilation = subprocess.run(
            [compiler, "--edition=2021", str(source_path), "-o", str(executable_path)],
            capture_output=True,
            text=True,
            timeout=max(timeout, 30.0),
            check=False,
        )
        if compilation.returncode != 0:
            raise ValueError(compilation.stderr or "Rust compilation failed.")
        return [str(executable_path)]

    raise ValueError(f"Unsupported target language: {target_language!r}.")


def _score_task(task: dict[str, Any], code: str, timeout: float) -> tuple[int, int]:
    tests = task["tests"]
    if not tests:
        raise ValueError(f"Task {task['task_id']!r} has no tests.")
    try:
        with tempfile.TemporaryDirectory(prefix="legacy-benchmark-") as temp_dir:
            command = _build_command(task["target_language"], code, Path(temp_dir), timeout)
            passed = 0
            for test_case in tests:
                result = subprocess.run(
                    command,
                    input=test_case["stdin"],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
                if result.returncode == 0 and result.stdout == test_case["stdout"]:
                    passed += 1
            return passed, len(tests)
    except (OSError, subprocess.SubprocessError, ValueError, RuntimeError):
        return 0, len(tests)


def score_submission(
    tasks: list[dict[str, Any]], submissions: dict[str, str], timeout: float = 2.0
) -> dict[str, Any]:
    task_ids = {task["task_id"] for task in tasks}
    extra_ids = set(submissions) - task_ids
    if extra_ids:
        raise ValueError(f"Submission has unknown task IDs: {sorted(extra_ids)}")

    task_results: dict[str, float] = {}
    language_totals: dict[str, list[float]] = {}
    for task in tasks:
        task_id = task["task_id"]
        code = submissions.get(task_id, "")
        passed, total = _score_task(task, code, timeout) if code.strip() else (0, len(task["tests"]))
        task_score = passed / total if total else 0.0
        task_results[task_id] = task_score
        language_totals.setdefault(task["target_language"], []).append(task_score)

    return {
        "score": sum(task_results.values()) / len(task_results),
        "tasks": task_results,
        "by_target_language": {
            language: sum(scores) / len(scores) for language, scores in language_totals.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args()

    result = score_submission(load_tasks(args.tasks), load_submission(args.submission), args.timeout)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()