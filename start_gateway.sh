#!/bin/bash
cd "$(dirname "$0")"

export TELEGRAM_BOT_TOKEN=8798579139:AAFDqCGdlmlJjOSMjn2mOGE7DIWgV1S3OKA

# Start Ollama if not already running
ollama serve &>/dev/null &
sleep 2

git pull origin agents

start_gateway() {
    pkill -f telegram_gateway.py 2>/dev/null
    sleep 1
    python agents/telegram_gateway.py &
    GATEWAY_PID=$!
    echo "[gateway] started pid=$GATEWAY_PID"
}

# Auto-updater — checks for new commits every 30s, restarts if changed
auto_update() {
    while true; do
        sleep 30
        git fetch origin agents --quiet
        LOCAL=$(git rev-parse HEAD)
        REMOTE=$(git rev-parse origin/agents)
        if [ "$LOCAL" != "$REMOTE" ]; then
            echo "[gateway] new commit detected, pulling and restarting..."
            git pull origin agents
            start_gateway
        fi
    done
}

start_gateway
auto_update &

echo "[gateway] running. auto-update active every 30s."
wait $GATEWAY_PID
