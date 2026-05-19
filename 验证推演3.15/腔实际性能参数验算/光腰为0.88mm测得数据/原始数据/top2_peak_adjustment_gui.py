from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from identify_top2_peaks import (
    DEFAULT_DETECTION_PARAMS,
    draw_selection_axes,
    load_detection_context,
    refine_selection_to_local_max,
    reset_selection,
    save_selection_outputs,
    selections_to_frame,
    shift_selection,
)


class Top2PeakAdjustmentApp(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=10)
        self.master = master
        self.master.title("CSV 前两高峰识别与微调工具")
        self.master.minsize(1180, 820)
        self.grid(sticky="nsew")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        self.rowconfigure(5, weight=1)

        self.context: dict[str, object] | None = None
        self.advanced_visible = tk.BooleanVar(value=False)

        self.input_csv_var = tk.StringVar(value="")
        self.output_dir_var = tk.StringVar(value=str(Path.cwd()))
        self.step_points_var = tk.StringVar(value="1")
        self.refine_window_var = tk.StringVar(value="4")

        self.param_vars: dict[str, tk.StringVar] = {
            name: tk.StringVar(value=str(value))
            for name, value in DEFAULT_DETECTION_PARAMS.items()
        }

        self._build_ui()
        self._refresh_tree()

    def _build_ui(self) -> None:
        input_frame = ttk.LabelFrame(self, text="输入 CSV")
        input_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        input_frame.columnconfigure(0, weight=1)
        ttk.Entry(input_frame, textvariable=self.input_csv_var).grid(row=0, column=0, sticky="ew", padx=(8, 6), pady=8)
        ttk.Button(input_frame, text="浏览", command=self._browse_input_csv).grid(row=0, column=1, padx=6, pady=8)
        ttk.Button(input_frame, text="自动识别", command=self._load_and_identify).grid(row=0, column=2, padx=(0, 8), pady=8)

        output_frame = ttk.LabelFrame(self, text="输出目录")
        output_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        output_frame.columnconfigure(0, weight=1)
        ttk.Entry(output_frame, textvariable=self.output_dir_var).grid(row=0, column=0, sticky="ew", padx=(8, 6), pady=8)
        ttk.Button(output_frame, text="浏览", command=self._browse_output_dir).grid(row=0, column=1, padx=6, pady=8)
        ttk.Button(output_frame, text="打开目录", command=self._open_output_dir).grid(row=0, column=2, padx=(0, 8), pady=8)

        params_frame = ttk.LabelFrame(self, text="微调参数")
        params_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(params_frame, text="左右移动步长(点)").grid(row=0, column=0, sticky="w", padx=(8, 6), pady=8)
        ttk.Entry(params_frame, textvariable=self.step_points_var, width=10).grid(row=0, column=1, sticky="w", pady=8)
        ttk.Label(params_frame, text="局部重找半宽(点)").grid(row=0, column=2, sticky="w", padx=(16, 6), pady=8)
        ttk.Entry(params_frame, textvariable=self.refine_window_var, width=10).grid(row=0, column=3, sticky="w", pady=8)
        self.toggle_advanced_button = ttk.Button(
            params_frame,
            text="显示高级识别参数",
            command=self._toggle_advanced_params,
        )
        self.toggle_advanced_button.grid(row=0, column=4, sticky="e", padx=8, pady=8)

        self.advanced_frame = ttk.Frame(params_frame)
        for idx, (name, var) in enumerate(self.param_vars.items()):
            row = idx // 2
            col = (idx % 2) * 2
            ttk.Label(self.advanced_frame, text=name).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=4)
            ttk.Entry(self.advanced_frame, textvariable=var, width=14).grid(row=row, column=col + 1, sticky="w", padx=(0, 16), pady=4)

        result_frame = ttk.LabelFrame(self, text="当前识别结果")
        result_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        columns = ("label", "lambda_nm", "raw_uW", "smooth_uW", "offset", "mode")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", selectmode="browse", height=3)
        self.result_tree.heading("label", text="峰")
        self.result_tree.heading("lambda_nm", text="当前波长 (nm)")
        self.result_tree.heading("raw_uW", text="原始功率 (uW)")
        self.result_tree.heading("smooth_uW", text="平滑功率 (uW)")
        self.result_tree.heading("offset", text="偏移点数")
        self.result_tree.heading("mode", text="调整方式")
        self.result_tree.column("label", width=150, anchor="center")
        self.result_tree.column("lambda_nm", width=200, anchor="center")
        self.result_tree.column("raw_uW", width=150, anchor="center")
        self.result_tree.column("smooth_uW", width=150, anchor="center")
        self.result_tree.column("offset", width=120, anchor="center")
        self.result_tree.column("mode", width=220, anchor="center")
        self.result_tree.grid(row=0, column=0, sticky="ew", padx=(8, 0), pady=8)

        tree_scroll = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_tree.yview)
        tree_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.result_tree.configure(yscrollcommand=tree_scroll.set)

        action_frame = ttk.LabelFrame(self, text="操作")
        action_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 8))
        action_frame.columnconfigure(0, weight=1)
        action_frame.rowconfigure(0, weight=1)
        ttk.Button(action_frame, text="左移选中峰", command=lambda: self._shift_selected_peak(-1)).grid(
            row=0, column=0, padx=(8, 6), pady=8, sticky="w"
        )
        ttk.Button(action_frame, text="右移选中峰", command=lambda: self._shift_selected_peak(1)).grid(
            row=0, column=1, padx=6, pady=8, sticky="w"
        )
        ttk.Button(action_frame, text="局部最高点微调", command=self._refine_selected_peak).grid(
            row=0, column=2, padx=6, pady=8, sticky="w"
        )
        ttk.Button(action_frame, text="重置选中峰", command=self._reset_selected_peak).grid(
            row=0, column=3, padx=6, pady=8, sticky="w"
        )
        ttk.Button(action_frame, text="全部重置", command=self._reset_all_peaks).grid(
            row=0, column=4, padx=6, pady=8, sticky="w"
        )
        ttk.Button(action_frame, text="保存结果", command=self._save_outputs).grid(
            row=0, column=5, padx=6, pady=8, sticky="w"
        )

        plot_frame = ttk.LabelFrame(self, text="曲线预览")
        plot_frame.grid(row=5, column=0, sticky="nsew", pady=(0, 8))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)

        self.figure = Figure(figsize=(10.5, 4.8), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        log_frame = ttk.LabelFrame(self, text="日志")
        log_frame.grid(row=6, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, height=8, wrap="word", state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.log_text.configure(yscrollcommand=log_scroll.set)

    def _browse_input_csv(self) -> None:
        file_path = filedialog.askopenfilename(
            title="选择 CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=self._safe_initial_dir(self.input_csv_var.get()),
        )
        if file_path:
            self.input_csv_var.set(file_path)
            self.output_dir_var.set(str(Path(file_path).resolve().parent))

    def _browse_output_dir(self) -> None:
        folder = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=self._safe_initial_dir(self.output_dir_var.get()),
        )
        if folder:
            self.output_dir_var.set(folder)

    def _open_output_dir(self) -> None:
        output_dir = Path(self.output_dir_var.get().strip() or Path.cwd())
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(output_dir)
        except Exception as exc:
            messagebox.showerror("打开失败", str(exc))

    def _toggle_advanced_params(self) -> None:
        if self.advanced_visible.get():
            self.advanced_frame.grid_remove()
            self.advanced_visible.set(False)
            self.toggle_advanced_button.config(text="显示高级识别参数")
        else:
            self.advanced_frame.grid(row=1, column=0, columnspan=5, sticky="ew", padx=8, pady=(0, 8))
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

    @staticmethod
    def _safe_initial_dir(value: str) -> str:
        raw = value.strip()
        if not raw:
            return str(Path.cwd())
        path = Path(raw)
        return str(path if path.exists() else Path.cwd())

    def _collect_detection_params(self) -> dict[str, int | float]:
        params: dict[str, int | float] = {}
        int_fields = {"smooth_window", "smooth_polyorder", "distance_points", "main_family_count"}
        for name, var in self.param_vars.items():
            raw = var.get().strip()
            if raw == "":
                raise ValueError(f"参数 {name} 不能为空。")
            params[name] = int(raw) if name in int_fields else float(raw)
        return params

    def _load_and_identify(self) -> None:
        csv_raw = self.input_csv_var.get().strip()
        if not csv_raw:
            messagebox.showwarning("缺少输入", "请先选择一个 CSV 文件。")
            return

        csv_path = Path(csv_raw)
        if not csv_path.exists():
            messagebox.showwarning("文件不存在", f"未找到文件:\n{csv_path}")
            return

        try:
            detection_params = self._collect_detection_params()
            output_dir = Path(self.output_dir_var.get().strip() or csv_path.parent)
            self.context = load_detection_context(
                input_csv=csv_path,
                output_dir=output_dir,
                **detection_params,
            )
            self.output_dir_var.set(str(output_dir.resolve()))
            self._clear_log()
            self._append_log(f"[识别] 输入文件: {csv_path.resolve()}")
            for _, row in selections_to_frame(self.context).iterrows():
                self._append_log(
                    "[识别] {label}: lambda={lam:.12f} nm | raw={raw:.6f} uW | smooth={smooth:.6f} uW".format(
                        label=row["label"],
                        lam=float(row["current_lambda_nm"]),
                        raw=float(row["power_raw_uW"]),
                        smooth=float(row["power_smooth_uW"]),
                    )
                )
            self._refresh_tree()
            self._redraw_plot()
        except Exception as exc:
            messagebox.showerror("识别失败", str(exc))

    def _selected_label(self) -> str:
        selection = self.result_tree.selection()
        if not selection:
            raise RuntimeError("请先在结果表中选中一个峰。")
        return str(selection[0])

    def _step_points(self) -> int:
        try:
            step = int(self.step_points_var.get().strip())
        except ValueError as exc:
            raise ValueError("左右移动步长必须是整数。") from exc
        if step < 1:
            raise ValueError("左右移动步长必须至少为 1。")
        return step

    def _refine_window_points(self) -> int:
        try:
            window = int(self.refine_window_var.get().strip())
        except ValueError as exc:
            raise ValueError("局部重找半宽必须是整数。") from exc
        if window < 1:
            raise ValueError("局部重找半宽必须至少为 1。")
        return window

    def _shift_selected_peak(self, direction: int) -> None:
        if self.context is None:
            messagebox.showwarning("尚未识别", "请先加载并识别一个 CSV。")
            return
        try:
            label = self._selected_label()
            shift_selection(self.context, label, direction * self._step_points())
            self._refresh_tree(selected_label=label)
            self._redraw_plot()
            row = selections_to_frame(self.context).set_index("label").loc[label]
            self._append_log(
                f"[微调] {label}: current_lambda={float(row['current_lambda_nm']):.12f} nm | mode={row['adjustment_mode']}"
            )
        except Exception as exc:
            messagebox.showerror("微调失败", str(exc))

    def _refine_selected_peak(self) -> None:
        if self.context is None:
            messagebox.showwarning("尚未识别", "请先加载并识别一个 CSV。")
            return
        try:
            label = self._selected_label()
            refine_selection_to_local_max(self.context, label, self._refine_window_points())
            self._refresh_tree(selected_label=label)
            self._redraw_plot()
            row = selections_to_frame(self.context).set_index("label").loc[label]
            self._append_log(
                f"[微调] {label}: current_lambda={float(row['current_lambda_nm']):.12f} nm | mode={row['adjustment_mode']}"
            )
        except Exception as exc:
            messagebox.showerror("微调失败", str(exc))

    def _reset_selected_peak(self) -> None:
        if self.context is None:
            messagebox.showwarning("尚未识别", "请先加载并识别一个 CSV。")
            return
        try:
            label = self._selected_label()
            reset_selection(self.context, label)
            self._refresh_tree(selected_label=label)
            self._redraw_plot()
            self._append_log(f"[重置] {label} 已恢复到自动识别位置。")
        except Exception as exc:
            messagebox.showerror("重置失败", str(exc))

    def _reset_all_peaks(self) -> None:
        if self.context is None:
            messagebox.showwarning("尚未识别", "请先加载并识别一个 CSV。")
            return
        try:
            for label in ("highest_peak", "second_highest_peak"):
                reset_selection(self.context, label)
            self._refresh_tree()
            self._redraw_plot()
            self._append_log("[重置] 两个峰都已恢复到自动识别位置。")
        except Exception as exc:
            messagebox.showerror("重置失败", str(exc))

    def _save_outputs(self) -> None:
        if self.context is None:
            messagebox.showwarning("尚未识别", "请先加载并识别一个 CSV。")
            return

        try:
            output_dir = Path(self.output_dir_var.get().strip() or Path.cwd())
            outputs = save_selection_outputs(self.context, output_dir=output_dir)
            self.output_dir_var.set(str(output_dir.resolve()))
            self._append_log(f"[保存] selected_csv: {outputs['selected_csv']}")
            self._append_log(f"[保存] marked_trace_csv: {outputs['marked_trace_csv']}")
            self._append_log(f"[保存] summary_json: {outputs['summary_json']}")
            self._append_log(f"[保存] plot_png: {outputs['plot_png']}")
            messagebox.showinfo("保存完成", f"结果已保存到:\n{output_dir.resolve()}")
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    def _refresh_tree(self, selected_label: str | None = None) -> None:
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        if self.context is None:
            return

        df = selections_to_frame(self.context)
        for _, row in df.iterrows():
            label = str(row["label"])
            display_label = "最高峰" if label == "highest_peak" else "第二高峰"
            self.result_tree.insert(
                "",
                "end",
                iid=label,
                values=(
                    display_label,
                    f"{float(row['current_lambda_nm']):.12f}",
                    f"{float(row['power_raw_uW']):.6f}",
                    f"{float(row['power_smooth_uW']):.6f}",
                    str(int(row["index_offset_points"])),
                    str(row["adjustment_mode"]),
                ),
            )

        target_selection = selected_label if selected_label in self.result_tree.get_children() else "highest_peak"
        if target_selection in self.result_tree.get_children():
            self.result_tree.selection_set(target_selection)
            self.result_tree.focus(target_selection)

    def _redraw_plot(self) -> None:
        self.ax.clear()
        if self.context is None:
            self.ax.set_title("请先选择并识别一个 CSV")
            self.ax.set_xlabel("Lambda_aligned (nm)")
            self.ax.set_ylabel("Power_uW")
            self.ax.grid(alpha=0.2)
        else:
            draw_selection_axes(self.ax, self.context)
        self.figure.tight_layout()
        self.canvas.draw_idle()


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    elif "clam" in style.theme_names():
        style.theme_use("clam")
    Top2PeakAdjustmentApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
