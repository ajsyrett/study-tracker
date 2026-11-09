import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
import sqlite3
from datetime import datetime, timedelta, date
from collections import defaultdict
import time
from pathlib import Path
from tkinter import font as tkfont
from tkcalendar import DateEntry
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.dates as mdates
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
    project_id INTEGER,
    FOREIGN KEY (recurring_id) REFERENCES recurring_tasks(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
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
    end_date TEXT,
    project_id INTEGER,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
"""

opening_query_projects = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    completed INTEGER NOT NULL DEFAULT 0
        CHECK (completed IN (0, 1))
);
"""

opening_query_milestones = """
CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    completed INTEGER NOT NULL DEFAULT 0
        CHECK (completed IN (0, 1)),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
"""

opening_query_targets = """
CREATE TABLE IF NOT EXISTS weekly_targets (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    description TEXT,
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

        self.first_run = True

        configure_appearance(self)
        self.calendars = {}
        self.widgets = {}
        self.milestones = {}
        self.target_charts = {}

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
        self.bind("<Configure>", self.report_window_size, add="+")
        self.load_data()
        self.get_targets()

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
            sticky="new",
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
        self.target_header = ttk.Label(self.weekly_progress, text="Targets This Week", style="Heading.TLabel")
        self.target_header.grid(row=0, column=0, sticky="w")

        self.fill_target_panel()

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

        self.projects = ProjectPage(self.notebook, self)
        self.notebook.add(
            self.projects,
            text="Projects",
        )

        self.visuals_tab = Visuals(self.notebook,self,)

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
        self.first_run = False

    def refresh_data(self):
        # Reload the database data into memory.
        self.load_data()

        if self.data_lookup['sessions'].empty:
            return

        # Recalculate weekly target progress.
        self.get_targets()

        # During startup, the tabs may not exist yet.
        if self.first_run:
            return

        # Update the weekly target panel.
        self.fill_target_panel()

        # Update both tabs directly.
        self.visuals_tab.update_tabs()
        self.analytics_tab.update_tabs()
        self.timer.update_options()

    def report_window_size(self, event):
        # Ignore resize events from child widgets.
        if event.widget is not self:
            return

        size = (event.width, event.height)

        # Only print when the window's dimensions change.
        if size != getattr(self, "_last_window_size", None):
            self._last_window_size = size
            print("Window size:", size)

    def load_data(self):
        rows = self.conn.execute("SELECT * FROM sessions").fetchall()
        sessions = pd.DataFrame([dict(row) for row in rows])

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

        if self.data_lookup['sessions'].empty:
            self.subjects = []
            self.projects_list = []
            self.project_ids = []
            self.project_lookup = {}
            return

        self.subjects = self.data_lookup['sessions']['subject'].unique().tolist()

        if self.data_lookup['projects'].empty:
            self.projects_list = []
            self.project_ids = []
            self.project_lookup = {}
            return
        
        projects_df = (
            self.data_lookup["projects"]
            .drop_duplicates(subset="name", keep="first")
        )

        if self.data_lookup["projects"].shape != projects_df.shape:
            print('multiple records removed')

        self.projects_list = projects_df["name"].tolist()
        self.project_ids = projects_df["id"].tolist()
        self.project_lookup = dict(zip(self.projects_list, self.project_ids))

    def get_targets(self):
        # code to set up the weekly targets to fill into the lower left panel
        sessions = self.data_lookup['sessions']

        if self.data_lookup['sessions'].empty or self.data_lookup['weekly_targets'].empty:
            return

        if not self.first_run:
            rows = self.conn.execute("SELECT * FROM weekly_targets").fetchall()
            weekly_targets = pd.DataFrame([dict(row) for row in rows])
            query = """
            SELECT *
            FROM sessions
            WHERE completed = 1
            AND date >= date('now', 'localtime', 'weekday 0', '-6 days')
            AND date < date('now', 'localtime', 'weekday 0', '+1 day');
            """
            rows = self.conn.execute(query).fetchall()
            last_week_data = pd.DataFrame([dict(row) for row in rows])
        else:
            weekly_targets = self.data_lookup['weekly_targets']
            sessions = self.data_lookup['sessions']

            today = date.today()
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)

            monday = monday.strftime("%Y-%m-%d")
            sunday = sunday.strftime("%Y-%m-%d")

            last_week_data = sessions.query('date >= @monday and date <= @sunday and completed == 1')


        sessions["common_id"] = sessions["project_id"].fillna(sessions["subject"])
        
        x = last_week_data.groupby('subject', as_index = False)[['minutes','completed']].sum()\
            .assign(hours=lambda df: df["minutes"] / 60)\
            .rename(columns = {'subject':'common_id'})

        y = last_week_data.groupby('project_id', as_index = False)[['minutes','completed']].sum()\
            .assign(hours=lambda df: df["minutes"] / 60)\
            .rename(columns = {'project_id':'common_id'})

        last_week_data = pd.concat([x,y])

        # filter down to the active targets.  we only want 3 max so we'll raise an error if there's more
        active_targets = weekly_targets.query('active == 1')[['subject', 'description', 'project_id', 'metric', 'target','id']]
        if len(active_targets) > 3:
            raise ValueError("You cannot have more than 3 targets.")

        def classify_type(row):
           subject_col = row['subject']
           if pd.isna(subject_col):
               return 'project'
           return 'subject'

        active_targets["applied_to"] = active_targets.apply(classify_type, axis=1)
        active_targets["common_id"] = active_targets["project_id"].fillna(active_targets["subject"])

        last_week_data["common_id"] = last_week_data["common_id"].astype(object)
        active_targets["common_id"] = active_targets["common_id"].astype(object)

        combined_df = active_targets.merge(
            last_week_data,
            on="common_id",
            how="left",
        )

        # Targets without matching sessions start at zero.
        columns = ["minutes", "hours", "completed"]
        combined_df[columns] = combined_df[columns].fillna(0)

        def get_metric_column(row):

           metric = row['metric']
           if metric == 'completed':
               return row['completed']
           elif metric == 'minutes':
               return row['minutes']
           else:
               return row['hours']
 
        combined_df['current'] = combined_df.apply(get_metric_column, axis=1)
        cols = ['id', 'description','metric', 'current', 
                'target', 'applied_to', 'common_id']
        self.target_subjects = combined_df[cols]

    def fill_target_panel(self):

        if self.data_lookup['sessions'].empty or self.data_lookup['weekly_targets'].empty:
            ttk.Label(
                self.weekly_progress,
                text="No goals this week get your shit together",
                style="Muted.TLabel",
            ).grid(row=1, column=0, sticky="w", padx=10, pady=10)
            return
        
        target_df = self.target_subjects
        
        if target_df.empty:
            ttk.Label(
                self.weekly_progress,
                text="No goals this week get your shit together",
                style="Muted.TLabel",
            ).grid(row=1, column=0, sticky="w", padx=10, pady=10)
            return


        for i in range(1, len(target_df) + 1):
            j = i-1
            _id = target_df.loc[j,'id']
            metric = target_df.loc[j,'metric']
            title = target_df.loc[j,'description']
            print(title)
            current = target_df.loc[j,'current']
            target = target_df.loc[j,'target']
            
            # in the tables we have a completed column.  that means tasked completed
            # so we change it to task so that it will read tasks completed
            metric = metric if metric != 'completed' else 'tasks'
            text = f"{metric} completed"

            self.target_charts[_id] = MetricBar(self.weekly_progress, title, current, metric, target, text=text)
            self.target_charts[_id].grid(column=0, row=i, sticky='ew')

    def insert_weekly_target(
        self,
        description,
        metric,
        target,
        subject=None,
        project_id=None,
        active=1,
    ):
        # Supply either a subject or a project_id, but not both.
        if (subject is None) == (project_id is None):
            raise ValueError("Choose either a subject or a project.")

        date = datetime.now().strftime("%Y-%m-%d")

        cursor = self.conn.execute(
            """
            INSERT INTO weekly_targets
                (date, description, subject, project_id, metric, target, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (date, description, subject, project_id, metric, target, active),
        )
        self.conn.commit()

        new_id = cursor.lastrowid
        self.refresh_data()
        return new_id

    def insert_project(self, name, completed=0):
        start_date = datetime.now().strftime("%Y-%m-%d")

        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO projects (name, completed, start_date)
                VALUES (?, ?, ?)
                """,
                (name, completed, start_date),
            )

        new_id = cursor.lastrowid
        self.refresh_data()
        return new_id

    def insert_milestone(self, project_id, name, completed=0):
        start_date = datetime.now().strftime("%Y-%m-%d")

        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO milestones (project_id, name, completed, start_date)
                VALUES (?, ?, ?, ?)
                """,
                (project_id, name, completed, start_date),
            )

        new_id = cursor.lastrowid
        self.refresh_data()
        return new_id

    def retrieve_records(self, date):
        return self.conn.execute(
            """
            SELECT * FROM sessions
            WHERE date = ?
            AND canceled != 1
            """,
            (date,),
        ).fetchall()

    def retrieve_active_targets(self):
        return self.conn.execute(
            """
            SELECT * FROM weekly_targets
            WHERE active = 1
            """
        ).fetchall()

    def retrieve_recurring_tasks(self, date):
        # Get the weekday for the selected date.
        day = datetime.strptime(date, "%Y-%m-%d").strftime("%A")

        return self.conn.execute(
            """
            SELECT *
            FROM recurring_tasks
            WHERE (
                frequency = 'daily'
                OR (frequency = 'weekly' AND day = ?)
            )
            AND (
                start_date IS NULL
                OR start_date <= ?
            )
            AND (
                end_date IS NULL
                OR end_date >= ?
            )
            AND id NOT IN (
                SELECT recurring_id
                FROM sessions
                WHERE date = ?
                AND recurring_id IS NOT NULL
            )
            """,
            (day, date, date, date),
        ).fetchall()

    def insert_record(
        self,
        date,
        subject,
        task,
        minutes=0,
        completed=0,
        canceled=0,
        recurring_id=None,
        project_id=None,
    ):
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO sessions (
                    date, subject, task, minutes, completed,
                    canceled, recurring_id, project_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    date, subject, task, minutes, completed,
                    canceled, recurring_id, project_id,
                ),
            )

        self.refresh_data()

    def insert_recurring_task(
        self, subject, task, frequency, day=None, start_date=None, end_date=None, project_id=None
    ):
        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO recurring_tasks (
                    subject, task, frequency, day, start_date, end_date, project_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (subject, task, frequency, day, start_date, end_date, project_id),
            )

        new_id = cursor.lastrowid
        self.refresh_data()
        return new_id

    def update_task(self, id, minutes, completed):
        with self.conn:
            self.conn.execute(
                """
                UPDATE sessions
                SET minutes = ?, completed = ?
                WHERE id = ?
                """,
                (minutes, completed, id),
            )

        self.refresh_data()

    def cancel_record(self, id):
        with self.conn:
            self.conn.execute(
                """
                UPDATE sessions
                SET canceled = 1
                WHERE id = ?
                """,
                (id,),
            )

        self.refresh_data()

    def delete_record(self, table, id):
        with self.conn:
            self.conn.execute(
                f"""
                DELETE FROM {table}
                WHERE id = ?
                """,
                (id,),
            )

        self.refresh_data()

    def update_record(self, id, table, column, value):
        try:
            value = int(value)
        except ValueError:
            pass

        id = int(id)

        with self.conn:
            self.conn.execute(
                f"""
                UPDATE {table}
                SET {column} = ?
                WHERE id = ?
                """,
                (value, id),
            )

        self.refresh_data()

    def update_milestone(self, milestone_id, completed):
        completed = int(completed)

        # Clear the end date when the milestone is unchecked.
        end_date = datetime.now().strftime("%Y-%m-%d") if completed else None

        with self.conn:
            self.conn.execute(
                """
                UPDATE milestones
                SET completed = ?, end_date = ?
                WHERE id = ?
                """,
                (completed, end_date, milestone_id),
            )

        self.refresh_data()

    def complete_project_record(self, project_id):
        end_date = datetime.now().strftime("%Y-%m-%d")

        # Mark the project complete and record today's date.
        with self.conn:
            self.conn.execute(
                """
                UPDATE projects
                SET completed = 1, end_date = ?
                WHERE id = ?
                """,
                (end_date, project_id),
            )

        self.refresh_data()

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

