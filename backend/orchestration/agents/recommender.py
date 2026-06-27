from __future__ import annotations

from typing import Any, List

from orchestration.agents.base import BaseAgent
from orchestration.models.agent_models import AgentResult, RecommendedAction
from orchestration.models.workflow_models import WorkflowContext


class RecommenderAgent(BaseAgent):
    """Produces Next Best Actions with evidence, confidence, and KPI lift."""

    name = "recommender"

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def execute(self, ctx: WorkflowContext) -> AgentResult:
        if ctx.interaction is None or ctx.org_context is None:
            return AgentResult(
                agent_name=self.name,
                success=False,
                decision="skipped",
                reason="Missing prerequisites for recommendation",
            )

        # Use rule-based fallback analysis if analyzer was skipped (fast FAQ path)
        if ctx.analysis is None:
            ctx.analysis = self.engine._analyze_business_context(
                ctx.interaction, ctx.org_context, ctx.domain  # type: ignore[arg-type]
            )

        actions = self.engine._recommend_with_llm(
            interaction=ctx.interaction,
            org_context=ctx.org_context,
            analysis=ctx.analysis,
            customer_id=ctx.customer_id,
            domain=ctx.domain,  # type: ignore[arg-type]
        )
        ctx.next_best_actions = actions
        ctx.recommendation_engine = dict(self.engine._last_recommendation_metadata)

        ctx.success_metrics = self.engine._compute_success_metrics(
            domain=ctx.domain,  # type: ignore[arg-type]
            analysis=ctx.analysis,
            next_best_actions=actions,
            interaction=ctx.interaction,
        )

        recommended: List[RecommendedAction] = []
        for nba in actions:
            kpi_lift = ""
            if ctx.success_metrics:
                first = next(iter(ctx.success_metrics.values()), {})
                if isinstance(first, dict):
                    kpi_lift = str(first.get("estimated_impact", ""))

            recommended.append(
                RecommendedAction(
                    title=nba.title,
                    description=nba.summary,
                    business_rationale=nba.rationale,
                    supporting_evidence=[e.source for e in nba.evidence],
                    confidence=nba.confidence,
                    expected_impact=kpi_lift,
                    priority="high" if nba.confidence >= 0.82 else "medium",
                    estimated_kpi_lift=kpi_lift,
                    recommended_next_questions=nba.recommended_next_questions,
                )
            )

        top_conf = actions[0].confidence if actions else 0.7
        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=top_conf,
            decision="recommended",
            reason=f"Proposed {len(actions)} next-best actions",
            data=recommended,
        )
