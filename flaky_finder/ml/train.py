import json
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.model_selection import LeaveOneGroupOut


FEATURE_NAMES = [
    "execution_count",
    "failure_count",
    "failure_rate",
    "pass_fail_transitions",
    "runtime_mean",
    "runtime_std",
    "runtime_variability",
    "temporal_failure_clustering",
    "sleep_indicators",
    "timeout_indicators",
    "randomness_indicators",
    "date_time_indicators",
    "concurrency_indicators",
    "shared_state_indicators",
    "ordering_indicators",
    "external_dependency_indicators",
]


def load_dataset(path):
    records = []

    with Path(path).open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number}"
                ) from error

    if not records:
        raise ValueError("Dataset is empty")

    return records


def evaluate():
    records = load_dataset("data/training_data.jsonl")

    X = [
        [float(record.get(name, 0)) for name in FEATURE_NAMES]
        for record in records
    ]
    y = [int(record["label"]) for record in records]
    groups = [record["project"] for record in records]

    if len(set(y)) != 2:
        raise ValueError("Dataset must contain both labels: 0 and 1")

    splitter = LeaveOneGroupOut()
    all_actual = []
    all_predicted = []
    project_results = []

    for train_indices, test_indices in splitter.split(
        X, y, groups
    ):
        train_labels = {y[i] for i in train_indices}

        if len(train_labels) < 2:
            project_results.append({
                "project": groups[test_indices[0]],
                "status": "SKIPPED",
                "reason": "Training fold does not contain both labels"
            })
            continue

        model = RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            class_weight="balanced"
        )

        model.fit(
            [X[i] for i in train_indices],
            [y[i] for i in train_indices]
        )

        predictions = model.predict(
            [X[i] for i in test_indices]
        )

        actual = [y[i] for i in test_indices]

        all_actual.extend(actual)
        all_predicted.extend(predictions)

        project_results.append({
            "project": groups[test_indices[0]],
            "status": "EVALUATED",
            "records": len(test_indices),
            "actual": actual,
            "predicted": [int(value) for value in predictions]
        })

    if not all_actual:
        raise ValueError(
            "No project folds could be evaluated. "
            "Add more labelled examples per project."
        )

    metrics = {
        "accuracy": accuracy_score(
            all_actual, all_predicted
        ),
        "precision": precision_score(
            all_actual, all_predicted,
            zero_division=0
        ),
        "recall": recall_score(
            all_actual, all_predicted,
            zero_division=0
        ),
        "f1": f1_score(
            all_actual, all_predicted,
            zero_division=0
        )
    }

    print(json.dumps({
        "evaluation": "Leave-one-project-out",
        "records": len(records),
        "projects": sorted(set(groups)),
        "metrics": metrics,
        "project_results": project_results,
        "warning": (
            "Only 8 synthetic records are available. "
            "These metrics are a pipeline check, not "
            "evidence of real-world performance."
        )
    }, indent=2))


if __name__ == "__main__":
    evaluate()