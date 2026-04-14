"""set.yml の読み込みと include/glob 展開。

サポートする set.yml 配置パターン:
  1. ssot-core モード:
       <catalog_dir>/sets/<set_name>/set.yml  +  distribution_root キー
       → distribution_root ディレクトリ配下を再帰的に収集

  2. catalog-root ベース include モード (Skills / MCP):
       <catalog_dir>/sets/<set_name>/set.yml  +  include キー
       <catalog_dir>/sets/<set_name>.yml      +  include キー
       → include glob を catalog_dir 基準で展開

  3. subdir ベース include モード (ssot-schema / ssot-policies):
       <catalog_dir>/<set_name>/set.yml  +  include キー
       → include glob を set.yml ディレクトリ基準で展開
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .models import ResolvedFile, UseEntry, Warning

logger = logging.getLogger(__name__)

# ----------------------------------------
# 内部ヘルパー
# ----------------------------------------

_SetMode = str  # "ssot-core" | "catalog-root" | "subdir"


def _find_set_yml(catalog_dir: Path, set_name: str) -> tuple[Path, _SetMode]:
    """set.yml を探して (path, mode) を返す。

    Raises:
        FileNotFoundError: set.yml が見つからない場合。
    """
    # 候補 1: sets/<set_name>/set.yml
    c1 = catalog_dir / "sets" / set_name / "set.yml"
    if c1.is_file():
        raw: Any = yaml.safe_load(c1.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "distribution_root" in raw:
            return c1, "ssot-core"
        return c1, "catalog-root"

    # 候補 2: sets/<set_name>.yml (フラット)
    c2 = catalog_dir / "sets" / f"{set_name}.yml"
    if c2.is_file():
        return c2, "catalog-root"

    # 候補 3: <set_name>/set.yml (ssot-schema / ssot-policies)
    c3 = catalog_dir / set_name / "set.yml"
    if c3.is_file():
        return c3, "subdir"

    raise FileNotFoundError(
        f"set.yml が見つかりません: catalog_dir={catalog_dir}, set_name={set_name}"
    )


def _validate_target_path(path: str, catalog_name: str) -> bool:
    """target path のセキュリティ検証（ path traversal 防止）。"""
    if path.startswith("/"):
        logger.warning("先頭 '/' のパスはスキップします: %s (%s)", path, catalog_name)
        return False
    if ".." in Path(path).parts:
        logger.warning("'..' を含むパスはスキップします: %s (%s)", path, catalog_name)
        return False
    return True


def _collect_from_distribution_root(
    distribution_root: Path,
    catalog_name: str,
) -> tuple[list[ResolvedFile], list[Warning]]:
    """ssot-core モード: distribution_root 配下を再帰収集する。"""
    files: list[ResolvedFile] = []
    warnings: list[Warning] = []

    if not distribution_root.is_dir():
        msg = f"distribution_root が存在しません: {distribution_root}"
        logger.warning("%s (%s)", msg, catalog_name)
        warnings.append(Warning(message=msg, catalog_name=catalog_name))
        return files, warnings

    for fpath in sorted(distribution_root.rglob("*")):
        if not fpath.is_file():
            continue
        # distribution_root からの相対パスを target path にする
        rel = fpath.relative_to(distribution_root).as_posix()
        if not _validate_target_path(rel, catalog_name):
            continue
        files.append(
            ResolvedFile(
                target_path=rel,
                absolute_source=str(fpath),
                catalog_name=catalog_name,
            )
        )

    logger.debug("ssot-core: %d ファイルを収集 (%s)", len(files), catalog_name)
    return files, warnings


def _normalize_glob_pattern(pattern: str) -> str:
    """Python 3.12+ の glob 挙動に合わせてパターンを正規化する。

    Python 3.12 以降、``**`` 終端パターンはディレクトリのみを返す。
    ``foo/**`` は ``foo/**/*`` に変換してファイルも対象にする。
    """
    # "**" 単体または末尾が "/**" の場合、"/*" を補完する
    if pattern == "**":
        return "**/*"
    if pattern.endswith("/**"):
        return pattern + "/*"
    return pattern


def _expand_includes(
    include_patterns: list[str],
    base_dir: Path,
    catalog_name: str,
) -> tuple[list[ResolvedFile], list[Warning]]:
    """include glob を base_dir 基準で展開する。"""
    files: list[ResolvedFile] = []
    warnings: list[Warning] = []

    for pattern in include_patterns:
        effective = _normalize_glob_pattern(pattern)
        matched: list[Path] = sorted(p for p in base_dir.glob(effective) if p.is_file())
        if not matched:
            msg = f"include パターンにマッチするファイルがありません: {pattern}"
            logger.warning("%s (%s)", msg, catalog_name)
            warnings.append(Warning(message=msg, catalog_name=catalog_name))
            continue

        for fpath in matched:
            rel = fpath.relative_to(base_dir).as_posix()
            if not _validate_target_path(rel, catalog_name):
                continue
            files.append(
                ResolvedFile(
                    target_path=rel,
                    absolute_source=str(fpath),
                    catalog_name=catalog_name,
                )
            )

    logger.debug("include 展開: %d ファイル収集 (%s)", len(files), catalog_name)
    return files, warnings


# ----------------------------------------
# 公開 API
# ----------------------------------------


def resolve_set(
    use: UseEntry,
    catalogs_root: Path,
) -> tuple[list[ResolvedFile], list[Warning]]:
    """use エントリ 1 件を解決し、(ファイルリスト, 警告リスト) を返す。

    Args:
        use: ssot-bot.yml の use エントリ。
        catalogs_root: カタログが checkout されているルートディレクトリ。
                       ``use.name`` （例: ``ssot/react-app``）をパスとして
                       結合したディレクトリにカタログが存在することを期待する。

    Raises:
        FileNotFoundError: カタログディレクトリまたは set.yml が見つからない場合。
        ValueError: set.yml の内容が不正な場合。
    """
    catalog_name = use.name
    # name を path として catalog_dir を決定 (例: "ssot/react-app" → catalogs_root/ssot/react-app/)
    # set_name は name の最後のパス要素
    name_parts = use.name.split("/")
    if len(name_parts) < 2:
        raise ValueError(
            f"use.name は '<domain>/<set-name>' の形式である必要があります: {use.name!r}"
        )

    # catalog_dir = catalogs_root / domain
    # set_name = name の最後の要素
    domain = name_parts[0]
    set_name = name_parts[-1]
    catalog_dir = catalogs_root / domain

    if not catalog_dir.is_dir():
        raise FileNotFoundError(
            f"カタログディレクトリが存在しません: {catalog_dir} (use.name={use.name!r})"
        )

    logger.info(
        "set を解決します: name=%s, ref=%s, catalog_dir=%s",
        catalog_name,
        use.ref,
        catalog_dir,
    )

    set_yml_path, mode = _find_set_yml(catalog_dir, set_name)
    logger.debug("set.yml 発見: %s (mode=%s)", set_yml_path, mode)

    raw: Any = yaml.safe_load(set_yml_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"set.yml のトップレベルが dict ではありません: {set_yml_path}")

    if mode == "ssot-core":
        dist_root_str = raw.get("distribution_root")
        if not isinstance(dist_root_str, str):
            raise ValueError(f"distribution_root が文字列ではありません: {dist_root_str!r}")
        distribution_root = (set_yml_path.parent / dist_root_str).resolve()
        return _collect_from_distribution_root(distribution_root, catalog_name)

    # include モード (catalog-root / subdir)
    includes = raw.get("include")
    if includes is None:
        # 空セットは no-op
        logger.info("include が空です (no-op): %s", catalog_name)
        return [], []
    if not isinstance(includes, list):
        raise ValueError(f"set.yml の include はリストである必要があります: {set_yml_path}")

    if mode == "catalog-root":
        base_dir = catalog_dir
    else:  # subdir
        base_dir = set_yml_path.parent

    return _expand_includes([str(p) for p in includes], base_dir, catalog_name)
