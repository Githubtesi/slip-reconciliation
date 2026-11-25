from pathlib import Path

import pandas as pd
import pytest

from app.pdf_export import export_summary_pdf


def _summary(count: int = 2) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"区分": "担当者", "担当者ｺｰﾄﾞ": "A01", "仕入先名略称": "", "行数": count},
            {"区分": "仕入先", "担当者ｺｰﾄﾞ": "A01", "仕入先名略称": "仕入先A", "行数": count},
            {"区分": "総合計", "担当者ｺｰﾄﾞ": "", "仕入先名略称": "", "行数": count},
        ]
    )


def test_export_creates_a4_pdf(tmp_path: Path) -> None:
    output = export_summary_pdf(
        _summary(), tmp_path, "2026-11-01", "2026-11-25", login_id="IR-301"
    )
    assert output.name == "伝票枚数集計.pdf"
    assert output.is_file()
    assert output.read_bytes().startswith(b"%PDF-")


def test_export_splits_into_multiple_pdf_pages(tmp_path: Path) -> None:
    rows = []
    for index in range(5):
        rows.append(
            {"区分": "担当者", "担当者ｺｰﾄﾞ": f"A{index}", "仕入先名略称": "", "行数": 1}
        )
    rows.append({"区分": "総合計", "担当者ｺｰﾄﾞ": "", "仕入先名略称": "", "行数": 5})
    output = export_summary_pdf(pd.DataFrame(rows), tmp_path, rows_per_page=2)
    content = output.read_bytes()
    assert content.startswith(b"%PDF-")
    assert content.count(b"/Type /Page") >= 3


def test_export_rejects_missing_columns(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="必要な列"):
        export_summary_pdf(pd.DataFrame([{"担当者ｺｰﾄﾞ": "A01"}]), tmp_path)
