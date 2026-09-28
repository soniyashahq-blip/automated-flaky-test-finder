import argparse
import json

from flaky_finder.scanner.repo_scanner import RepoScanner
from flaky_finder.history.loader import HistoryLoader
from flaky_finder.features.ranker import TestRanker
from flaky_finder.agents.developer import DeveloperAgent
from flaky_finder.agents.tester import TesterAgent
from flaky_finder.agents.reviewer import ReviewerAgent
from flaky_finder.fixes.patcher import PatchGenerator
from flaky_finder.fixes.verifier import FixVerifier


def scan_repository(path):
    scanner = RepoScanner(path)
    return scanner.scan()


def analyze_repository(repository, history_file=None):
    scan_report = scan_repository(repository)

    records = []
    ranked_tests = []

    if history_file:
        records = HistoryLoader().load(
            history_file
        )

        ranked_tests = TestRanker().rank(
            records,
            scan_report["flaky_indicators"]
        )

    developer = DeveloperAgent()

    developer_report = developer.analyze(
        scan_report
    )

    return {
        "scan": scan_report,
        "history_records": len(records),
        "ranked_tests": ranked_tests,
        "developer": developer_report
    }


def verify_test(repository, command):
    tester = TesterAgent()

    return tester.run(
        repository,
        command
    )


def fix_repository(
    repository,
    history_file,
    verification_runs=10
):
    analysis = analyze_repository(
        repository,
        history_file
    )

    developer_report = analysis["developer"]

    patch_generator = PatchGenerator()

    patches = patch_generator.generate(
        repository,
        developer_report.get(
            "proposed_fixes",
            []
        )
    )

    verification = []

    for patch_info in patches:

        if patch_info["status"] != "patch_generated":
            verification.append({
                "file": patch_info["file"],
                "status": patch_info["status"],
                "verified": False
            })
            continue

        file_path = patch_info["file"]

        from pathlib import Path

        target = (
            Path(repository).resolve()
            / file_path
        )

        original = target.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        fixed = original.replace(
            patch_info["original"],
            patch_info["replacement"],
            1
        )

        test_name = None

        for test in analysis["ranked_tests"]:
            if test["test_file"].replace(
                "\\",
                "/"
            ) == file_path.replace(
                "\\",
                "/"
            ):
                test_name = test["test_name"]
                break

        if test_name:

            command = (
                f"python -m pytest "
                f"{file_path}::{test_name}"
            )

            verifier = FixVerifier()

            result = verifier.verify(
                repository,
                file_path,
                original,
                fixed,
                command,
                verification_runs
            )

            verification.append({
                "file": file_path,
                "test": test_name,
                "patch_status": patch_info["status"],
                "verification": result
            })

    reviewer = ReviewerAgent()

    review = reviewer.review(
        analysis["scan"],
        developer_report,
        verification
    )

    return {
        "analysis": analysis,
        "patches": patches,
        "verification": verification,
        "review": review
    }


def review_repository(
    repository,
    history_file=None
):
    analysis = analyze_repository(
        repository,
        history_file
    )

    reviewer = ReviewerAgent()

    return reviewer.review(
        analysis["scan"],
        analysis["developer"]
    )


def main():

    parser = argparse.ArgumentParser(
        prog="flaky-finder",
        description="Automated Flaky Test Finder and Fixer"
    )

    subparsers = parser.add_subparsers(
        dest="command"
    )

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a repository"
    )

    scan_parser.add_argument(
        "repository"
    )

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze repository and test history"
    )

    analyze_parser.add_argument(
        "repository"
    )

    analyze_parser.add_argument(
        "history_file",
        nargs="?"
    )

    verify_parser = subparsers.add_parser(
        "verify",
        help="Run a test command"
    )

    verify_parser.add_argument(
        "repository"
    )

    verify_parser.add_argument(
        "command_text",
        nargs=argparse.REMAINDER
    )

    review_parser = subparsers.add_parser(
        "review",
        help="Generate a review report"
    )

    review_parser.add_argument(
        "repository"
    )

    review_parser.add_argument(
        "history_file",
        nargs="?"
    )

    fix_parser = subparsers.add_parser(
        "fix",
        help="Detect, patch and verify flaky tests"
    )

    fix_parser.add_argument(
        "repository"
    )

    fix_parser.add_argument(
        "history_file"
    )

    fix_parser.add_argument(
        "--runs",
        type=int,
        default=10,
        help="Number of verification runs"
    )

    args = parser.parse_args()

    try:

        if args.command == "scan":

            result = scan_repository(
                args.repository
            )

        elif args.command == "analyze":

            result = analyze_repository(
                args.repository,
                args.history_file
            )

        elif args.command == "verify":

            command = " ".join(
                args.command_text
            )

            result = verify_test(
                args.repository,
                command
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
                args.runs
            )

        else:

            parser.print_help()
            return 0

        print(
            json.dumps(
                result,
                indent=2
            )
        )

    except Exception as error:

        print(
            json.dumps(
                {
                    "error": str(error)
                },
                indent=2
            )
        )

        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )