from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class WorkflowDefinition:
    name: str
    description: str
    route: str
    agent_sequence: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.70


class WorkflowRegistry:
    _workflows: Dict[str, WorkflowDefinition] = {}

    @classmethod
    def register(cls, workflow: WorkflowDefinition) -> None:
        cls._workflows[workflow.name] = workflow

    @classmethod
    def get(cls, name: str) -> Optional[WorkflowDefinition]:
        return cls._workflows.get(name)

    @classmethod
    def list_workflows(cls) -> List[str]:
        return sorted(cls._workflows.keys())

    @classmethod
    def clear(cls) -> None:
        cls._workflows.clear()


def register_default_workflows() -> None:
    WorkflowRegistry.register(
        WorkflowDefinition(
            name="full_decision",
            description="Standard meeting notes / email / transcript pipeline",
            route="full",
            agent_sequence=["memory", "analyzer", "retriever", "recommender", "explainer"],
        )
    )
    WorkflowRegistry.register(
        WorkflowDefinition(
            name="fast_faq",
            description="Simple FAQ — knowledge search + explanation only",
            route="fast_faq",
            agent_sequence=["retriever", "explainer"],
            confidence_threshold=0.85,
        )
    )
    WorkflowRegistry.register(
        WorkflowDefinition(
            name="deep_analysis",
            description="Low confidence — extra retrieval, memory, and business rules",
            route="deep",
            agent_sequence=["memory", "analyzer", "retriever", "recommender", "explainer"],
            confidence_threshold=0.55,
        )
    )
    WorkflowRegistry.register(
        WorkflowDefinition(
            name="staffing_placement",
            description="Staffing domain extension workflow",
            route="full",
            agent_sequence=["memory", "staffing_domain", "analyzer", "retriever", "recommender", "explainer"],
        )
    )
