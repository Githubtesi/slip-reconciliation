"""Filtering utilities for purchase-slip CSV data."""

from __future__ import annotations

from datetime import date, datetime
from typing import Union

import pandas as pd


DateLike = Union[str, date, datetime]


def _to_yyyymmdd(value: DateLike, argument_name: str) -> int:
    """Convert a date or YYYY-MM-DD / YYYYMMDD string to an integer."""
    if isinstance(value, datetime):
        return int(value.strftime("%Y%m%d"))
    if isinstance(value, date):
        return int(value.strftime("%Y%m%d"))

    text = str(value).strip()
    for date_format in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return int(datetime.strptime(text, date_format).strftime("%Y%m%d"))
        except ValueError:
            continue

    raise ValueError(
        f"{argument_name}は YYYY-MM-DD または YYYYMMDD 形式で指定してください: {value}"
    )


def filter_purchase_data(
    dataframe: pd.DataFrame,
    start_date: DateLike,
    end_date: DateLike,
    login_id: str = "IR-301",
) -> pd.DataFrame:
    """Filter by inclusive slip date range, login ID, and non-empty product code.

    伝票日付は YYYYMMDD 形式（例: 20261125）の整数または文字列を想定します。
    元のDataFrameは変更せず、条件に一致した行のコピーを返します。
    """
    required_columns = {"伝票日付", "ﾛｸﾞｲﾝID", "商品ｺｰﾄﾞ"}
    missing = sorted(required_columns - set(dataframe.columns))
    if missing:
        raise ValueError("フィルタに必要な列がありません: " + ", ".join(missing))

    start_value = _to_yyyymmdd(start_date, "start_date")
    end_value = _to_yyyymmdd(end_date, "end_date")
    if start_value > end_value:
        raise ValueError("開始日は終了日以前の日付を指定してください。")

    slip_dates = pd.to_numeric(dataframe["伝票日付"], errors="coerce")
    date_mask = slip_dates.between(start_value, end_value, inclusive="both")

    login_mask = (
        dataframe["ﾛｸﾞｲﾝID"].astype("string").str.strip().eq(str(login_id).strip())
    ).fillna(False)

    product_codes = dataframe["商品ｺｰﾄﾞ"].astype("string").str.strip()
    product_mask = (product_codes.notna() & product_codes.ne("")).fillna(False)

    return dataframe.loc[date_mask & login_mask & product_mask].copy()
