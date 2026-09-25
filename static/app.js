// Columbia Library Data Graph Application Controller

let currentRole = 'user';
let graphSimulation = null;

document.addEventListener('DOMContentLoaded', () => {
  fetchStats();
  loadGraphVisualization();
  setupEventListeners();
  loadAdminData();
});

// Setup Form Listeners
function setupEventListeners() {
  const searchForm = document.getElementById('search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      executeSearch();
    });
  }
}

// Role Switching Logic
function switchRole(role) {
  currentRole = role;
  document.getElementById('role-user-btn').classList.toggle('active', role === 'user');
  document.getElementById('role-admin-btn').classList.toggle('active', role === 'admin');

  document.getElementById('user-view').classList.toggle('active', role === 'user');
  document.getElementById('admin-view').classList.toggle('active', role === 'admin');

  if (role === 'admin') {
    loadAdminData();
  }
}

// Admin Tab Switching
function switchAdminTab(tabId) {
  document.querySelectorAll('.admin-tabs .tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));

  event.currentTarget.classList.add('active');
  document.getElementById(tabId).classList.add('active');
}

// Set Query from Chip Suggestions
function setQuery(text) {
  document.getElementById('search-input').value = text;
  executeSearch();
}

// Fetch Overview Stats
async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('stat-datasets').innerText = data.total_datasets || 0;
    document.getElementById('stat-libguides').innerText = data.total_libguides || 0;
    document.getElementById('stat-restricted').innerText = data.restricted_datasets || 0;
    document.getElementById('stat-platforms').innerText = (data.platforms || []).length;
  } catch (err) {
    console.error("Failed to fetch stats", err);
  }
}

// Execute GraphRAG Search Query
async function executeSearch() {
  const query = document.getElementById('search-input').value.trim();
  if (!query) return;

  const container = document.getElementById('results-container');
  const statusEl = document.getElementById('search-status');
  statusEl.innerText = "Searching Vector & Neptune Graph...";
  statusEl.style.color = "#06b6d4";

  container.innerHTML = `
    <div class="placeholder-state">
      <i class="fa-solid fa-spinner fa-spin"></i>
      <p>Encoding query vector and traversing AWS Neptune OpenCypher graph...</p>
    </div>
  `;

  try {
    const res = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });

    const data = await res.json();
    statusEl.innerText = "Completed";
    statusEl.style.color = "#10b981";

    renderSearchResults(data);
  } catch (err) {
    console.error("Search error", err);
    statusEl.innerText = "Error";
    statusEl.style.color = "#ef4444";
    container.innerHTML = `<div class="agent-alert restricted">Failed to execute discovery search. Server error.</div>`;
  }
}

// Render Search Results Cards
function renderSearchResults(data) {
  const container = document.getElementById('results-container');
  container.innerHTML = '';

  const topMatch = data.top_match;
  if (!topMatch) {
    container.innerHTML = `<div class="placeholder-state"><p>No relevant resources matched your query.</p></div>`;
    return;
  }

  // Top Match Card
  const isDataset = topMatch.type === 'Dataset';
  const isRestricted = topMatch.access_level === 'Restricted';

  let alertMarkup = '';
  if (isDataset) {
    if (isRestricted) {
      alertMarkup = `
        <div class="agent-alert restricted">
          <strong><i class="fa-solid fa-triangle-exclamation"></i> AGENT ALERT: RESTRICTED ACCESS DATASET</strong>
          <span>This dataset is hosted on <strong>${topMatch.platform}</strong> and is excluded from standard CLIO searches.</span>
          <span>👉 <strong>Action Required:</strong> Contact custodian <strong>${topMatch.manager || 'Data Manager'}</strong> to request credentials on Redivis.</span>
        </div>
      `;
    } else {
      alertMarkup = `
        <div class="agent-alert licensed">
          <strong><i class="fa-solid fa-circle-check"></i> COLUMBIA-LICENSED ACCESS</strong>
          <span>Available to Columbia affiliates via UNI authentication on CLIO catalog.</span>
        </div>
      `;
    }
  } else {
    alertMarkup = `
      <div class="agent-alert licensed">
        <strong><i class="fa-solid fa-lightbulb"></i> CURATED RESEARCH LIBGUIDE</strong>
        <span>Targeted for program: <strong>${topMatch.program || 'General'}</strong>. Refer to guide tabs for analysis workflows.</span>
      </div>
    `;
  }

  const cypherQuery = data.neptune_graph_context ? data.neptune_graph_context.cypher_query : '';

  const cardHtml = `
    <div class="match-card top-match">
      <div class="match-header">
        <div class="match-title">[${topMatch.type}] ${topMatch.title}</div>
        <span class="score-badge"><i class="fa-solid fa-bullseye"></i> ${(topMatch.score * 100).toFixed(1)}% Match</span>
      </div>
      <p class="match-desc">${topMatch.description}</p>
      ${alertMarkup}
      ${cypherQuery ? `<div class="cypher-box"><strong>AWS Neptune Cypher Traversal:</strong><br>${cypherQuery}</div>` : ''}
    </div>
  `;

  container.insertAdjacentHTML('beforeend', cardHtml);

  // Render secondary matches
  const otherMatches = (data.all_results || []).slice(1);
  if (otherMatches.length > 0) {
    container.insertAdjacentHTML('beforeend', `<h4 style="margin-top: 1rem; color: var(--text-muted); font-size: 0.85rem;">Other Relevant Matches</h4>`);
    otherMatches.forEach(item => {
      container.insertAdjacentHTML('beforeend', `
        <div class="match-card" style="padding: 0.85rem;">
          <div class="match-header">
            <div class="match-title" style="font-size: 0.95rem;">[${item.type}] ${item.title}</div>
            <span class="score-badge" style="font-size: 0.7rem;">${(item.score * 100).toFixed(1)}%</span>
          </div>
          <p class="match-desc" style="font-size: 0.8rem; margin: 0;">${item.description}</p>
        </div>
      `);
    });
  }
}

