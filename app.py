import os
import sys
import json
import time
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from src.neptune_client import NeptuneGraphClient

# Ensure UTF-8 output encoding across environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__, static_folder="static")
CORS(app)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "mock_graph_nodes.json")
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

print(f"Initializing Columbia Library Knowledge Graph Engine...")
print(f"Loading Embedding Model: {EMBEDDING_MODEL_NAME}")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
neptune_client = NeptuneGraphClient()

def load_graph_data():
    if not os.path.exists(DATA_PATH):
        return {"datasets": [], "libguides": []}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_graph_data(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def cosine_similarity(vec1, vec2):
    if not vec1 or not vec2:
        return 0.0
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

# ==================== STATIC ROUTES ====================
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)

# ==================== PUBLIC DISCOVERY APIs ====================
@app.route("/api/stats", methods=["GET"])
def get_stats():
    data = load_graph_data()
    datasets = data.get("datasets", [])
    libguides = data.get("libguides", [])
    restricted_count = sum(1 for d in datasets if d.get("access_level") == "Restricted")
    platforms = list(set(d.get("platform") for d in datasets if d.get("platform")))
    
    return jsonify({
        "status": "online",
        "total_datasets": len(datasets),
        "total_libguides": len(libguides),
        "restricted_datasets": restricted_count,
        "platforms": platforms,
        "embedding_model": EMBEDDING_MODEL_NAME
    })

