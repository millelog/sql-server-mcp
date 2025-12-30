"""Table-related tools for SQL Server MCP."""

import json
from typing import TYPE_CHECKING

from sql_server_mcp.validation import quote_identifier, sanitize_identifier

if TYPE_CHECKING:
    from sql_server_mcp.database import Database


def _parse_table_name(table: str) -> tuple[str | None, str]:
    """Parse schema.table or just table name.

    Args:
        table: Table name, optionally with schema prefix

    Returns:
        Tuple of (schema, table_name)
    """
    parts = table.split(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, parts[0]


async def list_tables(
    db: "Database",
    database: str | None = None,
    schema: str | None = None,
    name_pattern: str | None = None,
) -> str:
    """List all tables in a database.

    Args:
        db: Database connection manager
        database: Database name
        schema: Filter by schema
        name_pattern: Filter by name pattern

    Returns:
        JSON string with table list
    """
    query = """
    SELECT
        s.name AS schema_name,
        t.name AS table_name,
        p.rows AS row_count,
        CAST(SUM(a.total_pages) * 8.0 / 1024 AS DECIMAL(10,2)) AS size_mb,
        t.create_date,
        t.modify_date
    FROM sys.tables t
    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
    INNER JOIN sys.indexes i ON t.object_id = i.object_id
    INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
    INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
    WHERE t.type = 'U'
    """

    if schema:
        sanitize_identifier(schema)
        query += f" AND s.name = '{schema}'"

    if name_pattern:
        query += f" AND t.name LIKE '{name_pattern}'"

    query += """
    GROUP BY s.name, t.name, p.rows, t.create_date, t.modify_date
    ORDER BY s.name, t.name
    """

    results = db.execute_query(query, database)

    return json.dumps(
        {
            "tables": results,
            "count": len(results),
        },
        indent=2,
        default=str,
    )


async def get_table_definition(
    db: "Database",
    table: str,
    database: str | None = None,
) -> str:
    """Get the full CREATE TABLE definition.

    Args:
        db: Database connection manager
        table: Table name (can include schema)
        database: Database name

    Returns:
        CREATE TABLE statement
    """
    schema, table_name = _parse_table_name(table)
    sanitize_identifier(table_name)
    if schema:
        sanitize_identifier(schema)

    # Get columns
    columns_query = f"""
    SELECT
        c.name AS column_name,
        t.name AS data_type,
        c.max_length,
        c.precision,
        c.scale,
        c.is_nullable,
        c.is_identity,
        ic.seed_value,
        ic.increment_value,
        dc.definition AS default_value,
        cc.definition AS computed_definition
    FROM sys.columns c
    INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
    INNER JOIN sys.tables tbl ON c.object_id = tbl.object_id
    INNER JOIN sys.schemas s ON tbl.schema_id = s.schema_id
    LEFT JOIN sys.identity_columns ic ON c.object_id = ic.object_id AND c.column_id = ic.column_id
    LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
    LEFT JOIN sys.computed_columns cc ON c.object_id = cc.object_id AND c.column_id = cc.column_id
    WHERE tbl.name = '{table_name}'
    {"AND s.name = '" + schema + "'" if schema else ""}
    ORDER BY c.column_id
    """

    columns = db.execute_query(columns_query, database)

    # Get primary key
    pk_query = f"""
    SELECT
        i.name AS constraint_name,
        c.name AS column_name
    FROM sys.indexes i
    INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
    INNER JOIN sys.tables t ON i.object_id = t.object_id
    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE i.is_primary_key = 1
    AND t.name = '{table_name}'
    {"AND s.name = '" + schema + "'" if schema else ""}
    ORDER BY ic.key_ordinal
    """

    pk_columns = db.execute_query(pk_query, database)

    # Build CREATE TABLE statement
    full_name = f"{quote_identifier(schema)}.{quote_identifier(table_name)}" if schema else quote_identifier(table_name)
    ddl = f"CREATE TABLE {full_name} (\n"

    col_defs = []
    for col in columns:
        col_def = f"    {quote_identifier(col['column_name'])} "

        if col["computed_definition"]:
            col_def += f"AS {col['computed_definition']}"
        else:
            # Data type with length/precision
            dtype = col["data_type"]
            if dtype in ("varchar", "nvarchar", "char", "nchar", "binary", "varbinary"):
                length = "MAX" if col["max_length"] == -1 else str(col["max_length"])
                if dtype.startswith("n"):
                    length = "MAX" if col["max_length"] == -1 else str(col["max_length"] // 2)
                col_def += f"{dtype}({length})"
            elif dtype in ("decimal", "numeric"):
                col_def += f"{dtype}({col['precision']},{col['scale']})"
            elif dtype in ("float", "real") and col["precision"]:
                col_def += f"{dtype}({col['precision']})"
            else:
                col_def += dtype

            # Identity
            if col["is_identity"]:
                seed = col["seed_value"] or 1
                incr = col["increment_value"] or 1
                col_def += f" IDENTITY({seed},{incr})"

            # Nullable
            col_def += " NULL" if col["is_nullable"] else " NOT NULL"

            # Default
            if col["default_value"]:
                col_def += f" DEFAULT {col['default_value']}"

        col_defs.append(col_def)

    # Add primary key constraint
    if pk_columns:
        pk_name = pk_columns[0]["constraint_name"]
        pk_cols = ", ".join(quote_identifier(c["column_name"]) for c in pk_columns)
        col_defs.append(f"    CONSTRAINT {quote_identifier(pk_name)} PRIMARY KEY ({pk_cols})")

    ddl += ",\n".join(col_defs)
    ddl += "\n);"

    return ddl


async def get_table_columns(
    db: "Database",
    table: str,
    database: str | None = None,
) -> str:
    """Get detailed column information for a table.

    Args:
        db: Database connection manager
        table: Table name
        database: Database name

    Returns:
        JSON string with column details
    """
    schema, table_name = _parse_table_name(table)
    sanitize_identifier(table_name)
    if schema:
        sanitize_identifier(schema)

    query = f"""
    SELECT
        c.name AS column_name,
        t.name AS data_type,
        c.max_length,
        c.precision,
        c.scale,
        c.is_nullable,
        c.is_identity,
        c.is_computed,
        dc.definition AS default_value,
        cc.definition AS computed_definition,
        ep.value AS description
    FROM sys.columns c
    INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
    INNER JOIN sys.tables tbl ON c.object_id = tbl.object_id
    INNER JOIN sys.schemas s ON tbl.schema_id = s.schema_id
    LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
    LEFT JOIN sys.computed_columns cc ON c.object_id = cc.object_id AND c.column_id = cc.column_id
    LEFT JOIN sys.extended_properties ep ON ep.major_id = c.object_id AND ep.minor_id = c.column_id AND ep.name = 'MS_Description'
    WHERE tbl.name = '{table_name}'
    {"AND s.name = '" + schema + "'" if schema else ""}
    ORDER BY c.column_id
    """

    results = db.execute_query(query, database)

    return json.dumps(
        {
            "table": table,
            "columns": results,
            "count": len(results),
        },
        indent=2,
        default=str,
    )


async def get_table_indexes(
    db: "Database",
    table: str,
    database: str | None = None,
) -> str:
    """Get index information for a table.

    Args:
        db: Database connection manager
        table: Table name
        database: Database name

    Returns:
        JSON string with index details
    """
    schema, table_name = _parse_table_name(table)
    sanitize_identifier(table_name)
    if schema:
        sanitize_identifier(schema)

    # Query indexes with column details - we'll aggregate in Python for compatibility
    query = f"""
    SELECT
        i.name AS index_name,
        i.type_desc AS index_type,
        i.is_unique,
        i.is_primary_key,
        c.name AS column_name,
        ic.key_ordinal,
        ic.is_included_column,
        ic.is_descending_key
    FROM sys.indexes i
    INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
    INNER JOIN sys.tables t ON i.object_id = t.object_id
    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE t.name = '{table_name}'
    {"AND s.name = '" + schema + "'" if schema else ""}
    AND i.name IS NOT NULL
    ORDER BY i.is_primary_key DESC, i.name, ic.key_ordinal
    """

    raw_results = db.execute_query(query, database)

    # Aggregate columns by index in Python
    indexes = {}
    for row in raw_results:
        idx_name = row["index_name"]
        if idx_name not in indexes:
            indexes[idx_name] = {
                "index_name": idx_name,
                "index_type": row["index_type"],
                "is_unique": row["is_unique"],
                "is_primary_key": row["is_primary_key"],
                "columns": [],
                "included_columns": [],
            }
        if row["is_included_column"]:
            indexes[idx_name]["included_columns"].append(row["column_name"])
        else:
            indexes[idx_name]["columns"].append(row["column_name"])

    # Convert columns lists to comma-separated strings
    results = []
    for idx in indexes.values():
        idx["columns"] = ", ".join(idx["columns"])
        idx["included_columns"] = ", ".join(idx["included_columns"]) if idx["included_columns"] else None
        results.append(idx)

    return json.dumps(
        {
            "table": table,
            "indexes": results,
            "count": len(results),
        },
        indent=2,
        default=str,
    )


async def get_table_relationships(
    db: "Database",
    table: str,
    database: str | None = None,
) -> str:
    """Get foreign key relationships for a table.

    Args:
        db: Database connection manager
        table: Table name
        database: Database name

    Returns:
        JSON string with relationship details
    """
    schema, table_name = _parse_table_name(table)
    sanitize_identifier(table_name)
    if schema:
        sanitize_identifier(schema)

    # Outgoing foreign keys (this table references others)
    outgoing_query = f"""
    SELECT
        fk.name AS constraint_name,
        ps.name AS parent_schema,
        pt.name AS parent_table,
        pc.name AS parent_column,
        rs.name AS referenced_schema,
        rt.name AS referenced_table,
        rc.name AS referenced_column,
        fk.delete_referential_action_desc AS on_delete,
        fk.update_referential_action_desc AS on_update
    FROM sys.foreign_keys fk
    INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
    INNER JOIN sys.tables pt ON fk.parent_object_id = pt.object_id
    INNER JOIN sys.schemas ps ON pt.schema_id = ps.schema_id
    INNER JOIN sys.columns pc ON fkc.parent_object_id = pc.object_id AND fkc.parent_column_id = pc.column_id
    INNER JOIN sys.tables rt ON fk.referenced_object_id = rt.object_id
    INNER JOIN sys.schemas rs ON rt.schema_id = rs.schema_id
    INNER JOIN sys.columns rc ON fkc.referenced_object_id = rc.object_id AND fkc.referenced_column_id = rc.column_id
    WHERE pt.name = '{table_name}'
    {"AND ps.name = '" + schema + "'" if schema else ""}
    ORDER BY fk.name, fkc.constraint_column_id
    """

    outgoing = db.execute_query(outgoing_query, database)

    # Incoming foreign keys (other tables reference this one)
    incoming_query = f"""
    SELECT
        fk.name AS constraint_name,
        ps.name AS referencing_schema,
        pt.name AS referencing_table,
        pc.name AS referencing_column,
        rs.name AS referenced_schema,
        rt.name AS referenced_table,
        rc.name AS referenced_column,
        fk.delete_referential_action_desc AS on_delete,
        fk.update_referential_action_desc AS on_update
    FROM sys.foreign_keys fk
    INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
    INNER JOIN sys.tables pt ON fk.parent_object_id = pt.object_id
    INNER JOIN sys.schemas ps ON pt.schema_id = ps.schema_id
    INNER JOIN sys.columns pc ON fkc.parent_object_id = pc.object_id AND fkc.parent_column_id = pc.column_id
    INNER JOIN sys.tables rt ON fk.referenced_object_id = rt.object_id
    INNER JOIN sys.schemas rs ON rt.schema_id = rs.schema_id
    INNER JOIN sys.columns rc ON fkc.referenced_object_id = rc.object_id AND fkc.referenced_column_id = rc.column_id
    WHERE rt.name = '{table_name}'
    {"AND rs.name = '" + schema + "'" if schema else ""}
    ORDER BY fk.name, fkc.constraint_column_id
    """

    incoming = db.execute_query(incoming_query, database)

    return json.dumps(
        {
            "table": table,
            "outgoing_relationships": outgoing,
            "incoming_relationships": incoming,
        },
        indent=2,
        default=str,
    )
