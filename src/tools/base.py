"""
Base Tool Interface and Abstract Definitions.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from src.models.schemas import ToolPermission, ToolResult
from src.core.logging import logger


class BaseTool(ABC):
    """Abstract base class for all system tools."""

    name: str
    description: str
    permission_level: ToolPermission = ToolPermission.READ_ONLY
    requires_network: bool = False
    timeout_seconds: float = 15.0

    @abstractmethod
    def run(self, **kwargs) -> Any:
        """Execute the tool's core logic. Must be implemented by subclasses."""
        pass

    def execute(self, **kwargs) -> ToolResult:
        """Safely wrap tool execution with latency tracking and error handling."""
        start_time = time.perf_counter()
        try:
            output = self.run(**kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=output,
                output=output,
                execution_time_ms=round(duration_ms, 2),
                output_summary=f"Tool '{self.name}' executed successfully.",
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Tool '{self.name}' failed: {e}", exc_info=True)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                execution_time_ms=round(duration_ms, 2),
                output_summary=f"Tool '{self.name}' failed: {e}",
            )