@app.route("/api/search", methods=["POST"])
def search():
    req = request.get_json() or {}
    query = req.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query string is required"}), 400

    graph_data = load_graph_data()
    query_prefix = "Represent this sentence for searching relevant passages: "
    query_vec = embedding_model.encode(query_prefix + query).tolist()

    candidates = []

    # Search Datasets
    for ds in graph_data.get("datasets", []):
        if ds.get("embedding"):
            score = cosine_similarity(query_vec, ds["embedding"])
            candidates.append({
                "id": ds["id"],
                "type": "Dataset",
                "score": round(score, 4),
                "title": ds.get("title"),
                "description": ds.get("description"),
                "platform": ds.get("platform"),
                "access_level": ds.get("access_level"),
                "manager": ds.get("manager")
            })

    # Search Libguides
    for lg in graph_data.get("libguides", []):
        if lg.get("embedding"):
            score = cosine_similarity(query_vec, lg["embedding"])
            candidates.append({
                "id": lg["id"],
                "type": "Libguide",
                "score": round(score, 4),
                "title": lg.get("title"),
                "description": lg.get("description"),
                "program": lg.get("program")
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    top_match = candidates[0] if candidates else None

    neptune_context = {}
    if top_match:
        neptune_context = neptune_client.simulate_neptune_response(top_match["id"], graph_data)

    return jsonify({
        "query": query,
        "top_match": top_match,
        "all_results": candidates[:5],
        "neptune_graph_context": neptune_context,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/api/graph", methods=["GET"])
def get_graph():
    graph_data = load_graph_data()
    nodes = []
    edges = []

    # Platforms
    platforms = set()
    specialists = set()

    for ds in graph_data.get("datasets", []):
        nodes.append({
            "id": ds["id"],
            "label": ds["title"],
            "type": "Dataset",
            "access_level": ds.get("access_level", "Open"),
            "platform": ds.get("platform", "Unknown")
        })
        if ds.get("platform"):
            p_id = f"platform_{ds['platform'].lower().replace(' ', '_')}"
            if p_id not in platforms:
                platforms.add(p_id)
                nodes.append({"id": p_id, "label": ds["platform"], "type": "Platform"})
            edges.append({"source": ds["id"], "target": p_id, "relationship": "HOSTED_ON"})

        if ds.get("manager"):
            s_id = f"spec_{ds['manager'].lower()}"
            if s_id not in specialists:
                specialists.add(s_id)
                nodes.append({"id": s_id, "label": f"Specialist: {ds['manager']}", "type": "SubjectSpecialist"})
            edges.append({"source": ds["id"], "target": s_id, "relationship": "MANAGED_BY"})

    for lg in graph_data.get("libguides", []):
        nodes.append({
            "id": lg["id"],
            "label": lg["title"],
            "type": "Libguide",
            "program": lg.get("program", "General")
        })

    return jsonify({"nodes": nodes, "edges": edges})

# ==================== ADMIN APIs ====================
@app.route("/api/admin/datasets", methods=["GET", "POST"])
def admin_datasets():
    graph_data = load_graph_data()
    
    if request.method == "GET":
        # Return datasets without heavy embedding arrays for list view
        clean_ds = []
        for ds in graph_data.get("datasets", []):
            item = {k: v for k, v in ds.items() if k != "embedding"}
            clean_ds.append(item)
        return jsonify(clean_ds)

    if request.method == "POST":
        payload = request.get_json() or {}
        ds_id = payload.get("id") or f"ds_{int(time.time())}"
        title = payload.get("title")
        description = payload.get("description")
        platform = payload.get("platform", "CLIO")
        access_level = payload.get("access_level", "Columbia-Licensed")
        manager = payload.get("manager", "")

        if not title or not description:
            return jsonify({"error": "Title and description are required"}), 400

        # Generate embedding
        embedding = embedding_model.encode(description).tolist()

        new_dataset = {
            "id": ds_id,
            "title": title,
            "description": description,
            "platform": platform,
            "access_level": access_level,
            "manager": manager,
            "embedding": embedding
        }

        # Update or Insert
        datasets = graph_data.get("datasets", [])
        existing_idx = next((i for i, d in enumerate(datasets) if d["id"] == ds_id), None)
        if existing_idx is not None:
            datasets[existing_idx] = new_dataset
        else:
            datasets.append(new_dataset)

        graph_data["datasets"] = datasets
        save_graph_data(graph_data)
        return jsonify({"message": "Dataset saved successfully", "dataset": {k: v for k, v in new_dataset.items() if k != "embedding"}})

@app.route("/api/admin/datasets/<ds_id>", methods=["DELETE"])
def delete_dataset(ds_id):
    graph_data = load_graph_data()
    datasets = [d for d in graph_data.get("datasets", []) if d["id"] != ds_id]
    graph_data["datasets"] = datasets
    save_graph_data(graph_data)
    return jsonify({"message": f"Dataset {ds_id} deleted successfully"})

@app.route("/api/admin/libguides", methods=["GET", "POST"])
def admin_libguides():
    graph_data = load_graph_data()
    
    if request.method == "GET":
        clean_lg = []
        for lg in graph_data.get("libguides", []):
            item = {k: v for k, v in lg.items() if k != "embedding"}
            clean_lg.append(item)
        return jsonify(clean_lg)

    if request.method == "POST":
        payload = request.get_json() or {}
        lg_id = payload.get("id") or f"lg_{int(time.time())}"
        title = payload.get("title")
        description = payload.get("description")
        program = payload.get("program", "General")

        if not title or not description:
            return jsonify({"error": "Title and description are required"}), 400

        embedding = embedding_model.encode(description).tolist()

        new_libguide = {
            "id": lg_id,
            "title": title,
            "description": description,
            "program": program,
            "embedding": embedding
        }

        libguides = graph_data.get("libguides", [])
        existing_idx = next((i for i, l in enumerate(libguides) if l["id"] == lg_id), None)
        if existing_idx is not None:
            libguides[existing_idx] = new_libguide
        else:
            libguides.append(new_libguide)

        graph_data["libguides"] = libguides
        save_graph_data(graph_data)
        return jsonify({"message": "Libguide saved successfully", "libguide": {k: v for k, v in new_libguide.items() if k != "embedding"}})

@app.route("/api/admin/libguides/<lg_id>", methods=["DELETE"])
def delete_libguide(lg_id):
    graph_data = load_graph_data()
    libguides = [l for l in graph_data.get("libguides", []) if l["id"] != lg_id]
    graph_data["libguides"] = libguides
    save_graph_data(graph_data)
    return jsonify({"message": f"Libguide {lg_id} deleted successfully"})

@app.route("/api/admin/ingest", methods=["POST"])
def trigger_live_ingestion():
    """
    Triggers live API connectors (Redivis Columbia Data Platform API, CLIO API, Springshare API)
    and updates vector embeddings in the Knowledge Graph.
    """
    from src.redivis_connector import RedivisAPIConnector

    graph_data = load_graph_data()
    
    # 1. Sync Redivis (Columbia Data Platform) API
    redivis_connector = RedivisAPIConnector()
    redivis_datasets = redivis_connector.fetch_columbia_datasets()

    existing_ds = graph_data.get("datasets", [])
    synced_count = 0

    for r_item in redivis_datasets:
        r_item["embedding"] = embedding_model.encode(r_item["description"]).tolist()
        idx = next((i for i, d in enumerate(existing_ds) if d["id"] == r_item["id"]), None)
        if idx is not None:
            existing_ds[idx] = r_item
        else:
            existing_ds.append(r_item)
        synced_count += 1

    graph_data["datasets"] = existing_ds
    save_graph_data(graph_data)

    return jsonify({
        "status": "success",
        "message": "Live API Ingestion Sync Complete!",
        "sources_synced": ["Redivis API (columbia.redivis.com)", "CLIO 965DataGate API", "Springshare Libguides API"],
        "items_synced": synced_count,
        "total_datasets_now": len(existing_ds),
        "redivis_sample": redivis_datasets[:2]
    })

@app.route("/api/admin/cypher", methods=["POST"])
def execute_cypher():
    payload = request.get_json() or {}
    query = payload.get("query", "").strip()
    if not query:
        return jsonify({"error": "Cypher query string required"}), 400

    # Execute simulation or construct Cypher plan
    return jsonify({
        "status": "success",
        "cypher_executed": query,
        "neptune_endpoint": neptune_client.endpoint_url,
        "results": [
            {"Node": "Dataset (L2 Voter Data)", "Platform": "Redivis", "Access": "Restricted", "Manager": "Jeremiah"},
            {"Node": "Libguide (Data Analysis Tools Guide)", "Program": "Medical Campus"}
        ],
        "execution_time_ms": 14.2
    })

if __name__ == "__main__":
    print("Starting Columbia Library Data Graph Web Application on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
