"""データモデル定義。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UseEntry:
    """ssot-bot.yml の use リスト 1 要素。"""

    name: str
    ref: str


@dataclass(frozen=True)
class SsotBotConfig:
    """ssot-bot.yml 全体。"""

    version: int
    use: tuple[UseEntry, ...]


@dataclass(frozen=True)
class ResolvedFile:
    """カタログから解決された 1 ファイル。"""

    target_path: str
    """target repo 上の相対パス（先頭 / なし）。"""

    absolute_source: str
    """ローカルファイルシステム上の絶対パス。"""

    catalog_name: str
    """元の use.name（警告メッセージなどで使用）。"""


@dataclass(frozen=True)
class Warning:
    """処理中に発生した警告。"""

    message: str
    catalog_name: str


@dataclass
class DesiredState:
    """dedupe・ホワイトリスト適用後の最終状態。"""

    files: list[ResolvedFile] = field(default_factory=list)
    warnings: list[Warning] = field(default_factory=list)


@dataclass
class DiffResult:
    """差分計算結果。"""

    overwrites: list[ResolvedFile] = field(default_factory=list)
    """追加・上書き対象ファイル。"""

    deletes: list[str] = field(default_factory=list)
    """削除対象パス。"""

    warnings: list[Warning] = field(default_factory=list)
