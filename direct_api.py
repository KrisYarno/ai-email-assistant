"""
This module provides a function to call the OpenAI API directly without the client library.
It handles various model-specific parameter naming and constraints.
"""
import requests
import json

def direct_openai_call(api_key, messages, model="gpt-4.1", temperature=0.7, max_tokens=1000, max_completion_tokens=None, reasoning_effort="medium"):
    """
    Make a direct API call to OpenAI without using the client library.
    
    Args:
        api_key (str): Your OpenAI API key
        messages (list): The messages to send to the API
        model (str): The model to use (default: gpt-4.1)
        temperature (float): Controls randomness in responses (default: 0.7)
        max_tokens (int): Maximum tokens in the response (default: 1000)
        max_completion_tokens (int): Alternative parameter for reasoning models
        reasoning_effort (str): Only for reasoning models - "low", "medium", or "high"
    
    Returns:
        str: The model's response text
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Start building the payload with common parameters
    payload = {
        "model": model,
        "messages": messages,
    }
    
    # Define model-specific settings
    model_settings = {
        # Format: model_name: (uses_reasoning_params, supports_temperature)
        "gpt-4o-mini": (False, True),
        "gpt-4o": (False, True),
        "gpt-4.1-mini": (False, True),
        "gpt-4.1": (False, True),
        "o4-mini": (True, False),  # Uses reasoning parameters, no temperature
        "o3": (True, False),       # Uses reasoning parameters, no temperature
        "o3-mini": (True, False)   # Uses reasoning parameters, no temperature
    }
    
    # Get settings for this model (default to standard parameters if model not in settings)
    uses_reasoning_params, supports_temperature = model_settings.get(
        model, (False, True)
    )
    
    # Add the appropriate tokens parameter based on model type
    if uses_reasoning_params:
        # For reasoning models (o-series), use max_completion_tokens
        payload["max_completion_tokens"] = max_completion_tokens or max_tokens
        # Add reasoning effort parameter
        payload["reasoning_effort"] = reasoning_effort
    else:
        # For standard chat models, use max_tokens
        payload["max_tokens"] = max_tokens
    
    # Add temperature parameter if supported by the model
    if supports_temperature:
        payload["temperature"] = temperature
    
    # Print the API request (for debugging)
    print(f"Sending API request to model: {model}")
    print(f"Payload parameters: {', '.join(payload.keys())}")
    
    # Make the API request
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )
        
        # Handle error responses
        if response.status_code != 200:
            try:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
            except json.JSONDecodeError:
                error_message = response.text or "Unknown error (no JSON response)"
            
            raise Exception(f"API request failed with status code {response.status_code}: {error_message}")
        
        # Parse and return the response
        result = response.json()
        print(f"Response received. Content length: {len(result['choices'][0]['message']['content'])}")
        return result["choices"][0]["message"]["content"]
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error when calling OpenAI API: {str(e)}")
    except json.JSONDecodeError:
        raise Exception(f"Invalid JSON response from OpenAI API: {response.text}")
    except Exception as e:
        raise Exception(f"Error calling OpenAI API: {str(e)}")