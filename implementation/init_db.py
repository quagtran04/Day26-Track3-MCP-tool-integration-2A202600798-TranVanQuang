from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "school.db"

SCHEMA_SQL = """
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;

CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cohort TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    score REAL NOT NULL
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    credits INTEGER NOT NULL
);

CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    grade REAL NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
"""

SEED_SQL = """
INSERT INTO students (name, cohort, email, score) VALUES
    ('An Nguyen', 'A1', 'an.nguyen@example.edu', 88.5),
    ('Binh Tran', 'A1', 'binh.tran@example.edu', 91.0),
    ('Chi Le', 'A2', 'chi.le@example.edu', 79.5),
    ('Dung Pham', 'B1', 'dung.pham@example.edu', 84.0),
    ('Hoa Vu', 'B1', 'hoa.vu@example.edu', 95.5);

INSERT INTO courses (code, title, credits) VALUES
    ('MCP101', 'Model Context Protocol Basics', 3),
    ('DB201', 'Applied Databases', 4),
    ('AI310', 'AI Tool Integration', 3);

INSERT INTO enrollments (student_id, course_id, grade, status) VALUES
    (1, 1, 87.0, 'completed'),
    (1, 2, 90.0, 'completed'),
    (2, 1, 93.0, 'completed'),
    (3, 2, 78.0, 'completed'),
    (4, 3, 82.0, 'in_progress'),
    (5, 3, 96.0, 'completed');
"""


def create_database(db_path: str | Path = DB_PATH) -> Path:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.executescript(SEED_SQL)
        connection.commit()
    return db_path


if __name__ == "__main__":
    path = create_database()
    print(f"Created SQLite database at {path}")
