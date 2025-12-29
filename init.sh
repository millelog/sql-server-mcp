#!/bin/bash
# SQL Server MCP - Development Environment Setup
# Run this script at the start of each development session

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== SQL Server MCP Development Setup ==="
echo ""

# Check Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python not found. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev]" -q

echo ""
echo "=== Environment Ready ==="
echo ""

# Show feature progress
echo "Feature Progress:"
python -c "
import json
with open('feature_list.json') as f:
    data = json.load(f)
    features = data['features']
    passing = sum(1 for f in features if f['passes'])
    p1 = sum(1 for f in features if f['priority'] == 1)
    p1_pass = sum(1 for f in features if f['priority'] == 1 and f['passes'])
    print(f'  Total: {passing}/{len(features)} passing')
    print(f'  Priority 1 (Critical): {p1_pass}/{p1} passing')
" 2>/dev/null || echo "  (feature_list.json not parseable)"

echo ""
echo "=== Quick Commands ==="
echo "  Run tests:        pytest tests/ -v"
echo "  Run MCP server:   python -m sql_server_mcp"
echo "  Check features:   cat feature_list.json | python -m json.tool"
echo ""

# Check if SQL Server is accessible (optional)
if [ -n "$MSSQL_HOST" ]; then
    echo "Checking SQL Server connection..."
    python -c "
from sql_server_mcp.database import test_connection
if test_connection():
    print('  SQL Server: Connected')
else:
    print('  SQL Server: Connection failed')
" 2>/dev/null || echo "  SQL Server: Not configured or module not ready"
else
    echo "Note: MSSQL_HOST not set. Set environment variables to test DB connection."
fi

echo ""
echo "Ready for development!"
