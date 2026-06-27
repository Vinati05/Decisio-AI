from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from orchestration.models.agent_models import AgentResult
from orchestration.models.workflow_models import WorkflowContext

logger = logging.getLogger("decisio.agents")


class BaseAgent(ABC):
    name: str = "base_agent"

    @abstractmethod
    def execute(self, ctx: WorkflowContext) -> AgentResult:
        ...

    def run(self, ctx: WorkflowContext, execution_order: int) -> AgentResult:
        start = time.perf_counter()
        logger.info("[Agent] %s start order=%d", self.name, execution_order)
        try:
            result = self.execute(ctx)
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "[Agent] %s finish duration_ms=%.1f decision=%s confidence=%s",
                self.name,
                duration_ms,
                result.decision,
                result.confidence,
            )
            result.duration_ms = duration_ms  # type: ignore[attr-defined]
            result.execution_order = execution_order  # type: ignore[attr-defined]
            return result
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error("[Agent] %s error duration_ms=%.1f error=%s", self.name, duration_ms, exc)
            return AgentResult(
                agent_name=self.name,
                success=False,
                decision="failed",
                reason=str(exc),
                error=str(exc),
            )
