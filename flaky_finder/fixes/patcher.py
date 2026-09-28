from pathlib import Path
import difflib


class PatchGenerator:

    def generate(self, repository, proposed_fixes):

        repository = Path(repository).resolve()

        patches = []

        for fix in proposed_fixes:

            file_path = repository / fix["file"]

            if not file_path.exists():
                patches.append({
                    "file": fix["file"],
                    "status": "file_not_found",
                    "patch": None
                })
                continue

            original = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            evidence = fix["evidence"]
            replacement = fix.get(
                "proposed_fix",
                ""
            ).strip()

            if not replacement:
                patches.append({
                    "file": fix["file"],
                    "status": "manual_review_required",
                    "patch": None
                })
                continue

            lines = original.splitlines()

            matching_index = None

            for index, line in enumerate(lines):
                if line.strip() == evidence.strip():
                    matching_index = index
                    break

            if matching_index is None:
                patches.append({
                    "file": fix["file"],
                    "status": "evidence_not_found",
                    "patch": None
                })
                continue

            original_line = lines[matching_index]

            indentation_length = (
                len(original_line)
                - len(original_line.lstrip())
            )

            indentation = original_line[
                :indentation_length
            ]

            replacement_line = (
                indentation
                + replacement.lstrip()
            )

            modified_lines = lines.copy()

            modified_lines[
                matching_index
            ] = replacement_line

            modified = "\n".join(
                modified_lines
            )

            if original.endswith("\n"):
                modified += "\n"

            patch = "".join(
                difflib.unified_diff(
                    original.splitlines(
                        keepends=True
                    ),
                    modified.splitlines(
                        keepends=True
                    ),
                    fromfile=f"a/{fix['file']}",
                    tofile=f"b/{fix['file']}"
                )
            )

            patches.append({
                "file": fix["file"],
                "status": "patch_generated",
                "patch": patch,
                "original": original_line,
                "replacement": replacement_line
            })

        return patches