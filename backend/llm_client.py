# backend/llm_client.py

import os
from dotenv import load_dotenv
from ollama import Client
from sentence_transformers import SentenceTransformer

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:1b")   # ✅ Correct offline model
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

# -----------------------------
# Initialize clients
# -----------------------------
client = Client(host=OLLAMA_HOST)
embedder = SentenceTransformer(EMBEDDING_MODEL)

print(f"✅ Ollama Client connected to {OLLAMA_HOST}, model: {LLM_MODEL}")
print(f"✅ Embedding model loaded: {EMBEDDING_MODEL}")

# -----------------------------
# Function: Generate chatbot response (Ollama)
# -----------------------------
def generate_response(message: str, context: str = "", system_prompt: str = "") -> str:
    """
    Generate response using local Ollama LLM.
    Fully offline.
    """
    try:
        # Build final prompt
        prompt_parts = []
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}")
        if context:
            prompt_parts.append(f"Context: {context}")
        prompt_parts.append(f"User: {message}")

        final_prompt = "\n\n".join(prompt_parts)

        # Call Ollama model
        response = client.generate(
            model=LLM_MODEL,
            prompt=final_prompt
        )

        return response.get("response", "").strip()

    except Exception as e:
        # Return a clear error message
        return f"❌ Ollama Error: {e}"

# -----------------------------
# Function: Generate embeddings
# -----------------------------
def get_embedding(text: str):
    """
    Generate embedding using SentenceTransformer.
    """
    try:
        return embedder.encode(text, show_progress_bar=False).tolist()
    except Exception as e:
        print("❌ Embedding Error:", e)
        return []
