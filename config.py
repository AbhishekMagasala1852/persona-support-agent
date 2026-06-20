"""
config.py

Think of this file as the "settings panel" for the whole project.
Instead of scattering important numbers and names all over different files
(and forgetting where you put them), we keep them ALL in one single place.

If you ever want to change how strict the escalation rule is, or which
folder holds the documents, you only need to change it HERE - and every
other file automatically uses the new value.
"""

import os
from dotenv import load_dotenv

# This line reads the .env file (where your secret API key lives)
# and makes it available to the rest of the program.
load_dotenv()

# -----------------------------------------------------------------------
# API KEY
# -----------------------------------------------------------------------
# We read the key from the .env file rather than typing it directly here.
# This keeps your secret key out of the code, which is safer.
# Check both possible environment variable names
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")

# -----------------------------------------------------------------------
# MODEL NAMES
# -----------------------------------------------------------------------
# These are the names of the specific Google Gemini AI models we use.
# One model writes/classifies text, the other turns text into number-lists
# (embeddings) so we can search documents by meaning instead of by keyword.
GENERATION_MODEL = "gemini-2.0-flash"
EMBEDDING_MODEL = "models/gemini-embedding-2"

# -----------------------------------------------------------------------
# FOLDER PATHS
# -----------------------------------------------------------------------
# Where the raw help-desk documents live.
DATA_DIR = "data"

# Where the searchable "vector database" gets saved on disk, so we don't
# have to re-process all documents every single time the app starts.
CHROMA_DB_DIR = "./chroma_db"

# The name of the collection (like a labeled drawer) inside the vector
# database where all our document chunks are stored.
COLLECTION_NAME = "support_kb"

# -----------------------------------------------------------------------
# CHUNKING SETTINGS
# -----------------------------------------------------------------------
# When we break documents into bite-sized pieces, this controls how big
# each piece is (in characters) and how much neighboring pieces overlap.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# -----------------------------------------------------------------------
# RETRIEVAL SETTINGS
# -----------------------------------------------------------------------
# How many matching document chunks to pull back for each user question.
TOP_K_RESULTS = 3

# -----------------------------------------------------------------------
# ESCALATION SETTINGS
# -----------------------------------------------------------------------
# If the best matching document chunk has a similarity score BELOW this
# number, we assume we don't have a good enough answer, and we hand the
# conversation off to a human instead of guessing.
CONFIDENCE_THRESHOLD = 0.45

# If the user's message mentions any of these sensitive words, we ALWAYS
# escalate to a human, no matter how confident the document search was.
# This protects against the AI making promises it shouldn't make about
# money, legal matters, or account security.
SENSITIVE_KEYWORDS = [
    "refund", "chargeback", "lawsuit", "legal action", "sue",
    "cancel my account", "delete my account", "fraud", "unauthorized charge",
    "lawyer", "attorney", "compensation", "demand a refund"
]

# Valid persona categories. Keeping this list in one place means every
# file that needs to check "is this a valid persona?" uses the exact
# same three options, with no risk of typos causing mismatches.
VALID_PERSONAS = ["Technical Expert", "Frustrated User", "Business Executive"]
