#!/bin/bash

# Stop both backend and frontend when this script is stopped
trap 'kill 0' EXIT

echo "Starting backend..."

cd backend

source .venv/bin/activate

uvicorn app.main:app --reload --port 8000 &

cd ../frontend

echo "Starting frontend..."

npm run dev &

wait