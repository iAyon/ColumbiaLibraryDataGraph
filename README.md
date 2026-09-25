# Columbia Library Data Graph

This repository contains the foundational architecture for the Columbia Library Data Graph project, a system designed to solve data fragmentation and discovery issues across library resources (Libguides, CLIO, Redivis).

This architecture heavily borrows from the agentic Knowledge Graph (KG) patterns established in the **AutoClimDS** project.

## Problem Statement

Columbia Library affiliates face a fragmented data ecosystem:
1.  **Libguides:** Created by subject specialists or RDS, containing valuable links, but scattered and distinct from the main catalog.
2.  **CLIO:** The main catalog (e.g., `965DataGate`), which indexes licensed datasets but *not* open-source datasets (NASA, Census) or restricted datasets.
3.  **Redivis (Columbia Data Platform):** Hosts specific datasets, including highly restricted ones (HCUP, L2 Voter Data, IPUMS) that are invisible to CLIO.

Students often don't know *what* exists or *where* to find it, especially when data is paid for by specific faculty and managed on isolated platforms.

## Solution Architecture: The Knowledge Graph & Agent

We solve this using a Knowledge Graph paired with a Data Discovery Agent, using the exact technologies proven in climate data science:

1.  **Ontology (Graph Schema):** We map the relationships between `Libguides`, `Datasets`, `SubjectSpecialists`, and `Platforms`.
2.  **Vector Embeddings:** We use the state-of-the-art `BAAI/bge-small-en-v1.5` model to encode the text of Libguides and dataset descriptions into mathematical vectors. This enables **semantic search** (e.g., a student searching "medical bio-stats" will instantly match Rafael A. Irizarry's books mentioned in the RDS R Libguide).
3.  **Agentic Logic:** A Python agent evaluates search results. If it detects a match for a `Restricted` dataset hosted on `Redivis` (like the L2 voter data), it programmatically warns the user and instructs them to contact the specific data manager (e.g., Jeremiah).

## Directory Structure

*   `docs/ontology.md`: The structural design of the Knowledge Graph nodes and edges.
*   `src/ingest_metadata.py`: A script simulating the ingestion of data from CLIO, Redivis, and Springshare Libguides, and the generation of vector embeddings.
*   `src/library_agent.py`: A prototype discovery agent demonstrating semantic search and access control routing.
*   `data/`: Directory for storing the generated mock graph JSON.

## Setup and Quick Start

1.  **Install requirements:**
    ```bash
    pip install sentence-transformers numpy
    ```

2.  **Run the ingestion pipeline (Build the Graph):**
    ```bash
    python src/ingest_metadata.py
    ```
    *This will create the `data/mock_graph_nodes.json` file populated with vectors.*

3.  **Run the Discovery Agent (Test the Search):**
    ```bash
    python src/library_agent.py
    ```
    *Watch how the agent correctly identifies restricted Redivis data and routes the user based on natural language queries!*

## Next Steps for the AI Community of Practice

1.  **Graph Database Integration:** Transition the output from `mock_graph_nodes.json` to OpenCypher CSV format and load it into a graph database like Neo4j or AWS Neptune.
2.  **CLIO API / Springshare API Integration:** Replace the mock ingestion data with live API calls to CLIO, Redivis, and the Springshare (Libguides) API.
3.  **CLIO LLM Project Integration:** As discussed by Rob in the AI Community of Practice, this Knowledge Graph is the perfect backend for an LLM chatbot. Instead of the LLM hallucinating answers, it can execute a vector search against this Graph, retrieve the exact access protocols (e.g., "Contact Jeremiah for L2"), and generate a perfectly grounded response for the student.
