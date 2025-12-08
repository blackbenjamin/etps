#!/bin/bash
# ETPS Development Server Restart Script
# Kills existing processes, clears caches, and restarts both servers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== ETPS Dev Server Restart ==="

# Kill existing processes
echo "Stopping existing servers..."
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
sleep 1

# Clear Next.js and node caches
echo "Clearing caches..."
rm -rf "$PROJECT_ROOT/frontend/.next"
rm -rf "$PROJECT_ROOT/frontend/node_modules/.cache"

# Start backend
echo "Starting backend on http://localhost:8000..."
cd "$PROJECT_ROOT/backend"
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend on http://localhost:3000..."
cd "$PROJECT_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

# Wait for services to be ready
echo "Waiting for services..."
sleep 3

# Health check
if curl -s -o /dev/null -w "" http://localhost:8000/health --max-time 5; then
    echo "✓ Backend healthy"
else
    echo "✗ Backend not responding"
fi

if curl -s -o /dev/null -w "" http://localhost:3000 --max-time 10; then
    echo "✓ Frontend healthy"
else
    echo "✗ Frontend not responding"
fi

echo ""
echo "=== Servers Running ==="
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for interrupt
wait
