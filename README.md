# Persona-Adaptive Customer Support Agent

An intelligent support chatbot that detects customer personas (Technical Expert, Frustrated User, or Business Executive) and adapts its responses accordingly. Built with Google's Gemini API, Streamlit, and a local RAG (Retrieval-Augmented Generation) pipeline.

## Features

*   **Persona Detection:** Classifies user messages using Gemini AI, with a local fallback classifier if the API quota is exceeded.
*   **Adaptive Responses:** Generates replies tailored to the detected persona (technical, empathetic, or concise).
*   **RAG Pipeline:** Searches a local knowledge base of documents (TXT, MD, PDF) for relevant information to ground the AI's answers.
*   **Safety & Escalation:** Automatically escalates conversations to a human agent for sensitive topics (e.g., refunds, legal threats) or if the AI is unsure.
*   **Frustration Detection:** Tracks repeated frustrated messages and suggests escalation.
*   **Interactive UI:** Clean, chat-based interface built with Streamlit.

## Project Structure
persona-support-agent/
├── data/ # Knowledge base documents
│ ├── api_troubleshooting.md
│ ├── billing_policy.txt
│ ├── business_impact.txt
│ ├── password_reset_guide.pdf
│ └── password_reset_guide.txt
├── src/ # Core application logic
│ ├── classifier.py # Persona detection (API + local fallback)
│ ├── config.py # Configuration settings
│ ├── escalator.py # Escalation logic
│ ├── generator.py # Response generation
│ ├── rag_pipeline.py # Document ingestion and retrieval
│ └── local_classifier.py # Local persona classifier
├── app.py # Streamlit web interface
├── requirements.txt # Python dependencies
└── README.md # This file

text
