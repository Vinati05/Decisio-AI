from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class BusinessAnalysis(BaseModel):
    """Structured output from AnalyzerAgent."""

    business_context: str = ""
    customer_intent: str = ""
    opportunities: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    urgency: Literal["low", "medium", "high"] = "medium"
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    signals: Dict[str, bool] = Field(default_factory=dict)
    analysis_engine: Dict[str, Any] = Field(default_factory=dict)


class RetrievedDocument(BaseModel):
    label: str
    excerpt: str
    source: str
    relevance: float = 1.0
    doc_type: str = "unknown"


class RetrievalResult(BaseModel):
    """Structured output from RetrieverAgent."""

    documents: List[RetrievedDocument] = Field(default_factory=list)
    relevance_scores: Dict[str, float] = Field(default_factory=dict)
    citations: List[str] = Field(default_factory=list)
    retrieval_summary: str = ""
    sources_used: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class RecommendedAction(BaseModel):
    title: str
    description: str
    business_rationale: str
    supporting_evidence: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    expected_impact: str = ""
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    estimated_kpi_lift: str = ""
    recommended_next_questions: List[str] = Field(default_factory=list)


class ExplanationBundle(BaseModel):
    """Structured output from ExplainerAgent."""

    executive_summary: str = ""
    decision_narrative: str = ""
    evidence_summary: str = ""
    confidence_explanation: str = ""
    business_justification: str = ""
    reviewer_guidance: str = ""
    natural_language_summary: str = ""


@dataclass
class ToolUsageRecord:
    tool_name: str
    success: bool
    duration_ms: float
    summary: str = ""
    error: Optional[str] = None


@dataclass
class AgentExecutionRecord:
    agent_name: str
    execution_order: int
    duration_ms: float
    confidence: Optional[float]
    decision: str
    reason: str
    tool_usage: List[ToolUsageRecord] = field(default_factory=list)
    retrieval_summary: Optional[str] = None
    error: Optional[str] = None
    skipped: bool = False


@dataclass
class AgentResult:
    agent_name: str
    success: bool
    confidence: Optional[float] = None
    decision: str = ""
    reason: str = ""
    data: Any = None
    tool_usage: List[ToolUsageRecord] = field(default_factory=list)
    error: Optional[str] = None
