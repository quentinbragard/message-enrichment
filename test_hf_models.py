# test_hf_models.py - Test which models work
import requests
import json

HF_TOKEN = "hf_YOUR_TOKEN_HERE"  # Replace with your token

models_to_test = [
    "mistralai/Mistral-7B-Instruct-v0.2",
    "meta-llama/Llama-2-7b-chat-hf",  # Requires access grant
    "HuggingFaceH4/zephyr-7b-beta",
    "tiiuae/falcon-7b-instruct",
    "google/flan-t5-xxl",
    "bigscience/bloom",
]

def test_model(model_id):
    """Test if a model is available"""
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    payload = {
        "inputs": "What is 2+2?",
        "parameters": {
            "max_new_tokens": 50,
            "temperature": 0.1
        }
    }
    
    print(f"\nTesting {model_id}...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print(f"✅ {model_id} WORKS!")
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"❌ {model_id} failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False

# Test all models
for model in models_to_test:
    test_model(model)
