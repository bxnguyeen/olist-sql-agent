import os
from datetime import datetime
from pathlib import Path
RUNS_DIR = Path("evals/runs")

import json
from decimal import Decimal

import yaml

from olist_agent.agent import AgentResult, ask
from olist_agent.db import run_query

DATASET_PATH = "evals/questions.yaml"

from decimal import Decimal


def normalize(value):
    """Make values comparable: all numbers become floats rounded to 2 decimals."""
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return round(float(value), 2)
    return value


def row_matches(gold_row: tuple, agent_row: tuple) -> bool:
    """True if every gold value appears in the agent row (extra columns are allowed)."""
    remaining = [normalize(value) for value in agent_row]
    for value in gold_row:
        if normalize(value) not in remaining:
            return False
        remaining.remove(normalize(value))
    return True


def results_match(gold_rows: list[tuple], agent_rows: list[tuple]) -> bool:
    """True if both results have the same rows, ignoring row order and extra columns."""
    if len(gold_rows) != len(agent_rows):
        return False
    remaining = list(agent_rows)
    for gold_row in gold_rows:
        match = next((row for row in remaining if row_matches(gold_row, row)), None)
        if match is None:
            return False
        remaining.remove(match)
    return True


def last_successful_sql(result: AgentResult) -> str | None:
    """Return the last run_sql query that ran without an error, or None."""
    for call in reversed(result.tool_calls):
        if call.name == "run_sql" and not call.result.startswith(("SQL error:", "Invalid arguments")):
            return json.loads(call.arguments)["query"]
    return None


def evaluate_case(case: dict) -> dict:
    """Run the agent on one case and compare its last query result with the gold result."""
    result = ask(case["question"])
    agent_sql = last_successful_sql(result)
    correct = False
    if agent_sql is not None:
        _, gold_rows = run_query(case["gold_sql"])
        _, agent_rows = run_query(agent_sql)
        correct = results_match(gold_rows, agent_rows)
    return {
        "id": case["id"],
        "question": case["question"],
        "correct": correct,
        "llm_calls": result.llm_calls,
        "total_tokens": result.total_tokens,
        "seconds": result.seconds,
        "agent_sql": agent_sql,
        "answer": result.answer,
    }



def main() -> None:
    """Run every case in the dataset and print a score table."""
    started_at = datetime.now().strftime("%Y%m%d-%H%M%S")
    with open(DATASET_PATH) as file:
        dataset = yaml.safe_load(file)

    print(f"{'case':<32}{'correct':<9}{'calls':>6}{'tokens':>8}{'seconds':>9}")
    outcomes = []
    for case in dataset["cases"]:
        outcome = evaluate_case(case)
        outcomes.append(outcome)
        mark = "yes" if outcome["correct"] else "NO"
        print(
            f"{outcome['id']:<32}{mark:<9}{outcome['llm_calls']:>6}"
            f"{outcome['total_tokens']:>8}{outcome['seconds']:>9.1f}"
        )

    total = len(outcomes)
    correct = sum(outcome["correct"] for outcome in outcomes)
    print()
    print(f"dataset version: {dataset['dataset_version']}")
    print(f"accuracy: {correct}/{total} ({correct / total:.0%})")
    print(f"average tokens: {sum(o['total_tokens'] for o in outcomes) / total:.0f}")
    print(f"average seconds: {sum(o['seconds'] for o in outcomes) / total:.1f}")
    run = {
        "started_at": started_at,
        "model": os.environ["LLM_MODEL"],
        "dataset_version": dataset["dataset_version"],
        "accuracy": correct / total,
        "outcomes": outcomes,
    }
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_path = RUNS_DIR / f"{started_at}.json"
    run_path.write_text(json.dumps(run, indent=2))
    print(f"saved: {run_path}")