// Load D3 Force-Directed Graph Visualization
async function loadGraphVisualization() {
  try {
    const res = await fetch('/api/graph');
    const data = await res.json();
    renderD3Graph(data.nodes, data.edges);
  } catch (err) {
    console.error("Failed to load graph visualization", err);
  }
}

function renderD3Graph(nodes, edges) {
  const container = document.getElementById('graph-canvas-container');
  const width = container.clientWidth || 600;
  const height = container.clientHeight || 450;

  d3.select("#graph-svg").selectAll("*").remove();
  const svg = d3.select("#graph-svg")
    .attr("viewBox", [0, 0, width, height]);

  const g = svg.append("g");

  // Zoom behavior
  svg.call(d3.zoom().on("zoom", (event) => {
    g.attr("transform", event.transform);
  }));

  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(edges).id(d => d.id).distance(100))
    .force("charge", d3.forceManyBody().strength(-250))
    .force("center", d3.forceCenter(width / 2, height / 2));

  // Draw Edges
  const link = g.append("g")
    .selectAll("line")
    .data(edges)
    .join("line")
    .attr("stroke", "rgba(255,255,255,0.15)")
    .attr("stroke-width", 1.5);

  // Draw Nodes
  const node = g.append("g")
    .selectAll("circle")
    .data(nodes)
    .join("circle")
    .attr("r", d => d.type === 'Dataset' ? 14 : d.type === 'Libguide' ? 12 : 9)
    .attr("fill", d => {
      if (d.type === 'Dataset') return '#6366f1';
      if (d.type === 'Libguide') return '#06b6d4';
      if (d.type === 'Platform') return '#f59e0b';
      return '#ec4899';
    })
    .attr("stroke", "#fff")
    .attr("stroke-width", 1.5)
    .call(drag(simulation));

  // Node Labels
  const labels = g.append("g")
    .selectAll("text")
    .data(nodes)
    .join("text")
    .text(d => d.label)
    .attr("font-size", "10px")
    .attr("fill", "#9ca3af")
    .attr("dx", 16)
    .attr("dy", 4);

  node.append("title").text(d => `${d.type}: ${d.label}`);

  simulation.on("tick", () => {
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    node
      .attr("cx", d => d.x)
      .attr("cy", d => d.y);

    labels
      .attr("x", d => d.x)
      .attr("y", d => d.y);
  });
}

function drag(simulation) {
  function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    event.subject.fx = event.subject.x;
    event.subject.fy = event.subject.y;
  }
  function dragged(event) {
    event.subject.fx = event.x;
    event.subject.fy = event.y;
  }
  function dragended(event) {
    if (!event.active) simulation.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
  }
  return d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended);
}

// Load Admin Datasets & Libguides Tables
async function loadAdminData() {
  loadAdminDatasets();
  loadAdminLibguides();
}

