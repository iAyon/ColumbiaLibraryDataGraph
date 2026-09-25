import json
import sys
import numpy as np
from sentence_transformers import SentenceTransformer
from src.neptune_client import NeptuneGraphClient

# Ensure UTF-8 output encoding across environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

class GraphRAGDiscoveryAgent:
    """
    GraphRAG Agent combining Vector Search (Embedding Similarity)
    with AWS Neptune OpenCypher Graph Traversal & Policy Routing.
    """
    def __init__(self, data_path: str):
        with open(data_path, "r") as f:
            self.graph_data = json.load(f)
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.neptune_client = NeptuneGraphClient()

    def search_and_traverse(self, query: str):
        print(f"\n=======================================================")
        print(f"QUERY: '{query}'")
        print(f"=======================================================")

        # Step 1: Vector Search Embedding
        query_prefix = "Represent this sentence for searching relevant passages: "
        query_vec = self.embedding_model.encode(query_prefix + query).tolist()

        candidates = []
        for ds in self.graph_data.get("datasets", []):
            if ds.get("embedding"):
                score = cosine_similarity(query_vec, ds["embedding"])
                candidates.append({"id": ds["id"], "type": "Dataset", "score": score, "raw": ds})

        for lg in self.graph_data.get("libguides", []):
            if lg.get("embedding"):
                score = cosine_similarity(query_vec, lg["embedding"])
                candidates.append({"id": lg["id"], "type": "Libguide", "score": score, "raw": lg})

        candidates.sort(key=lambda x: x["score"], reverse=True)
        top_match = candidates[0] if candidates else None

        if not top_match:
            print("No matching entity found.")
            return

        print(f"\n[STEP 1: VECTOR SEARCH MATCH]")
        print(f"Entity ID: {top_match['id']} | Type: {top_match['type']} | Score: {top_match['score']:.4f}")

        # Step 2: AWS Neptune Graph Traversal (Cypher)
        print(f"\n[STEP 2: AWS NEPTUNE CYPHER GRAPH TRAVERSAL]")
        graph_context = self.neptune_client.simulate_neptune_response(top_match["id"], self.graph_data)
        print("Executed Cypher Query:")
        print(graph_context.get("cypher_query"))

        # Step 3: GraphRAG Context Payload Construction
        print(f"\n[STEP 3: GRAPHRAG CONTEXT PAYLOAD FOR LLM]")
        payload = {
            "query": query,
            "matched_entity": top_match['raw']['title'],
            "graph_neighbors": graph_context
        }
        print(json.dumps(payload, indent=2))

        # Step 4: Policy & Access Control Evaluation
        print(f"\n[STEP 4: AGENT POLICY & ACCESS ROUTING]")
        if top_match["type"] == "Dataset":
            access_level = top_match["raw"].get("access_level")
            platform = top_match["raw"].get("platform")
            if access_level == "Restricted":
                mgr = top_match["raw"].get("manager", "Data Manager")
                print(f"⚠️ RESTRICTED ACCESS ALERT: Hosted on [{platform}]. Excluded from default CLIO catalog.")
                print(f"👉 INSTRUCTION: User must contact {mgr} to obtain credentials for Redivis.")
            elif access_level == "Columbia-Licensed":
                print(f"✅ Columbia Licensed: Accessible via CLIO with Columbia UNI authentication.")
        elif top_match["type"] == "Libguide":
            print(f"💡 RESEARCH GUIDE MATCH: Relevant to program [{top_match['raw'].get('program')}].")

if __name__ == "__main__":
    agent = GraphRAGDiscoveryAgent("data/mock_graph_nodes.json")
    agent.search_and_traverse("I need voter data for an election project.")
    agent.search_and_traverse("Looking for medical bio-stats tools in R.")
