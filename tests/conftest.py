"""Pytest configuration and fixtures for SQL Server MCP tests."""

import pytest


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    from sql_server_mcp.config import Settings

    return Settings(
        host="localhost",
        port=1433,
        user="test_user",
        password="test_password",  # type: ignore
        database="test_db",
    )


@pytest.fixture
def sample_queries():
    """Sample queries for validation testing."""
    return {
        "valid_select": [
            "SELECT * FROM users",
            "SELECT id, name FROM customers WHERE active = 1",
            "SELECT COUNT(*) FROM orders",
            "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id",
            "WITH cte AS (SELECT * FROM users) SELECT * FROM cte",
            "SELECT TOP 10 * FROM products ORDER BY price DESC",
            "SELECT * FROM users WHERE name LIKE '%test%'",
        ],
        "invalid_insert": [
            "INSERT INTO users (name) VALUES ('test')",
            "INSERT users (name) VALUES ('test')",
        ],
        "invalid_update": [
            "UPDATE users SET name = 'test' WHERE id = 1",
            "UPDATE users SET active = 0",
        ],
        "invalid_delete": [
            "DELETE FROM users WHERE id = 1",
            "DELETE users WHERE id = 1",
        ],
        "invalid_drop": [
            "DROP TABLE users",
            "DROP DATABASE test",
            "DROP VIEW user_view",
            "DROP PROCEDURE sp_test",
        ],
        "invalid_create": [
            "CREATE TABLE test (id INT)",
            "CREATE DATABASE test",
            "CREATE VIEW test AS SELECT 1",
            "CREATE PROCEDURE sp_test AS SELECT 1",
        ],
        "invalid_alter": [
            "ALTER TABLE users ADD column1 INT",
            "ALTER DATABASE test SET RECOVERY SIMPLE",
        ],
        "invalid_truncate": [
            "TRUNCATE TABLE users",
        ],
        "invalid_exec": [
            "EXEC sp_executesql N'DELETE FROM users'",
            "EXECUTE sp_executesql N'DROP TABLE users'",
        ],
        "invalid_select_into": [
            "SELECT * INTO new_table FROM users",
            "SELECT id, name INTO backup FROM users",
        ],
    }
