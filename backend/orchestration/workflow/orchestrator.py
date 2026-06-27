from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, List, Optional

from orchestration.models.agent_models import AgentExecutionRecord, ToolUsageRecord
from orchestration.models.workflow_models import RoutingDecision, WorkflowContext, WorkflowRoute
from orchestration.registries.agents import AgentRegistry
from orchestration.registries.tools import ToolRegistry
from orchestration.registries.workflows import WorkflowRegistry
from orchestration.workflow.states import WorkflowState, validate_transition

logger = logging.getLogger("decisio.orchestrator")


class WorkflowOrchestrator:
    """Lightweight state machine — Planner delegates execution here."""

    def __init__(
        self,
        engine: Any,
        tool_registry: ToolRegistry,
        agent_registry: type[AgentRegistry] = AgentRegistry,
    ) -> None:
        self.engine = engine
        self.tools = tool_registry
        self.agents = agent_registry

    def run(self, payload: dict[str, Any]) -> Any:
        from ai_platform import (
            CustomerInteraction,
            HumanReview,
            WorkflowStartResult,
        )

        customer_input = CustomerInteraction.from_payload(payload)
        customer_id = customer_input.customer_id
        domain = customer_input.domain
        if domain not in ("saas_sales", "customer_success", "staffing", "energy"):
            domain = "saas_sales"

        raw_text = customer_input.compose_raw_text()
        ctx = WorkflowContext(
            payload=payload,
            customer_id=customer_id,
            domain=domain,
            customer_input=customer_input,
            run_id=str(uuid.uuid4()),
            review_id=str(uuid.uuid4()),
        )

        self._transition(ctx, WorkflowState.INGESTED)

        # Ingestion (preprocess)
        interaction = self.engine._ingest_interaction(
            customer_input=customer_input,
            customer_id=customer_id,
            domain=domain,  # type: ignore[arg-type]
            raw_text=raw_text,
        )
        ctx.interaction = interaction
        self._transition(ctx, WorkflowState.PREPROCESSED)

        routing = self._decide_route(ctx)
        ctx.route = routing.route
        ctx.routing_decision = routing

        execution_order = 0
        for agent_name in routing.agents_to_run:
            agent = self.agents.get(agent_name)
            if agent is None:
                ctx.errors.append(f"Agent not registered: {agent_name}")
                continue

            execution_order += 1
            result = agent.run(ctx, execution_order)

            record = AgentExecutionRecord(
                agent_name=result.agent_name,
                execution_order=execution_order,
                duration_ms=getattr(result, "duration_ms", 0.0),
                confidence=result.confidence,
                decision=result.decision,
                reason=result.reason,
                tool_usage=result.tool_usage,
                retrieval_summary=(
                    ctx.retrieval_result.retrieval_summary if ctx.retrieval_result else None
                ),
                error=result.error,
                skipped=result.decision == "skipped",
            )
            ctx.agent_trace.append(record)

            if not result.success and result.decision != "skipped":
                ctx.errors.append(f"{agent_name}: {result.error or result.reason}")
                logger.warning("[Orchestrator] Agent %s failed; continuing: %s", agent_name, result.reason)

            self._sync_state_after_agent(ctx, agent_name)

        self._transition(ctx, WorkflowState.WAITING_REVIEW)

        review = HumanReview(
            review_id=ctx.review_id,
            status="pending",
            reviewer_notes=None,
            created_at=datetime.utcnow().isoformat() + "Z",
        )

        action_ids = [a.action_id for a in ctx.next_best_actions]
        draft_payload, _, _ = self.tools.execute(
            "draft_email",
            action_titles=[a.title for a in ctx.next_best_actions],
            customer_id=customer_id,
            domain=domain,
        )

        proposed_execution = {
            "executables": [
                {"type": "draft_email", "action_ids": action_ids, "payload": draft_payload},
                {
                    "type": "schedule_followup",
                    "action_ids": [ctx.next_best_actions[0].action_id] if ctx.next_best_actions else [],
                },
            ],
            "human_gate": True,
        }

        if ctx.explanation_bundle:
            ctx.explanation_bundle["agent_trace"] = [self._trace_to_dict(r) for r in ctx.agent_trace]
            ctx.explanation_bundle["orchestration"] = {
                "route": ctx.route,
                "routing_reason": routing.reason,
                "workflow_states": [s.value for s in self._state_path(ctx)],
                "errors": ctx.errors,
            }

        if ctx.analysis is None and ctx.interaction and ctx.org_context:
            ctx.analysis = self.engine._analyze_business_context(
                ctx.interaction, ctx.org_context, domain  # type: ignore[arg-type]
            )

        if not ctx.next_best_actions and ctx.interaction and ctx.org_context and ctx.analysis:
            ctx.next_best_actions = self.engine._recommend_next_best_actions(
                interaction=ctx.interaction,
                org_context=ctx.org_context,
                analysis=ctx.analysis,
                customer_id=customer_id,
                domain=domain,  # type: ignore[arg-type]
            )

        result = WorkflowStartResult(
            run_id=ctx.run_id,
            customer_id=customer_id,
            domain=domain,  # type: ignore[arg-type]
            interaction_id=interaction.interaction_id,
            analysis=ctx.analysis,  # type: ignore[arg-type]
            next_best_actions=ctx.next_best_actions,
            proposed_execution=proposed_execution,
            explanation_bundle=ctx.explanation_bundle,
            human_review=review,
            success_metrics=ctx.success_metrics,
        )

        self.engine.memory.put_run(result)
        self._transition(ctx, WorkflowState.COMPLETED)
        return result

    def _decide_route(self, ctx: WorkflowContext) -> RoutingDecision:
        text = (ctx.interaction.canonical_text if ctx.interaction else "").lower()
        enrichment = ctx.interaction.enriched_context if ctx.interaction else None

        # Staffing domain uses extension workflow
        if ctx.domain == "staffing":
            wf = WorkflowRegistry.get("staffing_placement")
            if wf:
                return RoutingDecision(
                    route="full",
                    reason="Staffing domain registered workflow",
                    agents_to_run=list(wf.agent_sequence),
                )

        # Simple FAQ: short question-like text
        is_short = len(text) < 120
        has_question = "?" in text or any(
            text.startswith(w) for w in ("what", "how", "when", "where", "why", "can", "is")
        )
        if is_short and has_question:
            wf = WorkflowRegistry.get("fast_faq")
            return RoutingDecision(
                route="fast_faq",
                reason="Short FAQ-style interaction — skip analyzer and recommender depth",
                agents_to_run=list(wf.agent_sequence) if wf else ["retriever", "explainer"],
            )

        # Deep path: negative sentiment, many open questions, sparse context
        missing_signals = 0
        if enrichment:
            if enrichment.sentiment in ("negative", "mixed"):
                missing_signals += 1
            if len(enrichment.open_questions) >= 2:
                missing_signals += 1
            if len(enrichment.topics) <= 1 and len(text) < 80:
                missing_signals += 1

        if missing_signals >= 2:
            wf = WorkflowRegistry.get("deep_analysis")
            return RoutingDecision(
                route="deep",
                reason="Low confidence signals — extra memory, retrieval, and analysis depth",
                agents_to_run=list(wf.agent_sequence) if wf else ["memory", "analyzer", "retriever", "recommender", "explainer"],
                confidence_threshold=0.55,
            )

        wf = WorkflowRegistry.get("full_decision")
        return RoutingDecision(
            route="full",
            reason="Standard enterprise interaction pipeline",
            agents_to_run=list(wf.agent_sequence) if wf else ["memory", "analyzer", "retriever", "recommender", "explainer"],
        )

    def _sync_state_after_agent(self, ctx: WorkflowContext, agent_name: str) -> None:
        mapping = {
            "memory": WorkflowState.PREPROCESSED,
            "staffing_domain": WorkflowState.PREPROCESSED,
            "analyzer": WorkflowState.ANALYZED,
            "retriever": WorkflowState.RETRIEVED,
            "recommender": WorkflowState.RECOMMENDED,
            "explainer": WorkflowState.EXPLAINED,
        }
        target = mapping.get(agent_name)
        if target:
            self._transition(ctx, target)

    def _transition(self, ctx: WorkflowContext, new_state: WorkflowState) -> None:
        try:
            current = WorkflowState(ctx.workflow_state)
        except ValueError:
            current = WorkflowState.INGESTED

        if current != new_state and not validate_transition(current, new_state):
            # Allow pragmatic jumps for fast_faq (PREPROCESSED -> RETRIEVED)
            logger.debug(
                "[Orchestrator] Non-standard transition %s -> %s (route=%s)",
                current.value,
                new_state.value,
                ctx.route,
            )

        ctx.workflow_state = new_state.value
        logger.info("[Orchestrator] State -> %s route=%s", new_state.value, ctx.route)

    def _state_path(self, ctx: WorkflowContext) -> List[WorkflowState]:
        seen: List[WorkflowState] = []
        for record in ctx.agent_trace:
            mapping = {
                "memory": WorkflowState.PREPROCESSED,
                "analyzer": WorkflowState.ANALYZED,
                "retriever": WorkflowState.RETRIEVED,
                "recommender": WorkflowState.RECOMMENDED,
                "explainer": WorkflowState.EXPLAINED,
            }
            st = mapping.get(record.agent_name)
            if st and st not in seen:
                seen.append(st)
        seen.append(WorkflowState.WAITING_REVIEW)
        return seen

    @staticmethod
    def _trace_to_dict(record: AgentExecutionRecord) -> dict[str, Any]:
        return {
            "agent_name": record.agent_name,
            "execution_order": record.execution_order,
            "duration_ms": round(record.duration_ms, 2),
            "confidence": record.confidence,
            "decision": record.decision,
            "reason": record.reason,
            "retrieval_summary": record.retrieval_summary,
            "error": record.error,
            "skipped": record.skipped,
            "tool_usage": [
                {
                    "tool_name": t.tool_name,
                    "success": t.success,
                    "duration_ms": round(t.duration_ms, 2),
                    "summary": t.summary,
                    "error": t.error,
                }
                for t in record.tool_usage
            ],
        }
