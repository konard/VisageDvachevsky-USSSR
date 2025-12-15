#!/bin/bash

# USSR Leaders Platform - Startup Script

echo "Starting USSR Leaders Platform..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r backend/requirements.txt

# Check if videos directory exists
if [ ! -d "videos" ]; then
    echo "Warning: videos directory not found. Please add video files (1.mp4 - 7.mp4) to the videos directory."
fi

# Run the application
echo "Starting Flask application..."
python backend/app.py
