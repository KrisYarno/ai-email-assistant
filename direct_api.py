"""
This module provides a fallback function to call the OpenAI API directly without the client library
"""
import requests
import json

def direct_openai_call(api_key, messages, model="gpt-4o-mini", temperature=0.7, max_tokens=500):
    """
    Make a direct API call to OpenAI without using the client library
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload)
    )
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
    
    result = response.json()
    return result["choices"][0]["message"]["content"]