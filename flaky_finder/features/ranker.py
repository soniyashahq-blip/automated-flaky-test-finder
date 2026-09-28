from collections import defaultdict

from flaky_finder.features.extractor import FeatureExtractor
from flaky_finder.ml.scorer import FlakyScorer


class TestRanker:

    def __init__(self):
        self.extractor = FeatureExtractor()
        self.scorer = FlakyScorer()

    def rank(self, records, indicators=None):
        groups = defaultdict(list)

        for record in records:
            test_name = record["test_name"]
            groups[test_name].append(record)

        ranked = []

        for test_name, test_records in groups.items():

            test_file = test_records[0]["test_file"]

            test_indicators = []

            for indicator in indicators or []:
                indicator_file = indicator["file"].replace(
                    "\\",
                    "/"
                )

                history_file = test_file.replace(
                    "\\",
                    "/"
                )

                if indicator_file == history_file:
                    test_indicators.append(indicator)

            features = self.extractor.extract(
                test_records,
                test_indicators
            )

            flaky_analysis = self.scorer.score(
                features
            )

            ranked.append(
                {
                    "test_name": test_name,
                    "test_file": test_file,
                    "executions": len(test_records),
                    "features": features,
                    "flaky_analysis": flaky_analysis,
                }
            )

        ranked.sort(
            key=lambda item:
            item["flaky_analysis"]["flaky_score"],
            reverse=True
        )

        return ranked