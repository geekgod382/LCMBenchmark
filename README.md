# Legacy Code Modernization Benchmark

> I build this benchmark for participating in Kaggle benchmarking challenge

An evaluation benchmark for translating legacy programs (initially COBOL,
Fortran, and PHP) into modern languages (initially Python and Rust).

## Benchmark contract

Each JSONL task contains a legacy source program, its source and target
languages, a natural-language specification, and input/output examples. A
translation is a complete program: it reads the task input from standard input
and writes its answer to standard output. Keep prompts and input/output
contracts explicit so scores measure translation rather than interface
guessing.

The starter corpus is synthetic and intentionally small. It is a format and
pipeline prototype, not a validated research benchmark. Before publishing a
Kaggle competition, expand the corpus with legally reusable, provenance-tracked
programs; add independently authored hidden tests; and review every expected
behavior with maintainers familiar with each source language.

## Run the local scorer

Requires Python 3.10+. Rust-target tasks additionally require `rustc` on PATH.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
```

Create a CSV with columns `task_id,translated_code`, one complete target
program per task, then score it:

```powershell
legacy-modernization-score --tasks data/tasks_v0.2_full.jsonl --submission data/sample_submission.csv
```

`data/sample_submission.csv` shows the required columns. CSV quoting must be
used for multiline source code; Python's `csv` module handles it.

## Publish a Kaggle Dataset

Build the answer-free upload folder from the development corpus:

```powershell
legacy-modernization-package --tasks data/tasks_v0.2_public.jsonl --output-dir kaggle
```

Upload the contents of `kaggle/` as a Kaggle Dataset. It contains public task
prompts, source programs, v0.2 metadata, a CSV submission template, and a
dataset README. The publisher omits `tests` while preserving the other
documented task metadata. The companion notebook at
`notebooks/kaggle_quickstart.ipynb` demonstrates loading the dataset and
writing `submission.csv` without executing submitted code.

This publishes a dataset and reproducible quickstart, not a Kaggle competition
or leaderboard. A competition needs a larger validated corpus, distinct public
and private splits, a documented metric, and a Kaggle-approved evaluator. The
local metric is macro-averaged exact test-case pass rate: score each task by
the fraction of tests whose stdout exactly matches the expected output,
including significant formatting whitespace, then average task scores equally. Compilation or runtime failure
scores zero. Expected outputs belong only in private evaluation data.

Use `data/tasks_v0.2_full.jsonl` as the expanded local scoring suite and
`data/tasks_v0.2_public.jsonl` as the public task source. They share task IDs,
metadata, and public test cases; the full file contains additional cases, so
it is **not a hidden holdout**. Do not use it for leaderboard evaluation until
independent, undisclosed tests are created. The generated `kaggle/` output
contains no expected outputs. Do not upload either raw JSONL file as-is.

## Safety

The local scorer compiles and executes submitted programs as child processes.
Its timeout limits runtime, but it does not sandbox filesystem, network, or
process access. Only use it with code you trust. Do not use this CLI to grade
untrusted Kaggle submissions; production grading needs a hardened container or
equivalent isolation boundary.