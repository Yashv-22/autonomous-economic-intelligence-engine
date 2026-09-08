"""
Unit Tests for Document Ingestion & Cryptographic Provenance.
"""

import os
import unittest
import tempfile
from src.ingestion.document_parser import (
    PDFParser,
    DocxParser,
    TextParser,
    DocumentIngestionEngine,
    compute_sha256,
)
from src.ingestion.provenance import ProvenanceLedger


class TestIngestion(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sample_txt = os.path.join(self.temp_dir.name, "sample.md")
        with open(self.sample_txt, "w", encoding="utf-8") as f:
            f.write("# Introduction\n\nThis is a sample document for testing cryptographic provenance.\n\n"
                    "## Section 2\n\nSecond paragraph containing substantive test claims about operating models.")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sha256_computation(self):
        h1 = compute_sha256("test content")
        h2 = compute_sha256(b"test content")
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_text_parser(self):
        parser = TextParser()
        spans = parser.parse(self.sample_txt)
        self.assertGreaterEqual(len(spans), 2)
        self.assertEqual(spans[0].document_name, "sample.md")
        self.assertEqual(len(spans[0].document_hash), 64)
        self.assertEqual(len(spans[0].span_hash), 64)

    def test_provenance_ledger_verification(self):
        parser = TextParser()
        spans = parser.parse(self.sample_txt)
        ledger = ProvenanceLedger()
        merkle_root = ledger.register_spans(spans)

        self.assertIsNotNone(merkle_root)
        self.assertEqual(len(merkle_root), 64)

        # Valid span verification
        first_span = spans[0]
        self.assertTrue(ledger.verify_span(first_span.span_hash, first_span.text))

        # Tampered text verification
        self.assertFalse(ledger.verify_span(first_span.span_hash, first_span.text + " TAMPERED"))

    def test_workspace_pdf_and_docx_parsing(self):
        """Test parsing actual workspace files if present."""
        engine = DocumentIngestionEngine()
        pdf_path = "AI-Era Operating Model Redesign.pdf"
        docx_path = "AI_Era_Operating_Model_Redesign_2026_Research.docx"

        if os.path.exists(pdf_path):
            spans = engine.ingest_file(pdf_path)
            self.assertGreater(len(spans), 10)
            self.assertTrue(all(len(s.span_hash) == 64 for s in spans))

        if os.path.exists(docx_path):
            spans = engine.ingest_file(docx_path)
            self.assertGreater(len(spans), 5)


if __name__ == "__main__":
    unittest.main()
