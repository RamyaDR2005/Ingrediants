#!/bin/bash

# SafeScan Startup Script
# This script starts both the backend API and Streamlit frontend

echo "🔬 SafeScan - Ingredient Scanner"
echo "================================"

# Start backend in background
echo "Starting backend API..."
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Give backend time to start
sleep 2

# Start Streamlit
echo "Starting Streamlit frontend..."
streamlit run main_app.py --server.port=8501 --server.address=0.0.0.0

# Cleanup
kill $BACKEND_PID 2>/dev/null
