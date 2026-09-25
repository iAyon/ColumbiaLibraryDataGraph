import json
import csv
import os

def export_opencypher():
    print("Exporting mock graph data to AWS Neptune OpenCypher format...")
    
    with open("data/mock_graph_nodes.json", "r") as f:
        graph_data = json.load(f)

    os.makedirs("data/opencypher", exist_ok=True)
    
    # 1. Export Dataset Nodes
    dataset_csv = "data/opencypher/datasets.csv"
    with open(dataset_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id:ID", "title:string", "description:string", "platform:string", "access_level:string", "manager:string", ":LABEL"])
        for ds in graph_data.get("datasets", []):
            writer.writerow([
                ds["id"],
                ds.get("title", ""),
                ds.get("description", ""),
                ds.get("platform", ""),
                ds.get("access_level", ""),
                ds.get("manager", ""),
                "Dataset"
            ])
    print(f"Wrote {dataset_csv}")

    # 2. Export Libguide Nodes
    libguide_csv = "data/opencypher/libguides.csv"
    with open(libguide_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id:ID", "title:string", "description:string", "program:string", ":LABEL"])
        for lg in graph_data.get("libguides", []):
            writer.writerow([
                lg["id"],
                lg.get("title", ""),
                lg.get("description", ""),
                lg.get("program", ""),
                "Libguide"
            ])
    print(f"Wrote {libguide_csv}")

    # 3. Export Platform & Specialist Nodes
    platforms = set()
    specialists = {}
    
    for ds in graph_data.get("datasets", []):
        if ds.get("platform"):
            platforms.add(ds["platform"])
        if ds.get("manager"):
            specialists[ds["manager"]] = f"spec_{ds['manager'].lower()}"

    platform_csv = "data/opencypher/platforms.csv"
    with open(platform_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id:ID", "name:string", ":LABEL"])
        for p in platforms:
            writer.writerow([f"platform_{p.lower().replace(' ', '_')}", p, "Platform"])
    print(f"Wrote {platform_csv}")

    specialist_csv = "data/opencypher/specialists.csv"
    with open(specialist_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id:ID", "name:string", ":LABEL"])
        for name, spec_id in specialists.items():
            writer.writerow([spec_id, name, "SubjectSpecialist"])
    print(f"Wrote {specialist_csv}")

    # 4. Export Relationships (Edges)
    edges_csv = "data/opencypher/edges.csv"
    with open(edges_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([":START_ID", ":END_ID", ":TYPE"])
        
        # Dataset -> Platform (HOSTED_ON)
        for ds in graph_data.get("datasets", []):
            if ds.get("platform"):
                platform_id = f"platform_{ds['platform'].lower().replace(' ', '_')}"
                writer.writerow([ds["id"], platform_id, "HOSTED_ON"])
            if ds.get("manager"):
                spec_id = specialists[ds["manager"]]
                writer.writerow([ds["id"], spec_id, "MANAGED_BY"])

    print(f"Wrote {edges_csv}")

    # 5. Export Standalone Cypher Seed File
    cypher_seed = "data/opencypher/seed_graph.cypher"
    with open(cypher_seed, "w", encoding="utf-8") as f:
        f.write("// Columbia Library Knowledge Graph Seed Queries (OpenCypher / Neo4j / AWS Neptune)\n\n")
        
        for ds in graph_data.get("datasets", []):
            f.write(f"CREATE (d:Dataset {{id: '{ds['id']}', title: '{ds['title']}', platform: '{ds.get('platform', '')}', access_level: '{ds.get('access_level', '')}'}});\n")
            
        for lg in graph_data.get("libguides", []):
            f.write(f"CREATE (l:Libguide {{id: '{lg['id']}', title: '{lg['title']}', program: '{lg.get('program', '')}'}});\n")
            
        for p in platforms:
            p_id = f"platform_{p.lower().replace(' ', '_')}"
            f.write(f"CREATE (p:Platform {{id: '{p_id}', name: '{p}'}});\n")

        for name, spec_id in specialists.items():
            f.write(f"CREATE (s:SubjectSpecialist {{id: '{spec_id}', name: '{name}'}});\n")

        # Edge creations
        for ds in graph_data.get("datasets", []):
            if ds.get("platform"):
                p_id = f"platform_{ds['platform'].lower().replace(' ', '_')}"
                f.write(f"MATCH (d:Dataset {{id: '{ds['id']}'}}), (p:Platform {{id: '{p_id}'}}) CREATE (d)-[:HOSTED_ON]->(p);\n")
            if ds.get("manager"):
                spec_id = specialists[ds["manager"]]
                f.write(f"MATCH (d:Dataset {{id: '{ds['id']}'}}), (s:SubjectSpecialist {{id: '{spec_id}'}}) CREATE (d)-[:MANAGED_BY]->(s);\n")
                
    print(f"Wrote {cypher_seed}")
    print("OpenCypher export complete!")

if __name__ == "__main__":
    export_opencypher()
