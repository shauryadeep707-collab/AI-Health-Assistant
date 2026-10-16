#!/bin/bash
echo "========================================="
echo "  AI Health Assistant - Starting..."
echo "========================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Please install Python 3.10+ from https://python.org"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Copy .env.example to .env if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your settings, or run: python scripts/setup_wizard.py"
fi

# Start the application
echo
echo "Starting AI Health Assistant..."
echo "Open http://localhost:5000 in your browser"
echo
python run.py
