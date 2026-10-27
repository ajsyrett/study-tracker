import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import datetime
from collections import defaultdict
import time
from pathlib import Path
from tkinter import font as tkfont
from tkcalendar import DateEntry
# import pandas as pd

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
        day TEX
    );
"""

class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        theme_path = (
            Path(__file__).parent
            / "Forest-ttk-theme-master"
            / "forest-light.tcl"
        )

        self.tk.call("source", str(theme_path))
        ttk.Style(self).theme_use("forest-light")

        style = ttk.Style(self)
        style.configure(
            "Debug.TFrame",
            relief="solid",
            borderwidth=1
        )

        self.heading_font = tkfont.nametofont("TkDefaultFont").copy()
        self.heading_font.configure(size=12, weight="bold")

        self.conn = sqlite3.connect("study_tracker.db")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(opening_query_sessions)
        self.conn.execute(opening_query_recurring_tasks)

        self.today = datetime.today().strftime("%Y-%m-%d")
        self.title("Study Tracker")
        self.geometry("1200x800")

        self.rowconfigure(0, weight=0)
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)

        self.canvas_frame = ScrollableFrame(self)
        self.canvas_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10
        )
        self.canvas_frame.columnconfigure(0, weight=1)

        self.tasks = days_goals(self.canvas_frame.scrollable_frame, self)
        self.tasks.grid(
            row=0,
            column=0,
            sticky="new"
        )

        stop_watch_and_task_adder = ttk.Frame(self, style="Debug.TFrame")
        stop_watch_and_task_adder.grid(row=0,column=1, padx=10, pady=10, sticky="wn")
        stop_watch_and_task_adder.columnconfigure(0, weight=1)

        self.goal_page = plan_new_goals(stop_watch_and_task_adder, self)
        self.goal_page.grid(row=0, column=0, padx=10, pady=10)

        self.timer = timer(stop_watch_and_task_adder, self)
        self.timer.grid(row=1, column=0, sticky="nw", padx=10, pady=10)

        self.stats_page = visuals(self)
        self.stats_page.grid(row=1, column=0, padx=10, pady=10, columnspan=2)

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

    def retrieve_new_records(self, date, existing_ids):
        existing_ids = tuple(existing_ids)
        placeholders = ", ".join("?" for _ in existing_ids)

        query = "SELECT * FROM sessions WHERE date = ?"

        if existing_ids:
            query += f" AND id NOT IN ({placeholders})"

        parameters = (date,) + existing_ids

        return self.conn.execute(query, parameters).fetchall()

class days_goals(ttk.Frame):

    def __init__(self, canvas, parent):
        super().__init__(
            canvas,
            borderwidth=1,
            relief="solid",
            padding=10,
            style="Debug.TFrame"
        )

        self.parent = parent

        self.days_items = {}
        self.days_subjects = defaultdict(list)
        self.subject_frames = {}
        self.check_boxes = {}
        self.hours = {}
        self.minutes = {}

        # Let the task area expand with the frame.
        self.columnconfigure(0, weight=1)

        self.header_frame = ttk.Frame(self, style="Debug.TFrame")
        self.header_frame.columnconfigure(0, weight=1)
        self.header_frame.grid(
            row=0, column=0,
            sticky="nw",
            padx=(0, 20),
        )

        self.calendar_frame = ttk.Frame(self, style="Debug.TFrame")
        self.calendar_frame.columnconfigure(0, weight=1)
        self.calendar_frame.grid(
            row=0, column=1,
            sticky="ne",
        )

        ttk.Separator(self, orient="horizontal").grid(
            row=1, column=0,
            columnspan=2,
            sticky="ew",
            pady=(16, 8),
        )

        self.task_frame = ttk.Frame(self, style="Debug.TFrame")
        self.task_frame.grid(
            row=2, column=0,
            columnspan=2,
            sticky="ew",
        )
        self.task_frame.columnconfigure(0, weight=1)

        self.save_frame = ttk.Frame(self, style="Debug.TFrame")
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
            font=self.parent.heading_font,
        )
        goal_label.grid(row=0, column=0, sticky="w")

        subtitle = ttk.Label(
            self.header_frame,
            text="Check off tasks and record your study time.",
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
            self.calendar_frame,
            width=12,
            date_pattern="yyyy-mm-dd",
        )
        self.calendar.grid(row=1, column=0, sticky="e")

        self.calendar.bind(
            "<<DateEntrySelected>>",
            self.change_date,
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

        if subject not in self.subject_frames:
            subject_frame = ttk.Frame(
                self.task_frame,
                padding=(0, 10),
                style="Debug.TFrame"
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

        self.days_subjects[subject].append(task)
        self.days_items[task_id] = record

    def subject_label(self, subject, subject_frame):
        label = ttk.Label(
            subject_frame,
            text=subject,
            font=self.parent.heading_font,
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
            subject_frame,
            text=task_name,
            variable=self.check_boxes[task_id],
        )
        checkbox.grid(
            row=row, column=0,
            sticky="w",
            pady=5,
        )

    def task_time_to_complete(self, task, row, subject_frame):
        task_id, _, task_minutes, _ = task

        hours, minutes = divmod(task_minutes, 60)

        self.hours[task_id] = tk.StringVar(self, value=hours)
        self.minutes[task_id] = tk.StringVar(self, value=minutes)

        time_frame = ttk.Frame(subject_frame, style="Debug.TFrame")
        time_frame.grid(
            row=row, column=1,
            sticky="e",
            padx=(20, 0),
            pady=5
        )

        hours_spinbox = ttk.Spinbox(
            time_frame,
            from_=0,
            to=24,
            width=4,
            justify="center",
            textvariable=self.hours[task_id],
            wrap=True
        )
        hours_spinbox.grid(row=0, column=0)

        ttk.Label(
            time_frame,
            text="hr"
        ).grid(row=0, column=1, padx=(3, 10))

        minutes_spinbox = ttk.Spinbox(
            time_frame,
            from_=0,
            to=59,
            width=4,
            justify="center",
            textvariable=self.minutes[task_id],
            wrap=True
        )
        minutes_spinbox.grid(row=0, column=2)

        ttk.Label(
            time_frame,
            text="min"
        ).grid(row=0, column=3, padx=(3, 0))

    def register_todays_recurring_items(self, date):
        days_recurring_tasks = self.parent.retrieve_recurring_tasks(date)

        for task in days_recurring_tasks:
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
            text="Save Changes",
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

class timer(ttk.Frame):

    def __init__(self, new_frame, parent):
        super().__init__(
            new_frame,
            borderwidth=1,
            relief="solid",
            padding=10,
            style="Debug.TFrame"
        )

        self.parent = parent
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
            font=self.parent.heading_font
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

        self.task_dropdown = ttk.Combobox(
            self,
            textvariable=self.task_choice,
            state="readonly",
            width=30
        )

        self.task_dropdown.grid(
            row=1,
            column=1,
            columnspan=2,
            sticky="ew",
            pady=(0, 15)
        )

        # Timer
        self.timer_display = ttk.Label(
            self,
            textvariable=self.sv,
            font=("Arial", 32, "bold"),
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
            self,
            text="Start",
            command=self.start
        ).grid(
            row=3,
            column=0,
            padx=(0, 5),
            sticky="ew"
        )

        ttk.Button(
            self,
            text="Stop",
            command=self.stop
        ).grid(
            row=3,
            column=1,
            padx=5,
            sticky="ew"
        )

        ttk.Button(
            self,
            text="Finish",
            command=self.complete
        ).grid(
            row=3,
            column=2,
            padx=(5, 0),
            sticky="ew"
        )


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

class plan_new_goals(ttk.Frame):

    def __init__(self, new_frame, parent):
        super().__init__(
            new_frame,
            padding=10,
            relief="solid",
            borderwidth=1,
            style="Debug.TFrame"
        )

        self.parent = parent
        self.tasks = parent.tasks
        self.day_choice = None

        for column in range(4):
            self.columnconfigure(column, weight=1)

        # Subject
        ttk.Label(
            self,
            text="Subject",
            font=self.parent.heading_font
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=(0, 5)
        )

        self.subject = ttk.Entry(self)
        self.subject.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 10)
        )

        # Task
        ttk.Label(
            self,
            text="Task Name",
            font=self.parent.heading_font
        ).grid(
            row=0,
            column=1,
            sticky="w",
            padx=10,
            pady=(0, 5)
        )

        self.task_name = ttk.Entry(self)
        self.task_name.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=10
        )

        # Frequency
        ttk.Label(
            self,
            text="Task Frequency",
            font=self.parent.heading_font
        ).grid(
            row=0,
            column=2,
            sticky="w",
            padx=10,
            pady=(0, 5)
        )

        self.frequency_choice = tk.StringVar(
            self,
            value="One Off"
        )

        self.frequency_dropdown = ttk.Combobox(
            self,
            textvariable=self.frequency_choice,
            values=["One Off", "Daily", "Weekly"],
            state="readonly"
        )

        self.frequency_dropdown.grid(
            row=1,
            column=2,
            sticky="ew",
            padx=10
        )

        # Date / Day
        self.create_date_selection("Choose Date")

        self.frequency_dropdown.bind(
            "<<ComboboxSelected>>",
            self.frequency_adjustment
        )

        # Submit
        button = ttk.Button(
            self,
            text="Add Task",
            command=self.submit_new_record
        )

        button.grid(
            row=2,
            column=3,
            sticky="e",
            pady=(20, 0)
        )


    def create_date_selection(self, label_text):
        self.day_choice = None

        self.date_label = ttk.Label(
            self,
            text=label_text,
            font=self.parent.heading_font
        )

        self.date_label.grid(
            row=0,
            column=3,
            sticky="w",
            padx=(10, 0),
            pady=(0, 5)
        )

        self.calendar = DateEntry(
            self,
            date_pattern="yyyy-mm-dd"
        )

        self.calendar.grid(
            row=1,
            column=3,
            sticky="ew",
            padx=(10, 0)
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
                font=self.parent.heading_font
            )

            self.date_label.grid(
                row=0,
                column=3,
                sticky="w",
                padx=(10, 0),
                pady=(0, 5)
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
                state="readonly"
            )

            self.calendar.grid(
                row=1,
                column=3,
                sticky="ew",
                padx=(10, 0)
            )


    def submit_new_record(self):
        try:
            subject = self.subject.get()
            task = self.task_name.get()
            frequency = self.frequency_choice.get()

            if frequency == "One Off":
                self.parent.insert_record(
                    self.calendar.get(),
                    subject,
                    task
                )
                return

            if self.day_choice is not None:
                day = self.day_choice.get()
            else:
                day = None

            self.parent.insert_recurring_task(
                subject,
                task,
                frequency,
                day=day
            )

        finally:
            self.tasks.check_for_new_records()

class ScrollableFrame(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent, style="Debug.TFrame")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self,
            highlightthickness=1,
            highlightbackground="red"
        )

        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        self.scrollable_frame = ttk.Frame(
            self.canvas,
            style="Debug.TFrame"
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


    def resize_frame(self, event):
        self.canvas.itemconfigure(
            self.canvas_window,
            width=event.width
        )

class StatCard(ttk.Frame):

    def __init__(self, parent, title, value, subtitle=None):
        super().__init__(parent, padding=15, relief="solid", borderwidth=1)

        ttk.Label(
            self,
            text=title.upper()
        ).pack(anchor="w")

        ttk.Label(
            self,
            text=value,
            font=("Arial", 18, "bold")
        ).pack(anchor="w", pady=(8, 0))

        if subtitle:
            ttk.Label(
                self,
                text=subtitle
            ).pack(anchor="w")

class analytics(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Debug.TFrame")
        # self.label = ttk.Label(self, text="Track Progress")
        # self.label.grid(row=0, column=0)
    
if __name__ == "__main__":
    main()
