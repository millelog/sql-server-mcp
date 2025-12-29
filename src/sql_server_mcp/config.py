"""Configuration management for SQL Server MCP."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="MSSQL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Connection settings
    host: str = Field(default="localhost", description="SQL Server hostname")
    port: int = Field(default=1433, description="SQL Server port")
    user: str = Field(default="", description="SQL Server username")
    password: SecretStr = Field(default=SecretStr(""), description="SQL Server password")
    database: str = Field(default="master", description="Default database")
    connection_string: str | None = Field(
        default=None, description="Full connection string (overrides other settings)"
    )

    # Query settings (without MSSQL_ prefix)
    max_rows: int = Field(default=100, description="Maximum rows returned by queries")
    query_timeout: int = Field(default=30, description="Query timeout in seconds")

    # Access control (without MSSQL_ prefix)
    allowed_databases: str = Field(
        default="", description="Comma-separated list of allowed databases"
    )
    blocked_databases: str = Field(
        default="", description="Comma-separated list of blocked databases"
    )

    @property
    def allowed_database_list(self) -> list[str]:
        """Parse allowed databases into a list."""
        if not self.allowed_databases:
            return []
        return [db.strip() for db in self.allowed_databases.split(",") if db.strip()]

    @property
    def blocked_database_list(self) -> list[str]:
        """Parse blocked databases into a list."""
        if not self.blocked_databases:
            return []
        return [db.strip() for db in self.blocked_databases.split(",") if db.strip()]

    def get_connection_string(self) -> str:
        """Build connection string from settings."""
        if self.connection_string:
            return self.connection_string
        # For pymssql, we don't use a connection string format
        # Instead we'll pass individual parameters
        return ""

    def is_database_allowed(self, database: str) -> bool:
        """Check if a database is allowed based on allow/block lists."""
        # If blocked, always deny
        if database in self.blocked_database_list:
            return False
        # If allowlist is set, database must be in it
        if self.allowed_database_list:
            return database in self.allowed_database_list
        # No restrictions
        return True


class QuerySettings(BaseSettings):
    """Query-specific settings (separate prefix)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_rows: int = Field(default=100, alias="MAX_ROWS")
    query_timeout: int = Field(default=30, alias="QUERY_TIMEOUT")
    allowed_databases: str = Field(default="", alias="ALLOWED_DATABASES")
    blocked_databases: str = Field(default="", alias="BLOCKED_DATABASES")


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


def get_query_settings() -> QuerySettings:
    """Get query settings."""
    return QuerySettings()
