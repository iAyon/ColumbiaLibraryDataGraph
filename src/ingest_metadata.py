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
            "id": "clio_965_numeric",
            "title": "Numeric Data Collection (965DataGate)",
            "description": "Columbia licensed numeric economic, financial, and social science datasets searchable in CLIO catalog using key index 965DataGate. Migrating to Redivis CDP.",
            "platform": "CLIO Catalog",
            "access_level": "Columbia-Licensed",
            "index_key": "965DataGate",
            "manager": "RDS Librarian",
            "language": "English"
        },
        {
            "id": "clio_965_polls",
            "title": "Public Opinion Poll Data Collection (965DataGate)",
            "description": "Licensed public opinion polling data collections searchable in CLIO via 965DataGate. Migrating to Redivis CDP.",
            "platform": "CLIO Catalog",
            "access_level": "Columbia-Licensed",
            "index_key": "965DataGate",
            "manager": "RDS Librarian",
            "language": "English"
        },
        {
            "id": "clio_965_elections",
            "title": "Licensed Election Data Collection (965DataGate)",
            "description": "Licensed aggregate election and voting behavior datasets indexed in CLIO under 965DataGate.",
            "platform": "CLIO Catalog",
            "access_level": "Columbia-Licensed",
            "index_key": "965DataGate",
            "manager": "RDS Librarian",
            "language": "English"
        },
        {
            "id": "open_nasa_climate",
            "title": "NASA Earth Science & Climate Open Datasets",
            "description": "Open source satellite observations, atmosphere, and climate datasets from NASA. Note: Open source datasets do not have CLIO catalog records.",
            "platform": "Open Source Repository",
            "access_level": "Open Access",
            "manager": "Open NASA Portal",
            "language": "English"
        },
        {
            "id": "open_amazon_biodiversity",
            "title": "Amazon Rainforest Climate & Biodiversity Corpus (AI CoP)",
            "description": "Multilingual complex research dataset on climate models, deforestation, and Amazon rainforest ecosystem biodiversity.",
            "platform": "CLIO AI Enhanced Repository",
            "access_level": "Columbia-Licensed",
            "manager": "Environmental Science Library & AI CoP",
            "language": "Portuguese / English",
            "upvotes": 14,
            "downvotes": 0
        },
        {
            "id": "open_barrier_reef",
            "title": "Great Barrier Reef Environmental Chemistry Collection (AI CoP)",
            "description": "Interdisciplinary environmental chemistry research on ocean acidification, coral reef bleaching, and Great Barrier Reef conservation efforts.",
            "platform": "CLIO AI Enhanced Repository",
            "access_level": "Open Access",
            "manager": "Chemistry & Earth Sciences Library",
            "language": "English",
            "upvotes": 22,
            "downvotes": 1
        },
        {
            "id": "clio_multilingual_global",
            "title": "Multilingual Global Academic Literature Corpus (AI CoP)",
            "description": "Cross-lingual academic literature collection across French, Spanish, German, Portuguese, and Chinese for automated translation search.",
            "platform": "CLIO AI Enhanced Repository",
            "access_level": "Columbia-Licensed",
            "manager": "Global Studies Librarian & CUIT AI",
            "language": "Multilingual (FR/ES/DE/ZH/PT)",
            "upvotes": 18,
            "downvotes": 0
        }
    ]
    for ds in clio_datasets:
        ds["embedding"] = generate_embedding(ds["description"])
    return clio_datasets

def mock_ingest_redivis():
    """Ingest Columbia Data Platform (Redivis) datasets."""
    logger.info("Ingesting from Redivis / Columbia Data Platform (CDP)...")
    redivis_datasets = [
        {
            "id": "cdp_hcup",
            "title": "HCUP Healthcare Cost and Utilization Project",
            "description": "Restricted access hospital inpatient and outpatient medical campus dataset. Paid by faculty across Morningside & Medical campuses, purchased and administered by Jeremiah.",
            "platform": "Redivis (Columbia Data Platform)",
            "access_level": "Restricted",
            "manager": "Jeremiah",
            "url": "https://columbia.redivis.com/cul_hcup",
            "language": "English",
            "project_permissions": ["Restricted Access", "DUA Required", "Jeremiah Custodian Approval"]
        },
        {
            "id": "cdp_l2_voter",
            "title": "L2 Micro-Level Election Voter Data",
            "description": "Granular micro-level election voter registration and turnout dataset managed by Population Research Center (CPRC). Excluded from CLIO search.",
            "platform": "Redivis (Columbia Data Platform)",
            "access_level": "Restricted",
            "manager": "Jeremiah & Ashley (CPRC / CUIT)",
            "url": "https://columbia.redivis.com/CPRC/datasets",
            "language": "English",
            "project_permissions": ["CPRC Approval Required", "Restricted Microdata DUA"]
        },
        {
            "id": "cdp_ipums_census",
            "title": "IPUMS Restricted Access Full Count US Census (1790-1950)",
            "description": "Full count US decennial census microdata (1790-1950) managed by Population Research Center (CPRC) & CUIT engineer Ashley. Excluded from default CLIO search.",
            "platform": "Redivis (Columbia Data Platform)",
            "access_level": "Restricted",
            "manager": "Jeremiah & Ashley (CPRC / CUIT)",
            "url": "https://usa.ipums.org/usa/full_count/restricted_full_count.shtml",
            "language": "English",
            "project_permissions": ["IPUMS Authorization Required", "CPRC Data Engineer Review"]
        },
        {
            "id": "dataset_ciesin_earth",
            "title": "Columbia CIESIN Data Catalog (Data of the Earth)",
            "description": "Socioeconomic and environmental spatial data catalog managed by Center for International Earth Science Information Network (CIESIN) for SIPA's MPA-ESP program.",
            "platform": "Redivis (Columbia Data Platform)",
            "access_level": "Columbia-Licensed",
            "manager": "RDS Librarian & CIESIN",
            "language": "English",
            "url": "https://ciesin.columbia.edu/content/data"
        },
        {
            "id": "cdp_geospatial_eric",
            "title": "Licensed Geospatial & Spatial Analytics Datasets",
            "description": "Licensed GIS maps, boundary files, and spatial layers managed by Eric. Migrated to Redivis CDP.",
            "platform": "Redivis (Columbia Data Platform)",
            "access_level": "Columbia-Licensed",
            "manager": "Eric",
            "language": "English",
            "url": "https://columbia.redivis.com/geospatial"
        },
        {
            "id": "cdp_text_moacir",
            "title": "Textual & Computational Linguistics Corpus",
            "description": "Licensed text mining, linguistic corpora, and digital humanities datasets managed by Moacir. Migrated to Redivis CDP.",
            "platform": "Redivis (Columbia Data Platform)",
            "access_level": "Columbia-Licensed",
            "manager": "Moacir",
            "language": "Multilingual",
            "url": "https://columbia.redivis.com/linguistics"
        }
    ]
    for ds in redivis_datasets:
        ds["embedding"] = generate_embedding(ds["description"])
    return redivis_datasets

