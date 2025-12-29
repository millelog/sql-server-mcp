#!/bin/bash
#
# SQL Server MCP - Update Script
#
# This script pulls the latest changes, rebuilds the Docker image,
# and restarts the container with the new image.
#
# Usage:
#   ./update.sh
#
# The script will:
#   1. Pull latest changes from git
#   2. Rebuild the Docker image
#   3. Stop the running container (if any)
#   4. Start a new container with the updated image
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="docker-compose.prod.yml"
CONTAINER_NAME="sql-server-mcp"

echo "========================================"
echo "SQL Server MCP - Update Script"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Create one with your SQL Server credentials:"
    echo ""
    echo "  MSSQL_HOST=your-server"
    echo "  MSSQL_PORT=1433"
    echo "  MSSQL_USER=your-user"
    echo "  MSSQL_PASSWORD='your-password'"
    echo "  MSSQL_DATABASE=master"
    echo ""
    exit 1
fi

# Step 1: Pull latest changes
echo "[1/4] Pulling latest changes from git..."
git fetch --all
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "      Already up to date."
    read -p "      Rebuild anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "      Skipping rebuild."
        exit 0
    fi
else
    echo "      Updates found. Pulling..."
    git pull
fi

# Step 2: Rebuild the Docker image
echo ""
echo "[2/4] Rebuilding Docker image..."
docker-compose -f "$COMPOSE_FILE" build --no-cache

# Step 3: Stop the running container
echo ""
echo "[3/4] Stopping current container (if running)..."
docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true

# Step 4: Start the new container
echo ""
echo "[4/4] Starting updated container..."
docker-compose -f "$COMPOSE_FILE" up -d

echo ""
echo "========================================"
echo "Update complete!"
echo "========================================"
echo ""
echo "Container status:"
docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
echo ""
echo "To view logs:  docker logs -f $CONTAINER_NAME"
echo "To stop:       docker-compose -f $COMPOSE_FILE down"
