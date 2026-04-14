"""BASE64 シリアライズ。"""

from __future__ import annotations

import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def encode_file(absolute_path: str) -> str:
    """ファイルを読み込んで BASE64 エンコードした文字列を返す。

    Args:
        absolute_path: ファイルの絶対パス。

    Returns:
        BASE64 エンコード済み文字列（ASCII）。

    Raises:
        FileNotFoundError: ファイルが存在しない場合。
        OSError: 読み込みエラー。
    """
    content = Path(absolute_path).read_bytes()
    encoded = base64.b64encode(content).decode("ascii")
    logger.debug("BASE64 エンコード: %s (%d bytes)", absolute_path, len(content))
    return encoded


def encode_bytes(data: bytes) -> str:
    """バイト列を BASE64 エンコードした文字列を返す。"""
    return base64.b64encode(data).decode("ascii")


def decode_base64(encoded: str) -> bytes:
    """BASE64 文字列をデコードしてバイト列を返す。"""
    return base64.b64decode(encoded)
