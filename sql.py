import sqlite3

conn = sqlite3.connect("study_tracker.db")
conn.row_factory = sqlite3.Row

dummy_recurring_tasks = """
INSERT INTO recurring_tasks
    (id, subject, task, frequency, day, start_date, end_date)
VALUES
    (1, 'Python',     'Python practice',      'daily',  NULL,        '2026-10-01', NULL),
    (2, 'French',     'Vocabulary review',    'daily',  NULL,        '2026-10-01', NULL),
    (3, 'SQL',        'SQL exercises',        'weekly', 'Monday',    '2026-10-01', NULL),
    (4, 'Statistics', 'Read Statistical Rethinking',
                                             'weekly', 'Wednesday', '2026-10-01', NULL),
    (5, 'French',     'Listening practice',   'weekly', 'Saturday',  '2026-10-01', '2026-10-31');
"""

dummy_sessions = """
INSERT INTO sessions
    (date, subject, task, minutes, completed, canceled, recurring_id)
VALUES
    ('2026-10-01', 'Python', 'Python practice', 45, 1, 0, 1),
    ('2026-10-01', 'French', 'Vocabulary review', 15, 1, 0, 2),
    ('2026-10-02', 'Python', 'Python practice', 30, 1, 0, 1),
    ('2026-10-02', 'French', 'Vocabulary review', 0, 0, 0, 2),
    ('2026-10-03', 'Python', 'Python practice', 60, 1, 0, 1),
    ('2026-10-03', 'French', 'Vocabulary review', 20, 1, 0, 2),
    ('2026-10-03', 'French', 'Listening practice', 30, 1, 0, 5),
    ('2026-10-04', 'Python', 'Python practice', 0, 0, 1, 1),
    ('2026-10-04', 'French', 'Vocabulary review', 10, 1, 0, 2),
    ('2026-10-05', 'Python', 'Python practice', 40, 1, 0, 1),
    ('2026-10-05', 'French', 'Vocabulary review', 15, 1, 0, 2),
    ('2026-10-05', 'SQL', 'SQL exercises', 45, 1, 0, 3),
    ('2026-10-06', 'Python', 'Python practice', 20, 0, 0, 1),
    ('2026-10-06', 'French', 'Vocabulary review', 0, 0, 1, 2),
    ('2026-10-07', 'Python', 'Python practice', 50, 1, 0, 1),
    ('2026-10-07', 'French', 'Vocabulary review', 15, 1, 0, 2),
    ('2026-10-07', 'Statistics', 'Read Statistical Rethinking', 60, 1, 0, 4),
    ('2026-10-08', 'Python', 'Python practice', 35, 1, 0, 1),
    ('2026-10-08', 'French', 'Vocabulary review', 20, 1, 0, 2),
    ('2026-10-09', 'Python', 'Python practice', 0, 0, 0, 1),
    ('2026-10-09', 'French', 'Vocabulary review', 15, 1, 0, 2),
    ('2026-10-10', 'Python', 'Python practice', 75, 1, 0, 1),
    ('2026-10-10', 'French', 'Vocabulary review', 10, 1, 0, 2),
    ('2026-10-10', 'French', 'Listening practice', 0, 0, 1, 5),
    ('2026-10-11', 'Python', 'Python practice', 45, 1, 0, 1),
    ('2026-10-11', 'French', 'Vocabulary review', 0, 0, 0, 2),
    ('2026-10-12', 'Python', 'Python practice', 30, 1, 0, 1),
    ('2026-10-12', 'French', 'Vocabulary review', 15, 1, 0, 2),
    ('2026-10-12', 'SQL', 'SQL exercises', 25, 0, 0, 3),
    ('2026-10-13', 'Python', 'Python practice', 60, 1, 0, 1),
    ('2026-10-13', 'French', 'Vocabulary review', 20, 1, 0, 2),
    ('2026-10-14', 'Python', 'Python practice', 15, 0, 0, 1),
    ('2026-10-14', 'French', 'Vocabulary review', 10, 1, 0, 2),
    ('2026-10-14', 'Statistics', 'Read Statistical Rethinking', 45, 1, 0, 4),
    ('2026-10-15', 'Python', 'Python practice', 40, 1, 0, 1),
    ('2026-10-15', 'French', 'Vocabulary review', 15, 1, 0, 2),
    ('2026-10-16', 'Python', 'Python practice', 0, 0, 1, 1),
    ('2026-10-16', 'French', 'Vocabulary review', 0, 0, 1, 2),
    ('2026-10-17', 'Python', 'Python practice', 90, 1, 0, 1),
    ('2026-10-17', 'French', 'Vocabulary review', 20, 1, 0, 2),
    ('2026-10-17', 'French', 'Listening practice', 40, 1, 0, 5),
    ('2026-10-18', 'Python', 'Python practice', 55, 1, 0, 1),
    ('2026-10-18', 'French', 'Vocabulary review', 15, 1, 0, 2),
    ('2026-10-19', 'Python', 'Python practice', 30, 1, 0, 1),
    ('2026-10-19', 'French', 'Vocabulary review', 10, 0, 0, 2),
    ('2026-10-19', 'SQL', 'SQL exercises', 60, 1, 0, 3),
    ('2026-10-20', 'Python', 'Python practice', 45, 1, 0, 1),
    ('2026-10-20', 'French', 'Vocabulary review', 15, 1, 0, 2),
    ('2026-10-21', 'Python', 'Python practice', 35, 1, 0, 1),
    ('2026-10-21', 'French', 'Vocabulary review', 0, 0, 0, 2),
    ('2026-10-21', 'Statistics', 'Read Statistical Rethinking', 0, 0, 1, 4),
    ('2026-10-22', 'Python', 'Python practice', 60, 1, 0, 1),
    ('2026-10-22', 'French', 'Vocabulary review', 20, 1, 0, 2),
    ('2026-10-23', 'Python', 'Python practice', 25, 0, 0, 1),
    ('2026-10-23', 'French', 'Vocabulary review', 15, 1, 0, 2),
    ('2026-10-24', 'Python', 'Python practice', 80, 1, 0, 1),
    ('2026-10-24', 'French', 'Vocabulary review', 10, 1, 0, 2),
    ('2026-10-24', 'French', 'Listening practice', 35, 1, 0, 5),
    ('2026-10-25', 'Python', 'Python practice', 50, 1, 0, 1),
    ('2026-10-25', 'French', 'Vocabulary review', 0, 0, 1, 2),
    ('2026-10-26', 'Python', 'Python practice', 45, 1, 0, 1),
    ('2026-10-26', 'French', 'Vocabulary review', 15, 1, 0, 2),
    ('2026-10-26', 'SQL', 'SQL exercises', 40, 1, 0, 3),
    ('2026-10-27', 'Python', 'Python practice', 30, 1, 0, 1),
    ('2026-10-27', 'French', 'Vocabulary review', 20, 1, 0, 2),
    ('2026-10-28', 'Python', 'Python practice', 65, 1, 0, 1),
    ('2026-10-28', 'French', 'Vocabulary review', 15, 1, 0, 2),
    ('2026-10-28', 'Statistics', 'Read Statistical Rethinking', 75, 1, 0, 4),
    ('2026-10-29', 'Python', 'Python practice', 40, 1, 0, 1),
    ('2026-10-29', 'French', 'Vocabulary review', 10, 1, 0, 2),
    ('2026-10-30', 'Python', 'Python practice', 55, 1, 0, 1),
    ('2026-10-30', 'French', 'Vocabulary review', 0, 0, 0, 2),
    ('2026-10-31', 'Python', 'Python practice', 20, 0, 0, 1),
    ('2026-10-31', 'French', 'Vocabulary review', 0, 0, 0, 2),
    ('2026-10-31', 'French', 'Listening practice', 0, 0, 0, 5),

    ('2026-10-03', 'Python', 'Build a timer widget', 90, 1, 0, NULL),
    ('2026-10-06', 'SQL', 'Design study tracker tables', 60, 1, 0, NULL),
    ('2026-10-09', 'Statistics', 'Review Bayes theorem', 35, 0, 0, NULL),
    ('2026-10-11', 'Python', 'Add a notes tab', 120, 1, 0, NULL),
    ('2026-10-15', 'SQL', 'Practice joins', 45, 1, 0, NULL),
    ('2026-10-18', 'Statistics', 'Plot a posterior distribution', 70, 1, 0, NULL),
    ('2026-10-22', 'French', 'Watch a French film', 0, 0, 1, NULL),
    ('2026-10-25', 'Python', 'Fix scrolling behavior', 85, 1, 0, NULL),
    ('2026-10-29', 'Python', 'Style analytics cards', 60, 1, 0, NULL),
    ('2026-10-31', 'Python', 'Test recurring task cancellation', 25, 0, 0, NULL);
"""

conn.executescript(dummy_recurring_tasks)
conn.executescript(dummy_sessions)
conn.commit()
