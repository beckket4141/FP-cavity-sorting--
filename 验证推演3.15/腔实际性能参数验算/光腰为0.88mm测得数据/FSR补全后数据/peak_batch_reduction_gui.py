from __future__ import annotations

import os
import queue
import re
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import pandas as pd

from reduce_crosstalk_peak import DEFAULT_DETECTION_PARAMS, DEFAULT_REDUCTION_FRAC, process_single_csv

VALID_REQUIRED_COLUMNS = {"Lambda_aligned", "Power_uW"}
EXCLUDED_STEM_SUFFIXES = (
    "_detected_peaks",
    "_selected_peak_families",
    "_peak_summary",
    "_crosstalk_reduced",
    "_crosstalk_reduction_summary",
    "_reduction_reference_detected_peaks",
    "_reduction_reference_peak_families",
)


@dataclass(frozen=True)
class ScannedCsvInfo:
    path: Path
    name: str
    rows: int
    l_value: int | None
    status: str


def extract_l_value(file_name: str) -> int | None:
    match = re.search(r"_l(\d+)", file_name, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def scan_valid_csv_files(folder: Path) -> tuple[list[ScannedCsvInfo], list[str]]:
    valid_files: list[ScannedCsvInfo] = []
    invalid_logs: list[str] = []

    if not folder.exists():
        raise FileNotFoundError(f"Input folder not found: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Input path is not a folder: {folder}")

    for csv_path in sorted(folder.glob("*.csv")):
        if csv_path.stem.endswith(EXCLUDED_STEM_SUFFIXES):
            invalid_logs.append(f"[跳过] {csv_path.name}: 属于本工具导出的结果文件")
            continue
        try:
            header_df = pd.read_csv(csv_path, nrows=0)
            missing = VALID_REQUIRED_COLUMNS - set(header_df.columns)
            if missing:
                invalid_logs.append(f"[跳过] {csv_path.name}: 缺少列 {sorted(missing)}")
                continue
            row_count = int(pd.read_csv(csv_path, usecols=["Lambda_aligned"]).shape[0])
            valid_files.append(
                ScannedCsvInfo(
                    path=csv_path,
                    name=csv_path.name,
                    rows=row_count,
                    l_value=extract_l_value(csv_path.name),
                    status="可处理",
                )
            )
        except Exception as exc:
            invalid_logs.append(f"[跳过] {csv_path.name}: {exc}")

    valid_files.sort(key=lambda item: (item.l_value if item.l_value is not None else 9999, item.name.lower()))
    return valid_files, invalid_logs


class BatchReductionApp(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=10)
        self.master = master
        self.master.title("批量 CSV 小干扰峰削减工具")
        self.master.minsize(980, 720)
        self.grid(sticky="nsew")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        self.rowconfigure(6, weight=1)

        self.scanned_files: dict[str, ScannedCsvInfo] = {}
        self.log_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.advanced_visible = tk.BooleanVar(value=False)

        self.input_dir_var = tk.StringVar(value=str(Path.cwd()))
        self.output_dir_var = tk.StringVar(value=str(Path.cwd()))
        self.reduction_percent_var = tk.StringVar(value=f"{DEFAULT_REDUCTION_FRAC * 100:.0f}")

        self.param_vars: dict[str, tk.StringVar] = {
            name: tk.StringVar(value=str(value))
            for name, value in DEFAULT_DETECTION_PARAMS.items()
        }

        self._build_ui()
        self.after(150, self._poll_queue)

    def _build_ui(self) -> None:
        input_frame = ttk.LabelFrame(self, text="输入目录")
        input_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        input_frame.columnconfigure(0, weight=1)
        ttk.Entry(input_frame, textvariable=self.input_dir_var).grid(row=0, column=0, sticky="ew", padx=(8, 6), pady=8)
        self.browse_input_button = ttk.Button(input_frame, text="浏览", command=self._browse_input_dir)
        self.browse_input_button.grid(row=0, column=1, padx=6, pady=8)
        self.scan_button = ttk.Button(input_frame, text="扫描 CSV", command=self._scan_folder)
        self.scan_button.grid(row=0, column=2, padx=(0, 8), pady=8)

        file_frame = ttk.LabelFrame(self, text="可处理文件（手动多选）")
        file_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(0, weight=1)

        columns = ("name", "l_value", "rows", "status")
        self.file_tree = ttk.Treeview(file_frame, columns=columns, show="headings", selectmode="extended", height=10)
        self.file_tree.heading("name", text="文件名")
        self.file_tree.heading("l_value", text="l")
        self.file_tree.heading("rows", text="行数")
        self.file_tree.heading("status", text="状态")
        self.file_tree.column("name", width=520, anchor="w")
        self.file_tree.column("l_value", width=70, anchor="center")
        self.file_tree.column("rows", width=90, anchor="center")
        self.file_tree.column("status", width=90, anchor="center")
        self.file_tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        tree_scroll = ttk.Scrollbar(file_frame, orient="vertical", command=self.file_tree.yview)
        tree_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.file_tree.configure(yscrollcommand=tree_scroll.set)

        file_button_frame = ttk.Frame(file_frame)
        file_button_frame.grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8))
        self.select_all_button = ttk.Button(file_button_frame, text="全选", command=self._select_all_files)
        self.select_all_button.grid(row=0, column=0, padx=(0, 6))
        self.clear_selection_button = ttk.Button(file_button_frame, text="清空选择", command=self._clear_file_selection)
        self.clear_selection_button.grid(row=0, column=1)

        output_frame = ttk.LabelFrame(self, text="输出目录")
        output_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        output_frame.columnconfigure(0, weight=1)
        ttk.Entry(output_frame, textvariable=self.output_dir_var).grid(row=0, column=0, sticky="ew", padx=(8, 6), pady=8)
        self.browse_output_button = ttk.Button(output_frame, text="浏览", command=self._browse_output_dir)
        self.browse_output_button.grid(row=0, column=1, padx=6, pady=8)
        self.open_output_button = ttk.Button(output_frame, text="打开输出目录", command=self._open_output_dir)
        self.open_output_button.grid(row=0, column=2, padx=(0, 8), pady=8)

        params_frame = ttk.LabelFrame(self, text="参数")
        params_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        params_frame.columnconfigure(1, weight=1)
        ttk.Label(params_frame, text="小干扰峰削减比例（%）").grid(row=0, column=0, sticky="w", padx=(8, 6), pady=8)
        ttk.Entry(params_frame, textvariable=self.reduction_percent_var, width=12).grid(row=0, column=1, sticky="w", pady=8)
        self.toggle_advanced_button = ttk.Button(
            params_frame,
            text="显示高级识别参数",
            command=self._toggle_advanced_params,
        )
        self.toggle_advanced_button.grid(row=0, column=2, sticky="e", padx=8, pady=8)

        self.advanced_frame = ttk.Frame(params_frame)
        advanced_items = list(self.param_vars.items())
        for idx, (name, var) in enumerate(advanced_items):
            row = idx // 2
            col = (idx % 2) * 2
            ttk.Label(self.advanced_frame, text=name).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=4)
            ttk.Entry(self.advanced_frame, textvariable=var, width=14).grid(row=row, column=col + 1, sticky="w", padx=(0, 16), pady=4)

        action_frame = ttk.Frame(self)
        action_frame.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        self.run_button = ttk.Button(action_frame, text="运行批处理", command=self._start_batch_run)
        self.run_button.grid(row=0, column=0, padx=(0, 6))
        self.exit_button = ttk.Button(action_frame, text="退出", command=self.master.destroy)
        self.exit_button.grid(row=0, column=1)

        log_frame = ttk.LabelFrame(self, text="运行日志")
        log_frame.grid(row=6, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, wrap="word", height=14, state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.log_text.configure(yscrollcommand=log_scroll.set)

    def _browse_input_dir(self) -> None:
        folder = filedialog.askdirectory(initialdir=self.input_dir_var.get().strip() or str(Path.cwd()))
        if folder:
            self.input_dir_var.set(folder)

    def _browse_output_dir(self) -> None:
        folder = filedialog.askdirectory(initialdir=self.output_dir_var.get().strip() or str(Path.cwd()))
        if folder:
            self.output_dir_var.set(folder)

    def _open_output_dir(self) -> None:
        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            messagebox.showwarning("缺少输出目录", "请先选择输出目录。")
            return
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(path)
        except Exception as exc:
            messagebox.showerror("打开失败", str(exc))

    def _toggle_advanced_params(self) -> None:
        if self.advanced_visible.get():
            self.advanced_frame.grid_remove()
            self.advanced_visible.set(False)
            self.toggle_advanced_button.config(text="显示高级识别参数")
        else:
            self.advanced_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 8))
            self.advanced_visible.set(True)
            self.toggle_advanced_button.config(text="隐藏高级识别参数")

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message.rstrip() + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _scan_folder(self) -> None:
        input_dir = Path(self.input_dir_var.get().strip())
        self._clear_log()
        self._populate_file_tree([])
        self.scanned_files.clear()

        try:
            valid_files, invalid_logs = scan_valid_csv_files(input_dir)
        except Exception as exc:
            messagebox.showerror("扫描失败", str(exc))
            return

        self._populate_file_tree(valid_files)
        self._append_log(f"[扫描] 目录: {input_dir}")
        self._append_log(f"[扫描] 发现可处理 CSV: {len(valid_files)} 个")
        for line in invalid_logs:
            self._append_log(line)
        if not valid_files:
            self._append_log("[提示] 当前目录没有找到包含 Lambda_aligned 和 Power_uW 的 CSV。")

    def _populate_file_tree(self, scanned_files: list[ScannedCsvInfo]) -> None:
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.scanned_files.clear()

        for idx, info in enumerate(scanned_files):
            item_id = f"csv_{idx}"
            self.scanned_files[item_id] = info
            l_display = "" if info.l_value is None else str(info.l_value)
            self.file_tree.insert("", "end", iid=item_id, values=(info.name, l_display, info.rows, info.status))

    def _select_all_files(self) -> None:
        item_ids = self.file_tree.get_children()
        self.file_tree.selection_set(item_ids)

    def _clear_file_selection(self) -> None:
        self.file_tree.selection_remove(self.file_tree.selection())

    def _collect_detection_params(self) -> dict[str, int | float]:
        params: dict[str, int | float] = {}
        int_fields = {"smooth_window", "smooth_polyorder", "distance_points", "main_family_count"}
        for name, var in self.param_vars.items():
            raw = var.get().strip()
            if raw == "":
                raise ValueError(f"高级参数 {name} 不能为空。")
            params[name] = int(raw) if name in int_fields else float(raw)
        return params

    def _start_batch_run(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo("处理中", "当前批处理还在运行，请稍等。")
            return

        selected_ids = list(self.file_tree.selection())
        if not selected_ids:
            messagebox.showwarning("未选择文件", "请先在列表中手动选择至少一个 CSV。")
            return

        input_dir_raw = self.input_dir_var.get().strip()
        output_dir_raw = self.output_dir_var.get().strip()
        if not input_dir_raw:
            messagebox.showwarning("输入目录无效", "请输入有效的输入目录。")
            return
        if not output_dir_raw:
            messagebox.showwarning("输出目录无效", "请输入有效的输出目录。")
            return

        input_dir = Path(input_dir_raw)
        output_dir = Path(output_dir_raw)
        if not input_dir.exists():
            messagebox.showwarning("输入目录无效", "请输入有效的输入目录。")
            return

        try:
            reduction_percent = float(self.reduction_percent_var.get().strip())
        except ValueError:
            messagebox.showwarning("比例无效", "削减比例必须是数字。")
            return
        if not (0.0 <= reduction_percent <= 100.0):
            messagebox.showwarning("比例无效", "削减比例必须在 0 到 100 之间。")
            return

        try:
            detection_params = self._collect_detection_params()
        except Exception as exc:
            messagebox.showwarning("参数无效", str(exc))
            return

        output_dir.mkdir(parents=True, exist_ok=True)
        selected_files = [self.scanned_files[item_id] for item_id in selected_ids if item_id in self.scanned_files]
        self._set_running_state(True)
        self._append_log(f"[开始] 选中 {len(selected_files)} 个文件，输出目录: {output_dir}")

        self.worker_thread = threading.Thread(
            target=self._run_batch_worker,
            args=(selected_files, output_dir, reduction_percent / 100.0, detection_params),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_batch_worker(
        self,
        selected_files: list[ScannedCsvInfo],
        output_dir: Path,
        reduction_frac: float,
        detection_params: dict[str, int | float],
    ) -> None:
        success_count = 0
        failure_count = 0
        for index, file_info in enumerate(selected_files, start=1):
            self.log_queue.put(("log", f"[处理中 {index}/{len(selected_files)}] {file_info.name}"))
            try:
                result = process_single_csv(
                    input_csv=file_info.path,
                    output_dir=output_dir,
                    reduction_frac=reduction_frac,
                    export_reference_tables=False,
                    **detection_params,
                )
                info = result["info"]
                stats = result["stats"]
                self.log_queue.put(
                    (
                        "log",
                        "[成功] {name} | λ={lam:.12f} nm | 原峰={old:.6f} uW | 新峰={new:.6f} uW | 修改点数={count} | 输出={out}".format(
                            name=file_info.name,
                            lam=info["target_lambda_nm"],
                            old=stats["old_peak_uW"],
                            new=stats["new_peak_uW"],
                            count=stats["modified_point_count"],
                            out=result["output_csv"],
                        ),
                    )
                )
                success_count += 1
            except Exception as exc:
                self.log_queue.put(("log", f"[失败] {file_info.name}: {exc}"))
                failure_count += 1

        self.log_queue.put(("done", {"success": success_count, "failure": failure_count, "output_dir": output_dir}))

    def _set_running_state(self, is_running: bool) -> None:
        state = "disabled" if is_running else "normal"
        for widget in (
            self.browse_input_button,
            self.scan_button,
            self.select_all_button,
            self.clear_selection_button,
            self.browse_output_button,
            self.open_output_button,
            self.toggle_advanced_button,
            self.run_button,
            self.exit_button,
        ):
            widget.config(state=state)

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.log_queue.get_nowait()
                if kind == "log":
                    self._append_log(str(payload))
                elif kind == "done":
                    self._set_running_state(False)
                    success = int(payload["success"])
                    failure = int(payload["failure"])
                    output_dir = payload["output_dir"]
                    self._append_log(f"[完成] 成功 {success} 个，失败 {failure} 个。")
                    messagebox.showinfo("批处理完成", f"成功 {success} 个，失败 {failure} 个。\n输出目录：{output_dir}")
        except queue.Empty:
            pass
        finally:
            self.after(150, self._poll_queue)


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    elif "clam" in style.theme_names():
        style.theme_use("clam")
    BatchReductionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
