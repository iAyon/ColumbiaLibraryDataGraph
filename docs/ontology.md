# Columbia Library Data Graph Ontology

This document defines the Knowledge Graph schema for the Columbia Library Data Discovery project, adapted from the AutoClimDS architecture.

## Nodes (Entities)

*   **Dataset:** Represents a specific collection of data.
    *   *Properties:* `id`, `title`, `description`, `embedding` (vector), `access_level` (Open, Columbia-Licensed, Restricted).
*   **Libguide:** Represents a curated research guide created by a librarian or subject specialist.
    *   *Properties:* `id`, `title`, `url`, `content_summary`, `embedding` (vector).
*   **Platform:** The hosting environment for the dataset.
    *   *Properties:* `name` (e.g., "CLIO", "Redivis/Columbia Data Platform", "External").
*   **SubjectSpecialist:** The librarian or data administrator responsible for a collection.
    *   *Properties:* `name`, `email`, `role`.
*   **AcademicProgram:** The specific school or program the data is relevant to.
    *   *Properties:* `name` (e.g., "SIPA MPA-ESP", "Medical Campus").

## Relationships (Edges)

*   `(Libguide)-[MENTIONS]->(Dataset)`
*   `(Dataset)-[HOSTED_ON]->(Platform)`
*   `(Dataset)-[MANAGED_BY]->(SubjectSpecialist)`
*   `(Libguide)-[CREATED_BY]->(SubjectSpecialist)`
*   `(Libguide)-[TARGETS_PROGRAM]->(AcademicProgram)`
*   `(Dataset)-[RELEVANT_TO]->(AcademicProgram)`
