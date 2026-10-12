
import subprocess
from pathlib import Path


class GitHubPRAgent:

    def create_pr(
        self,
        repository,
        verified_fixes,
        title="Fix verified flaky tests",
        base="master"
    ):
        repository = Path(repository).resolve()

        if not verified_fixes:
            raise ValueError(
                "Cannot create PR without verified fixes."
            )

        for fix in verified_fixes:
            if fix.get("status") != "VERIFIED":
                raise ValueError(
                    "Every fix must be VERIFIED before "
                    "creating a PR."
                )

        branch = self._run(
            ["git", "branch", "--show-current"],
            repository
        ).strip()

        if not branch:
            raise RuntimeError(
                "Could not determine current branch."
            )

        if branch in {"master", "main", base}:
            raise ValueError(
                "Create the PR from a separate feature branch."
            )

        self._run(
            ["gh", "auth", "status"],
            repository
        )

        self._run(
            ["git", "push", "-u", "origin", branch],
            repository
        )

        fix_lines = []

        for fix in verified_fixes:
            fix_lines.append(
                f"- {fix.get('file', 'Unknown file')}: "
                f"{fix.get('passes', 0)} passes, "
                f"{fix.get('failures', 0)} failures "
                f"during verification"
            )

        body = (
            "## Summary\n"
            "This PR contains fixes that passed "
            "the project's isolated verification.\n\n"
            "## Verified fixes\n"
            + "\n".join(fix_lines)
            + "\n\n"
            "## Safety\n"
            "- Fixes were verified before PR creation.\n"
            "- This tool does not merge the PR.\n"
            "- Please review the code and CI results."
        )

        result = self._run(
            [
                "gh",
                "pr",
                "create",
                "--base",
                base,
                "--head",
                branch,
                "--title",
                title,
                "--body",
                body
            ],
            repository
        )

        return {
            "created": True,
            "branch": branch,
            "base": base,
            "url": result.strip()
        }

    @staticmethod
    def _run(command, repository):
        result = subprocess.run(
            command,
            cwd=repository,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            message = (
                result.stderr.strip()
                or result.stdout.strip()
                or "Command failed."
            )

            raise RuntimeError(message)

        return result.stdout