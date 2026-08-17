#!/bin/bash
cd "$(dirname "$0")"

# SECURITY (2026-08-16): a live Telegram bot token was hard-coded on this line and is
# present in this repository's git history. It MUST be treated as compromised:
#
#   1. Revoke and rotate it now via @BotFather -> /revoke (or /token to reissue).
#   2. Removing it from the working tree, as done here, does NOT remove it from history.
#      Anyone with clone access to any commit before this one can still read it.
#   3. Do not commit the replacement. Provide it through the environment or an
#      untracked local file.
#
# Supply the token by either:
#   export TELEGRAM_BOT_TOKEN=...            # in your shell, or
#   echo 'TELEGRAM_BOT_TOKEN=...' > .env.local   # untracked; see .gitignore
if [[ -z "${TELEGRAM_BOT_TOKEN:-}" && -f ".env.local" ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env.local
    set +a
fi
if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
    echo "[gateway] FATAL: TELEGRAM_BOT_TOKEN is not set." >&2
    echo "[gateway] Export it, or put it in an untracked .env.local. Never commit it." >&2
    exit 1
fi
export TELEGRAM_BOT_TOKEN

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
