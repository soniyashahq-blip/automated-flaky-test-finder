import shutil
import subprocess
import tempfile
from pathlib import Path


class FixVerifier:

    def verify(
        self,
        repository,
        file_path,
        original_text,
        fixed_text,
        test_command,
        runs=10
    ):
        repository = Path(repository).resolve()

        with tempfile.TemporaryDirectory() as temp_dir:

            test_repository = Path(temp_dir)

            shutil.copytree(
                repository,
                test_repository,
                dirs_exist_ok=True
            )

            target_file = (
                test_repository / file_path
            )

            target_file.write_text(
                fixed_text,
                encoding="utf-8"
            )

            results = []

            for run_number in range(
                1,
                runs + 1
            ):
                result = subprocess.run(
                    test_command,
                    cwd=test_repository,
                    shell=True,
                    capture_output=True,
                    text=True
                )

                passed = result.returncode == 0

                results.append(
                    {
                        "run": run_number,
                        "result": (
                            "PASS"
                            if passed
                            else "FAIL"
                        )
                    }
                )

            failures = sum(
                1
                for result in results
                if result["result"] == "FAIL"
            )

            return {
                "runs": runs,
                "passes": runs - failures,
                "failures": failures,
                "failure_rate": failures / runs,
                "fixed": failures == 0,
                "results": results,
                "original_repository_modified": False
            }