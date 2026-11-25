"""集計結果をA4縦の複数ページPDFとして出力する。"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Union

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/meiryo.ttc"),
    Path("C:/Windows/Fonts/YuGothM.ttc"),
    Path("C:/Windows/Fonts/msgothic.ttc"),
]
FONT_NAME = "SlipJapanese"


def _register_japanese_font(font_path: Union[str, Path, None] = None) -> str:
    candidates = [Path(font_path)] if font_path else FONT_CANDIDATES
    for candidate in candidates:
        if candidate.is_file():
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME, str(candidate), subfontIndex=0))
                return FONT_NAME
            except Exception:
                continue
    # ReportLab標準の日本語CIDフォント。外部フォントファイル不要。
    cid_name = "HeiseiKakuGo-W5"
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(cid_name))
    except Exception:
        pass
    return cid_name


def _format_date(value: Union[str, date, datetime, None]) -> str:
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y/%m/%d")
    text = str(value)
    try:
        if len(text) == 8 and text.isdigit():
            return datetime.strptime(text, "%Y%m%d").strftime("%Y/%m/%d")
        return datetime.strptime(text.replace("-", "/"), "%Y/%m/%d").strftime("%Y/%m/%d")
    except ValueError:
        return text


def _paginate(rows: list[dict[str, object]], rows_per_page: int) -> list[list[dict[str, object]]]:
    if rows_per_page < 2:
        raise ValueError("rows_per_pageは2以上を指定してください。")
    totals = [row for row in rows if row.get("区分") == "総合計"]
    body = [row for row in rows if row.get("区分") != "総合計"]
    pages = [body[i:i + rows_per_page] for i in range(0, len(body), rows_per_page)]
    if not pages:
        pages = [[]]
    if len(pages[-1]) >= rows_per_page:
        pages.append([])
    pages[-1].extend(totals[:1])
    return pages


def export_summary_pdf(
    summary: pd.DataFrame,
    output_dir: Union[str, Path],
    start_date: Union[str, date, datetime, None] = None,
    end_date: Union[str, date, datetime, None] = None,
    login_id: str = "IR-301",
    filename: str = "伝票枚数集計",
    rows_per_page: int = 30,
    font_path: Union[str, Path, None] = None,
) -> Path:
    """集計結果をA4縦PDFに出力し、生成したPDFのパスを返す。"""
    required = {"区分", "担当者ｺｰﾄﾞ", "仕入先名略称", "行数"}
    missing = required.difference(summary.columns)
    if missing:
        raise ValueError("集計結果に必要な列がありません: " + ", ".join(sorted(missing)))

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    output_file = directory / f"{filename}.pdf"
    pages = _paginate(summary.to_dict("records"), rows_per_page)
    font_name = _register_japanese_font(font_path)

    page_width, page_height = A4
    left = 42
    right = page_width - 42
    row_height = 20
    header_y = page_height - 125
    table_top = page_height - 165

    pdf = canvas.Canvas(str(output_file), pagesize=A4)
    pdf.setTitle("伝票枚数集計表")
    pdf.setAuthor("伝票枚数カウント")

    for page_no, page_rows in enumerate(pages, start=1):
        pdf.setFont(font_name, 18)
        pdf.drawString(left, page_height - 48, "伝票枚数集計表")
        pdf.setFont(font_name, 9)
        pdf.drawString(left, page_height - 72, f"対象期間：{_format_date(start_date)} ～ {_format_date(end_date)}")
        pdf.drawString(left, page_height - 89, f"ログインID：{login_id}")
        pdf.drawRightString(right, page_height - 89, f"{page_no} / {len(pages)} ページ")

        pdf.setFillColor(colors.HexColor("#E8EDF2"))
        pdf.rect(left, table_top - 5, right - left, 25, fill=1, stroke=0)
        pdf.setFillColor(colors.black)
        pdf.setFont(font_name, 10)
        pdf.drawString(left + 10, table_top + 3, "担当者コード / 仕入先")
        pdf.drawRightString(right - 12, table_top + 3, "合計行数")

        y = table_top - 25
        for row in page_rows:
            kind = row.get("区分")
            if kind == "担当者":
                label = f"担当者　{row.get('担当者ｺｰﾄﾞ', '')}"
                pdf.setFillColor(colors.HexColor("#F1F4F7"))
                pdf.setFont(font_name, 10)
                indent = 10
            elif kind == "仕入先":
                label = f"　└ {row.get('仕入先名略称', '')}"
                pdf.setFillColor(colors.white)
                pdf.setFont(font_name, 9)
                indent = 25
            else:
                label = "総合計"
                pdf.setFillColor(colors.HexColor("#E2E8EE"))
                pdf.setFont(font_name, 10)
                indent = 10

            pdf.rect(left, y - 4, right - left, row_height, fill=1, stroke=0)
            pdf.setStrokeColor(colors.HexColor("#C8CDD2"))
            pdf.line(left, y - 4, right, y - 4)
            pdf.setFillColor(colors.black)
            pdf.drawString(left + indent, y + 2, label)
            pdf.drawRightString(right - 12, y + 2, f"{int(row.get('行数', 0)):,}")
            y -= row_height

        pdf.setFont(font_name, 8)
        pdf.setFillColor(colors.HexColor("#777777"))
        pdf.drawRightString(right, 25, f"伝票枚数集計表　{page_no} / {len(pages)}")
        pdf.showPage()

    pdf.save()
    return output_file
