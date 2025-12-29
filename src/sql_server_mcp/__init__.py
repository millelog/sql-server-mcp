"""SQL Server MCP - A read-only MCP server for SQL Server database introspection."""

__version__ = "0.1.0"

from sql_server_mcp.server import main

__all__ = ["main", "__version__"]
