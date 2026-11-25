"""集計結果をA4縦・300dpiの複数ページPNG画像として出力する。"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Union

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


PAGE_WIDTH = 2480
PAGE_HEIGHT = 3508
DPI = (300, 300)
DEFAULT_ROWS_PER_PAGE = 36

FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/meiryo.ttc"),
    Path("C:/Windows/Fonts/YuGothM.ttc"),
    Path("C:/Windows/Fonts/msgothic.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"),
]


def _load_font(size: int, font_path: Union[str, Path, None] = None) -> ImageFont.FreeTypeFont:
    """日本語表示可能なフォントを読み込む。"""
    candidates = [Path(font_path)] if font_path else FONT_CANDIDATES
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    raise FileNotFoundError(
        "日本語フォントが見つかりません。Windowsではメイリオ等を確認するか、"
        "font_pathでフォントファイルを指定してください。"
    )


def _format_date(value: Union[str, date, datetime, None]) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y/%m/%d")
    if isinstance(value, date):
        return value.strftime("%Y/%m/%d")
    text = str(value)
    try:
        if len(text) == 8 and text.isdigit():
            return datetime.strptime(text, "%Y%m%d").strftime("%Y/%m/%d")
        return datetime.strptime(text.replace("-", "/"), "%Y/%m/%d").strftime("%Y/%m/%d")
    except ValueError:
        return text


def _paginate(rows: list[dict[str, object]], rows_per_page: int) -> list[list[dict[str, object]]]:
    """最終ページに総合計を含め、指定行数を超えないよう分割する。"""
    if rows_per_page < 2:
        raise ValueError("rows_per_pageは2以上を指定してください。")

    total_rows = [row for row in rows if row.get("区分") == "総合計"]
    body_rows = [row for row in rows if row.get("区分") != "総合計"]
    pages = [
        body_rows[index:index + rows_per_page]
        for index in range(0, len(body_rows), rows_per_page)
    ]
    if not pages:
        pages = [[]]

    # 総合計用の1行を確保。最終ページに空きがなければ新しいページにする。
    if len(pages[-1]) >= rows_per_page:
        pages.append([])
    pages[-1].extend(total_rows[:1])
    return pages


def export_summary_images(
    summary: pd.DataFrame,
    output_dir: Union[str, Path],
    start_date: Union[str, date, datetime, None] = None,
    end_date: Union[str, date, datetime, None] = None,
    login_id: str = "IR-301",
    filename: str = "伝票枚数集計",
    rows_per_page: int = DEFAULT_ROWS_PER_PAGE,
    font_path: Union[str, Path, None] = None,
) -> list[Path]:
    """集計DataFrameをA4縦・300dpiのPNGに出力し、生成ファイルパスを返す。

    summaryはaggregate_purchase_data()の戻り値を想定する。
    複数ページの場合は _001.png, _002.png ... の連番を付ける。
    """
    required = {"区分", "担当者ｺｰﾄﾞ", "仕入先名略称", "行数"}
    missing = required.difference(summary.columns)
    if missing:
        raise ValueError("集計結果に必要な列がありません: " + ", ".join(sorted(missing)))

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rows = summary.to_dict("records")
    pages = _paginate(rows, rows_per_page)
    title_font = _load_font(66, font_path)
    meta_font = _load_font(32, font_path)
    body_font = _load_font(38, font_path)
    staff_font = _load_font(42, font_path)
    footer_font = _load_font(27, font_path)

    margin_x = 170
    table_top = 570
    row_height = 74
    line_color = (190, 190, 190)
    generated: list[Path] = []

    for page_number, page_rows in enumerate(pages, start=1):
        image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
        draw = ImageDraw.Draw(image)

        draw.text((margin_x, 150), "伝票枚数集計表", font=title_font, fill=(20, 20, 20))
        period = f"対象期間：{_format_date(start_date)} ～ {_format_date(end_date)}"
        draw.text((margin_x, 285), period, font=meta_font, fill=(55, 55, 55))
        draw.text((margin_x, 345), f"ログインID：{login_id}", font=meta_font, fill=(55, 55, 55))
        draw.text((PAGE_WIDTH - margin_x - 260, 345), f"{page_number}/{len(pages)} ページ", font=meta_font, fill=(80, 80, 80))

        # 表ヘッダー
        draw.rectangle((margin_x, table_top, PAGE_WIDTH - margin_x, table_top + 78), fill=(235, 239, 243))
        draw.text((margin_x + 28, table_top + 17), "担当者コード / 仕入先", font=body_font, fill=(25, 25, 25))
        draw.text((PAGE_WIDTH - margin_x - 360, table_top + 17), "合計行数", font=body_font, fill=(25, 25, 25))

        y = table_top + 78
        for row in page_rows:
            kind = row.get("区分")
            if kind == "担当者":
                label = f"担当者　{row.get('担当者ｺｰﾄﾞ', '')}"
                font = staff_font
                fill = (245, 247, 250)
                text_color = (15, 35, 55)
                indent = 28
            elif kind == "仕入先":
                label = f"　└ {row.get('仕入先名略称', '')}"
                font = body_font
                fill = (255, 255, 255)
                text_color = (45, 45, 45)
                indent = 64
            else:
                label = "総合計"
                font = staff_font
                fill = (230, 235, 240)
                text_color = (10, 25, 40)
                indent = 28

            draw.rectangle((margin_x, y, PAGE_WIDTH - margin_x, y + row_height), fill=fill)
            draw.line((margin_x, y + row_height, PAGE_WIDTH - margin_x, y + row_height), fill=line_color, width=2)
            draw.text((margin_x + indent, y + 14), label, font=font, fill=text_color)
            count_text = f"{int(row.get('行数', 0)):,}"
            bbox = draw.textbbox((0, 0), count_text, font=font)
            count_width = bbox[2] - bbox[0]
            draw.text((PAGE_WIDTH - margin_x - 50 - count_width, y + 14), count_text, font=font, fill=text_color)
            y += row_height

        footer = f"出力ページ：{page_number} / {len(pages)}"
        draw.text((PAGE_WIDTH - margin_x - 300, PAGE_HEIGHT - 125), footer, font=footer_font, fill=(110, 110, 110))

        if len(pages) == 1:
            page_file = output_path / f"{filename}.png"
        else:
            page_file = output_path / f"{filename}_{page_number:03d}.png"
        image.save(page_file, format="PNG", dpi=DPI)
        generated.append(page_file)

    return generated
