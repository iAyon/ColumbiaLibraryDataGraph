import json
import sys
import numpy as np
from sentence_transformers import SentenceTransformer

# Ensure stdout supports UTF-8 characters (emojis) across environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Load the same embedding model
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
print(f"Loading query embedding model: {EMBEDDING_MODEL_NAME}")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

class ColumbiaLibraryAgent:
    def __init__(self, data_path):
        with open(data_path, "r") as f:
            self.graph_data = json.load(f)

    def search(self, query: str):
        print(f"\n--- Processing Query: '{query}' ---")
        # BGE models require a prefix for queries for optimal retrieval
        query_prefix = "Represent this sentence for searching relevant passages: "
        query_vec = embedding_model.encode(query_prefix + query).tolist()

        results = []

        # Search Datasets
        for ds in self.graph_data.get("datasets", []):
            if "embedding" in ds and ds["embedding"]:
                score = cosine_similarity(query_vec, ds["embedding"])
                results.append({"type": "Dataset", "score": score, "data": ds})

        # Search Libguides
        for lg in self.graph_data.get("libguides", []):
            if "embedding" in lg and lg["embedding"]:
                score = cosine_similarity(query_vec, lg["embedding"])
                results.append({"type": "Libguide", "score": score, "data": lg})

        # Sort by similarity score
        results.sort(key=lambda x: x["score"], reverse=True)
        top_result = results[0] if results else None

        if top_result:
            self._handle_response(top_result)
        else:
            print("No relevant resources found.")

    def _handle_response(self, result):
        data = result["data"]
        print(f"Top Match [{result['type']}] (Score: {result['score']:.4f}): {data['title']}")
        print(f"Description: {data['description']}")

        # Access control / Agentic logic
        if result["type"] == "Dataset":
            print(f"Platform: {data['platform']}")
            if data.get("access_level") == "Restricted":
                manager = data.get("manager", "the appropriate department")
                print(f"⚠️ AGENT ALERT: This dataset is RESTRICTED. It will not appear in a standard CLIO search.")
                print(f"➡️ ACTION REQUIRED: You must contact {manager} to request access to this data on Redivis.")
            elif data.get("access_level") == "Columbia-Licensed":
                print("✅ Access: Available to Columbia affiliates (Requires UNI login via CLIO).")
        elif result["type"] == "Libguide":
            print(f"Target Program: {data.get('program', 'General')}")
            print("💡 TIP: Check this Libguide for detailed instructions and related resources.")

if __name__ == "__main__":
    agent = ColumbiaLibraryAgent("data/mock_graph_nodes.json")

    # Test queries based on user's prompt
    agent.search("I need voter data for an election project.")
    agent.search("Looking for medical bio-stats tools in R.")
