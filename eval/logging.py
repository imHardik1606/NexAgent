import csv
from pathlib import Path
from typing import Any

CALL_COLUMNS = ["run_id", "timestamp", "mode", "task_id", "repeat", "step_index", "backend", "model_name",
                "prompt_tokens", "completion_tokens", "latency_s", "cost_usd", "tool_called", "tool_call_valid",
                "escalated", "error", "blocked_command_attempted"]
RUN_COLUMNS = ["run_id", "timestamp", "mode", "task_id", "category", "repeat", "passed", "failure_reason",
               "steps_taken", "hit_step_limit", "total_latency_s", "total_cost_usd", "local_calls", "cloud_calls",
               "escalations", "temperature", "git_commit"]


def append_row(results_dir: Path, filename: str, columns: list[str], row: dict[str, Any]) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / filename
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow({column: row.get(column, "") for column in columns})


def append_call(results_dir: Path, row: dict[str, Any]) -> None:
    append_row(results_dir, "calls.csv", CALL_COLUMNS, row)


def append_run(results_dir: Path, row: dict[str, Any]) -> None:
    append_row(results_dir, "runs.csv", RUN_COLUMNS, row)
