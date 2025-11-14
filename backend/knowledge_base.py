# backend/knowledge_base.py
import os
import faiss
import numpy as np
import pickle

from llm_client import get_embedding

# FAISS index file path
INDEX_FILE = "knowledge_base.index"
DATA_FILE = "knowledge_data.pkl"

# Load or initialize FAISS index
def load_index(embedding_dim=1536):
    if os.path.exists(INDEX_FILE):
        index = faiss.read_index(INDEX_FILE)
        with open(DATA_FILE, "rb") as f:
            data = pickle.load(f)
        print("✅ Loaded existing Knowledge Base.")
        return index, data
    else:
        index = faiss.IndexFlatL2(embedding_dim)
        data = []
        print("🆕 Created new Knowledge Base.")
        return index, data


# Save index and data
def save_index(index, data):
    faiss.write_index(index, INDEX_FILE)
    with open(DATA_FILE, "wb") as f:
        pickle.dump(data, f)
    print("💾 Knowledge Base saved successfully.")


# Add new text to KB
def add_to_knowledge_base(text):
    embedding = np.array([get_embedding(text)], dtype="float32")
    index, data = load_index(len(embedding[0]))
    index.add(embedding)
    data.append(text)
    save_index(index, data)
    print(f"✅ Added: {text[:60]}...")


# Search similar text
def search_knowledge_base(query, top_k=3):
    embedding = np.array([get_embedding(query)], dtype="float32")
    index, data = load_index(len(embedding[0]))
    if index.ntotal == 0:
        return []
    distances, indices = index.search(embedding, top_k)
    results = [data[i] for i in indices[0] if i < len(data)]
    return results
