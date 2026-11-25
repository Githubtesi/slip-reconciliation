"""CSV loading and schema validation for Smile purchase-slip exports."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Union

import pandas as pd


EXPECTED_COLUMNS = [
    "伝票日付",
    "伝票№",
    "処理連番",
    "明細区分名",
    "行",
    "仕入先名略称",
    "担当者ｺｰﾄﾞ",
    "商品ｺｰﾄﾞ",
    "商品名１",
    "得意先ｺｰﾄﾞ",
    "得意先名",
    "数量",
    "単価",
    "金額",
    "行摘要１",
    "行摘要２",
    "備考",
    "発注№",
    "発注行",
    "ﾛｸﾞｲﾝID",
]

# コード類は数値変換せず、先頭のゼロを保持する。
STRING_COLUMNS = {
    "担当者ｺｰﾄﾞ": "string",
    "商品ｺｰﾄﾞ": "string",
    "ﾛｸﾞｲﾝID": "string",
}


class CsvValidationError(ValueError):
    """CSVの形式または列構成が想定と異なる場合のエラー。"""


def _read_header(path: Path, encoding: str) -> list[str]:
    """CSVのヘッダーを読み取り、重複列名を検出する。"""
    with path.open("r", encoding=encoding, newline="") as file:
        reader = csv.reader(file)
        try:
            return next(reader)
        except StopIteration as exc:
            raise CsvValidationError("CSVファイルが空です。") from exc


def _validate_columns(columns: list[str]) -> None:
    """必須列・余分な列・重複列を検証する。"""
    duplicates = sorted({name for name in columns if columns.count(name) > 1})
    if duplicates:
        raise CsvValidationError(
            "CSVに重複している列名があります: " + ", ".join(duplicates)
        )

    missing = [name for name in EXPECTED_COLUMNS if name not in columns]
    unexpected = [name for name in columns if name not in EXPECTED_COLUMNS]

    if missing or unexpected:
        messages = []
        if missing:
            messages.append("不足している列: " + ", ".join(missing))
        if unexpected:
            messages.append("想定外の列: " + ", ".join(unexpected))
        raise CsvValidationError(
            "CSVの列構成が shiire_list_smile と一致しません。\n"
            + "\n".join(messages)
        )


def load_csv(file_path: Union[str, Path]) -> pd.DataFrame:
    """Smileの仕入データCSVを読み込み、列名と列構成を検証する。

    対応文字コード: UTF-8 BOM付き、UTF-8、CP932（Shift-JIS系）。
    列の並び順は問いません。読み込み後は EXPECTED_COLUMNS の順に統一します。
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"CSVファイルが見つかりません: {path}")

    last_decode_error = None

    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            columns = _read_header(path, encoding)
            _validate_columns(columns)

            dataframe = pd.read_csv(
                path,
                encoding=encoding,
                dtype=STRING_COLUMNS,
                keep_default_na=False,
                on_bad_lines="error",
            )
            # 列順が異なるCSVでも、アプリ内では常に定義順にそろえる。
            return dataframe.loc[:, EXPECTED_COLUMNS]

        except UnicodeDecodeError as exc:
            last_decode_error = exc
            continue
        except pd.errors.EmptyDataError as exc:
            raise CsvValidationError("CSVファイルにヘッダーがありません。") from exc
        except pd.errors.ParserError as exc:
            raise CsvValidationError(f"CSVの読み込みに失敗しました: {exc}") from exc

    raise CsvValidationError(
        "CSVの文字コードを判定できませんでした。"
        "UTF-8またはCP932形式で保存し直してください。"
    ) from last_decode_error
