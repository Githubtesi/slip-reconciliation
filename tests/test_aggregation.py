import pandas as pd
import pytest

from app.aggregation import aggregate_purchase_data


def test_aggregate_staff_then_supplier_and_grand_total() -> None:
    dataframe = pd.DataFrame(
        [
            {"担当者ｺｰﾄﾞ": "A01", "仕入先名略称": "仕入先A"},
            {"担当者ｺｰﾄﾞ": "A01", "仕入先名略称": "仕入先A"},
            {"担当者ｺｰﾄﾞ": "A01", "仕入先名略称": "仕入先B"},
            {"担当者ｺｰﾄﾞ": "B02", "仕入先名略称": "仕入先A"},
            {"担当者ｺｰﾄﾞ": "B02", "仕入先名略称": "仕入先C"},
            {"担当者ｺｰﾄﾞ": "B02", "仕入先名略称": "仕入先C"},
        ]
    )

    result = aggregate_purchase_data(dataframe)

    assert result.to_dict("records") == [
        {"区分": "担当者", "担当者ｺｰﾄﾞ": "A01", "仕入先名略称": "", "行数": 3},
        {"区分": "仕入先", "担当者ｺｰﾄﾞ": "A01", "仕入先名略称": "仕入先A", "行数": 2},
        {"区分": "仕入先", "担当者ｺｰﾄﾞ": "A01", "仕入先名略称": "仕入先B", "行数": 1},
        {"区分": "担当者", "担当者ｺｰﾄﾞ": "B02", "仕入先名略称": "", "行数": 3},
        {"区分": "仕入先", "担当者ｺｰﾄﾞ": "B02", "仕入先名略称": "仕入先A", "行数": 1},
        {"区分": "仕入先", "担当者ｺｰﾄﾞ": "B02", "仕入先名略称": "仕入先C", "行数": 2},
        {"区分": "総合計", "担当者ｺｰﾄﾞ": "", "仕入先名略称": "", "行数": 6},
    ]


def test_aggregate_counts_identical_rows_separately() -> None:
    dataframe = pd.DataFrame(
        [
            {"担当者ｺｰﾄﾞ": "A01", "仕入先名略称": "仕入先A"},
            {"担当者ｺｰﾄﾞ": "A01", "仕入先名略称": "仕入先A"},
        ]
    )

    result = aggregate_purchase_data(dataframe)

    assert result.iloc[0]["行数"] == 2
    assert result.iloc[1]["行数"] == 2
    assert result.iloc[-1]["行数"] == 2


def test_aggregate_empty_dataframe_returns_zero_total() -> None:
    dataframe = pd.DataFrame(columns=["担当者ｺｰﾄﾞ", "仕入先名略称"])

    result = aggregate_purchase_data(dataframe)

    assert result.to_dict("records") == [
        {"区分": "総合計", "担当者ｺｰﾄﾞ": "", "仕入先名略称": "", "行数": 0}
    ]


def test_aggregate_requires_columns() -> None:
    with pytest.raises(ValueError, match="必要な列"):
        aggregate_purchase_data(pd.DataFrame({"担当者ｺｰﾄﾞ": ["A01"]}))
