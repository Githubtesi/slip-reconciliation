"""担当者コード > 仕入先名略称の階層で明細行数を集計する。"""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = ["担当者ｺｰﾄﾞ", "仕入先名略称"]


def aggregate_purchase_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """担当者別小計、仕入先別明細行数、総合計を階層順に返す。

    同一内容の明細行も重複排除せず、それぞれ1行として数える。
    戻り値の「区分」は「担当者」「仕入先」「総合計」のいずれか。
    """
    missing = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing:
        raise ValueError("必要な列がありません: " + ", ".join(missing))

    rows: list[dict[str, object]] = []
    total = 0

    # sort=FalseでCSVに現れた担当者・仕入先の順序を維持する。
    grouped = dataframe.groupby(
        ["担当者ｺｰﾄﾞ", "仕入先名略称"], sort=False, dropna=False
    ).size()

    if not grouped.empty:
        for staff_code, supplier_groups in grouped.groupby(level=0, sort=False):
            staff_total = int(supplier_groups.sum())
            rows.append(
                {
                    "区分": "担当者",
                    "担当者ｺｰﾄﾞ": staff_code,
                    "仕入先名略称": "",
                    "行数": staff_total,
                }
            )

            for key, count in supplier_groups.items():
                supplier_name = key[1]
                rows.append(
                    {
                        "区分": "仕入先",
                        "担当者ｺｰﾄﾞ": staff_code,
                        "仕入先名略称": supplier_name,
                        "行数": int(count),
                    }
                )
            total += staff_total

    rows.append(
        {
            "区分": "総合計",
            "担当者ｺｰﾄﾞ": "",
            "仕入先名略称": "",
            "行数": total,
        }
    )

    return pd.DataFrame(
        rows, columns=["区分", "担当者ｺｰﾄﾞ", "仕入先名略称", "行数"]
    )
