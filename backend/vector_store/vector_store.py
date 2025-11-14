# backend/vector_store/vector_store.py
import os
import pickle
import re
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from urllib.parse import urlparse

EMBED_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def _sanitize_filename(url):
    """Convert URL to safe filename for storing FAISS index & metadata."""
    parsed = urlparse(url)
    name = parsed.netloc.replace(".", "_").replace("-", "_")
    if not name:
        name = re.sub(r'\W+', '_', url)
    return name

def save_to_vector_index(url, text, chunk_size=1000):
    """Save text chunks into a FAISS index & metadata file per website."""
    if not text.strip():
        return

    # Split text into chunks
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    embeddings = EMBED_MODEL.encode(chunks, convert_to_numpy=True)

    # Create file paths per website
    base_name = _sanitize_filename(url)
    index_path = f"backend/vector_store/{base_name}_index.faiss"
    metadata_path = f"backend/vector_store/{base_name}_meta.pkl"

    # Load existing index if exists, else create new
    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
    else:
        index = faiss.IndexFlatL2(embeddings.shape[1])
        metadata = []

    # Add embeddings & metadata
    index.add(np.array(embeddings))
    metadata.extend([{"url": url, "chunk": c} for c in chunks])

    # Save back
    faiss.write_index(index, index_path)
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata, f)

    print(f"💾 Saved FAISS index at: {index_path}")
    print(f"💾 Saved metadata at: {metadata_path}")
