import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

import config
from agent import run_task
from backend import CloudBackend, ProviderError
from eval.logging import append_call, append_run
from eval.tasks import TASKS

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
SANDBOX_DIR = ROOT / "sandbox"


def _cloud_ready() -> str | None:
    if not os.getenv("GROQ_API_KEY", "").strip() or os.getenv("GROQ_API_KEY") == "your_key_here":
        return "GROQ_API_KEY is not set. Required for modes: all_cloud, routed, all"
    return None


def _cloud_preflight() -> str | None:
    try:
        CloudBackend().preflight()
    except (ProviderError, ValueError) as exc:
        return str(exc)
    return None


def _local_ready() -> str | None:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError) as exc:
        return f"Ollama is not reachable at localhost:11434. Start Ollama, then retry. ({exc})"
    models = {item.get("name", "") for item in payload.get("models", [])}
    if config.LOCAL_MODEL not in models:
        return f"Model {config.LOCAL_MODEL} not found. Run: ollama pull {config.LOCAL_MODEL}"
    return None


def preflight_check(mode: str) -> bool:
    modes = {"all_cloud", "all_local", "routed", "all"}
    if mode not in modes:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        raise SystemExit(2)
    checks = []
    if mode in {"all_cloud", "routed", "all"}:
        checks.extend([_cloud_ready, _cloud_preflight])
    if mode in {"all_local", "routed", "all"}:
        checks.append(_local_ready)
    for check in checks:
        message = check()
        if message:
            print(message, file=sys.stderr)
            raise SystemExit(1)
    return True


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _completed(results_dir: Path) -> set[tuple[str, str, int]]:
    path = results_dir / "runs.csv"
    if not path.exists():
        return set()
    import csv
    with path.open(newline="", encoding="utf-8") as handle:
        return {(row["mode"], row["task_id"], int(row["repeat"])) for row in csv.DictReader(handle)}


def _reset_sandbox(task: object) -> tuple[Path, str]:
    if SANDBOX_DIR.exists():
        shutil.rmtree(SANDBOX_DIR)
    SANDBOX_DIR.mkdir(parents=True)
    task.setup(SANDBOX_DIR)
    memory_path = SANDBOX_DIR / "memory.json"
    return SANDBOX_DIR, str(memory_path)


def _cost(call: object) -> float:
    if call.backend != "cloud":
        return 0.0
    return (call.prompt_tokens * config.CLOUD_PRICE_PER_M_INPUT + call.completion_tokens * config.CLOUD_PRICE_PER_M_OUTPUT) / 1_000_000


def run_one(task: object, mode: str, repeat: int, results_dir: Path) -> None:
    run_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    started = __import__("time").perf_counter()
    result = None
    failure_reason = ""
    passed = False
    sandbox = None
    try:
        sandbox, memory_path = _reset_sandbox(task)
        result = run_task(task.prompt, mode, sandbox=str(sandbox), memory_path=memory_path)
        passed, failure_reason = task.check(sandbox, result)
        if not result.passed and not failure_reason:
            failure_reason = result.failure_reason
    except Exception as exc:
        raise ProviderError(f"Evaluation aborted for {task.id}: {exc}") from exc

    for call in result.calls:
        append_call(results_dir, {
            "run_id": run_id, "timestamp": timestamp, "mode": mode, "task_id": task.id, "repeat": repeat,
            "step_index": call.step_index, "backend": call.backend, "model_name": call.model_name,
            "prompt_tokens": call.prompt_tokens, "completion_tokens": call.completion_tokens,
            "latency_s": call.latency_s, "cost_usd": _cost(call),
            "tool_called": bool(call.tool_calls), "tool_call_valid": call.tool_call_valid,
            "escalated": call.escalated, "error": call.error,
            "blocked_command_attempted": call.blocked_command_attempted,
        })
    if not passed and not failure_reason:
        failure_reason = result.failure_reason
    append_run(results_dir, {
        "run_id": run_id, "timestamp": timestamp, "mode": mode, "task_id": task.id, "category": task.category,
        "repeat": repeat, "passed": passed, "failure_reason": failure_reason, "steps_taken": result.steps,
        "hit_step_limit": result.hit_step_limit,
        "total_latency_s": sum(call.latency_s for call in result.calls),
        "total_cost_usd": sum(_cost(call) for call in result.calls),
        "local_calls": sum(call.backend == "local" for call in result.calls),
        "cloud_calls": sum(call.backend == "cloud" for call in result.calls),
        "escalations": sum(call.escalated for call in result.calls), "temperature": config.TEMPERATURE,
        "git_commit": _git_commit(),
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all_cloud", "all_local", "routed", "all"], required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--tasks")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    preflight_check(args.mode)
    selected = TASKS
    if args.tasks:
        wanted = set(args.tasks.split(","))
        selected = [task for task in TASKS if task.id in wanted]
        if len(selected) != len(wanted):
            raise SystemExit("Unknown task id")
    modes = ["all_cloud", "all_local", "routed"] if args.mode == "all" else [args.mode]
    completed = _completed(RESULTS_DIR)
    for mode in modes:
        for task in selected:
            for repeat in range(1, args.repeats + 1):
                if (mode, task.id, repeat) in completed:
                    continue
                try:
                    run_one(task, mode, repeat, RESULTS_DIR)
                except ProviderError as exc:
                    print(str(exc), file=sys.stderr)
                    raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
