from pathlib import Path

import pandas as pd
from PIL import ImageFont

from app.image_export import PAGE_HEIGHT, PAGE_WIDTH, export_summary_images


def _summary(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(
        rows, columns=["区分", "担当者ｺｰﾄﾞ", "仕入先名略称", "行数"]
    )


def test_export_creates_single_a4_png(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.image_export._load_font", lambda size, font_path=None: ImageFont.load_default())
    summary = _summary(
        [
            {"区分": "担当者", "担当者ｺｰﾄﾞ": "A01", "仕入先名略称": "", "行数": 2},
            {"区分": "仕入先", "担当者ｺｰﾄﾞ": "A01", "仕入先名略称": "仕入先A", "行数": 2},
            {"区分": "総合計", "担当者ｺｰﾄﾞ": "", "仕入先名略称": "", "行数": 2},
        ]
    )

    paths = export_summary_images(summary, tmp_path, "2026-11-01", "2026-11-25")

    assert len(paths) == 1
    assert paths[0].name == "伝票枚数集計.png"
    with Image.open(paths[0]) as image:
        assert image.size == (PAGE_WIDTH, PAGE_HEIGHT)
        assert image.info["dpi"] == (300.0, 300.0)


def test_export_splits_into_multiple_pages(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.image_export._load_font", lambda size, font_path=None: ImageFont.load_default())
    rows = []
    for index in range(5):
        rows.append(
            {"区分": "担当者", "担当者ｺｰﾄﾞ": f"A{index}", "仕入先名略称": "", "行数": 1}
        )
    rows.append({"区分": "総合計", "担当者ｺｰﾄﾞ": "", "仕入先名略称": "", "行数": 5})

    paths = export_summary_images(rows=_summary(rows), output_dir=tmp_path, rows_per_page=2)

    assert [path.name for path in paths] == [
        "伝票枚数集計_001.png",
        "伝票枚数集計_002.png",
        "伝票枚数集計_003.png",
    ]
    assert all(path.is_file() for path in paths)


def test_export_rejects_missing_columns(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError, match="必要な列"):
        export_summary_images(pd.DataFrame({"担当者ｺｰﾄﾞ": []}), tmp_path)
