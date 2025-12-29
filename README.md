# SQL Server MCP

A read-only Model Context Protocol (MCP) server for SQL Server database introspection. This MCP allows AI assistants like Claude to explore SQL Server databases, retrieve schema information, and execute read-only queries.

## Features

- **Database Exploration**: List databases, tables, views, stored procedures, and functions
- **Schema Introspection**: Get DDL definitions for tables, views, procedures, and functions
- **Read-Only Queries**: Execute SELECT queries with automatic mutation blocking
- **Sample Data**: Retrieve sample rows from tables
- **Cross-Database Search**: Search for objects by name across all databases
- **Security**: Built-in protection against SQL injection and mutation operations

## Installation

### Using pip

```bash
pip install sql-server-mcp
```

### From source

```bash
git clone https://github.com/yourusername/sql-server-mcp.git
cd sql-server-mcp
pip install -e ".[dev]"
```

### Using Docker

```bash
docker build -t sql-server-mcp .
docker run --rm -it \
  -e MSSQL_HOST=your-server \
  -e MSSQL_USER=your-user \
  -e MSSQL_PASSWORD=your-password \
  sql-server-mcp
```

## Configuration

Configure the server using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MSSQL_HOST` | SQL Server hostname | `localhost` |
| `MSSQL_PORT` | SQL Server port | `1433` |
| `MSSQL_USER` | Username | (required) |
| `MSSQL_PASSWORD` | Password | (required) |
| `MSSQL_DATABASE` | Default database | `master` |
| `MAX_ROWS` | Maximum rows returned | `100` |
| `QUERY_TIMEOUT` | Query timeout (seconds) | `30` |
| `ALLOWED_DATABASES` | Comma-separated allowlist | (all) |
| `BLOCKED_DATABASES` | Comma-separated blocklist | (none) |

## Usage

### With Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sql-server": {
      "command": "python",
      "args": ["-m", "sql_server_mcp"],
      "env": {
        "MSSQL_HOST": "your-server",
        "MSSQL_USER": "your-user",
        "MSSQL_PASSWORD": "your-password"
      }
    }
  }
}
```

### With Claude Code

```bash
# Set environment variables
export MSSQL_HOST=your-server
export MSSQL_USER=your-user
export MSSQL_PASSWORD=your-password

# Run the server
python -m sql_server_mcp
```

## Available Tools

### Database Tools
- `list_databases` - List all accessible databases
- `get_schema_overview` - Get database overview (table/view/procedure counts)

### Table Tools
- `list_tables` - List tables in a database
- `get_table_definition` - Get CREATE TABLE DDL
- `get_table_columns` - Get column metadata
- `get_table_indexes` - Get index information
- `get_table_relationships` - Get foreign key relationships

### View Tools
- `list_views` - List views in a database
- `get_view_definition` - Get CREATE VIEW DDL

### Stored Procedure Tools
- `list_procedures` - List stored procedures
- `get_procedure_definition` - Get CREATE PROCEDURE DDL
- `get_procedure_parameters` - Get parameter metadata

### Function Tools
- `list_functions` - List user-defined functions
- `get_function_definition` - Get CREATE FUNCTION DDL

### Query Tools
- `execute_query` - Execute read-only SELECT queries
- `get_sample_data` - Get sample rows from a table

### Search Tools
- `search_objects` - Search for objects by name
- `search_definitions` - Search within object definitions

## Security

This MCP is designed to be **read-only**. It includes multiple layers of protection:

1. **Query Validation**: All queries are validated before execution. INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, and other mutation operations are blocked.

2. **Parameterized Queries**: User inputs are properly sanitized to prevent SQL injection.

3. **Connection Security**: Credentials are never exposed in error messages or responses.

4. **Row Limits**: Query results are limited to prevent excessive data transfer.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/sql-server-mcp.git
cd sql-server-mcp

# Run the setup script
./init.sh
```

### Running Tests

```bash
# Unit tests (no database required)
pytest tests/test_validation.py -v

# All tests (requires SQL Server)
pytest tests/ -v

# With coverage
pytest tests/ --cov=src/sql_server_mcp --cov-report=term-missing
```

### Docker Compose Development

```bash
# Start SQL Server for testing
docker-compose up -d sqlserver

# Run the MCP server
docker-compose up mcp

# Run tests
docker-compose run --rm test
```

## Contributing

Contributions are welcome! Please read the development guidelines in `claude.md` before submitting pull requests.

## License

MIT License - see LICENSE file for details.
