"""ssot-sync-controller CLI エントリポイント。

処理フロー:
    1. ssot-bot.yml 読込
    2. カタログ checkout (ローカルディレクトリからの読取)
    3. set 定義読込
    4. include 展開（glob のみ）
    5. dedupe
    6. ホワイトリストフィルタ
    7. desired state 生成
    8. 差分計算
    9. PR 用データ生成
   10. BASE64 変換（pr_builder 内で実行）
   11. ssot-bot へ渡す JSON を出力
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

from .config_loader import load_allowed_paths, load_ssot_bot_config
from .deduper import dedupe
from .diff_generator import generate_diff
from .models import Warning
from .path_validator import filter_by_whitelist
from .pr_builder import build_output_json
from .set_resolver import resolve_set

logger = logging.getLogger(__name__)


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        stream=sys.stderr,
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ssot-sync-controller",
        description="SSOT 同期制御層 — desired state を生成し ssot-bot 向け JSON を出力する",
    )
    parser.add_argument(
        "--ssot-bot-yml",
        required=True,
        type=Path,
        help="ssot-bot.yml のパス",
    )
    parser.add_argument(
        "--catalogs-root",
        required=True,
        type=Path,
        help=(
            "カタログが checkout されているルートディレクトリ。"
            "use.name（例: ssot/react-app）をパスとして結合したディレクトリに"
            "カタログが存在することを期待する。"
        ),
    )
    parser.add_argument(
        "--allowed-paths-config",
        type=Path,
        default=None,
        help="allowed-paths.yml のパス（省略時はデフォルト config/allowed-paths.yml を使用）",
    )
    parser.add_argument(
        "--current-state",
        type=Path,
        default=None,
        help=(
            "target repo の現在の管理ファイル状態を表す JSON ファイル。"
            '形式: {"path": "base64_content", ...}。'
            "省略時は空（初回実行）として扱う。"
        ),
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="target リポジトリ（例: owner/repo-name）",
    )
    parser.add_argument(
        "--base-branch",
        default="main",
        help="ベースブランチ名（デフォルト: main）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="出力先ファイルパス（省略時は標準出力）",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="DEBUG レベルのログを出力する",
    )
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    """メイン処理。返り値は終了コード（0: 正常, 1: エラー）。"""
    args = _parse_args(argv)
    _setup_logging(args.verbose)

    logger.info("ssot-sync-controller 開始")

    # --- 1. ssot-bot.yml 読込 ---
    try:
        config = load_ssot_bot_config(args.ssot_bot_yml)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("ssot-bot.yml の読込に失敗しました: %s", exc)
        return 1

    # --- allowed-paths.yml 読込 ---
    allowed_paths_file = args.allowed_paths_config
    if allowed_paths_file is None:
        # デフォルト: このスクリプトの位置から 3 階層上の config/allowed-paths.yml
        allowed_paths_file = Path(__file__).parent.parent.parent / "config" / "allowed-paths.yml"
    try:
        allowed_patterns = load_allowed_paths(allowed_paths_file)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("allowed-paths.yml の読込に失敗しました: %s", exc)
        return 1

    # --- current-state 読込 ---
    current_state: dict[str, str] = {}
    if args.current_state is not None:
        try:
            raw = json.loads(args.current_state.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                logger.error("current-state.json のトップレベルが dict ではありません")
                return 1
            current_state = {str(k): str(v) for k, v in raw.items()}
        except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
            logger.error("current-state の読込に失敗しました: %s", exc)
            return 1

    # --- 2-4. カタログ読込・set 解決・include 展開 ---
    all_files = []
    all_warnings: list[Warning] = []
    error_occurred = False

    for use in config.use:
        logger.info("カタログ解決: %s@%s", use.name, use.ref)
        try:
            files, warnings = resolve_set(use, args.catalogs_root)
        except (FileNotFoundError, ValueError) as exc:
            logger.error("set 解決に失敗しました (%s): %s", use.name, exc)
            error_occurred = True
            continue
        all_files.extend(files)
        all_warnings.extend(warnings)

    if error_occurred:
        return 1

    # --- 5. dedupe ---
    deduped = dedupe(all_files)

    # --- 6. ホワイトリストフィルタ ---
    whitelisted, skipped_paths = filter_by_whitelist(deduped, allowed_patterns)
    if skipped_paths:
        for p in skipped_paths:
            all_warnings.append(
                Warning(
                    message=f"ホワイトリスト外のパスはスキップされました: {p}",
                    catalog_name="(path_validator)",
                )
            )

    # --- 7. desired state = whitelisted files ---
    logger.info("desired state: %d ファイル", len(whitelisted))

    if not whitelisted and not current_state:
        logger.info("変更なし（空セット・no-op）")
        output = {
            "repo": args.repo,
            "base_branch": args.base_branch,
            "head_branch": "",
            "commit": {"message": "", "files": []},
            "pull_request": {"title": "", "body": "", "labels": []},
        }
        _write_output(output, args.output)
        return 0

    # --- 8. 差分計算 ---
    ts = datetime.now(tz=UTC)
    diff = generate_diff(whitelisted, current_state, allowed_patterns, all_warnings)

    if not diff.overwrites and not diff.deletes:
        logger.info("差分なし（no-op）")
        output = {
            "repo": args.repo,
            "base_branch": args.base_branch,
            "head_branch": "",
            "commit": {"message": "", "files": []},
            "pull_request": {"title": "", "body": "", "labels": []},
        }
        _write_output(output, args.output)
        return 0

    # --- 9-11. PR データ生成・BASE64 変換・JSON 出力 ---
    output = build_output_json(
        repo=args.repo,
        base_branch=args.base_branch,
        use_entries=config.use,
        diff=diff,
        ts=ts,
    )

    _write_output(output, args.output)
    logger.info("ssot-sync-controller 完了")
    return 0


def _write_output(data: dict, output_path: Path | None) -> None:  # type: ignore[type-arg]
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if output_path is None:
        sys.stdout.write(text + "\n")
    else:
        output_path.write_text(text, encoding="utf-8")
        logger.info("JSON を出力しました: %s", output_path)


def main() -> None:
    """console_scripts エントリポイント。"""
    sys.exit(run())


if __name__ == "__main__":
    main()
