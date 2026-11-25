"""Tkinter desktop GUI for slip reconciliation."""

from __future__ import annotations

import json
import sys
import threading
from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from tkcalendar import DateEntry

from app.aggregation import aggregate_purchase_data
from app.csv_reader import load_csv, load_login_ids
from app.filters import filter_purchase_data
from app.pdf_export import export_summary_pdf


def _application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _settings_path() -> Path:
    return _application_dir() / "config" / "settings.json"


def _load_settings() -> dict[str, str]:
    path = _settings_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {
                "csv_path": str(data.get("csv_path", "")),
                "output_dir": str(data.get("output_dir", "")),
            }
    except (OSError, json.JSONDecodeError):
        pass
    return {"csv_path": "", "output_dir": ""}


def _save_settings(csv_path: str, output_dir: str) -> None:
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps({"csv_path": csv_path, "output_dir": output_dir}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp_path.replace(path)


class SlipReconciliationApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("伝票枚数カウント")
        self.root.geometry("760x480")
        self.root.minsize(680, 440)
        settings = _load_settings()
        self.csv_path = tk.StringVar(value=settings["csv_path"])
        default_output = str(_application_dir() / "data" / "output")
        saved_output = settings["output_dir"]
        self.output_dir = tk.StringVar(
            value=saved_output if saved_output and Path(saved_output).is_dir() else default_output
        )
        self.login_id = tk.StringVar()
        self.status = tk.StringVar(value="CSVファイルを確認してください。")
        self._build_ui()
        if self.csv_path.get() and Path(self.csv_path.get()).is_file():
            self._start_login_id_loading(self.csv_path.get())

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=22)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="伝票枚数カウント", font=("", 18, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 18)
        )
        ttk.Label(frame, text="CSVファイル").grid(row=1, column=0, sticky="w")
        csv_row = ttk.Frame(frame)
        csv_row.grid(row=2, column=0, sticky="ew", pady=(5, 14))
        csv_row.columnconfigure(0, weight=1)
        ttk.Entry(csv_row, textvariable=self.csv_path).grid(row=0, column=0, sticky="ew")
        self.select_button = ttk.Button(csv_row, text="参照...", command=self._choose_csv)
        self.select_button.grid(row=0, column=1, padx=(8, 0))

        ttk.Label(frame, text="出力先フォルダ").grid(row=3, column=0, sticky="w")
        output_row = ttk.Frame(frame)
        output_row.grid(row=4, column=0, sticky="ew", pady=(5, 14))
        output_row.columnconfigure(0, weight=1)
        ttk.Entry(output_row, textvariable=self.output_dir).grid(row=0, column=0, sticky="ew")
        ttk.Button(output_row, text="参照...", command=self._choose_output_dir).grid(
            row=0, column=1, padx=(8, 0)
        )

        ttk.Label(frame, text="集計対象期間").grid(row=5, column=0, sticky="w")
        date_row = ttk.Frame(frame)
        date_row.grid(row=6, column=0, sticky="w", pady=(5, 14))
        ttk.Label(date_row, text="開始日").pack(side="left")
        self.start_date = DateEntry(date_row, date_pattern="yyyy-mm-dd", width=13)
        self.start_date.set_date(date(date.today().year, date.today().month, 1))
        self.start_date.pack(side="left", padx=(8, 20))
        ttk.Label(date_row, text="終了日").pack(side="left")
        self.end_date = DateEntry(date_row, date_pattern="yyyy-mm-dd", width=13)
        self.end_date.set_date(date.today())
        self.end_date.pack(side="left", padx=(8, 0))

        ttk.Label(frame, text="ログインID").grid(row=7, column=0, sticky="w")
        self.login_combo = ttk.Combobox(
            frame, textvariable=self.login_id, state="readonly", width=28
        )
        self.login_combo.grid(row=8, column=0, sticky="w", pady=(5, 18))

        self.run_button = ttk.Button(
            frame, text="集計・PDF出力", command=self._run, state="disabled"
        )
        self.run_button.grid(row=9, column=0, sticky="ew", ipady=8)
        ttk.Separator(frame).grid(row=10, column=0, sticky="ew", pady=16)
        ttk.Label(frame, textvariable=self.status, wraplength=700, justify="left").grid(
            row=11, column=0, sticky="w"
        )

    def _choose_csv(self) -> None:
        selected = filedialog.askopenfilename(
            title="仕入CSVを選択",
            initialdir=str(Path(self.csv_path.get()).parent) if self.csv_path.get() else None,
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")],
        )
        if not selected:
            return
        self.csv_path.set(selected)
        self._persist_settings()
        self._start_login_id_loading(selected)

    def _choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(
            title="PDF出力先フォルダを選択",
            initialdir=self.output_dir.get() or str(_application_dir()),
            mustexist=True,
        )
        if selected:
            self.output_dir.set(selected)
            self._persist_settings()

    def _persist_settings(self) -> None:
        try:
            _save_settings(self.csv_path.get().strip(), self.output_dir.get().strip())
        except OSError as exc:
            messagebox.showwarning("設定保存", f"設定を保存できませんでした。\n{exc}")

    def _start_login_id_loading(self, selected: str) -> None:
        self.login_combo["values"] = ()
        self.login_id.set("")
        self.run_button.configure(state="disabled")
        self.select_button.configure(state="disabled")
        self.status.set("CSV内のログインIDを確認しています...")
        threading.Thread(
            target=self._read_login_ids_worker, args=(selected,), daemon=True
        ).start()

    def _read_login_ids_worker(self, selected: str) -> None:
        try:
            ids = load_login_ids(selected)
            self.root.after(0, lambda: self._login_ids_loaded(selected, ids, None))
        except Exception as exc:
            self.root.after(0, lambda error=exc: self._login_ids_loaded(selected, [], error))

    def _login_ids_loaded(
        self, selected: str, login_ids: list[str], error: Exception | None
    ) -> None:
        self.select_button.configure(state="normal")
        if selected != self.csv_path.get():
            return
        if error:
            self.status.set("CSVの確認に失敗しました。")
            messagebox.showerror("CSV読み込みエラー", str(error))
            return
        if not login_ids:
            self.status.set("CSV内にログインIDが見つかりませんでした。")
            messagebox.showwarning("確認", "CSV内にログインIDがありません。")
            return
        self.login_combo["values"] = login_ids
        self.login_id.set("IR-301" if "IR-301" in login_ids else login_ids[0])
        self.run_button.configure(state="normal")
        self.status.set(f"ログインIDを{len(login_ids)}件取得しました。集計条件を指定してください。")

    def _run(self) -> None:
        csv_file = self.csv_path.get().strip()
        output_dir = self.output_dir.get().strip()
        selected_login = self.login_id.get().strip()
        start = self.start_date.get_date()
        end = self.end_date.get_date()
        if not csv_file or not Path(csv_file).is_file():
            messagebox.showwarning("入力確認", "CSVファイルを選択してください。")
            return
        if not output_dir:
            messagebox.showwarning("入力確認", "PDF出力先フォルダを指定してください。")
            return
        if not selected_login:
            messagebox.showwarning("入力確認", "ログインIDを選択してください。")
            return
        if start > end:
            messagebox.showwarning("入力確認", "開始日は終了日以前の日付を指定してください。")
            return
        if not Path(output_dir).is_dir():
            messagebox.showwarning("入力確認", "指定した出力先フォルダが存在しません。")
            return

        self._persist_settings()
        self.run_button.configure(state="disabled")
        self.select_button.configure(state="disabled")
        self.status.set("CSVを読み込み、集計しています。ファイルサイズにより時間がかかります...")
        threading.Thread(
            target=self._process_worker,
            args=(csv_file, output_dir, start, end, selected_login),
            daemon=True,
        ).start()

    def _process_worker(
        self, csv_file: str, output_dir: str, start: date, end: date, selected_login: str
    ) -> None:
        try:
            data = load_csv(csv_file)
            filtered = filter_purchase_data(data, start, end, selected_login)
            summary = aggregate_purchase_data(filtered)
            pdf_path = export_summary_pdf(
                summary, output_dir, start_date=start, end_date=end, login_id=selected_login
            )
            self.root.after(
                0, lambda: self._process_finished(len(data), len(filtered), pdf_path, None)
            )
        except Exception as exc:
            self.root.after(0, lambda error=exc: self._process_finished(0, 0, None, error))

    def _process_finished(
        self, source_count: int, filtered_count: int,
        pdf_path: Path | None, error: Exception | None
    ) -> None:
        self.run_button.configure(state="normal")
        self.select_button.configure(state="normal")
        if error:
            self.status.set("処理に失敗しました。")
            messagebox.showerror("処理エラー", str(error))
            return
        self.status.set(
            f"完了：元データ {source_count:,}行 / 抽出 {filtered_count:,}行\n"
            f"出力ファイル：{pdf_path}"
        )
        messagebox.showinfo(
            "集計完了",
            f"集計が完了しました。\n抽出行数：{filtered_count:,}行\n\n"
            f"PDF出力先：{pdf_path}",
        )


def launch_gui() -> None:
    root = tk.Tk()
    SlipReconciliationApp(root)
    root.mainloop()
