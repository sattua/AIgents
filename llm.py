import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2:7b"


def call_llm(messages, numPredict=200, temperature=0.3) -> str:
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "num_predict": numPredict,
        "temperature": temperature
    }

    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code != 200:
        raise Exception(f"Ollama error: {response.text}")

    data = response.json()

    return data["message"]["content"]

def call_ops_llm(payload: dict) -> str:
    payload["model"] = MODEL

    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code != 200:
        raise Exception(f"Ollama error: {response.text}")

    data = response.json()
    return data["message"]["content"].strip()
    
