from flaky_finder.scanner.repo_scanner import RepoScanner


def test_scanner_finds_python():
    scanner = RepoScanner(".")
    result = scanner.scan()

    assert "Python" in result["languages"]


def test_scanner_finds_tests_directory():
    scanner = RepoScanner(".")
    result = scanner.scan()

    assert "tests" in result["test_directories"]


def test_scanner_returns_test_files():
    scanner = RepoScanner(".")
    result = scanner.scan()

    assert "tests\\test_scanner.py" in result["test_files"]