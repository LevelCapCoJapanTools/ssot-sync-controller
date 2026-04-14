"""path_validator のテスト。"""

from __future__ import annotations

import pytest

from ssot_sync_controller.models import ResolvedFile
from ssot_sync_controller.path_validator import filter_by_whitelist, is_path_allowed

PATTERNS = [
    "docs/**",
    ".github/copilot/**",
    ".github/copilot-instructions.md",
    ".github/instructions/**",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".agent.md",
    ".claude/**",
]


# -------------------------
# is_path_allowed
# -------------------------


@pytest.mark.parametrize(
    "path, expected",
    [
        ("AGENTS.md", True),
        ("CLAUDE.md", True),
        ("GEMINI.md", True),
        (".agent.md", True),
        ("docs/README.md", True),
        ("docs/sub/file.md", True),
        (".github/copilot-instructions.md", True),
        (".github/copilot/00-index.md", True),
        (".github/instructions/python.instructions.md", True),
        (".claude/agents/myagent.md", True),
        # ホワイトリスト外
        ("src/app.py", False),
        (".github/workflows/ci.yml", False),
        ("package.json", False),
        ("README.md", False),
    ],
)
def test_is_path_allowed(path: str, expected: bool) -> None:
    assert is_path_allowed(path, PATTERNS) == expected


# -------------------------
# filter_by_whitelist
# -------------------------


def _rf(target: str, catalog: str = "cat") -> ResolvedFile:
    return ResolvedFile(target_path=target, absolute_source="/src/f", catalog_name=catalog)


def test_filter_allows_matching_paths() -> None:
    files = [_rf("AGENTS.md"), _rf("docs/guide.md"), _rf("src/app.py")]
    passed, skipped = filter_by_whitelist(files, PATTERNS)
    assert len(passed) == 2
    assert {f.target_path for f in passed} == {"AGENTS.md", "docs/guide.md"}
    assert skipped == ["src/app.py"]


def test_filter_empty_files() -> None:
    passed, skipped = filter_by_whitelist([], PATTERNS)
    assert passed == []
    assert skipped == []


def test_filter_all_rejected() -> None:
    files = [_rf("src/a.py"), _rf("package.json")]
    passed, skipped = filter_by_whitelist(files, PATTERNS)
    assert passed == []
    assert len(skipped) == 2


def test_filter_all_passed() -> None:
    files = [_rf("AGENTS.md"), _rf("CLAUDE.md"), _rf("GEMINI.md")]
    passed, skipped = filter_by_whitelist(files, PATTERNS)
    assert len(passed) == 3
    assert skipped == []
