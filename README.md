# SQL Server MCP

A read-only MCP (Model Context Protocol) server for SQL Server database introspection.

## Features

- List databases, tables, views, stored procedures, and functions
- Get object definitions (DDL/source code)
- Execute read-only SELECT queries
- Search for objects across databases
- **Read-only by design** - all mutation queries are blocked

## Installation

```bash
pip install sql-server-mcp
```

## Configuration

Set environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MSSQL_HOST` | SQL Server hostname | `localhost` |
| `MSSQL_PORT` | SQL Server port | `1433` |
| `MSSQL_USER` | Username | - |
| `MSSQL_PASSWORD` | Password | - |
| `MSSQL_DATABASE` | Default database | `master` |
| `MAX_ROWS` | Maximum rows returned | `100` |
| `QUERY_TIMEOUT` | Query timeout (seconds) | `30` |

## Usage with Claude Desktop

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "sql-server": {
      "command": "sql-server-mcp",
      "env": {
        "MSSQL_HOST": "your-server",
        "MSSQL_USER": "your-user",
        "MSSQL_PASSWORD": "your-password"
      }
    }
  }
}
```

## Docker

```bash
docker build -t sql-server-mcp .
docker run --rm -it \
  -e MSSQL_HOST=your-server \
  -e MSSQL_USER=your-user \
  -e MSSQL_PASSWORD=your-password \
  sql-server-mcp
```

## Available Tools

- `list_databases` - List all accessible databases
- `list_tables` - List tables in a database
- `get_table_definition` - Get CREATE TABLE DDL
- `list_views` - List views in a database
- `get_view_definition` - Get CREATE VIEW DDL
- `list_procedures` - List stored procedures
- `get_procedure_definition` - Get CREATE PROCEDURE DDL
- `execute_query` - Run read-only SELECT queries
- `search_objects` - Search for objects by name

## License

MIT
