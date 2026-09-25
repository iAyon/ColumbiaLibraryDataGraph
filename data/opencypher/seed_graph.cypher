// Columbia Library Knowledge Graph Seed Queries (OpenCypher / Neo4j / AWS Neptune)

CREATE (d:Dataset {id: 'clio_123', title: 'Public Opinion Poll Data 2020', platform: 'CLIO', access_level: 'Columbia-Licensed'});
CREATE (d:Dataset {id: 'cdp_hcup', title: 'HCUP Healthcare Cost and Utilization Project', platform: 'Redivis', access_level: 'Restricted'});
CREATE (d:Dataset {id: 'cdp_l2', title: 'L2 Voter Data', platform: 'Redivis', access_level: 'Restricted'});
CREATE (l:Libguide {id: 'lg_intl', title: 'International Data Guide', program: 'SIPA MPA-ESP'});
CREATE (l:Libguide {id: 'lg_med', title: 'Data Analysis Tools Guide', program: 'Medical Campus'});
CREATE (p:Platform {id: 'platform_clio', name: 'CLIO'});
CREATE (p:Platform {id: 'platform_redivis', name: 'Redivis'});
CREATE (s:SubjectSpecialist {id: 'spec_jeremiah', name: 'Jeremiah'});
MATCH (d:Dataset {id: 'clio_123'}), (p:Platform {id: 'platform_clio'}) CREATE (d)-[:HOSTED_ON]->(p);
MATCH (d:Dataset {id: 'cdp_hcup'}), (p:Platform {id: 'platform_redivis'}) CREATE (d)-[:HOSTED_ON]->(p);
MATCH (d:Dataset {id: 'cdp_hcup'}), (s:SubjectSpecialist {id: 'spec_jeremiah'}) CREATE (d)-[:MANAGED_BY]->(s);
MATCH (d:Dataset {id: 'cdp_l2'}), (p:Platform {id: 'platform_redivis'}) CREATE (d)-[:HOSTED_ON]->(p);
MATCH (d:Dataset {id: 'cdp_l2'}), (s:SubjectSpecialist {id: 'spec_jeremiah'}) CREATE (d)-[:MANAGED_BY]->(s);
