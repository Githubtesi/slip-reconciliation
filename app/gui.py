"""Tkinter desktop GUI for slip reconciliation."""

from __future__ import annotations

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
from app.image_export import export_summary_images


def _application_dir() -> Path:
    """EXE実行時はEXEの隣、Python実行時はプロジェクト直下を返す。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


class SlipReconciliationApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("伝票枚数カウント")
        self.root.geometry("680x430")
        self.root.minsize(620, 400)
        self.csv_path = tk.StringVar()
        self.login_id = tk.StringVar()
        self.status = tk.StringVar(value="CSVファイルを選択してください。")
        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=22)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="伝票枚数カウント", font=("", 18, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 18)
        )
        ttk.Label(frame, text="CSVファイル").grid(row=1, column=0, sticky="w")
        file_row = ttk.Frame(frame)
        file_row.grid(row=2, column=0, sticky="ew", pady=(5, 16))
        file_row.columnconfigure(0, weight=1)
        ttk.Entry(file_row, textvariable=self.csv_path).grid(row=0, column=0, sticky="ew")
        self.select_button = ttk.Button(file_row, text="参照...", command=self._choose_csv)
        self.select_button.grid(row=0, column=1, padx=(8, 0))

        ttk.Label(frame, text="集計対象期間").grid(row=3, column=0, sticky="w")
        date_row = ttk.Frame(frame)
        date_row.grid(row=4, column=0, sticky="w", pady=(5, 16))
        ttk.Label(date_row, text="開始日").pack(side="left")
        self.start_date = DateEntry(date_row, date_pattern="yyyy-mm-dd", width=13)
        self.start_date.set_date(date(date.today().year, date.today().month, 1))
        self.start_date.pack(side="left", padx=(8, 20))
        ttk.Label(date_row, text="終了日").pack(side="left")
        self.end_date = DateEntry(date_row, date_pattern="yyyy-mm-dd", width=13)
        self.end_date.set_date(date.today())
        self.end_date.pack(side="left", padx=(8, 0))

        ttk.Label(frame, text="ログインID").grid(row=5, column=0, sticky="w")
        self.login_combo = ttk.Combobox(
            frame, textvariable=self.login_id, state="readonly", width=28
        )
        self.login_combo.grid(row=6, column=0, sticky="w", pady=(5, 18))

        self.run_button = ttk.Button(
            frame, text="集計・画像出力", command=self._run, state="disabled"
        )
        self.run_button.grid(row=7, column=0, sticky="ew", ipady=8)
        ttk.Separator(frame).grid(row=8, column=0, sticky="ew", pady=18)
        ttk.Label(frame, textvariable=self.status, wraplength=620, justify="left").grid(
            row=9, column=0, sticky="w"
        )

    def _choose_csv(self) -> None:
        selected = filedialog.askopenfilename(
            title="仕入CSVを選択",
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")],
        )
        if not selected:
            return
        self.csv_path.set(selected)
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
        self.status.set(
            f"ログインIDを{len(login_ids)}件取得しました。集計条件を指定してください。"
        )

    def _run(self) -> None:
        csv_file = self.csv_path.get().strip()
        selected_login = self.login_id.get().strip()
        start = self.start_date.get_date()
        end = self.end_date.get_date()
        if not csv_file or not Path(csv_file).is_file():
            messagebox.showwarning("入力確認", "CSVファイルを選択してください。")
            return
        if not selected_login:
            messagebox.showwarning("入力確認", "ログインIDを選択してください。")
            return
        if start > end:
            messagebox.showwarning("入力確認", "開始日は終了日以前の日付を指定してください。")
            return

        self.run_button.configure(state="disabled")
        self.select_button.configure(state="disabled")
        self.status.set("CSVを読み込み、集計しています。ファイルサイズにより時間がかかります...")
        threading.Thread(
            target=self._process_worker,
            args=(csv_file, start, end, selected_login),
            daemon=True,
        ).start()

    def _process_worker(
        self, csv_file: str, start: date, end: date, selected_login: str
    ) -> None:
        try:
            data = load_csv(csv_file)
            filtered = filter_purchase_data(data, start, end, selected_login)
            summary = aggregate_purchase_data(filtered)
            output_dir = _application_dir() / "data" / "output"
            paths = export_summary_images(
                summary, output_dir, start_date=start, end_date=end, login_id=selected_login
            )
            self.root.after(
                0, lambda: self._process_finished(len(data), len(filtered), paths, None)
            )
        except Exception as exc:
            self.root.after(0, lambda error=exc: self._process_finished(0, 0, [], error))

    def _process_finished(
        self, source_count: int, filtered_count: int,
        paths: list[Path], error: Exception | None
    ) -> None:
        self.run_button.configure(state="normal")
        self.select_button.configure(state="normal")
        if error:
            self.status.set("処理に失敗しました。")
            messagebox.showerror("処理エラー", str(error))
            return
        file_list = "\n".join(str(path) for path in paths)
        self.status.set(
            f"完了：元データ {source_count:,}行 / 抽出 {filtered_count:,}行\n"
            f"出力先：{paths[0].parent}"
        )
        messagebox.showinfo(
            "集計完了",
            f"集計が完了しました。\n抽出行数：{filtered_count:,}行\n"
            f"出力ページ数：{len(paths)}\n\n{file_list}",
        )


def launch_gui() -> None:
    root = tk.Tk()
    SlipReconciliationApp(root)
    root.mainloop()
