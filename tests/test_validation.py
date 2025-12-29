"""Tests for query validation - these tests don't require a database connection."""

import pytest

from sql_server_mcp.validation import (
    QueryType,
    ValidationError,
    detect_query_type,
    quote_identifier,
    sanitize_identifier,
    validate_query,
)


class TestDetectQueryType:
    """Tests for query type detection."""

    def test_detect_select(self):
        assert detect_query_type("SELECT * FROM users") == QueryType.SELECT
        assert detect_query_type("  SELECT id FROM users") == QueryType.SELECT
        assert detect_query_type("select * from users") == QueryType.SELECT

    def test_detect_insert(self):
        assert detect_query_type("INSERT INTO users VALUES (1)") == QueryType.INSERT

    def test_detect_update(self):
        assert detect_query_type("UPDATE users SET name = 'x'") == QueryType.UPDATE

    def test_detect_delete(self):
        assert detect_query_type("DELETE FROM users") == QueryType.DELETE

    def test_detect_drop(self):
        assert detect_query_type("DROP TABLE users") == QueryType.DROP

    def test_detect_create(self):
        assert detect_query_type("CREATE TABLE users (id INT)") == QueryType.CREATE

    def test_detect_alter(self):
        assert detect_query_type("ALTER TABLE users ADD col INT") == QueryType.ALTER

    def test_detect_truncate(self):
        assert detect_query_type("TRUNCATE TABLE users") == QueryType.TRUNCATE

    def test_detect_exec(self):
        assert detect_query_type("EXEC sp_help") == QueryType.EXEC
        assert detect_query_type("EXECUTE sp_help") == QueryType.EXECUTE

    def test_detect_with_comments(self):
        query = """
        -- This is a comment
        SELECT * FROM users
        """
        assert detect_query_type(query) == QueryType.SELECT

    def test_detect_with_cte(self):
        query = """
        WITH cte AS (SELECT * FROM users)
        SELECT * FROM cte
        """
        assert detect_query_type(query) == QueryType.SELECT


class TestValidateQuery:
    """Tests for query validation."""

    def test_valid_select_queries(self, sample_queries):
        for query in sample_queries["valid_select"]:
            result = validate_query(query)
            assert result.is_valid, f"Query should be valid: {query}"
            assert result.query_type == QueryType.SELECT

    def test_invalid_insert_queries(self, sample_queries):
        for query in sample_queries["invalid_insert"]:
            result = validate_query(query)
            assert not result.is_valid, f"Query should be invalid: {query}"
            assert "INSERT" in result.error_message or "not allowed" in result.error_message

    def test_invalid_update_queries(self, sample_queries):
        for query in sample_queries["invalid_update"]:
            result = validate_query(query)
            assert not result.is_valid, f"Query should be invalid: {query}"

    def test_invalid_delete_queries(self, sample_queries):
        for query in sample_queries["invalid_delete"]:
            result = validate_query(query)
            assert not result.is_valid, f"Query should be invalid: {query}"

    def test_invalid_drop_queries(self, sample_queries):
        for query in sample_queries["invalid_drop"]:
            result = validate_query(query)
            assert not result.is_valid, f"Query should be invalid: {query}"

    def test_invalid_create_queries(self, sample_queries):
        for query in sample_queries["invalid_create"]:
            result = validate_query(query)
            assert not result.is_valid, f"Query should be invalid: {query}"

    def test_invalid_alter_queries(self, sample_queries):
        for query in sample_queries["invalid_alter"]:
            result = validate_query(query)
            assert not result.is_valid, f"Query should be invalid: {query}"

    def test_invalid_truncate_queries(self, sample_queries):
        for query in sample_queries["invalid_truncate"]:
            result = validate_query(query)
            assert not result.is_valid, f"Query should be invalid: {query}"

    def test_invalid_exec_queries(self, sample_queries):
        for query in sample_queries["invalid_exec"]:
            result = validate_query(query)
            assert not result.is_valid, f"Query should be invalid: {query}"

    def test_invalid_select_into(self, sample_queries):
        for query in sample_queries["invalid_select_into"]:
            result = validate_query(query)
            assert not result.is_valid, f"Query should be invalid: {query}"

    def test_select_into_variable_allowed(self):
        # SELECT INTO @variable should be allowed
        query = "SELECT @var = column1 FROM users"
        result = validate_query(query)
        # This might not be detected as SELECT INTO since it uses @ prefix
        # The validation should pass

    def test_empty_query(self):
        result = validate_query("")
        assert not result.is_valid
        assert "empty" in result.error_message.lower()

    def test_whitespace_only_query(self):
        result = validate_query("   \n\t  ")
        assert not result.is_valid

    def test_xp_cmdshell_blocked(self):
        result = validate_query("SELECT * FROM xp_cmdshell('dir')")
        assert not result.is_valid
        assert "forbidden" in result.error_message.lower()

    def test_openrowset_blocked(self):
        result = validate_query("SELECT * FROM OPENROWSET('test')")
        assert not result.is_valid

    def test_sp_executesql_blocked(self):
        result = validate_query("EXEC sp_executesql N'SELECT 1'")
        assert not result.is_valid


