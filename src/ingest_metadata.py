import json
import logging
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    return embedding_model.encode(text).tolist()

def mock_ingest_clio():
    """Ingest CLIO catalog 965DataGate datasets & open-source non-CLIO datasets."""
    logger.info("Ingesting from CLIO & Open Source sources...")
    clio_datasets = [
        {
            "id": "clio_965_poll2020",
            "title": "Public Opinion Poll Data 2020 (965DataGate)",
            "description": "Licensed public opinion polling data for the 2020 election cycle indexed in CLIO catalog under key 965DataGate.",
            "platform": "CLIO Catalog",
            "access_level": "Columbia-Licensed",
            "index_key": "965DataGate"
        },
        {
            "id": "clio_965_numeric",
            "title": "Numeric Data Collection (965DataGate)",
            "description": "Columbia licensed numeric economic and social datasets searchable in CLIO catalog using key index 965DataGate.",
            "platform": "CLIO Catalog",
            "access_level": "Columbia-Licensed",
            "index_key": "965DataGate"
        },
        {
            "id": "open_nasa_earth",
            "title": "NASA Earth Science & Climate Open Datasets",
            "description": "Open source satellite data and climate observations from NASA. Note: Open source datasets do not have standard CLIO records.",
            "platform": "Open Source Repository",
            "access_level": "Open Access"
        }
    ]
    for ds in clio_datasets:
        ds["embedding"] = generate_embedding(ds["description"])
    return clio_datasets

def mock_ingest_redivis():
    """Ingest Columbia Data Platform (Redivis) datasets including restricted HCUP, L2, IPUMS, and Eric/Moacir collections."""
    logger.info("Ingesting from Redivis / Columbia Data Platform (CDP)...")
    redivis_datasets = [
        {
            "id": "cdp_hcup",
            "title": "HCUP Healthcare Cost and Utilization Project",
            "description": "Restricted access hospital inpatient and outpatient medical campus dataset. Funded by faculty across Morningside and Medical campuses.",
            "platform": "Redivis (Columbia Data Platform)",
            "access_level": "Restricted",
            "manager": "Jeremiah",
            "url": "https://columbia.redivis.com/cul_hcup"
        },
        {
            "id": "cdp_l2_voter",
            "title": "L2 Micro-Level Election Voter Data",
            "description": "Granular micro-level election voter data managed by Population Research Center (CPRC). Not searchable in CLIO.",
            "platform": "Redivis (Columbia Data Platform)",
            "access_level": "Restricted",
            "manager": "Jeremiah & Ashley (CPRC / CUIT)",
            "url": "https://columbia.redivis.com/CPRC/datasets"
        },
        {
            "id": "cdp_ipums_census",
            "title": "IPUMS Restricted Access Full Count US Census (1790-1950)",
            "description": "Full count US decennial census microdata (1790-1950) managed by Population Research Center (CPRC). Not searchable in CLIO.",
            "platform": "Redivis (Columbia Data Platform)",
            "access_level": "Restricted",
            "manager": "Jeremiah & Ashley (CPRC / CUIT)",
            "url": "https://usa.ipums.org/usa/full_count/restricted_full_count.shtml"
        },
        {
            "id": "cdp_geospatial_eric",
            "title": "Licensed Geospatial & Spatial Analytics Datasets",
            "description": "Licensed GIS maps, boundary files, and spatial layers managed by Eric.",
            "platform": "Redivis (Columbia Data Platform)",
            "access_level": "Columbia-Licensed",
            "manager": "Eric"
        },
        {
            "id": "cdp_text_moacir",
            "title": "Textual & Computational Linguistics Corpus",
            "description": "Licensed text mining, linguistic corpora, and digital humanities datasets managed by Moacir.",
            "platform": "Redivis (Columbia Data Platform)",
            "access_level": "Columbia-Licensed",
            "manager": "Moacir"
        }
    ]
    for ds in redivis_datasets:
        ds["embedding"] = generate_embedding(ds["description"])
    return redivis_datasets

def mock_ingest_libguides():
    """Ingest RDS & Subject Specialist Libguides with specific program embeddings."""
    logger.info("Ingesting from Libguides (RDS & Subject Guides)...")
    libguides = [
        {
            "id": "lg_international_sipa",
            "title": "International Data Guide",
            "description": "Features 'Data of the Earth' section for SIPA's MPA-ESP program, including the Columbia CIESIN data catalog.",
            "program": "SIPA MPA-ESP",
            "url": "https://guides.library.columbia.edu/internationaldata",
            "key_sections": ["Data of the Earth", "Columbia CIESIN Data Catalog"]
        },
        {
            "id": "lg_datatools_med",
            "title": "Data Analysis Tools Guide",
            "description": "Includes two bio-stats books by Rafael A. Irizarry under the 'R' tab, tailored for Medical Campus R users.",
            "program": "Medical Campus",
            "url": "https://guides.library.columbia.edu/datatools/r",
            "key_sections": ["R Tab", "Rafael A. Irizarry Bio-Stats"]
        },
        {
            "id": "lg_numeric_data",
            "title": "Numeric Data Collection Guide",
            "description": "Index of Columbia licensed datasets searchable in CLIO via 965DataGate and migrating to Redivis CDP.",
            "program": "Research Data Services (RDS)",
            "url": "https://guides.library.columbia.edu/numeric/home"
        },
        {
            "id": "lg_election_opinion",
            "title": "Public Opinion Poll & Election Data Guide",
            "description": "Covers polling data, CPRC election voter data (L2), and IPUMS restricted access census datasets.",
            "program": "Political Science & CPRC",
            "url": "https://guides.library.columbia.edu/ElectionData/"
        }
    ]
    for lg in libguides:
        lg["embedding"] = generate_embedding(lg["description"])
    return libguides

if __name__ == "__main__":
    logger.info("Starting Columbia Library Data Graph Ingestion Pipeline")
    datasets = mock_ingest_clio() + mock_ingest_redivis()
    libguides = mock_ingest_libguides()

    logger.info(f"Successfully processed {len(datasets)} datasets and {len(libguides)} libguides.")

    with open("data/mock_graph_nodes.json", "w", encoding="utf-8") as f:
        json.dump({"datasets": datasets, "libguides": libguides}, f, indent=2)
    logger.info("Saved mock graph data to JSON.")
