"""main (CLI) の統合テスト。"""

from __future__ import annotations

import json
from pathlib import Path

from ssot_sync_controller.main import run

# -------------------------
# テストヘルパー
# -------------------------


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _make_allowed(tmp_path: Path) -> Path:
    content = "allowed:\n  - AGENTS.md\n  - CLAUDE.md\n  - docs/**\n"
    return _write(tmp_path / "allowed-paths.yml", content)


def _make_ssot_bot_yml(tmp_path: Path, name: str = "skills/myset", ref: str = "v1.0.0") -> Path:
    content = f"version: 1\nuse:\n  - name: {name}\n    ref: {ref}\n"
    return _write(tmp_path / "ssot-bot.yml", content)


def _make_catalog_skills(tmp_path: Path, set_name: str = "myset") -> Path:
    """catalog-root ベースの skills カタログを作成する。"""
    catalog_dir = tmp_path / "catalogs" / "skills"
    sets_dir = catalog_dir / "sets"
    sets_dir.mkdir(parents=True)
    # カタログのファイル
    agents_dir = catalog_dir / "docs"
    agents_dir.mkdir(parents=True)
    _write(agents_dir / "guide.md", "# Guide")
    # set.yml
    _write(sets_dir / f"{set_name}.yml", "include:\n  - docs/**\n")
    return tmp_path / "catalogs"


# -------------------------
# 正常系テスト
# -------------------------


def test_run_basic_no_op(tmp_path: Path) -> None:
    """変更なしの場合、files が空の JSON が出力される。"""
    allowed = _make_allowed(tmp_path)
    ssot_bot = _make_ssot_bot_yml(tmp_path)
    catalogs = _make_catalog_skills(tmp_path)
    output = tmp_path / "out.json"

    ret = run(
        [
            "--ssot-bot-yml",
            str(ssot_bot),
            "--catalogs-root",
            str(catalogs),
            "--allowed-paths-config",
            str(allowed),
            "--repo",
            "owner/repo",
            "--output",
            str(output),
        ]
    )

    assert ret == 0
    data = json.loads(output.read_text())
    assert data["repo"] == "owner/repo"
    # docs/guide.md はホワイトリストに一致するため overwrite に含まれるはず
    files = data["commit"]["files"]
    paths = [f["path"] for f in files]
    assert "docs/guide.md" in paths


def test_run_with_current_state_generates_deletes(tmp_path: Path) -> None:
    """current_state に allowed ファイルがあり desired にない場合、削除される。"""
    allowed = _make_allowed(tmp_path)
    ssot_bot = _make_ssot_bot_yml(tmp_path)
    catalogs = _make_catalog_skills(tmp_path)

    current = {"AGENTS.md": "base64x", "docs/guide.md": "old"}
    current_file = tmp_path / "current.json"
    current_file.write_text(json.dumps(current), encoding="utf-8")

    output = tmp_path / "out.json"

    ret = run(
        [
            "--ssot-bot-yml",
            str(ssot_bot),
            "--catalogs-root",
            str(catalogs),
            "--allowed-paths-config",
            str(allowed),
            "--current-state",
            str(current_file),
            "--repo",
            "owner/repo",
            "--output",
            str(output),
        ]
    )

    assert ret == 0
    data = json.loads(output.read_text())
    files = data["commit"]["files"]
    delete_paths = [f["path"] for f in files if f.get("delete")]
    # AGENTS.md は desired になく allowed 範囲内 → 削除
    assert "AGENTS.md" in delete_paths


def test_run_invalid_ssot_bot_yml(tmp_path: Path) -> None:
    """ssot-bot.yml が不正な場合、非ゼロを返す。"""
    allowed = _make_allowed(tmp_path)
    bad_yml = _write(tmp_path / "ssot-bot.yml", "version: 99\nuse: []\n")

    ret = run(
        [
            "--ssot-bot-yml",
            str(bad_yml),
            "--catalogs-root",
            str(tmp_path / "catalogs"),
            "--allowed-paths-config",
            str(allowed),
            "--repo",
            "owner/repo",
        ]
    )
    assert ret == 1


def test_run_catalog_not_found(tmp_path: Path) -> None:
    """カタログディレクトリが存在しない場合、非ゼロを返す。"""
    allowed = _make_allowed(tmp_path)
    ssot_bot = _make_ssot_bot_yml(tmp_path)

    ret = run(
        [
            "--ssot-bot-yml",
            str(ssot_bot),
            "--catalogs-root",
            str(tmp_path / "nonexistent"),
            "--allowed-paths-config",
            str(allowed),
            "--repo",
            "owner/repo",
        ]
    )
    assert ret == 1


def test_run_output_json_schema(tmp_path: Path) -> None:
    """出力 JSON が必須キーを持つ。"""
    allowed = _make_allowed(tmp_path)
    ssot_bot = _make_ssot_bot_yml(tmp_path)
    catalogs = _make_catalog_skills(tmp_path)
    output = tmp_path / "out.json"

    run(
        [
            "--ssot-bot-yml",
            str(ssot_bot),
            "--catalogs-root",
            str(catalogs),
            "--allowed-paths-config",
            str(allowed),
            "--repo",
            "owner/repo",
            "--output",
            str(output),
        ]
    )

    data = json.loads(output.read_text())
    assert "repo" in data
    assert "base_branch" in data
    assert "head_branch" in data
    assert "commit" in data
    assert "pull_request" in data
    assert "files" in data["commit"]
    assert "title" in data["pull_request"]
    assert "body" in data["pull_request"]
    assert "labels" in data["pull_request"]
