import json
import logging
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the state-of-the-art embedding model
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
try:
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
except Exception as e:
    logger.error(f"Failed to load embedding model: {e}")
    embedding_model = None

def generate_embedding(text):
    if not embedding_model or not text:
        return []
    # For documents, BGE doesn't strictly need a prefix, but we generate the raw embedding
    return embedding_model.encode(text).tolist()

def mock_ingest_clio():
    """Mock function to simulate ingesting '965DataGate' datasets from CLIO."""
    logger.info("Ingesting from CLIO...")
    clio_datasets = [
        {
            "id": "clio_123",
            "title": "Public Opinion Poll Data 2020",
            "description": "Licensed public opinion polling data for the 2020 election cycle.",
            "platform": "CLIO",
            "access_level": "Columbia-Licensed"
        }
    ]
    for ds in clio_datasets:
        ds["embedding"] = generate_embedding(ds["description"])
    return clio_datasets

def mock_ingest_redivis():
    """Mock function to simulate ingesting restricted datasets from Redivis (CDP)."""
    logger.info("Ingesting from Redivis/CDP...")
    redivis_datasets = [
        {
            "id": "cdp_hcup",
            "title": "HCUP Healthcare Cost and Utilization Project",
            "description": "Restricted access medical campus and department data.",
            "platform": "Redivis",
            "access_level": "Restricted",
            "manager": "Jeremiah"
        },
        {
            "id": "cdp_l2",
            "title": "L2 Voter Data",
            "description": "Micro-level election voter data managed by the Population Research Center.",
            "platform": "Redivis",
            "access_level": "Restricted",
            "manager": "Jeremiah"
        }
    ]
    for ds in redivis_datasets:
        ds["embedding"] = generate_embedding(ds["description"])
    return redivis_datasets

def mock_ingest_libguides():
    """Mock function to simulate scraping Springshare Libguides."""
    logger.info("Ingesting from Libguides...")
    libguides = [
        {
            "id": "lg_intl",
            "title": "International Data Guide",
            "description": "Contains Data of the Earth for SIPA's MPA-ESP program, including Columbia CIESIN data.",
            "program": "SIPA MPA-ESP"
        },
        {
            "id": "lg_med",
            "title": "Data Analysis Tools Guide",
            "description": "Includes bio-stats books by Rafael A. Irizarry under the R tab for Medical Campus R users.",
            "program": "Medical Campus"
        }
    ]
    for lg in libguides:
        lg["embedding"] = generate_embedding(lg["description"])
    return libguides

if __name__ == "__main__":
    logger.info("Starting Columbia Library Data Graph Ingestion Pipeline")
    datasets = mock_ingest_clio() + mock_ingest_redivis()
    libguides = mock_ingest_libguides()

    # In a real scenario, this data would be written to CSVs in OpenCypher format
    # and loaded into AWS Neptune or Neo4j.
    logger.info(f"Successfully processed {len(datasets)} datasets and {len(libguides)} libguides.")

    with open("data/mock_graph_nodes.json", "w") as f:
        json.dump({"datasets": datasets, "libguides": libguides}, f, indent=2)
    logger.info("Saved mock graph data to JSON.")
