"""
Tool Registry and Permission Enforcement.
Registers, checks permissions, and executes system tools.
"""

from typing import Dict, List, Optional, Any
from src.tools.base import BaseTool, ToolResult, ToolPermission
from src.core.errors import ToolExecutionError, SecurityViolationError
from src.core.events import EventBus, SystemEvent, default_event_bus
from src.core.logging import logger

PERMISSION_RANKS = {
    ToolPermission.READ_ONLY: 1,
    "READ_ONLY": 1,
    ToolPermission.STATE_CHANGING: 2,
    "STATE_CHANGING": 2,
    ToolPermission.HIGH_RISK: 3,
    "HIGH_RISK": 3,
}


class ToolRegistry:
    """Central registry enforcing permission levels and caller verification for tools."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self._tools: Dict[str, BaseTool] = {}
        self.event_bus = event_bus or default_event_bus

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool in the registry."""
        self._tools[tool.name] = tool
        perm = getattr(tool, "permission_level", getattr(tool, "permission", ToolPermission.READ_ONLY))
        perm_name = perm.name if hasattr(perm, "name") else str(perm)
        logger.info(f"Registered tool: '{tool.name}' (Permission: {perm_name})")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Retrieve tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def invoke_tool(
        self,
        tool_name: str,
        caller_permission_level: Optional[ToolPermission] = None,
        caller_permission: Optional[ToolPermission] = None,
        **kwargs,
    ) -> ToolResult:
        """Alias for execute_tool."""
        return self.execute_tool(
            tool_name=tool_name,
            caller_permission_level=caller_permission_level,
            caller_permission=caller_permission,
            **kwargs,
        )

    def execute_tool(
        self,
        tool_name: str,
        caller_permission_level: Optional[ToolPermission] = None,
        caller_permission: Optional[ToolPermission] = None,
        **kwargs,
    ) -> ToolResult:
        """
        Execute tool with permission gating.
        Raises SecurityViolationError if caller permission level is insufficient.
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ToolExecutionError(f"Tool '{tool_name}' is not registered.")

        perm_level = caller_permission or caller_permission_level or ToolPermission.READ_ONLY
        tool_perm = getattr(tool, "permission_level", getattr(tool, "permission", ToolPermission.READ_ONLY))

        tool_rank = PERMISSION_RANKS.get(tool_perm, 1)
        caller_rank = PERMISSION_RANKS.get(perm_level, 1)

        # Permission verification
        if tool_rank > caller_rank:
            tool_name_str = tool_perm.name if hasattr(tool_perm, "name") else str(tool_perm)
            caller_name_str = perm_level.name if hasattr(perm_level, "name") else str(perm_level)
            err_msg = (
                f"Permission denied: Tool '{tool_name}' requires level {tool_name_str} "
                f"({tool_rank}), but caller has {caller_name_str} "
                f"({caller_rank})."
            )
            logger.error(err_msg)
            raise SecurityViolationError(err_msg)

        # Execute
        result = tool.execute(**kwargs)

        # Publish telemetry
        self.event_bus.publish(
            SystemEvent(
                event_type="TOOL_EXECUTED",
                payload={
                    "tool_name": tool_name,
                    "success": result.success,
                    "latency_ms": result.execution_time_ms,
                    "error": result.error,
                },
                agent_id=f"tool:{tool_name}",
            )
        )
        return result


# Global default registry with core tools pre-registered
default_tool_registry = ToolRegistry()

from src.tools.search_tool import SearchTool
from src.tools.fetch_tool import FetchTool
from src.tools.extract_tool import ExtractTool
from src.tools.crawl_tool import CrawlTool
from src.tools.agent_reach_tool import AgentReachTool

default_tool_registry.register_tool(SearchTool())
default_tool_registry.register_tool(FetchTool())
default_tool_registry.register_tool(ExtractTool())
default_tool_registry.register_tool(CrawlTool())
default_tool_registry.register_tool(AgentReachTool())
