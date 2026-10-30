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

    # Frames
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

    # Controls
    style.configure(
        "TCheckbutton",
        background=UI_COLORS["surface"],
        font=(family, 10),
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
        state_date TEST NOT NULL,
        end_date TEXT NOT NULL
    );
"""

class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        configure_appearance(self)

        self.conn = sqlite3.connect("study_tracker.db")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(opening_query_sessions)
        self.conn.execute(opening_query_recurring_tasks)

        self.today = datetime.today().strftime("%Y-%m-%d")
        self.title("Study Tracker")
        self.geometry("1280x850")

        # setting up canvas frame that will contain scroll bar so we can scroll through
        # daily tasks when the list gets too long 
        self.canvas_frame = ScrollableFrame(self)
        self.canvas_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10
        )

        # we create the task frame now inside the scrollable bar frame
        # the scrollable bar frame is created in the ScrollableFrame class 
        self.tasks = Tasks(self.canvas_frame.scrollable_frame, self)
        self.tasks.grid(
            row=0,
            column=0,
            sticky="new"
        )

        # we want the stop watch and task adder panel to line up nicely with the 
        # task frame so we create a separate frame next to the task frame and then put
        # these two frames inside it

        # First we create and place the frame to sit next to the tasks
        stop_watch_and_task_adder = ttk.Frame(self, style="Page.TFrame")
        stop_watch_and_task_adder.grid(row=0,column=1, padx=10, pady=10, sticky="new")
        stop_watch_and_task_adder.columnconfigure(0, weight=1)

        # Now we add the scheduler and timer to that new frame
        self.goal_page = Schedule(stop_watch_and_task_adder, self)
        self.goal_page.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.goal_page.columnconfigure(0, weight=1)

        self.timer = Timer(stop_watch_and_task_adder, self)
        self.timer.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.timer.columnconfigure(0, weight=1)

        # the lower panel will be a long panel to display visuals 
        # we will add subequent frames inside notebook frame 
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=10,
            pady=10,
        )

        # this is a dataload to pull all the data into memory so it's
        # available to analyze if we need it
        self.load_data()

        # these are the visual and analytics tab that we create within the notebook and then add them 
        self.visuals_tab = Visuals(self.notebook, self, self.df)
        self.analytics_tab = Analytics(self.notebook, self)

        self.notebook.add(self.analytics_tab, text="Analytics")
        self.notebook.add(self.visuals_tab, text="Visuals")

        self.bottom_panel_dates = date_range_update(stop_watch_and_task_adder, self)
        self.bottom_panel_dates.grid(row=2, column=0, sticky='ew')

        # First layer column configure
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        # make next layer expandable
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.scrollable_frame.columnconfigure(0, weight=1)
        self.tasks.columnconfigure(0, weight=1)

    def load_data(self):
       rows = self.conn.execute("SELECT * FROM sessions").fetchall()
       self.df = pd.DataFrame([dict(row) for row in rows])

    def change_stats_period(self, event=None):
        period = self.stats_period.get()
        self.statistics_tab.set_period(period)
        self.visuals_tab.set_period(period)

    def retrieve_records(self, date):

        return self.conn.execute("""
            SELECT * FROM sessions
            WHERE date = ?
        """, (date,)).fetchall()

    def retrieve_recurring_tasks(self, date):

        day = datetime.strptime(date, "%Y-%m-%d").strftime("%A")

        return self.conn.execute("""
            SELECT *
            FROM recurring_tasks
            WHERE (
                frequency = 'daily'
                OR (frequency = 'weekly' AND day = ?)
            )
            AND id NOT IN (
                SELECT recurring_id
                FROM sessions
                WHERE date = ?
                AND recurring_id IS NOT NULL
            )
        """, (day, date)).fetchall()

    def insert_record(self, date, subject, task, minutes=0, completed=0, recurring_id=None):
        
        with self.conn:
            self.conn.execute("""
                INSERT INTO sessions (date, subject, task, minutes, completed, recurring_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (date, subject, task, minutes, completed, recurring_id))

    def insert_recurring_task(self, subject, task, frequency, day=None):
      
        with self.conn:
            cursor = self.conn.execute("""
                INSERT INTO recurring_tasks (subject, task, frequency, day)
                VALUES (?, ?, ?, ?)
            """, (subject, task, frequency, day))

        return cursor.lastrowid

    def update_record(self, id, minutes, completed):

        with self.conn:
            self.conn.execute("""
                UPDATE sessions
                SET minutes = ?, completed = ?
                WHERE id = ?
            """, (minutes, completed, id))

    def delete_record(self, id):
        with self.conn:
            self.conn.execute("""
                DELETE FROM sessions
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

class Tasks(ttk.Frame):
    def __init__(self, canvas, parent):
        super().__init__(
            canvas,
            borderwidth=0,
            relief="flat",
            padding=18,
            style="Card.TFrame"
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

        self.header_frame = ttk.Frame(self, style="Card.TFrame")
        self.header_frame.columnconfigure(0, weight=1)
        self.header_frame.grid(
            row=0, column=0,
            sticky="nw",
            padx=(0, 20),
        )

        self.calendar_frame = ttk.Frame(self, style="Card.TFrame")
        self.calendar_frame.columnconfigure(0, weight=1)
        self.calendar_frame.grid(
            row=0, column=1,
            sticky="ne",
        )
        self.calendar_frame.bind(
            "<FocusOut>",
            lambda event: self.calendar_frame.event_generate("<Escape>")
        )
        self.calendar_frame.bind(
            "<Escape>",
            lambda event: self.calendar_frame.event_generate("<Escape>")
        )

        ttk.Separator(self, orient="horizontal").grid(
            row=1, column=0,
            columnspan=2,
            sticky="ew",
            pady=(16, 8),
        )

        self.task_frame = ttk.Frame(self, style="Card.TFrame")
        self.task_frame.grid(
            row=2, column=0,
            columnspan=2,
            sticky="ew",
        )
        self.task_frame.columnconfigure(0, weight=1)

        self.save_frame = ttk.Frame(self, style="Card.TFrame")
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
        self.date_label = ttk.Label(
            self.calendar_frame,
            text="Choose date",
        )
        self.date_label.grid(
            row=0, column=0,
            sticky="w",
            pady=(0, 6),
        )

        self.calendar = DateEntry(
            self.calendar_frame, cursor="xterm",
            width=12,
            date_pattern="yyyy-mm-dd",
        )
        self.calendar.grid(row=1, column=0, sticky="e")

        self.calendar.bind(
            "<<DateEntrySelected>>",
            self.change_date,
        )
        self.calendar.bind(
            "<FocusOut>",
            lambda event: self.calendar.event_generate("<Escape>")
        )
        self.calendar.bind(
            "<Escape>",
            lambda event: self.calendar.event_generate("<Escape>")
        )

    def add_task(self, record):
        task_id = record["id"]
        subject = record["subject"]

        task = (
            task_id,
            record["task"],
            record["minutes"],
            record["completed"],
        )

        print(task)

        if subject not in self.subject_frames:
            subject_frame = ttk.Frame(
                self.task_frame,
                padding=(0, 10),
                style="Card.TFrame"
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

        self.check_box(task, task_row, subject_frame)
        self.task_time_to_complete(task, task_row, subject_frame)
        self.delete_button(task, task_row, subject_frame)

        self.days_subjects[subject].append(task)
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

    def check_box(self, task, row, subject_frame):
        task_id, task_name, _, completed_status = task

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

    def delete_button(self, task, row, subject_frame):
        task_id, task_name, _, completed_status = task

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
        self.parent.delete_record(task_id)
        print(task_id, 'deleted')

        for widget in self.row_widgets.pop(task_id):
            widget.destroy()

        subject = self.days_items.pop(task_id)['subject']
        subject_frame = self.subject_frames[subject]

        if len(subject_frame.winfo_children()) == 1:
            subject_frame.destroy()
            del self.subject_frames[subject]

        self.parent.timer.get_stop_watch_options(self)

    def task_time_to_complete(self, task, row, subject_frame):
        task_id, _, task_minutes, _ = task

        hours, minutes = divmod(task_minutes, 60)

        self.hours[task_id] = tk.StringVar(self, value=hours)
        self.minutes[task_id] = tk.StringVar(self, value=minutes)

        time_frame = ttk.Frame(subject_frame, style="Card.TFrame", borderwidth=0, relief="flat")
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
        days_recurring_tasks = self.parent.retrieve_recurring_tasks(date)

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
        date = self.calendar.get()

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
                self.parent.update_record(
                    task_id,
                    task_minutes_after,
                    task_completed_after,
                )

class Timer(ttk.Frame):

    def __init__(self, new_frame, parent):
        super().__init__(
            new_frame,
            borderwidth=0,
            relief="flat",
            padding=18,
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
            columnspan=3,
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
            width=30,
            values=self.task_names,
        )

        self.task_dropdown.grid(
            row=1,
            column=1,
            columnspan=2,
            sticky="ew",
            pady=(0, 15),
        )

        # Timer
        self.timer_display = ttk.Label(
            self,
            textvariable=self.sv,
            style="Timer.TLabel",
            font=(self.parent.ui_font, 30, "bold"),
            anchor="center"
        )

        self.timer_display.grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(10, 20)
        )

        # Buttons
        ttk.Button(
            self, cursor="hand2",
            text="Start",
            style="Accent.TButton",
            command=self.start
        ).grid(
            row=3,
            column=0,
            padx=(0, 5),
            sticky="ew"
        )

        ttk.Button(
            self, cursor="hand2",
            text="Stop",
            style="Accent.TButton",
            command=self.stop
        ).grid(
            row=3,
            column=1,
            padx=5,
            sticky="ew"
        )

        ttk.Button(
            self, cursor="hand2",
            text="Finish",
            style="Accent.TButton",
            command=self.complete
        ).grid(
            row=3,
            column=2,
            padx=(5, 0),
            sticky="ew"
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
            padding=18,
            relief="flat",
            borderwidth=0,
            style="Card.TFrame"
        )

        self.parent = parent
        self.tasks = parent.tasks
        self.day_choice = None

        for column in range(2):
            self.columnconfigure(column, weight=1)

        # Subject
        ttk.Label(
            self,
            text="Subject",
            style="Muted.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 6),
            pady=(8, 5)
        )

        self.subject = ttk.Entry(self, cursor="xterm", width=18)
        self.subject.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 6)
        )

        # Task
        ttk.Label(
            self,
            text="Task Name",
            style="Muted.TLabel"
        ).grid(
            row=0,
            column=1,
            sticky="w",
            padx=(6, 0),
            pady=(8, 5)
        )

        self.task_name = ttk.Entry(self, cursor="xterm", width=18)
        self.task_name.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(6, 0)
        )

        # Frequency
        ttk.Label(
            self,
            text="Task Frequency",
            style="Muted.TLabel"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 6),
            pady=(12, 5)
        )

        self.frequency_choice = tk.StringVar(
            self,
            value="One Off"
        )

        self.frequency_dropdown = ttk.Combobox(
            self,
            textvariable=self.frequency_choice,
            values=["One Off", "Daily", "Weekly"],
            width=18,
            state="readonly"
        )

        self.frequency_dropdown.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=(0, 6)
        )

        # Date / Day
        self.create_date_selection("Choose Date")

        self.frequency_dropdown.bind(
            "<<ComboboxSelected>>",
            self.frequency_adjustment
        )

        # Submit
        button = ttk.Button(
            self, cursor="hand2",
            text="Add Task",
            style="Accent.TButton",
            command=self.submit_new_record
        )

        button.grid(
            row=4,
            column=0,
            sticky="w",
            pady=(20, 0),
            columnspan=1
        )

        self.error_text = tk.StringVar()

        self.error_label = ttk.Label(
            self,
            textvariable=self.error_text,
            style="Error.TLabel",
            wraplength=180,
        )
        self.error_label.grid(
            row=4, column=0, columnspan=1,
            sticky="e", padx=10, pady=(0, 8),
        )

        self.recurrence_frame = ttk.Frame(
            self,
            style="Card.TFrame",
        )

        self.recurrence_frame.grid(
            row=4,
            column=1,
            sticky="e",
            pady=(12,0)
        )

        self.recurrence_frame.columnconfigure(0, weight=1)
        self.recurrence_frame.columnconfigure(1, weight=1)

    def create_date_selection(self, label_text):
        self.day_choice = None

        self.date_label = ttk.Label(
            self.recurrence_frame,
            text="Choose Date",
            style="Muted.TLabel"
        )

        self.date_label.grid(
            row=2,
            column=1,
            sticky="w",
            padx=(6, 0),
            pady=(12, 5)
        )

        self.calendar = DateEntry(
            self.recurrence_frame, 
            cursor="xterm",
            date_pattern="yyyy-mm-dd"
        )

        self.calendar.grid(
            row=3,
            column=1,
            sticky="ew",
            padx=(6, 0)
        )


    def frequency_adjustment(self, event=None):
        self.date_label.destroy()
        self.calendar.destroy()

        frequency = self.frequency_choice.get()

        if frequency == "One Off":
            self.create_date_selection("Choose Date")

        elif frequency == "Daily":
            self.create_date_selection("Choose Starting Date")

        else:
            self.date_label = ttk.Label(
                self,
                text="Choose Day",
                style="Muted.TLabel"
            )

            self.date_label.grid(
                row=2,
                column=1,
                sticky="w",
                padx=(10, 0),
                pady=(10, 5)
            )

            self.day_choice = tk.StringVar(
                self,
                value="Friday"
            )

            self.calendar = ttk.Combobox(
                self,
                textvariable=self.day_choice,
                values=[
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday"
                ],
                width=18,
            state="readonly"
            )

            self.calendar.grid(
                row=3,
                column=1,
                sticky="ew",
                padx=(10, 0)
            )


    def submit_new_record(self):
        try:
            subject = self.subject.get().strip().lower()
            task = self.task_name.get().strip().lower()
            frequency = self.frequency_choice.get().lower()

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
                    self.calendar.get(),
                    self.subject.get().strip(),
                    self.task.get().strip()
                )
                return

            if self.day_choice is not None:
                day = self.day_choice.get()
            else:
                day = None

            self.parent.insert_recurring_task(
                self.subject.get().strip(),
                self.task.get().strip(),
                frequency,
                day=day
            )

            self.error_text.set("")
            self.subject.delete(0, tk.END)
            self.task_name.delete(0, tk.END)

        finally:
            self.tasks.check_for_new_records()
            self.parent.timer.get_stop_watch_options()

class ScrollableFrame(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")

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
            style="Card.TFrame"
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

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.canvas.bind("<Enter>", self.bind_mousewheel)
        self.canvas.bind("<Leave>", self.unbind_mousewheel)

    def bind_mousewheel(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self.mousewheel)

    def unbind_mousewheel(self, event=None):
        self.canvas.unbind_all("<MouseWheel>")

    def mousewheel(self, event):
        self.canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )

    def resize_frame(self, event):
        self.canvas.itemconfigure(
            self.canvas_window,
            width=event.width
        )

class StatCard(ttk.Frame):

    def __init__(self, parent, title, value, subtitle=None):
        super().__init__(parent, padding=18, style="StatCard.TFrame")

        ttk.Label(
            self,
            text=title.upper(),
            style="Muted.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            self,
            text=value,
            style="Metric.TLabel"
        ).pack(anchor="w", pady=(8, 0))

        if subtitle:
            ttk.Label(
                self,
                text=subtitle,
                style="Muted.TLabel"
            ).pack(anchor="w")

class Visuals(ttk.Frame):
    def __init__(self, notebook, parent, df):
        super().__init__(parent, style="Card.TFrame")

        self.parent = parent
        self.df = df
        self.today = datetime.today()

        self.canvas = None
        self.fig = None

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
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
      
class Analytics(ttk.Frame):
    def __init__(self, notebook, parent):
        super().__init__(parent, style="Card.TFrame")

        self.parent = parent
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        for column in range(3):
            self.columnconfigure(column, weight=1, uniform="analytics")

    def get_cards(self):

        cards = [
            self.get_total_study_time(),
            self.tasks_completed(),
            self.study_days(),
            self.most_studied(),
            self.most_consistent(),
            self.most_skipped(),
        ]

        for i, (title, value, subtitle) in enumerate(cards):
            row, column = divmod(i, 3)

            StatCard(self,title,value,subtitle)\
            .grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=8,
                pady=8,
            )

    def filter_dates(self, start, end):
        self.df_filt = self.parent.df.query('date >= @start and date <= @end')

    def format_minutes(self, minutes):
        hours, minutes = divmod(int(minutes), 60)
        return f"{hours}h {minutes:02d}m"

    def get_total_study_time(self):
        total_time = self.df_filt["minutes"].sum()
        subjects = self.df_filt.loc[self.df_filt["minutes"] > 0, "subject"].nunique()

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
        days = self.df_filt.loc[self.df_filt["minutes"] > 0, "date"].nunique()

        return (
            "Study days",
            f"{days} of {6}",
            "Days with time recorded",
        )

    def most_studied(self):
            totals = self.df_filt.groupby("subject")["minutes"].sum()
            total_time = totals.sum()

            if totals.empty or total_time == 0:
                return ("Most studied", "—", "No study time recorded")

            subject = totals.idxmax()
            minutes = totals.loc[subject]
            share = minutes / total_time

            return (
                "Most studied",
                subject,
                f"{self.format_minutes(minutes)} · {share:.0%} of study time",
            )


    def past_task_summary(self):
        today = datetime.today()

        past = self.df_filt.loc[pd.to_datetime(self.df_filt["date"]) < today]

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

class date_range_update(ttk.Frame):
    def __init__(self, new_frame, parent):
        super().__init__(
            new_frame,
            borderwidth=0,
            relief="flat",
            padding=18,
            style="Card.TFrame"
        )

        self.parent = parent
        self.rowconfigure(0, weight=1)

        date_choice_label = ttk.Label(
            self,
            text="Choose Date Range",
            style="Heading.TLabel",
        )
        date_choice_label.grid(row=0, column=0)

        self.date_option = tk.StringVar()
        self.date_dropdown = ttk.Combobox(
            self,
            textvariable=self.date_option,
            values=["Last Week", "Last Month", "Last Year", "Custom Range"],
            state="readonly"
        )
        self.date_dropdown.grid(row=1, column=0, padx=5)

        self.date_dropdown.bind(
            "<<ComboboxSelected>>",
            lambda x: self.update_tabs()
        )

    def get_start_and_end_dates(self):

        choice = self.date_option.get()

        if choice == 'Last Week':
            self.end = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            self.start = (datetime.today() - timedelta(days=8)).strftime("%Y-%m-%d")

        elif choice == 'Last Month':
            self.end = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            self.start = (datetime.today() - timedelta(days=31)).strftime("%Y-%m-%d")

        elif choice == 'Last Year':
            self.end = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            self.start = (datetime.today() - timedelta(days=366)).strftime("%Y-%m-%d")

    def update_tabs(self):
        self.get_start_and_end_dates()
        self.parent.analytics_tab.filter_dates(self.start, self.end)
        self.parent.analytics_tab.get_cards()
        self.parent.visuals_tab.plot_study((self.start, self.end))
    
if __name__ == "__main__":
    main()
