"""diff_generator のテスト。"""

from __future__ import annotations

from ssot_sync_controller.diff_generator import generate_diff
from ssot_sync_controller.models import ResolvedFile, Warning

ALLOWED = ["docs/**", "AGENTS.md", "CLAUDE.md", ".github/copilot/**"]


def _rf(target: str, source: str = "/src/f", catalog: str = "cat") -> ResolvedFile:
    return ResolvedFile(target_path=target, absolute_source=source, catalog_name=catalog)


# -------------------------
# 基本動作
# -------------------------


def test_diff_all_new_files() -> None:
    """current_state が空の場合、すべて overwrite。"""
    desired = [_rf("AGENTS.md"), _rf("docs/guide.md")]
    result = generate_diff(desired, {}, ALLOWED)
    assert len(result.overwrites) == 2
    assert result.deletes == []
    assert result.warnings == []


def test_diff_no_change() -> None:
    """desired と current_state が同一の場合、overwrites は desired ファイル全件、deletes は空。"""
    desired = [_rf("AGENTS.md"), _rf("CLAUDE.md")]
    current = {"AGENTS.md": "base64a", "CLAUDE.md": "base64b"}
    result = generate_diff(desired, current, ALLOWED)
    # 上書き: desired の全ファイル
    assert len(result.overwrites) == 2
    assert result.deletes == []


def test_diff_delete_removed_file() -> None:
    """current にあり desired にないファイルは削除対象になる（allowed 範囲内）。"""
    desired = [_rf("AGENTS.md")]
    current = {"AGENTS.md": "base64a", "CLAUDE.md": "base64b"}
    result = generate_diff(desired, current, ALLOWED)
    assert "CLAUDE.md" in result.deletes


def test_diff_no_delete_outside_allowed() -> None:
    """allowed 外のパスは削除対象にならない。"""
    desired = [_rf("AGENTS.md")]
    current = {"AGENTS.md": "base64a", "src/app.py": "base64x"}
    result = generate_diff(desired, current, ALLOWED)
    assert "src/app.py" not in result.deletes


def test_diff_empty_desired_deletes_all_managed() -> None:
    """desired が空で current に管理ファイルがある場合、allowed 範囲内を削除。"""
    desired: list[ResolvedFile] = []
    current = {"AGENTS.md": "base64a", "CLAUDE.md": "base64b", "src/app.py": "base64x"}
    result = generate_diff(desired, current, ALLOWED)
    assert "AGENTS.md" in result.deletes
    assert "CLAUDE.md" in result.deletes
    assert "src/app.py" not in result.deletes


def test_diff_warnings_propagated() -> None:
    """extra_warnings が DiffResult に含まれる。"""
    warn = Warning(message="テスト警告", catalog_name="cat")
    result = generate_diff([], {}, ALLOWED, extra_warnings=[warn])
    assert len(result.warnings) == 1
    assert result.warnings[0].message == "テスト警告"


def test_diff_add_and_delete() -> None:
    """追加・削除が混在するケース。"""
    desired = [_rf("AGENTS.md"), _rf("docs/new.md")]
    current = {"AGENTS.md": "base64a", "CLAUDE.md": "base64b"}
    result = generate_diff(desired, current, ALLOWED)
    assert len(result.overwrites) == 2
    assert "CLAUDE.md" in result.deletes
    assert "AGENTS.md" not in result.deletes
