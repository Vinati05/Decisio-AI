from __future__ import annotations

from typing import Any, Dict, List, Optional

from orchestration.tools.base import BaseTool
from orchestration.tools.business_rule_tool import BusinessRuleTool
from orchestration.tools.crm_tool import CRMTool
from orchestration.tools.draft_email import DraftEmailTool
from orchestration.tools.knowledge_search import KnowledgeSearchTool
from orchestration.tools.memory_tool import MemoryTool


class ToolRegistry:
    """Planner requests tools through ToolRegistry — never imports tools directly."""

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def execute(self, name: str, **kwargs: Any) -> tuple[Any, float, Optional[str]]:
        tool = self.get(name)
        if tool is None:
            return None, 0.0, f"Tool not registered: {name}"
        return tool.run_safe(**kwargs)

    def list_tools(self) -> List[str]:
        return sorted(self._tools.keys())

    def health_report(self) -> Dict[str, Any]:
        return {name: tool.health() for name, tool in self._tools.items()}


def register_default_tools(
    knowledge_base: Any,
    crm_simulator: Any,
    memory_store: Any,
    business_rules: Dict[str, Any],
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(KnowledgeSearchTool(knowledge_base))
    registry.register(CRMTool(crm_simulator))
    registry.register(MemoryTool(memory_store))
    registry.register(BusinessRuleTool(business_rules))
    registry.register(DraftEmailTool())
    return registry
