import csv
from pathlib import Path

from app.csv_reader import EXPECTED_COLUMNS, load_login_ids


def test_load_login_ids_reads_unique_values_and_ignores_blanks(tmp_path: Path) -> None:
    path = tmp_path / "login_ids.csv"
    rows = [
        ["20261101", "1", "1", "通常", "1", "仕入先A", "A01", "P001", "商品", "1", "得意先", "1", "1", "1", "", "", "", "1", "1", "IR-301"],
        ["20261102", "2", "1", "通常", "1", "仕入先B", "A02", "P002", "商品", "1", "得意先", "1", "1", "1", "", "", "", "1", "1", "IR-302"],
        ["20261103", "3", "1", "通常", "1", "仕入先B", "A02", "P003", "商品", "1", "得意先", "1", "1", "1", "", "", "", "1", "1", "IR-301"],
        ["20261104", "4", "1", "通常", "1", "仕入先B", "A02", "P004", "商品", "1", "得意先", "1", "1", "1", "", "", "", "1", "1", ""],
    ]
    with path.open("w", encoding="utf-16", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(EXPECTED_COLUMNS)
        writer.writerows(rows)

    assert load_login_ids(path, chunksize=2) == ["IR-301", "IR-302"]
