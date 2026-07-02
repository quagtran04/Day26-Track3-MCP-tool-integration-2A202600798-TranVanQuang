from __future__ import annotations

import json

from db import SQLiteAdapter, ValidationError
from init_db import DB_PATH, create_database


def show(title: str, payload) -> None:
    print(f"\n## {title}")
    print(json.dumps(payload, indent=2))


def main() -> None:
    create_database(DB_PATH)
    adapter = SQLiteAdapter(DB_PATH)

    show("Tables", adapter.list_tables())
    show("Full schema resource payload", adapter.get_database_schema())
    show("Search students in cohort A1", adapter.search("students", filters={"cohort": "A1"}, order_by="score", descending=True))
    show("Insert a new student", adapter.insert("students", {"name": "Minh Do", "cohort": "A2", "email": "minh.do@example.edu", "score": 86.0}))
    show("Count students", adapter.aggregate("students", "count"))
    show("Average score by cohort", adapter.aggregate("students", "avg", column="score", group_by="cohort"))

    try:
        adapter.search("missing_table")
    except ValidationError as exc:
        show("Expected invalid request error", {"error": str(exc)})


if __name__ == "__main__":
    main()
