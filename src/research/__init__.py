"""
Research Subsystem Package.
Provides multi-dimensional query generation, autonomous discovery, research memory, and saturation tracking.
"""

from src.research.query_generation.multi_dimensional import (
    MultiDimensionalQueryGenerator,
    ResearchQuery,
)
from src.research.memory.session_store import (
    ResearchSessionStore,
    ResearchSessionState,
)
from src.research.saturation.tracker import (
    ResearchSaturationTracker,
    SaturationMetrics,
)
from src.research.gap_detector import ResearchGapDetector
from src.research.discovery.engine import AutonomousResearchEngine
from src.research.loop import AutonomousResearchLoop

__all__ = [
    "MultiDimensionalQueryGenerator",
    "ResearchQuery",
    "ResearchSessionStore",
    "ResearchSessionState",
    "ResearchSaturationTracker",
    "SaturationMetrics",
    "ResearchGapDetector",
    "AutonomousResearchEngine",
    "AutonomousResearchLoop",
]
