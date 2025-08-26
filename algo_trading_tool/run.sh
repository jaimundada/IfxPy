#!/bin/bash

# Algorithmic Trading Tool - Startup Script

echo "=========================================="
echo "  Algorithmic Trading Tool"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found"
    echo "Creating .env from template..."
    cp .env.example .env
    echo "Please edit .env file with your API keys and configuration"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# Check if Redis is running (optional)
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        echo "✓ Redis is running"
    else
        echo "! Redis is not running (optional - will use in-memory cache)"
    fi
else
    echo "! Redis not installed (optional - will use in-memory cache)"
fi

# Start the application
echo "Starting Algorithmic Trading Tool..."
echo "Dashboard will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the application"
echo "=========================================="

python app.py