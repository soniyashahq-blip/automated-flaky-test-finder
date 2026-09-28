import os
import re
from pathlib import Path


class RepoScanner:

    def __init__(self, repository):
        self.repository = Path(repository).resolve()

        if not self.repository.exists():
            raise FileNotFoundError(
                f"Repository not found: {repository}"
            )

        if not self.repository.is_dir():
            raise ValueError(
                f"Repository path is not a directory: {repository}"
            )

    def scan(self):
        files = self._get_files()
        test_files = self._find_test_files(files)

        return {
            "repository": str(self.repository),
            "languages": self._detect_languages(files),
            "test_frameworks": self._detect_frameworks(files),
            "test_files": test_files,
            "test_directories": self._find_test_directories(),
            "test_commands": self._detect_test_commands(files),
            "configuration_files": self._find_config_files(files),
            "ci_configuration": self._find_ci_files(files),
            "flaky_indicators": self._find_flaky_indicators(
                files,
                test_files
            ),
        }

    def _get_files(self):
        ignored = {
            ".git",
            ".venv",
            "venv",
            "env",
            "node_modules",
            "__pycache__",
            ".idea",
            ".vscode",
            ".pytest_cache",
            ".mypy_cache",
            ".tox",
            "dist",
            "build",
            "coverage",
        }

        result = []

        for root, dirs, filenames in os.walk(self.repository):
            dirs[:] = [
                directory
                for directory in dirs
                if directory not in ignored
            ]

            for filename in filenames:
                result.append(Path(root) / filename)

        return result

    def _detect_languages(self, files):
        extensions = {
            ".py": "Python",
            ".java": "Java",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".c": "C",
            ".h": "C",
            ".cpp": "C++",
            ".cc": "C++",
            ".cxx": "C++",
            ".hpp": "C++",
            ".cs": "C#",
            ".go": "Go",
            ".rs": "Rust",
        }

        languages = set()

        for file in files:
            language = extensions.get(
                file.suffix.lower()
            )

            if language:
                languages.add(language)

        return sorted(languages)

    def _detect_frameworks(self, files):
        frameworks = set()

        names = {
            file.name.lower()
            for file in files
        }

        if "pytest.ini" in names:
            frameworks.add("pytest")

        for file in files:
            if file.name.lower() == "pyproject.toml":
                text = self._read(file).lower()

                if (
                    "pytest" in text
                    or "testpaths" in text
                ):
                    frameworks.add("pytest")

            if file.name.lower() == "conftest.py":
                frameworks.add("pytest")

            if file.suffix.lower() == ".py":
                text = self._read(file)

                if re.search(
                    r"^\s*(import|from)\s+pytest\b",
                    text,
                    re.MULTILINE
                ):
                    frameworks.add("pytest")

                if re.search(
                    r"^\s*(import|from)\s+unittest\b",
                    text,
                    re.MULTILINE
                ):
                    frameworks.add("unittest")

            if file.name.lower() == "package.json":
                text = self._read(file).lower()

                if "jest" in text:
                    frameworks.add("Jest")

                if "mocha" in text:
                    frameworks.add("Mocha")

                if "vitest" in text:
                    frameworks.add("Vitest")

            if file.name.lower() == "pom.xml":
                text = self._read(file).lower()

                if "junit" in text:
                    frameworks.add("JUnit")

            if file.name.lower() in {
                "build.gradle",
                "build.gradle.kts"
            }:
                text = self._read(file).lower()

                if "junit" in text:
                    frameworks.add("JUnit")

        return sorted(frameworks)

    def _find_test_files(self, files):
        result = []

        test_directories = {
            "test",
            "tests",
            "spec",
            "specs"
        }

        source_extensions = {
            ".py",
            ".java",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".c",
            ".cc",
            ".cpp",
            ".cxx",
            ".h",
            ".hpp",
            ".cs",
            ".go",
            ".rs"
        }

        for file in files:
            relative = file.relative_to(
                self.repository
            )

            name = file.name.lower()

            if file.suffix.lower() not in source_extensions:
                continue

            parent_parts = {
                part.lower()
                for part in relative.parts[:-1]
            }

            inside_test_directory = bool(
                parent_parts.intersection(
                    test_directories
                )
            )

            test_name = (
                name.startswith("test_")
                or name.endswith("_test.py")
                or name.endswith(".test.js")
                or name.endswith(".test.ts")
                or name.endswith(".test.jsx")
                or name.endswith(".test.tsx")
                or name.endswith(".spec.js")
                or name.endswith(".spec.ts")
                or name.endswith(".spec.jsx")
                or name.endswith(".spec.tsx")
                or name.endswith("test.java")
                or name.endswith("test.cpp")
                or name.endswith("test.cc")
                or name.endswith("test.c")
            )

            if inside_test_directory or test_name:
                result.append(str(relative))

        return sorted(set(result))

    def _find_test_directories(self):
        result = []

        ignored = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__"
        }

        for root, dirs, _ in os.walk(self.repository):
            dirs[:] = [
                directory
                for directory in dirs
                if directory not in ignored
            ]

            for directory in dirs:
                if directory.lower() in {
                    "test",
                    "tests",
                    "spec",
                    "specs"
                }:
                    path = Path(root) / directory

                    result.append(
                        str(
                            path.relative_to(
                                self.repository
                            )
                        )
                    )

        return sorted(set(result))

    def _detect_test_commands(self, files):
        commands = []

        names = {
            file.name.lower()
            for file in files
        }

        extensions = {
            file.suffix.lower()
            for file in files
        }

        if ".py" in extensions:
            if (
                "pytest.ini" in names
                or "conftest.py" in names
                or "pyproject.toml" in names
            ):
                commands.append("pytest")
            else:
                commands.append(
                    "python -m unittest discover"
                )

        if "package.json" in names:
            commands.append("npm test")

        if "pom.xml" in names:
            commands.append("mvn test")

        if (
            "build.gradle" in names
            or "build.gradle.kts" in names
        ):
            commands.append("gradle test")

        if "cmakelists.txt" in names:
            commands.append("ctest")

        return sorted(set(commands))

    def _find_config_files(self, files):
        config_names = {
            "pyproject.toml",
            "pytest.ini",
            "setup.cfg",
            "tox.ini",
            "package.json",
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
            "cmakelists.txt",
            "jest.config.js",
            "jest.config.ts",
            "vitest.config.js",
            "vitest.config.ts"
        }

        result = []

        for file in files:
            if file.name.lower() in config_names:
                result.append(
                    str(
                        file.relative_to(
                            self.repository
                        )
                    )
                )

        return sorted(result)

    def _find_ci_files(self, files):
        result = []

        ci_names = {
            ".travis.yml",
            "jenkinsfile",
            ".gitlab-ci.yml",
            "azure-pipelines.yml"
        }

        for file in files:
            relative = file.relative_to(
                self.repository
            )

            parts = [
                part.lower()
                for part in relative.parts
            ]

            if (
                ".github" in parts
                and "workflows" in parts
            ):
                result.append(str(relative))

            elif file.name.lower() in ci_names:
                result.append(str(relative))

        return sorted(set(result))

    def _find_flaky_indicators(
        self,
        files,
        test_files
    ):
        patterns = {
            "sleep/time delay": [
                r"\btime\.sleep\s*\(",
                r"(?<!\.)\bsleep\s*\("
            ],
            "timeout": [
                r"\btimeout\s*=",
                r"\btimeout\s*\("
            ],
            "randomness": [
                r"\brandom\.",
                r"\brandint\s*\(",
                r"\brandomize\s*\(",
                r"\bMath\.random\s*\("
            ],
            "date/time": [
                r"\bdatetime\.now\s*\(",
                r"\bdatetime\.today\s*\(",
                r"\btime\.time\s*\(",
                r"\bdate\.today\s*\(",
                r"\bnew\s+Date\s*\("
            ],
            "threading/concurrency": [
                r"\bthreading\.",
                r"\bThread\s*\(",
                r"\basyncio\.",
                r"\basync\s+def\b",
                r"\bawait\s+"
            ],
            "shared/global state": [
                r"^\s*global\s+\w+",
                r"\bsingleton\b"
            ],
            "ordering dependency": [
                r"\bdepends_on\s*\(",
                r"\bdepends_on\s*="
            ],
            "external dependency": [
                r"\brequests\.",
                r"\burllib\.",
                r"\bhttpx\.",
                r"\baxios\.",
                r"\bfetch\s*\(",
                r"\bhttp://",
                r"\bhttps://"
            ]
        }

        test_paths = {
            Path(path)
            for path in test_files
        }

        indicators = []

        for file in files:
            relative = file.relative_to(
                self.repository
            )

            if relative not in test_paths:
                continue

            text = self._read(file)

            for line_number, line in enumerate(
                text.splitlines(),
                start=1
            ):
                stripped = line.strip()

                if not stripped:
                    continue

                if (
                    stripped.startswith("#")
                    or stripped.startswith("//")
                ):
                    continue

                for category, regexes in patterns.items():
                    for regex in regexes:
                        if re.search(
                            regex,
                            line,
                            re.IGNORECASE
                        ):
                            indicators.append(
                                {
                                    "category": category,
                                    "file": str(relative),
                                    "line": line_number,
                                    "evidence": stripped
                                }
                            )
                            break

        return indicators

    @staticmethod
    def _read(file):
        try:
            return file.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except (
            OSError,
            PermissionError
        ):
            return ""


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python -m "
            "flaky_finder.scanner.repo_scanner "
            "<repository>"
        )
        raise SystemExit(1)

    scanner = RepoScanner(sys.argv[1])

    print(
        json.dumps(
            scanner.scan(),
            indent=2
        )
    )