import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import time
from pathlib import Path
from tkinter import font as tkfont
from tkcalendar import DateEntry
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Appearance only: configured once when the app opens.
UI_COLORS = {
    "page": "#F3F6FB",
    "surface": "#FFFFFF",
    "text": "#203047",
    "muted": "#687990",
    "accent": "#0078D4",
    "border": "#DFE7F1",
    "danger": "#DC2626",
}
CHART_COLORS = ("#0078D4", "#249D97", "#8073CA", "#D69A38",
                "#D56F89", "#517798", "#77A44C", "#A47850")

def configure_appearance(root):
    family = tkfont.nametofont("TkDefaultFont").actual("family")
    root.ui_font = family
    root.configure(background=UI_COLORS["page"])

    style = ttk.Style(root)
    style.theme_use("alt")

    # Frames
    style.configure(
        "TFrame",
        background=UI_COLORS["surface"],
    )
    style.configure(
        "Page.TFrame",
        background=UI_COLORS["page"],
    )
    style.configure(
        "Card.TFrame",
        background=UI_COLORS["surface"],
        borderwidth=0,
        relief="flat",
    )
    style.configure(
        "StatCard.TFrame",
        background=UI_COLORS["surface"],
        borderwidth=1,
        relief="solid",
    )

    # Project cards use LabelFrame, so they need their own styles.
    style.configure(
        "Card.TLabelframe",
        background=UI_COLORS["surface"],
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=UI_COLORS["surface"],
        foreground=UI_COLORS["accent"],
        font=(family, 12, "bold"),
    )

    # Labels
    style.configure(
        "TLabel",
        background=UI_COLORS["surface"],
        foreground=UI_COLORS["text"],
        font=(family, 10),
    )
    style.configure(
        "Heading.TLabel",
        background=UI_COLORS["surface"],
        foreground=UI_COLORS["text"],
        font=(family, 12, "bold"),
    )
    style.configure(
        "Muted.TLabel",
        background=UI_COLORS["surface"],
        foreground=UI_COLORS["muted"],
        font=(family, 9),
    )
    style.configure(
        "Subject.TLabel",
        background=UI_COLORS["surface"],
        foreground=UI_COLORS["accent"],
        font=(family, 11, "bold"),
    )
    style.configure(
        "Metric.TLabel",
        background=UI_COLORS["surface"],
        foreground=UI_COLORS["text"],
        font=(family, 22, "bold"),
    )
    style.configure(
        "Timer.TLabel",
        background=UI_COLORS["surface"],
        foreground=UI_COLORS["accent"],
        font=(family, 40, "bold"),
    )
    style.configure(
        "Error.TLabel",
        background=UI_COLORS["surface"],
        foreground=UI_COLORS["danger"],
        font=(family, 9),
    )
    style.configure(
        "Small.Accent.TButton",
        font=(family, 9),
        padding=(6, 3),
    )

    # Controls
    style.configure(
        "TCheckbutton",
        background=UI_COLORS["surface"],
        foreground=UI_COLORS["text"],
        font=(family, 10),
    )
    style.map(
        "TCheckbutton",
        background=[("active", UI_COLORS["surface"])],
    )
    style.configure(
        "TButton",
        font=(family, 10),
        padding=(12, 7),
    )
    style.configure(
        "Accent.TButton",
        font=(family, 10, "bold"),
        padding=(14, 8),
    )

    # Progress bars used by project cards and metric cards.
    style.configure(
        "Card.Horizontal.TProgressbar",
        background=UI_COLORS["accent"],
        troughcolor=UI_COLORS["page"],
    )

    # Notebook
    style.configure(
        "TNotebook",
        background=UI_COLORS["page"],
        borderwidth=0,
    )
    style.configure(
        "TNotebook.Tab",
        font=(family, 10),
        padding=(18, 9),
    )

    # Treeview
    style.configure(
        "TaskManager.Treeview",
        background=UI_COLORS["surface"],
        fieldbackground=UI_COLORS["surface"],
        foreground=UI_COLORS["text"],
        font=(family, 10),
        rowheight=30,
        borderwidth=0,
    )
    style.configure(
        "TaskManager.Treeview.Heading",
        font=(family, 10, "bold"),
        padding=(8, 7),
    )
    style.map(
        "TaskManager.Treeview",
        background=[("selected", UI_COLORS["accent"])],
        foreground=[("selected", "#FFFFFF")],
    )
    style.configure(
        "White.TRadiobutton",
        background="white"
    )

    # Charts
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [family, "DejaVu Sans"],
        "font.size": 10,
        "figure.facecolor": UI_COLORS["surface"],
        "axes.facecolor": UI_COLORS["surface"],
        "text.color": UI_COLORS["text"],
        "axes.labelcolor": UI_COLORS["muted"],
        "axes.edgecolor": UI_COLORS["border"],
        "xtick.color": UI_COLORS["muted"],
        "ytick.color": UI_COLORS["muted"],
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.axisbelow": True,
        "grid.color": UI_COLORS["border"],
        "grid.linewidth": 0.7,
    })

def main():
    app = Application()
    app.mainloop()

opening_query_sessions = """
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY,
        date TEXT NOT NULL,
        subject TEXT NOT NULL,
        task TEXT NOT NULL,
        minutes INTEGER NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
        canceled INTEGER NOT NULL DEFAULT 0 CHECK (canceled IN (0, 1)),
        recurring_id INTEGER,
        FOREIGN KEY (recurring_id) REFERENCES recurring_tasks(id)
    );
"""

opening_query_recurring_tasks = """
    CREATE TABLE IF NOT EXISTS recurring_tasks (
        id INTEGER PRIMARY KEY,
        subject TEXT NOT NULL,
        task TEXT NOT NULL,
        frequency TEXT NOT NULL CHECK (frequency IN ('daily', 'weekly')),
        day TEXT,
        start_date TEXT,
        end_date TEXT
    );
"""

opening_query_projects = """
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0
            CHECK (completed IN (0, 1))
    );
"""

opening_query_milestones = """
    CREATE TABLE IF NOT EXISTS milestones (
        id INTEGER PRIMARY KEY,
        project_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0
            CHECK (completed IN (0, 1)),
        FOREIGN KEY (project_id) REFERENCES projects(id)
);
"""

opening_query_targets = """
CREATE TABLE IF NOT EXISTS weekly_targets (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    subject TEXT,
    project_id INTEGER,
    metric TEXT NOT NULL
        CHECK (metric IN ('minutes', 'completed', 'hours')),
    target INTEGER NOT NULL CHECK (target > 0),
    active INTEGER NOT NULL DEFAULT 0 CHECK (active IN (0, 1)),
    FOREIGN KEY (project_id) REFERENCES projects(id),

    -- Each target applies to either a subject or a project.
    CHECK (
        (subject IS NOT NULL AND project_id IS NULL)
        OR
        (subject IS NULL AND project_id IS NOT NULL)
    )
);
"""

#####################
# Root Class
#####################

