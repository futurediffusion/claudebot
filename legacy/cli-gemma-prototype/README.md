# Ollama Agent - CLI Mode

## Quick Test

```bash
# Load system prompt into variable
SYSTEM_PROMPT=$(cat agent/system_prompt.txt)

# Test with simple command
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma\",
    \"prompt\": \"create folder called myproject\",
    \"system\": \"$SYSTEM_PROMPT\",
    \"stream\": false
  }"
```

## If still giving assistant responses

Try the /api/chat endpoint instead:

```bash
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma",
    "messages": [
      {"role": "system", "content": "'"$(cat agent/system_prompt.txt)"'"},
      {"role": "user", "content": "create folder called test"}
    ]
  }'
```

## Direct test of run_shell.py

```bash
python run_shell.py "mkdir -p test1 test2"
```