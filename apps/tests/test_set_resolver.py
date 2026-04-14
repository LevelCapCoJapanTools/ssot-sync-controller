"""set_resolver のテスト。"""

from __future__ import annotations

from pathlib import Path

import pytest

from ssot_sync_controller.models import UseEntry
from ssot_sync_controller.set_resolver import resolve_set


def _make_use(name: str, ref: str = "v1.0.0") -> UseEntry:
    return UseEntry(name=name, ref=ref)


# -------------------------
# ssot-core モード
# -------------------------


def test_resolve_set_ssot_core_mode(tmp_path: Path) -> None:
    """ssot-core モード（distribution_root）でファイルを収集する。"""
    # catalogs_root/ssot/ に ssot-core 相当のディレクトリ構造を作成
    catalog_dir = tmp_path / "ssot"
    set_dir = catalog_dir / "sets" / "react-app"
    set_dir.mkdir(parents=True)

    dist_root = catalog_dir / "react-app"
    dist_root.mkdir(parents=True)
    (dist_root / "AGENTS.md").write_text("agents content", encoding="utf-8")
    dot_github = dist_root / ".github"
    dot_github.mkdir(parents=True)
    (dot_github / "copilot-instructions.md").write_text("copilot", encoding="utf-8")

    (set_dir / "set.yml").write_text(
        "version: 1\ndistribution_root: ../../react-app\n",
        encoding="utf-8",
    )

    use = _make_use("ssot/react-app")
    files, warnings = resolve_set(use, tmp_path)

    assert warnings == []
    target_paths = {f.target_path for f in files}
    assert "AGENTS.md" in target_paths
    assert ".github/copilot-instructions.md" in target_paths


def test_resolve_set_ssot_core_missing_dist_root(tmp_path: Path) -> None:
    """distribution_root が存在しない場合は警告を返す。"""
    catalog_dir = tmp_path / "ssot"
    set_dir = catalog_dir / "sets" / "missing-set"
    set_dir.mkdir(parents=True)
    (set_dir / "set.yml").write_text(
        "version: 1\ndistribution_root: ../../nonexistent\n",
        encoding="utf-8",
    )

    use = _make_use("ssot/missing-set")
    files, warnings = resolve_set(use, tmp_path)
    assert files == []
    assert len(warnings) == 1
    assert "distribution_root" in warnings[0].message


# -------------------------
# catalog-root include モード (Skills / MCP)
# -------------------------


def test_resolve_set_catalog_root_include(tmp_path: Path) -> None:
    """catalog-root ベースの include glob が正しく展開される。"""
    catalog_dir = tmp_path / "skills"
    sets_dir = catalog_dir / "sets"
    sets_dir.mkdir(parents=True)

    # カタログ内のファイル
    agents_dir = catalog_dir / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "agent1.md").write_text("agent1", encoding="utf-8")
    (agents_dir / "agent2.md").write_text("agent2", encoding="utf-8")

    # flat set.yml
    (sets_dir / "frontend-ui.yml").write_text(
        "include:\n  - .claude/agents/**\n",
        encoding="utf-8",
    )

    use = _make_use("skills/frontend-ui")
    files, warnings = resolve_set(use, tmp_path)

    assert warnings == []
    target_paths = {f.target_path for f in files}
    assert ".claude/agents/agent1.md" in target_paths
    assert ".claude/agents/agent2.md" in target_paths


def test_resolve_set_catalog_root_include_nested_set_dir(tmp_path: Path) -> None:
    """sets/<name>/set.yml + include（catalog-root ベース）が正しく展開される。"""
    catalog_dir = tmp_path / "mcp"
    set_dir = catalog_dir / "sets" / "basic-tools"
    set_dir.mkdir(parents=True)

    mcp_dir = catalog_dir / ".claude" / "mcp"
    mcp_dir.mkdir(parents=True)
    (mcp_dir / "tool.json").write_text("{}", encoding="utf-8")

    (set_dir / "set.yml").write_text(
        "include:\n  - .claude/mcp/**\n",
        encoding="utf-8",
    )

    use = _make_use("mcp/basic-tools")
    files, warnings = resolve_set(use, tmp_path)

    assert warnings == []
    assert any(f.target_path == ".claude/mcp/tool.json" for f in files)


# -------------------------
# subdir モード (ssot-schema / ssot-policies)
# -------------------------


def test_resolve_set_subdir_include(tmp_path: Path) -> None:
    """subdir モード（set.yml からの相対 include）が正しく展開される。"""
    catalog_dir = tmp_path / "ssot-schema"
    agile_dir = catalog_dir / "agile"
    github_dir = agile_dir / ".github" / "instructions"
    github_dir.mkdir(parents=True)
    (github_dir / "rule.instructions.md").write_text("rule", encoding="utf-8")

    (agile_dir / "set.yml").write_text(
        "include:\n  - .github/instructions/**\n",
        encoding="utf-8",
    )

    use = _make_use("ssot-schema/agile")
    files, warnings = resolve_set(use, tmp_path)

    assert warnings == []
    target_paths = {f.target_path for f in files}
    assert ".github/instructions/rule.instructions.md" in target_paths


# -------------------------
# 警告系テスト
# -------------------------


def test_resolve_set_missing_include_warns(tmp_path: Path) -> None:
    """存在しない include パスは警告を返しエラーにならない。"""
    catalog_dir = tmp_path / "skills"
    sets_dir = catalog_dir / "sets"
    sets_dir.mkdir(parents=True)
    (sets_dir / "empty.yml").write_text(
        "include:\n  - nonexistent/**\n",
        encoding="utf-8",
    )

    use = _make_use("skills/empty")
    files, warnings = resolve_set(use, tmp_path)

    assert files == []
    assert len(warnings) == 1
    assert "nonexistent/**" in warnings[0].message


def test_resolve_set_empty_include(tmp_path: Path) -> None:
    """include が null の場合は no-op（空リスト）を返す。"""
    catalog_dir = tmp_path / "skills"
    sets_dir = catalog_dir / "sets"
    sets_dir.mkdir(parents=True)
    (sets_dir / "noop.yml").write_text("include:\n", encoding="utf-8")

    use = _make_use("skills/noop")
    files, warnings = resolve_set(use, tmp_path)

    assert files == []
    assert warnings == []


# -------------------------
# エラー系テスト
# -------------------------


def test_resolve_set_invalid_name_format(tmp_path: Path) -> None:
    """name が '<domain>/<set-name>' 形式でない場合 ValueError を送出する。"""
    use = _make_use("invalid-no-slash")
    with pytest.raises(ValueError, match="<domain>/<set-name>"):
        resolve_set(use, tmp_path)


def test_resolve_set_catalog_dir_not_found(tmp_path: Path) -> None:
    """カタログディレクトリが存在しない場合 FileNotFoundError を送出する。"""
    use = _make_use("nonexistent/set")
    with pytest.raises(FileNotFoundError):
        resolve_set(use, tmp_path)


def test_resolve_set_set_yml_not_found(tmp_path: Path) -> None:
    """set.yml が見つからない場合 FileNotFoundError を送出する。"""
    catalog_dir = tmp_path / "skills"
    catalog_dir.mkdir()
    use = _make_use("skills/no-set-yml")
    with pytest.raises(FileNotFoundError, match="set.yml"):
        resolve_set(use, tmp_path)
