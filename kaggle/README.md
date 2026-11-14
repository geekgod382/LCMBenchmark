# Legacy Code Modernization Benchmark (Prototype)

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
