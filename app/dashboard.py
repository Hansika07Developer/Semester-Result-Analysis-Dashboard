from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .data_processing import REQUIRED_COLUMNS, clean_results, kpis, student_overview, student_summary
from .charts import grade_chart, histogram_chart, scatter_chart, semester_chart, subject_chart

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA = BASE_DIR / "data" / "sample_results.csv"


class _HeadlessVar:
    def __init__(self, value=""):
        self._value = value

    def set(self, value):
        self._value = value

    def get(self):
        return self._value

    def trace_add(self, *_args, **_kwargs):
        return None


class DashboardApp:
    def __init__(self, root=None):
        self.root = root
        if self.root is None:
            try:
                self.root = tk.Tk()
            except tk.TclError:
                self.root = None
        if self.root is not None:
            self.root.title("Semester Result Analysis Dashboard")
            self.root.geometry("1920x1200")
            self.root.minsize(1440, 960)
            self.root.state("zoomed")
        self.raw = pd.DataFrame()
        self.filtered = pd.DataFrame()
        self.dataset_name = ""
        self.source_files = []
        self.figure = None
        self.canvas = None
        self.search_var = _HeadlessVar()
        self.semester_var = _HeadlessVar("All")
        self.section_var = _HeadlessVar("All")
        self.chart_var = _HeadlessVar("Grade Distribution")
        self.context_var = _HeadlessVar("Load a CSV file to view results.")
        self.dataset_var = _HeadlessVar("Loading sample results…")
        self.student_count_var = _HeadlessVar("0 students")
        self.chart_description_var = _HeadlessVar()
        self.kpi_vars = {
            key: _HeadlessVar("-")
            for key in ["students", "passed", "average", "pass_rate"]
        }
        self.insight_vars = {
            key: _HeadlessVar("-")
            for key in ["leaders", "subjects", "grades", "semesters", "attendance", "attention"]
        }
        if self.root is not None:
            self._build_ui()
        if DEFAULT_DATA.exists():
            self.load_file(DEFAULT_DATA)

    def _build_ui(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background="#F3F6FA")
        style.configure("Sidebar.TFrame", background="#172B3A")
        style.configure("Panel.TFrame", background="#FFFFFF", relief="solid", borderwidth=1)
        style.configure("TLabel", background="#F3F6FA", foreground="#263746", font=("Segoe UI", 17))
        style.configure("Title.TLabel", background="#F3F6FA", foreground="#18324B",
                        font=("Segoe UI", 21, "bold"))
        style.configure("Subtitle.TLabel", background="#F3F6FA", foreground="#708090",
                        font=("Segoe UI", 17))
        style.configure("Section.TLabel", background="#F3F6FA", foreground="#18324B",
                        font=("Segoe UI", 21, "bold"))
        style.configure("Muted.TLabel", background="#F3F6FA", foreground="#708090",
                        font=("Segoe UI", 17))
        style.configure("PanelSection.TLabel", background="#FFFFFF", foreground="#18324B",
                        font=("Segoe UI", 21, "bold"))
        style.configure("PanelMuted.TLabel", background="#FFFFFF", foreground="#708090",
                        font=("Segoe UI", 17))
        style.configure("SideBrand.TLabel", background="#172B3A", foreground="#FFFFFF",
                        font=("Segoe UI", 21, "bold"))
        style.configure("SideEyebrow.TLabel", background="#172B3A", foreground="#94A8B7",
                        font=("Segoe UI", 17, "bold"))
        style.configure("SideLabel.TLabel", background="#172B3A", foreground="#E3EBF0",
                        font=("Segoe UI", 21, "bold"))
        style.configure("SideNote.TLabel", background="#172B3A", foreground="#94A8B7",
                        font=("Segoe UI", 17))
        style.configure("Card.TFrame", background="#FFFFFF", relief="solid", borderwidth=1)
        style.configure("CardLabel.TLabel", background="#FFFFFF", foreground="#708090",
                        font=("Segoe UI", 21, "bold"))
        style.configure("CardValue.TLabel", background="#FFFFFF", foreground="#18324B",
                        font=("Segoe UI", 21, "bold"))
        style.configure("CardHint.TLabel", background="#FFFFFF", foreground="#708090",
                        font=("Segoe UI", 17))
        style.configure("InsightTitle.TLabel", background="#FFFFFF", foreground="#18324B",
                        font=("Segoe UI", 21, "bold"))
        style.configure("InsightBody.TLabel", background="#FFFFFF", foreground="#526575",
                        font=("Segoe UI", 17))
        style.configure("Accent.TButton", font=("Segoe UI", 19, "bold"), padding=(13, 10),
                        background="#256A91", foreground="#FFFFFF", borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#1D5879")])
        style.configure("TButton", font=("Segoe UI", 19), padding=(11, 9))
        style.configure("Side.TButton", font=("Segoe UI", 19, "bold"), padding=(11, 9),
                        background="#263F50", foreground="#FFFFFF", borderwidth=0)
        style.map("Side.TButton", background=[("active", "#314F63")])
        style.configure("TCombobox", padding=14, fieldbackground="#FFFFFF", font=("Segoe UI", 22))
        style.configure("TEntry", padding=12, font=("Segoe UI", 21))
        style.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground="#263746", rowheight=52, font=("Segoe UI", 17), borderwidth=0)
        style.configure("Treeview.Heading", background="#F2F5F8", foreground="#526575",
                        font=("Segoe UI", 21, "bold"), padding=(9, 9), relief="flat")
        style.map("Treeview", background=[("selected", "#DCEAF4")],
                  foreground=[("selected", "#18324B")])
        style.configure("Vertical.TScrollbar", background="#EAF0F5", troughcolor="#FFFFFF")
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 20))
        self.root.option_add("*TCombobox*Listbox.selectBackground", "#DCEAF4")
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#18324B")

        self.root.configure(background="#F3F6FA")
        shell = ttk.Frame(self.root)
        shell.pack(fill="both", expand=True)
        sidebar = ttk.Frame(shell, style="Sidebar.TFrame", width=390, padding=(28, 32))
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        ttk.Label(sidebar, text="ACADEMIC INSIGHTS", style="SideEyebrow.TLabel").pack(anchor="w")
        ttk.Label(sidebar, text="Semester\nResults", style="SideBrand.TLabel",
                  justify="left").pack(anchor="w", pady=(8, 30))
        ttk.Label(sidebar, text="DASHBOARD", style="SideEyebrow.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(sidebar, text="◉   Performance overview", style="SideLabel.TLabel",
                  padding=(10, 10)).pack(fill="x", pady=(0, 26))
        ttk.Label(sidebar, text="FILTER RESULTS", style="SideEyebrow.TLabel").pack(anchor="w", pady=(0, 14))
        self.semester_var = tk.StringVar(value="All")
        self.section_var = tk.StringVar(value="All")
        ttk.Label(sidebar, text="Semester", style="SideLabel.TLabel").pack(anchor="w", pady=(0, 6))
        self.semester_box = ttk.Combobox(
            sidebar, textvariable=self.semester_var, state="readonly", height=10
        )
        self.semester_box.pack(fill="x", pady=(0, 14))
        ttk.Label(sidebar, text="Section", style="SideLabel.TLabel").pack(anchor="w", pady=(0, 6))
        self.section_box = ttk.Combobox(
            sidebar, textvariable=self.section_var, state="readonly", height=10
        )
        self.section_box.pack(fill="x", pady=(0, 17))
        ttk.Button(sidebar, text="Apply filters", style="Accent.TButton",
                   command=self.apply_filters).pack(fill="x", pady=(0, 8))
        ttk.Button(sidebar, text="Clear filters", style="Side.TButton",
                   command=self.reset_filters).pack(fill="x")
        ttk.Separator(sidebar).pack(fill="x", pady=(25, 14))
        ttk.Label(sidebar, text="CURRENT DATA", style="SideEyebrow.TLabel").pack(anchor="w")
        self.dataset_var = tk.StringVar(value="Loading sample results…")
        ttk.Label(sidebar, textvariable=self.dataset_var, style="SideNote.TLabel",
                  wraplength=320, justify="left").pack(anchor="w", pady=(10, 0))

        main_area = ttk.Frame(shell)
        main_area.pack(side="left", fill="both", expand=True)
        content_canvas = tk.Canvas(main_area, background="#F3F6FA", highlightthickness=0)
        content_scroll = ttk.Scrollbar(main_area, orient="vertical", command=content_canvas.yview)
        content_canvas.configure(yscrollcommand=content_scroll.set)
        content_scroll.pack(side="right", fill="y")
        content_canvas.pack(side="left", fill="both", expand=True)
        content = ttk.Frame(content_canvas, padding=(28, 25, 28, 22))
        content_window = content_canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind(
            "<Configure>",
            lambda event: content_canvas.configure(scrollregion=event.widget.master.bbox("all")),
        )
        content_canvas.bind(
            "<Configure>",
            lambda event: content_canvas.itemconfigure(
                content_window, width=max(event.width, content.winfo_reqwidth())
            ),
        )
        header = ttk.Frame(content)
        header.pack(fill="x", pady=(0, 18))
        title_block = ttk.Frame(header)
        title_block.pack(fill="x")
        ttk.Label(title_block, text="Results dashboard", style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_block, text="A focused view of student achievement and attendance",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))
        actions = ttk.Frame(header)
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="Open CSV", command=self.open_csv).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Import Excel", command=self.open_excel).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Export summary", style="Accent.TButton",
                   command=self.export_csv).pack(side="left")

        context_row = ttk.Frame(content)
        context_row.pack(fill="x", pady=(0, 11))
        self.context_var = tk.StringVar(value="Load a CSV file to view results.")
        ttk.Label(context_row, textvariable=self.context_var, style="Muted.TLabel").pack(side="left")

        cards = ttk.Frame(content)
        cards.pack(fill="x")
        self.kpi_vars = {
            key: tk.StringVar(value="-")
            for key in ["students", "passed", "average", "pass_rate"]
        }
        self.insight_vars = {
            key: tk.StringVar(value="-")
            for key in ["leaders", "subjects", "grades", "semesters", "attendance", "attention"]
        }
        metrics = [
            ("students", "Students", "Unique students in this view"),
            ("passed", "Passed", "Passed every subject"),
            ("average", "Class average", "Mean student percentage"),
            ("pass_rate", "Pass rate", "Students passing every subject"),
        ]
        for column, (key, label, hint) in enumerate(metrics):
            cards.columnconfigure(column, weight=1)
            box = ttk.Frame(cards, style="Card.TFrame", padding=(15, 12))
            box.grid(row=0, column=column, sticky="nsew", padx=4)
            ttk.Label(box, text=label.upper(), style="CardLabel.TLabel").pack(anchor="w")
            ttk.Label(box, textvariable=self.kpi_vars[key], style="CardValue.TLabel").pack(anchor="w", pady=(5, 1))
            ttk.Label(box, text=hint, style="CardHint.TLabel").pack(anchor="w")

        insights_panel = ttk.Frame(content, style="Panel.TFrame", padding=(15, 13))
        insights_panel.pack(fill="x", pady=(14, 0))
        ttk.Label(insights_panel, text="Class insights", style="PanelSection.TLabel").pack(
            anchor="w", pady=(0, 10)
        )
        insight_cards = ttk.Frame(insights_panel, style="Panel.TFrame")
        insight_cards.pack(fill="x")
        insight_sections = [
            ("leaders", "TOP PERFORMERS"),
            ("subjects", "SUBJECT AVERAGES"),
            ("grades", "STUDENTS BY GRADE"),
            ("semesters", "SEMESTER COMPARISON"),
            ("attendance", "ATTENDANCE RELATIONSHIP"),
            ("attention", "MAY NEED ATTENTION"),
        ]
        for index, (key, title) in enumerate(insight_sections):
            row, column = divmod(index, 3)
            insight_cards.columnconfigure(column, weight=1)
            card = ttk.Frame(insight_cards, style="Card.TFrame", padding=(12, 10))
            card.grid(row=row, column=column, sticky="nsew", padx=4, pady=4)
            ttk.Label(
                card, text=title, style="CardLabel.TLabel", wraplength=430, justify="left"
            ).pack(anchor="w", fill="x")
            ttk.Label(
                card, textvariable=self.insight_vars[key], style="InsightBody.TLabel",
                justify="left", anchor="nw", wraplength=430,
            ).pack(fill="both", expand=True, anchor="nw", pady=(6, 0))

        chart_panel = ttk.Frame(content, style="Panel.TFrame", padding=(15, 13))
        chart_panel.pack(fill="both", expand=True, pady=(14, 12))
        chart_controls = ttk.Frame(chart_panel, style="Panel.TFrame")
        chart_controls.pack(fill="x")
        ttk.Label(chart_controls, text="Performance trends", style="PanelSection.TLabel").pack(side="left")
        self.chart_var = tk.StringVar(value="Grade Distribution")
        self.chart_var2 = tk.StringVar(value="Subject Averages")
        chart_options = [
            "Grade Distribution", "Subject Averages", "Semester Comparison",
            "Percentage Histogram", "Attendance vs Percentage",
        ]
        self.chart_box = ttk.Combobox(
            chart_controls, textvariable=self.chart_var, state="readonly",
            values=chart_options, width=32, height=8,
        )
        self.chart_box.pack(side="left", fill="x", expand=True, padx=(16, 8))
        self.chart_box.bind("<<ComboboxSelected>>", self._on_chart_selected)
        self.chart_box2 = ttk.Combobox(
            chart_controls, textvariable=self.chart_var2, state="readonly",
            values=chart_options, width=32, height=8,
        )
        self.chart_box2.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.chart_box2.bind("<<ComboboxSelected>>", self._on_chart_selected)
        self.chart_description_vars = [tk.StringVar(), tk.StringVar()]
        self.chart_frames = []
        chart_display = ttk.Frame(chart_panel, style="Panel.TFrame")
        chart_display.pack(fill="both", expand=True, pady=(6, 0))
        chart_display.columnconfigure((0, 1), weight=1, uniform="chart")
        for column in range(2):
            chart_slot = ttk.Frame(chart_display, style="Panel.TFrame")
            chart_slot.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0))
            ttk.Label(
                chart_slot, textvariable=self.chart_description_vars[column],
                style="PanelMuted.TLabel", wraplength=420, justify="left",
            ).pack(anchor="w", pady=(0, 4))
            chart_frame = ttk.Frame(chart_slot, style="Panel.TFrame")
            chart_frame.pack(fill="both", expand=True)
            self.chart_frames.append(chart_frame)
        self.figures = [None, None]
        self.canvases = [None, None]
        self.chart_frame = self.chart_frames[0]

        students_panel = ttk.Frame(content, style="Panel.TFrame", padding=(15, 13))
        students_panel.pack(fill="both", expand=True)
        student_heading = ttk.Frame(students_panel, style="Panel.TFrame")
        student_heading.pack(fill="x", pady=(0, 11))
        heading_text = ttk.Frame(student_heading, style="Panel.TFrame")
        heading_text.pack(fill="x")
        ttk.Label(heading_text, text="Student results", style="PanelSection.TLabel").pack(anchor="w")
        ttk.Label(heading_text, text="Average and attendance are calculated per student, semester and section",
                  style="PanelMuted.TLabel").pack(anchor="w", pady=(3, 0))
        student_tools = ttk.Frame(student_heading, style="Panel.TFrame")
        student_tools.pack(fill="x", pady=(8, 0))
        search_box = ttk.Frame(student_tools, style="Panel.TFrame")
        search_box.pack(side="left")
        ttk.Label(search_box, text="Find name or ID", style="PanelMuted.TLabel").pack(side="left", padx=(0, 7))
        search_entry = ttk.Entry(search_box, textvariable=self.search_var, width=32)
        search_entry.pack(side="left")
        self.search_var.trace_add("write", self._on_search_changed)
        self.student_count_var = tk.StringVar(value="0 students")
        ttk.Label(student_tools, textvariable=self.student_count_var, style="PanelMuted.TLabel").pack(
            side="right")

        columns = ("student_id", "name", "percentage", "attendance", "grade", "passed", "semester", "section")
        table_frame = ttk.Frame(students_panel, style="Panel.TFrame")
        table_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        headings = {
            "student_id": "STUDENT\nID", "name": "STUDENT", "percentage": "AVERAGE\n%",
            "attendance": "ATTENDANCE\n%", "grade": "GRADE", "passed": "RESULT",
            "semester": "SEMESTER", "section": "SECTION",
        }
        widths = {
            "student_id": 130, "name": 180, "percentage": 140, "attendance": 170,
            "grade": 95, "passed": 100, "semester": 120, "section": 110,
        }
        min_widths = {
            "student_id": 80, "name": 80, "percentage": 80, "attendance": 90,
            "grade": 65, "passed": 70, "semester": 80, "section": 70,
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(
                col, width=widths[col], minwidth=min_widths[col],
                anchor="w" if col == "name" else "center", stretch=True,
            )
        self.tree.tag_configure("pass", foreground="#23805A")
        self.tree.tag_configure("fail", foreground="#C14D4D")
        vertical_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        horizontal_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    def reset_filters(self):
        self.semester_var.set("All")
        self.section_var.set("All")
        self.apply_filters()

    def _on_search_changed(self, *_args):
        if len(_args) == 3:
            self._refresh_table()

    def _on_chart_selected(self, _event):
        if _event.widget in (self.chart_box, self.chart_box2):
            self.show_chart()

    def load_file(self, path):
        try:
            loaded = clean_results(pd.read_csv(path))
            self.raw = loaded
            self.source_files = [Path(path).name]
            self._update_dataset_name()
            if self.root is None:
                self.filtered = self.raw.copy()
                self.semester_var.set("All")
                self.section_var.set("All")
                self.search_var.set("")
                self.context_var.set(f"{self.dataset_name}  ·  All semesters and sections  ·  {self.raw['student_id'].nunique():,} students")
                self._refresh_kpis()
                return
            self.dataset_var.set(f"{self.dataset_name}\n{len(self.raw):,} subject results")
            self._update_filter_options()
            self.semester_var.set("All")
            self.section_var.set("All")
            self.search_var.set("")
            self.apply_filters()
            self.root.title(f"Semester Result Analysis Dashboard — {self.dataset_name}")
        except Exception as exc:
            if self.root is not None:
                messagebox.showerror("Load error", str(exc))
            else:
                raise

    def open_csv(self):
        if self.root is None:
            return
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            self.load_file(path)

    def open_excel(self):
        if self.root is None:
            return
        path = filedialog.askopenfilename(
            filetypes=[("Excel workbooks", "*.xlsx")]
        )
        if not path:
            return
        try:
            added = self.import_excel_file(path)
        except (OSError, ValueError, ImportError) as exc:
            messagebox.showerror("Excel import error", str(exc))
            return
        messagebox.showinfo(
            "Excel import complete",
            f"Added {added:,} subject result rows from {Path(path).name}.",
        )

    def import_excel_file(self, path):
        """Validate and append result rows from the first worksheet of an Excel workbook."""
        try:
            imported = pd.read_excel(path)
        except ImportError as exc:
            raise ImportError(
                "Excel support is unavailable. Install the project dependencies and try again."
            ) from exc
        imported = imported.dropna(how="all")
        missing = [column for column in REQUIRED_COLUMNS if column not in imported.columns]
        if missing:
            raise ValueError(
                f"Excel file is missing required columns: {', '.join(missing)}. "
                f"Required columns are: {', '.join(REQUIRED_COLUMNS)}."
            )
        if imported.empty:
            raise ValueError("The Excel worksheet has no student result rows.")

        cleaned = clean_results(imported)
        combined = pd.concat([self.raw, cleaned], ignore_index=True)
        source_name = Path(path).name
        self.raw = combined
        self.source_files.append(source_name)
        self._update_dataset_name()

        semesters = sorted(cleaned["semester"].unique().tolist())
        sections = sorted(cleaned["section"].unique().tolist())
        self.semester_var.set(semesters[0] if len(semesters) == 1 else "All")
        self.section_var.set(sections[0] if len(sections) == 1 else "All")
        self.search_var.set("")
        if self.root is None:
            self.filtered = self.raw.copy()
            self._refresh_kpis()
        else:
            self._update_filter_options()
            self.dataset_var.set(
                f"{self.dataset_name}\n{len(self.raw):,} subject results"
            )
            self.apply_filters()
            self.root.title(f"Semester Result Analysis Dashboard — {self.dataset_name}")
        return len(cleaned)

    def _update_dataset_name(self):
        if len(self.source_files) == 1:
            self.dataset_name = self.source_files[0]
        else:
            self.dataset_name = f"{len(self.source_files)} data files"

    def _update_filter_options(self):
        self.semester_box["values"] = ["All"] + sorted(self.raw["semester"].unique().tolist())
        self.section_box["values"] = ["All"] + sorted(self.raw["section"].unique().tolist())

    def apply_filters(self):
        df = self.raw
        if self.semester_var.get() != "All":
            df = df[df["semester"] == self.semester_var.get()]
        if self.section_var.get() != "All":
            df = df[df["section"] == self.section_var.get()]
        self.filtered = df.copy()
        summary_count = int(self.filtered["student_id"].nunique()) if not self.filtered.empty else 0
        semester = self.semester_var.get()
        section = self.section_var.get()
        filters = []
        if semester != "All":
            filters.append(f"Semester {semester}")
        if section != "All":
            filters.append(f"Section {section}")
        filter_text = " · ".join(filters) if filters else "All semesters and sections"
        source = f"{self.dataset_name}  ·  " if self.dataset_name else ""
        self.context_var.set(f"{source}{filter_text}  ·  {summary_count:,} students")
        self._refresh_kpis()
        if self.root is None:
            return
        self._refresh_table()
        self.show_chart()

    def _refresh_kpis(self):
        values = kpis(self.filtered)
        self.kpi_vars["students"].set(str(values["students"]))
        self.kpi_vars["passed"].set(str(values["passed"]))
        self.kpi_vars["average"].set(f"{values['average']:.1f}%")
        self.kpi_vars["pass_rate"].set(f"{values['pass_rate']:.1f}%")
        self._refresh_insights()

    def _refresh_insights(self):
        overview = student_overview(self.filtered)
        if overview.empty:
            for variable in self.insight_vars.values():
                variable.set("No results in this view.")
            return

        leaders = overview.head(5)
        self.insight_vars["leaders"].set("\n".join(
            f"{index + 1}. {row['name']} ({row['student_id']}) — {row['percentage']:.1f}%"
            for index, (_, row) in enumerate(leaders.iterrows())
        ))

        subject_averages = self.filtered.groupby("subject")["percentage"].mean().sort_values()
        low_subject, high_subject = subject_averages.index[0], subject_averages.index[-1]
        self.insight_vars["subjects"].set(
            f"Highest: {high_subject} ({subject_averages.iloc[-1]:.1f}%)\n"
            f"Lowest: {low_subject} ({subject_averages.iloc[0]:.1f}%)"
        )

        grade_counts = overview["grade"].value_counts().reindex(
            ["A+", "A", "B", "C", "D", "E", "F"], fill_value=0
        )
        self.insight_vars["grades"].set("   ".join(
            f"{grade}: {count}" for grade, count in grade_counts.items()
        ))

        semester_results = self.filtered.groupby(
            ["semester", "student_id"]
        )["percentage"].mean()
        semester_averages = semester_results.groupby(level="semester").mean().sort_index()
        if semester_averages.empty:
            semester_text = "No semester data."
        else:
            semester_text = "\n".join(
                f"{semester}: {average:.1f}%"
                for semester, average in semester_averages.items()
            )
        self.insight_vars["semesters"].set(semester_text)

        correlation = overview["attendance"].corr(overview["percentage"])
        if pd.isna(correlation):
            attendance_text = "Not enough variation or student data to compare."
        elif abs(correlation) < 0.1:
            attendance_text = f"Little linear relationship (r = {correlation:.2f})."
        else:
            direction = "positive" if correlation > 0 else "negative"
            attendance_text = (
                f"{direction.title()} association (r = {correlation:.2f}); "
                "association is not causation."
            )
        self.insight_vars["attendance"].set(attendance_text)

        needs_attention = overview[
            overview["failed_subjects"].gt(0) | overview["percentage"].lt(50)
        ].sort_values("percentage")
        if needs_attention.empty:
            attention_text = "No students flagged in this view."
        else:
            rows = []
            for _, row in needs_attention.head(5).iterrows():
                reasons = []
                if row["failed_subjects"]:
                    reasons.append(f"{row['failed_subjects']} failed subject(s)")
                if row["percentage"] < 50:
                    reasons.append("average below 50%")
                rows.append(
                    f"{row['name']} ({row['student_id']}) — "
                    f"{row['percentage']:.1f}%: {', '.join(reasons)}"
                )
            attention_text = f"{len(needs_attention)} student(s) flagged:\n" + "\n".join(rows)
            if len(needs_attention) > 5:
                attention_text += "\n…"
        self.insight_vars["attention"].set(attention_text)

    def _refresh_table(self):
        if self.root is None:
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        summary = self._visible_summary()
        self.student_count_var.set(f"{len(summary):,} student records")
        for _, row in summary.iterrows():
            self.tree.insert(
                "", "end",
                values=(
                    row["student_id"], row["name"], f"{row['percentage']:.1f}%",
                    f"{row['attendance']:.1f}%", row["grade"],
                    "Pass" if row["passed"] else "Fail", row["semester"], row["section"],
                ),
                tags=("pass" if row["passed"] else "fail",),
            )

    def _visible_summary(self):
        if self.filtered.empty:
            return pd.DataFrame(columns=[
                "student_id", "name", "semester", "section", "subjects",
                "percentage", "attendance", "grade", "passed",
            ])
        summary = student_summary(self.filtered)
        query = self.search_var.get().strip().casefold()
        if query:
            matches = (
                summary["student_id"].astype(str).str.casefold().str.contains(query, regex=False)
                | summary["name"].astype(str).str.casefold().str.contains(query, regex=False)
            )
            summary = summary[matches]
        return summary

    def show_chart(self):
        if self.root is None:
            return
        descriptions = {
            "Grade Distribution": "Counts unique students in each grade for the selected view.",
            "Subject Averages": "Compares the mean percentage achieved in each subject.",
            "Semester Comparison": "Compares average student percentages across semesters.",
            "Percentage Histogram": "Groups subject percentages into 10-point score bands.",
            "Attendance vs Percentage": "Each point represents one student's average attendance and result.",
        }
        chart_functions = {
            "Grade Distribution": grade_chart,
            "Subject Averages": subject_chart,
            "Semester Comparison": semester_chart,
            "Percentage Histogram": histogram_chart,
            "Attendance vs Percentage": scatter_chart,
        }
        for index, (chart_name, chart_frame) in enumerate(zip(
            (self.chart_var.get(), self.chart_var2.get()), self.chart_frames
        )):
            if self.canvases[index]:
                self.canvases[index].get_tk_widget().destroy()
            if self.figures[index]:
                self.figures[index].clear()
            self.canvases[index] = None
            self.figures[index] = None
            for child in chart_frame.winfo_children():
                child.destroy()
            self.chart_description_vars[index].set(descriptions[chart_name])
            if self.filtered.empty:
                ttk.Label(
                    chart_frame, text="No results match these filters.",
                    style="Muted.TLabel", anchor="center",
                ).pack(fill="both", expand=True)
                continue
            self.figures[index] = chart_functions[chart_name](self.filtered)
            self.figures[index].set_size_inches(4.3, 3.7, forward=True)
            self.canvases[index] = FigureCanvasTkAgg(
                self.figures[index], master=chart_frame
            )
            self.canvases[index].draw()
            self.canvases[index].get_tk_widget().pack(fill="both", expand=True)
        self.figure = self.figures[0]
        self.canvas = self.canvases[0]

    def export_csv(self):
        if self.root is None:
            summary = self._visible_summary()
            if summary.empty:
                raise ValueError("No filtered data to export.")
            path = DEFAULT_DATA.with_name("exported_summary.csv")
            summary.to_csv(path, index=False)
            return path
        summary = self._visible_summary()
        if summary.empty:
            messagebox.showwarning("Export", "No filtered data to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if path:
            summary.to_csv(path, index=False)
            messagebox.showinfo("Export", f"Saved to {path}")

    def run(self):
        if self.root is None:
            return
        self.root.mainloop()
