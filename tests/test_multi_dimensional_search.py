"""
Unit tests for Multi-Dimensional Query Generation.
"""

import unittest
from src.research.query_generation.multi_dimensional import MultiDimensionalQueryGenerator


class TestMultiDimensionalSearch(unittest.TestCase):

    def test_query_generation_all_dimensions(self):
        queries = MultiDimensionalQueryGenerator.generate_queries(
            topic="AI-era operating model redesign",
            max_queries=15,
        )
        self.assertGreaterEqual(len(queries), 7)
        dimensions = {q.dimension for q in queries}
        self.assertIn("academic", dimensions)
        self.assertIn("economic", dimensions)
        self.assertIn("negative_evidence", dimensions)
        self.assertIn("organizational", dimensions)

    def test_prioritization_of_disconfirming_evidence(self):
        queries = MultiDimensionalQueryGenerator.generate_queries(
            topic="Agentic AI operating models",
            max_queries=10,
        )
        # Verify negative evidence has high priority
        neg_queries = [q for q in queries if q.dimension == "negative_evidence"]
        self.assertTrue(len(neg_queries) > 0)
        self.assertGreaterEqual(neg_queries[0].priority, 1.1)


if __name__ == "__main__":
    unittest.main()
