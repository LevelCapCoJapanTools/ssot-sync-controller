"""テスト共通フィクスチャ。"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """一時ディレクトリ（pytest の tmp_path をそのまま使用）。"""
    return tmp_path
