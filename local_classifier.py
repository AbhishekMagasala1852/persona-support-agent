"""
local_classifier.py - Simple local classifier that doesn't need API calls
"""
import re

def classify_persona_local(user_message: str) -> dict:
    """
    Classifies the user message into one of three personas using simple rules.
    No API calls needed!
    """
    message_lower = user_message.lower()
    
    # Check for Technical Expert keywords
    tech_keywords = [
        'api', 'code', 'config', 'error', 'log', 'debug', 'server', 'database',
        'syntax', 'function', 'module', 'package', 'dependency', 'crash', 'stack',
        'trace', 'exception', 'timeout', 'connection', 'authentication', 'token',
        'key', 'endpoint', 'request', 'response', 'json', 'xml', 'http', 'url',
        'linux', 'windows', 'mac', 'terminal', 'command', 'script', 'python',
        'java', 'javascript', 'git', 'github', 'deploy', 'production', 'staging'
    ]
    
    # Check for Business Executive keywords
    biz_keywords = [
        'roi', 'revenue', 'cost', 'budget', 'timeline', 'deadline', 'client',
        'customer', 'stakeholder', 'project', 'delivery', 'business', 'impact',
        'strategy', 'priority', 'resource', 'efficiency', 'productivity',
        'market', 'growth', 'quarter', 'annual', 'forecast', 'kpi', 'metric'
    ]
    
    # Check for Frustration keywords
    frustration_keywords = [
        'frustrat', 'angry', 'annoy', 'upset', 'disappoint', 'unacceptable',
        'terrible', 'horrible', 'useless', 'waste', 'never', 'always', 'fix',
        'immediately', 'asap', 'right now', 'urgent', 'now!', 'help!',
        'not working', 'broken', 'failed', 'error', 'issue', 'problem'
    ]
    
    # Count keyword matches
    tech_score = sum(1 for word in tech_keywords if word in message_lower)
    biz_score = sum(1 for word in biz_keywords if word in message_lower)
    frustration_score = sum(1 for word in frustration_keywords if word in message_lower)
    
    # Exclamation marks and uppercase words indicate frustration
    exclamation_count = message_lower.count('!')
    uppercase_count = sum(1 for c in user_message if c.isupper())
    
    # Adjust scores
    if exclamation_count >= 2:
        frustration_score += 2
    if uppercase_count > len(user_message) * 0.3:
        frustration_score += 2
    
    # Check for technical language (presence of code-like things)
    if ':' in user_message and any(c.isdigit() for c in user_message):
        tech_score += 1
    if '#' in user_message or '{' in user_message or '}' in user_message:
        tech_score += 1
    
    # Check for business language (numbers with $, %, etc.)
    if '$' in user_message or '%' in user_message:
        biz_score += 1
    
    # Determine the persona
    max_score = max(tech_score, biz_score, frustration_score)
    
    if max_score == 0:
        # If no keywords matched, default to Frustrated User (most empathetic)
        persona = "Frustrated User"
        confidence = 0.3
        reasoning = "No clear indicators; defaulting to empathetic approach."
    elif frustration_score >= tech_score and frustration_score >= biz_score:
        persona = "Frustrated User"
        confidence = min(0.9, 0.5 + (frustration_score / 10))
        reasoning = f"Message contains frustration indicators (score: {frustration_score})"
    elif tech_score >= biz_score:
        persona = "Technical Expert"
        confidence = min(0.9, 0.5 + (tech_score / 10))
        reasoning = f"Message contains technical keywords (score: {tech_score})"
    else:
        persona = "Business Executive"
        confidence = min(0.9, 0.5 + (biz_score / 10))
        reasoning = f"Message contains business keywords (score: {biz_score})"
    
    return {
        "persona": persona,
        "confidence": round(confidence, 2),
        "reasoning": reasoning
    }