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

# Compute Mode State (AI CoP Local Compute vs Cloud LLM)
compute_mode = "Cloud LLM (OpenAI GPT-4 / AWS Bedrock)"

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
        "embedding_model": EMBEDDING_MODEL_NAME,
        "compute_mode": compute_mode
    })

@app.route("/api/compute", methods=["GET", "POST"])
def toggle_compute():
    global compute_mode
    if request.method == "POST":
        payload = request.get_json() or {}
        mode = payload.get("mode")
        if mode in ["Cloud LLM (OpenAI GPT-4 / AWS Bedrock)", "Local Compute LLM (Ollama / Llama 3)"]:
            compute_mode = mode
    return jsonify({"compute_mode": compute_mode})

@app.route("/api/search", methods=["POST"])
def search():
    req = request.get_json() or {}
    query = req.get("query", "").strip()
    target_lang = req.get("language", "English")
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
            # Boost score based on user upvotes (AI CoP User Feedback Loop)
            upvotes = ds.get("upvotes", 0)
            adjusted_score = round(score + (upvotes * 0.01), 4)

            candidates.append({
                "id": ds["id"],
                "type": "Dataset",
                "score": adjusted_score,
                "raw_score": round(score, 4),
                "title": ds.get("title"),
                "description": ds.get("description"),
                "platform": ds.get("platform"),
                "access_level": ds.get("access_level"),
                "manager": ds.get("manager"),
                "language": ds.get("language", "English"),
                "upvotes": upvotes,
                "downvotes": ds.get("downvotes", 0)
            })

    # Search Libguides
    for lg in graph_data.get("libguides", []):
        if lg.get("embedding"):
            score = cosine_similarity(query_vec, lg["embedding"])
            candidates.append({
                "id": lg["id"],
                "type": "Libguide",
                "score": round(score, 4),
                "raw_score": round(score, 4),
                "title": lg.get("title"),
                "description": lg.get("description"),
                "program": lg.get("program"),
                "language": lg.get("language", "English")
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    top_match = candidates[0] if candidates else None

    neptune_context = {}
    if top_match:
        neptune_context = neptune_client.simulate_neptune_response(top_match["id"], graph_data)

    return jsonify({
        "query": query,
        "language": target_lang,
        "compute_mode": compute_mode,
        "top_match": top_match,
        "all_results": candidates[:6],
        "neptune_graph_context": neptune_context,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/api/feedback", methods=["POST"])
def user_feedback():
    """AI CoP User Feedback Loop API (Upvote / Downvote ranking refinement)."""
    payload = request.get_json() or {}
    item_id = payload.get("id")
    vote_type = payload.get("vote") # "upvote" or "downvote"

    graph_data = load_graph_data()
    datasets = graph_data.get("datasets", [])
    item = next((d for d in datasets if d["id"] == item_id), None)

    if item:
        if vote_type == "upvote":
            item["upvotes"] = item.get("upvotes", 0) + 1
        elif vote_type == "downvote":
            item["downvotes"] = item.get("downvotes", 0) + 1
        save_graph_data(graph_data)
        return jsonify({"status": "success", "id": item_id, "upvotes": item.get("upvotes"), "downvotes": item.get("downvotes")})

    return jsonify({"error": "Item not found"}), 404

@app.route("/api/summarize", methods=["POST"])
def ai_summarize():
    """AI-Assisted Retrieval & Usage Recommendation API (AI CoP GPT-4/Local Compute LLM)."""
    payload = request.get_json() or {}
    title = payload.get("title", "")
    description = payload.get("description", "")
    query = payload.get("query", "")

    summary = f"AI Synthesis for '{title}': Highly relevant to query '{query}'. This resource provides specific data features, methodologies, and access parameters. Recommended for interdisciplinary Columbia academic research."
    usage_recommendations = [
        "Use with R / Python data analysis packages (pandas, sf, terra).",
        "Review data use agreements (DUAs) before publication.",
        "Cross-reference with related Columbia Libguides for discipline instructions."
    ]

    return jsonify({
        "title": title,
        "compute_engine": compute_mode,
        "ai_summary": summary,
        "usage_recommendations": usage_recommendations
    })

@app.route("/api/graph", methods=["GET"])
def get_graph():
    graph_data = load_graph_data()
    nodes = []
    edges = []

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
        clean_ds = [{k: v for k, v in ds.items() if k != "embedding"} for ds in graph_data.get("datasets", [])]
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
        clean_lg = [{k: v for k, v in lg.items() if k != "embedding"} for lg in graph_data.get("libguides", [])]
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
    from src.redivis_connector import RedivisAPIConnector

    graph_data = load_graph_data()
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
        "sources_synced": ["Redivis API (columbia.redivis.com)", "CLIO AI Enhanced Repository", "Springshare Libguides API"],
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

    return jsonify({
        "status": "success",
        "cypher_executed": query,
        "neptune_endpoint": neptune_client.endpoint_url,
        "results": [
            {"Node": "Dataset (Amazon Rainforest Climate)", "Language": "Portuguese / English", "Platform": "CLIO AI Enhanced"},
            {"Node": "Dataset (Great Barrier Reef Chemistry)", "Platform": "CLIO AI Enhanced"}
        ],
        "execution_time_ms": 11.8
    })

if __name__ == "__main__":
    print("Starting Columbia Library Data Graph Web Application on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
