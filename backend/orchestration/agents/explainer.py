from __future__ import annotations

from typing import Any

from orchestration.agents.base import BaseAgent
from orchestration.models.agent_models import AgentResult, ExplanationBundle
from orchestration.models.workflow_models import WorkflowContext


class ExplainerAgent(BaseAgent):
    """Business-friendly explanations — executive summary, narrative, reviewer guidance."""

    name = "explainer"

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def execute(self, ctx: WorkflowContext) -> AgentResult:
        analysis = ctx.analysis
        actions = ctx.next_best_actions
        metrics = ctx.success_metrics

        if analysis is None and ctx.interaction and ctx.org_context:
            analysis = self.engine._analyze_business_context(
                ctx.interaction, ctx.org_context, ctx.domain  # type: ignore[arg-type]
            )
            ctx.analysis = analysis

        if not actions and ctx.interaction and ctx.org_context and analysis:
            actions = self.engine._recommend_next_best_actions(
                interaction=ctx.interaction,
                org_context=ctx.org_context,
                analysis=analysis,
                customer_id=ctx.customer_id,
                domain=ctx.domain,  # type: ignore[arg-type]
            )
            ctx.next_best_actions = actions
            if not metrics:
                ctx.success_metrics = self.engine._compute_success_metrics(
                    domain=ctx.domain,  # type: ignore[arg-type]
                    analysis=analysis,
                    next_best_actions=actions,
                    interaction=ctx.interaction,
                )
                metrics = ctx.success_metrics

        if analysis is None:
            return AgentResult(
                agent_name=self.name,
                success=False,
                decision="skipped",
                reason="No analysis available for explanation",
            )

        overall = self.engine._overall_confidence(actions) if actions else 0.65
        nl_summary = self.engine._make_natural_language_summary(analysis, actions, metrics or {})

        opp = analysis.opportunities[0] if analysis.opportunities else "Enterprise opportunity identified"
        risk = analysis.risks[0] if analysis.risks else "Standard execution risk"
        top = actions[0].title if actions else "Qualification follow-up"

        retrieval_summary = ""
        if ctx.retrieval_result:
            retrieval_summary = ctx.retrieval_result.retrieval_summary

        structured = ExplanationBundle(
            executive_summary=(
                f"Recommend proceeding with '{top}' for {ctx.customer_id} "
                f"in the {ctx.domain.replace('_', ' ')} domain."
            ),
            decision_narrative=(
                f"{opp} Key risk to address: {risk}. "
                f"The platform proposes {len(actions)} evidence-backed actions pending human review."
            ),
            evidence_summary=retrieval_summary or "Evidence retrieved from playbooks and CRM history.",
            confidence_explanation=(
                f"Overall confidence {int(overall * 100)}% reflects evidence grounding, "
                f"information completeness, and historical approval patterns."
            ),
            business_justification=nl_summary,
            reviewer_guidance=(
                "Approve if the top action aligns with customer constraints. "
                "Reject or modify if champion, budget, or security gates are unresolved."
            ),
            natural_language_summary=nl_summary,
        )
        ctx.structured_explanation = structured

        enrichment = ctx.interaction.enriched_context if ctx.interaction else None
        ctx.explanation_bundle = {
            "evidence_summary": {
                "num_articles": len(ctx.org_context.knowledge_articles) if ctx.org_context else 0,
                "num_playbooks": len(ctx.org_context.playbooks) if ctx.org_context else 0,
                "num_product_docs": len(ctx.org_context.product_docs) if ctx.org_context else 0,
                "num_crm_events": len(ctx.org_context.crm_history) if ctx.org_context else 0,
            },
            "ingestion_enrichment": {
                "detected_format": enrichment.detected_format if enrichment else "raw",
                "source_type": enrichment.source_type if enrichment else "conversation",
                "participants": enrichment.participants if enrichment else [],
                "topics": enrichment.topics if enrichment else [],
                "action_items_mentioned": enrichment.action_items_mentioned if enrichment else [],
                "sentiment": enrichment.sentiment if enrichment else "neutral",
                "open_questions": enrichment.open_questions if enrichment else [],
                "meeting_date": enrichment.meeting_date if enrichment else None,
                "email_subject": enrichment.email_subject if enrichment else None,
            },
            "natural_language_summary": nl_summary,
            "analysis_engine": ctx.analysis_engine,
            "recommendation_engine": ctx.recommendation_engine,
            "confidence": {
                "overall": round(overall, 2),
                "confidence_interpretation": structured.confidence_explanation,
            },
            "why_next_best": [{"title": a.title, "why": a.rationale} for a in actions],
            "success_metrics": metrics or {},
            "executive_summary": structured.executive_summary,
            "decision_narrative": structured.decision_narrative,
            "business_justification": structured.business_justification,
            "reviewer_guidance": structured.reviewer_guidance,
        }

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=overall,
            decision="explained",
            reason="Generated business-friendly explanation bundle",
            data=structured,
        )