def mock_ingest_libguides():
    """Ingest RDS & Subject Specialist Libguides."""
    logger.info("Ingesting from Libguides (RDS & Subject Guides)...")
    libguides = [
        {
            "id": "lg_international_sipa",
            "title": "International Data Guide",
            "description": "Contains 'Data of the Earth' section for SIPA's MPA-ESP program, linking to Columbia CIESIN data catalog.",
            "program": "SIPA MPA-ESP",
            "url": "https://guides.library.columbia.edu/internationaldata",
            "language": "English",
            "key_sections": ["Data of the Earth", "Columbia CIESIN Data Catalog"]
        },
        {
            "id": "lg_datatools_med",
            "title": "Data Analysis Tools Guide",
            "description": "Features two bio-stats books by Rafael A. Irizarry under the 'R' tab, specifically for Medical Campus R users.",
            "program": "Medical Campus",
            "url": "https://guides.library.columbia.edu/datatools/r",
            "language": "English",
            "key_sections": ["R Tab", "Rafael A. Irizarry Bio-Stats"]
        },
        {
            "id": "lg_numeric_data",
            "title": "Numeric Data Collection Guide",
            "description": "Curated index of Columbia licensed numeric datasets searchable in CLIO via '965DataGate' and migrating to Redivis CDP.",
            "program": "Research Data Services (RDS)",
            "url": "https://guides.library.columbia.edu/numeric/home",
            "language": "English"
        },
        {
            "id": "lg_opinion_poll",
            "title": "Public Opinion Poll Data Guide",
            "description": "Curated guide for public opinion polling data collections, survey archives, and electoral sentiment datasets.",
            "program": "Political Science & RDS",
            "url": "https://guides.library.columbia.edu/opinionpolldata",
            "language": "English"
        },
        {
            "id": "lg_election_data",
            "title": "Election Data Guide",
            "description": "Guides election data discovery, including L2 voter microdata and IPUMS restricted access decennial census datasets.",
            "program": "Political Science & CPRC",
            "url": "https://guides.library.columbia.edu/ElectionData/",
            "language": "English"
        },
        {
            "id": "lg_subject_data_research",
            "title": "Data for Research Subject Guide",
            "description": "Master subject guide for data management, repository storage, and research data instructions.",
            "program": "Research Data Services (RDS)",
            "url": "https://library.columbia.edu/services/subject-guides.html#data",
            "language": "English"
        },
        {
            "id": "lg_subject_business",
            "title": "Business Data Subject Guide",
            "description": "Discipline-oriented business, finance, corporate, and market data guide created by Business Librarians.",
            "program": "Business School",
            "url": "https://library.columbia.edu/services/subject-guides.html#business",
            "language": "English"
        },
        {
            "id": "lg_subject_math_stats",
            "title": "Math & Statistics Subject Guide",
            "description": "Discipline-oriented mathematics, statistical computing, and quantitative data guide.",
            "program": "Math & Statistics Department",
            "url": "https://library.columbia.edu/services/subject-guides.html#math-statistics",
            "language": "English"
        }
    ]
    for lg in libguides:
        lg["embedding"] = generate_embedding(lg["description"])
    return libguides

if __name__ == "__main__":
    logger.info("Starting Complete Columbia Library Knowledge Graph Ingestion Pipeline (AI CoP Enhanced)")
    datasets = mock_ingest_clio() + mock_ingest_redivis()
    libguides = mock_ingest_libguides()

    logger.info(f"Successfully processed {len(datasets)} datasets and {len(libguides)} libguides.")

    with open("data/mock_graph_nodes.json", "w", encoding="utf-8") as f:
        json.dump({"datasets": datasets, "libguides": libguides}, f, indent=2)
    logger.info("Saved complete mock graph data to JSON.")
