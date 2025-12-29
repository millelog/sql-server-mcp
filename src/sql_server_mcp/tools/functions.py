"""User-defined function tools for SQL Server MCP."""

import json
from typing import TYPE_CHECKING

from sql_server_mcp.validation import sanitize_identifier

if TYPE_CHECKING:
    from sql_server_mcp.database import Database


def _parse_function_name(function: str) -> tuple[str | None, str]:
    """Parse schema.function or just function name."""
    parts = function.split(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, parts[0]


# Function type mapping
FUNCTION_TYPES = {
    "FN": "Scalar",
    "IF": "Inline Table-Valued",
    "TF": "Table-Valued",
}


async def list_functions(
    db: "Database",
    database: str | None = None,
    schema: str | None = None,
    function_type: str = "all",
) -> str:
    """List all user-defined functions in a database.

    Args:
        db: Database connection manager
        database: Database name
        schema: Filter by schema
        function_type: Filter by type: 'scalar', 'table', or 'all'

    Returns:
        JSON string with function list
    """
    query = """
    SELECT
        s.name AS schema_name,
        o.name AS function_name,
        o.type AS type_code,
        CASE o.type
            WHEN 'FN' THEN 'Scalar'
            WHEN 'IF' THEN 'Inline Table-Valued'
            WHEN 'TF' THEN 'Table-Valued'
        END AS function_type,
        o.create_date,
        o.modify_date,
        OBJECTPROPERTY(o.object_id, 'IsEncrypted') AS is_encrypted
    FROM sys.objects o
    INNER JOIN sys.schemas s ON o.schema_id = s.schema_id
    WHERE o.type IN ('FN', 'IF', 'TF')
    AND o.is_ms_shipped = 0
    """

    if schema:
        sanitize_identifier(schema)
        query += f" AND s.name = '{schema}'"

    if function_type.lower() == "scalar":
        query += " AND o.type = 'FN'"
    elif function_type.lower() == "table":
        query += " AND o.type IN ('IF', 'TF')"

    query += " ORDER BY s.name, o.name"

    results = db.execute_query(query, database)

    return json.dumps(
        {
            "functions": results,
            "count": len(results),
        },
        indent=2,
        default=str,
    )


async def get_function_definition(
    db: "Database",
    function: str,
    database: str | None = None,
) -> str:
    """Get the CREATE FUNCTION definition.

    Args:
        db: Database connection manager
        function: Function name (can include schema)
        database: Database name

    Returns:
        CREATE FUNCTION statement or error message
    """
    schema, func_name = _parse_function_name(function)
    sanitize_identifier(func_name)
    if schema:
        sanitize_identifier(schema)

    query = f"""
    SELECT
        s.name AS schema_name,
        o.name AS function_name,
        o.type AS type_code,
        m.definition,
        OBJECTPROPERTY(o.object_id, 'IsEncrypted') AS is_encrypted
    FROM sys.objects o
    INNER JOIN sys.schemas s ON o.schema_id = s.schema_id
    LEFT JOIN sys.sql_modules m ON o.object_id = m.object_id
    WHERE o.type IN ('FN', 'IF', 'TF')
    AND o.name = '{func_name}'
    {"AND s.name = '" + schema + "'" if schema else ""}
    """

    results = db.execute_query(query, database)

    if not results:
        return f"Function '{function}' not found"

    result = results[0]

    if result["is_encrypted"]:
        return f"-- Function '{function}' is encrypted. Definition is not available."

    if result["definition"]:
        return result["definition"]

    return f"-- Unable to retrieve definition for function '{function}'"
