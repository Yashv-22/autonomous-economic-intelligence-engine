"""
Search Tool implementation using MultiProviderSearchEngine.
"""

from typing import Dict, Any, List, Optional
from src.tools.base import BaseTool
from src.models.schemas import ToolPermission
from src.internet.search.engine import MultiProviderSearchEngine
from src.internet.providers.base import SearchResultItem


class SearchTool(BaseTool):
    """Executes live research search queries across web, academic, and industry providers."""

    name: str = "search_sources"
    description: str = "Searches live web, arXiv, and encyclopedic sources for research topics."
    permission_level: ToolPermission = ToolPermission.READ_ONLY
    requires_network: bool = True

    def __init__(self, search_engine: Optional[MultiProviderSearchEngine] = None):
        super().__init__()
        self.engine = search_engine or MultiProviderSearchEngine()

    def run(self, query: str = "", max_results: int = 10, dimension: Optional[str] = None, **kwargs) -> Any:
        """Execute multi-provider search query."""
        results: List[SearchResultItem] = self.engine.search(
            query=query,
            max_results=max_results,
            dimension=dimension,
        )
        return [r.dict() for r in results]
