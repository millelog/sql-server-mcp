"""Stored procedure tools for SQL Server MCP."""

import json
from typing import TYPE_CHECKING

from sql_server_mcp.validation import sanitize_identifier

if TYPE_CHECKING:
    from sql_server_mcp.database import Database


def _parse_procedure_name(procedure: str) -> tuple[str | None, str]:
    """Parse schema.procedure or just procedure name."""
    parts = procedure.split(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, parts[0]


async def list_procedures(
    db: "Database",
    database: str | None = None,
    schema: str | None = None,
    name_pattern: str | None = None,
    include_system: bool = False,
) -> str:
    """List all stored procedures in a database.

    Args:
        db: Database connection manager
        database: Database name
        schema: Filter by schema
        name_pattern: Filter by name pattern
        include_system: Include system procedures

    Returns:
        JSON string with procedure list
    """
    query = """
    SELECT
        s.name AS schema_name,
        p.name AS procedure_name,
        p.create_date,
        p.modify_date,
        OBJECTPROPERTY(p.object_id, 'IsEncrypted') AS is_encrypted
    FROM sys.procedures p
    INNER JOIN sys.schemas s ON p.schema_id = s.schema_id
    WHERE 1=1
    """

    if not include_system:
        query += " AND p.is_ms_shipped = 0"

    if schema:
        sanitize_identifier(schema)
        query += f" AND s.name = '{schema}'"

    if name_pattern:
        query += f" AND p.name LIKE '{name_pattern}'"

    query += " ORDER BY s.name, p.name"

    results = db.execute_query(query, database)

    return json.dumps(
        {
            "procedures": results,
            "count": len(results),
        },
        indent=2,
        default=str,
    )


async def get_procedure_definition(
    db: "Database",
    procedure: str,
    database: str | None = None,
) -> str:
    """Get the CREATE PROCEDURE definition.

    Args:
        db: Database connection manager
        procedure: Procedure name (can include schema)
        database: Database name

    Returns:
        CREATE PROCEDURE statement or error message
    """
    schema, proc_name = _parse_procedure_name(procedure)
    sanitize_identifier(proc_name)
    if schema:
        sanitize_identifier(schema)

    query = f"""
    SELECT
        s.name AS schema_name,
        p.name AS procedure_name,
        m.definition,
        OBJECTPROPERTY(p.object_id, 'IsEncrypted') AS is_encrypted
    FROM sys.procedures p
    INNER JOIN sys.schemas s ON p.schema_id = s.schema_id
    LEFT JOIN sys.sql_modules m ON p.object_id = m.object_id
    WHERE p.name = '{proc_name}'
    {"AND s.name = '" + schema + "'" if schema else ""}
    """

    results = db.execute_query(query, database)

    if not results:
        return f"Procedure '{procedure}' not found"

    result = results[0]

    if result["is_encrypted"]:
        return f"-- Procedure '{procedure}' is encrypted. Definition is not available."

    if result["definition"]:
        return result["definition"]

    return f"-- Unable to retrieve definition for procedure '{procedure}'"


async def get_procedure_parameters(
    db: "Database",
    procedure: str,
    database: str | None = None,
) -> str:
    """Get parameter information for a stored procedure.

    Args:
        db: Database connection manager
        procedure: Procedure name
        database: Database name

    Returns:
        JSON string with parameter details
    """
    schema, proc_name = _parse_procedure_name(procedure)
    sanitize_identifier(proc_name)
    if schema:
        sanitize_identifier(schema)

    query = f"""
    SELECT
        par.name AS parameter_name,
        t.name AS data_type,
        par.max_length,
        par.precision,
        par.scale,
        par.is_output,
        par.has_default_value,
        par.default_value,
        par.parameter_id
    FROM sys.parameters par
    INNER JOIN sys.procedures p ON par.object_id = p.object_id
    INNER JOIN sys.schemas s ON p.schema_id = s.schema_id
    INNER JOIN sys.types t ON par.user_type_id = t.user_type_id
    WHERE p.name = '{proc_name}'
    {"AND s.name = '" + schema + "'" if schema else ""}
    ORDER BY par.parameter_id
    """

    results = db.execute_query(query, database)

    # Format parameter direction
    for param in results:
        if param["is_output"]:
            param["direction"] = "OUTPUT"
        else:
            param["direction"] = "INPUT"

    return json.dumps(
        {
            "procedure": procedure,
            "parameters": results,
            "count": len(results),
        },
        indent=2,
        default=str,
    )
