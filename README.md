# 伝票枚数カウント（slip-reconciliation）

SMILEから出力した仕入データCSVを読み込み、指定した期間・ログインIDで抽出した明細行数を担当者・仕入先別に集計し、A4縦のPDFとして出力するWindowsデスクトップアプリです。

## 主な機能

- SMILEの仕入データCSV（`shiire_list_smile`相当）を読み込み
- UTF-8 / UTF-8 BOM付き / UTF-16 / UTF-16LE・BE / CP932のCSVに対応
- CSV内のログインIDを自動取得し、プルダウンから選択
- 初期ログインIDは `IR-301`（CSV内に存在する場合）
- 伝票日付の開始日・終了日で抽出
- 商品コードが空欄の明細を除外
- 担当者コード → 仕入先名略称の2階層で明細行数を集計
- 担当者別小計、仕入先別件数、全体の総合計を表示
- A4縦の複数ページPDFを1ファイルに出力
- 前回選択したCSVファイルとPDF出力先フォルダを保存し、次回起動時に復元

## 集計仕様

| 項目 | 内容 |
|---|---|
| 日付フィルタ | `伝票日付` |
| ログインIDフィルタ | `ﾛｸﾞｲﾝID` |
| 商品コード判定 | `商品ｺｰﾄﾞ` が空欄でない明細を対象 |
| 第1階層 | `担当者ｺｰﾄﾞ` |
| 第2階層 | `仕入先名略称` |
| 集計値 | CSVの明細行数 |

同じ内容の明細行であっても重複排除はせず、CSV上の1行を1件として数えます。集計表は担当者ごとの合計行の下に、その担当者に属する仕入先別の行数を表示します。

## 画面・出力

1. CSVファイルを選択します。
2. PDFの出力先フォルダを選択します。
3. 集計期間とログインIDを指定します。
4. 「集計・PDF出力」を押します。

出力されるPDFのファイル名は `伝票枚数集計.pdf` です。同じ出力先に同名ファイルがある場合は上書きされます。必要なPDFは別フォルダへ移動するなどして保管してください。

## 動作環境

- Windows 10 / 11
- Python 3.11以上（ソースから実行する場合）
- EXE版はPythonのインストール不要

## ソースからの実行方法

### 1. リポジトリを取得

```powershell
git clone https://github.com/Githubtesi/slip-reconciliation.git
cd slip-reconciliation
```

既に取得済みの場合は、プロジェクトフォルダで `git pull origin main` を実行してください。

### 2. 仮想環境を作成して依存パッケージをインストール

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. アプリを起動

```powershell
python main.py
```

### 4. テスト

```powershell
python -m pytest -v
```

## EXEのビルド方法

EXEの作成はWindows上で行ってください。以下はPowerShellでの手順です。

### 1. 仮想環境を有効化

```powershell
.venv\Scripts\Activate.ps1
```

### 2. PyInstallerをインストール

```powershell
python -m pip install pyinstaller
```

### 3. EXEを作成

プロジェクトのルートフォルダで実行します。

```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "伝票枚数カウント" --collect-all tkcalendar --collect-all babel main.py
```

ビルドが完了すると、次の場所にEXEが作成されます。

```text
dist/伝票枚数カウント.exe
```

EXEを配布する際は、EXEを任意のフォルダに置いて実行してください。初回起動時にEXEと同じ場所へ `config/settings.json` が作成されます。設定を保存するため、EXEを置くフォルダには書き込み権限が必要です。会社PCで利用する場合は、デスクトップやユーザーが書き込み可能なフォルダへの配置を推奨します。

## 設定ファイル・出力先

- 設定ファイル：EXEと同じフォルダの `config/settings.json`
- 設定内容：前回選択したCSVファイルのパス、PDF出力先フォルダ
- PDF出力先：アプリ画面で指定したフォルダ

`config/settings.json` はPCごとのローカルパスを保存するため、Git管理対象外です。別のPCへEXEを移した場合、CSVファイルや出力先はそのPCで改めて指定してください。

## ディレクトリ構成

```text
slip-reconciliation/
├── app/
│   ├── __init__.py
│   ├── aggregation.py
│   ├── csv_reader.py
│   ├── filters.py
│   ├── gui.py
│   ├── image_export.py
│   └── pdf_export.py
├── config/
│   └── .gitkeep
├── data/
│   ├── input/
│   │   └── .gitkeep
│   └── output/
│       └── .gitkeep
├── tests/
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

## データ管理上の注意

仕入データCSVには取引先情報などの社内情報が含まれる可能性があります。実データや個人情報をGitHubへ登録しないでください。実データはローカルPCまたは社内で許可された保存先に置いてください。

## 今後の拡張候補

- 現品票の実枚数入力
- CSV集計結果と現品票枚数の照合
- 差異の一覧表示・履歴保存
