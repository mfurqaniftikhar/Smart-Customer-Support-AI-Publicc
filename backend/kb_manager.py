import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ✅ Load embedding model (same as your .env)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
model = SentenceTransformer(EMBEDDING_MODEL)

# 📂 File path for knowledge base
KB_PATH = "knowledge_data.pkl"

# 🔹 Load Knowledge Base
def load_knowledge_base():
    """Load the knowledge base from pickle file"""
    if os.path.exists(KB_PATH):
        try:
            with open(KB_PATH, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"❌ Error loading knowledge base: {e}")
            return {"texts": [], "embeddings": []}
    return {"texts": [], "embeddings": []}

# 🔹 Save Knowledge Base
def save_knowledge_base(kb):
    """Save the knowledge base to pickle file"""
    try:
        with open(KB_PATH, "wb") as f:
            pickle.dump(kb, f)
    except Exception as e:
        print(f"❌ Error saving knowledge base: {e}")

# 🔹 Add new text to KB
def add_to_knowledge_base(text):
    """Add new text and its embedding to the knowledge base"""
    try:
        kb = load_knowledge_base()
        embedding = model.encode([text])[0]
        kb["texts"].append(text)
        kb["embeddings"].append(embedding.tolist())  # Convert to list for pickle
        save_knowledge_base(kb)
        print(f"✅ Added to Knowledge Base: {text[:60]}...")
        return True
    except Exception as e:
        print(f"❌ Error adding to knowledge base: {e}")
        return False

# 🔹 Search KB for relevant answers
def search_knowledge_base(query, top_k=3):
    """Search knowledge base for most relevant texts based on query"""
    try:
        kb = load_knowledge_base()
        
        if not kb["texts"] or not kb["embeddings"]:
            return []
        
        # Encode query
        query_embedding = model.encode([query])[0]
        
        # Convert embeddings back to numpy arrays if needed
        kb_embeddings = [np.array(emb) for emb in kb["embeddings"]]
        
        # Calculate similarities
        similarities = cosine_similarity(
            [query_embedding], kb_embeddings
        )[0]
        
        # Get top_k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Return results with similarity scores
        results = [
            {
                "text": kb["texts"][i],
                "score": float(similarities[i])
            }
            for i in top_indices if similarities[i] > 0.3  # Threshold for relevance
        ]
        
        return results
        
    except Exception as e:
        print(f"❌ Error searching knowledge base: {e}")
        return []

# 🔹 Optional: Clear knowledge base
def clear_knowledge_base():
    """Clear all data from knowledge base"""
    try:
        if os.path.exists(KB_PATH):
            os.remove(KB_PATH)
            print("✅ Knowledge base cleared")
        else:
            print("ℹ️ Knowledge base already empty")
    except Exception as e:
        print(f"❌ Error clearing knowledge base: {e}")

# 🔹 Optional: Get KB stats
def get_kb_stats():
    """Get statistics about the knowledge base"""
    kb = load_knowledge_base()
    return {
        "total_entries": len(kb["texts"]),
        "has_embeddings": len(kb["embeddings"]) > 0
    }
    
# 🔹 Reset knowledge base if corrupted
def reset_knowledge_base():
    """Reset knowledge base by deleting the file"""
    try:
        if os.path.exists(KB_PATH):
            os.remove(KB_PATH)
            print("✅ Knowledge base reset successfully")
        save_knowledge_base({"texts": [], "embeddings": []})
        print("✅ New knowledge base created")
    except Exception as e:
        print(f"❌ Error resetting knowledge base: {e}")