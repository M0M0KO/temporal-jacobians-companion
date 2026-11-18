"""Embed the three published aggregate tables in the offline browser companion."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source-data"
TABLES = {
    "exact": "figure2a_recovery_rates.csv",
    "cohorts": "figure3a_3b_a002_cohort_metrics.csv",
    "human": "figure4b_architecture_equivalence.csv",
}


def read_table(name):
    with (SOURCE / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def embedded_data():
    data = {key: read_table(name) for key, name in TABLES.items()}
    summary = json.loads((SOURCE / "analysis_summary.json").read_text(encoding="utf-8-sig"))
    benchmark = summary["synthetic"]
    human = summary["human_prediction"]
    exact = [row for row in data["exact"] if row["condition"] == "Exact known system"]
    assert sum(int(row["successes"]) for row in exact) == benchmark["exact_recovered"]
    assert len(data["cohorts"]) == benchmark["learned_total"]
    assert sum(row["complete_recovery"] == "TRUE" for row in data["cohorts"]) == benchmark["learned_recovered"]
    assert all(float(row["finite_effect_r2"]) >= 0.8 and float(row["finite_sign_accuracy"]) >= 0.9
               for row in data["cohorts"])
    assert len(data["human"]) == 24 and all(int(x["n_participants"]) == human["participants"] for x in data["human"])
    assert human["common_events"] == 73219
    data["humanEvents"] = human["common_events"]
    return json.dumps(data, separators=(",", ":"), ensure_ascii=True).replace("<", r"\u003c")


if __name__ == "__main__":
    token = "__PUBLIC_FROZEN_TABLES__"
    template = (ROOT / "template.html").read_text(encoding="utf-8")
    assert template.count(token) == 1
    with (ROOT / "index.html").open("w", encoding="utf-8", newline="\n") as output:
        output.write(template.replace(token, embedded_data()))
