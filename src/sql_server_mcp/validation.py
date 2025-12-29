"""Query validation for SQL Server MCP.

This module provides security validation to ensure only read-only queries
are executed. It blocks all mutation operations (INSERT, UPDATE, DELETE, etc.)
and potentially dangerous commands.
"""

import re
from dataclasses import dataclass
from enum import Enum


class ValidationError(Exception):
    """Raised when query validation fails."""

    pass


class QueryType(Enum):
    """Types of SQL queries."""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"
    TRUNCATE = "TRUNCATE"
    EXEC = "EXEC"
    EXECUTE = "EXECUTE"
    MERGE = "MERGE"
    GRANT = "GRANT"
    REVOKE = "REVOKE"
    DENY = "DENY"
    BACKUP = "BACKUP"
    RESTORE = "RESTORE"
    BULK = "BULK"
    UNKNOWN = "UNKNOWN"


# Queries that are allowed (read-only)
ALLOWED_QUERY_TYPES = {QueryType.SELECT}

# Patterns that indicate mutation operations
MUTATION_PATTERNS = [
    r"\bINSERT\s+INTO\b",
    r"\bINSERT\s+\w+\s*\(",  # INSERT table (cols)
    r"\bUPDATE\s+\w+\s+SET\b",
    r"\bDELETE\s+FROM\b",
    r"\bDELETE\s+\w+\s+WHERE\b",  # DELETE table WHERE
    r"\bDROP\s+(TABLE|DATABASE|VIEW|PROCEDURE|FUNCTION|INDEX|TRIGGER|SCHEMA)\b",
    r"\bCREATE\s+(TABLE|DATABASE|VIEW|PROCEDURE|FUNCTION|INDEX|TRIGGER|SCHEMA)\b",
    r"\bALTER\s+(TABLE|DATABASE|VIEW|PROCEDURE|FUNCTION|INDEX|TRIGGER|SCHEMA)\b",
    r"\bTRUNCATE\s+TABLE\b",
    r"\bMERGE\s+INTO\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bDENY\b",
    r"\bBACKUP\s+DATABASE\b",
    r"\bRESTORE\s+DATABASE\b",
    r"\bBULK\s+INSERT\b",
    r"\bEXEC\s*\(",  # EXEC with dynamic SQL
    r"\bEXECUTE\s*\(",  # EXECUTE with dynamic SQL
    r"\bsp_executesql\b",
    r"\bOPENROWSET\b",
    r"\bOPENQUERY\b",
    r"\bxp_cmdshell\b",
    r"\bxp_\w+\b",  # Extended stored procedures
]

# Compile patterns for performance
COMPILED_MUTATION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in MUTATION_PATTERNS
]


@dataclass
class ValidationResult:
    """Result of query validation."""

    is_valid: bool
    query_type: QueryType
    error_message: str | None = None


def detect_query_type(query: str) -> QueryType:
    """Detect the type of SQL query.

    Args:
        query: The SQL query string

    Returns:
        The detected QueryType
    """
    # Normalize whitespace and get first keyword
    normalized = query.strip().upper()

    # Remove comments
    normalized = re.sub(r"--.*$", "", normalized, flags=re.MULTILINE)
    normalized = re.sub(r"/\*.*?\*/", "", normalized, flags=re.DOTALL)
    normalized = normalized.strip()

    # Check for WITH CTE (which could be SELECT or mutation)
    if normalized.startswith("WITH"):
        # Check what follows the CTE
        # Find the main query after CTE definitions
        cte_end = normalized.rfind(")")
        if cte_end != -1:
            after_cte = normalized[cte_end + 1 :].strip()
            for qt in QueryType:
                if qt != QueryType.UNKNOWN and after_cte.startswith(qt.value):
                    return qt

    # Check each query type
    for qt in QueryType:
        if qt != QueryType.UNKNOWN and normalized.startswith(qt.value):
            return qt

    return QueryType.UNKNOWN


def validate_query(query: str) -> ValidationResult:
    """Validate a SQL query for read-only execution.

    Args:
        query: The SQL query to validate

    Returns:
        ValidationResult indicating if the query is safe to execute

    Raises:
        ValidationError: If the query contains mutation operations
    """
    if not query or not query.strip():
        return ValidationResult(
            is_valid=False, query_type=QueryType.UNKNOWN, error_message="Query cannot be empty"
        )

    query_type = detect_query_type(query)

    # Check if query type is allowed
    if query_type not in ALLOWED_QUERY_TYPES:
        if query_type != QueryType.UNKNOWN:
            return ValidationResult(
                is_valid=False,
                query_type=query_type,
                error_message=f"{query_type.value} queries are not allowed. Only SELECT queries are permitted.",
            )

    # Even for SELECT queries, check for mutation patterns
    # (e.g., SELECT INTO, subqueries with mutations)
    for pattern in COMPILED_MUTATION_PATTERNS:
        if pattern.search(query):
            match = pattern.search(query)
            matched_text = match.group(0) if match else "unknown"
            return ValidationResult(
                is_valid=False,
                query_type=query_type,
                error_message=f"Query contains forbidden pattern: {matched_text}. Only read-only operations are allowed.",
            )

    # Check for SELECT INTO (creates a table)
    if re.search(r"\bSELECT\b.*\bINTO\s+\w+", query, re.IGNORECASE | re.DOTALL):
        # But allow INTO @variable (local variable)
        if not re.search(r"\bSELECT\b.*\bINTO\s+@", query, re.IGNORECASE | re.DOTALL):
            return ValidationResult(
                is_valid=False,
                query_type=query_type,
                error_message="SELECT INTO (table creation) is not allowed. Only read-only operations are permitted.",
            )

    return ValidationResult(is_valid=True, query_type=query_type)


def sanitize_identifier(identifier: str) -> str:
    """Sanitize a SQL identifier (table name, column name, etc.).

    This prevents SQL injection by ensuring identifiers contain only valid characters.

    Args:
        identifier: The identifier to sanitize

    Returns:
        The sanitized identifier

    Raises:
        ValidationError: If the identifier contains invalid characters
    """
    if not identifier:
        raise ValidationError("Identifier cannot be empty")

    # Allow alphanumeric, underscores, and brackets for quoted identifiers
    # Also allow dots for schema.table notation
    if not re.match(r"^[\w\.\[\]]+$", identifier):
        raise ValidationError(
            f"Invalid identifier: {identifier}. "
            "Identifiers can only contain letters, numbers, underscores, dots, and brackets."
        )

    # Check for common SQL injection patterns
    dangerous_patterns = [
        r";\s*--",
        r";\s*/\*",
        r"'\s*OR\s*'",
        r"'\s*AND\s*'",
        r"UNION\s+SELECT",
        r";\s*DROP",
        r";\s*DELETE",
        r";\s*INSERT",
        r";\s*UPDATE",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, identifier, re.IGNORECASE):
            raise ValidationError(f"Potentially dangerous pattern detected in identifier: {identifier}")

    return identifier


def quote_identifier(identifier: str) -> str:
    """Quote a SQL identifier using bracket notation.

    Args:
        identifier: The identifier to quote

    Returns:
        The quoted identifier (e.g., [table_name])
    """
    # Remove existing brackets if present
    identifier = identifier.strip("[]")

    # Handle schema.table notation
    parts = identifier.split(".")
    quoted_parts = [f"[{part}]" for part in parts]

    return ".".join(quoted_parts)
