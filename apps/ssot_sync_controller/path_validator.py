"""ホワイトリスト（allowed-paths）によるパス検証。"""

from __future__ import annotations

import fnmatch
import logging

from .models import ResolvedFile

logger = logging.getLogger(__name__)


def is_path_allowed(path: str, allowed_patterns: list[str]) -> bool:
    """path がいずれかの allowed パターンに一致するか判定する。

    Args:
        path: 検査対象の相対パス（先頭 / なし）。
        allowed_patterns: glob パターンリスト（fnmatch 形式）。

    Returns:
        True: 少なくとも 1 パターンに一致する。
    """
    for pattern in allowed_patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def filter_by_whitelist(
    files: list[ResolvedFile], allowed_patterns: list[str]
) -> tuple[list[ResolvedFile], list[str]]:
    """ホワイトリストに一致するファイルのみを通過させる。

    Args:
        files: 入力ファイルリスト。
        allowed_patterns: allowed-paths.yml から取得したパターンリスト。

    Returns:
        (通過したファイルリスト, スキップされたパスリスト)
    """
    passed: list[ResolvedFile] = []
    skipped: list[str] = []

    for f in files:
        if is_path_allowed(f.target_path, allowed_patterns):
            passed.append(f)
        else:
            logger.warning(
                "ホワイトリスト外のパスをスキップ: %s (%s)",
                f.target_path,
                f.catalog_name,
            )
            skipped.append(f.target_path)

    logger.info(
        "ホワイトリストフィルタ: %d → %d ファイル（スキップ: %d）",
        len(files),
        len(passed),
        len(skipped),
    )
    return passed, skipped
