import sqlite3

conn = sqlite3.connect("study_tracker.db")
conn.row_factory = sqlite3.Row

# Create the table
conn.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY,
        date TEXT NOT NULL,
        subject TEXT NOT NULL,
        task TEXT NOT NULL,
        minutes INTEGER NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1))
    )
""")

dummy_data = [
    # date, subject, task, minutes, completed
    ("2026-10-18", "Python", "Practice for loops", 25, 1),
    ("2026-10-18", "Statistics", "Read about probability", 40, 1),
    ("2026-10-19", "French", "Practice listening", 20, 1),
    ("2026-10-19", "Python", "Build a Tkinter frame", 60, 1),
    ("2026-10-20", "Statistics", "Practice Bayes theorem", 45, 1),
    ("2026-10-20", "French", "Review vocabulary", 15, 0),
    ("2026-10-21", "Python", "Add buttons to study tracker", 35, 1),
    ("2026-10-21", "SQL", "Learn SELECT queries", 30, 1),
    ("2026-10-22", "Statistics", "Fit a Poisson model", 55, 1),
    ("2026-10-22", "SQL", "Practice filtering rows", 25, 0),
    ("2026-10-23", "Python", "Practice classes", 50, 1),
    ("2026-10-23", "French", "Read a short article", 20, 1),
    ("2026-10-24", "SQL", "Create a SQLite database", 30, 1),
    ("2026-10-24", "Python", "Connect app to database", 45, 1),
    ("2026-10-25", "Statistics", "Review probability distributions", 30, 1),
    ("2026-10-25", "French", "Practice speaking", 10, 0),

    # Next week: future tasks start with zero minutes
    ("2026-10-26", "Python", "Add a completed checkbox", 0, 0),
    ("2026-10-26", "SQL", "Practice UPDATE statements", 0, 0),
    ("2026-10-27", "Statistics", "Review logistic regression", 0, 0),
    ("2026-10-27", "French", "Listen to a French podcast", 0, 0),
    ("2026-10-28", "Python", "Build a study timer", 0, 0),
    ("2026-10-28", "SQL", "Practice GROUP BY queries", 0, 0),
    ("2026-10-29", "Statistics", "Fit a binomial model", 0, 0),
    ("2026-10-29", "French", "Review verb conjugations", 0, 0),
    ("2026-10-30", "Python", "Plot weekly study minutes", 0, 0),
    ("2026-10-30", "SQL", "Calculate totals by subject", 0, 0),
    ("2026-10-31", "Statistics", "Practice interpreting posteriors", 0, 0),
    ("2026-10-31", "French", "Read a short story", 0, 0),
    ("2026-11-01", "Python", "Test the study tracker", 0, 0),
    ("2026-11-01", "SQL", "Review database queries", 0, 0),
]

conn.executemany("""
    INSERT INTO sessions (date, subject, task, minutes, completed)
    VALUES (?, ?, ?, ?, ?)
""", dummy_data)

conn.commit()

rows = conn.execute("""SELECT * FROM sessions""").fetchall()

for row in rows:
    print(dict(row))
