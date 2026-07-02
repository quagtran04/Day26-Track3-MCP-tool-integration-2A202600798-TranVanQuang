from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class ValidationError(Exception):
    """Raised when a request cannot be safely executed."""


class SQLiteAdapter:
    """Small SQLite data-access layer with identifier validation."""

    FILTER_OPERATORS = {
        "eq": "=",
        "ne": "!=",
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
        "like": "LIKE",
        "in": "IN",
    }
    AGGREGATES = {"count", "avg", "sum", "min", "max"}

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def list_tables(self) -> list[str]:
        sql = """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        with self.connect() as connection:
            rows = connection.execute(sql).fetchall()
        return [row["name"] for row in rows]

    def get_table_schema(self, table: str) -> list[dict[str, Any]]:
        self._validate_table(table)
        with self.connect() as connection:
            rows = connection.execute(f"PRAGMA table_info({self._quote_identifier(table)})").fetchall()
        return [
            {
                "name": row["name"],
                "type": row["type"],
                "not_null": bool(row["notnull"]),
                "default": row["dflt_value"],
                "primary_key": bool(row["pk"]),
            }
            for row in rows
        ]

    def get_database_schema(self) -> dict[str, list[dict[str, Any]]]:
        return {table: self.get_table_schema(table) for table in self.list_tables()}

    def search(
        self,
        table: str,
        columns: list[str] | None = None,
        filters: Any = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = False,
    ) -> dict[str, Any]:
        self._validate_table(table)
        table_columns = self._column_names(table)
        selected_columns = self._selected_columns(columns, table_columns)
        where_sql, params = self._build_where(filters, table_columns)
        limit, offset = self._validate_pagination(limit, offset)

        sql = f"SELECT {', '.join(self._quote_identifier(c) for c in selected_columns)} FROM {self._quote_identifier(table)}"
        if where_sql:
            sql += f" WHERE {where_sql}"
        if order_by:
            self._validate_column(order_by, table_columns)
            direction = "DESC" if descending else "ASC"
            sql += f" ORDER BY {self._quote_identifier(order_by)} {direction}"
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.connect() as connection:
            rows = [dict(row) for row in connection.execute(sql, params).fetchall()]
        return {"table": table, "count": len(rows), "rows": rows, "limit": limit, "offset": offset}

    def insert(self, table: str, values: dict[str, Any]) -> dict[str, Any]:
        self._validate_table(table)
        if not values:
            raise ValidationError("Insert values cannot be empty.")

        table_columns = self._column_names(table)
        for column in values:
            self._validate_column(column, table_columns)

        columns = list(values.keys())
        placeholders = ", ".join("?" for _ in columns)
        column_sql = ", ".join(self._quote_identifier(column) for column in columns)
        sql = f"INSERT INTO {self._quote_identifier(table)} ({column_sql}) VALUES ({placeholders})"

        with self.connect() as connection:
            cursor = connection.execute(sql, [values[column] for column in columns])
            connection.commit()
            inserted_id = cursor.lastrowid

        payload = dict(values)
        pk_column = self._single_integer_primary_key(table)
        if pk_column and pk_column not in payload:
            payload[pk_column] = inserted_id
        return {"table": table, "inserted": payload}

    def aggregate(
        self,
        table: str,
        metric: str,
        column: str | None = None,
        filters: Any = None,
        group_by: str | list[str] | None = None,
    ) -> dict[str, Any]:
        self._validate_table(table)
        metric = metric.lower()
        if metric not in self.AGGREGATES:
            raise ValidationError(f"Unsupported aggregate metric '{metric}'.")

        table_columns = self._column_names(table)
        if metric == "count" and column is None:
            aggregate_target = "*"
        else:
            if column is None:
                raise ValidationError(f"Aggregate metric '{metric}' requires a column.")
            self._validate_column(column, table_columns)
            aggregate_target = self._quote_identifier(column)

        group_columns = self._normalize_group_by(group_by, table_columns)
        where_sql, params = self._build_where(filters, table_columns)

        select_parts = [self._quote_identifier(column_name) for column_name in group_columns]
        select_parts.append(f"{metric.upper()}({aggregate_target}) AS value")
        sql = f"SELECT {', '.join(select_parts)} FROM {self._quote_identifier(table)}"
        if where_sql:
            sql += f" WHERE {where_sql}"
        if group_columns:
            sql += " GROUP BY " + ", ".join(self._quote_identifier(column_name) for column_name in group_columns)

        with self.connect() as connection:
            rows = [dict(row) for row in connection.execute(sql, params).fetchall()]
        return {"table": table, "metric": metric, "column": column, "group_by": group_columns, "rows": rows}

    def _validate_table(self, table: str) -> None:
        if table not in self.list_tables():
            raise ValidationError(f"Unknown table '{table}'.")

    def _column_names(self, table: str) -> set[str]:
        return {column["name"] for column in self.get_table_schema(table)}

    def _validate_column(self, column: str, table_columns: set[str]) -> None:
        if column not in table_columns:
            raise ValidationError(f"Unknown column '{column}'.")

    def _selected_columns(self, columns: list[str] | None, table_columns: set[str]) -> list[str]:
        if not columns:
            return sorted(table_columns)
        for column in columns:
            self._validate_column(column, table_columns)
        return columns

    def _build_where(self, filters: Any, table_columns: set[str]) -> tuple[str, list[Any]]:
        if not filters:
            return "", []

        clauses: list[str] = []
        params: list[Any] = []
        for column, operator, value in self._normalize_filters(filters):
            self._validate_column(column, table_columns)
            if operator not in self.FILTER_OPERATORS:
                raise ValidationError(f"Unsupported filter operator '{operator}'.")
            sql_operator = self.FILTER_OPERATORS[operator]
            if operator == "in":
                if not isinstance(value, list) or not value:
                    raise ValidationError("The 'in' operator requires a non-empty list value.")
                placeholders = ", ".join("?" for _ in value)
                clauses.append(f"{self._quote_identifier(column)} IN ({placeholders})")
                params.extend(value)
            else:
                clauses.append(f"{self._quote_identifier(column)} {sql_operator} ?")
                params.append(value)
        return " AND ".join(clauses), params

    def _normalize_filters(self, filters: Any) -> list[tuple[str, str, Any]]:
        if isinstance(filters, dict):
            normalized = []
            for column, condition in filters.items():
                if isinstance(condition, dict):
                    for operator, value in condition.items():
                        normalized.append((column, operator, value))
                else:
                    normalized.append((column, "eq", condition))
            return normalized

        if isinstance(filters, list):
            normalized = []
            for item in filters:
                if not isinstance(item, dict):
                    raise ValidationError("Each filter list item must be an object.")
                column = item.get("column")
                operator = item.get("operator", "eq")
                if "value" not in item:
                    raise ValidationError("Each filter object must include a value.")
                normalized.append((column, operator, item["value"]))
            return normalized

        raise ValidationError("Filters must be an object or a list of filter objects.")

    def _validate_pagination(self, limit: int, offset: int) -> tuple[int, int]:
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100.")
        if offset < 0:
            raise ValidationError("Offset cannot be negative.")
        return limit, offset

    def _normalize_group_by(self, group_by: str | list[str] | None, table_columns: set[str]) -> list[str]:
        if group_by is None:
            return []
        group_columns = [group_by] if isinstance(group_by, str) else group_by
        for column in group_columns:
            self._validate_column(column, table_columns)
        return group_columns

    def _single_integer_primary_key(self, table: str) -> str | None:
        primary_keys = [column for column in self.get_table_schema(table) if column["primary_key"]]
        if len(primary_keys) == 1 and "INT" in primary_keys[0]["type"].upper():
            return primary_keys[0]["name"]
        return None

    def _quote_identifier(self, identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'
