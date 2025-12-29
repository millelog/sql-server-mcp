"""Query execution tools for SQL Server MCP."""

import json
from typing import TYPE_CHECKING

from sql_server_mcp.validation import ValidationError, quote_identifier, sanitize_identifier

if TYPE_CHECKING:
    from sql_server_mcp.database import Database


def _parse_table_name(table: str) -> tuple[str | None, str]:
    """Parse schema.table or just table name."""
    parts = table.split(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, parts[0]


async def execute_query(
    db: "Database",
    query: str,
    database: str | None = None,
    max_rows: int = 100,
) -> str:
    """Execute a read-only SELECT query.

    Args:
        db: Database connection manager
        query: The SELECT query to execute
        database: Database to query
        max_rows: Maximum rows to return

    Returns:
        JSON string with query results

    Raises:
        ValidationError: If query is not read-only
    """
    # Validation is done in db.execute_query
    try:
        results = db.execute_query(query, database, max_rows=max_rows)

        truncated = len(results) >= max_rows

        return json.dumps(
            {
                "results": results,
                "row_count": len(results),
                "truncated": truncated,
                "max_rows": max_rows,
            },
            indent=2,
            default=str,
        )

    except ValidationError as e:
        return json.dumps(
            {
                "error": str(e),
                "query_blocked": True,
            },
            indent=2,
        )


async def get_sample_data(
    db: "Database",
    table: str,
    database: str | None = None,
    rows: int = 10,
    random: bool = False,
) -> str:
    """Get sample rows from a table.

    Args:
        db: Database connection manager
        table: Table name (can include schema)
        database: Database name
        rows: Number of rows to return
        random: Return random sample instead of first N rows

    Returns:
        JSON string with sample data
    """
    schema, table_name = _parse_table_name(table)
    sanitize_identifier(table_name)
    if schema:
        sanitize_identifier(schema)

    # Ensure rows doesn't exceed max
    max_rows = db.settings.max_rows
    rows = min(rows, max_rows)

    # Build table reference
    if schema:
        table_ref = f"{quote_identifier(schema)}.{quote_identifier(table_name)}"
    else:
        table_ref = quote_identifier(table_name)

    if random:
        query = f"SELECT TOP {rows} * FROM {table_ref} ORDER BY NEWID()"
    else:
        query = f"SELECT TOP {rows} * FROM {table_ref}"

    results = db.execute_query(query, database, max_rows=rows)

    return json.dumps(
        {
            "table": table,
            "sample_data": results,
            "row_count": len(results),
            "is_random": random,
        },
        indent=2,
        default=str,
    )
