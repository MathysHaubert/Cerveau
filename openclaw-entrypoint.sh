#!/bin/sh
# Start OpenClaw in background, patch model once config is written, then foreground
openclaw gateway &
GATEWAY_PID=$!

# Wait for config to be written
sleep 5

python3 -c "
import json
path = '/home/node/.openclaw/openclaw.json'
with open(path) as f:
    d = json.load(f)
d['agents']['defaults']['model']['primary'] = 'openai/claude-haiku-4'
with open(path, 'w') as f:
    json.dump(d, f, indent=2)
" 2>/dev/null || true

wait $GATEWAY_PID
