import argparse
import json
import subprocess
from pathlib import Path

from flaky_finder.scanner.repo_scanner import RepoScanner
from flaky_finder.history.loader import HistoryLoader
from flaky_finder.features.ranker import TestRanker
from flaky_finder.agents.developer import DeveloperAgent
from flaky_finder.agents.tester import TesterAgent
from flaky_finder.agents.reviewer import ReviewerAgent
from flaky_finder.agents.github_pr import GitHubPRAgent
from flaky_finder.fixes.patcher import PatchGenerator
from flaky_finder.fixes.verifier import FixVerifier


def scan_repository(path):
    return RepoScanner(path).scan()


def analyze_repository(repository, history_file=None):
    scan_report = scan_repository(repository)
    records = []
    ranked_tests = []

    if history_file:
        records = HistoryLoader().load(history_file)
        ranked_tests = TestRanker().rank(
            records,
            scan_report["flaky_indicators"]
        )

    developer = DeveloperAgent()
    developer_report = developer.analyze(scan_report)

    return {
        "scan": scan_report,
        "history_records": len(records),
        "ranked_tests": ranked_tests,
        "developer": developer_report
    }


def verify_test(repository, command):
    return TesterAgent().run(repository, command)


def _run_git(repository, command):
    result = subprocess.run(
        ["git"] + command,
        cwd=repository,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or result.stdout.strip()
        )

    return result.stdout.strip()


def fix_repository(
    repository,
    history_file,
    verification_runs=10,
    create_pr=False
):
    repository = Path(repository).resolve()

    if verification_runs < 1:
        raise ValueError("Verification runs must be at least 1")

    branch = _run_git(
        repository,
        ["branch", "--show-current"]
    )

    if create_pr and branch in {"master", "main"}:
        raise ValueError(
            "PR creation requires a separate feature branch."
        )

    analysis = analyze_repository(repository, history_file)
    developer_report = analysis["developer"]

    patches = PatchGenerator().generate(
        repository,
        developer_report.get("proposed_fixes", [])
    )

    verification = []
    verified_changes = []

    for patch_info in patches:
        if patch_info["status"] != "patch_generated":
            verification.append({
                "file": patch_info["file"],
                "status": patch_info["status"],
                "verified": False
            })
            continue

        relative_path = Path(patch_info["file"])

        if relative_path.is_absolute() or ".." in relative_path.parts:
            verification.append({
                "file": patch_info["file"],
                "status": "unsafe_file_path",
                "verified": False
            })
            continue

        target = (repository / relative_path).resolve()

        if repository not in target.parents:
            verification.append({
                "file": patch_info["file"],
                "status": "unsafe_file_path",
                "verified": False
            })
            continue

        if not target.is_file():
            verification.append({
                "file": patch_info["file"],
                "status": "file_not_found",
                "verified": False
            })
            continue

        original = target.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        old_line = patch_info["original"]
        new_line = patch_info["replacement"]

        if original.count(old_line) != 1:
            verification.append({
                "file": patch_info["file"],
                "status": "ambiguous_or_changed_evidence",
                "verified": False
            })
            continue

        fixed = original.replace(old_line, new_line, 1)

        normalized_patch_file = Path(
            patch_info["file"]
        ).as_posix()

        matching_tests = [
            test for test in analysis["ranked_tests"]
            if Path(test["test_file"]).as_posix()
            == normalized_patch_file
        ]

        if not matching_tests:
            verification.append({
                "file": patch_info["file"],
                "status": "no_matching_history_test",
                "verified": False
            })
            continue

        test_name = matching_tests[0]["test_name"]
        test_file = normalized_patch_file
        command = f"python -m pytest {test_file}::{test_name}"

        result = FixVerifier().verify(
            repository,
            str(relative_path),
            original,
            fixed,
            command,
            verification_runs
        )

        is_verified = result.get("fixed") is True

        verification.append({
            "file": patch_info["file"],
            "test": test_name,
            "patch_status": patch_info["status"],
            "verification": result,
            "status": "VERIFIED" if is_verified else "REJECTED"
        })

        if is_verified:
            verified_changes.append({
                "file": relative_path.as_posix(),
                "original": original,
                "fixed": fixed,
                "passes": result.get("passes", 0),
                "failures": result.get("failures", 0),
                "status": "VERIFIED"
            })

    review = ReviewerAgent().review(
        analysis["scan"],
        developer_report,
        verification
    )

    pr_result = {
        "created": False,
        "reason": "PR creation was not requested."
    }

    if create_pr:
        if not verified_changes:
            pr_result = {
                "created": False,
                "reason": "No fixes passed verification."
            }
        else:
            changed_files = {
                item["file"] for item in verified_changes
            }

            if len(changed_files) != len(verified_changes):
                raise RuntimeError(
                    "Multiple verified fixes target the same file. "
                    "Review and combine them before publishing."
                )

            existing_changes = _run_git(
                repository,
                ["status", "--porcelain"]
            )

            if existing_changes:
                raise RuntimeError(
                    "Working tree is not clean. Commit or stash "
                    "existing changes before applying verified fixes."
                )

            for item in verified_changes:
                target = (repository / item["file"]).resolve()

                if repository not in target.parents:
                    raise RuntimeError(
                        "Unsafe file path detected before applying fix."
                    )

                target.write_text(
                    item["fixed"],
                    encoding="utf-8"
                )

            _run_git(
                repository,
                ["add"] + [
                    item["file"] for item in verified_changes
                ]
            )

            staged = _run_git(
                repository,
                ["diff", "--cached", "--name-only"]
            ).splitlines()

            expected = sorted(
                Path(item["file"]).as_posix()
                for item in verified_changes
            )

            staged = [
                Path(item).as_posix() for item in staged
            ]

            if sorted(staged) != expected:
                raise RuntimeError(
                    "Staged files do not match the verified fixes. "
                    "Review the Git index before continuing."
                )

            _run_git(
                repository,
                [
                    "commit",
                    "-m",
                    "Apply verified flaky test fixes"
                ]
            )

            pr_fixes = [
                {
                    "file": item["file"],
                    "status": "VERIFIED",
                    "passes": item["passes"],
                    "failures": item["failures"]
                }
                for item in verified_changes
            ]

            pr_result = GitHubPRAgent().create_pr(
                repository,
                pr_fixes
            )

    return {
        "analysis": analysis,
        "patches": patches,
        "verification": verification,
        "review": review,
        "github_pr": pr_result
    }


