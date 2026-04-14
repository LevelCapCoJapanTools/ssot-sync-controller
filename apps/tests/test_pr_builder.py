"""pr_builder のテスト。"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from pathlib import Path

from ssot_sync_controller.models import DiffResult, ResolvedFile, UseEntry, Warning
from ssot_sync_controller.pr_builder import (
    build_branch_name,
    build_commit_message,
    build_output_json,
    build_pr_body,
    build_pr_title,
)

_TS = datetime(2026, 4, 4, 12, 0, 1, tzinfo=UTC)
_USE1 = UseEntry(name="ssot/react-app", ref="v1.2.3")
_USE2 = UseEntry(name="skills/copilot-frontend", ref="v2.0.0")


# -------------------------
# build_branch_name
# -------------------------


def test_build_branch_name() -> None:
    assert build_branch_name(_TS) == "ssot/sync-20260404-120001"


# -------------------------
# build_commit_message
# -------------------------


def test_build_commit_message_single() -> None:
    msg = build_commit_message((_USE1,), _TS)
    assert msg == "chore(ssot): sync ssot/react-app@v1.2.3 [20260404-120001]"


def test_build_commit_message_multiple() -> None:
    msg = build_commit_message((_USE1, _USE2), _TS)
    assert "ssot/react-app@v1.2.3" in msg
    assert "+1" in msg
    assert "20260404-120001" in msg


# -------------------------
# build_pr_title
# -------------------------


def test_build_pr_title_equals_commit_message() -> None:
    assert build_pr_title((_USE1,), _TS) == build_commit_message((_USE1,), _TS)


# -------------------------
# build_pr_body
# -------------------------


def _make_diff(overwrites: int = 1, deletes: int = 1, warnings: int = 0) -> DiffResult:
    rf = ResolvedFile(target_path="AGENTS.md", absolute_source="/src/f", catalog_name="cat")
    warn = Warning(message="warn msg", catalog_name="cat")
    return DiffResult(
        overwrites=[rf] * overwrites,
        deletes=["CLAUDE.md"] * deletes,
        warnings=[warn] * warnings,
    )


def test_build_pr_body_contains_source() -> None:
    body = build_pr_body((_USE1,), _make_diff(), _TS)
    assert "ssot/react-app@v1.2.3" in body


def test_build_pr_body_contains_changes_count() -> None:
    body = build_pr_body((_USE1,), _make_diff(overwrites=3, deletes=2), _TS)
    assert "3" in body
    assert "2" in body


def test_build_pr_body_contains_warnings() -> None:
    body = build_pr_body((_USE1,), _make_diff(warnings=1), _TS)
    assert "warn msg" in body


def test_build_pr_body_auto_generated_note() -> None:
    body = build_pr_body((_USE1,), _make_diff(), _TS)
    assert "自動生成" in body


def test_build_pr_body_no_warnings_section_if_empty() -> None:
    body = build_pr_body((_USE1,), _make_diff(warnings=0), _TS)
    assert "Warnings" not in body


# -------------------------
# build_output_json
# -------------------------


def test_build_output_json_structure(tmp_path: Path) -> None:
    """出力 JSON が期待するキーを持つ。"""
    # ダミーファイルを作成
    src = tmp_path / "AGENTS.md"
    src.write_text("agents", encoding="utf-8")

    rf = ResolvedFile(
        target_path="AGENTS.md",
        absolute_source=str(src),
        catalog_name="ssot/react-app",
    )
    diff = DiffResult(
        overwrites=[rf],
        deletes=["CLAUDE.md"],
        warnings=[],
    )

    result = build_output_json(
        repo="owner/repo",
        base_branch="main",
        use_entries=(_USE1,),
        diff=diff,
        ts=_TS,
    )

    assert result["repo"] == "owner/repo"
    assert result["base_branch"] == "main"
    assert result["head_branch"] == "ssot/sync-20260404-120001"

    files = result["commit"]["files"]
    overwrite_entry = next(f for f in files if f.get("path") == "AGENTS.md")
    assert "content" in overwrite_entry
    assert overwrite_entry["mode"] == "100644"
    # BASE64 デコードが元ファイルと一致する
    assert base64.b64decode(overwrite_entry["content"]) == b"agents"

    delete_entry = next(f for f in files if f.get("path") == "CLAUDE.md")
    assert delete_entry.get("delete") is True

    pr = result["pull_request"]
    assert "ssot" in pr["labels"]
    assert "auto-generated" in pr["labels"]


def test_build_output_json_no_files_when_no_diff(tmp_path: Path) -> None:
    """diff が空の場合 files も空。"""
    diff = DiffResult(overwrites=[], deletes=[], warnings=[])
    result = build_output_json(
        repo="owner/repo",
        base_branch="main",
        use_entries=(_USE1,),
        diff=diff,
        ts=_TS,
    )
    assert result["commit"]["files"] == []