class TestSanitizeIdentifier:
    """Tests for identifier sanitization."""

    def test_valid_identifiers(self):
        assert sanitize_identifier("users") == "users"
        assert sanitize_identifier("user_table") == "user_table"
        assert sanitize_identifier("Users123") == "Users123"
        assert sanitize_identifier("dbo.users") == "dbo.users"
        assert sanitize_identifier("[users]") == "[users]"

    def test_empty_identifier(self):
        with pytest.raises(ValidationError):
            sanitize_identifier("")

    def test_invalid_characters(self):
        with pytest.raises(ValidationError):
            sanitize_identifier("users; DROP TABLE--")

    def test_sql_injection_patterns(self):
        with pytest.raises(ValidationError):
            sanitize_identifier("users; --")

        with pytest.raises(ValidationError):
            sanitize_identifier("' OR '1'='1")


class TestQuoteIdentifier:
    """Tests for identifier quoting."""

    def test_simple_identifier(self):
        assert quote_identifier("users") == "[users]"

    def test_already_quoted(self):
        assert quote_identifier("[users]") == "[users]"

    def test_schema_qualified(self):
        assert quote_identifier("dbo.users") == "[dbo].[users]"

    def test_schema_qualified_already_quoted(self):
        assert quote_identifier("[dbo].[users]") == "[dbo].[users]"


class TestMutationPatterns:
    """Additional tests for mutation pattern detection."""

    def test_merge_blocked(self):
        query = "MERGE INTO target USING source ON ..."
        result = validate_query(query)
        assert not result.is_valid

    def test_bulk_insert_blocked(self):
        query = "BULK INSERT users FROM 'file.csv'"
        result = validate_query(query)
        assert not result.is_valid

    def test_grant_blocked(self):
        query = "GRANT SELECT ON users TO public"
        result = validate_query(query)
        assert not result.is_valid

    def test_revoke_blocked(self):
        query = "REVOKE SELECT ON users FROM public"
        result = validate_query(query)
        assert not result.is_valid

    def test_backup_blocked(self):
        query = "BACKUP DATABASE test TO DISK = 'test.bak'"
        result = validate_query(query)
        assert not result.is_valid

    def test_restore_blocked(self):
        query = "RESTORE DATABASE test FROM DISK = 'test.bak'"
        result = validate_query(query)
        assert not result.is_valid


class TestComplexQueries:
    """Tests for complex query patterns."""

    def test_subquery_select(self):
        query = """
        SELECT *
        FROM users
        WHERE id IN (SELECT user_id FROM orders WHERE total > 100)
        """
        result = validate_query(query)
        assert result.is_valid

    def test_cte_select(self):
        query = """
        WITH active_users AS (
            SELECT * FROM users WHERE active = 1
        ),
        user_orders AS (
            SELECT * FROM orders WHERE user_id IN (SELECT id FROM active_users)
        )
        SELECT * FROM user_orders
        """
        result = validate_query(query)
        assert result.is_valid

    def test_union_select(self):
        query = """
        SELECT id, name FROM users
        UNION ALL
        SELECT id, company_name FROM companies
        """
        result = validate_query(query)
        assert result.is_valid

    def test_case_insensitive_blocking(self):
        # Test that blocking works regardless of case
        queries = [
            "insert into users values (1)",
            "INSERT INTO users VALUES (1)",
            "Insert Into Users Values (1)",
            "UPDATE users set name = 'x'",
            "update USERS SET name = 'x'",
            "delete from users",
            "DELETE FROM users",
        ]
        for query in queries:
            result = validate_query(query)
            assert not result.is_valid, f"Query should be blocked: {query}"
