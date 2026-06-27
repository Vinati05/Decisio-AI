from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

if TYPE_CHECKING:
    from ai_platform import (
        CustomerInteraction,
        IngestedInteraction,
        NextBestAction,
        OpportunityRisk,
        OrgContext,
        WorkflowStartResult,
    )

    from orchestration.models.agent_models import (
        AgentExecutionRecord,
        BusinessAnalysis,
        ExplanationBundle,
        RetrievalResult,
    )


WorkflowRoute = Literal["full", "fast_faq", "deep"]


@dataclass
class RoutingDecision:
    route: WorkflowRoute
    reason: str
    agents_to_run: List[str]
    confidence_threshold: float = 0.70


@dataclass
class WorkflowContext:
    """Mutable state passed through the orchestration pipeline."""

    payload: Dict[str, Any]
    customer_id: str
    domain: str
    route: WorkflowRoute = "full"
    routing_decision: Optional[RoutingDecision] = None

    # Populated as workflow progresses
    customer_input: Any = None
    interaction: Optional["IngestedInteraction"] = None
    org_context: Optional["OrgContext"] = None
    analysis: Optional["OpportunityRisk"] = None
    business_analysis: Optional["BusinessAnalysis"] = None
    retrieval_result: Optional["RetrievalResult"] = None
    next_best_actions: List["NextBestAction"] = field(default_factory=list)
    success_metrics: Dict[str, Any] = field(default_factory=dict)
    explanation_bundle: Dict[str, Any] = field(default_factory=dict)
    structured_explanation: Optional["ExplanationBundle"] = None

    run_id: str = ""
    review_id: str = ""
    workflow_state: str = "INGESTED"
    agent_trace: List["AgentExecutionRecord"] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Engine metadata (Ollama, etc.)
    analysis_engine: Dict[str, Any] = field(default_factory=dict)
    recommendation_engine: Dict[str, Any] = field(default_factory=dict)
