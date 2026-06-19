"""
classifier.py - Uses Gemini API, but falls back to local classifier if quota hit

This file's only job is: look at a customer's message, and decide which
"persona" (personality type) the message sounds like it came from.
"""

import json
from google import genai
from google.genai import types
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
    
    # Set up the connection to Google's Gemini AI
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    system_instruction = (
        "You are an advanced classification engine. Your task is to analyze the "
        "sentiment, vocabulary, and tone of an incoming support message and classify "
        "it into exactly one of three customer personas:\n"
        "1. 'Technical Expert': Uses jargon, asks about APIs/code/configs.\n"
        "2. 'Frustrated User': Uses emotional language, exclamation marks, or mentions urgency.\n"
        "3. 'Business Executive': Focuses on business impact, ROI, timelines, and brevity.\n\n"
        "Provide your evaluation strictly in the requested JSON structure."
    )

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "persona": {
                "type": "STRING",
                "enum": config.VALID_PERSONAS
            },
            "confidence": {"type": "NUMBER"},
            "reasoning": {"type": "STRING"}
        },
        "required": ["persona", "confidence", "reasoning"]
    }

    try:
        response = client.models.generate_content(
            model=config.GENERATION_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1
            )
        )
        result = json.loads(response.text)

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