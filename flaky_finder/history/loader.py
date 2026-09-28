import json
from pathlib import Path


class HistoryLoader:
    REQUIRED_FIELDS = {
        "project",
        "repository",
        "commit",
        "test_name",
        "test_file",
        "timestamp",
        "result",
        "runtime",
    }

    def load(self, path):
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"History file not found: {path}")

        records = []

        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, 1):
                line = line.strip()

                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"Invalid JSON on line {line_number}"
                    ) from error

                missing = self.REQUIRED_FIELDS - record.keys()

                if missing:
                    raise ValueError(
                        f"Missing fields on line {line_number}: "
                        f"{sorted(missing)}"
                    )

                if record["result"] not in {"PASS", "FAIL"}:
                    raise ValueError(
                        f"Invalid result on line {line_number}: "
                        f"{record['result']}"
                    )

                records.append(record)

        return records