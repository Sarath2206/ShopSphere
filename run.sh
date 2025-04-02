#!/bin/bash

# AI-Powered Clothing Comparator Runner Script

echo "Starting AI-Powered Clothing Comparator..."

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "Error: pip is not installed or not in PATH"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed or not in PATH"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed or not in PATH"
    exit 1
fi

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
python -m pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend/my-app
npm install
cd ../..

# Start Django server in the background
echo "Starting Django backend server..."
cd backend
python manage.py runserver &
DJANGO_PID=$!
cd ..

echo "Django server started with PID: $DJANGO_PID"
echo "API available at: http://localhost:8000/api/"

# Start the frontend development server
echo "Starting frontend development server..."
cd frontend/my-app
npm run dev &
FRONTEND_PID=$!
cd ../..

echo "Frontend server started with PID: $FRONTEND_PID"
echo "Frontend available at: http://localhost:5173/"

echo "AI-Powered Clothing Comparator is now running!"
echo "Open http://localhost:5173/ in your browser to use the application."
echo ""
echo "Press Ctrl+C to stop the servers."

# Wait for user to press Ctrl+C
trap "echo 'Stopping servers...'; kill $DJANGO_PID $FRONTEND_PID; echo 'Servers stopped.'; exit 0" INT
wait
