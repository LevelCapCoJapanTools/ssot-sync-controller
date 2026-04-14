"""deduper のテスト。"""

from __future__ import annotations

from ssot_sync_controller.deduper import dedupe
from ssot_sync_controller.models import ResolvedFile


def _rf(target: str, source: str = "/src/a", catalog: str = "cat") -> ResolvedFile:
    return ResolvedFile(target_path=target, absolute_source=source, catalog_name=catalog)


def test_dedupe_no_duplicates() -> None:
    """重複なしの場合はそのまま返す。"""
    files = [_rf("a.md"), _rf("b.md"), _rf("c.md")]
    result = dedupe(files)
    assert [f.target_path for f in result] == ["a.md", "b.md", "c.md"]


def test_dedupe_later_wins() -> None:
    """同一パスは後勝ち（後のエントリが残る）。"""
    f1 = ResolvedFile(target_path="AGENTS.md", absolute_source="/a", catalog_name="cat1")
    f2 = ResolvedFile(target_path="AGENTS.md", absolute_source="/b", catalog_name="cat2")
    result = dedupe([f1, f2])
    assert len(result) == 1
    assert result[0].catalog_name == "cat2"
    assert result[0].absolute_source == "/b"


def test_dedupe_preserves_unique_order() -> None:
    """ユニークなパスの出現順序は維持される。"""
    files = [_rf("z.md"), _rf("a.md"), _rf("m.md")]
    result = dedupe(files)
    assert [f.target_path for f in result] == ["z.md", "a.md", "m.md"]


def test_dedupe_multiple_duplicates() -> None:
    """3 回以上重複する場合も最後の 1 つだけ残る。"""
    files = [
        ResolvedFile(target_path="x.md", absolute_source="/1", catalog_name="c1"),
        ResolvedFile(target_path="x.md", absolute_source="/2", catalog_name="c2"),
        ResolvedFile(target_path="x.md", absolute_source="/3", catalog_name="c3"),
    ]
    result = dedupe(files)
    assert len(result) == 1
    assert result[0].absolute_source == "/3"


def test_dedupe_empty_input() -> None:
    """空リストは空リストを返す。"""
    assert dedupe([]) == []


def test_dedupe_mixed() -> None:
    """重複あり・なし混在のケース。"""
    files = [
        _rf("a.md", "/1", "c1"),
        _rf("b.md", "/2", "c2"),
        _rf("a.md", "/3", "c3"),
        _rf("c.md", "/4", "c4"),
    ]
    result = dedupe(files)
    paths = [f.target_path for f in result]
    assert "a.md" in paths
    assert "b.md" in paths
    assert "c.md" in paths
    assert len(result) == 3
    # a.md は後勝ちで c3
    a_file = next(f for f in result if f.target_path == "a.md")
    assert a_file.catalog_name == "c3"
