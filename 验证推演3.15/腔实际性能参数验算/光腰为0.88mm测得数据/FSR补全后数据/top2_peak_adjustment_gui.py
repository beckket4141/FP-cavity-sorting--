from __future__ import annotations

import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, str(Path(__file__).parent))

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from identify_top2_peaks import (
    DEFAULT_DETECTION_PARAMS,
    DEFAULT_REDUCTION_FRAC,
    candidate_labels,
    draw_selection_axes,
    load_detection_context,
    reduce_candidate_peak,
    reset_all_reductions,
    save_reduction_outputs,
    selections_to_frame,
    set_active_candidate,
    step_active_candidate,
)


class PeakReductionBrowserApp(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=10)
        self.master = master
        self.master.title("CSV 峰整体调低工具")
        self.master.minsize(1260, 860)
        self.grid(sticky="nsew")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        self.rowconfigure(6, weight=1)

        self.context: dict[str, object] | None = None
        self.advanced_visible = tk.BooleanVar(value=False)
        self._updating_tree = False

        self.input_csv_var = tk.StringVar(value="")
        self.output_dir_var = tk.StringVar(value=str(Path.cwd()))
        self.output_name_var = tk.StringVar(value="")
        self.reduction_percent_var = tk.StringVar(value=f"{DEFAULT_REDUCTION_FRAC * 100:.0f}")
        self.active_peak_var = tk.StringVar(value="当前未选择峰")

        self.param_vars: dict[str, tk.StringVar] = {
            name: tk.StringVar(value=str(value))
            for name, value in DEFAULT_DETECTION_PARAMS.items()
        }

        self._build_ui()
        self._refresh_tree()
        self._redraw_plot()

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
        ttk.Label(output_frame, text="输出 CSV 名称").grid(row=1, column=0, sticky="w", padx=(8, 6), pady=(0, 4))
        ttk.Entry(output_frame, textvariable=self.output_name_var).grid(row=2, column=0, sticky="ew", padx=(8, 6), pady=(0, 8))

        params_frame = ttk.LabelFrame(self, text="调低参数")
        params_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(params_frame, text="峰整体调低比例(%)").grid(row=0, column=0, sticky="w", padx=(8, 6), pady=8)
        ttk.Entry(params_frame, textvariable=self.reduction_percent_var, width=10).grid(row=0, column=1, sticky="w", pady=8)
        self.toggle_advanced_button = ttk.Button(
            params_frame,
            text="显示高级识别参数",
            command=self._toggle_advanced_params,
        )
        self.toggle_advanced_button.grid(row=0, column=2, sticky="e", padx=8, pady=8)

        self.advanced_frame = ttk.Frame(params_frame)
        for idx, (name, var) in enumerate(self.param_vars.items()):
            row = idx // 2
            col = (idx % 2) * 2
            ttk.Label(self.advanced_frame, text=name).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=4)
            ttk.Entry(self.advanced_frame, textvariable=var, width=14).grid(row=row, column=col + 1, sticky="w", padx=(0, 16), pady=4)

        browse_frame = ttk.LabelFrame(self, text="峰浏览")
        browse_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(browse_frame, text="上一个峰", command=lambda: self._move_active_peak(-1)).grid(
            row=0, column=0, padx=(8, 6), pady=8, sticky="w"
        )
        ttk.Button(browse_frame, text="下一个峰", command=lambda: self._move_active_peak(1)).grid(
            row=0, column=1, padx=6, pady=8, sticky="w"
        )
        ttk.Label(browse_frame, textvariable=self.active_peak_var).grid(row=0, column=2, padx=(18, 8), pady=8, sticky="w")

        result_frame = ttk.LabelFrame(self, text="已检测峰列表")
        result_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 8))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        columns = ("rank", "active", "lambda_nm", "raw_uW", "smooth_uW", "mode")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", selectmode="browse", height=8)
        self.result_tree.heading("rank", text="排序")
        self.result_tree.heading("active", text="当前")
        self.result_tree.heading("lambda_nm", text="当前波长 (nm)")
        self.result_tree.heading("raw_uW", text="当前功率 (uW)")
        self.result_tree.heading("smooth_uW", text="平滑功率 (uW)")
        self.result_tree.heading("mode", text="最近操作")
        self.result_tree.column("rank", width=90, anchor="center")
        self.result_tree.column("active", width=80, anchor="center")
        self.result_tree.column("lambda_nm", width=240, anchor="center")
        self.result_tree.column("raw_uW", width=170, anchor="center")
        self.result_tree.column("smooth_uW", width=170, anchor="center")
        self.result_tree.column("mode", width=220, anchor="center")
        self.result_tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        self.result_tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        tree_scroll = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_tree.yview)
        tree_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.result_tree.configure(yscrollcommand=tree_scroll.set)

        action_frame = ttk.LabelFrame(self, text="当前选中峰操作")
        action_frame.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(action_frame, text="调低当前峰", command=self._reduce_active_peak).grid(
            row=0, column=0, padx=(8, 6), pady=8, sticky="w"
        )
        ttk.Button(action_frame, text="全部重置", command=self._reset_all_peaks).grid(
            row=0, column=1, padx=6, pady=8, sticky="w"
        )
        ttk.Button(action_frame, text="保存结果", command=self._save_outputs).grid(
            row=0, column=2, padx=6, pady=8, sticky="w"
        )

        plot_frame = ttk.LabelFrame(self, text="曲线预览")
        plot_frame.grid(row=6, column=0, sticky="nsew", pady=(0, 8))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)

        self.figure = Figure(figsize=(10.8, 4.8), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=0.06, right=0.985, top=0.90, bottom=0.22)
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        log_frame = ttk.LabelFrame(self, text="日志")
        log_frame.grid(row=7, column=0, sticky="nsew")
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
            self.output_name_var.set(f"{Path(file_path).stem}_selected_peak_reduced.csv")

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

    def _reduction_frac(self) -> float:
        try:
            reduction_percent = float(self.reduction_percent_var.get().strip())
        except ValueError as exc:
            raise ValueError("调低比例必须是数字。") from exc
        if not (0.0 <= reduction_percent <= 100.0):
            raise ValueError("调低比例必须在 0 到 100 之间。")
        return reduction_percent / 100.0

    def _active_label(self) -> str:
        if self.context is None:
            raise RuntimeError("请先加载并识别一个 CSV。")
        return str(self.context["active_label"])

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
            if not self.output_name_var.get().strip():
                self.output_name_var.set(f"{csv_path.stem}_selected_peak_reduced.csv")
            self._clear_log()
            self._append_log(f"[识别] 输入文件: {csv_path.resolve()}")
            self._append_log(f"[识别] 共检测到 {len(candidate_labels(self.context))} 个峰候选。")
            self._append_log("[提示] 默认选中第 1 高峰，可以点“下一个峰”继续浏览。")
            self._refresh_tree()
            self._redraw_plot()
        except Exception as exc:
            messagebox.showerror("识别失败", str(exc))

    def _set_active_peak_text(self) -> None:
        if self.context is None:
            self.active_peak_var.set("当前未选择峰")
            return
        df = selections_to_frame(self.context)
        active_rows = df.loc[df["is_active"] == 1]
        if active_rows.empty:
            self.active_peak_var.set("当前未选择峰")
            return
        row = active_rows.iloc[0]
        self.active_peak_var.set(
            "当前峰: 第{rank}高峰 | λ={lam:.12f} nm | 当前功率={raw:.6f} uW | 平滑={smooth:.6f} uW".format(
                rank=int(row["rank"]),
                lam=float(row["current_lambda_nm"]),
                raw=float(row["power_raw_uW"]),
                smooth=float(row["power_smooth_uW"]),
            )
        )

    def _move_active_peak(self, step: int) -> None:
        if self.context is None:
            messagebox.showwarning("尚未识别", "请先加载并识别一个 CSV。")
            return
        candidate = step_active_candidate(self.context, step)
        self._refresh_tree(selected_label=candidate.label)
        self._redraw_plot()
        self._append_log(f"[浏览] 切换到第 {candidate.rank} 高峰。")

    def _reduce_active_peak(self) -> None:
        if self.context is None:
            messagebox.showwarning("尚未识别", "请先加载并识别一个 CSV。")
            return
        try:
            label = self._active_label()
            report = reduce_candidate_peak(self.context, label, self._reduction_frac())
            self._refresh_tree(selected_label=self._active_label())
            self._redraw_plot()
            self._append_log(
                "[调低] λ={lam:.12f} nm | old={old:.6f} uW | new={new:.6f} uW | modified_points={count}".format(
                    lam=float(report["target_lambda_nm"]),
                    old=float(report["old_peak_uW"]),
                    new=float(report["new_peak_uW"]),
                    count=int(report["modified_point_count"]),
                )
            )
        except Exception as exc:
            messagebox.showerror("调低失败", str(exc))

    def _reset_all_peaks(self) -> None:
        if self.context is None:
            messagebox.showwarning("尚未识别", "请先加载并识别一个 CSV。")
            return
        try:
            reset_all_reductions(self.context)
            self._refresh_tree()
            self._redraw_plot()
            self._append_log("[重置] 已恢复到初始曲线。")
        except Exception as exc:
            messagebox.showerror("重置失败", str(exc))

    def _save_outputs(self) -> None:
        if self.context is None:
            messagebox.showwarning("尚未识别", "请先加载并识别一个 CSV。")
            return
        try:
            output_dir = Path(self.output_dir_var.get().strip() or Path.cwd())
            output_name = self.output_name_var.get().strip()
            if not output_name:
                raise ValueError("请先填写输出 CSV 名称。")
            outputs = save_reduction_outputs(self.context, output_dir=output_dir, output_name=output_name)
            self.output_dir_var.set(str(output_dir.resolve()))
            self._append_log(f"[保存] output_csv: {outputs['output_csv']}")
            self._append_log(f"[保存] summary_txt: {outputs['summary_txt']}")
            self._append_log(f"[保存] plot_png: {outputs['plot_png']}")
            messagebox.showinfo("保存完成", f"结果已保存到:\n{output_dir.resolve()}")
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    def _refresh_tree(self, selected_label: str | None = None) -> None:
        self._updating_tree = True
        try:
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)

            if self.context is None:
                self._set_active_peak_text()
                return

            df = selections_to_frame(self.context)
            for _, row in df.iterrows():
                label = str(row["label"])
                self.result_tree.insert(
                    "",
                    "end",
                    iid=label,
                    values=(
                        f"第 {int(row['rank'])} 高峰",
                        "是" if int(row["is_active"]) == 1 else "",
                        f"{float(row['current_lambda_nm']):.12f}",
                        f"{float(row['power_raw_uW']):.6f}",
                        f"{float(row['power_smooth_uW']):.6f}",
                        str(row["adjustment_mode"]),
                    ),
                )

            target_selection = selected_label if selected_label in self.result_tree.get_children() else self._active_label()
            if target_selection in self.result_tree.get_children():
                self.result_tree.selection_set(target_selection)
                self.result_tree.focus(target_selection)

            self._set_active_peak_text()
        finally:
            self._updating_tree = False

    def _redraw_plot(self) -> None:
        self.ax.clear()
        if self.context is None:
            self.ax.set_title("请先选择并识别一个 CSV")
            self.ax.set_xlabel("Lambda_aligned (nm)")
            self.ax.set_ylabel("Power_uW")
            self.ax.grid(alpha=0.2)
        else:
            draw_selection_axes(self.ax, self.context)
        self.canvas.draw_idle()

    def _on_tree_select(self, _event: object) -> None:
        if self.context is None or self._updating_tree:
            return
        selection = self.result_tree.selection()
        if not selection:
            return
        label = str(selection[0])
        if label == self._active_label():
            return
        set_active_candidate(self.context, label)
        self._refresh_tree(selected_label=label)
        self._redraw_plot()


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    elif "clam" in style.theme_names():
        style.theme_use("clam")
    PeakReductionBrowserApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
