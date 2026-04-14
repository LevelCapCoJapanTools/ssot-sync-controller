"""重複排除（後勝ちルール）。"""

from __future__ import annotations

import logging

from .models import ResolvedFile

logger = logging.getLogger(__name__)


def dedupe(files: list[ResolvedFile]) -> list[ResolvedFile]:
    """同一 target_path のファイルを後勝ちルールで排除する。

    入力リストの順序を維持しつつ、同一パスが複数ある場合は
    最後に現れたものを採用する。

    Args:
        files: 入力ファイルリスト（上から順に評価されることを前提とする）。

    Returns:
        重複を排除したファイルリスト（後勝ち適用後の最終状態、
        「最後に来た順」で並ぶ）。
    """
    seen: dict[str, ResolvedFile] = {}
    for f in files:
        if f.target_path in seen:
            logger.debug(
                "パス重複: %s  前=%s  後=%s（後勝ち）",
                f.target_path,
                seen[f.target_path].catalog_name,
                f.catalog_name,
            )
        seen[f.target_path] = f

    result = list(seen.values())
    logger.info("dedupe: %d → %d ファイル", len(files), len(result))
    return result
