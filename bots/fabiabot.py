# bots/fabiabot.py

import requests

def get_fabia_answer(prompt: str) -> str:
    """
    Call your custom endpoint / model for FabiaBot here.
    Adjust the endpoint URL and any required payload, headers, or auth.
    """
    # Replace this with your actual endpoint URL
    FABIA_BOT_ENDPOINT = "https://api.fabiabot.com/complete"
    
    # Prepare the JSON payload that your bot expects
    payload = {
        "prompt": prompt
    }
    
    try:
        response = requests.post(FABIA_BOT_ENDPOINT, json=payload)
        # Raise an HTTPError if the response was an error status
        response.raise_for_status()
        
        # Parse the response JSON to get the bot's answer
        data = response.json()
        # Adjust "answer" to match the actual key in your bot's JSON response
        answer = data.get("answer", "No answer received from FabiaBot.")
        
        return answer
    
    except requests.exceptions.RequestException as e:
        # Catch any request errors (connection, timeout, etc.)
        return f"Error communicating with FabiaBot: {e}"
