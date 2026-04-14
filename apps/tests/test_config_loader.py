"""config_loader のテスト。"""

from __future__ import annotations

from pathlib import Path

import pytest

from ssot_sync_controller.config_loader import load_allowed_paths, load_ssot_bot_config
from ssot_sync_controller.models import UseEntry

# -------------------------
# load_ssot_bot_config
# -------------------------


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_load_ssot_bot_config_minimal(tmp_path: Path) -> None:
    """最小構成の ssot-bot.yml を正常に読み込む。"""
    f = _write(
        tmp_path,
        "ssot-bot.yml",
        "version: 1\nuse:\n  - name: ssot/react-app\n    ref: v1.2.0\n",
    )
    cfg = load_ssot_bot_config(f)
    assert cfg.version == 1
    assert len(cfg.use) == 1
    assert cfg.use[0] == UseEntry(name="ssot/react-app", ref="v1.2.0")


def test_load_ssot_bot_config_multiple_entries(tmp_path: Path) -> None:
    """複数 use エントリを正しく読み込む。"""
    content = (
        "version: 1\n"
        "use:\n"
        "  - name: ssot/react-app\n"
        "    ref: v1.2.0\n"
        "  - name: skills/copilot-frontend\n"
        "    ref: v2.0.0\n"
        "  - name: mcp/basic-tools\n"
        "    ref: v1.0.0\n"
    )
    f = _write(tmp_path, "ssot-bot.yml", content)
    cfg = load_ssot_bot_config(f)
    assert len(cfg.use) == 3
    assert cfg.use[1].name == "skills/copilot-frontend"
    assert cfg.use[2].ref == "v1.0.0"


def test_load_ssot_bot_config_invalid_version(tmp_path: Path) -> None:
    """version != 1 の場合 ValueError を送出する。"""
    f = _write(tmp_path, "ssot-bot.yml", "version: 2\nuse: []\n")
    with pytest.raises(ValueError, match="version"):
        load_ssot_bot_config(f)


def test_load_ssot_bot_config_missing_name(tmp_path: Path) -> None:
    """name が欠損している場合 ValueError を送出する。"""
    content = "version: 1\nuse:\n  - ref: v1.0.0\n"
    f = _write(tmp_path, "ssot-bot.yml", content)
    with pytest.raises(ValueError, match="name"):
        load_ssot_bot_config(f)


def test_load_ssot_bot_config_missing_ref(tmp_path: Path) -> None:
    """ref が欠損している場合 ValueError を送出する。"""
    content = "version: 1\nuse:\n  - name: ssot/react-app\n"
    f = _write(tmp_path, "ssot-bot.yml", content)
    with pytest.raises(ValueError, match="ref"):
        load_ssot_bot_config(f)


def test_load_ssot_bot_config_file_not_found(tmp_path: Path) -> None:
    """存在しないファイルは FileNotFoundError を送出する。"""
    with pytest.raises(FileNotFoundError):
        load_ssot_bot_config(tmp_path / "not-exist.yml")


def test_load_ssot_bot_config_empty_use(tmp_path: Path) -> None:
    """use が空リストの場合は正常（no-op）として扱う。"""
    f = _write(tmp_path, "ssot-bot.yml", "version: 1\nuse: []\n")
    cfg = load_ssot_bot_config(f)
    assert cfg.use == ()


# -------------------------
# load_allowed_paths
# -------------------------


def test_load_allowed_paths_basic(tmp_path: Path) -> None:
    """正常な allowed-paths.yml を読み込む。"""
    content = "allowed:\n  - docs/**\n  - AGENTS.md\n"
    f = _write(tmp_path, "allowed-paths.yml", content)
    patterns = load_allowed_paths(f)
    assert patterns == ["docs/**", "AGENTS.md"]


def test_load_allowed_paths_invalid_format(tmp_path: Path) -> None:
    """allowed フィールドがリストでない場合 ValueError を送出する。"""
    f = _write(tmp_path, "allowed-paths.yml", "allowed: notalist\n")
    with pytest.raises(ValueError):
        load_allowed_paths(f)


def test_load_allowed_paths_file_not_found(tmp_path: Path) -> None:
    """存在しないファイルは FileNotFoundError を送出する。"""
    with pytest.raises(FileNotFoundError):
        load_allowed_paths(tmp_path / "not-exist.yml")
