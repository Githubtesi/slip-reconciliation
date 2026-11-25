# slip-reconciliation

社内システムから出力したCSVデータと、実際の現品票の枚数を照合するためのPythonプロジェクトです。

## 目的

社内システム上の処理件数と現品票の実枚数を比較し、処理漏れ・現品票の不足・過剰などの差異を確認できるようにします。

## Phase 1：CSV集計表の作成

仕入データCSVを条件で絞り込み、ピボットテーブル形式の集計表をA4縦のPDFとして出力します。

### 使用列

| 用途 | CSV列 |
|---|---|
| 日付フィルタ | 伝票日付 |
| ログインIDフィルタ | ﾛｸﾞｲﾝID |
| 集計第1階層 | 商品ｺｰﾄﾞ |
| 集計第2階層 | 仕入先名略称 |
| 集計対象 | CSVの明細行 |

### 集計ルール

- 伝票日付を開始日・終了日で絞り込みます。
- ﾛｸﾞｲﾝIDで絞り込みます（全IDも選択可能にする予定）。
- 商品ｺｰﾄﾞ > 仕入先名略称の2階層で集計します。
- 集計値はCSVの明細行数です。同一内容の行も重複排除せず、それぞれ1件として数えます。
- 商品コードごとの小計と全体の総計を表示します。

### 出力仕様

- A4縦のPDFとして出力します。
- タイトル、集計期間、ログインID、商品コード別小計、仕入先別件数、総計を表示します。
- A4縦、2480 × 3508px、300dpiで出力します。\n- データ量が多い場合は複数ページに分割し、ページ番号を表示します。

## 開発ロードマップ

1. CSV読み込み（文字コード・列名の確認を含む）
2. 伝票日付・ログインIDフィルタ
3. 商品コード・仕入先別の明細行数集計
4. A4 PDF出力
5. 集計結果のプレビュー画面
6. 現品票の実枚数入力または画像からの取得
7. CSV集計と現品票枚数の照合・差異管理

## 技術構成（初期案）

- Python 3.11以上
- pandas：CSV読み込み・集計
- ReportLab：A4 PDF生成
- FastAPI / Uvicorn：将来のWeb画面
- SQLite：将来の履歴・照合結果保存
- pytest：テスト

## ディレクトリ構成

```text
slip-reconciliation/
├── app/
│   ├── __init__.py
│   ├── csv_reader.py
│   ├── filters.py
│   ├── aggregation.py
│   └── image_export.py
├── config/
│   └── .gitkeep
├── data/
│   ├── input/
│   │   └── .gitkeep
│   └── output/
│       └── .gitkeep
├── tests/
│   └── .gitkeep
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

## セットアップ

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

### Linux / macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

## データ管理上の注意

社内CSVには取引先情報・個人情報などが含まれる可能性があります。実データや機密情報をGitHubへ登録しないでください。data/input/とdata/output/内の実ファイルはGit管理対象外です。動作確認には匿名化したダミーデータを使用してください。

## 開発状況

CSV読み込み、日付・ログインID・商品コードによる絞り込み、担当者・仕入先別集計、A4縦の複数ページPDF出力、CSVファイル・出力先フォルダの前回設定保存を実装済みです。実データでの一連の動作確認と、実行画面・EXE化は今後の作業です。
