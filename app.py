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

        self.heading_font = tkfont.nametofont("TkDefaultFont").copy()
        self.heading_font.configure(size=12, weight="bold")

        self.conn = sqlite3.connect("study_tracker.db")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(opening_query_sessions)
        self.conn.execute(opening_query_recurring_tasks)

        self.today = datetime.today().strftime("%Y-%m-%d")
        self.title("Study Tracker")
        self.geometry("500x500")

        self.tasks = days_goals(self)
        self.tasks.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)

        stop_watch_and_task_adder = ttk.Frame(self)
        stop_watch_and_task_adder.grid(row=0,column=1, padx=30, pady=30)

        self.goal_page = plan_new_goals(stop_watch_and_task_adder, self)
        self.goal_page.grid(row=0, column=0, padx=30, pady=30)

        self.timer = timer(stop_watch_and_task_adder, self)
        self.timer.grid(row=1, column=0, sticky="nsew", padx=30, pady=30)

        self.stats_page = visuals(self)
        self.stats_page.grid(row=1, column=0, padx=30, pady=30, columnspan=2)

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

    def __init__(self, parent):
        super().__init__(
            parent,
            borderwidth=1,
            relief="solid",
            padding=20,
        )

        self.parent = parent

        self.days_items = {}
        self.days_subjects = defaultdict(list)
        self.subject_frames = {}
        self.check_boxes = {}
        self.minutes = {}

        # Let the task area expand with the frame.
        self.columnconfigure(0, weight=1)

        self.header_frame = ttk.Frame(self)
        self.header_frame.grid(
            row=0, column=0,
            sticky="nw",
            padx=(0, 20),
        )

        self.calendar_frame = ttk.Frame(self)
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

        self.task_frame = ttk.Frame(self)
        self.task_frame.grid(
            row=2, column=0,
            columnspan=2,
            sticky="ew",
        )
        self.task_frame.columnconfigure(0, weight=1)

        self.save_frame = ttk.Frame(self)
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

        minutes_label = ttk.Label(
            subject_frame,
            text="Minutes",
            width=10,
            anchor="center",
        )
        minutes_label.grid(
            row=0, column=1,
            sticky="e",
            padx=(20, 0),
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

        self.minutes[task_id] = tk.StringVar(
            self,
            value=task_minutes,
        )

        spin_box = ttk.Spinbox(
            subject_frame,
            from_=0,
            to=1000,
            width=8,
            justify="center",
            textvariable=self.minutes[task_id],
            wrap=True,
        )
        spin_box.grid(
            row=row, column=1,
            sticky="e",
            padx=(20, 0),
            pady=5,
        )

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
        super().__init__(new_frame, borderwidth=5, relief="ridge", padding=30)
        self.sv = tk.StringVar()
        self.start_time = None
        self.current_elapsed = None
        self.all_zeros = "00:00:00"
        self.parent = parent
        self.make_widgets()

    def make_widgets(self):

        ttk.Label(self, text = "Time A Task", font=self.parent.heading_font).grid(row=0,column=0)
        ttk.Label(self, text = "Select Task", font=self.parent.heading_font).grid(row=0,column=1)        

        self.timer_display = ttk.Label(self, textvariable=self.sv, text=self.all_zeros)
        self.timer_display.grid(row=1,column=0, columnspan=3)

        ttk.Button(self, text='Start', command=self.start).grid(row=2, column=0, padx=5)
        ttk.Button(self, text='Stop', command=self.stop).grid(row=2, column=1, padx=5)
        ttk.Button(self, text='Finish', command=self.complete).grid(row=2, column=2, padx=5)

    def timer(self):

        self.sv.set(self.format_time(time.time() - self.start_time))
        self.after_job = self.timer_display.after(30, self.timer)

    def start(self):

        self.start_time = time.time()
        if self.current_elapsed is not None:
            self.start_time -= self.current_elapsed
        self.timer()

    def stop(self):

        self.timer_display.after_cancel(self.after_job)
        self.current_elapsed = time.time() - self.start_time

    def complete(self):

        self.timer_display.after_cancel(self.after_job)
        self.sv.set(self.all_zeros)
        self.current_elapsed=None

    @staticmethod

    def format_time(elap):
        hours = int(elap / 3600)
        minutes = int(elap / 60 - hours * 60.0)
        seconds = int(elap - hours * 3600.0 - minutes * 60.0)
        return '%02d:%02d:%02d' % (hours, minutes, seconds)

class plan_new_goals(ttk.Frame):

    def __init__(self, new_frame, parent):
        super().__init__(new_frame)

        self.parent = parent
        self.tasks = parent.tasks
        subject_label = ttk.Label(self, text="Subject", font=self.parent.heading_font)
        subject_label.grid(row=0, column=0)

        self.subject = ttk.Entry(self)
        self.subject.grid(row=1, column=0, padx=30, pady=30)

        task_label = ttk.Label(self, text="Task Name", font=self.parent.heading_font)
        task_label.grid(row=0, column=1)

        self.task_name = ttk.Entry(self)
        self.task_name.grid(row=1, column=1, padx=30, pady=30)

        frequency_label = ttk.Label(self, text="Task Frequency", font=self.parent.heading_font)
        frequency_label.grid(row=0, column=2)
        self.frequency_choice = tk.StringVar(self, value="One Off")
        self.day_choice=None

        dropdown = ttk.Combobox(
            self,
            textvariable=self.frequency_choice,
            values=["One Off", "Daily", "Weekly"],
            state="readonly"
        )
        dropdown.grid(row=1, column=2)

        self.create_date_selection("Choose Date")
        dropdown.bind("<<ComboboxSelected>>", self.frequency_adjustment)
        button = ttk.Button(self, text="Submit", command=self.submit_new_record)
        button.grid(row=2, column=0, columnspan=4, pady=10)

    def create_date_selection(self, label_text):
        self.day_choice=None
        self.date_label = ttk.Label(self,text=label_text,font=self.parent.heading_font)
        self.date_label.grid(row=0, column=3)
        self.calendar = DateEntry(self,width=12,date_pattern="yyyy-mm-dd")
        self.calendar.grid(row=1,column=3,padx=30,pady=30)    

    def frequency_adjustment(self, event):

        self.date_label.destroy()
        self.calendar.destroy()

        if self.frequency_choice.get() == "One Off":
            self.create_date_selection("Choose Starting Date")
        elif self.frequency_choice.get() == "Daily":
            self.create_date_selection("Choose Date")
        else:
            self.date_label = ttk.Label(self, text="Choose Day", font=self.parent.heading_font)
            self.date_label.grid(row=0, column=3)
            self.day_choice = tk.StringVar(self, value="Friday")
            self.calendar = ttk.Combobox(
                self,
                textvariable=self.day_choice,
                values=["Monday", "Tuesday", "Wednesday","Thursday","Friday","Saturday","Sunday"],
                state="readonly"
            )
            self.calendar.grid(row=1, column=3, padx=30, pady=30)

    def submit_new_record(self):
        if self.frequency_choice.get() == "One Off":
            self.parent.insert_record(self.calendar.get(), self.subject.get(), self.task_name.get())
            return
        if self.day_choice is not None:
            day=self.day_choice.get()
        else:
            day=None
        self.parent.insert_recurring_task(self.subject.get(), self.task_name.get(), self.frequency_choice.get(), day=day)

class visuals(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # self.label = ttk.Label(self, text="Track Progress")
        # self.label.grid(row=0, column=0)
    
if __name__ == "__main__":
    main()