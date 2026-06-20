"""
generator.py - Fixed version with standard Google Gemini API
"""
import os
import google.generativeai as genai

import config
from escalator import generate_handoff_summary


# ---------------------------------------------------------------------
# PERSONA -> WRITING STYLE INSTRUCTIONS
# ---------------------------------------------------------------------
PERSONA_INSTRUCTIONS = {
    "Technical Expert": (
        "You are a Senior Systems Engineer. Provide clear root-cause analysis, "
        "configuration specifications, and precise API pathways or code blocks. "
        "Keep technical descriptions exact and structured."
    ),
    "Frustrated User": (
        "You are a deeply empathetic, reassuring Customer Care Specialist. "
        "Begin with a warm, genuine validation of their difficulty. Use straightforward, "
        "reassuring, and simple action-oriented bullet steps. Avoid confusing jargon."
    ),
    "Business Executive": (
        "You are a concise Client Relations Director. Focus on direct business outcomes, "
        "impact summaries, and timelines for resolution. Keep responses extremely "
        "brief, professional, and skip unnecessary configuration details."
    )
}


def generate_adaptive_response(user_query: str, persona: str, context_chunks: list) -> dict:
    """
    Produces the final reply. If API fails, uses template-based responses.
    """
    
    best_score = max([chunk["score"] for chunk in context_chunks]) if context_chunks else 0.0
    
    if best_score < config.CONFIDENCE_THRESHOLD or len(context_chunks) == 0:
        return {
            "escalated": True,
            "response": (
                "I apologize, but I am unable to locate the precise solution to your "
                "request in our knowledge base. I am connecting you with a live human "
                "support specialist who can assist further."
            ),
            "handoff_summary": generate_handoff_summary(user_query, persona, context_chunks)
        }
    
    # If we have good context, try to use Gemini
    persona_instructions = PERSONA_INSTRUCTIONS.get(
        persona, PERSONA_INSTRUCTIONS["Frustrated User"]
    )
    
    context_text = "\n\n".join(
        [f"Source [{c['source']}]: {c['text']}" for c in context_chunks]
    )
    
    full_system_prompt = (
        f"{persona_instructions}\n\n"
        "CRITICAL RULES:\n"
        "- Base your response ONLY on the provided context.\n"
        "- Do not hallucinate or assume facts not found in the documents.\n"
        "- If the context does not fully answer the question, say so honestly "
        "rather than inventing details.\n\n"
        f"FACTUAL CONTEXT DOCUMENTS:\n{context_text}"
    )
    
    # Configure the Gemini API
    genai.configure(api_key=config.GEMINI_API_KEY)
    
    # Use the model
    model = genai.GenerativeModel(
        model_name=config.GENERATION_MODEL,
        generation_config={
            "temperature": 0.2,
        },
        system_instruction=full_system_prompt
    )
    
    try:
        response = model.generate_content(user_query)
        
        return {
            "escalated": False,
            "response": response.text,
            "handoff_summary": None
        }
    
    except Exception as error:
        # If Gemini fails, use a simple template response
        print(f"[generator.py] Gemini API failed: {error}")
        print("[generator.py] Using template response...")
        
        # Pick a response based on persona
        template_responses = {
            "Technical Expert": (
                "Based on the documentation, here's what I found:\n\n"
                f"{context_chunks[0]['text'][:500]}\n\n"
                "For more details, please refer to the source documentation."
            ),
            "Business Executive": (
                "Here's a brief summary from our documentation:\n\n"
                f"{context_chunks[0]['text'][:300]}\n\n"
                "For complete information, please review the full documentation."
            ),
            "Frustrated User": (
                "I understand you're having trouble. Let me help you with what I found:\n\n"
                f"{context_chunks[0]['text'][:500]}\n\n"
                "I hope this helps! Let me know if you need more assistance."
            )
        }
        
        response_text = template_responses.get(persona, template_responses["Frustrated User"])
        
        return {
            "escalated": False,
            "response": response_text,
            "handoff_summary": None
        }
