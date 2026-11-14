import shutil
import json
from pathlib import Path

import pytest

from legacy_modernization_benchmark.package_release import build_release
from legacy_modernization_benchmark.score import score_submission


def test_python_translation_is_scored_by_test_case():
    task = {
        "task_id": "add",
        "target_language": "python",
        "tests": [
            {"stdin": "2 3\n", "stdout": "5\n"},
            {"stdin": "0 0\n", "stdout": "0\n"},
        ],
    }
    submission = {"add": "a, b = map(int, input().split())\nprint(a + b)\n"}

    result = score_submission([task], submission)

    assert result["score"] == 1.0
    assert result["tasks"] == {"add": 1.0}


def test_output_comparison_preserves_significant_whitespace():
    task = {
        "task_id": "fixed_width",
        "target_language": "python",
        "tests": [{"stdin": "", "stdout": "  7\n"}],
    }

    result = score_submission([task], {"fixed_width": "print(7)\n"})

    assert result["score"] == 0.0


def test_rust_translation_runs_when_compiler_is_available():
    if shutil.which("rustc") is None:
        pytest.skip("rustc is not installed")
    task = {
        "task_id": "double",
        "target_language": "rust",
        "tests": [{"stdin": "6\n", "stdout": "12\n"}],
    }
    submission = {
        "double": (
            "use std::io;\nfn main() { let mut s = String::new(); "
            "io::stdin().read_line(&mut s).unwrap(); "
            "let n: i32 = s.trim().parse().unwrap(); println!(\"{}\", n * 2); }"
        )
    }

    result = score_submission([task], submission)

    assert result["score"] == 1.0


def test_kaggle_release_strips_expected_outputs_and_builds_template(tmp_path):
    source_tasks = Path(__file__).parents[1] / "data" / "tasks_v0.2_public.jsonl"
    tasks_path, submission_path = build_release(source_tasks, tmp_path / "release")

    released_tasks = [json.loads(line) for line in tasks_path.read_text(encoding="utf-8").splitlines()]
    assert len(released_tasks) == 20
    assert all("tests" not in task for task in released_tasks)
    assert {"family_id", "difficulty", "legacy_features", "reference_runtime", "provenance", "version"}.issubset(released_tasks[0])
    assert released_tasks[0]["task_id"] == "cobol_pic_overflow_python"
    submission_lines = submission_path.read_text(encoding="utf-8").splitlines()
    assert submission_lines[0] == "task_id,translated_code"
    assert len(submission_lines) == 21
    assert (tmp_path / "release" / "README.md").exists()
    assert (tmp_path / "release" / "kaggle_quickstart.ipynb").exists()


def test_v02_public_and_full_tasks_are_aligned():
    data_dir = Path(__file__).parents[1] / "data"

    def read_jsonl(filename):
        return [
            json.loads(line)
            for line in (data_dir / filename).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    public_tasks = read_jsonl("tasks_v0.2_public.jsonl")
    full_tasks = read_jsonl("tasks_v0.2_full.jsonl")

    assert [task["task_id"] for task in public_tasks] == [task["task_id"] for task in full_tasks]
    for public_task, full_task in zip(public_tasks, full_tasks):
        assert {key: value for key, value in public_task.items() if key != "tests"} == {
            key: value for key, value in full_task.items() if key != "tests"
        }
        assert all(test in full_task["tests"] for test in public_task["tests"])