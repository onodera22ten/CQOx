#!/bin/bash
set -e

# Start engine server on port 8081 in background
echo "Starting engine server on port 8081..."
uvicorn backend.engine.server:app --host 0.0.0.0 --port 8081 &
ENGINE_PID=$!

# Wait for engine to be ready (poll health endpoint)
echo "Waiting for engine to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if python3 -c "import httpx; httpx.get('http://localhost:8081/openapi.json', timeout=1.0)" 2>/dev/null; then
        echo "Engine is ready!"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "Waiting for engine... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 1
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "ERROR: Engine failed to start within 30 seconds"
    exit 1
fi

# Start gateway server on port 8080 in foreground
echo "Starting gateway server on port 8080..."
exec uvicorn backend.gateway.app:app --host 0.0.0.0 --port 8080
