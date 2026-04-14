"""差分生成（上書き・削除判定）。"""

from __future__ import annotations

import logging

from .models import DiffResult, ResolvedFile, Warning
from .path_validator import is_path_allowed

logger = logging.getLogger(__name__)


def generate_diff(
    desired_files: list[ResolvedFile],
    current_state: dict[str, str],
    allowed_patterns: list[str],
    extra_warnings: list[Warning] | None = None,
) -> DiffResult:
    """desired state と current state を比較し差分を生成する。

    Args:
        desired_files: desired state のファイルリスト（dedupe・whitelist 適用済み）。
        current_state: target repo の現在管理ファイル dict。
                       ``{target_path: base64_content}`` 形式。
                       空 dict の場合はすべて追加扱い。
        allowed_patterns: ホワイトリストパターン（削除対象の特定に使用）。
        extra_warnings: 上流から伝搬する警告リスト。

    Returns:
        DiffResult（overwrites, deletes, warnings）
    """
    result = DiffResult(warnings=list(extra_warnings) if extra_warnings else [])

    desired_paths = {f.target_path for f in desired_files}

    # 追加・上書き: desired にあるすべてのファイル
    for f in desired_files:
        result.overwrites.append(f)

    # 削除: current_state にあり、allowed 配下で、desired にないパス
    for path, _content in current_state.items():
        if path not in desired_paths and is_path_allowed(path, allowed_patterns):
            result.deletes.append(path)
            logger.debug("削除対象: %s", path)

    logger.info("差分: 上書き=%d, 削除=%d", len(result.overwrites), len(result.deletes))
    return result
