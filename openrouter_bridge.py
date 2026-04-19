import os, json, requests

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_model(model, messages):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "reasoning": {"enabled": True}}
    resp = requests.post(BASE_URL, headers=headers, json=payload)
    resp.raise_for_status()
    result = resp.json()["choices"][0]["message"]
    return result.get("content", ""), result.get("reasoning_details", {})

if __name__ == "__main__":
    import sys
    input_data = json.load(sys.stdin)
    content, reasoning = call_model(input_data["model"], input_data["messages"])
    print(json.dumps({"content": content, "reasoning_details": reasoning}))