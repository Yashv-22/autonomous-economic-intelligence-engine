"""
Unit tests for Raw and Normalized Corpus Storage.
"""

import unittest
import tempfile
import os
from src.storage.raw_corpus import RawCorpusManager
from src.storage.normalized_corpus import NormalizedCorpusManager
from src.internet.providers.base import FetchResult
from src.models.schemas import SourceSpan
from src.core.identifiers import compute_sha256


class TestStorageLayer(unittest.TestCase):

    def setUp(self):
        self.raw_dir = tempfile.mkdtemp()
        self.norm_dir = tempfile.mkdtemp()
        self.raw_mgr = RawCorpusManager(base_dir=self.raw_dir)
        self.norm_mgr = NormalizedCorpusManager(base_dir=self.norm_dir)

    def test_raw_corpus_persistence(self):
        content = b"<html><body>McKinsey QuantumBlack Report 2026</body></html>"
        fetch_res = FetchResult(
            url="https://mckinsey.com/qb",
            final_url="https://mckinsey.com/qb",
            status_code=200,
            content_type="text/html",
            raw_content=content,
            content_hash=compute_sha256(content),
            size_bytes=len(content),
        )
        saved_path = self.raw_mgr.store_raw_artifact(fetch_res)
        self.assertTrue(os.path.exists(saved_path))
        
        retrieved_bytes = self.raw_mgr.get_raw_artifact(fetch_res.content_hash)
        self.assertEqual(retrieved_bytes, content)

    def test_normalized_corpus_persistence(self):
        span = SourceSpan(
            document_name="test_doc.html",
            document_hash="doc_hash_123",
            page_or_section="Section 1",
            paragraph_index=0,
            text="84% of enterprises miss projected AI returns.",
            span_hash=compute_sha256("84% of enterprises miss projected AI returns."),
        )
        doc_path = self.norm_mgr.store_normalized_document(
            document_hash="doc_hash_123",
            document_name="test_doc.html",
            source_url="https://example.com/test",
            spans=[span],
        )
        self.assertTrue(os.path.exists(doc_path))
        doc_data = self.norm_mgr.get_normalized_document("doc_hash_123")
        self.assertEqual(doc_data["total_spans"], 1)
        self.assertEqual(doc_data["spans"][0]["span_hash"], span.span_hash)


if __name__ == "__main__":
    unittest.main()
