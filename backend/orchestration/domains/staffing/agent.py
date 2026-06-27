"""Staffing domain agent — enriches interaction context for placement workflows."""

from __future__ import annotations

from typing import Any

from orchestration.agents.base import BaseAgent
from orchestration.models.agent_models import AgentResult
from orchestration.models.workflow_models import WorkflowContext


class StaffingDomainAgent(BaseAgent):
    name = "staffing_domain"

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def execute(self, ctx: WorkflowContext) -> AgentResult:
        if ctx.interaction is None:
            return AgentResult(
                agent_name=self.name,
                success=False,
                decision="skipped",
                reason="No interaction",
            )

        text = ctx.interaction.canonical_text.lower()
        topics = list(ctx.interaction.enriched_context.topics)

        staffing_signals = {
            "fill_rate": any(k in text for k in ("fill rate", "time-to-fill", "open req", "requisition")),
            "candidate_quality": any(k in text for k in ("candidate", "interview", "submittal", "pipeline")),
            "client_urgency": any(k in text for k in ("urgent", "asap", "start date", "deadline")),
            "compliance": any(k in text for k in ("background check", "compliance", "credential", "license")),
        }

        for key, active in staffing_signals.items():
            if active and key.replace("_", " ") not in topics:
                topics.append(key.replace("_", " "))

        ctx.interaction.enriched_context.topics = topics
        analysis_text = ctx.interaction.enriched_context.analysis_text
        ctx.interaction.enriched_context.analysis_text = (
            f"{analysis_text}\n\n[Staffing domain: {', '.join(k for k, v in staffing_signals.items() if v) or 'general'}]"
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=0.78,
            decision="staffing_enriched",
            reason=f"Applied staffing domain signals: {[k for k, v in staffing_signals.items() if v]}",
            data=staffing_signals,
        )
