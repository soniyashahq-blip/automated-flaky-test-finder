import json
import re
from pathlib import Path

from flaky_finder.agents.qwen_client import QwenClient
from flaky_finder.fixes.suggestions import generate_suggestions


class DeveloperAgent:

    def __init__(self):
        self.qwen = QwenClient()

    def analyze(self, scan_report):

        indicators = scan_report.get(
            "flaky_indicators",
            []
        )

        suggestions = generate_suggestions(
            indicators
        )

        proposed_fixes = []

        repository = Path(
            scan_report["repository"]
        )

        for indicator in indicators:

            file_path = (
                repository / indicator["file"]
            )

            code_context = self._get_context(
                file_path,
                indicator["line"]
            )

            prompt = f"""
You are a software engineer fixing a flaky test.

File:
{indicator["file"]}

Problematic line:
{indicator["line"]}

Detected root cause:
{indicator["category"]}

Problematic code:
{indicator["evidence"]}

Relevant test code:
{code_context}

Return ONLY valid JSON.

Use exactly this format:

{{
  "cause": "short root cause",
  "replacement": "complete replacement line of code",
  "explanation": "short explanation"
}}

Rules:
- The replacement MUST make the test deterministic.
- The replacement MUST preserve the intended test behavior.
- Read the assertion and surrounding test code before choosing the replacement.
- The replacement MUST NOT intentionally make the test fail.
- Do not modify unrelated code.
- Do not include markdown.
- Do not include ``` fences.
- Return only JSON.
"""

            try:

                ai_response = self.qwen.generate(
                    prompt
                )

                ai_fix = self._parse_response(
                    ai_response
                )

            except Exception as error:

                ai_response = (
                    f"Qwen analysis unavailable: {error}"
                )

                ai_fix = {
                    "cause": indicator["category"],
                    "replacement": "",
                    "explanation": ai_response
                }

            proposed_fixes.append(
                {
                    "file": indicator["file"],
                    "line": indicator["line"],
                    "cause": indicator["category"],
                    "evidence": indicator["evidence"],
                    "ai_analysis": ai_fix[
                        "explanation"
                    ],
                    "proposed_fix": ai_fix[
                        "replacement"
                    ],
                    "safe_action": (
                        "Review the AI-generated fix before "
                        "modifying the repository."
                    )
                }
            )

        return {
            "suspected_causes": suggestions,
            "proposed_fixes": proposed_fixes,
            "automatic_modification": False
        }

    @staticmethod
    def _get_context(file_path, line_number):

        try:
            lines = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            ).splitlines()

        except OSError:
            return ""

        start = max(
            0,
            line_number - 6
        )

        end = min(
            len(lines),
            line_number + 5
        )

        context = []

        for index in range(start, end):

            context.append(
                f"{index + 1}: {lines[index]}"
            )

        return "\n".join(context)

    @staticmethod
    def _parse_response(response):

        response = response.strip()

        response = re.sub(
            r"^```json\s*",
            "",
            response,
            flags=re.IGNORECASE
        )

        response = re.sub(
            r"\s*```$",
            "",
            response
        )

        data = json.loads(response)

        return {
            "cause": data.get(
                "cause",
                "unknown"
            ),
            "replacement": data.get(
                "replacement",
                ""
            ),
            "explanation": data.get(
                "explanation",
                ""
            )
        }