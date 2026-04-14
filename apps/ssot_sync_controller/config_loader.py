"""ssot-bot.yml および allowed-paths.yml の読み込み。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .models import SsotBotConfig, UseEntry

logger = logging.getLogger(__name__)


def load_ssot_bot_config(path: Path) -> SsotBotConfig:
    """ssot-bot.yml を読み込み、SsotBotConfig を返す。

    Raises:
        ValueError: 必須フィールドが欠損している場合。
        FileNotFoundError: ファイルが存在しない場合。
    """
    logger.info("ssot-bot.yml を読み込みます: %s", path)

    raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"ssot-bot.yml のトップレベルが dict ではありません: {path}")

    version = raw.get("version")
    if version != 1:
        raise ValueError(
            f"ssot-bot.yml の version は 1 のみ対応しています（実際の値: {version!r}）"
        )

    use_raw = raw.get("use")
    if not isinstance(use_raw, list):
        raise ValueError("ssot-bot.yml の use フィールドはリストである必要があります")

    entries: list[UseEntry] = []
    for i, item in enumerate(use_raw):
        if not isinstance(item, dict):
            raise ValueError(f"use[{i}] が dict ではありません: {item!r}")
        name = item.get("name")
        ref = item.get("ref")
        if not isinstance(name, str) or not name:
            raise ValueError(f"use[{i}].name が無効です: {name!r}")
        if not isinstance(ref, str) or not ref:
            raise ValueError(f"use[{i}].ref が無効です: {ref!r}")
        entries.append(UseEntry(name=name, ref=ref))

    logger.info("use エントリ数: %d", len(entries))
    return SsotBotConfig(version=int(version), use=tuple(entries))


def load_allowed_paths(path: Path) -> list[str]:
    """allowed-paths.yml を読み込み、glob パターンリストを返す。

    Raises:
        ValueError: 形式が不正な場合。
        FileNotFoundError: ファイルが存在しない場合。
    """
    logger.info("allowed-paths.yml を読み込みます: %s", path)

    raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"allowed-paths.yml のトップレベルが dict ではありません: {path}")

    allowed = raw.get("allowed")
    if not isinstance(allowed, list):
        raise ValueError("allowed-paths.yml の allowed フィールドはリストである必要があります")

    patterns: list[str] = []
    for item in allowed:
        if not isinstance(item, str):
            raise ValueError(f"allowed パターンが文字列ではありません: {item!r}")
        patterns.append(item)

    logger.info("許可パターン数: %d", len(patterns))
    return patterns