#####################
# Main Frame Classes
#####################

class Targets(ttk.Frame):
    def __init__(self, new_frame, parent):
        super().__init__(
            new_frame,
            style="Card.TFrame",
            padding=12,
        )

        self.parent = parent

        # Temporary data
        self.subjects = self.parent.subjects

        self.projects = self.parent.projects_list
        self.project_ids = self.parent.project_ids
        self.project_lookup = dict(zip(self.projects, self.project_ids))

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

        self.week_targets = ttk.Frame(self, style="Card.TFrame")

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

        radio_button_container.pack(anchor="w")

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

        if len(self.parent.target_charts) >= 3:
            state='disabled'
        else:
            state='normal'
        self.add_button = ttk.Button(
            self.submit_and_remove_frame,
            cursor="hand2",
            text="Add Target",
            style="Accent.TButton",
            state=state,
            command=self.add_weekly_target
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

        if len(self.parent.target_charts) == 0:
            state='disabled'
        else:
            state='normal'
        self.remove_button = ttk.Button(
            self.submit_and_remove_frame,
            text="Remove",
            cursor="hand2",
            style="Accent.TButton",
            state=state,
            command=self.remove_weekly_target
        )

        self.refresh_remove_choices()

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

    def add_weekly_target(self):
        name = self.target_choice.get().strip()

        try:
            amount = int(self.amount.get())
        except ValueError:
            raise ValueError("Enter a whole number for the target.")

        if amount <= 0:
            raise ValueError("The target must be greater than zero.")
        
        metric = {
            "Minutes": "minutes",
            "Hours": "hours",
            "Tasks": "completed",
        }.get(self.measure.get())

        if metric is None:
            raise ValueError("Choose a measure.")

        subject = None
        project_id = None

        if self.target_type.get() == "subject":
            subject = name
        else:
            project_id = self.project_lookup[name]

        # Refresh the preview in case the amount changed.
        self.update_preview()

        self.parent.insert_weekly_target(
            description=self.preview.get(),
            metric=metric,
            target=amount,
            subject=subject,
            project_id=project_id,
            active=1,
        )

        self.parent.get_targets()

        for widget in self.parent.weekly_progress.winfo_children():
            if widget is not self.parent.target_header:
                widget.destroy()

        self.parent.target_charts.clear()

        self.parent.fill_target_panel()

        if len(self.parent.target_charts) >= 3:
            self.add_button.configure(state="disable")

        self.refresh_remove_choices()

    def refresh_remove_choices(self):
        rows = self.parent.conn.execute(
            """
            SELECT MIN(id) AS id, description
            FROM weekly_targets
            WHERE active = 1
            GROUP BY description
            ORDER BY id
            """
        ).fetchall()

        self.remove_target_lookup = {row["description"]: row["id"] for row in rows}

        choices = list(self.remove_target_lookup)

        self.remove_target.widget.configure(values=choices)
        self.remove_target.widget.set(choices[0] if choices else "")

        self.remove_button.configure(
            state="normal" if choices else "disabled"
        )

    def remove_weekly_target(self):
        selection = self.remove_target.get()
        target_id = self.remove_target_lookup.get(selection)

        if target_id is None:
            return

        self.parent.conn.execute(
            "UPDATE weekly_targets SET active = 0 WHERE id = ?",
            (target_id,),
        )
        self.parent.conn.commit()

        chart = self.parent.target_charts.pop(target_id, None)
        if chart is not None:
            chart.destroy()

        self.add_button.configure(state="normal")

        self.refresh_remove_choices()

        if len(self.parent.target_charts) == 0:
            ttk.Label(
                self.parent.weekly_progress,
                text="No goals this week get your shit together",
                style="Muted.TLabel",
            ).grid(row=1, column=0, sticky="w", padx=10, pady=10)

class Tasks(ttk.Frame):
    def __init__(self, canvas, parent):
        super().__init__(
            canvas,
            padding=10,
            style="Card.TFrame",
        )

        self.parent = parent

        self.target_contributors = {}

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

        self.task_calendar.calendar.bind("<<DateEntrySelected>>", self.change_date)

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
        project_id = record["project_id"]

        if project_id:
            lookup = self.parent.data_lookup['projects'].set_index('id')
            project_name = lookup.loc[project_id,'name']
        else:
            project_name=None

        self.check_boxes[task_id] = tk.BooleanVar(
            self,
            value=bool(completed_status),
        )

        sub_task_frame = ttk.Frame(subject_frame)
        sub_task_frame.grid(
            row=row, column=0,
            sticky="w",
        )

        checkbox = ttk.Checkbutton(
            sub_task_frame, cursor="hand2",
            text=task_name,
            variable=self.check_boxes[task_id],
        )
        checkbox.pack(anchor="w")
        if project_name:
            ttk.Label(
                sub_task_frame,
                text=project_name,
                style="Muted.TLabel",
                font=(self.parent.ui_font, 9),
            ).pack(anchor="w")

        self.row_widgets[task_id].append(sub_task_frame)
                
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
            # padx=6,
            pady=0,
            command=lambda: self.handle_delete(task_id),
        )
        button.grid(
            row=row, column=2,
            sticky="e",
            # padx=5,
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

        self.parent.timer.update_options()

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
            width=3,
            justify="center",
            textvariable=self.hours[task_id],
            wrap=True
        )
        hours_spinbox.grid(row=0, column=0)

        hour_label = ttk.Label(
            time_frame,
            text="hr"
        )
        
        hour_label.grid(row=0, column=1)

        minutes_spinbox = ttk.Spinbox(
            time_frame, cursor="xterm",
            from_=0,
            to=59,
            width=3,
            justify="center",
            textvariable=self.minutes[task_id],
            wrap=True
        )
        minutes_spinbox.grid(row=0, column=2, padx=(5,0))

        min_label = ttk.Label(
            time_frame,
            text="min"
        )   
        min_label.grid(row=0, column=3, padx=(0,3))

        self.row_widgets[task_id].append(time_frame)

    def register_todays_recurring_items(self, date):
        days_recurring_tasks = self.parent.retrieve_recurring_tasks(date)

        # Read existing tasks for the selected date.
        existing_tasks = {
            (task["subject"].strip().lower(), task["task"].strip().lower())
            for task in self.parent.retrieve_records(date)
        }

        for task in days_recurring_tasks:
            task_key = (
                task["subject"].strip().lower(),
                task["task"].strip().lower(),
            )

            if task_key not in existing_tasks:
                self.parent.insert_record(
                    date,
                    task["subject"],
                    task["task"],
                    recurring_id=task["id"],
                    project_id=task["project_id"],
                )

                existing_tasks.add(task_key)

    def check_for_new_records(self):
        # Remove the previous empty-state label.
        if hasattr(self, "empty_label"):
            self.empty_label.destroy()
            del self.empty_label

        date = self.task_calendar.get()

        self.register_todays_recurring_items(date)
        new_records = self.parent.retrieve_records(date)

        if not new_records:
            self.empty_label = ttk.Label(
                self,
                text="Nothing to do today? .... You're Lazy",
                style="Muted.TLabel",
            )
            self.empty_label.grid(
                row=2, column=0, sticky="w", padx=5, pady=10
            )

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
        self.is_stopped = True

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

        self.task_choice.set(self.task_names[0] if self.task_names else "")

        self.task_dropdown.grid(
            row=1,
            column=1,
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

    def update_options(self):
        self.get_stop_watch_options()
        self.task_dropdown.configure(values=self.task_names)

        if self.task_choice.get() not in self.task_names:
            self.task_choice.set("")

    def timer(self):
        self.sv.set(
            self.format_time(time.time() - self.start_time)
        )

        self.after_job = self.after(
            30,
            self.timer
        )

    def start(self):
        self.is_stopped=False
        if self.after_job is not None:
            return

        self.start_time = time.time()

        if self.current_elapsed is not None:
            self.start_time -= self.current_elapsed

        self.timer()

    def stop(self):
        if self.is_stopped:
            self.sv.set(self.all_zeros)
            self.after_job = None
            self.start_time = None
            self.current_elapsed = None
            return

        if self.after_job is None:
            return

        self.after_cancel(self.after_job)
        self.after_job = None

        self.current_elapsed = time.time() - self.start_time
        self.is_stopped=True


    def complete(self):
        if self.after_job is not None:
            self.after_cancel(self.after_job)

        self.after_job = None
        self.start_time = None
        self.current_elapsed = None
        self.is_stopped=True

        hours, minutes, seconds = map(int, self.sv.get().split(":"))
        if seconds > 29:
            minutes+=1

        task_choice = self.task_choice.get()

        # Stop if no task is selected.
        if task_choice == "":
            self.sv.set(self.all_zeros)
            return

        task_id = self.task_id_look_up[task_choice]
        self.tasks.hours[task_id].set(hours)
        self.tasks.minutes[task_id].set(minutes)

        self.sv.set(self.all_zeros)
        self.is_stopped=True


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
        self.task_info_frame.grid(row=1, column=0, sticky="ew")

        self.attach_to_project = tk.BooleanVar(value=False)

        # Initial build.
        self.build_task_info()

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

    def build_task_info(self, subject="", task="", project=""):

        # Recreate the checkbox using the same BooleanVar.
        self.project_option = ttk.Checkbutton(
            self.task_info_frame,
            text="Attach to project",
            variable=self.attach_to_project,
            command=self.rebuild_task_info,
            cursor="hand2",
        )
        self.project_option.pack(side="left", padx=(0, 12), pady=(0, 5))

        # Remove the existing widgets, including the checkbox.
        for widget in self.task_info_frame.winfo_children():
            if widget is not self.project_option:
                widget.destroy()

        self.project = None

        # Include the project dropdown only when checked.
        if self.attach_to_project.get():
            self.project = DropdownField(
                self.task_info_frame,
                "Project",
                "new_task_project_input",
                self.parent.projects_list,
            )
            self.project.pack(
                side="left", padx=(0, 6), pady=(0, 5)
            )
            self.project.widget.set(
                project or (self.parent.projects_list[0] if self.parent.projects_list else "")
            )

        # Subject is always available.
        self.subject = DropdownField(
            self.task_info_frame,
            "Subject",
            "new_task_subject_input",
            self.parent.subjects,
        )
        self.subject.pack(side="left", padx=(0, 6), pady=(0, 5))
        self.subject.widget.set(
            subject or (self.parent.subjects[0] if self.parent.subjects else "")
        )
        self.subject.widget.configure(state="normal")

        # Task name is always available.
        self.task_name = EntryField(
            self.task_info_frame,
            "Task",
            "new_task",
        )
        self.task_name.pack(side="left", padx=(0, 6), pady=(0, 5))
        self.task_name.widget.insert(0, task)
        self.task_name.widget.bind("<Return>", lambda event: self.submit_new_record())

    def rebuild_task_info(self):
        # Preserve the entered values before destroying the widgets.
        subject = self.subject.get()
        task = self.task_name.get()
        project = self.project.get() if self.project is not None else ""

        self.build_task_info(
            subject=subject,
            task=task,
            project=project,
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

        self.include_start_date = tk.BooleanVar(value=False)
        self.include_end_date = tk.BooleanVar(value=False)

        # Separate containers keep each checkbox beside its calendar.
        start_frame = ttk.Frame(self.recurrence_frame)
        start_frame.pack(side="left", padx=(0, 12))

        end_frame = ttk.Frame(self.recurrence_frame)
        end_frame.pack(side="left", padx=(0, 12))

        def toggle_start_date():
            if self.include_start_date.get():
                self.start_date.pack(side="left")
            else:
                self.start_date.pack_forget()

        def toggle_end_date():
            if self.include_end_date.get():
                self.end_date.pack(side="left")
            else:
                self.end_date.pack_forget()

        self.start_option = ttk.Checkbutton(
            start_frame,
            text="Include Start Date?",
            variable=self.include_start_date,
            command=toggle_start_date,
            cursor="hand2",
        )
        self.start_option.pack()

        # Hidden until packed by the callback.
        self.start_date = CalendarField(
            start_frame, "Choose Start Date", "start_date"
        )

        self.end_option = ttk.Checkbutton(
            end_frame,
            text="Include End Date?",
            variable=self.include_end_date,
            command=toggle_end_date,
            cursor="hand2",
        )
        self.end_option.pack()

        self.end_date = CalendarField(
            end_frame, "End Date", "end_date"
        )

    def create_weekly_fields(self):
        self.calendar = None
        days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        self.weekdays = DropdownField(self.recurrence_frame, "Choose Day", 'day_of_week', days, default="Friday")
        self.weekdays.pack(side='left',padx=(0, 6), pady=(0, 5))

    def frequency_adjustment(self, event=None):
        frequency = self.frequency.value.get()

        if frequency == "One Off":
            self.clear_calendars()
            self.create_one_off_fields()

        elif frequency == "Daily":
            self.clear_calendars()
            self.create_daily_fields()

        elif frequency == "Weekly":
            self.clear_calendars()
            self.create_weekly_fields()
            self.create_daily_fields()

    def submit_new_record(self):
        try:
            subject = self.subject.get().strip()
            task = self.task_name.get().strip()
            frequency = self.frequency.get().lower()

            if not task:
                self.error_text.set("Please enter a task name.")
                return

            if not subject:
                self.error_text.set("Please choose a subject.")
                return

            # Look up the selected project only when attaching to one.
            project_id = None

            if self.attach_to_project.get():
                project_name = self.project.get().strip()
                project_id = self.parent.project_lookup.get(project_name)

            combinations = []

            for task_info in self.tasks.days_items.values():
                task_name = task_info["task"].strip().lower()
                task_subject = task_info["subject"].strip().lower()
                combinations.append((task_subject, task_name))

            if (
                (subject.lower(), task.lower()) in combinations
                and frequency == "one off"
            ):
                self.error_text.set("That's already scheduled.")
                return

            if frequency == "one off":
                self.parent.insert_record(
                    self.one_off.get(),
                    subject,
                    task,
                    project_id=project_id,
                )

            else:
                day = (
                    self.weekdays.get()
                    if self.weekdays is not None
                    else None
                )
                print(self.weekdays.get())
                print(day)

                # Only read dates when their checkboxes are checked.
                start_date = (
                    self.start_date.get()
                    if self.include_start_date.get()
                    else None
                )

                end_date = (
                    self.end_date.get()
                    if self.include_end_date.get()
                    else None
                )

                self.parent.insert_recurring_task(
                    subject,
                    task,
                    frequency,
                    day=day,
                    start_date=start_date,
                    end_date=end_date,
                    project_id=project_id,
                )

            # Clear the inputs after either kind of successful insert.
            self.error_text.set("")
            self.subject.widget.set("")
            self.task_name.widget.delete(0, tk.END)

        finally:
            self.tasks.check_for_new_records()
            self.parent.timer.update_options()

class Visuals(ttk.Frame):
    def __init__(self, notebook, parent):
        super().__init__(parent, style="Card.TFrame", )

        self.parent = parent
        self.df = self.parent.data_lookup['sessions']
        self.today = datetime.today()

        self.projects = self.parent.projects_list
        self.project_ids = self.parent.project_ids
        self.project_lookup = dict(zip(self.projects, self.project_ids))

        self.canvas = None
        self.fig = None

        # ==========================================
        # Header
        # ==========================================

        self.header_frame = ttk.Frame(
            self,
            style="Card.TFrame"
        )

        self.header_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=10,
            pady=10
        )

        # ==========================================
        # Default Date Range
        # ==========================================

        default_date_frame = ttk.Frame(
            self.header_frame,
            style="Card.TFrame"
        )

        default_date_frame.pack(
            side="left",
            anchor="n",
            padx=(0, 15)
        )

        ttk.Label(
            default_date_frame,
            text="Choose Date Range",
            style="Heading.TLabel"
        ).pack(
            anchor="w",
            pady=(0, 5)
        )

        self.date_option = tk.StringVar(
            value="Last Week"
        )

        self.date_dropdown = ttk.Combobox(
            default_date_frame,
            textvariable=self.date_option,
            values=[
                "Last Week",
                "Last Month",
                "Last Year"
            ],
            state="readonly",
            width=16
        )

        self.date_dropdown.pack(
            anchor="w"
        )

        # ==========================================
        # Separator
        # ==========================================

        ttk.Separator(
            self.header_frame,
            orient="vertical"
        ).pack(
            side="left",
            fill="y",
            padx=15,
            pady=5
        )

        # ==========================================
        # Custom Date Range
        # ==========================================

        custom_date_frame = ttk.Frame(
            self.header_frame,
            style="Card.TFrame"
        )

        custom_date_frame.pack(
            side="left",
            anchor="n"
        )

        ttk.Label(
            custom_date_frame,
            text="Custom Date Range",
            style="Heading.TLabel"
        ).pack(
            anchor="w",
            pady=(0, 5)
        )

        # Start / End date container
        custom_dates = ttk.Frame(
            custom_date_frame,
            style="Card.TFrame"
        )

        custom_dates.pack(
            anchor="w"
        )

        self.custom_start = CalendarField(
            custom_dates,
            "Start Date",
            "visuals_start_date"
        )

        self.custom_start.pack(
            side="left",
            anchor="n",
            padx=(0, 8)
        )

        self.custom_end = CalendarField(
            custom_dates,
            "End Date",
            "visuals_end_date"
        )

        self.custom_end.pack(
            side="left",
            anchor="n",
            padx=(0, 8)
        )

        self.apply_custom_dates = ttk.Button(
            custom_dates,
            text="Apply",
            command=lambda: self.update_tabs(custom=True),
            style="Small.Accent.TButton",
            cursor="hand2"
        )

        self.apply_custom_dates.pack(
            side="left",
            anchor="s",
            padx=(4, 0)
        )

        # ==========================================
        # Separator
        # ==========================================

        ttk.Separator(
            self.header_frame,
            orient="vertical"
        ).pack(
            side="left",
            fill="y",
            padx=15,
            pady=5
        )

        # ==========================================
        # Filters
        # ==========================================

        filter_frame = ttk.Frame(
            self.header_frame,
            style="Card.TFrame"
        )

        filter_frame.pack(
            side="left",
            anchor="n"
        )

        ttk.Label(
            filter_frame,
            text="Filter Your Data",
            style="Heading.TLabel"
        ).pack(
            anchor="w",
            pady=(0, 5)
        )

        # Container for Subject + Project controls
        filter_options_frame = ttk.Frame(
            filter_frame,
            style="Card.TFrame"
        )

        filter_options_frame.pack(
            anchor="w"
        )

        # ==========================================
        # Subject Filter
        # ==========================================

        subject_frame = ttk.Frame(
            filter_options_frame,
            style="Card.TFrame"
        )

        subject_frame.pack(
            side="left",
            anchor="n",
            padx=(0, 10)
        )

        ttk.Label(
            subject_frame,
            text="Subjects",
            style="Muted.TLabel"
        ).pack(
            anchor="w",
            pady=(5, 5)
        )

        self.subject_options = self.parent.subjects

        self.subject_vars = {
            subject: tk.BooleanVar(value=True)
            for subject in self.subject_options
        }

        self.subject_button = ttk.Menubutton(
            subject_frame,
            text="All Subjects"
        )

        self.subject_menu = tk.Menu(
            self.subject_button,
            tearoff=False
        )

        self.subject_button["menu"] = self.subject_menu

        for subject in self.subject_options:
            self.subject_menu.add_checkbutton(
                label=subject,
                variable=self.subject_vars[subject],
                command=self.update_tabs
            )

        self.subject_button.pack(
            anchor="w"
        )

        # ==========================================
        # Project Filter
        # ==========================================

        self.project_filter = DropdownField(
            filter_options_frame,
            "Project",
            "visuals_project",
            ["All Projects", *self.projects],
        )

        self.project_filter.widget.set("All Projects")

        self.project_filter.pack(
            side="left",
            anchor="n",
        )

        self.project_filter.widget.bind(
            "<<ComboboxSelected>>",
            lambda event: self.update_tabs(),
        )

        # ==========================================
        # Bind Default Date Range
        # ==========================================

        self.date_dropdown.bind(
            "<<ComboboxSelected>>",
            lambda event: self.update_tabs()
        )

        self.date_dropdown.bind(
            "<<ComboboxSelected>>",
            lambda x: self.update_tabs()
        )

        if not self.parent.data_lookup['sessions'].empty:       
            self.update_tabs()

    def update_tabs(self, custom=False):
        if custom:
            start = self.custom_start.calendar.get()
            end = self.custom_end.calendar.get()
        else:
            self.parent.get_start_and_end_dates(self.date_option.get())
            start = self.parent.start
            end = self.parent.end

        # self.parent.filter_dates(start, end)
        self.plot_study((start, end))

    def filter_and_group(self, data, dates, freq='daily'):
        start, end = map(pd.Timestamp, dates)

        data = data.copy()
        data['date'] = pd.to_datetime(data['date']).dt.normalize()

        frequency = {
            'daily': 'D',
            'weekly': 'W',
            'monthly': 'MS',
        }[freq]

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

    def clean_data(self, data, dates, freq='daily'):
        start, end = map(pd.Timestamp, dates)

        offset = {
            'daily': pd.offsets.Day(),
            'weekly': pd.offsets.Week(weekday=6),
            'monthly': pd.offsets.MonthBegin(),
        }[freq]

        # Monthly groups are labeled with the first day of the month.
        if freq == 'monthly':
            first = offset.rollback(start)
            last = offset.rollback(end)
        else:
            first = offset.rollforward(start)
            last = offset.rollforward(end)

        period_dates = pd.date_range(
            first,
            last,
            freq=offset,
        )

        return (
            data.groupby('date')['minutes']
                .sum()
                .reindex(period_dates, fill_value=0)
                .tolist()
        )

    def plot_study(self, dates, total=False):
        start, end = [pd.Timestamp(date).normalize() for date in dates]
        dates = (start, end)

        # Daily through 8 weeks.
        if end <= start + pd.DateOffset(weeks=8):
            freq = 'daily'
            plot_dates = pd.date_range(start, end, freq='D')

            # Inclusive range: 7 dates or fewer.
            date_format = '%a' if len(plot_dates) <= 7 else '%b %d'

        # Weekly after 8 weeks, up to but not including 6 months.
        elif end < start + pd.DateOffset(months=6):
            freq = 'weekly'
            sunday = pd.offsets.Week(weekday=6)
            plot_dates = pd.date_range(
                sunday.rollforward(start),
                sunday.rollforward(end),
                freq='W',
            )

        # Monthly at 6 months or longer.
        else:
            freq = 'monthly'
            month_start = pd.offsets.MonthBegin()
            plot_dates = pd.date_range(
                month_start.rollback(start),
                month_start.rollback(end),
                freq='MS',
            )

        subjects = [subject for subject, variable in self.subject_vars.items() if variable.get()]

        print(subjects)

        selected = self.df[self.df['subject'].isin(subjects)]
        project_choice = self.project_filter.widget.get()

        if project_choice != "All Projects":
            project_id = self.project_lookup[project_choice]
            selected = selected[selected['project_id'] == project_id]

        subjects = selected['subject'].unique().tolist()
        grouped = self.filter_and_group(selected, dates, freq)

        # Remove the previous chart.
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            plt.close(self.fig)

        self.fig = Figure(figsize=(8, 5), dpi=100)
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(UI_COLORS["surface"])
        ax.grid(axis="y")
        ax.tick_params(axis="both", length=0, pad=7)

        colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(subjects))]
        bottom = np.zeros(len(plot_dates))

        plot_subjects = [None] if total else subjects

        monthly_values = []
        monthly_labels = []
        monthly_colors = []

        for i, subject in enumerate(plot_subjects):
            minutes = np.array(self.clean_data(grouped.query('subject == @subject'), dates, freq))
            label = 'Total' if total else subject
            color = UI_COLORS["accent"] if total else colors[i]

            if freq in ('daily', 'weekly'):
                ax.bar(
                    plot_dates,
                    minutes,
                    bottom=bottom,
                    width=0.8 if freq == 'daily' else 5.6,
                    label=label,
                    color=color,
                )
                bottom += minutes

            else:
                # Collect each subject for the monthly stacked plot.
                monthly_values.append(minutes)
                monthly_labels.append(label)
                monthly_colors.append(color)

        # Stack all subjects together in one call.
        if freq == 'monthly' and monthly_values:
            ax.stackplot(
                plot_dates,
                *monthly_values,
                labels=monthly_labels,
                colors=monthly_colors,
                alpha=0.85,
            )

        ax.set_ylabel('Minutes')
        ax.set_title(
            f"{'Daily' if freq == 'daily' else 'Weekly'} Study Time",
            loc="left", pad=16
        )
        ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))

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
            style="Card.TFrame"
        )

        self.header_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=10,
            pady=10
        )

        # ==========================================
        # Default Date Range
        # ==========================================

        default_date_frame = ttk.Frame(
            self.header_frame,
            style="Card.TFrame"
        )

        default_date_frame.pack(
            side="left",
            anchor="n",
            padx=(0, 15)
        )

        ttk.Label(
            default_date_frame,
            text="Choose Date Range",
            style="Heading.TLabel"
        ).pack(
            anchor="w",
            pady=(0, 5)
        )

        self.date_option = tk.StringVar(
            value="Last Week"
        )

        self.date_dropdown = ttk.Combobox(
            default_date_frame,
            textvariable=self.date_option,
            values=[
                "Last Week",
                "Last Month",
                "Last Year"
            ],
            state="readonly",
            width=16
        )

        self.date_dropdown.pack(
            anchor="w"
        )

        # ==========================================
        # Separator
        # ==========================================

        ttk.Separator(
            self.header_frame,
            orient="vertical"
        ).pack(
            side="left",
            fill="y",
            padx=15,
            pady=5
        )

        # ==========================================
        # Custom Date Range
        # ==========================================

        custom_date_frame = ttk.Frame(
            self.header_frame,
            style="Card.TFrame"
        )

        custom_date_frame.pack(
            side="left",
            anchor="n"
        )

        ttk.Label(
            custom_date_frame,
            text="Custom Date Range",
            style="Heading.TLabel"
        ).pack(
            anchor="w",
            pady=(0, 5)
        )

        # Start / End date container
        custom_dates = ttk.Frame(
            custom_date_frame,
            style="Card.TFrame"
        )

        custom_dates.pack(
            anchor="w"
        )

        self.custom_start = CalendarField(
            custom_dates,
            "Start Date",
            "visuals_start_date"
        )

        self.custom_start.pack(
            side="left",
            anchor="n",
            padx=(0, 8)
        )

        self.custom_end = CalendarField(
            custom_dates,
            "End Date",
            "visuals_end_date"
        )

        self.custom_end.pack(
            side="left",
            anchor="n",
            padx=(0, 8)
        )

        self.apply_custom_dates = ttk.Button(
            custom_dates,
            text="Apply",
            command=lambda: self.update_tabs(custom=True),
            style="Small.Accent.TButton",
            cursor="hand2"
        )

        self.apply_custom_dates.pack(
            side="left",
            anchor="s",
            padx=(4, 0)
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

        for row in range(3):
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

        for i in range(9):
            row, column = divmod(i, 3)

            card = StatCard(
                self.bottom_left_frame,
                title="",
                value="",
            )
            # sticky = "new" if row==1 else "sew"
            card.grid(
                row=row,
                column=column,
                sticky="nsew",
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

        if not self.parent.data_lookup['sessions'].empty:
            self.update_tabs()

    def update_tabs(self, custom=False):

        df = self.parent.data_lookup['sessions']

        if custom:
            start = self.custom_start.calendar.get()
            end = self.custom_end.calendar.get()
        else:
            self.parent.get_start_and_end_dates(self.date_option.get())
            start = self.parent.start
            end = self.parent.end

        self.df_filt = df.query('date >= @start and date <= @end')

        # Update the denominator used by the Study Days card.
        self.period_days = (
            pd.Timestamp(end) - pd.Timestamp(start)
        ).days + 1

        self.start = pd.Timestamp(start).normalize()
        self.end = pd.Timestamp(end).normalize()

        self.update_cards()
        self.update_subject_tree()

    def update_cards(self):

        card_values = [
            self.get_total_study_time(),
            self.tasks_completed(),
            self.study_days(),
            self.average_study_day(),
            self.longest_study_streak(),
            self.most_studied(),
            self.most_consistent(),
            self.milestones_completed(),
            self.projects_completed(),
        ]
        
        for card, (title, value, subtitle) in zip(
            self.cards, card_values
        ):
            card.set_title(title)
            card.set_value(value)
            card.set_subtitle(subtitle)

    def update_subject_tree(self):
        summary = self.df_filt.groupby("subject").agg(
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
        total_time = self.df_filt["minutes"].sum()
        subjects = self.df_filt.loc[
            self.df_filt["minutes"] > 0, "subject"
        ].nunique()

        return (
            "Total study time",
            self.format_minutes(total_time),
            f"Across {subjects} subjects",
        )

    def tasks_completed(self):
        total_tasks = len(self.df_filt)
        completed = int(self.df_filt["completed"].eq(1).sum())
        rate = completed / total_tasks if total_tasks else 0

        return (
            "Tasks completed",
            f"{completed} of {total_tasks}",
            f"{rate:.0%} completion",
        )

    def study_days(self):
        if self.df_filt.empty:
            return (
            "Study days",
            f"0 of {self.parent.period_days}",
            "Days with time recorded",
        )

        dates = pd.to_datetime(
            self.df_filt.loc[self.df_filt["minutes"] > 0, "date"]
        )
        days = dates.dt.normalize().nunique()

        return (
            "Study days",
            f"{days} of {self.parent.period_days}",
            "Days with time recorded",
        )

    def most_studied(self):
        if self.df_filt.empty:
            return (
            "Most studied",
            "—",
            "No study time recorded",
        )

        totals = self.df_filt.groupby("subject")["minutes"].sum()
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
        if self.df_filt.empty:
            return pd.DataFrame()

        return self.df_filt.groupby("subject").agg(
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

    def average_study_day(self):
        # Average only across days with study time recorded.
        data = self.df_filt

        if data.empty:
            return (
            "Average study day",
            "-",
            "No study time recorded",
        )

        study_dates = pd.to_datetime(
            data.loc[data['minutes'] > 0, 'date']
        ).dt.normalize()

        days = study_dates.nunique()
        total_minutes = data['minutes'].sum()
        average = total_minutes / days if days else 0

        return (
            "Average study day",
            self.format_minutes(average),
            "Per day with time recorded",
        )


    def longest_study_streak(self):
        data = self.df_filt

        if data.empty:
            return (
            "Longest study streak",
            "-",
            "No study time recorded",
        )

        dates = (
            pd.to_datetime(data.loc[data['minutes'] > 0, 'date'])
            .dt.normalize()
            .drop_duplicates()
            .sort_values()
        )

        longest = 0
        current = 0
        previous = None

        for date in dates:
            if previous is not None and date - previous == pd.Timedelta(days=1):
                current += 1
            else:
                current = 1

            longest = max(longest, current)
            previous = date

        return (
            "Longest study streak",
            f"{longest} {'day' if longest == 1 else 'days'}",
            "Consecutive days in selected range",
        )


    def milestones_completed(self):
        data = self.parent.data_lookup['milestones']

        if data.empty:
            return (
            "Milestones completed",
            str(0),
            "Completed in selected range",
        )

        # Normalize timestamps so the entire end date is included.
        completion_dates = pd.to_datetime(
            data['end_date'], errors='coerce'
        ).dt.normalize()

        count = (
            (data['completed'] == 1)
            & completion_dates.between(self.start, self.end)
        ).sum()

        return (
            "Milestones completed",
            str(int(count)),
            "Completed in selected range",
        )


    def projects_completed(self):
        data = self.parent.data_lookup['projects']

        if data.empty:
            return (
                    "Project completed",
                    str(0),
                    "Completed in selected range",
                )

        completion_dates = pd.to_datetime(
            data['end_date'], errors='coerce'
        ).dt.normalize()

        count = (
            (data['completed'] == 1)
            & completion_dates.between(self.start, self.end)
        ).sum()

        return (
            "Projects completed",
            str(int(count)),
            "Completed in selected range",
        )

class TaskManager(ttk.Frame):
    def __init__(self, notebook, parent):
        super().__init__(
            notebook,
            style="Page.TFrame",
            padding=10,
        )
        self.root = self.winfo_toplevel()
        self.parent = parent

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
            "Projects": {
                "table": "projects",
                "title": "Projects",
                "columns": (
                    "name", "completed",
                ),
                "names": (
                    "Project Name", "Completed",
                ),
                "default_widths": (300, 100),
            },
            "Milestones": {
                "table": "milestones",
                "title": "Milestones",
                "columns": (
                    "project_id", "name", "completed",
                ),
                "names": (
                    "Project ID", "Milestone Name", "Completed",
                ),
                "default_widths": (100, 300, 100),
            },
            "Weekly targets": {
                "table": "weekly_targets",
                "title": "Weekly Targets",
                "columns": (
                    "date", "description", "subject",
                    "project_id", "metric", "target", "active",
                ),
                "names": (
                    "Date", "Description", "Subject",
                    "Project ID", "Metric", "Target", "Active",
                ),
                "default_widths": (100, 200, 100, 100, 100, 80, 80),
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
            command=lambda: self.current_dataset.delete_selected()
        )
        self.delete_button.grid(row=0, column=3)

    def generate_tree(self, dataset):
        settings = self.dataset_lookup[dataset]

        # Retrieve the selected DataFrame already in memory
        self.table_name = settings["table"]
        df = self.root.data_lookup[self.table_name]

        if df.empty:
            return

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
            on_complete=lambda _id=new_id: self.complete_project(_id),
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
                on_complete=lambda _id=existing_id: self.complete_project(_id),
            )
        self.arrange_projects()

    def complete_project(self, project_id):
        self.parent.complete_project_record(project_id)

        widget = self.projects.pop(project_id)
        widget.destroy()
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
        # Dedicated styles keep the blue background on every layer.
        style = ttk.Style(parent)
        family = tkfont.nametofont("TkDefaultFont").actual("family")
        background = UI_COLORS["accent"]

        style.configure(
            "BlueStat.TFrame",
            background=background,
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "BlueStatTitle.TLabel",
            background=background,
            foreground="white",
            font=(family, 9, "bold"),
        )
        style.configure(
            "BlueStatValue.TLabel",
            background=background,
            foreground="white",
            font=(family, 18, "bold"),
        )
        style.configure(
            "BlueStatSubtitle.TLabel",
            background=background,
            foreground="white",
            font=(family, 9),
        )

        super().__init__(
            parent,
            padding=10,
            style="BlueStat.TFrame",
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Stretch horizontally while keeping content centered vertically.
        self.content = ttk.Frame(self, style="BlueStat.TFrame")
        self.content.grid(row=0, column=0, sticky="ew")

        self.title_label = ttk.Label(
            self.content,
            text=title.upper(),
            style="BlueStatTitle.TLabel",
            anchor="center",
            justify="center",
            wraplength=140,
        )
        self.title_label.pack(fill="x")

        self.value_label = ttk.Label(
            self.content,
            text=value,
            style="BlueStatValue.TLabel",
            anchor="center",
            justify="center",
            wraplength=140,
        )
        self.value_label.pack(fill="x", pady=(5, 0))

        self.subtitle_label = ttk.Label(
            self.content,
            text=subtitle or "",
            style="BlueStatSubtitle.TLabel",
            anchor="center",
            justify="center",
            wraplength=140,
        )
        if subtitle:
            self.subtitle_label.pack(fill="x", pady=(4, 0))

        # Adjust wrapping whenever the card changes size.
        # self.bind("<Configure>", self.update_wrap)

    def update_wrap(self, event):
        available_width = max(1, event.width - 24)

        for label in (
            self.title_label,
            self.value_label,
            self.subtitle_label,
        ):
            label.configure(wraplength=available_width)

    def set_title(self, title):
        self.title_label.configure(text=title.upper())

    def set_value(self, value):
        self.value_label.configure(text=value)

    def set_subtitle(self, subtitle):
        self.subtitle_label.configure(text=subtitle or "")

        if subtitle:
            self.subtitle_label.pack(fill="x", pady=(4, 0))
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

        # Save the listener ID so we can remove it later.
        self.search_trace_id = self.current_entry.trace_add(
            "write", self.search_rows
        )

        # Apply any search text already entered.
        self.search_rows()

    def destroy(self):
        # Only remove the listener if it was created.
        if hasattr(self, "current_entry") and hasattr(self, "search_trace_id"):
            self.current_entry.trace_remove("write", self.search_trace_id)

        # Destroy the frame and its child widgets.
        super().destroy()

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
    def __init__(self, parent, title, current, metric, target, text=""):
        super().__init__(
            parent,
            padding=10,
            style="Card.TFrame")

        self.current = current
        self.metric = metric
        self.target = target
        self.text = text

        # Card heading
        ttk.Label(
            self,
            text=title,
            style="Subject.TLabel",
        ).pack(anchor="w")

        # Progress toward the target
        self.bar = ttk.Progressbar(
            self,
            maximum=target,
            value=current,
            style="Card.Horizontal.TProgressbar",
        )
        self.bar.pack(fill="x", pady=8)

        self.label = ttk.Label(
            self,
            text=f"{current} / {target} {text}",
            style="Muted.TLabel",
        )
        
        self.label.pack(anchor="w")

    def update_current(self, current):
        self.current = current
        self.bar.configure(value=current)
        self.label.configure(
            text=f"{current} / {self.target} {self.text}"
    )

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
            command=lambda: on_complete(),
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
        print(self.project_id)
        milestone_id = self.root.insert_milestone(self.project_id, title)

        self.root.milestones[milestone_id] = tk.BooleanVar(self, value=False)
        row = len(self.root.milestones) - 1

        ttk.Checkbutton(
            self.milestone_frame,
            variable=self.root.milestones[milestone_id],
            command=lambda milestone_id=milestone_id: self.update_progress(milestone_id=milestone_id),
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
                command=lambda milestone_id=milestone_id: self.update_progress(milestone_id=milestone_id),
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

    def update_progress(self, milestone_id=None):
        total = len(self.root.milestone_record_lookup[self.project_id])

        milestone_ids = [row["id"] for row in self.root.milestone_record_lookup[self.project_id]]

        completed = sum(variable.get() for key, variable in self.root.milestones.items() if key in milestone_ids)

        self.progress["value"] = completed / total * 100 if total else 0

        self.progress_text["text"] = f"{completed} / {total} milestones completed"
        
        self.complete_button["state"] = "normal" if total and completed == total else "disabled" 

        # Save only the milestone whose checkbox changed.
        if milestone_id is not None:
            self.root.update_milestone(
                milestone_id,
                self.root.milestones[milestone_id].get(),
            )

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
