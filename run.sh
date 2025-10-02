#!/bin/bash

# Banking Workflow Automation - Quick Start Script

echo "🏦 Banking Workflow Automation Platform"
echo "========================================"
echo ""

# Check Python version
python_version=$(python --version 2>&1)
echo "✓ Python: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Start the server
echo ""
echo "🚀 Starting Banking Workflow Automation API..."
echo ""
echo "   Dashboard: http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   API JSON:  http://localhost:8000/openapi.json"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

cd backend
python app.py
