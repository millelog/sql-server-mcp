"""View-related tools for SQL Server MCP."""

import json
from typing import TYPE_CHECKING

from sql_server_mcp.validation import sanitize_identifier

if TYPE_CHECKING:
    from sql_server_mcp.database import Database


def _parse_view_name(view: str) -> tuple[str | None, str]:
    """Parse schema.view or just view name."""
    parts = view.split(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, parts[0]


async def list_views(
    db: "Database",
    database: str | None = None,
    schema: str | None = None,
    name_pattern: str | None = None,
) -> str:
    """List all views in a database.

    Args:
        db: Database connection manager
        database: Database name
        schema: Filter by schema
        name_pattern: Filter by name pattern

    Returns:
        JSON string with view list
    """
    query = """
    SELECT
        s.name AS schema_name,
        v.name AS view_name,
        v.create_date,
        v.modify_date,
        OBJECTPROPERTY(v.object_id, 'IsSchemaBound') AS is_schema_bound,
        OBJECTPROPERTY(v.object_id, 'IsIndexed') AS is_indexed
    FROM sys.views v
    INNER JOIN sys.schemas s ON v.schema_id = s.schema_id
    WHERE 1=1
    """

    if schema:
        sanitize_identifier(schema)
        query += f" AND s.name = '{schema}'"

    if name_pattern:
        query += f" AND v.name LIKE '{name_pattern}'"

    query += " ORDER BY s.name, v.name"

    results = db.execute_query(query, database)

    return json.dumps(
        {
            "views": results,
            "count": len(results),
        },
        indent=2,
        default=str,
    )


async def get_view_definition(
    db: "Database",
    view: str,
    database: str | None = None,
) -> str:
    """Get the CREATE VIEW definition.

    Args:
        db: Database connection manager
        view: View name (can include schema)
        database: Database name

    Returns:
        CREATE VIEW statement or error message
    """
    schema, view_name = _parse_view_name(view)
    sanitize_identifier(view_name)
    if schema:
        sanitize_identifier(schema)

    query = f"""
    SELECT
        s.name AS schema_name,
        v.name AS view_name,
        m.definition,
        OBJECTPROPERTY(v.object_id, 'IsEncrypted') AS is_encrypted
    FROM sys.views v
    INNER JOIN sys.schemas s ON v.schema_id = s.schema_id
    LEFT JOIN sys.sql_modules m ON v.object_id = m.object_id
    WHERE v.name = '{view_name}'
    {"AND s.name = '" + schema + "'" if schema else ""}
    """

    results = db.execute_query(query, database)

    if not results:
        return f"View '{view}' not found"

    result = results[0]

    if result["is_encrypted"]:
        return f"-- View '{view}' is encrypted. Definition is not available."

    if result["definition"]:
        return result["definition"]

    return f"-- Unable to retrieve definition for view '{view}'"


async def get_view_columns(
    db: "Database",
    view: str,
    database: str | None = None,
) -> str:
    """Get column information for a view.

    Args:
        db: Database connection manager
        view: View name
        database: Database name

    Returns:
        JSON string with column details
    """
    schema, view_name = _parse_view_name(view)
    sanitize_identifier(view_name)
    if schema:
        sanitize_identifier(schema)

    query = f"""
    SELECT
        c.name AS column_name,
        t.name AS data_type,
        c.max_length,
        c.precision,
        c.scale,
        c.is_nullable
    FROM sys.columns c
    INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
    INNER JOIN sys.views v ON c.object_id = v.object_id
    INNER JOIN sys.schemas s ON v.schema_id = s.schema_id
    WHERE v.name = '{view_name}'
    {"AND s.name = '" + schema + "'" if schema else ""}
    ORDER BY c.column_id
    """

    results = db.execute_query(query, database)

    return json.dumps(
        {
            "view": view,
            "columns": results,
            "count": len(results),
        },
        indent=2,
        default=str,
    )
