class FlakyScorer:

    def score(self, features):
        score = 0.0

        failure_rate = features.get(
            "failure_rate",
            0
        )

        transitions = features.get(
            "pass_fail_transitions",
            0
        )

        runtime_variability = features.get(
            "runtime_variability",
            0
        )

        temporal_clustering = features.get(
            "temporal_failure_clustering",
            0
        )

        if failure_rate >= 0.10:
            score += 0.30

        if failure_rate >= 0.25:
            score += 0.15

        if transitions >= 2:
            score += 0.20

        if transitions >= 4:
            score += 0.10

        if runtime_variability >= 0.30:
            score += 0.15

        if runtime_variability >= 0.60:
            score += 0.05

        if temporal_clustering >= 1:
            score += 0.05

        score = min(score, 1.0)

        if score >= 0.70:
            classification = "highly suspicious"
        elif score >= 0.40:
            classification = "suspicious"
        else:
            classification = "likely stable"

        return {
            "flaky_score": round(score, 3),
            "classification": classification
        }