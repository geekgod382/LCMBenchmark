"""Build answer-free files for publishing as a Kaggle dataset."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any

PUBLIC_FIELDS = (
    "task_id",
    "family_id",
    "source_language",
    "target_language",
    "difficulty",
    "legacy_features",
    "prompt",
    "source_code",
    "reference_runtime",
    "provenance",
    "version",
)
DATASET_README = """# Legacy Code Modernization Benchmark (Prototype)

This Kaggle Dataset contains public prompts and source programs for synthetic
legacy-to-modern translation tasks. It is a small format and workflow demo,
not a validated benchmark or Kaggle leaderboard competition.

## Files

- `tasks.jsonl`: one public task per line with `task_id`, `family_id`,
  `source_language`, `target_language`, `difficulty`, `legacy_features`,
  `prompt`, `source_code`, `reference_runtime`, `provenance`, and `version`.
  The private `tests` field is omitted.
- `sample_submission.csv`: required columns are `task_id` and
    `translated_code`. Put one complete target-language program in each row.
- `kaggle_quickstart.ipynb`: example for inspecting tasks and preparing a CSV.

The public package intentionally omits expected outputs. This prototype does
not include a hosted hidden-test evaluator or a leaderboard. The repository's
local scorer is only for trusted code and is not a sandbox. Do not run
untrusted translations outside an isolated grading service.

All source programs in this prototype are synthetic examples. Before wider
release, expand the corpus, record provenance and licensing per task, select
an appropriate dataset license, add expert-reviewed tests, and establish a
private evaluation split.
"""


def build_release(tasks_path: Path, output_dir: Path) -> tuple[Path, Path]:
    tasks: list[dict[str, Any]] = []
    with tasks_path.open(encoding="utf-8") as task_file:
        for line_number, line in enumerate(task_file, start=1):
            if not line.strip():
                continue
            task = json.loads(line)
            missing = set(PUBLIC_FIELDS) - task.keys()
            if missing:
                raise ValueError(f"Task on line {line_number} is missing fields: {sorted(missing)}")
            tasks.append({field: task[field] for field in PUBLIC_FIELDS})

    if not tasks:
        raise ValueError("The task file contains no tasks.")
    task_ids = [task["task_id"] for task in tasks]
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("Task IDs must be unique.")

    output_dir.mkdir(parents=True, exist_ok=True)
    tasks_output = output_dir / "tasks.jsonl"
    with tasks_output.open("w", encoding="utf-8", newline="\n") as task_file:
        for task in tasks:
            task_file.write(json.dumps(task, ensure_ascii=False) + "\n")

    submission_output = output_dir / "sample_submission.csv"
    with submission_output.open("w", encoding="utf-8", newline="") as submission_file:
        writer = csv.writer(submission_file)
        writer.writerow(("task_id", "translated_code"))
        writer.writerows((task_id, "") for task_id in task_ids)

    (output_dir / "README.md").write_text(DATASET_README, encoding="utf-8")
    notebook_path = Path(__file__).resolve().parents[2] / "notebooks" / "kaggle_quickstart.ipynb"
    if notebook_path.exists():
        shutil.copyfile(notebook_path, output_dir / notebook_path.name)
    return tasks_output, submission_output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    tasks_path, submission_path = build_release(args.tasks, args.output_dir)
    print(f"Wrote {tasks_path} and {submission_path}")


if __name__ == "__main__":
    main()