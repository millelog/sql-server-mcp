# SQL Server MCP - Agent Guide

This document provides guidance for AI coding agents working on this project.

## Project Overview

This is a Python-based MCP (Model Context Protocol) server that provides read-only access to SQL Server databases. It allows Claude Code and other MCP clients to:
- List databases, tables, views, stored procedures, and functions
- Get object definitions (DDL/source code)
- Execute read-only queries with sample data
- Search for objects across databases

**CRITICAL: This MCP is READ-ONLY. No mutations are allowed.**

## Getting Started (Every Session)

1. **Get your bearings:**
   ```bash
   pwd
   git log --oneline -10
   ```

2. **Read the progress file:**
   ```bash
   cat claude-progress.txt
   ```

3. **Check feature status:**
   ```bash
   cat feature_list.json | python -c "import sys,json; d=json.load(sys.stdin); print(f'Passing: {sum(1 for f in d[\"features\"] if f[\"passes\"])}/{len(d[\"features\"])}')"
   ```

4. **Run the init script to start the dev environment:**
   ```bash
   ./init.sh
   ```

5. **Run basic tests to verify nothing is broken:**
   ```bash
   pytest tests/ -v --tb=short
   ```

## Project Structure

```
sql-server-mcp/
├── src/
│   └── sql_server_mcp/
│       ├── __init__.py
│       ├── server.py          # Main MCP server implementation
│       ├── database.py        # Database connection and query execution
│       ├── tools/             # MCP tool implementations
│       │   ├── __init__.py
│       │   ├── databases.py   # list_databases tool
│       │   ├── tables.py      # Table-related tools
│       │   ├── views.py       # View-related tools
│       │   ├── procedures.py  # Stored procedure tools
│       │   ├── queries.py     # Query execution tools
│       │   └── search.py      # Search tools
│       ├── validation.py      # Query validation (mutation blocking)
│       └── config.py          # Configuration management
├── tests/
│   ├── __init__.py
│   ├── test_validation.py     # Unit tests for query validation
│   ├── test_tools.py          # Tool tests
│   └── conftest.py            # Pytest fixtures
├── .vscode/
│   └── launch.json            # VS Code debug configurations
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── init.sh                    # Development environment setup
├── feature_list.json          # Feature tracking (DO NOT DELETE FEATURES)
├── claude-progress.txt        # Progress log
└── claude.md                  # This file
```

## Key Technologies

- **Python 3.11+**: Main language
- **mcp**: Model Context Protocol SDK (`pip install mcp`)
- **pyodbc** or **pymssql**: SQL Server connectivity
- **pytest**: Testing framework
- **Docker**: Containerization

## Development Workflow

### Working on a Feature

1. Choose the highest-priority failing feature from `feature_list.json`
2. Implement the feature incrementally
3. Write/update tests
4. Test manually using the MCP inspector or test client
5. Update `feature_list.json` - set `"passes": true` only after verification
6. Commit with descriptive message
7. Update `claude-progress.txt`

### Commit Guidelines

- Make small, focused commits
- Use descriptive commit messages explaining WHY not just WHAT
- Always run tests before committing
- Format: `[category] Brief description`
  - `[core] Add MCP server initialization`
  - `[tools] Implement list_databases tool`
  - `[security] Add mutation query blocking`
  - `[docker] Add Dockerfile and compose config`

### Feature List Rules

**IMPORTANT: It is unacceptable to remove or edit feature descriptions in `feature_list.json`.**

You may ONLY:
- Change `"passes": false` to `"passes": true` after verifying a feature works
- Add NEW features if requirements expand (append to array)

### Testing Strategy

1. **Unit Tests**: Test validation logic, parsing, etc. without DB connection
2. **Integration Tests**: Test against real SQL Server (use Docker container)
3. **Manual Testing**: Use MCP inspector to verify tool behavior

Run tests:
```bash
# Unit tests only (no DB required)
pytest tests/test_validation.py -v

# All tests (requires SQL Server)
pytest tests/ -v

# With coverage
pytest tests/ --cov=src/sql_server_mcp --cov-report=term-missing
```

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MSSQL_HOST` | SQL Server hostname | `localhost` |
| `MSSQL_PORT` | SQL Server port | `1433` |
| `MSSQL_USER` | Username | - |
| `MSSQL_PASSWORD` | Password | - |
| `MSSQL_DATABASE` | Default database | `master` |
| `MSSQL_CONNECTION_STRING` | Full connection string (overrides above) | - |
| `MAX_ROWS` | Maximum rows returned by queries | `100` |
| `QUERY_TIMEOUT` | Query timeout in seconds | `30` |
| `ALLOWED_DATABASES` | Comma-separated allowlist | - |
| `BLOCKED_DATABASES` | Comma-separated blocklist | - |

## Security Requirements

This MCP MUST be read-only. Implement these safeguards:

1. **Query Validation**: Block INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, EXEC (for mutation procs)
2. **Parameterized Queries**: Never concatenate user input into SQL
3. **Connection Settings**: Use `ApplicationIntent=ReadOnly` where supported
4. **Credential Protection**: Never log or return passwords in errors

## MCP Tool Reference

### Database Tools
- `list_databases`: List all accessible databases
- `get_database_info`: Get database metadata

### Table Tools
- `list_tables`: List tables in a database
- `get_table_definition`: Get CREATE TABLE DDL
- `get_table_columns`: Get column metadata
- `get_table_indexes`: Get index information
- `get_table_relationships`: Get foreign key relationships

### View Tools
- `list_views`: List views in a database
- `get_view_definition`: Get CREATE VIEW DDL

### Procedure Tools
- `list_procedures`: List stored procedures
- `get_procedure_definition`: Get CREATE PROCEDURE DDL
- `get_procedure_parameters`: Get parameter metadata

### Function Tools
- `list_functions`: List user-defined functions
- `get_function_definition`: Get CREATE FUNCTION DDL

### Query Tools
- `execute_query`: Run read-only SELECT query
- `get_sample_data`: Get sample rows from a table

### Search Tools
- `search_objects`: Search for objects by name
- `search_definitions`: Search within object definitions

## Common Issues

### pyodbc vs pymssql
- `pyodbc` requires ODBC driver installed (more complex but more features)
- `pymssql` is pure Python (easier to install, fewer features)
- Recommend `pymssql` for Docker simplicity

### Testing Without SQL Server
- Unit tests should mock database connections
- Use `pytest-mock` for mocking
- Integration tests use Docker SQL Server

### Docker SQL Server for Testing
```bash
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourStrong@Passw0rd" \
  -p 1433:1433 --name sqlserver-test \
  mcr.microsoft.com/mssql/mssql-server:2022-latest
```

## Progress Tracking

After each work session:

1. Update `claude-progress.txt` with:
   - Date/time
   - What was accomplished
   - Current state of the code
   - What should be worked on next
   - Any known issues or blockers

2. Commit your changes with a descriptive message

3. Run `git status` to verify clean state

## Quick Reference

```bash
# Start development
./init.sh

# Run tests
pytest tests/ -v

# Check feature progress
python -c "import json; f=json.load(open('feature_list.json')); p=[x for x in f['features'] if x['passes']]; print(f'{len(p)}/{len(f[\"features\"])} features passing')"

# Test MCP server manually
python -m src.sql_server_mcp.server

# Build Docker image
docker build -t sql-server-mcp .

# Run Docker container
docker run --rm -it \
  -e MSSQL_HOST=host.docker.internal \
  -e MSSQL_USER=sa \
  -e MSSQL_PASSWORD=yourpassword \
  sql-server-mcp
```
