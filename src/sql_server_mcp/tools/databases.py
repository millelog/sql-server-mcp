"""Database-related tools for SQL Server MCP."""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sql_server_mcp.database import Database

# System databases to exclude by default
SYSTEM_DATABASES = {"master", "model", "msdb", "tempdb"}


async def list_databases(
    db: "Database",
    include_system: bool = False,
    name_pattern: str | None = None,
) -> str:
    """List all accessible databases on the SQL Server.

    Args:
        db: Database connection manager
        include_system: Include system databases
        name_pattern: Filter by name pattern (SQL LIKE syntax)

    Returns:
        JSON string with database list
    """
    query = """
    SELECT
        d.name AS database_name,
        d.database_id,
        d.create_date,
        d.state_desc AS state,
        d.recovery_model_desc AS recovery_model,
        CAST(SUM(mf.size) * 8.0 / 1024 AS DECIMAL(10,2)) AS size_mb
    FROM sys.databases d
    LEFT JOIN sys.master_files mf ON d.database_id = mf.database_id
    WHERE 1=1
    """

    if not include_system:
        system_list = ", ".join(f"'{db}'" for db in SYSTEM_DATABASES)
        query += f" AND d.name NOT IN ({system_list})"

    if name_pattern:
        query += f" AND d.name LIKE '{name_pattern}'"

    query += """
    GROUP BY d.name, d.database_id, d.create_date, d.state_desc, d.recovery_model_desc
    ORDER BY d.name
    """

    results = db.execute_query(query, database="master")

    return json.dumps(
        {
            "databases": results,
            "count": len(results),
        },
        indent=2,
        default=str,
    )


async def list_schemas(
    db: "Database",
    database: str | None = None,
) -> str:
    """List all schemas in a database with object counts.

    Args:
        db: Database connection manager
        database: Database name (uses default if not specified)

    Returns:
        JSON string with schema list and object counts
    """
    query = """
    SELECT
        s.name AS schema_name,
        s.schema_id,
        dp.name AS owner_name,
        COUNT(CASE WHEN o.type = 'U' THEN 1 END) AS table_count,
        COUNT(CASE WHEN o.type = 'V' THEN 1 END) AS view_count,
        COUNT(CASE WHEN o.type = 'P' THEN 1 END) AS procedure_count,
        COUNT(CASE WHEN o.type IN ('FN', 'IF', 'TF') THEN 1 END) AS function_count,
        COUNT(o.object_id) AS total_objects
    FROM sys.schemas s
    INNER JOIN sys.database_principals dp ON s.principal_id = dp.principal_id
    LEFT JOIN sys.objects o ON s.schema_id = o.schema_id AND o.is_ms_shipped = 0
    WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA', 'guest')
    GROUP BY s.name, s.schema_id, dp.name
    ORDER BY s.name
    """

    results = db.execute_query(query, database)

    return json.dumps(
        {
            "database": database or db.settings.database,
            "schemas": results,
            "count": len(results),
        },
        indent=2,
        default=str,
    )


async def get_schema_overview(
    db: "Database",
    database: str | None = None,
) -> str:
    """Get an overview of a database schema.

    Args:
        db: Database connection manager
        database: Database name (uses default if not specified)

    Returns:
        JSON string with schema overview
    """
    # Count tables
    tables_query = """
    SELECT COUNT(*) as count FROM sys.tables WHERE type = 'U'
    """
    table_count = db.execute_scalar(tables_query, database)

    # Count views
    views_query = """
    SELECT COUNT(*) as count FROM sys.views
    """
    view_count = db.execute_scalar(views_query, database)

    # Count procedures
    procs_query = """
    SELECT COUNT(*) as count FROM sys.procedures WHERE is_ms_shipped = 0
    """
    proc_count = db.execute_scalar(procs_query, database)

    # Count functions
    funcs_query = """
    SELECT COUNT(*) as count FROM sys.objects
    WHERE type IN ('FN', 'IF', 'TF') AND is_ms_shipped = 0
    """
    func_count = db.execute_scalar(funcs_query, database)

    # Get database size
    size_query = """
    SELECT
        CAST(SUM(size) * 8.0 / 1024 AS DECIMAL(10,2)) as size_mb
    FROM sys.database_files
    """
    size_mb = db.execute_scalar(size_query, database)

    # Get schemas
    schemas_query = """
    SELECT s.name, COUNT(o.object_id) as object_count
    FROM sys.schemas s
    LEFT JOIN sys.objects o ON s.schema_id = o.schema_id
    WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA', 'guest')
    GROUP BY s.name
    ORDER BY object_count DESC
    """
    schemas = db.execute_query(schemas_query, database)

    return json.dumps(
        {
            "database": database or db.settings.database,
            "tables": table_count,
            "views": view_count,
            "procedures": proc_count,
            "functions": func_count,
            "size_mb": float(size_mb) if size_mb else 0,
            "schemas": schemas,
        },
        indent=2,
        default=str,
    )