class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        configure_appearance(self)
        self.calendars = {}
        self.widgets = {}
        self.milestones = {}


        self.conn = sqlite3.connect("study_tracker.db")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(opening_query_sessions)
        self.conn.execute(opening_query_recurring_tasks)
        self.conn.execute(opening_query_projects)
        self.conn.execute(opening_query_milestones)
        self.conn.execute(opening_query_targets)

        self.today = datetime.today().strftime("%Y-%m-%d")
        self.title("Study Tracker")
        self.geometry("1080x650")
        self.load_data()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10,
        )

        self.main_tab = ttk.Frame(
            self.notebook,
            style="Page.TFrame",
            padding=10,
        )
        self.notebook.add(self.main_tab, text="Daily tasks")

        self.main_tab.columnconfigure(0, weight=3)
        self.main_tab.columnconfigure(1, weight=2)
        self.main_tab.rowconfigure(0, weight=1)


        tasks_and_weekly_progress = ttk.Frame(
            self.main_tab,
            style="Page.TFrame",
            padding=10
        )
        tasks_and_weekly_progress.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        tasks_and_weekly_progress.columnconfigure(0, weight=1)
        tasks_and_weekly_progress.rowconfigure(0, weight=1)
        tasks_and_weekly_progress.rowconfigure(1, weight=0)

        self.canvas_frame = ScrollableFrame(tasks_and_weekly_progress)
        self.canvas_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.canvas_frame.scrollable_frame.columnconfigure(
            0, weight=1
        )

        self.tasks = Tasks(
            self.canvas_frame.scrollable_frame,
            self,
        )
        self.tasks.grid(
            row=0,
            column=0,
            sticky="new",
        )

        self.weekly_progress = ttk.Frame(
            tasks_and_weekly_progress,
            style="Card.TFrame",
            padding=10
        )
        self.weekly_progress.grid(
            row=1,
            column=0,
            sticky="nsew",
            pady=(10,0)
        )
        self.weekly_progress.columnconfigure(0,weight=1)
        ttk.Label(self.weekly_progress, text="Targets This Week", style="Heading.TLabel")\
            .grid(row=0, column=0, sticky="w")
        target_df = self.target_subjects
        for i in range(1,4):
            j = i-1
            title = target_df.loc[j,'subject']
            current = target_df.loc[j,'current']
            target = target_df.loc[j,'target']

            bar = MetricBar(self.weekly_progress, title, current, target, text="placeholder")
            bar.grid(column=0, row=i, sticky='ew')

        stop_watch_and_task_adder = ttk.Frame(
            self.main_tab,
            style="Page.TFrame",
        )
        stop_watch_and_task_adder.grid(
            row=0,
            column=1,
            sticky="nsew",
        )
        stop_watch_and_task_adder.columnconfigure(0, weight=1)

        self.goal_page = Schedule(
            stop_watch_and_task_adder,
            self,
        )
        self.goal_page.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 12),
        )
        self.goal_page.columnconfigure(0, weight=1)

        self.targets = Targets(
            stop_watch_and_task_adder,
            self,
        )
        self.targets.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 12),
        )
        self.targets.columnconfigure(0, weight=1)

        self.timer = Timer(
            stop_watch_and_task_adder,
            self,
        )
        self.timer.grid(
            row=2,
            column=0,
            sticky="nw",
        )
        self.timer.columnconfigure(0, weight=1)

        stop_watch_and_task_adder.rowconfigure(2, weight=1)

        self.visuals_tab = Visuals(
            self.notebook,
            self,
            self.df,
        )

        self.analytics_tab = Analytics(self.notebook, self)
        self.notebook.add(
            self.analytics_tab,
            text="Analytics",
        )

        self.notebook.add(
            self.visuals_tab,
            text="Visuals",
        )

        self.task_manager = TaskManager(self.notebook, self)
        self.notebook.add(
            self.task_manager,
            text="Manage Data",
        )

        self.projects = ProjectPage(self.notebook, self)
        self.notebook.add(
            self.projects,
            text="Projects",
        )

    def load_data(self):
       rows = self.conn.execute("SELECT * FROM sessions").fetchall()
       sessions = pd.DataFrame([dict(row) for row in rows])
       self.df=sessions

       rows = self.conn.execute("SELECT * FROM recurring_tasks").fetchall()
       recurring_tasks = pd.DataFrame([dict(row) for row in rows])

       rows = self.conn.execute("SELECT * FROM weekly_targets").fetchall()
       weekly_targets = pd.DataFrame([dict(row) for row in rows])

       rows = self.conn.execute("SELECT * FROM projects").fetchall()
       self.active_project_records = [row for row in rows if row['completed']==0]
       active_project_ids = [row['id'] for row in self.active_project_records]
       projects = pd.DataFrame([dict(row) for row in rows])

       rows = self.conn.execute("SELECT * FROM milestones").fetchall()
       milestones = pd.DataFrame([dict(row) for row in rows])
       self.active_milestones = [row for row in rows if row['project_id'] in active_project_ids]

       self.milestone_record_lookup = defaultdict(list)
       for record in self.active_milestones:
           self.milestone_record_lookup[record['project_id']].append(record)
           
       self.data_lookup = {
           'sessions':sessions,
           'recurring_tasks':recurring_tasks,
           'weekly_targets':weekly_targets,
           'projects':projects,
           'milestones':milestones
       }

       week_start = "2026-10-25"
       last_week_data = sessions.query('date > @week_start').groupby('subject', as_index = False)[['minutes','completed']].sum()\
        .assign(hours=lambda df: df["minutes"] // 60)
       active_targets = weekly_targets.query('active == 1')[['subject', 'metric', 'target']]
       
       combined_df = last_week_data.merge(active_targets, on='subject')
       
       def get_metric_column(row):

           metric = row['metric']
           if metric == 'completed':
               return row['completed']
           elif metric == 'minutes':
               return row['minutes']
           else:
               return row['hours']

       combined_df['current'] = combined_df.apply(get_metric_column, axis=1)

       self.target_subjects = combined_df

    def insert_project(self, name, completed=0):
        self.cursor.execute(
            """
            INSERT INTO projects (
                name_projects,
                completed_projects
            )
            VALUES (?, ?)
            """,
            (name, completed)
        )

        self.conn.commit()

        return self.cursor.lastrowid

    def change_stats_period(self, event=None):
        period = self.stats_period.get()
        self.statistics_tab.set_period(period)
        self.visuals_tab.set_period(period)

    def insert_milestone(self, project_id, name, completed=0):
        self.cursor.execute(
            """
            INSERT INTO milestones (
                project_id,
                name_milestone,
                completed_milestone
            )
            VALUES (?, ?, ?)
            """,
            (project_id, name, completed)
        )

        self.conn.commit()

        return self.cursor.lastrowid

    def retrieve_records(self, date):

        return self.conn.execute("""
            SELECT * FROM sessions
            WHERE date = ?
            AND canceled != 1
        """, (date,)).fetchall()

    def retrieve_recurring_tasks(self):

        day = datetime.today().strftime("%A")

        return self.conn.execute("""
            SELECT *
            FROM recurring_tasks
            WHERE (
                frequency = 'daily'
                OR (frequency = 'weekly' AND day = ?)
            )
            AND start_date <= date('now', 'localtime')
            AND (
                end_date IS NULL
                OR end_date >= date('now', 'localtime')
            )
            AND id NOT IN (
                SELECT recurring_id
                FROM sessions
                WHERE date = date('now', 'localtime')
                AND recurring_id IS NOT NULL
            )
            AND id NOT IN (
                SELECT recurring_id
                FROM sessions
                WHERE date = date('now', 'localtime')
                AND canceled = 1
            )
        """, (day,)).fetchall()

    def insert_record(self, date, subject, task, minutes=0, completed=0, canceled=0, recurring_id=None):
        
        with self.conn:
            self.conn.execute("""
                INSERT INTO sessions (date, subject, task, minutes, completed, canceled, recurring_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date, subject, task, minutes, completed, canceled, recurring_id))

    def insert_recurring_task(self, subject, task, frequency, day=None):
      
        with self.conn:
            cursor = self.conn.execute("""
                INSERT INTO recurring_tasks (subject, task, frequency, day)
                VALUES (?, ?, ?, ?)
            """, (subject, task, frequency, day))

        return cursor.lastrowid

    def update_task(self, id, minutes, completed):

        with self.conn:
            self.conn.execute("""
                UPDATE sessions
                SET minutes = ?, completed = ?
                WHERE id = ?
            """, (minutes, completed, id))

    def cancel_record(self, id):

        with self.conn:
            self.conn.execute("""
                UPDATE sessions
                SET canceled = 1
                WHERE id = ?
            """, (id,))

    def delete_record(self, table, id):
        with self.conn:
            self.conn.execute(f"""
                DELETE FROM {table}
                WHERE id = ?
            """, (id,))

    def retrieve_new_records(self, date, existing_ids):
        existing_ids = tuple(existing_ids)
        placeholders = ", ".join("?" for _ in existing_ids)

        query = "SELECT * FROM sessions WHERE date = ?"

        if existing_ids:
            query += f" AND id NOT IN ({placeholders})"

        parameters = (date,) + existing_ids

        return self.conn.execute(query, parameters).fetchall()

    def update_record(self, id, table, column, value):

        try:
            value = int(value)
        except ValueError:
            pass

        id = int(id)

        with self.conn:
            self.conn.execute(f"""
                UPDATE {table}
                SET {column} = ?
                WHERE id = ?
            """, (value, id))

    def get_start_and_end_dates(self, selection):
        days_by_choice = {
            "Last Week": 7,
            "Last Month": 30,
            "Last Year": 365,
        }

        self.period_days = days_by_choice[selection]

        today = datetime.today().date()
        self.end = (today - timedelta(days=1)).isoformat()
        self.start = (
            today - timedelta(days=self.period_days)
        ).isoformat()

    def filter_dates(self, start, end):
        dates = pd.to_datetime(self.df["date"]).dt.normalize()

        self.df_filt = self.df.loc[
            dates.between(pd.Timestamp(start), pd.Timestamp(end))
        ]

#####################
# Main Frame Classes
#####################

class Targets(ttk.Frame):
    def __init__(self, parent, on_add=None):
        super().__init__(
            parent,
            style="Card.TFrame",
            padding=12,
        )

        self.parent = parent

        # Temporary data
        self.subjects = ["French", "Python", "SQL"]
        self.projects = ["Finish App", "Do Homework"]

        # Variables
        self.target_type = tk.StringVar(value="subject")
        self.choices = self.subjects
        self.amount = tk.StringVar(value="120")

        self.preview = tk.StringVar()

        # ==========================================
        # Header
        # ==========================================

        ttk.Label(
            self,
            text="Weekly Target",
            style="Heading.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 5)
        )

        # ==========================================
        # Weekly Target Form
        # ==========================================

        self.week_targets = ttk.Frame(
            self,
            style="Card.TFrame",
        )

        self.week_targets.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        # ==========================================
        # Apply To
        # ==========================================

        radio_frame = ttk.Frame(
            self.week_targets,
            style="Card.TFrame",
        )
        
        radio_frame.pack(side='left', padx=(0, 6),pady=(0, 5))

        # Everything inside radio_frame uses pack().
        radio_label = ttk.Label(
            radio_frame,
            text="Apply To",
            style="Muted.TLabel"
        )
        
        radio_label.pack(anchor="w", pady=(5, 5))

        # Separate frame lets us pack the two
        # radio buttons next to each other.
        radio_button_container = ttk.Frame(
            radio_frame,
            style="Card.TFrame",
        )

        radio_button_container.pack(
            anchor="w"
        )

        subject_button = ttk.Radiobutton(
            radio_button_container,
            text="Subject",
            variable=self.target_type,
            command=self.update_choices,
            value="subject",
            cursor="hand2",
            style="White.TRadiobutton"
        )
        
        subject_button.pack(side="left", padx=(0, 8))

        project_button = ttk.Radiobutton(
            radio_button_container,
            text="Project",
            variable=self.target_type,
            command=self.update_choices,
            value="project",
            cursor="hand2",
            style="White.TRadiobutton"
        )
        
        project_button.pack(side="left")

        # ==========================================
        # Subject / Project Choice
        # ==========================================

        self.target_label = "Pick a Subject"
        self.target_choice = DropdownField(
            self.week_targets,
            "Choose Subject",
            "target_choice",
            self.choices
        )
        
        self.target_choice.pack(side='left', padx=(0, 6),pady=(0, 5))
        # ==========================================
        # Target Amount
        # ==========================================

        amount_frame = ttk.Frame(
            self.week_targets,
            style="Card.TFrame"
        )
        
        amount_frame.pack(side='left', padx=(0, 6),pady=(0, 5))
        # Again, pack is fine here because all children
        # of amount_frame use pack().
        amount_lablel = ttk.Label(
            amount_frame,
            text="Target",
            style="Muted.TLabel"
        )
        
        amount_lablel.pack(anchor="w", pady=(5, 5))

        self.amount_widget = ttk.Spinbox(
            amount_frame,
            from_=1,
            to=10080,
            textvariable=self.amount,
            width=8,
            cursor="xterm"
        )

        self.amount_widget.pack(anchor="w")

        # ==========================================
        # Measure
        # ==========================================

        self.measure = DropdownField(
            self.week_targets,
            "Measure",
            "measuring",
            ["Minutes", "Hours", "Tasks"]
        )

        self.measure.pack(
            side="left",
            padx=(0, 6),
            pady=(0, 5)
        )

        self.measure.widget.set("Minutes")

        # ==========================================
        # Add Target
        # ==========================================

        self.submit_and_remove_frame = ttk.Frame(
            self,
            style="Card.TFrame",
        )

        self.submit_and_remove_frame.grid(
            row=2,
            column=0,
            sticky="ew"
        )

        self.add_button = ttk.Button(
            self.submit_and_remove_frame,
            cursor="hand2",
            text="Add Target",
            style="Accent.TButton"
        )

        self.add_button.pack(
            side='left',
            pady=(12, 0)
        )

        self.preview_label = ttk.Label(
            self.submit_and_remove_frame,
            textvariable=self.preview,
            style="Muted.TLabel",
            wraplength=150,
            justify="left"
        )

        self.preview_label.pack(
            side='left',
            pady=(10, 0),
            padx=(12,0)
        )

        divider = ttk.Separator(
            self.submit_and_remove_frame,
            orient="vertical"
        )

        divider.pack(
            side="left",
            fill="y",
            padx=12,
            pady=5
        )

        # Remove target dropdown
        self.remove_target = DropdownField(
            self.submit_and_remove_frame,
            "Remove Target",
            "remove_target",
            []
        )

        self.remove_target.pack(
            side='left',
            anchor="w",
            padx=(12,0),
        )

        self.remove_button = ttk.Button(
            self.submit_and_remove_frame,
            text="Remove",
            cursor="hand2",
            style="Accent.TButton"
            # command=self.remove_weekly_target
        )

        self.remove_button.pack(
            side='left',
            anchor="w",
            pady=(12, 0),
            padx=(12,0),
        )

        self.target_choice.widget.bind(
            "<<ComboboxSelected>>",
            self.update_preview
        )

        self.measure.widget.bind(
            "<<ComboboxSelected>>",
            self.update_preview
        )

        self.update_choices()
        self.update_preview()

    def update_preview(self, *_):
        name = self.target_choice.get()
        amount = self.amount.get()
        measure = self.measure.get()

        if not name:
            self.preview.set(f"Choose a {self.target_type.get()}.")
            return

        if not amount:
            self.preview.set("Enter a target.")
            return

        if measure == "Minutes":
            self.preview.set(
                f"Spend {amount} minutes on {name} this week."
            )

        elif measure == "Hours":
            self.preview.set(
                f"Spend {amount} hours on {name} this week."
            )

        elif measure == "Tasks":
            self.preview.set(
                f"Complete {amount} tasks for {name} this week."
            )

    def update_choices(self):
        target_type = self.target_type.get()

        choices = (
            self.subjects
            if target_type == "subject"
            else self.projects
        )

        target_label = (
            "Subject"
            if target_type == "subject"
            else "Project"
        )

        self.target_choice.label.configure(
            text=f"Choose {target_label}"
        )

        self.target_choice.widget.configure(
            values=choices
        )

        self.target_choice.widget.set(
            choices[0] if choices else ""
        )

        self.update_preview()

class Tasks(ttk.Frame):
    def __init__(self, canvas, parent):
        super().__init__(
            canvas,
            padding=10,
            style="Card.TFrame",
        )

        self.parent = parent

        # dictionary to track record read in by id number
        self.days_items = {}

        # dictionary key by subject used when filling out task list
        self.days_subjects = defaultdict(list)

        # dictionary to hold subject frame to store list of tasks
        self.subject_frames = {}

        # dictionary to hold actual widgets for each task row
        self.row_widgets = defaultdict(list)

        # dictionary to hold string variables to update 
        self.check_boxes = {}
        self.hours = {}
        self.minutes = {}

        # Let the task area expand with the frame.
        self.columnconfigure(0, weight=1)

        self.header_frame = ttk.Frame(self, style="Card.TFrame",)
        self.header_frame.columnconfigure(0, weight=1)
        self.header_frame.grid(
            row=0, column=0,
            sticky="nw",
            padx=(0, 20),
        )

        ttk.Separator(self, orient="horizontal").grid(
            row=1, column=0,
            columnspan=2,
            sticky="ew",
            pady=(16, 8),
        )

        self.task_frame = ttk.Frame(self, style="Card.TFrame", )
        self.task_frame.grid(
            row=2, column=0,
            columnspan=2,
            sticky="ew",
        )
        self.task_frame.columnconfigure(0, weight=1)

        self.save_frame = ttk.Frame(self, style="Card.TFrame",)
        self.save_frame.grid(
            row=3, column=0,
            columnspan=2,
            sticky="ew",
            pady=(16, 0),
        )
        self.save_frame.columnconfigure(0, weight=1)

        self.header_widgets()
        self.calendar_widget()
        self.save_button()
        self.check_for_new_records()

    def header_widgets(self):
        goal_label = ttk.Label(
            self.header_frame,
            text="Daily Goals",
            style="Heading.TLabel",
        )
        goal_label.grid(row=0, column=0, sticky="w")

        subtitle = ttk.Label(
            self.header_frame,
            text="Check off tasks and record your study time.",
            style="Muted.TLabel",
        )
        subtitle.grid(
            row=1, column=0,
            sticky="w",
            pady=(6, 0),
        )

    def calendar_widget(self):
        self.task_calendar = CalendarField(self, "Choose Date", 'task_date')
        self.task_calendar.grid(
            row=0, column=1,
            sticky="ne",
        )

    def add_task(self, record):
        task_id = record["id"]
        subject = record["subject"]

        if subject not in self.subject_frames:
            subject_frame = ttk.Frame(
                self.task_frame,
                padding=(0, 10),
                style="Card.TFrame",
            )
            subject_frame.grid(
                row=len(self.subject_frames),
                column=0,
                sticky="ew",
            )
            subject_frame.columnconfigure(0, weight=1)

            self.subject_frames[subject] = subject_frame
            self.subject_label(subject, subject_frame)

        subject_frame = self.subject_frames[subject]
        task_row = len(self.days_subjects[subject]) + 1

        self.check_box(record, task_row, subject_frame)
        self.task_time_to_complete(record, task_row, subject_frame)
        self.delete_button(record, task_row, subject_frame)

        self.days_subjects[subject].append(record)
        self.days_items[task_id] = record

    def subject_label(self, subject, subject_frame):
        label = ttk.Label(
            subject_frame,
            text=subject,
            style="Subject.TLabel",
        )
        label.grid(
            row=0, column=0,
            sticky="w",
            pady=(0, 8),
        )

    def check_box(self, record, row, subject_frame):
        task_id = record["id"]
        completed_status = record["completed"]
        task_name = record["task"]

        self.check_boxes[task_id] = tk.BooleanVar(
            self,
            value=bool(completed_status),
        )

        checkbox = ttk.Checkbutton(
            subject_frame, cursor="hand2",
            text=task_name,
            variable=self.check_boxes[task_id],
        )
        checkbox.grid(
            row=row, column=0,
            sticky="w",
            pady=5,
        )

        self.row_widgets[task_id].append(checkbox)

    def delete_button(self, record, row, subject_frame):
        task_id = record['id']

        button = tk.Button(
            subject_frame,
            text="×",
            font=(self.parent.ui_font, 13),
            fg=UI_COLORS["muted"],
            bg=UI_COLORS["surface"],
            activeforeground=UI_COLORS["danger"],
            activebackground=UI_COLORS["surface"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            padx=6,
            pady=0,
            command=lambda: self.handle_delete(task_id),
        )
        button.grid(
            row=row, column=2,
            sticky="e",
            padx=5,
            pady=5,
        )

        self.row_widgets[task_id].append(button)

    def handle_delete(self, task_id):
        recurring_id = self.days_items[task_id]["recurring_id"]
        if recurring_id is not None:
            self.parent.cancel_record(task_id)
        else:
            self.parent.delete_record("sessions", task_id)

        for widget in self.row_widgets.pop(task_id):
            widget.destroy()

        subject = self.days_items.pop(task_id)['subject']
        subject_frame = self.subject_frames[subject]

        if len(subject_frame.winfo_children()) == 1:
            subject_frame.destroy()
            del self.subject_frames[subject]

        self.parent.timer.get_stop_watch_options()

    def task_time_to_complete(self, record, row, subject_frame):
        task_id = record["id"]
        task_minutes = record["minutes"]

        hours, minutes = divmod(task_minutes, 60)

        self.hours[task_id] = tk.StringVar(self, value=hours)
        self.minutes[task_id] = tk.StringVar(self, value=minutes)

        time_frame = ttk.Frame(subject_frame, style="Card.TFrame",)
        time_frame.grid(
            row=row, column=1,
            # sticky="e",
            padx=(20, 0),
            pady=5
        )

        hours_spinbox = ttk.Spinbox(
            time_frame, 
            cursor="xterm",
            from_=0,
            to=24,
            width=4,
            justify="center",
            textvariable=self.hours[task_id],
            wrap=True
        )
        hours_spinbox.grid(row=0, column=0, padx=(0, 6))

        hour_label = ttk.Label(
            time_frame,
            text="hr"
        )
        
        hour_label.grid(row=0, column=1, padx=(0, 18))

        minutes_spinbox = ttk.Spinbox(
            time_frame, cursor="xterm",
            from_=0,
            to=59,
            width=4,
            justify="center",
            textvariable=self.minutes[task_id],
            wrap=True
        )
        minutes_spinbox.grid(row=0, column=2)

        min_label = ttk.Label(
            time_frame,
            text="min"
        )   
        min_label.grid(row=0, column=3, padx=(0, 6))

        self.row_widgets[task_id].append(time_frame)

    def register_todays_recurring_items(self, date):
        days_recurring_tasks = self.parent.retrieve_recurring_tasks()

        today_tasks = []
        for task_info in self.days_items.values():
            task_name = task_info['task'].strip().lower()
            task_subject = task_info['subject'].strip().lower()
            today_tasks.append((task_subject, task_name))

        for task in days_recurring_tasks:
            recurring_task_name = task["task"].strip().lower()
            recurring_task_subject = task["subject"].strip().lower()
            recurring_task_id = task["id"]

            if (recurring_task_subject, recurring_task_name) not in today_tasks:
                self.parent.insert_record(
                    date,
                    task["subject"],
                    task["task"],
                    recurring_id=task["id"],
                )

    def check_for_new_records(self):
        date = self.task_calendar.get()

        self.register_todays_recurring_items(date)
        new_records = self.parent.retrieve_records(date)

        for record in new_records:
            if record["id"] not in self.days_items:
                self.add_task(record)

    def change_date(self, event=None):
        for frame in self.subject_frames.values():
            frame.destroy()

        self.subject_frames.clear()
        self.days_subjects.clear()
        self.days_items.clear()
        self.check_boxes.clear()
        self.minutes.clear()

        self.check_for_new_records()

    def save_button(self):
        save_button = ttk.Button(
            self.save_frame, 
            cursor="hand2",
            text="Save Changes",
            style="Accent.TButton",
            command=self.save_information,
            padding=(14, 6),
        )
        save_button.grid(row=0, column=0, sticky="e")

    def save_information(self):
        for task in self.days_items.values():
            task_id = task["id"]
            task_completed_before = task["completed"]
            task_minutes_before = task["minutes"]

            task_completed_after = int(self.check_boxes[task_id].get())
            task_minutes_after = self.minutes[task_id].get()

            if (
                task_completed_before != task_completed_after
                or str(task_minutes_before) != task_minutes_after
            ):
                self.parent.update_task(
                    task_id,
                    task_minutes_after,
                    task_completed_after,
                )

class Timer(ttk.Frame):

    def __init__(self, new_frame, parent):
        super().__init__(
            new_frame,
            padding=10,
            style="Card.TFrame"
        )

        self.parent = parent
        self.tasks = parent.tasks
        self.sv = tk.StringVar(value="00:00:00")
        self.start_time = None
        self.current_elapsed = None
        self.after_job = None
        self.all_zeros = "00:00:00"

        self.make_widgets()


    def make_widgets(self):

        # Allow center section to expand
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        # Header
        ttk.Label(
            self,
            text="Time A Task",
            style="Heading.TLabel"
        ).grid(
            row=0,
            column=0,
            # columnspan=3,
            sticky="w",
            pady=(0, 15)
        )

        # Task selection
        ttk.Label(
            self,
            text="Select Task"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(0, 15)
        )

        self.task_choice = tk.StringVar()
        self.get_stop_watch_options()

        self.task_dropdown = ttk.Combobox(
            self,
            textvariable=self.task_choice,
            state="readonly",
            # width=30,
            values=self.task_names,
        )

        self.task_dropdown.grid(
            row=1,
            column=1,
            # columnspan=2,
            # sticky="w",
            pady=(0, 15),
        )

        # Timer
        self.timer_display = ttk.Label(
            self,
            textvariable=self.sv,
            style="Timer.TLabel",
            font=(self.parent.ui_font, 15, "bold"),
            anchor="center"
        )

        self.timer_display.grid(
            row=2,
            column=0,
            # columnspan=3,
            sticky="ew",
            pady=(0, 5)
        )

        # Buttons
        ttk.Button(
            self, cursor="hand2",
            text="Start",
            style="Small.Accent.TButton",
            command=self.start
        ).grid(
            row=2,
            column=1,
            padx=(0, 5),
            sticky="e"
        )

        ttk.Button(
            self, cursor="hand2",
            text="Stop",
            style="Small.Accent.TButton",
            command=self.stop
        ).grid(
            row=2,
            column=2,
            padx=5,
            sticky="w"
        )

        ttk.Button(
            self, cursor="hand2",
            text="Finish",
            style="Small.Accent.TButton",
            command=self.complete
        ).grid(
            row=2,
            column=3,
            padx=(5, 0),
            sticky="w"
        )

    def get_stop_watch_options(self):
        self.task_names = []
        self.task_id_look_up = {}
        for task in self.tasks.days_items.values():
            task_id = task['id']
            name = task['task']
            self.task_names.append(name)
            self.task_id_look_up[name] = task_id

    def timer(self):
        self.sv.set(
            self.format_time(time.time() - self.start_time)
        )

        self.after_job = self.after(
            30,
            self.timer
        )


    def start(self):
        if self.after_job is not None:
            return

        self.start_time = time.time()

        if self.current_elapsed is not None:
            self.start_time -= self.current_elapsed

        self.timer()


    def stop(self):
        if self.after_job is None:
            return

        self.after_cancel(self.after_job)
        self.after_job = None

        self.current_elapsed = time.time() - self.start_time


    def complete(self):
        if self.after_job is not None:
            self.after_cancel(self.after_job)

        self.after_job = None
        self.start_time = None
        self.current_elapsed = None

        hours, minutes, seconds = map(int, self.sv.get().split(":"))
        if seconds > 29:
            minutes+=1

        task_id = self.task_id_look_up[self.task_choice.get()]
        self.tasks.hours[task_id].set(hours)
        self.tasks.minutes[task_id].set(minutes)

        self.sv.set(self.all_zeros)


    @staticmethod
    def format_time(elap):
        hours = int(elap / 3600)
        minutes = int(elap / 60 - hours * 60)
        seconds = int(elap - hours * 3600 - minutes * 60)

        return "%02d:%02d:%02d" % (
            hours,
            minutes,
            seconds
        )

class Schedule(ttk.Frame):
    def __init__(self, new_frame, parent):
        super().__init__(
            new_frame,
            padding=10,
            style="Card.TFrame"
        )

        self.parent = parent
        self.tasks = parent.tasks
        self.day_choice = None

        task_label = ttk.Label(
            self,
            text="Create Task",
            style="Heading.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        # ==========================================
        # Subject / Task Frame
        # ==========================================

        self.task_info_frame = ttk.Frame(
            self,
            style="Card.TFrame",
        )

        self.task_info_frame.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        # Everything inside radio_frame uses pack().
        self.target_type = tk.StringVar(value="subject")

        radio_frame = ttk.Frame(
            self.task_info_frame,
            style="Card.TFrame",
        )
        
        radio_frame.pack(side='left', padx=(0, 6),pady=(0, 5))

        radio_label = ttk.Label(
            radio_frame,
            text="Task For",
            style="Muted.TLabel"
        )
        
        radio_label.pack(anchor="w", pady=(5, 5))

        # Separate frame lets us pack the two
        # radio buttons next to each other.
        radio_button_container = ttk.Frame(
            radio_frame,
            style="Card.TFrame",
        )

        radio_button_container.pack(
            anchor="w"
        )

        subject_button = ttk.Radiobutton(
            radio_button_container,
            text="Subject",
            variable=self.target_type,
            # command=self.update_choices,
            value="subject",
            cursor="hand2",
            style="White.TRadiobutton"
        )
        
        subject_button.pack(side="left", padx=(0, 8))

        project_button = ttk.Radiobutton(
            radio_button_container,
            text="Project",
            variable=self.target_type,
            # command=self.update_choices,
            value="project",
            cursor="hand2",
            style="White.TRadiobutton"
        )
        
        project_button.pack(side="left")

        # Project
        self.project = EntryField(self.task_info_frame, "Project", "new_task_project_input")
        self.project.pack(side='left',padx=(0, 6),pady=(0, 5))

        # Task
        self.task_name = EntryField(self.task_info_frame, "Task", "new_task")
        self.task_name.pack(side='left',padx=(0, 6),pady=(0, 5))

        # ==========================================
        # Recurrence Frame
        # ==========================================

        self.recurrence_frame = ttk.Frame(
            self,
            style="Card.TFrame",
        )

        self.recurrence_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(10, 0)
        )

        for column in range(4):
            self.recurrence_frame.columnconfigure(
                column,
                weight=1,
                uniform="recurrence"
            )

        # Frequency
        self.frequency = DropdownField(self.recurrence_frame, "Task Frequency", 'frequency', ["One Off", "Daily", "Weekly"], default="One Off")
        self.frequency.pack(side='left',padx=(0, 6),pady=(0, 5))

        # Initial One-Off date field
        self.create_one_off_fields()

        self.parent.widgets['frequency'].bind(
            "<<ComboboxSelected>>",
            self.frequency_adjustment
        )

        # ==========================================
        # Submit / Error Frame
        # ==========================================

        self.submit_frame = ttk.Frame(
            self,
            style="Card.TFrame",
        )

        self.submit_frame.grid(
            row=3,
            column=0,
            sticky="w",
            pady=(12, 0)
        )

        self.error_text = tk.StringVar()

        button = ttk.Button(
            self.submit_frame,
            cursor="hand2",
            text="Add Task",
            style="Accent.TButton",
            command=self.submit_new_record
        )

        button.grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.error_label = ttk.Label(
            self.submit_frame,
            textvariable=self.error_text,
            style="Error.TLabel",
            wraplength=180
        )

        self.error_label.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(12, 0)
        )
    def clear_calendars(self):
        for widget in self.recurrence_frame.winfo_children():
            if widget is not self.frequency:
                widget.destroy()

    def create_one_off_fields(self):
        self.day_choice = None
        self.start_date = None
        self.end_date = None

        self.one_off = CalendarField(self.recurrence_frame, "Choose Date", 'one_off')
        self.one_off.pack(side='left', padx=(0, 6),pady=(0, 5))

    def create_daily_fields(self):
        self.day_choice = None
        self.calendar = None

        self.start_date = CalendarField(self.recurrence_frame, "Choose Start Date", 'start_date')
        self.start_date.pack(side='left', padx=(0, 6),pady=(0, 5))

        self.end_date = CalendarField(self.recurrence_frame, "End Date", 'end_date')
        self.end_date.pack(side='left', padx=(0, 6),pady=(0, 5))


    def create_weekly_fields(self):
        self.calendar = None
        days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        self.weekdays = DropdownField(self.recurrence_frame, "Choose Day", 'day_of_week', days, default="Friday")
        self.weekdays.pack(side='left',padx=(0, 6), pady=(0, 5))

    def frequency_adjustment(self, event=None):
        frequency = self.frequency.value.get()

        if frequency == "One Off":
            self.self.clear_calendars()
            self.self.create_one_off_fields()

        elif frequency == "Daily":
            self.clear_calendars()
            self.create_daily_fields()

        elif frequency == "Weekly":
            self.clear_calendars()
            self.create_daily_fields()
            self.create_weekly_fields()

    def submit_new_record(self):
        try:
            subject = self.subject.get().strip().lower()
            task = self.task_name.get().strip().lower()
            frequency = self.frequency.get().lower()

            combinations = []
            for task_info in self.tasks.days_items.values():
                task_name = task_info['task'].strip().lower()
                task_subject = task_info['subject'].strip().lower()
                combinations.append((task_subject, task_name))

            if (subject, task) in combinations and frequency == 'one off':
                self.error_text.set("That's already scheduled.")
                return

            if not task:
                self.error_text.set("Please enter a task name.")
                return

            if not subject:
                self.error_text.set("Please choose a subject.")
                return

            if frequency == "one off":
                self.parent.insert_record(
                    self.one_off.get(),
                    self.subject.get().strip(),
                    self.task_name.get().strip()
                )
                return

            if self.day_choice is not None:
                day = self.day_choice.get()
            else:
                day = None

            self.parent.insert_recurring_task(
                self.subject.get().strip(),
                self.tasks.get().strip(),
                frequency,
                day=day
            )

            self.error_text.set("")
            self.subject.delete(0, tk.END)
            self.task_name.delete(0, tk.END)

        finally:
            self.tasks.check_for_new_records()
            self.parent.timer.get_stop_watch_options()

class Visuals(ttk.Frame):
    def __init__(self, notebook, parent, df):
        super().__init__(parent, style="Card.TFrame", )

        self.parent = parent
        self.df = df
        self.today = datetime.today()

        self.canvas = None
        self.fig = None

        self.header_frame = ttk.Frame(self)
        self.header_frame.grid(row=0, column=0, sticky='ew')

        date_choice_label = ttk.Label(
            self.header_frame,
            text="Choose Date Range",
            style="Heading.TLabel",
        )
        date_choice_label.grid(row=0, column=0)

        self.date_option = tk.StringVar(value="Last Week")
        self.date_dropdown = ttk.Combobox(
            self.header_frame,
            textvariable=self.date_option,
            values=["Last Week", "Last Month", "Last Year"],
            state="readonly"
        )
        self.date_dropdown.grid(row=1, column=0, padx=5)

        self.date_dropdown.bind(
            "<<ComboboxSelected>>",
            lambda x: self.update_tabs()
        )

    def update_tabs(self):
        self.parent.get_start_and_end_dates(self.date_option.get())
        self.parent.filter_dates(self.parent.start, self.parent.end)
        self.plot_study((self.parent.start, self.parent.end))

    def filter_and_group(self, data, dates, freq='daily'):
        start, end = map(pd.Timestamp, dates)

        data = data.copy()
        data['date'] = pd.to_datetime(data['date']).dt.normalize()

        frequency = {'daily': 'D', 'weekly': 'W'}[freq]

        return (
            data.loc[data['date'].between(start, end)]
                .groupby([
                    pd.Grouper(key='date', freq=frequency),
                    'subject',
                ])[['minutes']]
                .sum()
                .reset_index()
                .sort_values('date')
        )

    def clean_data(self, data, dates, freq='daily', subject=None):
        start, end = map(pd.Timestamp, dates)

        offset = {
            'daily': pd.offsets.Day(),
            'weekly': pd.offsets.Week(weekday=6),
        }[freq]

        period_dates = pd.date_range(
            offset.rollforward(start),
            offset.rollforward(end),
            freq=offset,
        )

        if subject is not None:
            data = data.loc[data['subject'].eq(subject)]

        return (
            data.groupby('date')['minutes']
                .sum()
                .reindex(period_dates, fill_value=0)
                .tolist()
        )

    def plot_study(self, dates, total=False):
        start, end = [pd.Timestamp(date).normalize() for date in dates]
        dates = (start, end)

        if end <= start + pd.DateOffset(months=1):
            freq = 'daily'
            plot_dates = pd.date_range(start, end, freq='D')
        else:
            freq = 'weekly'
            sunday = pd.offsets.Week(weekday=6)
            plot_dates = pd.date_range(
                sunday.rollforward(start),
                sunday.rollforward(end),
                freq='W',
            )

        subjects = self.df['subject'].dropna().unique().tolist()

        selected = self.df.loc[self.df['subject'].isin(subjects)]
        grouped = self.filter_and_group(selected, dates, freq)

        # Remove the previous chart.
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            plt.close(self.fig)

        self.fig, ax = plt.subplots(figsize=(8, 5))
        ax.set_facecolor(UI_COLORS["surface"])
        ax.grid(axis="y")
        ax.tick_params(axis="both", length=0, pad=7)

        colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(subjects))]
        bottom = np.zeros(len(plot_dates))

        plot_subjects = [None] if total else subjects

        for i, subject in enumerate(plot_subjects):
            minutes = np.array(
                self.clean_data(grouped, dates, freq, subject)
            )
            label = 'Total' if total else subject
            color = UI_COLORS["accent"] if total else colors[i]

            if freq == 'daily':
                ax.bar(
                    plot_dates,
                    minutes,
                    bottom=bottom,
                    label=label,
                    color=color,
                )
                bottom += minutes
            else:
                ax.plot(
                    plot_dates,
                    minutes,
                    label=label,
                    color=color,
                    marker='o', markersize=4, linewidth=2,
                )

        ax.set_ylabel('Minutes')
        ax.set_title(
            f"{'Daily' if freq == 'daily' else 'Weekly'} Study Time",
            loc="left", pad=16
        )

        if plot_subjects:
            ax.legend(frameon=False, fontsize=9)

        self.fig.autofmt_xdate()
        self.fig.tight_layout()

        # Display the figure inside this frame.
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(
            row=1, column=0, sticky="nsew"
        )

        # Allow the chart's row and column to expand.
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
      
class Analytics(ttk.Frame):
    def __init__(self, notebook, parent):
        super().__init__(
            notebook,
            style="Card.TFrame",
        )

        self.parent = parent
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.header_frame = ttk.Frame(
            self,
            style="Card.TFrame",
        )
        self.header_frame.grid(
            row=0, column=0, sticky="ew", padx=10, pady=10
        )

        ttk.Label(
            self.header_frame,
            text="Choose Date Range",
            style="Heading.TLabel",
        ).grid(row=0, column=0, sticky="w")

        self.date_option = tk.StringVar(value="Last Week")

        self.date_dropdown = ttk.Combobox(
            self.header_frame,
            textvariable=self.date_option,
            values=["Last Week", "Last Month", "Last Year"],
            state="readonly",
        )
        self.date_dropdown.grid(
            row=1, column=0, sticky="w", pady=(5, 0)
        )
        self.date_dropdown.bind(
            "<<ComboboxSelected>>",
            lambda event: self.update_tabs(),
        )

        self.bottom_frame = ttk.Frame(
            self,
            style="Card.TFrame",
        )
        self.bottom_frame.grid(
            row=1, column=0, sticky="nsew"
        )
        self.bottom_frame.rowconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(
            0, weight=1, uniform="equal"
        )
        self.bottom_frame.columnconfigure(
            1, weight=1, uniform="equal"
        )

        self.bottom_left_frame = ttk.Frame(
            self.bottom_frame,
            style="Card.TFrame",
        )
        self.bottom_left_frame.grid(
            row=0, column=0, sticky="nsew"
        )

        for column in range(3):
            self.bottom_left_frame.columnconfigure(
                column, weight=1, uniform="cards"
            )

        for row in range(2):
            self.bottom_left_frame.rowconfigure(
                row, weight=1, uniform="cards"
            )

        self.bottom_right_frame = ttk.Frame(
            self.bottom_frame,
            style="Card.TFrame",
        )
        self.bottom_right_frame.grid(
            row=0, column=1, sticky="nsew", padx=8, pady=8
        )
        self.bottom_right_frame.columnconfigure(0, weight=1)
        self.bottom_right_frame.rowconfigure(0, weight=1)

        # Create the cards once and retain their instances
        self.cards = []

        for i in range(6):
            row, column = divmod(i, 3)

            card = StatCard(
                self.bottom_left_frame,
                title="",
                value="",
            )
            sticky = "new" if row==1 else "sew"
            card.grid(
                row=row,
                column=column,
                sticky=sticky,
                padx=8,
                pady=8,
            )

            self.cards.append(card)

        self.subject_table = TreeView(
            parent=self.bottom_right_frame,
            title="Summary by Subject",
            columns=("subject", "time", "completed", "rate"),
            names=("Subject", "Study Time", "Completed", "Completion"),
            default_widths=(120, 100, 100, 100),
        )
        self.subject_table.grid(
            row=0, column=0, sticky="nsew"
        )

        self.update_tabs()

    def update_tabs(self):
        self.parent.get_start_and_end_dates(self.date_option.get())
        self.parent.filter_dates(self.parent.start, self.parent.end)
        self.update_cards()
        self.update_subject_tree()

    def update_cards(self):
        card_values = [
            self.get_total_study_time(),
            self.tasks_completed(),
            self.study_days(),
            self.most_studied(),
            self.most_consistent(),
            self.most_skipped(),
        ]

        for card, (title, value, subtitle) in zip(
            self.cards, card_values
        ):
            card.set_title(title)
            card.set_value(value)
            card.set_subtitle(subtitle)

    def update_subject_tree(self):
        summary = self.parent.df_filt.groupby("subject").agg(
            total_minutes=("minutes", "sum"),
            total_tasks=("completed", "size"),
            total_completed=("completed", "sum"),
            completion_rate=("completed", "mean"),
        )

        tree = self.subject_table.tree
        current_ids = set()

        for (subject, result) in summary.iterrows():
            row_id = f"subject:{subject}"
            current_ids.add(row_id)

            values = (
                subject,
                self.format_minutes(result["total_minutes"]),
                f"{int(result['total_completed'])} "
                f"of {int(result['total_tasks'])}",
                f"{result['completion_rate']:.0%}",
            )

            self.subject_table.insert_row(values=values,iid=row_id)

        for row_id in tree.get_children():
            if row_id not in current_ids:
                tree.delete(row_id)

    def format_minutes(self, minutes):
        hours, minutes = divmod(int(minutes), 60)
        return f"{hours}h {minutes:02d}m"

    def get_total_study_time(self):
        total_time = self.parent.df_filt["minutes"].sum()
        subjects = self.parent.df_filt.loc[
            self.parent.df_filt["minutes"] > 0, "subject"
        ].nunique()

        return (
            "Total study time",
            self.format_minutes(total_time),
            f"Across {subjects} subjects",
        )

    def tasks_completed(self):
        total_tasks = len(self.parent.df_filt)
        completed = int(self.parent.df_filt["completed"].eq(1).sum())
        rate = completed / total_tasks if total_tasks else 0

        return (
            "Tasks completed",
            f"{completed} of {total_tasks}",
            f"{rate:.0%} completion",
        )

    def study_days(self):
        dates = pd.to_datetime(
            self.parent.df_filt.loc[self.parent.df_filt["minutes"] > 0, "date"]
        )
        days = dates.dt.normalize().nunique()

        return (
            "Study days",
            f"{days} of {self.parent.period_days}",
            "Days with time recorded",
        )

    def most_studied(self):
        totals = self.parent.df_filt.groupby("subject")["minutes"].sum()
        total_time = totals.sum()

        if totals.empty or total_time == 0:
            return (
                "Most studied",
                "—",
                "No study time recorded",
            )

        subject = totals.idxmax()
        minutes = totals.loc[subject]
        share = minutes / total_time

        return (
            "Most studied",
            subject,
            f"{self.format_minutes(minutes)} · "
            f"{share:.0%} of study time",
        )

    def past_task_summary(self):
        today = pd.Timestamp.today().normalize()

        past = self.parent.df_filt.loc[
            pd.to_datetime(self.parent.df_filt["date"]) < today
        ]

        return past.groupby("subject").agg(
            total_tasks=("completed", "size"),
            total_completed=("completed", "sum"),
            completion_rate=("completed", "mean"),
        )

    def most_consistent(self):
        summary = self.past_task_summary()

        if summary.empty:
            return ("Most consistent", "—", "No past tasks")

        subject = summary["completion_rate"].idxmax()
        result = summary.loc[subject]

        return (
            "Most consistent",
            subject,
            f"Completed {int(result['total_completed'])} "
            f"of {int(result['total_tasks'])} past tasks",
        )

    def most_skipped(self):
        summary = self.past_task_summary()

        if summary.empty:
            return ("Most skipped", "—", "No past tasks")

        summary["skipped"] = (
            summary["total_tasks"] - summary["total_completed"]
        )

        if summary["skipped"].sum() == 0:
            return ("Most skipped", "None", "No past tasks skipped")

        subject = summary["completion_rate"].idxmin()
        result = summary.loc[subject]

        return (
            "Most skipped",
            subject,
            f"Skipped {int(result['skipped'])} "
            f"of {int(result['total_tasks'])} past tasks",
        )

class TaskManager(ttk.Frame):
    def __init__(self, notebook, parent):
        super().__init__(
            notebook,
            style="Page.TFrame",
            padding=10,
        )
        self.root = self.winfo_toplevel()

        self.dataset_lookup = {
            "Sessions": {
                "table": "sessions",
                "title": "Task History",
                "columns": (
                    "date", "subject", "task",
                    "minutes", "completed", "canceled",
                ),
                "names": (
                    "Date", "Subject", "Task Name",
                    "Minutes", "Completed", "Canceled",
                ),
                "default_widths": (100, 100, 200, 100, 100, 100),
            },
            "Recurring tasks": {
                "table": "recurring_tasks",
                "title": "Recurring Tasks",
                "columns": (
                    "subject", "task", "frequency",
                    "day", "start_date", "end_date",
                ),
                "names": (
                    "Subject", "Task Name", "Frequency",
                    "Day", "Start Date", "End Date",
                ),
                "default_widths": (100, 200, 100, 100, 100, 100),
            },
        }

        self.current_dataset = None

        self.dataset_choice = tk.StringVar(value="Sessions")

        self.header_frame = ttk.Frame(self, style="Card.TFrame")
        self.header_frame.grid(
            row=0, column=0, sticky="ew", pady=(0, 10)
        )
        self.header_frame.columnconfigure(1, weight=1)

        # Search label and entry
        self.search_label = ttk.Label(
            self.header_frame,
            text="Search:",
        )
        self.search_label.grid(row=0, column=0, padx=(0, 8))

        self.search_text = tk.StringVar()

        self.search_entry = ttk.Entry(
            self.header_frame,
            textvariable=self.search_text,
            cursor="xterm",
        )
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 20))

        # Dataset label and dropdown
        self.dataset_label = ttk.Label(
            self.header_frame,
            text="Dataset:",
        )
        self.dataset_label.grid(
            row=0, column=4, padx=(20, 8)
        )

        self.dataset_combo = ttk.Combobox(
            self.header_frame,
            textvariable=self.dataset_choice,
            values=tuple(self.dataset_lookup),
            state="readonly",
            width=20,
        )
        self.dataset_combo.grid(
            row=0, column=5
        )

        # Switch tables when the user selects a dataset
        self.dataset_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.generate_tree(self.dataset_choice.get()),
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.generate_tree(self.dataset_choice.get())

        # Delete label and button
        self.delete_label = ttk.Label(
            self.header_frame,
            text="Selected row:",
        )
        self.delete_label.grid(row=0, column=2, padx=(0, 8))

        self.delete_button = ttk.Button(
            self.header_frame,
            text="Delete",
            cursor="hand2",
            command=self.current_dataset.delete_selected
        )
        self.delete_button.grid(row=0, column=3)

    def generate_tree(self, dataset):
        settings = self.dataset_lookup[dataset]

        # Retrieve the selected DataFrame already in memory
        self.table_name = settings["table"]
        df = self.root.data_lookup[self.table_name]

        # Remove the previous table
        if self.current_dataset is not None:
            self.current_dataset.destroy()

        self.current_dataset = TreeView(
            parent=self,
            title=settings["title"],
            columns=settings["columns"],
            names=settings["names"],
            default_widths=settings["default_widths"],
        )
        self.current_dataset.dataset = settings["table"]
        self.current_dataset.grid(
            row=1, column=0, sticky="nsew"
        )

        # Use database IDs as row IDs and match the display column order
        display_df = df.set_index("id")[list(settings["columns"])]
        self.current_dataset.load_dataframe(display_df)

        # Save the new table's row IDs for searching
        self.all_row_ids = self.current_dataset.tree.get_children()

        self.current_dataset.search_table(self.search_text)

class ProjectPage(ttk.Frame):
    def __init__(self, notebook, parent):
        super().__init__(
            parent,
            padding=15,
            style="Page.TFrame",
        )

        self.parent = parent
        self.projects = {}

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Create a project
        header = ttk.Frame(
            self,
            padding=12,
            style="Card.TFrame",
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header.columnconfigure(1, weight=1)

        ttk.Label(
            header,
            text="New project:",
            style="Heading.TLabel",
        ).grid(row=0, column=0, padx=(0, 8))

        self.project_name = ttk.Entry(header, cursor="xterm")
        self.project_name.grid(row=0, column=1, sticky="ew")
        self.project_name.bind("<Return>", self.add_project)

        self.add_button = ttk.Button(
            header,
            text="Add project",
            command=self.add_project,
            cursor="hand2",
            style="Accent.TButton",
        )
        self.add_button.grid(row=0, column=2, padx=(8, 0))

        self.project_count = ttk.Label(
            header,
            text="0 / 3 active projects",
            style="Muted.TLabel",
        )
        self.project_count.grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )

        # Three equally sized project columns
        self.project_frame = ttk.Frame(
            self,
            style="Page.TFrame",
        )
        self.project_frame.grid(row=1, column=0, sticky="nsew")
        self.project_frame.rowconfigure(0, weight=1)

        for column in range(3):
            self.project_frame.columnconfigure(
                column, weight=1, uniform="projects"
            )

        self.fill_existing_projects()

    def add_project(self, event=None):
        name = self.project_name.get().strip()

        if not name or len(self.projects) >= 3:
            return

        new_id = self.parent.insert_project(name)

        self.projects[new_id] = ProjectCard(
            self.project_frame,
            name,
            new_id,
            on_complete=self.complete_project,
        )
        self.project_name.delete(0, "end")
        self.arrange_projects()

    def fill_existing_projects(self):
        for saved_project in self.parent.active_project_records:
            existing_id = saved_project['id']
            name = saved_project['name']
            self.projects[existing_id] = ProjectCard(
                self.project_frame,
                name,
                existing_id,
                on_complete=self.complete_project,
            )
            self.arrange_projects()

    def complete_project(self, project):
        self.projects.remove(project)
        project.destroy()
        self.arrange_projects()

    def arrange_projects(self):
        for column, project in enumerate(self.projects.values()):
            project.grid(
                row=0, column=column, sticky="nsew", padx=5
            )

        count = len(self.projects)
        self.project_count["text"] = f"{count} / 3 active projects"
        self.add_button["state"] = (
            "disabled" if count == 3 else "normal"
        )

#####################
# Sub Frame Classes
#####################

class StatCard(ttk.Frame):

    def __init__(self, parent, title, value, subtitle=None):
        super().__init__(parent, padding=18, style="StatCard.TFrame")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # No sticky: the content stays centered inside this cell.
        self.content = ttk.Frame(self, style="Card.TFrame")
        self.content.grid(row=0, column=0)

        self.title_label = ttk.Label(
            self.content,
            text=title.upper(),
            style="Muted.TLabel",
            anchor="center",
            justify="center",
        )
        self.title_label.pack(fill="x")

        self.value_label = ttk.Label(
            self.content,
            text=value,
            style="Metric.TLabel",
            anchor="center",
            justify="center",
        )
        self.value_label.pack(fill="x", pady=(8, 0))

        self.subtitle_label = ttk.Label(
            self.content,
            text=subtitle or "",
            style="Muted.TLabel",
            anchor="center",
            justify="center",
        )
        if subtitle:
            self.subtitle_label.pack(fill="x")

    def set_title(self, title):
        self.title_label.configure(text=title.upper())

    def set_value(self, value):
        self.value_label.configure(text=value)

    def set_subtitle(self, subtitle):
        self.subtitle_label.configure(text=subtitle or "")

        if subtitle:
            self.subtitle_label.pack(fill="x")
        else:
            self.subtitle_label.pack_forget()

class TreeView(ttk.Frame):
    def __init__(self, parent, title, columns, names, default_widths):
        super().__init__(parent, style="Card.TFrame")

        self.names = columns
        self.parent = parent
        self.root = self.winfo_toplevel()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(
            self,
            text=title,
            style="Heading.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        # Frame containing the table and scrollbar
        tree_frame = ttk.Frame(
            self,
            style="Card.TFrame",
        )
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=8,
            style="TaskManager.Treeview",
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        for column, name, width in zip(columns, names, default_widths):
            self.tree.heading(column, text=name)
            self.tree.column(
                column,
                width=width,
                minwidth=60,
                anchor="w",
            )

        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.configure(style="TaskManager.Treeview")

        for column in self.tree["columns"]:
            self.tree.heading(
                column,
                command=lambda col=column: self.sort_values(col),
            )

        self.tree.bind("<Double-1>", lambda event: self.onDoubleClick(event))

    def insert_row(self, values, iid=None):
        if self.tree.exists(iid):
            self.tree.item(iid, values=values)
        else:
            self.tree.insert("","end",iid=iid,values=values)

    def sort_values(self, column, descending=False):

        self.column_sort_date = {other_column:None for other_column in self.tree["columns"] if other_column != column}

        row_ids = self.tree.get_children()

        def get_name(row_id):
            value = self.tree.set(row_id, column)

            try:
                return float(value)
            except ValueError:
                return value.casefold()

        sorted_ids = sorted(row_ids, key=get_name, reverse=descending)

        for position, row_id in enumerate(sorted_ids):
            self.tree.move(row_id, "", position)

        self.tree.heading(
            column,
            command=lambda col=column: self.sort_values(col, descending=not descending),
        )

    def load_dataframe(self, df):
        current_ids = set()

        for index, row in df.iterrows():
            row_id = str(index)
            current_ids.add(row_id)

            self.insert_row(
                values=tuple(row),
                iid=row_id,
            )

        for row_id in self.tree.get_children():
            if row_id not in current_ids:
                self.tree.delete(row_id)

    def onDoubleClick(self, event):
            '''Executed, when a row is double-clicked'''
            # close previous popups
            try:  # in case there was no previous popup
                self.entryPopup.destroy()
            except AttributeError:
                pass

            # what row and column was clicked on
            rowid = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)

            # return if the header was double clicked
            if not rowid:
                return

            # Get cell position and dimensions
            x, y, width, height = self.tree.bbox(rowid, column)

            # Get cell text
            column_index = int(column[1:]) - 1
            text = self.tree.item(rowid, "values")[column_index]

            column_name = self.names[column_index]

            # Create and position the entry over the cell
            self.entryPopup = EntryPopup(self, rowid, column_index, text)
            self.entryPopup.place(
                in_=self.tree,
                x=x,
                y=y,
                width=width,
                height=height,
                anchor="nw",
            )

    def delete_selected(self):
        selected = self.tree.selection()

        if not selected:
            return

        row_id = selected[0]
        self.tree.delete(row_id)
        self.root.delete_record(self.dataset, row_id)

    def search_table(self, string_variable):
        self.all_row_ids = self.tree.get_children()

        self.current_entry = string_variable
        self.current_entry.trace_add("write", self.search_rows)

    def search_rows(self, *args):
        # we need *args included because trace_add is going to pass 3 argument variable’s name, index and operation.
        # even though we don't need them we have to accept them
        search = self.current_entry.get().strip().casefold()

        for row_id in self.all_row_ids:
            values = self.tree.item(row_id, "values")

            matches = False

            for value in values:
                if search in str(value).casefold():
                    matches = True
                    break

            if matches:
                self.tree.move(row_id, "", "end")
            else:
                self.tree.detach(row_id)

class ScrollableFrame(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent, 
                         style="Card.TFrame",
                         padding=10)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            background=UI_COLORS["surface"]
        )

        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        self.scrollable_frame = ttk.Frame(
            self.canvas,
            style="Page.TFrame"
        )
        self.scrollable_frame.columnconfigure(0,weight=1)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.canvas.bind(
            "<Configure>",
            self.resize_frame
        )

        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.canvas.bind("<Enter>", self.bind_mousewheel)
        self.canvas.bind("<Leave>", self.unbind_mousewheel)

    def bind_mousewheel(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self.mousewheel)

    def unbind_mousewheel(self, event=None):
        self.canvas.unbind_all("<MouseWheel>")

    def mousewheel(self, event):
        # If all content is visible, don't scroll.
        top, bottom = self.canvas.yview()

        if top <= 0 and bottom >= 1:
            return "break"

        self.canvas.yview_scroll(
            int(-event.delta / 120),
            "units",
        )
        return "break"

    def resize_frame(self, event):
        self.canvas.itemconfigure(
            self.canvas_window,
            width=event.width
        )

class MetricBar(ttk.Frame):
    def __init__(self, parent, title, current, target, text=""):
        super().__init__(
            parent,
            padding=10,
            style="Card.TFrame"        )

        # Card heading
        ttk.Label(
            self,
            text=title,
            style="Heading.TLabel",
        ).pack(anchor="w")

        # Progress toward the target
        self.bar = ttk.Progressbar(
            self,
            maximum=target,
            value=current,
            style="Card.Horizontal.TProgressbar",
        )
        self.bar.pack(fill="x", pady=8)

        ttk.Label(
            self,
            text=f"{current} / {target} — {text}",
            style="Muted.TLabel",
        ).pack(anchor="w")

class CalendarField(ttk.Frame):
    def __init__(self, parent, label_text, tracking_key, **kwargs):
        super().__init__(
            parent,
            style="Card.TFrame",
        )

        self.columnconfigure(0, weight=1)

        self.label = ttk.Label(
            self,
            text=label_text,
            style="Muted.TLabel"
        )

        self.label.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(5, 5)
        )

        self.calendar = DateEntry(
            self,
            cursor="xterm",
            date_pattern="yyyy-mm-dd",

            # Selected date
            selectbackground=UI_COLORS["accent"],
            selectforeground="white",

            # Calendar headers
            headersbackground=UI_COLORS["accent"],
            headersforeground="white",

            # Normal days
            normalbackground="white",
            normalforeground=UI_COLORS["text"],

            # Weekend days
            weekendbackground="white",
            weekendforeground=UI_COLORS["text"],

            # Other month's days
            othermonthbackground="#F3F6FA",
            othermonthforeground="#9AA4B2",

            # Calendar background
            background=UI_COLORS["accent"],
            foreground="white",

            **kwargs
        )

        root = self.winfo_toplevel()
        root.calendars[tracking_key] = self.calendar

        self.calendar.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        self.calendar.bind(
            "<FocusOut>",
            self.close_calendar
        )

        self.calendar.bind(
            "<Escape>",
            self.close_calendar
        )

    def close_calendar(self, event=None):
        self.calendar.event_generate("<Escape>")

    def get(self):
        return self.calendar.get()

class EntryField(ttk.Frame):

    def __init__(self, parent, label_text, tracking_key, width=18, **kwargs):
        super().__init__(
            parent,
            style="Card.TFrame",
        )

        self.columnconfigure(0, weight=1)

        self.label = ttk.Label(
            self,
            text=label_text,
            style="Muted.TLabel"
        )

        self.label.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(5, 5)
        )

        self.widget = ttk.Entry(
            self,
            cursor="xterm",
            width=width,
            **kwargs
        )

        self.widget.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        root = self.winfo_toplevel()
        root.widgets[tracking_key] = self.widget

    def get(self):
        return self.widget.get()

    def clear(self):
        self.widget.delete(0, tk.END)

class DropdownField(ttk.Frame):
    def __init__(
        self,
        parent,
        label_text,
        tracking_key,
        values,
        default=None,
        width=18,
        **kwargs
    ):
        super().__init__(
            parent,
            style="Card.TFrame",
        )

        self.columnconfigure(0, weight=1)

        self.value = tk.StringVar(
            self,
            value=default or ""
        )

        self.label = ttk.Label(
            self,
            text=label_text,
            style="Muted.TLabel"
        )

        self.label.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(5, 5)
        )

        self.widget = ttk.Combobox(
            self,
            textvariable=self.value,
            values=values,
            width=width,
            state="readonly",
            **kwargs
        )

        self.widget.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        root = self.winfo_toplevel()
        root.widgets[tracking_key] = self.widget

    def get(self):
        return self.widget.get()

    def set(self, value):
        self.widget.set(value)

    def bind_selection(self, function):
        self.widget.bind(
            "<<ComboboxSelected>>",
            function
        )

class ProjectCard(ttk.LabelFrame):
    def __init__(self, parent, name, project_id, on_complete):
        super().__init__(
            parent,
            text=name,
            padding=12,
            style="Card.TLabelframe",
        )

        self.project_name = name
        self.project_id = project_id
        self.root = self.winfo_toplevel()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        # Progress
        self.progress = ttk.Progressbar(
            self,
            maximum=100,
            style="Card.Horizontal.TProgressbar",
        )
        self.progress.grid(row=0, column=0, sticky="ew")

        self.progress_text = ttk.Label(
            self,
            text="0 / 0 milestones completed",
            style="Muted.TLabel",
        )
        self.progress_text.grid(
            row=1, column=0, sticky="w", pady=(6, 15)
        )

        # Add a milestone
        ttk.Label(
            self,
            text="New milestone:",
            style="Muted.TLabel",
        ).grid(row=2, column=0, sticky="w")

        entry_frame = ttk.Frame(self, style="Card.TFrame")
        entry_frame.grid(
            row=3, column=0, sticky="ew", pady=(5, 10)
        )
        entry_frame.columnconfigure(0, weight=1)

        self.milestone_name = ttk.Entry(
            entry_frame, width=15, cursor="xterm"
        )
        self.milestone_name.grid(row=0, column=0, sticky="ew")
        self.milestone_name.bind("<Return>", self.add_milestone)

        ttk.Button(
            entry_frame,
            text="Add",
            command=self.add_milestone,
            cursor="hand2",
        ).grid(row=0, column=1, padx=(6, 0))

        # Canvas is a tk widget: set its background directly.
        self.canvas = tk.Canvas(
            self,
            background=UI_COLORS["surface"],
            highlightthickness=0,
            borderwidth=0,
            width=1,
        )
        self.canvas.grid(row=4, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
        )
        scrollbar.grid(row=4, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.milestone_frame = ttk.Frame(
            self.canvas,
            style="Card.TFrame",
        )
        self.milestone_frame.columnconfigure(1, weight=1)

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.milestone_frame,
            anchor="nw",
        )

        self.milestone_frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            ),
        )
        self.canvas.bind("<Configure>", self.resize_milestones)

        self.complete_button = ttk.Button(
            self,
            text="Complete project",
            command=lambda: on_complete(self),
            state="disabled",
            cursor="hand2",
            style="Accent.TButton",
        )
        self.complete_button.grid(
            row=5, column=0, sticky="ew", pady=(12, 0)
        )

        self.add_existing_milestones()

    def add_milestone(self, event=None):
        title = self.milestone_name.get().strip()

        if not title:
            return

        milestone_id = self.root.insert_milestone(self, self.project_id, title)

        self.root.milestones[milestone_id] = tk.BooleanVar(self, value=False)
        row = len(self.root.milestones) - 1

        ttk.Checkbutton(
            self.milestone_frame,
            variable=self.root.milestones[milestone_id],
            command=self.update_progress,
            cursor="hand2",
        ).grid(row=row, column=0, sticky="nw", pady=5)

        ttk.Label(
            self.milestone_frame,
            text=title,
            style="TLabel",
            wraplength=max(50, self.canvas.winfo_width() - 40),
        ).grid(row=row, column=1, sticky="nw", pady=5)

        self.milestone_name.delete(0, "end")
        self.update_progress()

    def add_existing_milestones(self):
        existing_milestones = self.root.milestone_record_lookup[self.project_id]
        for record in existing_milestones:
            name = record['name']
            milestone_id = record['id']
            self.root.milestones[milestone_id] = tk.BooleanVar(self, value=False)
            row = len(self.root.milestones) - 1

            ttk.Checkbutton(
                self.milestone_frame,
                variable=self.root.milestones[milestone_id],
                command=self.update_progress,
                cursor="hand2",
            ).grid(row=row, column=0, sticky="nw", pady=5)

            ttk.Label(
                self.milestone_frame,
                text=name,
                style="TLabel",
                wraplength=max(50, self.canvas.winfo_width() - 40),
            ).grid(row=row, column=1, sticky="nw", pady=5)

            self.milestone_name.delete(0, "end")
            self.update_progress()

    def resize_milestones(self, event):
        self.canvas.itemconfigure(
            self.canvas_window, width=event.width
        )

        for widget in self.milestone_frame.winfo_children():
            if isinstance(widget, ttk.Label):
                widget.configure(
                    wraplength=max(50, event.width - 40)
                )

    def update_progress(self):
        total = len(self.root.milestones)

        completed = sum(variable.get() for variable in self.root.milestones.values())

        self.progress["value"] = (completed / total * 100 if total else 0)

        self.progress_text["text"] = (f"{completed} / {total} milestones completed")

        self.complete_button["state"] = ("normal" if total and completed == total else "disabled")

#####################
# Custom Widgets
#####################

class EntryPopup(ttk.Entry):
    def __init__(self, parent, iid, column, text, **kw):
        super().__init__(parent, **kw)
        self.tv = parent.tree  # reference to parent window's treeview
        self.iid = iid  # row id
        self.column = column 

        self.insert(0, text) 
        self['exportselection'] = False  # Prevents selected text from being copied to  
                                         # clipboard when widget loses focus
        self.focus_force()  # Set focus to the Entry widget
        self.select_all()   # Highlight all text within the entry widget
        self.bind("<Return>", self.on_return) # Enter key bind
        self.bind("<Control-a>", self.select_all) # CTRL + A key bind
        self.bind("<Escape>", lambda *ignore: self.destroy()) # ESC key bind


        self.column_name = parent.names[column]
        self.dataset = parent.dataset
        self.root = self.winfo_toplevel()

    def on_return(self, event):
        '''Insert text into treeview, and delete the entry popup'''
        rowid = self.tv.focus()  # Find row id of the cell which was clicked
        vals = self.tv.item(rowid, 'values')  # Returns a tuple of all values from the row with id, "rowid"
        vals = list(vals)  # Convert the values to a list so it becomes mutable
        user_inputted_value = self.get()
        vals[self.column] = self.get()  # Update values with the new text from the entry widget
        self.tv.item(rowid, values=vals)  # Update the Treeview cell with updated row values
        self.root.update_record(rowid, self.dataset, self.column_name, user_inputted_value)
        self.destroy()  # Destroy the Entry Widget
        
    def select_all(self, *ignore):
        ''' Set selection on the whole text '''
        self.selection_range(0, 'end')
        return 'break' # returns 'break' to interrupt default key-bindings

if __name__ == "__main__":
    main()
