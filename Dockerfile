# SQL Server MCP - Docker Image
# Multi-stage build for smaller image size

FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir .

# --- Production stage ---
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies for pymssql
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi8 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source (needed for running as module)
COPY src/ ./src/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Environment variables with defaults
ENV MSSQL_HOST=localhost \
    MSSQL_PORT=1433 \
    MSSQL_DATABASE=master \
    MAX_ROWS=100 \
    QUERY_TIMEOUT=30

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from sql_server_mcp.server import health_check; health_check()" || exit 1

# Run the MCP server
# MCP servers communicate via stdio, so we run directly
ENTRYPOINT ["python", "-m", "sql_server_mcp"]
