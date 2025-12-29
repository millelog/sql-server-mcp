"""Search tools for SQL Server MCP."""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sql_server_mcp.database import Database


async def search_objects(
    db: "Database",
    pattern: str,
    object_types: list[str] | None = None,
    database: str | None = None,
) -> str:
    """Search for database objects by name across all databases.

    Args:
        db: Database connection manager
        pattern: Name pattern to search for (SQL LIKE syntax)
        object_types: Object types to search
        database: Limit search to specific database

    Returns:
        JSON string with matching objects
    """
    # Default to all types if not specified
    if not object_types:
        object_types = ["table", "view", "procedure", "function"]

    results = []

    # Get list of databases to search
    if database:
        databases = [database]
    else:
        db_query = "SELECT name FROM sys.databases WHERE state = 0"
        db_results = db.execute_query(db_query, database="master")
        databases = [r["name"] for r in db_results if db.settings.is_database_allowed(r["name"])]

    for db_name in databases:
        try:
            # Build query based on object types
            type_conditions = []
            if "table" in object_types:
                type_conditions.append("(o.type = 'U')")
            if "view" in object_types:
                type_conditions.append("(o.type = 'V')")
            if "procedure" in object_types:
                type_conditions.append("(o.type = 'P')")
            if "function" in object_types:
                type_conditions.append("(o.type IN ('FN', 'IF', 'TF'))")

            if not type_conditions:
                continue

            type_filter = " OR ".join(type_conditions)

            query = f"""
            SELECT
                '{db_name}' AS database_name,
                s.name AS schema_name,
                o.name AS object_name,
                CASE o.type
                    WHEN 'U' THEN 'table'
                    WHEN 'V' THEN 'view'
                    WHEN 'P' THEN 'procedure'
                    WHEN 'FN' THEN 'scalar_function'
                    WHEN 'IF' THEN 'inline_table_function'
                    WHEN 'TF' THEN 'table_function'
                END AS object_type,
                o.create_date,
                o.modify_date
            FROM sys.objects o
            INNER JOIN sys.schemas s ON o.schema_id = s.schema_id
            WHERE o.name LIKE '{pattern}'
            AND ({type_filter})
            AND o.is_ms_shipped = 0
            ORDER BY o.name
            """

            db_results = db.execute_query(query, db_name, max_rows=100)
            results.extend(db_results)

        except Exception:
            # Skip databases we can't access
            continue

    return json.dumps(
        {
            "pattern": pattern,
            "results": results,
            "count": len(results),
            "databases_searched": len(databases),
        },
        indent=2,
        default=str,
    )


async def search_definitions(
    db: "Database",
    pattern: str,
    database: str | None = None,
    object_types: list[str] | None = None,
) -> str:
    """Search within object definitions.

    Args:
        db: Database connection manager
        pattern: Text pattern to search for
        database: Limit search to specific database
        object_types: Object types to search

    Returns:
        JSON string with matching objects and context
    """
    # Default to searchable types
    if not object_types:
        object_types = ["view", "procedure", "function"]

    results = []

    # Get list of databases to search
    if database:
        databases = [database]
    else:
        db_query = "SELECT name FROM sys.databases WHERE state = 0"
        db_results = db.execute_query(db_query, database="master")
        databases = [r["name"] for r in db_results if db.settings.is_database_allowed(r["name"])]

    for db_name in databases:
        try:
            # Build query based on object types
            type_conditions = []
            if "view" in object_types:
                type_conditions.append("(o.type = 'V')")
            if "procedure" in object_types:
                type_conditions.append("(o.type = 'P')")
            if "function" in object_types:
                type_conditions.append("(o.type IN ('FN', 'IF', 'TF'))")

            if not type_conditions:
                continue

            type_filter = " OR ".join(type_conditions)

            query = f"""
            SELECT
                '{db_name}' AS database_name,
                s.name AS schema_name,
                o.name AS object_name,
                CASE o.type
                    WHEN 'V' THEN 'view'
                    WHEN 'P' THEN 'procedure'
                    WHEN 'FN' THEN 'scalar_function'
                    WHEN 'IF' THEN 'inline_table_function'
                    WHEN 'TF' THEN 'table_function'
                END AS object_type,
                CHARINDEX('{pattern}', m.definition) AS match_position
            FROM sys.objects o
            INNER JOIN sys.schemas s ON o.schema_id = s.schema_id
            INNER JOIN sys.sql_modules m ON o.object_id = m.object_id
            WHERE m.definition LIKE '%{pattern}%'
            AND ({type_filter})
            AND o.is_ms_shipped = 0
            ORDER BY o.name
            """

            db_results = db.execute_query(query, db_name, max_rows=100)
            results.extend(db_results)

        except Exception:
            # Skip databases we can't access
            continue

    return json.dumps(
        {
            "pattern": pattern,
            "results": results,
            "count": len(results),
            "databases_searched": len(databases),
        },
        indent=2,
        default=str,
    )
