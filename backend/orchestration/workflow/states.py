from __future__ import annotations

from enum import Enum
from typing import Dict, List, Set


class WorkflowState(str, Enum):
    INGESTED = "INGESTED"
    PREPROCESSED = "PREPROCESSED"
    ANALYZED = "ANALYZED"
    RETRIEVED = "RETRIEVED"
    RECOMMENDED = "RECOMMENDED"
    EXPLAINED = "EXPLAINED"
    WAITING_REVIEW = "WAITING_REVIEW"
    APPROVED = "APPROVED"
    LEARNING = "LEARNING"
    COMPLETED = "COMPLETED"


# Explicit transition graph — no implicit nested calls.
ALLOWED_TRANSITIONS: Dict[WorkflowState, Set[WorkflowState]] = {
    WorkflowState.INGESTED: {WorkflowState.PREPROCESSED},
    WorkflowState.PREPROCESSED: {WorkflowState.ANALYZED, WorkflowState.RETRIEVED},
    WorkflowState.ANALYZED: {WorkflowState.RETRIEVED},
    WorkflowState.RETRIEVED: {WorkflowState.RECOMMENDED},
    WorkflowState.RECOMMENDED: {WorkflowState.EXPLAINED},
    WorkflowState.EXPLAINED: {WorkflowState.WAITING_REVIEW},
    WorkflowState.WAITING_REVIEW: {WorkflowState.APPROVED, WorkflowState.COMPLETED},
    WorkflowState.APPROVED: {WorkflowState.LEARNING},
    WorkflowState.LEARNING: {WorkflowState.COMPLETED},
    WorkflowState.COMPLETED: set(),
}


def validate_transition(current: WorkflowState, next_state: WorkflowState) -> bool:
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    return next_state in allowed


def transition_sequence_for_route(route: str) -> List[WorkflowState]:
    """Expected state sequence for observability — actual skips are logged in trace."""
    if route == "fast_faq":
        return [
            WorkflowState.INGESTED,
            WorkflowState.PREPROCESSED,
            WorkflowState.RETRIEVED,
            WorkflowState.EXPLAINED,
            WorkflowState.WAITING_REVIEW,
            WorkflowState.COMPLETED,
        ]
    if route == "deep":
        return [
            WorkflowState.INGESTED,
            WorkflowState.PREPROCESSED,
            WorkflowState.ANALYZED,
            WorkflowState.RETRIEVED,
            WorkflowState.RECOMMENDED,
            WorkflowState.EXPLAINED,
            WorkflowState.WAITING_REVIEW,
            WorkflowState.COMPLETED,
        ]
    return [
        WorkflowState.INGESTED,
        WorkflowState.PREPROCESSED,
        WorkflowState.ANALYZED,
        WorkflowState.RETRIEVED,
        WorkflowState.RECOMMENDED,
        WorkflowState.EXPLAINED,
        WorkflowState.WAITING_REVIEW,
        WorkflowState.COMPLETED,
    ]
