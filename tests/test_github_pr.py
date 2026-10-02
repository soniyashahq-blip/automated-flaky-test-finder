
import pytest

from flaky_finder.agents.github_pr import GitHubPRAgent


def test_pr_rejects_empty_fixes():
    agent = GitHubPRAgent()

    with pytest.raises(ValueError):
        agent.create_pr(
            ".",
            []
        )


def test_pr_rejects_unverified_fix():
    agent = GitHubPRAgent()

    with pytest.raises(ValueError):
        agent.create_pr(
            ".",
            [
                {
                    "file": "tests/test_flaky.py",
                    "status": "REJECTED",
                    "passes": 0,
                    "failures": 5
                }
            ]
        )