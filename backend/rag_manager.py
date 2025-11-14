# backend/rag_manager.py
import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# -------------------------------------------------
# Config & Paths
# -------------------------------------------------
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
model = SentenceTransformer(EMBEDDING_MODEL)

VECTOR_DIR = "backend/vector_store"
PKL_DIR = os.path.join(VECTOR_DIR, "pkl_data")
INDEX_FILE = os.path.join(VECTOR_DIR, "faiss_index.bin")
META_FILE = os.path.join(VECTOR_DIR, "meta.pkl")  # mapping: website → chunk count

# Ensure folders exist
os.makedirs(VECTOR_DIR, exist_ok=True)
os.makedirs(PKL_DIR, exist_ok=True)

# -------------------------------------------------
# FAISS index helpers
# -------------------------------------------------
def load_index():
    if os.path.exists(INDEX_FILE):
        index = faiss.read_index(INDEX_FILE)
    else:
        index = faiss.IndexFlatL2(384)  # for MiniLM-L6-v2 embeddings
    return index

def save_index(index):
    faiss.write_index(index, INDEX_FILE)

def embed_text(texts):
    return np.array(model.encode(texts, show_progress_bar=False, convert_to_numpy=True))

# -------------------------------------------------
# Website pickle helpers
# -------------------------------------------------
def get_pickle_path(website_name: str):
    safe_name = (
        website_name.replace("https://", "")
        .replace("http://", "")
        .replace("/", "_")
        .replace(":", "_")
    )
    return os.path.join(PKL_DIR, f"{safe_name}.pkl")

def save_chunks_to_pickle(website_name: str, chunks: list[str]):
    pkl_path = get_pickle_path(website_name)
    with open(pkl_path, "wb") as f:
        pickle.dump(chunks, f)
    print(f"✅ Saved {len(chunks)} chunks to {pkl_path}")

def load_chunks_from_pickle(website_name: str):
    pkl_path = get_pickle_path(website_name)
    if os.path.exists(pkl_path):
        with open(pkl_path, "rb") as f:
            chunks = pickle.load(f)
        print(f"📂 Loaded {len(chunks)} chunks from {pkl_path}")
        return chunks
    return None

# -------------------------------------------------
# Add website data to RAG
# -------------------------------------------------
def add_website_data_to_rag(website_name: str, chunks: list[str]):
    """Embed website chunks, save to pickle, and add to FAISS index."""
    if not chunks:
        print(f"⚠️ No chunks to add for {website_name}")
        return

    # Save pickle
    save_chunks_to_pickle(website_name, chunks)

    # Load index and add vectors
    index = load_index()
    vectors = embed_text(chunks)
    index.add(vectors)
    save_index(index)

    # Save/update metadata (chunk count per website)
    meta = {}
    if os.path.exists(META_FILE):
        with open(META_FILE, "rb") as f:
            meta = pickle.load(f)
    meta[website_name] = len(chunks)
    with open(META_FILE, "wb") as f:
        pickle.dump(meta, f)

    print(f"✅ Added {len(chunks)} chunks from {website_name} to FAISS index")

# -------------------------------------------------
# Search RAG index
# -------------------------------------------------
def search_rag(query: str, top_k: int = 3):
    """Search FAISS index and return top matching text chunks."""
    # Collect all text chunks from .pkl files
    all_chunks = []
    for file in os.listdir(PKL_DIR):
        if file.endswith(".pkl"):
            try:
                with open(os.path.join(PKL_DIR, file), "rb") as f:
                    chunks = pickle.load(f)
                    all_chunks.extend(chunks)
            except Exception as e:
                print(f"⚠️ Could not read {file}: {e}")

    if not all_chunks:
        print("⚠️ No data available in RAG store")
        return []

    index = load_index()
    if index.ntotal == 0:
        print("⚠️ Empty FAISS index")
        return []

    query_vec = embed_text([query])
    distances, indices = index.search(query_vec, top_k)

    results = []
    for i in indices[0]:
        if 0 <= i < len(all_chunks):
            results.append(all_chunks[i])
    return results
