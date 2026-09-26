import os
import unittest
import json
from app import app, load_graph_data

class TestColumbiaLibraryGraph(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_stats_endpoint(self):
        """Test GET /api/stats returns online status and valid counters."""
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data.get("status"), "online")
        self.assertGreater(data.get("total_datasets", 0), 0)
        self.assertGreater(data.get("total_libguides", 0), 0)

    def test_search_endpoint(self):
        """Test POST /api/search returns valid top match and graph context."""
        response = self.app.post('/api/search', 
                                json={"query": "Where can I find IPUMS census microdata for 1790 to 1950?"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsNotNone(data.get("top_match"))
        self.assertIn("IPUMS", data["top_match"]["title"])
        self.assertEqual(data["top_match"]["access_level"], "Restricted")

    def test_graph_endpoint(self):
        """Test GET /api/graph returns nodes and edges arrays for D3 visualizer."""
        response = self.app.get('/api/graph')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertGreater(len(data["nodes"]), 0)

    def test_feedback_endpoint(self):
        """Test POST /api/feedback records upvotes correctly."""
        data = load_graph_data()
        datasets = data.get("datasets", [])
        if datasets:
            first_id = datasets[0]["id"]
            response = self.app.post('/api/feedback', json={"id": first_id, "vote": "upvote"})
            self.assertEqual(response.status_code, 200)
            resp_data = json.loads(response.data)
            self.assertEqual(resp_data.get("status"), "success")

if __name__ == "__main__":
    unittest.main()
