from __future__ import annotations

from typing import Any

from orchestration.agents.base import BaseAgent
from orchestration.models.agent_models import AgentResult, BusinessAnalysis
from orchestration.models.workflow_models import WorkflowContext


class AnalyzerAgent(BaseAgent):
    """Business context, intent, risk/opportunity detection — structured Pydantic output."""

    name = "analyzer"

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def execute(self, ctx: WorkflowContext) -> AgentResult:
        if ctx.interaction is None or ctx.org_context is None:
            return AgentResult(
                agent_name=self.name,
                success=False,
                decision="skipped",
                reason="Missing interaction or org context",
            )

        domain = ctx.domain  # type: ignore[arg-type]
        analysis = self.engine._analyze_with_llm(ctx.interaction, ctx.org_context, domain)
        ctx.analysis = analysis
        ctx.analysis_engine = dict(self.engine._last_analysis_metadata)

        text = self.engine._analysis_text(ctx.interaction)
        signals = self.engine._detect_signals(text, domain)
        missing_count = len(analysis.missing_information)
        confidence = max(0.45, min(0.95, 0.82 - missing_count * 0.04))

        priority = "medium"
        if signals.get("renewal_risk") or signals.get("no_champion"):
            priority = "high"
        if missing_count >= 4:
            priority = "critical" if signals.get("renewal_risk") else "high"

        urgency = "medium"
        if signals.get("timeline_pressure") or signals.get("renewal_risk"):
            urgency = "high"

        business_analysis = BusinessAnalysis(
            business_context=f"{ctx.domain} interaction ({ctx.interaction.enriched_context.detected_format})",
            customer_intent=(
                ctx.interaction.enriched_context.action_items_mentioned[0]
                if ctx.interaction.enriched_context.action_items_mentioned
                else "Clarify next enterprise decision step"
            ),
            opportunities=analysis.opportunities,
            risks=analysis.risks,
            missing_information=analysis.missing_information,
            priority=priority,  # type: ignore[arg-type]
            urgency=urgency,  # type: ignore[arg-type]
            confidence=round(confidence, 2),
            signals=signals,
            analysis_engine=ctx.analysis_engine,
        )
        ctx.business_analysis = business_analysis

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=business_analysis.confidence,
            decision="analyzed",
            reason=f"Detected {len(signals)} signals; {missing_count} information gaps",
            data=business_analysis,
        )
