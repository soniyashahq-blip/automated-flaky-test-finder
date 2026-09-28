from collections import Counter
from statistics import mean, stdev
from datetime import datetime


class FeatureExtractor:

    def extract(self, records, indicators=None):
        if not records:
            return {}

        indicators = indicators or []

        results = [record["result"] for record in records]
        runtimes = [
            float(record["runtime"])
            for record in records
        ]

        failures = results.count("FAIL")

        transitions = 0

        for i in range(1, len(results)):
            if results[i] != results[i - 1]:
                transitions += 1

        runtime_mean = mean(runtimes)

        if len(runtimes) > 1:
            runtime_std = stdev(runtimes)
        else:
            runtime_std = 0.0

        temporal_failures = self._temporal_failure_count(records)

        categories = Counter(
            indicator["category"]
            for indicator in indicators
        )

        return {
            "execution_count": len(records),
            "failure_count": failures,
            "failure_rate": failures / len(records),
            "pass_fail_transitions": transitions,
            "runtime_mean": runtime_mean,
            "runtime_std": runtime_std,
            "runtime_variability": (
                runtime_std / runtime_mean
                if runtime_mean > 0
                else 0.0
            ),
            "temporal_failure_clustering": temporal_failures,
            "sleep_indicators": categories.get(
                "sleep/time delay", 0
            ),
            "timeout_indicators": categories.get(
                "timeout", 0
            ),
            "randomness_indicators": categories.get(
                "randomness", 0
            ),
            "date_time_indicators": categories.get(
                "date/time", 0
            ),
            "concurrency_indicators": categories.get(
                "threading/concurrency", 0
            ),
            "shared_state_indicators": categories.get(
                "shared/global state", 0
            ),
            "ordering_indicators": categories.get(
                "ordering dependency", 0
            ),
            "external_dependency_indicators": categories.get(
                "external dependency", 0
            ),
        }

    def _temporal_failure_count(self, records):
        failures = []

        for record in records:
            if record["result"] == "FAIL":
                try:
                    failures.append(
                        datetime.fromisoformat(
                            record["timestamp"]
                        )
                    )
                except ValueError:
                    continue

        if len(failures) < 2:
            return 0

        failures.sort()

        clustered = 0

        for i in range(1, len(failures)):
            seconds = (
                failures[i] - failures[i - 1]
            ).total_seconds()

            if seconds <= 3600:
                clustered += 1

        return clustered