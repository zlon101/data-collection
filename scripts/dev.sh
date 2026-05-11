#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cleanup() {
  echo -e "\n🛑 Stopping services..."
  kill "$BACKEND_PID" 2>/dev/null || true
  kill "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" 2>/dev/null || true
  wait "$FRONTEND_PID" 2>/dev/null || true
  echo "✅ All services stopped."
  exit 0
}

trap cleanup SIGINT SIGTERM EXIT

echo "🚀 Starting Data Collection Platform..."

# Start backend
cd "$PROJECT_ROOT"
uv run uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "📡 Backend (PID: $BACKEND_PID) → http://localhost:8000"
echo "📡 API Docs → http://localhost:8000/docs"

# Wait for backend to be ready
sleep 2

# Start frontend
cd "$PROJECT_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!
echo "🎨 Frontend (PID: $FRONTEND_PID) → http://localhost:5173"

echo ""
echo "✅ Both services started. Press Ctrl+C to stop all."
echo ""

# Wait for either process to exit
wait
