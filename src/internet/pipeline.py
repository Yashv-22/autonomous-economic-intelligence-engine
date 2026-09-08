"""
Internet Acquisition Pipeline.
Orchestrates end-to-end Internet intelligence:
Query Planning -> Discovery (Agent Reach multi-channel) -> Acquisition -> Normalization -> Provenance Tagging.
"""

from typing import List, Dict, Any, Optional
from src.internet.discovery.engine import DiscoveryEngine
from src.internet.acquisition.engine import AcquisitionEngine
from src.internet.normalization.engine import NormalizationEngine, NormalizedSourceDocument
from src.internet.provenance.tracker import InternetProvenanceTracker
from src.models.schemas import SourceSpan, ProvenanceMetadata
from src.provenance.ledger import ProvenanceLedger
from src.core.identifiers import compute_sha256
from src.core.logging import logger


class InternetAcquisitionPipeline:
    """
    Unified Internet Intelligence & Acquisition Pipeline.
    Encapsulates Agent Reach and external capability providers behind stable internal interfaces.
    """

    def __init__(
        self,
        discovery: Optional[DiscoveryEngine] = None,
        acquisition: Optional[AcquisitionEngine] = None,
        normalization: Optional[NormalizationEngine] = None,
        provenance_tracker: Optional[InternetProvenanceTracker] = None,
    ):
        self.discovery = discovery or DiscoveryEngine()
        self.acquisition = acquisition or AcquisitionEngine()
        self.normalization = normalization or NormalizationEngine()
        self.provenance_tracker = provenance_tracker or InternetProvenanceTracker()

    def execute(
        self,
        queries: List[str],
        max_sources: int = 5,
        channel: Optional[str] = None,
    ) -> List[SourceSpan]:
        """
        Execute full autonomous acquisition lifecycle from queries to verifiable spans.
        """
        logger.info(f"InternetPipeline: Executing internet acquisition for {len(queries)} queries (Max sources: {max_sources})")

        # 1. Discovery across Agent Reach multi-channel and search engines
        discovered_items = self.discovery.discover_sources(
            queries=queries,
            budget_per_query=max_sources,
            channel=channel,
        )
        if not discovered_items:
            logger.info("InternetPipeline: No new remote sources discovered.")
            return []

        # 2. Acquisition with SSRF defense and prompt injection containment
        fetched_sources = self.acquisition.acquire_sources(
            sources=discovered_items,
            max_sources=max_sources,
        )
        if not fetched_sources:
            logger.info("InternetPipeline: No sources could be fetched successfully.")
            return []

        # 3. Normalization into clean text chunks
        normalized_docs = self.normalization.normalize(fetched_sources)

        # 4. Provenance tracking and cryptographic Merkle leaf generation
        source_spans = self.provenance_tracker.track_and_register(normalized_docs)

        logger.info(f"InternetPipeline: Successfully produced {len(source_spans)} verifiable spans.")
        return source_spans

