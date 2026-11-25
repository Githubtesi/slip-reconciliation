from pathlib import Path

import pandas as pd
import pytest

from app.csv_reader import (
    EXPECTED_COLUMNS,
    CsvValidationError,
    load_csv,
)


def _sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [{column: "" for column in EXPECTED_COLUMNS}],
        columns=EXPECTED_COLUMNS,
    )


def test_load_csv_utf8_and_keep_code_as_string(tmp_path: Path) -> None:
    dataframe = _sample_dataframe()
    dataframe.loc[0, "商品ｺｰﾄﾞ"] = "00123"
    dataframe.loc[0, "ﾛｸﾞｲﾝID"] = "0007"
    path = tmp_path / "sample.csv"
    dataframe.to_csv(path, index=False, encoding="utf-8-sig")

    result = load_csv(path)

    assert list(result.columns) == EXPECTED_COLUMNS
    assert result.loc[0, "商品ｺｰﾄﾞ"] == "00123"
    assert result.loc[0, "ﾛｸﾞｲﾝID"] == "0007"


def test_load_csv_cp932(tmp_path: Path) -> None:
    path = tmp_path / "sample_cp932.csv"
    _sample_dataframe().to_csv(path, index=False, encoding="cp932")

    result = load_csv(path)

    assert len(result) == 1
    assert list(result.columns) == EXPECTED_COLUMNS


def test_load_csv_reorders_columns(tmp_path: Path) -> None:
    reversed_columns = list(reversed(EXPECTED_COLUMNS))
    path = tmp_path / "reordered.csv"
    pd.DataFrame([{column: "" for column in reversed_columns}]).to_csv(
        path, index=False, encoding="utf-8-sig"
    )

    result = load_csv(path)

    assert list(result.columns) == EXPECTED_COLUMNS


def test_load_csv_reports_missing_column(tmp_path: Path) -> None:
    columns = EXPECTED_COLUMNS[:-1]
    path = tmp_path / "missing.csv"
    pd.DataFrame(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")

    with pytest.raises(CsvValidationError, match="不足している列"):
        load_csv(path)


def test_load_csv_reports_unexpected_column(tmp_path: Path) -> None:
    columns = EXPECTED_COLUMNS + ["追加列"]
    path = tmp_path / "extra.csv"
    pd.DataFrame(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")

    with pytest.raises(CsvValidationError, match="想定外の列"):
        load_csv(path)


def test_load_csv_reports_duplicate_column(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.csv"
    path.write_text(
        ",".join(EXPECTED_COLUMNS + ["商品ｺｰﾄﾞ"]) + "\n",
        encoding="utf-8-sig",
    )

    with pytest.raises(CsvValidationError, match="重複"):
        load_csv(path)
