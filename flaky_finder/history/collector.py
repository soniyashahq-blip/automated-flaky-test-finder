import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path


class HistoryCollector:

    def collect(
        self,
        repository,
        test_file,
        test_name,
        output_file,
        runs=10
    ):
        repository = Path(repository).resolve()
        output_file = Path(output_file)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        records = []

        command = (
            f"python -m pytest "
            f"{test_file}::{test_name}"
        )

        for run_number in range(1, runs + 1):

            start = time.perf_counter()

            result = subprocess.run(
                command,
                cwd=repository,
                shell=True,
                capture_output=True,
                text=True
            )

            runtime = time.perf_counter() - start

            record = {
                "project": repository.name,
                "repository": str(repository),
                "commit": self._get_commit(repository),
                "test_name": test_name,
                "test_file": test_file,
                "timestamp": datetime.now().isoformat(),
                "result": (
                    "PASS"
                    if result.returncode == 0
                    else "FAIL"
                ),
                "runtime": round(runtime, 6),
                "run_number": run_number
            }

            records.append(record)

            print(
                f"Run {run_number}/{runs}: "
                f"{record['result']} "
                f"({record['runtime']}s)"
            )

        with output_file.open(
            "w",
            encoding="utf-8"
        ) as file:

            for record in records:
                file.write(
                    json.dumps(record)
                    + "\n"
                )

        return records

    @staticmethod
    def _get_commit(repository):
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repository,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except (
            subprocess.SubprocessError,
            OSError
        ):
            pass

        return "unknown"