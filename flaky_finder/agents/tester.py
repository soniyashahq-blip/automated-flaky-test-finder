import subprocess
import time


class TesterAgent:

    def run(self, repository, command):
        start = time.perf_counter()

        try:
            result = subprocess.run(
                command,
                cwd=repository,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )

            runtime = time.perf_counter() - start

            return {
                "result": "PASS" if result.returncode == 0 else "FAIL",
                "exit_code": result.returncode,
                "runtime": runtime,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired as error:
            runtime = time.perf_counter() - start

            return {
                "result": "FAIL",
                "exit_code": -1,
                "runtime": runtime,
                "stdout": error.stdout or "",
                "stderr": "Test execution timed out.",
            }