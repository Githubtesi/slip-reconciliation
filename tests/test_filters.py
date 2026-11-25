import pandas as pd
import pytest

from app.filters import filter_purchase_data


def _dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"伝票日付": 20261101, "ﾛｸﾞｲﾝID": "IR-301", "商品ｺｰﾄﾞ": "001"},
            {"伝票日付": 20261125, "ﾛｸﾞｲﾝID": "IR-301", "商品ｺｰﾄﾞ": "002"},
            {"伝票日付": 20261031, "ﾛｸﾞｲﾝID": "IR-301", "商品ｺｰﾄﾞ": "003"},
            {"伝票日付": 20261110, "ﾛｸﾞｲﾝID": "OTHER", "商品ｺｰﾄﾞ": "004"},
            {"伝票日付": 20261110, "ﾛｸﾞｲﾝID": "IR-301", "商品ｺｰﾄﾞ": ""},
            {"伝票日付": 20261110, "ﾛｸﾞｲﾝID": "IR-301", "商品ｺｰﾄﾞ": None},
            {"伝票日付": 20261110, "ﾛｸﾞｲﾝID": "IR-301", "商品ｺｰﾄﾞ": "   "},
        ]
    )


def test_filter_by_inclusive_date_login_and_product_code() -> None:
    result = filter_purchase_data(
        _dataframe(), "2026-11-01", "2026-11-25", login_id="IR-301"
    )

    assert result["商品ｺｰﾄﾞ"].tolist() == ["001", "002"]


def test_filter_accepts_compact_date_format() -> None:
    result = filter_purchase_data(
        _dataframe(), "20261101", "20261125"
    )

    assert len(result) == 2


def test_filter_rejects_start_date_after_end_date() -> None:
    with pytest.raises(ValueError, match="開始日"):
        filter_purchase_data(_dataframe(), "2026-11-25", "2026-11-01")


def test_filter_requires_columns() -> None:
    with pytest.raises(ValueError, match="必要な列"):
        filter_purchase_data(pd.DataFrame({"伝票日付": []}), "2026-11-01", "2026-11-25")
