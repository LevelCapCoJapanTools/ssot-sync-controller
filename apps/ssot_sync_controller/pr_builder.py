"""PR / ブランチ / コミット情報の構築と出力 JSON 生成。"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from .models import DiffResult, UseEntry
from .serializer import encode_file

logger = logging.getLogger(__name__)

_LABELS = ["ssot", "auto-generated"]


def _timestamp_str(ts: datetime) -> str:
    """YYYYMMDD-HHMMSS 形式文字列を返す（UTC）。"""
    utc = ts.astimezone(UTC)
    return utc.strftime("%Y%m%d-%H%M%S")


def build_branch_name(ts: datetime) -> str:
    """``ssot/sync-YYYYMMDD-HHMMSS`` 形式のブランチ名を返す。"""
    return f"ssot/sync-{_timestamp_str(ts)}"


def _source_summary(use_entries: tuple[UseEntry, ...]) -> str:
    """use エントリの一覧を 1 行テキストにまとめる。"""
    return ", ".join(f"{e.name}@{e.ref}" for e in use_entries)


def build_commit_message(use_entries: tuple[UseEntry, ...], ts: datetime) -> str:
    """コミットメッセージを返す。

    単一エントリの場合は ``chore(ssot): sync <name>@<ref> [YYYYMMDD-HHMMSS]``、
    複数エントリの場合は最初のエントリをメインに置く。
    """
    ts_str = _timestamp_str(ts)
    if len(use_entries) == 1:
        e = use_entries[0]
        return f"chore(ssot): sync {e.name}@{e.ref} [{ts_str}]"
    first = use_entries[0]
    return f"chore(ssot): sync {first.name}@{first.ref} +{len(use_entries) - 1} [{ts_str}]"


def build_pr_title(use_entries: tuple[UseEntry, ...], ts: datetime) -> str:
    """PR タイトルを返す。コミットメッセージと同一形式。"""
    return build_commit_message(use_entries, ts)


def build_pr_body(
    use_entries: tuple[UseEntry, ...],
    diff: DiffResult,
    ts: datetime,
) -> str:
    """PR 本文を生成する。

    含む情報:
    - Source（利用セット + version）
    - Changes（更新件数 / 削除件数）
    - Diff Summary（対象パス）
    - Warnings（存在しない include 等）
    - 自動生成である旨
    """
    ts_str = _timestamp_str(ts)
    lines: list[str] = [
        "<!-- このPRはssot-sync-controllerにより自動生成されました -->",
        "",
        "## Source",
        "",
    ]
    for e in use_entries:
        lines.append(f"- `{e.name}@{e.ref}`")

    lines += [
        "",
        "## Changes",
        "",
        f"- 追加/上書き: {len(diff.overwrites)} ファイル",
        f"- 削除: {len(diff.deletes)} ファイル",
        "",
        "## Diff Summary",
        "",
    ]
    if diff.overwrites:
        lines.append("### 追加/上書き")
        lines.append("")
        for f in sorted(diff.overwrites, key=lambda x: x.target_path):
            lines.append(f"- `{f.target_path}`")
        lines.append("")
    if diff.deletes:
        lines.append("### 削除")
        lines.append("")
        for p in sorted(diff.deletes):
            lines.append(f"- `{p}`")
        lines.append("")

    if diff.warnings:
        lines += ["## Warnings", ""]
        for w in diff.warnings:
            lines.append(f"- [{w.catalog_name}] {w.message}")
        lines.append("")

    lines += [
        "---",
        f"_自動生成 by ssot-sync-controller [{ts_str}]_",
    ]
    return "\n".join(lines)


def build_output_json(
    repo: str,
    base_branch: str,
    use_entries: tuple[UseEntry, ...],
    diff: DiffResult,
    ts: datetime,
) -> dict:  # type: ignore[type-arg]
    """ssot-bot へ渡す JSON dict を生成する。

    content フィールドは BASE64 エンコード済み。

    Args:
        repo: ``owner/repo-name`` 形式。
        base_branch: ベースブランチ名。
        use_entries: ssot-bot.yml の use エントリ群。
        diff: 差分計算結果。
        ts: 実行タイムスタンプ（UTC 推奨）。

    Returns:
        ssot-bot に渡す dict（JSON シリアライズ可能）。
    """
    head_branch = build_branch_name(ts)
    commit_message = build_commit_message(use_entries, ts)
    pr_title = build_pr_title(use_entries, ts)
    pr_body = build_pr_body(use_entries, diff, ts)

    files: list[dict] = []  # type: ignore[type-arg]

    for f in diff.overwrites:
        encoded = encode_file(f.absolute_source)
        files.append(
            {
                "path": f.target_path,
                "content": encoded,
                "mode": "100644",
            }
        )

    for path in diff.deletes:
        files.append({"path": path, "delete": True})

    return {
        "repo": repo,
        "base_branch": base_branch,
        "head_branch": head_branch,
        "commit": {
            "message": commit_message,
            "files": files,
        },
        "pull_request": {
            "title": pr_title,
            "body": pr_body,
            "labels": _LABELS,
        },
    }
