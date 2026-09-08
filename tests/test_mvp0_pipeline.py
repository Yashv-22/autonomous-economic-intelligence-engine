"""
End-to-End Integration Test for MVP-0 Pipeline.
"""

import os
import gc
import unittest
import tempfile
import json
from src.cli.run_mvp0 import run_mvp0_pipeline


class TestMVP0Pipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = os.path.join(self.temp_dir.name, "output")
        self.db_path = os.path.join(self.output_dir, "test_ledger.db")

    def tearDown(self):
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_pipeline_execution(self):
        dossier = run_mvp0_pipeline(
            input_dir=".",
            output_dir=self.output_dir,
            db_path=self.db_path,
        )

        self.assertIsNotNone(dossier)
        self.assertGreater(dossier.total_documents_ingested, 0)
        self.assertGreater(dossier.total_claims_extracted, 10)
        self.assertGreater(len(dossier.verified_contradictions), 0)
        self.assertGreater(len(dossier.hypothesized_problems), 0)

        # Verify output files
        json_file = os.path.join(self.output_dir, "mvp0_claims_ledger.json")
        md_file = os.path.join(self.output_dir, "mvp0_problem_dossier.md")

        self.assertTrue(os.path.exists(self.db_path))
        self.assertTrue(os.path.exists(json_file))
        self.assertTrue(os.path.exists(md_file))

        # Check JSON integrity
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["dossier_id"], dossier.dossier_id)

        # Check Markdown content
        with open(md_file, "r", encoding="utf-8") as f:
            md_content = f.read()
        self.assertIn("MVP-0 Research & Problem Dossier", md_content)
        self.assertIn("Verified Cross-Source Analytical Contradictions", md_content)


if __name__ == "__main__":
    unittest.main()