async function loadAdminDatasets() {
  const tbody = document.getElementById('admin-datasets-tbody');
  try {
    const res = await fetch('/api/admin/datasets');
    const datasets = await res.json();
    tbody.innerHTML = '';
    if (datasets.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center">No datasets in graph.</td></tr>`;
      return;
    }
    datasets.forEach(ds => {
      tbody.innerHTML += `
        <tr>
          <td><code>${ds.id}</code></td>
          <td><strong>${ds.title}</strong></td>
          <td><span class="badge badge-accent">${ds.platform || 'CLIO'}</span></td>
          <td><span class="badge ${ds.access_level === 'Restricted' ? 'badge-warning' : 'badge-success'}">${ds.access_level}</span></td>
          <td>${ds.manager || 'N/A'}</td>
          <td>
            <button class="btn btn-sm btn-danger" onclick="deleteDataset('${ds.id}')"><i class="fa-solid fa-trash"></i> Delete</button>
          </td>
        </tr>
      `;
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Failed to load datasets.</td></tr>`;
  }
}

async function loadAdminLibguides() {
  const tbody = document.getElementById('admin-libguides-tbody');
  try {
    const res = await fetch('/api/admin/libguides');
    const libguides = await res.json();
    tbody.innerHTML = '';
    if (libguides.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center">No libguides in graph.</td></tr>`;
      return;
    }
    libguides.forEach(lg => {
      tbody.innerHTML += `
        <tr>
          <td><code>${lg.id}</code></td>
          <td><strong>${lg.title}</strong></td>
          <td><span class="badge badge-accent">${lg.program || 'General'}</span></td>
          <td>${lg.description}</td>
          <td>
            <button class="btn btn-sm btn-danger" onclick="deleteLibguide('${lg.id}')"><i class="fa-solid fa-trash"></i> Delete</button>
          </td>
        </tr>
      `;
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Failed to load libguides.</td></tr>`;
  }
}

// Delete Handlers
async function deleteDataset(id) {
  if (!confirm(`Delete dataset ${id}?`)) return;
  await fetch(`/api/admin/datasets/${id}`, { method: 'DELETE' });
  loadAdminDatasets();
  fetchStats();
  loadGraphVisualization();
}

async function deleteLibguide(id) {
  if (!confirm(`Delete libguide ${id}?`)) return;
  await fetch(`/api/admin/libguides/${id}`, { method: 'DELETE' });
  loadAdminLibguides();
  fetchStats();
  loadGraphVisualization();
}

// Live Ingestion Sync Trigger
async function triggerLiveIngest() {
  const logEl = document.getElementById('ingest-log-output');
  logEl.innerText = "Triggering live API connectors (CLIO 965DataGate API, Redivis API, Springshare Libguides API)...\nBuilding vector embeddings...";

  try {
    const res = await fetch('/api/admin/ingest', { method: 'POST' });
    const data = await res.json();

    logEl.innerText = JSON.stringify(data, null, 2);
    loadAdminDatasets();
    fetchStats();
    loadGraphVisualization();
  } catch (err) {
    logEl.innerText = "Failed to sync API connectors.";
  }
}

// Run Cypher Console Query
async function runCypherQuery() {
  const query = document.getElementById('cypher-input').value;
  const resultEl = document.getElementById('cypher-result');
  resultEl.innerText = "Executing query against AWS Neptune endpoint...";

  try {
    const res = await fetch('/api/admin/cypher', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const data = await res.json();
    resultEl.innerText = JSON.stringify(data, null, 2);
  } catch (err) {
    resultEl.innerText = "Cypher execution error.";
  }
}

// Modal Form Controls
function openAddModal(type) {
  document.getElementById('modal-node-type').value = type;
  document.getElementById('modal-title').innerText = type === 'dataset' ? 'Add New Dataset Node' : 'Add New Libguide Node';
  document.getElementById('dataset-fields').style.display = type === 'dataset' ? 'block' : 'none';
  document.getElementById('libguide-fields').style.display = type === 'libguide' ? 'block' : 'none';

  document.getElementById('modal-form').reset();
  document.getElementById('item-modal').classList.add('active');
}

function closeModal() {
  document.getElementById('item-modal').classList.remove('active');
}

async function handleModalSubmit(e) {
  e.preventDefault();
  const type = document.getElementById('modal-node-type').value;

  if (type === 'dataset') {
    const payload = {
      title: document.getElementById('modal-input-title').value,
      description: document.getElementById('modal-input-description').value,
      platform: document.getElementById('modal-input-platform').value,
      access_level: document.getElementById('modal-input-access').value,
      manager: document.getElementById('modal-input-manager').value
    };
    await fetch('/api/admin/datasets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  } else {
    const payload = {
      title: document.getElementById('modal-input-title').value,
      description: document.getElementById('modal-input-description').value,
      program: document.getElementById('modal-input-program').value
    };
    await fetch('/api/admin/libguides', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  }

  closeModal();
  loadAdminData();
  fetchStats();
  loadGraphVisualization();
}
