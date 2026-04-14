"""serializer のテスト。"""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from ssot_sync_controller.serializer import decode_base64, encode_bytes, encode_file


def test_encode_bytes_roundtrip() -> None:
    """encode_bytes でエンコードした内容が decode_base64 で復元できる。"""
    data = b"Hello, SSOT world!"
    encoded = encode_bytes(data)
    assert decode_base64(encoded) == data


def test_encode_bytes_empty() -> None:
    """空バイト列をエンコードできる。"""
    encoded = encode_bytes(b"")
    assert encoded == ""


def test_encode_file(tmp_path: Path) -> None:
    """ファイルを正しく BASE64 エンコードする。"""
    content = b"file content here"
    f = tmp_path / "test.md"
    f.write_bytes(content)

    encoded = encode_file(str(f))
    assert base64.b64decode(encoded) == content


def test_encode_file_not_found(tmp_path: Path) -> None:
    """存在しないファイルは FileNotFoundError を送出する。"""
    with pytest.raises(FileNotFoundError):
        encode_file(str(tmp_path / "nonexistent.md"))


def test_encode_bytes_ascii_safe() -> None:
    """エンコード結果は ASCII 文字列のみで構成される。"""
    encoded = encode_bytes("日本語コンテンツ".encode())
    assert encoded.isascii()


def test_encode_file_binary_content(tmp_path: Path) -> None:
    """バイナリファイルもエンコードできる。"""
    data = bytes(range(256))
    f = tmp_path / "binary.bin"
    f.write_bytes(data)
    encoded = encode_file(str(f))
    assert decode_base64(encoded) == data
