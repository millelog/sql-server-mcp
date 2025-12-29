#!/bin/bash
#
# SQL Server MCP - Initial Setup Script
#
# Run this once on a new server to set up the MCP container.
#
# Usage:
#   ./setup.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "SQL Server MCP - Initial Setup"
echo "========================================"
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed."
    echo "Install Docker first: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check for docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: docker-compose is not installed."
    echo "Install docker-compose first."
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'ENVEOF'
# SQL Server MCP Configuration
# Update these values for your SQL Server

MSSQL_HOST=localhost
MSSQL_PORT=1433
MSSQL_USER=your-username
MSSQL_PASSWORD='your-password'
MSSQL_DATABASE=master

# Query Settings
MAX_ROWS=100
QUERY_TIMEOUT=30

# Access Control (optional, comma-separated)
ALLOWED_DATABASES=
BLOCKED_DATABASES=
ENVEOF
    echo ""
    echo "IMPORTANT: Edit .env with your SQL Server credentials:"
    echo "  nano .env"
    echo ""
    echo "Then run ./update.sh to build and start the container."
else
    echo ".env file already exists."
    echo ""
    echo "Running update.sh to build and start..."
    ./update.sh
fi