def review_repository(repository, history_file=None):
    analysis = analyze_repository(repository, history_file)
    return ReviewerAgent().review(
        analysis["scan"],
        analysis["developer"]
    )


def main():
    parser = argparse.ArgumentParser(
        prog="flaky-finder",
        description="Automated Flaky Test Finder and Fixer"
    )

    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("repository")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("repository")
    analyze_parser.add_argument("history_file", nargs="?")

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("repository")
    verify_parser.add_argument(
        "command_text",
        nargs=argparse.REMAINDER
    )

    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("repository")
    review_parser.add_argument("history_file", nargs="?")

    fix_parser = subparsers.add_parser("fix")
    fix_parser.add_argument("repository")
    fix_parser.add_argument("history_file")
    fix_parser.add_argument("--runs", type=int, default=10)
    fix_parser.add_argument(
        "--create-pr",
        action="store_true",
        help="Apply verified fixes on this branch and open a PR"
    )

    args = parser.parse_args()

    try:
        if args.command == "scan":
            result = scan_repository(args.repository)

        elif args.command == "analyze":
            result = analyze_repository(
                args.repository,
                args.history_file
            )

        elif args.command == "verify":
            result = verify_test(
                args.repository,
                " ".join(args.command_text)
            )

        elif args.command == "review":
            result = review_repository(
                args.repository,
                args.history_file
            )

        elif args.command == "fix":
            result = fix_repository(
                args.repository,
                args.history_file,
                args.runs,
                args.create_pr
            )

        else:
            parser.print_help()
            return 0

        print(json.dumps(result, indent=2))
        return 0

    except Exception as error:
        print(json.dumps({"error": str(error)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
