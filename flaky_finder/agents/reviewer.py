class ReviewerAgent:

    def review(
        self,
        scan_report,
        developer_report,
        test_report=None
    ):
        verified_fixes = []

        for result in test_report or []:

            verification = result.get(
                "verification",
                {}
            )

            if verification.get("fixed") is True:

                verified_fixes.append({
                    "file": result["file"],
                    "test": result.get("test"),
                    "status": "VERIFIED",
                    "passes": verification.get(
                        "passes",
                        0
                    ),
                    "failures": verification.get(
                        "failures",
                        0
                    ),
                    "failure_rate": verification.get(
                        "failure_rate",
                        1.0
                    )
                })

            else:

                verified_fixes.append({
                    "file": result["file"],
                    "test": result.get("test"),
                    "status": "REJECTED",
                    "passes": verification.get(
                        "passes",
                        0
                    ),
                    "failures": verification.get(
                        "failures",
                        0
                    ),
                    "failure_rate": verification.get(
                        "failure_rate",
                        1.0
                    )
                })

        return {
            "summary": "Flaky test analysis review",
            "suspected_causes": developer_report.get(
                "suspected_causes",
                []
            ),
            "test_result": test_report,
            "verified_fixes": verified_fixes,
            "github_action": "No GitHub changes were made.",
            "approval_required": True
        }