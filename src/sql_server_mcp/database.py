"""Database connection and query execution for SQL Server MCP."""

import logging
from contextlib import contextmanager
from typing import Any, Generator

import pymssql

from sql_server_mcp.config import Settings, get_settings
from sql_server_mcp.validation import ValidationError, validate_query

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Raised when a database operation fails."""

    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


class QueryError(DatabaseError):
    """Raised when query execution fails."""

    pass


class Database:
    """Database connection manager for SQL Server."""

    def __init__(self, settings: Settings | None = None):
        """Initialize database connection manager.

        Args:
            settings: Application settings. If None, loads from environment.
        """
        self.settings = settings or get_settings()
        self._connection: pymssql.Connection | None = None

    @contextmanager
    def get_connection(
        self, database: str | None = None
    ) -> Generator[pymssql.Connection, None, None]:
        """Get a database connection.

        Args:
            database: Optional database name to connect to.
                     Uses default from settings if not specified.

        Yields:
            A database connection

        Raises:
            ConnectionError: If connection fails
        """
        db_name = database or self.settings.database

        # Check if database is allowed
        if not self.settings.is_database_allowed(db_name):
            raise ConnectionError(f"Access to database '{db_name}' is not allowed")

        try:
            conn = pymssql.connect(
                server=self.settings.host,
                port=self.settings.port,
                user=self.settings.user,
                password=self.settings.password.get_secret_value(),
                database=db_name,
                timeout=self.settings.query_timeout,
                login_timeout=10,
                as_dict=True,
            )
            try:
                yield conn
            finally:
                conn.close()
        except pymssql.Error as e:
            # Sanitize error message to avoid exposing credentials
            error_msg = str(e)
            if self.settings.password.get_secret_value() in error_msg:
                error_msg = error_msg.replace(
                    self.settings.password.get_secret_value(), "****"
                )
            raise ConnectionError(f"Failed to connect to database: {error_msg}") from e

    def execute_query(
        self,
        query: str,
        database: str | None = None,
        params: tuple[Any, ...] | None = None,
        max_rows: int | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a read-only query and return results.

        Args:
            query: The SQL query to execute (must be SELECT only)
            database: Optional database name to query
            params: Optional query parameters for parameterized queries
            max_rows: Maximum number of rows to return

        Returns:
            List of result rows as dictionaries

        Raises:
            ValidationError: If query is not read-only
            QueryError: If query execution fails
        """
        # Validate query is read-only
        validation_result = validate_query(query)
        if not validation_result.is_valid:
            raise ValidationError(validation_result.error_message or "Query validation failed")

        max_rows = max_rows or self.settings.max_rows

        with self.get_connection(database) as conn:
            try:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                results = []
                for i, row in enumerate(cursor):
                    if i >= max_rows:
                        break
                    results.append(dict(row))

                return results

            except pymssql.Error as e:
                raise QueryError(f"Query execution failed: {e}") from e

    def execute_scalar(
        self, query: str, database: str | None = None, params: tuple[Any, ...] | None = None
    ) -> Any:
        """Execute a query and return a single scalar value.

        Args:
            query: The SQL query to execute
            database: Optional database name to query
            params: Optional query parameters

        Returns:
            The first column of the first row, or None

        Raises:
            ValidationError: If query is not read-only
            QueryError: If query execution fails
        """
        results = self.execute_query(query, database, params, max_rows=1)
        if results:
            # Return first value from first row
            first_row = results[0]
            if first_row:
                return next(iter(first_row.values()))
        return None


def test_connection() -> bool:
    """Test if database connection is working.

    Returns:
        True if connection is successful, False otherwise
    """
    try:
        db = Database()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False


def health_check() -> None:
    """Health check for Docker/Kubernetes.

    Raises:
        SystemExit: If health check fails
    """
    if not test_connection():
        raise SystemExit(1)
