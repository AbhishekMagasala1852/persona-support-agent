"""
classifier.py - Uses Gemini API, but falls back to local classifier if quota hit

This file's only job is: look at a customer's message, and decide which
"persona" (personality type) the message sounds like it came from.
"""

import json
import os
import google.generativeai as genai
import config
from local_classifier import classify_persona_local


def classify_customer_persona(user_message: str) -> dict:
    """
    Looks at the customer's message and returns a dictionary like:
        {
            "persona": "Technical Expert",
            "confidence": 0.92,
            "reasoning": "The user mentions API keys and error codes."
        }
    """

    # Configure the Gemini API
    genai.configure(api_key=config.GEMINI_API_KEY)
    
    # Use the model
    model = genai.GenerativeModel(
        model_name=config.GENERATION_MODEL,
        generation_config={
            "temperature": 0.1,
            "response_mime_type": "application/json",
        },
        system_instruction=(
            "You are an advanced classification engine. Your task is to analyze the "
            "sentiment, vocabulary, and tone of an incoming support message and classify "
            "it into exactly one of three customer personas:\n"
            "1. 'Technical Expert': Uses jargon, asks about APIs/code/configs.\n"
            "2. 'Frustrated User': Uses emotional language, exclamation marks, or mentions urgency.\n"
            "3. 'Business Executive': Focuses on business impact, ROI, timelines, and brevity.\n\n"
            "Provide your evaluation strictly in this JSON format:\n"
            '{"persona": "Technical Expert", "confidence": 0.92, "reasoning": "The user mentions API keys and error codes."}'
        )
    )

    try:
        response = model.generate_content(user_query)
        
        # Parse the JSON response
        result = json.loads(response.text)
        
        # Validate the persona
        if result.get("persona") not in config.VALID_PERSONAS:
            result["persona"] = "Frustrated User"
        
        return result

    except Exception as error:
        print(f"[classifier.py] Gemini API failed: {error}")
        print("[classifier.py] Falling back to local classifier...")
        return classify_persona_local(user_message)


# Test block
if __name__ == "__main__":
    test_msg = "Our production API key stopped working with a 401 Unauthorized error."
    result = classify_customer_persona(test_msg)
    print(json.dumps(result, indent=2))
