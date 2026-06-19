"""
escalator.py

Some situations are too risky, too sensitive, or too uncertain for an AI
to handle alone. This file is the "safety net" that decides:

    "Should a human take over this conversation instead of the AI?"

There are three separate reasons we might escalate to a human:
  1. LOW CONFIDENCE - our document search didn't find a good enough match.
     (This check actually lives in generator.py, since it needs the
     retrieved chunks' scores - but it follows the same threshold defined
     in config.py.)
  2. SENSITIVE TOPICS - the message mentions things like refunds, legal
     threats, or account deletion, which carry real-world risk if handled
     incorrectly.
  3. REPEATED FRUSTRATION - the same customer has been frustrated across
     several messages in a row, suggesting the AI isn't actually helping.

When we DO escalate, this file also builds a clean, structured summary
(a "handoff package") so the human agent picking up the conversation
doesn't have to start from zero - they get the full picture immediately.
"""

import json
import config


def contains_sensitive_topic(user_message: str) -> bool:
    """
    Checks if the customer's message mentions any sensitive keyword (like
    "refund", "lawsuit", "fraud", etc.) that we've decided should ALWAYS
    go to a human, regardless of how confident the AI's document search
    was. This protects against the AI making risky promises about money,
    legal matters, or account security.
    """
    lowered_message = user_message.lower()
    return any(keyword in lowered_message for keyword in config.SENSITIVE_KEYWORDS)


def check_repeated_frustration(conversation_history: list, persona_now: str) -> bool:
    """
    Looks at the last few messages in the conversation. If the customer
    has been classified as "Frustrated User" for several messages IN A ROW
    (including this current one), we escalate - because it suggests the
    AI's answers so far have not actually solved their problem.

    'conversation_history' is expected to be a list of past persona labels,
    e.g. ["Frustrated User", "Frustrated User"], collected as the
    conversation goes on. We check the last 2 PLUS the current one,
    so 3 frustrated messages in a row triggers this rule.
    """
    FRUSTRATION_STREAK_LIMIT = 3

    recent_personas = conversation_history[-(FRUSTRATION_STREAK_LIMIT - 1):]
    recent_personas = recent_personas + [persona_now]

    if len(recent_personas) < FRUSTRATION_STREAK_LIMIT:
        return False

    return all(p == "Frustrated User" for p in recent_personas)


def should_escalate(user_message: str, persona: str, best_retrieval_score: float,
                     conversation_history: list = None) -> tuple:
    """
    The main decision function. Checks all escalation rules in order and
    returns a tuple: (should_escalate: bool, reason: str)

    We check rules in this order because some reasons are more urgent /
    obvious than others, and it's helpful for the human agent to know
    WHY they're getting this conversation.
    """
    if conversation_history is None:
        conversation_history = []

    if contains_sensitive_topic(user_message):
        return True, "sensitive_topic"

    if check_repeated_frustration(conversation_history, persona):
        return True, "repeated_frustration"

    if best_retrieval_score < config.CONFIDENCE_THRESHOLD:
        return True, "low_retrieval_confidence"

    return False, None


def generate_handoff_summary(user_query: str, persona: str, context_chunks: list,
                              reason: str = "low_retrieval_confidence") -> str:
    """
    Builds a clean, structured JSON "handoff package" for the human agent
    who will take over this conversation. Think of this like a sticky
    note attached to a file folder, summarizing everything the next
    person needs to know before they even open the folder.
    """
    handoff_data = {
        "escalation_reason": reason,
        "persona": persona,
        "detected_issue": user_query[:200] + ("..." if len(user_query) > 200 else ""),
        "retrieved_sources": [c["source"] for c in context_chunks],
        "confidence_score": round(
            max([c["score"] for c in context_chunks]) if context_chunks else 0.0, 3
        ),
        "recommended_action": _recommend_action_for_reason(reason)
    }
    return json.dumps(handoff_data, indent=2)


def _recommend_action_for_reason(reason: str) -> str:
    """
    Small helper that picks a sensible, human-readable suggestion for the
    support agent, based on WHY the conversation was escalated. This is
    kept private (the underscore prefix is a Python convention meaning
    "internal helper, not meant to be used outside this file").
    """
    recommendations = {
        "sensitive_topic": (
            "Review billing/account records directly and contact the customer "
            "personally, as this topic carries financial or legal sensitivity."
        ),
        "repeated_frustration": (
            "Customer has expressed frustration across multiple messages. "
            "Prioritize a direct, personal response rather than further automation."
        ),
        "low_retrieval_confidence": (
            "Review system documentation and error codes manually, as no strong "
            "match was found in the existing knowledge base for this query."
        )
    }
    return recommendations.get(reason, "Review conversation manually and respond directly.")
