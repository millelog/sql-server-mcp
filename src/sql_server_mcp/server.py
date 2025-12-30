"""MCP Server implementation for SQL Server introspection."""

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

from sql_server_mcp.config import get_settings
from sql_server_mcp.database import Database, DatabaseError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server instance
server = Server("sql-server-mcp")

# Initialize database connection
settings = get_settings()
db = Database(settings)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools.

    Returns:
        List of Tool definitions
    """
    return [
        Tool(
            name="list_databases",
            description="List all accessible databases on the SQL Server",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_system": {
                        "type": "boolean",
                        "description": "Include system databases (master, model, msdb, tempdb)",
                        "default": False,
                    },
                    "name_pattern": {
                        "type": "string",
                        "description": "Filter databases by name pattern (SQL LIKE syntax)",
                    },
                },
            },
        ),
        Tool(
            name="list_tables",
            description="List all tables in a database",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name (uses default if not specified)",
                    },
                    "schema": {
                        "type": "string",
                        "description": "Filter by schema name",
                    },
                    "name_pattern": {
                        "type": "string",
                        "description": "Filter tables by name pattern (SQL LIKE syntax)",
                    },
                },
            },
        ),
        Tool(
            name="get_table_definition",
            description="Get the full CREATE TABLE definition for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                    "table": {
                        "type": "string",
                        "description": "Table name (can include schema, e.g., 'dbo.Users')",
                    },
                },
                "required": ["table"],
            },
        ),
        Tool(
            name="get_table_columns",
            description="Get detailed column information for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                    "table": {
                        "type": "string",
                        "description": "Table name (can include schema)",
                    },
                },
                "required": ["table"],
            },
        ),
        Tool(
            name="get_table_indexes",
            description="Get index information for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                    "table": {
                        "type": "string",
                        "description": "Table name (can include schema)",
                    },
                },
                "required": ["table"],
            },
        ),
        Tool(
            name="get_table_relationships",
            description="Get foreign key relationships for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                    "table": {
                        "type": "string",
                        "description": "Table name (can include schema)",
                    },
                },
                "required": ["table"],
            },
        ),
        Tool(
            name="list_views",
            description="List all views in a database",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                    "schema": {
                        "type": "string",
                        "description": "Filter by schema name",
                    },
                    "name_pattern": {
                        "type": "string",
                        "description": "Filter views by name pattern",
                    },
                },
            },
        ),
        Tool(
            name="get_view_definition",
            description="Get the CREATE VIEW definition",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                    "view": {
                        "type": "string",
                        "description": "View name (can include schema)",
                    },
                },
                "required": ["view"],
            },
        ),
        Tool(
            name="get_view_columns",
            description="Get column information for a view",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                    "view": {
                        "type": "string",
                        "description": "View name (can include schema)",
                    },
                },
                "required": ["view"],
            },
        ),
        Tool(
            name="list_procedures",
            description="List all stored procedures in a database",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                    "schema": {
                        "type": "string",
                        "description": "Filter by schema name",
                    },
                    "name_pattern": {
                        "type": "string",
                        "description": "Filter procedures by name pattern",
                    },
                    "include_system": {
                        "type": "boolean",
                        "description": "Include system procedures",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="get_procedure_definition",
            description="Get the CREATE PROCEDURE definition",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                    "procedure": {
                        "type": "string",
                        "description": "Procedure name (can include schema)",
                    },
                },
                "required": ["procedure"],
            },
        ),
        Tool(
            name="get_procedure_parameters",
            description="Get parameter information for a stored procedure",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                    "procedure": {
                        "type": "string",
                        "description": "Procedure name (can include schema)",
                    },
                },
                "required": ["procedure"],
            },
        ),
        Tool(
            name="list_functions",
            description="List all user-defined functions in a database",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                    "schema": {
                        "type": "string",
                        "description": "Filter by schema name",
                    },
                    "function_type": {
                        "type": "string",
                        "description": "Filter by function type: 'scalar', 'table', or 'all'",
                        "default": "all",
                    },
                },
            },
        ),
        Tool(
            name="get_function_definition",
            description="Get the CREATE FUNCTION definition",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                    "function": {
                        "type": "string",
                        "description": "Function name (can include schema)",
                    },
                },
                "required": ["function"],
            },
        ),
        Tool(
            name="execute_query",
            description="Execute a read-only SELECT query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SELECT query to execute",
                    },
                    "database": {
                        "type": "string",
                        "description": "Database to query",
                    },
                    "max_rows": {
                        "type": "integer",
                        "description": "Maximum rows to return (default: 100)",
                        "default": 100,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_sample_data",
            description="Get sample rows from a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                    "table": {
                        "type": "string",
                        "description": "Table name (can include schema)",
                    },
                    "rows": {
                        "type": "integer",
                        "description": "Number of rows to return (default: 10)",
                        "default": 10,
                    },
                    "random": {
                        "type": "boolean",
                        "description": "Return random sample instead of first N rows",
                        "default": False,
                    },
                },
                "required": ["table"],
            },
        ),
        Tool(
            name="search_objects",
            description="Search for database objects by name across all databases",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Name pattern to search for (SQL LIKE syntax)",
                    },
                    "object_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Object types to search: 'table', 'view', 'procedure', 'function'",
                    },
                    "database": {
                        "type": "string",
                        "description": "Limit search to specific database",
                    },
                },
                "required": ["pattern"],
            },
        ),
        Tool(
            name="search_definitions",
            description="Search within object definitions (procedure/function/view source code)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Text pattern to search for",
                    },
                    "database": {
                        "type": "string",
                        "description": "Limit search to specific database",
                    },
                    "object_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Object types to search: 'view', 'procedure', 'function'",
                    },
                },
                "required": ["pattern"],
            },
        ),
        Tool(
            name="list_schemas",
            description="List all schemas in a database with object counts",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                },
            },
        ),
        Tool(
            name="get_schema_overview",
            description="Get an overview of a database schema (counts of objects, size info)",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls.

    Args:
        name: Name of the tool to call
        arguments: Tool arguments

    Returns:
        List of TextContent with results
    """
    try:
        # Import tool implementations
        from sql_server_mcp.tools import (
            databases,
            functions,
            procedures,
            queries,
            search,
            tables,
            views,
        )

        # Route to appropriate handler
        handlers = {
            "list_databases": databases.list_databases,
            "list_tables": tables.list_tables,
            "get_table_definition": tables.get_table_definition,
            "get_table_columns": tables.get_table_columns,
            "get_table_indexes": tables.get_table_indexes,
            "get_table_relationships": tables.get_table_relationships,
            "list_views": views.list_views,
            "get_view_definition": views.get_view_definition,
            "get_view_columns": views.get_view_columns,
            "list_procedures": procedures.list_procedures,
            "get_procedure_definition": procedures.get_procedure_definition,
            "get_procedure_parameters": procedures.get_procedure_parameters,
            "list_functions": functions.list_functions,
            "get_function_definition": functions.get_function_definition,
            "execute_query": queries.execute_query,
            "get_sample_data": queries.get_sample_data,
            "search_objects": search.search_objects,
            "search_definitions": search.search_definitions,
            "list_schemas": databases.list_schemas,
            "get_schema_overview": databases.get_schema_overview,
        }

        if name not in handlers:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        result = await handlers[name](db, **arguments)
        return [TextContent(type="text", text=result)]

    except DatabaseError as e:
        logger.error(f"Database error in {name}: {e}")
        return [TextContent(type="text", text=f"Database error: {e}")]
    except Exception as e:
        logger.exception(f"Error in tool {name}")
        return [TextContent(type="text", text=f"Error: {e}")]


async def run_server() -> None:
    """Run the MCP server."""
    logger.info("Starting SQL Server MCP server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    """Entry point for the MCP server."""
    asyncio.run(run_server())


def health_check() -> None:
    """Health check for Docker.

    Raises:
        SystemExit: If health check fails
    """
    from sql_server_mcp.database import test_connection

    if not test_connection():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
