#!/bin/bash
cd "$(dirname "$0")"
git pull origin agents
export TELEGRAM_BOT_TOKEN=8798579139:AAFDqCGdlmlJjOSMjn2mOGE7DIWgV1S3OKA
ollama serve &>/dev/null &
sleep 2
python agents/telegram_gateway.py
