from __future__ import annotations

from typing import Any, List

from orchestration.agents.base import BaseAgent
from orchestration.models.agent_models import AgentResult, ToolUsageRecord
from orchestration.models.workflow_models import WorkflowContext
from orchestration.registries.tools import ToolRegistry


class MemoryAgent(BaseAgent):
    """Only component allowed to read/write shared memory for the workflow."""

    name = "memory"

    def __init__(self, engine: Any, tool_registry: ToolRegistry) -> None:
        self.engine = engine
        self.tools = tool_registry

    def execute(self, ctx: WorkflowContext) -> AgentResult:
        tool_usage: List[ToolUsageRecord] = []

        if ctx.interaction is not None:
            _, dur, err = self.tools.execute(
                "memory", operation="put_interaction", interaction=ctx.interaction
            )
            tool_usage.append(
                ToolUsageRecord("memory", err is None, dur, summary="stored interaction", error=err)
            )

        memory_data, dur, err = self.tools.execute("memory", operation="get", customer_id=ctx.customer_id)
        tool_usage.append(
            ToolUsageRecord(
                "memory",
                err is None,
                dur,
                summary=f"{len((memory_data or {}).get('learned_insights', []))} insights",
                error=err,
            )
        )

        lessons, dur2, err2 = self.tools.execute(
            "memory",
            operation="lessons",
            customer_id=ctx.customer_id,
            domain=ctx.domain,
        )
        tool_usage.append(
            ToolUsageRecord(
                "memory",
                err2 is None,
                dur2,
                summary=f"{len(lessons or [])} lessons",
                error=err2,
            )
        )

        insight_count = len((memory_data or {}).get("learned_insights", []))
        return AgentResult(
            agent_name=self.name,
            success=err is None,
            confidence=0.9 if insight_count > 0 else 0.6,
            decision="memory_loaded",
            reason=f"Retrieved {insight_count} memory insights for bias and learning",
            data={"memory": memory_data, "lessons": lessons},
            tool_usage=tool_usage,
        )
