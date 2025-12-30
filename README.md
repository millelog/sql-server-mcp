# SQL Server MCP

A read-only MCP (Model Context Protocol) server for SQL Server database introspection. Use with Claude Desktop to let Claude explore and query your SQL Server databases.

## Features

- List databases, tables, views, stored procedures, and functions
- Get object definitions (DDL/source code)
- Execute read-only SELECT queries
- Search for objects across databases
- **Read-only by design** - all mutation queries are blocked

## Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/sql-server-mcp.git
cd sql-server-mcp

# Install in a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Claude Desktop Configuration

Add to your Claude Desktop config file:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sql-server": {
      "command": "python",
      "args": ["-m", "sql_server_mcp"],
      "cwd": "C:\\path\\to\\sql-server-mcp",
      "env": {
        "MSSQL_HOST": "your-server",
        "MSSQL_USER": "your-username",
        "MSSQL_PASSWORD": "your-password",
        "MSSQL_DATABASE": "master"
      }
    }
  }
}
```

Restart Claude Desktop after updating the config.

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `MSSQL_HOST` | SQL Server hostname | `localhost` |
| `MSSQL_PORT` | SQL Server port | `1433` |
| `MSSQL_USER` | Username | - |
| `MSSQL_PASSWORD` | Password | - |
| `MSSQL_DATABASE` | Default database | `master` |
| `MSSQL_CONNECTION_STRING` | Full connection string (overrides above) | - |
| `MAX_ROWS` | Maximum rows returned | `100` |
| `QUERY_TIMEOUT` | Query timeout (seconds) | `30` |
| `ALLOWED_DATABASES` | Comma-separated allowlist | - |
| `BLOCKED_DATABASES` | Comma-separated blocklist | - |

## Available Tools

| Tool | Description |
|------|-------------|
| `list_databases` | List all accessible databases |
| `list_tables` | List tables in a database |
| `get_table_definition` | Get CREATE TABLE DDL |
| `get_table_columns` | Get column metadata |
| `get_table_indexes` | Get index information |
| `get_table_relationships` | Get foreign key relationships |
| `list_views` | List views in a database |
| `get_view_definition` | Get CREATE VIEW DDL |
| `list_procedures` | List stored procedures |
| `get_procedure_definition` | Get CREATE PROCEDURE DDL |
| `get_procedure_parameters` | Get procedure parameters |
| `list_functions` | List user-defined functions |
| `get_function_definition` | Get CREATE FUNCTION DDL |
| `execute_query` | Run read-only SELECT queries |
| `get_sample_data` | Get sample rows from a table |
| `search_objects` | Search for objects by name |
| `search_definitions` | Search within object definitions |
| `get_schema_overview` | Get database schema summary (object counts, size) |

## Development

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/sql_server_mcp
```

## License

MIT
