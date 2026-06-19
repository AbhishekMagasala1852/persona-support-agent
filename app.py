"""
app.py

THIS is the file you actually run to start the chatbot. It creates the
chat window you see in your web browser, using a tool called Streamlit.

Think of this file as the "conductor" of an orchestra. It doesn't play
any instrument itself - it just tells each musician (classifier.py,
rag_pipeline.py, generator.py, escalator.py) exactly when to play their
part, in the right order:

    1. Customer types a message.
    2. classifier.py decides: who is this customer? (persona)
    3. rag_pipeline.py searches our documents for relevant facts.
    4. escalator.py checks: is this too risky/sensitive to auto-answer?
    5. generator.py writes the final reply (or escalator.py's note wins).
    6. The reply is shown on screen.
"""

import sys
import os
import json
import streamlit as st

# Make sure Python can find our files inside the src/ folder.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import config
from classifier import classify_customer_persona
from rag_pipeline import LocalRAGPipeline
from generator import generate_adaptive_response
from escalator import should_escalate, generate_handoff_summary


# -----------------------------------------------------------------------
# PAGE SETUP
# -----------------------------------------------------------------------
st.set_page_config(page_title="Persona-Adaptive Support Agent", page_icon="🤖")
st.title("🤖 Persona-Adaptive Customer Support Agent")
st.caption(
    "This assistant detects whether you sound like a Technical Expert, a "
    "Frustrated User, or a Business Executive, and adapts its tone "
    "accordingly. It only answers using our real help documents."
)


# -----------------------------------------------------------------------
# ONE-TIME SETUP (runs once, then gets cached/reused automatically)
# -----------------------------------------------------------------------
@st.cache_resource
def load_pipeline():
    pipeline = LocalRAGPipeline()
    # Don't build knowledge base here - we'll build it lazily
    return pipeline

# Remove the spinner and build call
rag_pipeline = load_pipeline()

# Add a small check after loading
if rag_pipeline.collection.count() == 0:
    st.warning("Knowledge base is empty. Documents will be processed when you ask your first question.")


# -----------------------------------------------------------------------
# CONVERSATION MEMORY
# -----------------------------------------------------------------------
# Streamlit re-runs this whole script every time the user sends a
# message, so we use "session_state" as a notebook that survives between
# those re-runs, to remember the chat history and detected personas.
if "messages" not in st.session_state:
    st.session_state.messages = []  # what gets displayed on screen

if "persona_history" not in st.session_state:
    st.session_state.persona_history = []  # used for the "repeated frustration" check


# Re-display the full conversation so far, every time the page refreshes.
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# -----------------------------------------------------------------------
# MAIN CHAT LOOP
# -----------------------------------------------------------------------
user_input = st.chat_input("Type your support question here...")

if user_input:
    # 1. Show the customer's own message immediately on screen.
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            # 2. CLASSIFY: which persona does this message sound like?
            classification = classify_customer_persona(user_input)
            persona = classification["persona"]

            # 3. RETRIEVE: search our documents for relevant chunks.
            # Build knowledge base if it's empty
            if rag_pipeline.collection.count() == 0:
                with st.spinner("Processing documents for the first time..."):
                    rag_pipeline.build_knowledge_base()
            context_chunks = rag_pipeline.retrieve_context(user_input)
            best_score = max([c["score"] for c in context_chunks]) if context_chunks else 0.0

            # 4. ESCALATION CHECK: should a human take over instead?
            escalate_now, reason = should_escalate(
                user_message=user_input,
                persona=persona,
                best_retrieval_score=best_score,
                conversation_history=st.session_state.persona_history
            )

            if escalate_now:
                # A human needs to step in. We build a clean handoff
                # summary instead of letting the AI attempt an answer.
                handoff_json = generate_handoff_summary(
                    user_input, persona, context_chunks, reason
                )
                reply_text = (
                    "I want to make sure this gets the right attention, so I'm "
                    "connecting you with a human support specialist who can help "
                    "further. Here's a summary I've prepared for them:"
                )
                st.markdown(reply_text)
                st.code(handoff_json, language="json")
                final_display_text = reply_text + "\n\n```json\n" + handoff_json + "\n```"

            else:
                # 5. GENERATE: write the persona-adapted, fact-grounded reply.
                result = generate_adaptive_response(user_input, persona, context_chunks)
                st.markdown(result["response"])
                final_display_text = result["response"]

            # Small transparency footer showing what the system detected.
            # This is genuinely useful during grading/demo, since it shows
            # your classifier and retrieval system are actually working.
            with st.expander("🔍 Debug info (persona + retrieval details)"):
                st.write(f"**Detected persona:** {persona}")
                st.write(f"**Classifier confidence:** {classification.get('confidence')}")
                st.write(f"**Classifier reasoning:** {classification.get('reasoning')}")
                st.write(f"**Best retrieval score:** {best_score:.3f}")
                st.write(f"**Sources used:** {[c['source'] for c in context_chunks]}")

    # 6. Save this turn into memory for next time.
    st.session_state.messages.append({"role": "assistant", "content": final_display_text})
    st.session_state.persona_history.append(persona)