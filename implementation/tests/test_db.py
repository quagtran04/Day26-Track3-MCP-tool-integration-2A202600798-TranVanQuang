from __future__ import annotations

from pathlib import Path

import pytest

from db import SQLiteAdapter, ValidationError
from init_db import create_database


@pytest.fixture()
def adapter(tmp_path: Path) -> SQLiteAdapter:
    db_path = tmp_path / "school.db"
    create_database(db_path)
    return SQLiteAdapter(db_path)


def test_search_filters_ordering_and_pagination(adapter: SQLiteAdapter) -> None:
    result = adapter.search("students", filters={"cohort": "A1"}, order_by="score", descending=True, limit=1)

    assert result["count"] == 1
    assert result["rows"][0]["name"] == "Binh Tran"


def test_insert_returns_generated_id(adapter: SQLiteAdapter) -> None:
    result = adapter.insert("students", {"name": "Lan Ho", "cohort": "A2", "email": "lan.ho@example.edu", "score": 89.0})

    assert result["inserted"]["id"] > 0
    assert result["inserted"]["email"] == "lan.ho@example.edu"


def test_aggregate_avg_by_group(adapter: SQLiteAdapter) -> None:
    result = adapter.aggregate("students", "avg", column="score", group_by="cohort")

    cohorts = {row["cohort"] for row in result["rows"]}
    assert {"A1", "A2", "B1"}.issubset(cohorts)


def test_rejects_unknown_table(adapter: SQLiteAdapter) -> None:
    with pytest.raises(ValidationError, match="Unknown table"):
        adapter.search("not_a_table")


def test_rejects_unknown_column(adapter: SQLiteAdapter) -> None:
    with pytest.raises(ValidationError, match="Unknown column"):
        adapter.search("students", filters={"password": "secret"})


def test_rejects_bad_operator(adapter: SQLiteAdapter) -> None:
    with pytest.raises(ValidationError, match="Unsupported filter operator"):
        adapter.search("students", filters={"score": {"contains": 90}})


def test_rejects_empty_insert(adapter: SQLiteAdapter) -> None:
    with pytest.raises(ValidationError, match="cannot be empty"):
        adapter.insert("students", {})
