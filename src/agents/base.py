"""
Base Agent Interface & Autonomous Role Definition.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from src.models.schemas import ToolPermission
from src.tools.registry import ToolRegistry, default_tool_registry
from src.gateway.gateway import ModelGateway, default_model_gateway
from src.core.logging import logger


class AgentContext(BaseModel):
    """Execution context and memory passed to agents."""
    task_id: str
    correlation_id: str
    run_id: Optional[str] = None
    budget_tokens: int = 10000
    timeout_seconds: float = 60.0
    shared_blackboard: Dict[str, Any] = {}


class BaseAgent(ABC):
    """Abstract base class for specialized operating model agents."""

    name: str
    role: str
    description: str
    allowed_tools: List[str] = []
    permission_level: ToolPermission = ToolPermission.READ_ONLY

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        model_gateway: Optional[ModelGateway] = None,
    ):
        self.tool_registry = tool_registry or default_tool_registry
        self.model_gateway = model_gateway or default_model_gateway

    @abstractmethod
    def run(self, context: AgentContext, **kwargs) -> Any:
        """Execute the agent's core task."""
        pass

    def invoke_tool(self, context: AgentContext, tool_name: str, **kwargs) -> Any:
        """Safely invoke an authorized tool through the tool registry."""
        if tool_name not in self.allowed_tools:
            raise PermissionError(f"Agent '{self.name}' is not authorized to invoke tool '{tool_name}'")

        result = self.tool_registry.invoke_tool(
            tool_name=tool_name,
            caller_permission=self.permission_level,
            actor_id=self.name,
            correlation_id=context.correlation_id,
            **kwargs
        )
        if not result.success:
            logger.warning(f"Tool {tool_name} returned error: {result.error}")
        return result
