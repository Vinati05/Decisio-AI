from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple


DecisionDomain = Literal[
    "saas_sales",
    "customer_success",
    "staffing",
    "energy",
]

SourceType = Literal["email", "meeting_notes", "transcript", "crm_update", "conversation"]
DetectedFormat = Literal["raw", "email", "transcript", "meeting_notes", "crm_update", "conversation"]
SentimentLabel = Literal["positive", "neutral", "negative", "mixed"]


@dataclass
class CustomerInteraction:
    """Flexible input schema for /workflow/start — supports raw text and structured formats.

    Backward compatible: `interaction_text` alone still works.
    Structured fields (email_*, meeting_*, transcript) are merged into a single text blob
    before preprocessing detects format and extracts business elements.
    """

    customer_id: str
    domain: str = "saas_sales"
    source_type: Optional[str] = None
    interaction_text: Optional[str] = None
    email_subject: Optional[str] = None
    email_from: Optional[str] = None
    email_body: Optional[str] = None
    meeting_date: Optional[str] = None
    meeting_context: Optional[str] = None
    meeting_notes: Optional[str] = None
    transcript: Optional[str] = None

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "CustomerInteraction":
        return cls(
            customer_id=str(payload["customer_id"]),
            domain=str(payload.get("domain", "saas_sales")),
            source_type=payload.get("source_type"),
            interaction_text=payload.get("interaction_text"),
            email_subject=payload.get("email_subject"),
            email_from=payload.get("email_from"),
            email_body=payload.get("email_body"),
            meeting_date=payload.get("meeting_date"),
            meeting_context=payload.get("meeting_context"),
            meeting_notes=payload.get("meeting_notes"),
            transcript=payload.get("transcript"),
        )

    def compose_raw_text(self) -> str:
        """Merge structured fields into one string for format detection."""
        parts: List[str] = []

        if self.email_subject or self.email_from or self.email_body:
            if self.email_subject:
                parts.append(f"Subject: {self.email_subject}")
            if self.email_from:
                parts.append(f"From: {self.email_from}")
            if self.email_body:
                parts.append(self.email_body.strip())

        if self.meeting_date or self.meeting_context or self.meeting_notes:
            if self.meeting_date:
                parts.append(f"Date: {self.meeting_date}")
            if self.meeting_context:
                parts.append(f"Context: {self.meeting_context}")
            if self.meeting_notes:
                parts.append(self.meeting_notes.strip())

        if self.transcript:
            parts.append(self.transcript.strip())

        if self.interaction_text:
            parts.append(self.interaction_text.strip())

        merged = "\n\n".join(p for p in parts if p)
        return merged


@dataclass
class InteractionEnrichment:
    """Structured output from dynamic ingestion — feeds business analysis heuristics."""

    detected_format: DetectedFormat
    source_type: SourceType
    participants: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    action_items_mentioned: List[str] = field(default_factory=list)
    sentiment: SentimentLabel = "neutral"
    open_questions: List[str] = field(default_factory=list)
    meeting_date: Optional[str] = None
    email_subject: Optional[str] = None
    email_from: Optional[str] = None
    analysis_text: str = ""  # canonical + topic hints for signal detection


@dataclass
class IngestedInteraction:
    interaction_id: str
    customer_id: str
    domain: DecisionDomain
    source_type: SourceType
    raw_text: str
    canonical_text: str
    ingested_at: str
    enriched_context: InteractionEnrichment = field(default_factory=lambda: InteractionEnrichment("raw", "conversation"))


@dataclass
class OrgContext:
    knowledge_articles: List[Dict[str, str]]
    playbooks: List[Dict[str, str]]
    product_docs: List[Dict[str, str]]
    crm_history: List[Dict[str, str]]


@dataclass
class OpportunityRisk:
    opportunities: List[str]
    risks: List[str]
    missing_information: List[str]


@dataclass
class EvidenceItem:
    label: str
    excerpt: str
    source: str


@dataclass
class NextBestAction:
    action_id: str
    title: str
    summary: str
    confidence: float
    evidence: List[EvidenceItem]
    rationale: str
    recommended_next_questions: List[str] = field(default_factory=list)


@dataclass
class HumanReview:
    review_id: str
    status: Literal["pending", "approved", "rejected"]
    reviewer_notes: Optional[str]
    created_at: str


@dataclass
class WorkflowStartResult:
    run_id: str
    customer_id: str
    domain: DecisionDomain
    interaction_id: str
    analysis: OpportunityRisk
    next_best_actions: List[NextBestAction]
    proposed_execution: Dict[str, Any]
    explanation_bundle: Dict[str, Any]
    human_review: HumanReview
    success_metrics: Dict[str, Any] = field(default_factory=dict)


class MemoryStore:
    """Minimal in-memory store for MVP.

    Designed to be replaceable by a DB later.
    """

    def __init__(self) -> None:
        self._interactions: Dict[str, IngestedInteraction] = {}
        self._reviews: Dict[str, HumanReview] = {}
        self._runs: Dict[str, WorkflowStartResult] = {}
        self._lessons: Dict[Tuple[str, DecisionDomain], List[Dict[str, Any]]] = {}

    def put_interaction(self, interaction: IngestedInteraction) -> None:
        self._interactions[interaction.interaction_id] = interaction

    def put_run(self, result: WorkflowStartResult) -> None:
        self._runs[result.run_id] = result
        self._reviews[result.human_review.review_id] = result.human_review

    def update_review(self, review_id: str, status: str, reviewer_notes: Optional[str]) -> None:
        hr = self._reviews[review_id]
        hr.status = status  # type: ignore[assignment]
        hr.reviewer_notes = reviewer_notes

    def get_memory(self, customer_id: str) -> Dict[str, Any]:
        lessons: List[Dict[str, Any]] = []
        for (cid, _domain), items in self._lessons.items():
            if cid == customer_id:
                lessons.extend(items)

        approved = [l for l in lessons if l.get("review_status") == "approved"]
        rejected = [l for l in lessons if l.get("review_status") == "rejected"]

        # Aggregate KPI deltas from approved outcomes to show continuous improvement.
        kpi_history: Dict[str, List[str]] = {}
        for lesson in approved:
            improvements = lesson.get("kpi_improvements") or {}
            if improvements:
                for metric, impact in improvements.items():
                    kpi_history.setdefault(metric, []).append(str(impact))
            else:
                for metric, value in (lesson.get("kpi_snapshot") or {}).items():
                    if isinstance(value, dict) and value.get("estimated_impact"):
                        kpi_history.setdefault(metric, []).append(str(value["estimated_impact"]))
                    elif isinstance(value, str):
                        kpi_history.setdefault(metric, []).append(value)

        learned_insights: List[str] = []
        if approved:
            top_actions = [l.get("top_action_title") for l in approved if l.get("top_action_title")]
            if top_actions:
                learned_insights.append(
                    f"Past approvals favor: {top_actions[-1]} "
                    f"({len(approved)} approved run(s) on record)."
                )
            if kpi_history:
                sample = next(iter(kpi_history.items()))
                learned_insights.append(
                    f"Observed KPI movement on '{sample[0]}': {sample[1][-1]} (latest approved run)."
                )
        if rejected:
            notes = [l.get("reviewer_notes") for l in rejected if l.get("reviewer_notes")]
            if notes:
                learned_insights.append(
                    f"Rejected runs often cite: \"{notes[-1][:80]}\" — future plans should address this."
                )
            else:
                learned_insights.append(
                    f"{len(rejected)} rejected run(s) suggest recommendations need tighter qualification."
                )
        if not lessons:
            learned_insights.append("No prior outcomes yet — recommendations use playbook defaults.")

        return {
            "customer_id": customer_id,
            "saved_lessons_learned": lessons,
            "learned_insights": learned_insights,
            "outcome_summary": {
                "total_runs": len(lessons),
                "approved": len(approved),
                "rejected": len(rejected),
                "approval_rate": round(len(approved) / len(lessons), 2) if lessons else None,
            },
            "kpi_history": kpi_history,
        }

    def learn_from_outcome(
        self,
        customer_id: str,
        domain: DecisionDomain,
        run_id: str,
        review_status: str,
        reviewer_notes: Optional[str],
    ) -> None:
        key = (customer_id, domain)
        self._lessons.setdefault(key, [])

        run = self._runs.get(run_id)
        kpi_snapshot = dict(run.success_metrics) if run else {}
        top_action_title = run.next_best_actions[0].title if run and run.next_best_actions else None

        # Simulate KPI improvement when a human approves — demonstrates closed-loop learning.
        kpi_improvements: Dict[str, str] = {}
        if review_status == "approved" and kpi_snapshot:
            for metric_key, metric_val in kpi_snapshot.items():
                if isinstance(metric_val, dict) and "estimated_impact" in metric_val:
                    kpi_improvements[metric_key] = metric_val["estimated_impact"]
                elif isinstance(metric_val, str):
                    kpi_improvements[metric_key] = metric_val

        self._lessons[key].append(
            {
                "run_id": run_id,
                "review_status": review_status,
                "reviewer_notes": reviewer_notes,
                "learned_at": datetime.utcnow().isoformat() + "Z",
                "kpi_snapshot": kpi_snapshot,
                "kpi_improvements": kpi_improvements,
                "top_action_title": top_action_title,
                "insight": self._derive_lesson_insight(review_status, reviewer_notes, top_action_title),
            }
        )

    @staticmethod
    def _derive_lesson_insight(
        review_status: str,
        reviewer_notes: Optional[str],
        top_action_title: Optional[str],
    ) -> str:
        if review_status == "approved":
            base = f"Approved plan anchored on '{top_action_title}'" if top_action_title else "Approved plan"
            return f"{base}; similar playbook steps should be prioritized next time."
        if reviewer_notes:
            return f"Rejected due to: {reviewer_notes[:120]} — tighten qualification before proposing."
        return "Rejected without notes — increase discovery depth before recommending execution."

    def get_lessons_for_customer(self, customer_id: str, domain: DecisionDomain) -> List[Dict[str, Any]]:
        return list(self._lessons.get((customer_id, domain), []))


class MockKnowledge:
    """Hard-coded knowledge so the hackathon demo works offline."""

    def __init__(self) -> None:
        # SaaS Sales: 12 entries across categories — primary demo domain.
        self._articles = {
            "saas_sales": [
                {
                    "id": "KB-SAAS-01",
                    "title": "Discovery: qualify pain + champion",
                    "excerpt": (
                        "Focus on pain severity (1–10), urgency, current workaround cost, and identify "
                        "a champion who owns the outcome. Deals without a named champion stall 2.3× longer "
                        "in mid-funnel stages per internal win/loss analysis."
                    ),
                },
                {
                    "id": "KB-SAAS-02",
                    "title": "Multi-threading enterprise deals",
                    "excerpt": (
                        "Map economic buyer, technical evaluator, and end-user sponsor before proposal. "
                        "Single-threaded deals (>60 days) convert at 18% vs 41% when 3+ stakeholders "
                        "are engaged with tailored value narratives."
                    ),
                },
                {
                    "id": "KB-SAAS-03",
                    "title": "Competitive displacement playbook",
                    "excerpt": (
                        "When a competitor is named, document their gaps on reporting latency, integration "
                        "depth, and TCO. Position a proof-of-value sprint rather than a feature bake-off — "
                        "POV-to-close rate is 34% higher than RFP-led cycles."
                    ),
                },
            ],
            "customer_success": [
                {
                    "id": "KB-CS-01",
                    "title": "Health scoring: leading indicators",
                    "excerpt": (
                        "Usage drops >15% MoM and support escalations within 14 days often precede churn "
                        "by 6–8 weeks. Trigger recovery outreach when health score falls below 65."
                    ),
                },
                {
                    "id": "KB-CS-02",
                    "title": "Executive business review cadence",
                    "excerpt": (
                        "Quarterly EBRs with ROI proof points reduce churn risk by ~22% for accounts "
                        "above $50K ARR. Include adoption milestones, support trend, and expansion signals."
                    ),
                },
            ],
        }

        self._playbooks = {
            "saas_sales": [
                {
                    "id": "PB-SAAS-01",
                    "title": "Mutual action plan (MAP) after discovery",
                    "excerpt": (
                        "Within 48 hours of discovery, propose a 30/60-day MAP: named stakeholders, "
                        "success metrics (e.g., time-to-report), decision dates, and next meeting agenda. "
                        "MAP acceptance correlates with +25% win probability in enterprise segments."
                    ),
                },
                {
                    "id": "PB-SAAS-02",
                    "title": "Champion enablement kit",
                    "excerpt": (
                        "Provide champion with internal pitch deck, ROI one-pager, and security FAQ. "
                        "Champions who receive enablement close internal approvals 12 days faster on average."
                    ),
                },
                {
                    "id": "PB-SAAS-03",
                    "title": "Security & procurement fast-track",
                    "excerpt": (
                        "If security review is mentioned, initiate SOC2/ISO packet and pre-fill questionnaire "
                        "within 5 business days. Delayed security responses are the #2 reason for slip in Q3–Q4."
                    ),
                },
            ],
            "customer_success": [
                {
                    "id": "PB-CS-01",
                    "title": "At-risk account recovery",
                    "excerpt": (
                        "Reconfirm value drivers, execute a 30-day adoption plan with weekly check-ins, "
                        "and escalate internally with customer consent. Recovery plans executed within "
                        "10 days reduce churn probability by ~18%."
                    ),
                },
            ],
        }

        self._product_docs = {
            "saas_sales": [
                {
                    "id": "DOC-SAAS-API",
                    "title": "CRM sync integration",
                    "excerpt": (
                        "Bi-directional sync of meeting outcomes, MAP milestones, and champion notes into "
                        "Salesforce/HubSpot custom fields. Keeps stakeholders aligned and reduces "
                        "time-to-follow-up by ~40% when auto-logged."
                    ),
                },
                {
                    "id": "DOC-SAAS-REPORT",
                    "title": "Executive reporting module",
                    "excerpt": (
                        "Pre-built dashboards cut report generation from 4 hours to 15 minutes. "
                        "Customers cite reporting speed as top-3 buying criterion in 68% of won deals."
                    ),
                },
                {
                    "id": "DOC-SAAS-SSO",
                    "title": "Enterprise SSO & audit trail",
                    "excerpt": (
                        "SAML/OIDC SSO with full audit logging satisfies most enterprise security reviews. "
                        "Average security review cycle: 8 business days when packet is complete upfront."
                    ),
                },
            ],
            "customer_success": [
                {
                    "id": "DOC-CS-HEALTH",
                    "title": "Health dashboard",
                    "excerpt": (
                        "Shows usage trends, feature adoption heatmaps, and correlates them with support "
                        "tickets and onboarding milestones. CSMs use it to prioritize outreach."
                    ),
                },
                {
                    "id": "DOC-CS-ADOPT",
                    "title": "Adoption milestone tracker",
                    "excerpt": (
                        "Tracks customer-defined milestones (e.g., 80% user activation by day 30). "
                        "Accounts hitting milestones renew at 91% vs 71% when milestones are missed."
                    ),
                },
            ],
        }

        self._crm_history = {
            "saas_sales": [
                {
                    "id": "CRM-SAAS-1",
                    "timestamp": "2026-06-10",
                    "text": (
                        "Discovery call: VP Ops wants faster reporting (currently 4hr manual); "
                        "no champion identified. Competitor X mentioned for analytics."
                    ),
                },
                {
                    "id": "CRM-SAAS-2",
                    "timestamp": "2026-06-18",
                    "text": (
                        "Follow-up email opened but no reply. IT lead asked about SSO and data residency "
                        "— security review likely required before pilot."
                    ),
                },
                {
                    "id": "CRM-SAAS-3",
                    "timestamp": "2026-06-22",
                    "text": (
                        "Similar account (Acme Corp) closed after MAP + champion enablement in 45 days. "
                        "Win driver: quantified time-to-report ROI."
                    ),
                },
            ],
            "customer_success": [
                {
                    "id": "CRM-CS-1",
                    "timestamp": "2026-06-12",
                    "text": (
                        "Support tickets up 40% last 2 weeks; product usage dipped 18%. "
                        "Customer success manager flagged at-risk status."
                    ),
                },
                {
                    "id": "CRM-CS-2",
                    "timestamp": "2026-06-20",
                    "text": (
                        "Recovery plan started: weekly adoption check-ins scheduled. "
                        "Usage stabilized after onboarding refresher for power users."
                    ),
                },
            ],
        }

    def get_context(self, domain: DecisionDomain) -> OrgContext:
        return OrgContext(
            knowledge_articles=self._articles.get(domain, []),
            playbooks=self._playbooks.get(domain, []),
            product_docs=self._product_docs.get(domain, []),
            crm_history=self._crm_history.get(domain, []),
        )


class PlannerAgent:
    def __init__(self, knowledge: MockKnowledge, memory: MemoryStore) -> None:
        self.knowledge = knowledge
        self.memory = memory

    def run_workflow(self, payload: Dict[str, Any]) -> WorkflowStartResult:
        customer_input = CustomerInteraction.from_payload(payload)
        customer_id = customer_input.customer_id
        domain = customer_input.domain
        domain = domain if domain in ("saas_sales", "customer_success", "staffing", "energy") else "saas_sales"

        raw_text = customer_input.compose_raw_text()

        interaction = self._ingest_interaction(
            customer_input=customer_input,
            customer_id=customer_id,
            domain=domain,  # type: ignore[arg-type]
            raw_text=raw_text,
        )
        self.memory.put_interaction(interaction)

        org_context = self.knowledge.get_context(domain)  # type: ignore[arg-type]

        # Enriched ingestion context drives heuristics below (participants, topics, open questions).
        analysis = self._analyze_business_context(interaction, org_context, domain)  # type: ignore[arg-type]

        next_best_actions = self._recommend_next_best_actions(
            interaction=interaction,
            org_context=org_context,
            analysis=analysis,
            customer_id=customer_id,
            domain=domain,  # type: ignore[arg-type]
        )

        success_metrics = self._compute_success_metrics(
            domain=domain,  # type: ignore[arg-type]
            analysis=analysis,
            next_best_actions=next_best_actions,
            interaction=interaction,
        )

        run_id = str(uuid.uuid4())
        review = HumanReview(
            review_id=str(uuid.uuid4()),
            status="pending",
            reviewer_notes=None,
            created_at=datetime.utcnow().isoformat() + "Z",
        )

        proposed_execution = {
            "executables": [
                {"type": "draft_email", "action_ids": [a.action_id for a in next_best_actions]},
                {"type": "schedule_followup", "action_ids": [next_best_actions[0].action_id] if next_best_actions else []},
            ],
            "human_gate": True,
        }

        enrichment = interaction.enriched_context
        explanation_bundle = {
            "evidence_summary": {
                "num_articles": len(org_context.knowledge_articles),
                "num_playbooks": len(org_context.playbooks),
                "num_product_docs": len(org_context.product_docs),
                "num_crm_events": len(org_context.crm_history),
            },
            "ingestion_enrichment": {
                "detected_format": enrichment.detected_format,
                "source_type": enrichment.source_type,
                "participants": enrichment.participants,
                "topics": enrichment.topics,
                "action_items_mentioned": enrichment.action_items_mentioned,
                "sentiment": enrichment.sentiment,
                "open_questions": enrichment.open_questions,
                "meeting_date": enrichment.meeting_date,
                "email_subject": enrichment.email_subject,
            },
            "natural_language_summary": self._make_natural_language_summary(analysis, next_best_actions, success_metrics),
            "confidence": {
                "overall": round(self._overall_confidence(next_best_actions), 2),
                "confidence_interpretation": "Higher means the recommendation is closer to playbook patterns found in the mock enterprise knowledge.",
            },
            "why_next_best": [
                {
                    "title": nba.title,
                    "why": nba.rationale,
                }
                for nba in next_best_actions
            ],
            "success_metrics": success_metrics,
        }

        result = WorkflowStartResult(
            run_id=run_id,
            customer_id=customer_id,
            domain=domain,  # type: ignore[arg-type]
            interaction_id=interaction.interaction_id,
            analysis=analysis,
            next_best_actions=next_best_actions,
            proposed_execution=proposed_execution,
            explanation_bundle=explanation_bundle,
            human_review=review,
            success_metrics=success_metrics,
        )
        self.memory.put_run(result)
        return result

    def _ingest_interaction(
        self,
        customer_input: CustomerInteraction,
        customer_id: str,
        domain: DecisionDomain,
        raw_text: str,
    ) -> IngestedInteraction:
        enrichment = self._preprocess_interaction(
            text=raw_text,
            source_type_hint=customer_input.source_type,
            structured={
                "email_subject": customer_input.email_subject,
                "email_from": customer_input.email_from,
                "meeting_date": customer_input.meeting_date,
            },
        )

        canonical = enrichment.analysis_text.strip() or raw_text.strip()
        if not canonical:
            canonical = "(No interaction text provided)"

        valid_sources = ("email", "meeting_notes", "transcript", "crm_update", "conversation")
        source_type = enrichment.source_type
        if customer_input.source_type and customer_input.source_type in valid_sources:
            source_type = customer_input.source_type  # type: ignore[assignment]

        return IngestedInteraction(
            interaction_id=str(uuid.uuid4()),
            customer_id=customer_id,
            domain=domain,
            source_type=source_type,
            raw_text=raw_text,
            canonical_text=canonical,
            ingested_at=datetime.utcnow().isoformat() + "Z",
            enriched_context=enrichment,
        )

    # --- Dynamic ingestion layer -------------------------------------------------
    # Preprocessing detects format (email/transcript/note), extracts participants,
    # topics, action items, sentiment, and open questions. The enriched `analysis_text`
    # is what downstream heuristics use — richer than raw strip() alone.

    _SPEAKER_LINE = re.compile(r"^([A-Za-z][A-Za-z0-9 .\-'()]{0,50}):\s*(.+)$", re.MULTILINE)
    _TITLE_NAME = re.compile(
        r"\b((?:VP|Director|Manager|Head|Chief|Dr\.?)\s+[A-Za-z][A-Za-z .\-']+|"
        r"[A-Za-z][A-Za-z .\-']+(?:,\s*(?:VP|Director|Manager|Head)))",
        re.IGNORECASE,
    )
    _TOPIC_KEYWORDS: Dict[str, List[str]] = {
        "reporting_pain": ["report", "dashboard", "manual", "slow", "spreadsheet", "excel"],
        "champion_gap": ["champion", "decision maker", "stakeholder", "sponsor", "owner"],
        "competitive": ["competitor", "alternative", "evaluating", "incumbent", "versus"],
        "security": ["security", "soc2", "sso", "compliance", "audit", "procurement"],
        "timeline": ["urgent", "deadline", "q3", "q4", "asap", "timeline", "end of quarter"],
        "budget": ["budget", "pricing", "cost", "roi", "contract"],
        "integration": ["integrat", "api", "crm", "salesforce", "hubspot", "sync"],
        "support_friction": ["ticket", "escalat", "support", "bug", "issue", "broken"],
        "usage_adoption": ["usage", "adoption", "active users", "login", "inactive"],
        "renewal_churn": ["renew", "churn", "cancel", "at-risk", "contract end"],
    }
    _POSITIVE_WORDS = ("excited", "great", "love", "interested", "progress", "approved", "yes", "eager")
    _NEGATIVE_WORDS = ("frustrated", "concern", "problem", "issue", "slow", "blocked", "unhappy", "risk", "churn")

    def _preprocess_interaction(
        self,
        text: str,
        source_type_hint: Optional[str] = None,
        structured: Optional[Dict[str, Optional[str]]] = None,
    ) -> InteractionEnrichment:
        structured = structured or {}
        stripped = text.strip()

        detected_format, source_type = self._detect_input_format(stripped, source_type_hint, structured)

        participants = self._extract_participants(stripped, structured, detected_format)
        topics = self._extract_topics(stripped)
        action_items = self._extract_action_items(stripped)
        open_questions = self._extract_open_questions(stripped)
        sentiment = self._detect_sentiment(stripped)

        meeting_date = structured.get("meeting_date")
        if not meeting_date and detected_format == "meeting_notes":
            meeting_date = self._extract_meeting_date(stripped)

        email_subject = structured.get("email_subject")
        email_from = structured.get("email_from")
        if detected_format == "email" and not email_subject:
            email_subject = self._extract_email_field(stripped, "Subject")
        if detected_format == "email" and not email_from:
            email_from = self._extract_email_field(stripped, "From")

        # Append topic hints so signal detection catches structured extractions.
        topic_hint = " ".join(topics)
        analysis_text = stripped
        if topic_hint:
            analysis_text = f"{stripped}\n\n[Ingestion topics: {topic_hint}]"

        return InteractionEnrichment(
            detected_format=detected_format,
            source_type=source_type,
            participants=participants,
            topics=topics,
            action_items_mentioned=action_items,
            sentiment=sentiment,
            open_questions=open_questions,
            meeting_date=meeting_date,
            email_subject=email_subject,
            email_from=email_from,
            analysis_text=analysis_text,
        )

    def _detect_input_format(
        self,
        text: str,
        source_type_hint: Optional[str],
        structured: Dict[str, Optional[str]],
    ) -> Tuple[DetectedFormat, SourceType]:
        lower = text.lower()

        if structured.get("email_subject") or structured.get("email_from") or (
            "subject:" in lower and ("from:" in lower or "to:" in lower)
        ):
            return "email", "email"

        if structured.get("meeting_date") or any(
            k in lower for k in ("date:", "attendees:", "meeting notes", "context:", "agenda:")
        ):
            return "meeting_notes", "meeting_notes"

        speaker_matches = self._SPEAKER_LINE.findall(text)
        if len(speaker_matches) >= 2 or "transcript" in (source_type_hint or "").lower():
            return "transcript", "transcript"

        hint_map: Dict[str, Tuple[DetectedFormat, SourceType]] = {
            "email": ("email", "email"),
            "meeting_notes": ("meeting_notes", "meeting_notes"),
            "transcript": ("transcript", "transcript"),
            "crm_update": ("crm_update", "crm_update"),
            "conversation": ("conversation", "conversation"),
        }
        if source_type_hint and source_type_hint in hint_map:
            return hint_map[source_type_hint]

        if not text:
            return "raw", "conversation"
        return "raw", "conversation"

    def _extract_participants(
        self,
        text: str,
        structured: Dict[str, Optional[str]],
        detected_format: DetectedFormat,
    ) -> List[str]:
        found: List[str] = []

        if structured.get("email_from"):
            found.append(structured["email_from"])

        for match in self._SPEAKER_LINE.findall(text):
            speaker = match[0].strip()
            if speaker.lower() not in ("note", "notes", "action", "actions"):
                found.append(speaker)

        for line in text.splitlines():
            ll = line.lower()
            if ll.startswith("attendees:") or ll.startswith("participants:"):
                names = line.split(":", 1)[1]
                found.extend(n.strip() for n in re.split(r"[,;]", names) if n.strip())

        for match in self._TITLE_NAME.findall(text):
            name = match if isinstance(match, str) else match[0]
            if len(name) > 3:
                found.append(name.strip())

        # De-dupe preserving order.
        seen: set[str] = set()
        out: List[str] = []
        for p in found:
            key = p.lower()
            if key not in seen:
                seen.add(key)
                out.append(p)
        return out[:8]

    def _extract_topics(self, text: str) -> List[str]:
        lower = text.lower()
        topics: List[str] = []
        for topic, keywords in self._TOPIC_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                topics.append(topic.replace("_", " "))
        return topics

    def _extract_action_items(self, text: str) -> List[str]:
        items: List[str] = []
        action_patterns = (
            r"(?:action item|todo|follow[- ]?up|need to|will send|next step|assign(?:ed)? to)\s*[:\-]?\s*(.+)",
            r"^\s*[-*]\s*(?:action|follow up|todo)\s*[:\-]?\s*(.+)$",
        )
        for line in text.splitlines():
            for pattern in action_patterns:
                m = re.search(pattern, line, re.IGNORECASE)
                if m:
                    item = m.group(1).strip().rstrip(".")
                    if len(item) > 5:
                        items.append(item[:160])
        return items[:6]

    def _extract_open_questions(self, text: str) -> List[str]:
        questions: List[str] = []
        for line in text.splitlines():
            line = line.strip()
            # Strip transcript speaker prefix so questions are customer-facing.
            speaker_match = self._SPEAKER_LINE.match(line)
            if speaker_match:
                line = speaker_match.group(2).strip()
            if "?" in line:
                parts = re.split(r"(?<=\?)\s*", line)
                for p in parts:
                    q = p.strip()
                    if q.endswith("?") and len(q) > 8:
                        questions.append(q[:200])
            elif re.match(r"^(who|what|when|where|why|how|can we|do we|is there)\b", line, re.I):
                questions.append(line[:200])
        return questions[:8]

    def _detect_sentiment(self, text: str) -> SentimentLabel:
        lower = text.lower()
        pos = sum(1 for w in self._POSITIVE_WORDS if w in lower)
        neg = sum(1 for w in self._NEGATIVE_WORDS if w in lower)
        if pos > 0 and neg > 0:
            return "mixed"
        if neg >= 2:
            return "negative"
        if pos >= 2:
            return "positive"
        if neg == 1:
            return "mixed"
        return "neutral"

    @staticmethod
    def _extract_meeting_date(text: str) -> Optional[str]:
        for line in text.splitlines():
            if line.lower().startswith("date:"):
                return line.split(":", 1)[1].strip()[:40]
        m = re.search(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b", text)
        return m.group(1) if m else None

    @staticmethod
    def _extract_email_field(text: str, field: str) -> Optional[str]:
        prefix = f"{field.lower()}:"
        for line in text.splitlines():
            if line.lower().startswith(prefix):
                return line.split(":", 1)[1].strip()[:200]
        return None

    def _analysis_text(self, interaction: IngestedInteraction) -> str:
        """Text used for signal detection — prefers enriched analysis_text."""
        return interaction.enriched_context.analysis_text.lower() or interaction.canonical_text.lower()

    def _memory_bias_factors(self, customer_id: str, domain: DecisionDomain) -> Dict[str, float]:
        """Translate past human outcomes into confidence biases for similar actions."""
        lessons = self.memory.get_lessons_for_customer(customer_id, domain)
        bias: Dict[str, float] = {
            "map": 0.0,
            "champion": 0.0,
            "security": 0.0,
            "recovery": 0.0,
            "qualification": 0.0,
        }
        for lesson in lessons:
            status = lesson.get("review_status", "")
            notes = (lesson.get("reviewer_notes") or "").lower()
            title = (lesson.get("top_action_title") or "").lower()
            delta = 0.06 if status == "approved" else -0.05 if status == "rejected" else 0.0

            if "map" in title or "action plan" in title:
                bias["map"] += delta
            if "champion" in title or "champion" in notes:
                bias["champion"] += delta
            if "security" in title or "security" in notes or "sso" in notes:
                bias["security"] += delta
            if "recovery" in title or "at-risk" in title:
                bias["recovery"] += delta
            if "qualif" in title or "follow-up" in title:
                bias["qualification"] += delta

        return bias

    def _detect_signals(self, text: str, domain: DecisionDomain) -> Dict[str, bool]:
        """Keyword heuristics for nuanced business context — not ML, but playbook-aligned."""
        signals: Dict[str, bool] = {}

        if domain == "saas_sales":
            signals["pain_workflow"] = any(k in text for k in (
                "pain", "problem", "slow", "report", "manual", "bottleneck", "workflow", "inefficient",
            ))
            signals["no_champion"] = any(k in text for k in (
                "no champion", "unclear champion", "no decision", "no owner", "who owns",
            )) or ("champion" not in text and any(k in text for k in ("stakeholder", "vp", "director")))
            signals["competitor"] = any(k in text for k in (
                "competitor", "alternative", "evaluating", "vs ", "versus", "incumbent",
            ))
            signals["security"] = any(k in text for k in (
                "security", "soc2", "iso", "compliance", "sso", "audit", "procurement", "legal review",
            ))
            signals["timeline_pressure"] = any(k in text for k in (
                "urgent", "asap", "deadline", "q3", "q4", "end of quarter", "this month", "timeline",
            ))
            signals["budget"] = any(k in text for k in (
                "budget", "pricing", "cost", "roi", "discount", "contract value",
            ))
            signals["integration"] = any(k in text for k in (
                "integrat", "api", "crm", "salesforce", "hubspot", "sync", "data",
            ))
        elif domain == "customer_success":
            signals["support_friction"] = any(k in text for k in (
                "ticket", "issue", "escalat", "support", "bug", "broken", "frustrated",
            ))
            signals["usage_drop"] = any(k in text for k in (
                "usage", "adoption", "dip", "drop", "decline", "inactive", "not using",
            ))
            signals["renewal_risk"] = any(k in text for k in (
                "renew", "churn", "cancel", "at-risk", "at risk", "contract end",
            ))
            signals["expansion"] = any(k in text for k in (
                "expand", "upsell", "more seats", "additional", "growth",
            ))
        else:
            signals["generic"] = True

        return signals

    def _analyze_business_context(
        self,
        interaction: IngestedInteraction,
        org_context: OrgContext,
        domain: DecisionDomain,
    ) -> OpportunityRisk:
        text = self._analysis_text(interaction)
        enrichment = interaction.enriched_context
        lessons = self.memory.get_lessons_for_customer(interaction.customer_id, domain)
        _ = lessons
        memory_bias = self._memory_bias_factors(interaction.customer_id, domain)
        signals = self._detect_signals(text, domain)

        opportunities: List[str] = []
        risks: List[str] = []
        missing: List[str] = []

        # Ingestion-derived context feeds missing-info and risk framing directly.
        if enrichment.open_questions:
            for q in enrichment.open_questions[:2]:
                missing.append(q)
        if enrichment.participants and not signals.get("no_champion"):
            opportunities.append(
                f"Multi-thread with identified participants ({', '.join(enrichment.participants[:3])}) "
                "to accelerate stakeholder alignment."
            )
        if enrichment.action_items_mentioned:
            opportunities.append(
                f"Customer already mentioned next steps: \"{enrichment.action_items_mentioned[0]}\" — "
                "align recommendations to their stated intent."
            )
        if enrichment.sentiment in ("negative", "mixed"):
            risks.append(
                f"Sentiment is {enrichment.sentiment} — address concerns explicitly before proposing execution."
            )
        if "champion gap" in enrichment.topics:
            signals["no_champion"] = True  # type: ignore[index]
        if "security" in enrichment.topics:
            signals["security"] = True  # type: ignore[index]
        if "competitive" in enrichment.topics:
            signals["competitor"] = True  # type: ignore[index]

        if domain == "saas_sales":
            if signals.get("pain_workflow"):
                opportunities.append(
                    "Quantify the reporting/workflow pain (hours saved, error rate) and tie it to a "
                    "30-day measurable outcome — this aligns with won-deal patterns in CRM history."
                )
                missing.append(
                    "What metric defines success (e.g., report time <15 min, 95% data accuracy)?"
                )
            else:
                opportunities.append(
                    "Run a tight discovery to surface the highest-severity workflow pain and urgency."
                )
                missing.append("Which workflow is most painful today, and who feels it daily?")

            if signals.get("no_champion") or "champion" in text:
                missing.append("Who is the internal champion and what does winning look like for them?")
                risks.append(
                    "Without a named champion, discovery meetings often stall — CRM shows 2.3× longer cycles."
                )

            if signals.get("competitor"):
                opportunities.append(
                    "Position a proof-of-value sprint focused on reporting speed vs. competitor gaps."
                )
                risks.append(
                    "Feature bake-offs favor incumbents; avoid RFP-style comparisons without a POV anchor."
                )
                missing.append("What criteria will the customer use to compare vendors?")

            if signals.get("security"):
                opportunities.append(
                    "Fast-track security review with pre-filled SOC2/SSO packet — removes a top slip reason."
                )
                missing.append("Who owns security review internally, and what is their typical timeline?")
            else:
                missing.append("Any security, procurement, or legal gates before a pilot?")

            if signals.get("timeline_pressure"):
                opportunities.append(
                    "Lock a mutual action plan with decision dates to capitalize on urgency."
                )
                risks.append("Compressed timelines without MAP alignment often lead to slipped close dates.")

            if signals.get("budget"):
                missing.append("Is budget allocated this quarter, and who signs off on spend?")
            else:
                missing.append("Has budget been discussed or is this still exploratory?")

            if signals.get("integration"):
                opportunities.append(
                    "Lead with CRM sync + reporting module demo — top buying criteria in 68% of won deals."
                )

            # Memory-informed risk adjustment: past rejections on champion gaps raise urgency.
            if memory_bias.get("champion", 0) < 0:
                risks.append(
                    "Past reviews flagged champion gaps — prioritize champion identification before MAP."
                )
            if memory_bias.get("map", 0) > 0:
                opportunities.append(
                    "Historical approvals favor MAP-first approach — propose MAP within 48 hours."
                )

            if not risks:
                risks.append(
                    "Generic follow-ups without quantified pain and champion increase stall risk after discovery."
                )

        elif domain == "customer_success":
            if signals.get("support_friction") or signals.get("usage_drop"):
                opportunities.append(
                    "Launch a 30-day recovery plan with weekly adoption check-ins — reduces churn ~18% when started within 10 days."
                )
                missing.append("Which workflows are failing and for which user groups?")
            else:
                opportunities.append(
                    "Proactively reconfirm value drivers and review leading health indicators."
                )
                missing.append("What usage milestone did the customer expect by now?")

            if signals.get("renewal_risk"):
                risks.append(
                    "Renewal risk is elevated — usage dips + support spikes precede churn by 6–8 weeks."
                )
                missing.append("When is the renewal date and who is the economic buyer?")
            else:
                risks.append(
                    "If usage continues to dip unnoticed, churn risk rises before a formal renewal signal."
                )

            if signals.get("expansion"):
                opportunities.append(
                    "Expansion signal detected — pair recovery/adoption wins with an EBR to discuss growth."
                )

            if memory_bias.get("recovery", 0) > 0:
                opportunities.append(
                    "Past approvals favor structured recovery plans — replicate weekly check-in cadence."
                )

        else:
            opportunities.append("Use a domain playbook to identify next-step stakeholders and outcomes.")
            missing.append("Provide key context needed to tailor recommendations.")
            risks.append("Missing enterprise context can lead to generic or non-actionable guidance.")

        # Always include constraint discovery — critical for enterprise deals.
        missing.append(
            "Any constraints: timeline, budget, internal approvals, or security review requirements?"
        )

        # De-duplicate while preserving order.
        def _dedupe(items: List[str]) -> List[str]:
            seen: set[str] = set()
            out: List[str] = []
            for item in items:
                if item not in seen:
                    seen.add(item)
                    out.append(item)
            return out

        return OpportunityRisk(
            opportunities=_dedupe(opportunities),
            risks=_dedupe(risks),
            missing_information=_dedupe(missing),
        )

    def _build_evidence_pool(self, org_context: OrgContext) -> List[EvidenceItem]:
        evidence_pool: List[EvidenceItem] = []

        for a in org_context.knowledge_articles:
            evidence_pool.append(
                EvidenceItem(
                    label=a.get("title", "KB"),
                    excerpt=a.get("excerpt", ""),
                    source=f"knowledge_article:{a.get('id', 'KB')}",
                )
            )
        for p in org_context.playbooks:
            evidence_pool.append(
                EvidenceItem(
                    label=p.get("title", "Playbook"),
                    excerpt=p.get("excerpt", ""),
                    source=f"playbook:{p.get('id', 'PB')}",
                )
            )
        for d in org_context.product_docs:
            evidence_pool.append(
                EvidenceItem(
                    label=d.get("title", "Doc"),
                    excerpt=d.get("excerpt", ""),
                    source=f"product_doc:{d.get('id', 'DOC')}",
                )
            )
        for c in org_context.crm_history:
            evidence_pool.append(
                EvidenceItem(
                    label=f"CRM event {c.get('timestamp', '')}".strip(),
                    excerpt=c.get("text", ""),
                    source=f"crm_event:{c.get('id', 'CRM')}",
                )
            )

        return evidence_pool

    def _score_evidence_relevance(
        self,
        evidence: EvidenceItem,
        text: str,
        action_keywords: List[str],
    ) -> float:
        """Rank evidence by overlap with interaction text and action intent."""
        blob = f"{evidence.label} {evidence.excerpt} {evidence.source}".lower()
        score = 0.0
        for kw in action_keywords:
            if kw in blob:
                score += 2.0
            if kw in text and kw in blob:
                score += 1.5
        if "playbook" in evidence.source:
            score += 0.5
        if "crm_event" in evidence.source:
            score += 0.3
        return score

    def _select_evidence_for_action(
        self,
        evidence_pool: List[EvidenceItem],
        text: str,
        action_keywords: List[str],
        count: int = 2,
    ) -> List[EvidenceItem]:
        if not evidence_pool:
            return [EvidenceItem(label="No enterprise evidence", excerpt="(mock)", source="none")]

        ranked = sorted(
            evidence_pool,
            key=lambda e: self._score_evidence_relevance(e, text, action_keywords),
            reverse=True,
        )
        selected: List[EvidenceItem] = []
        seen_sources: set[str] = set()
        for item in ranked:
            if item.source in seen_sources:
                continue
            selected.append(item)
            seen_sources.add(item.source)
            if len(selected) >= count:
                break
        return selected or ranked[:count]

    def _calibrate_confidence(
        self,
        base: float,
        evidence: List[EvidenceItem],
        missing_count: int,
        memory_boost: float,
    ) -> float:
        """Adjust confidence based on evidence quality, gaps, and learned preferences."""
        evidence_boost = min(0.12, len(evidence) * 0.04)
        missing_penalty = min(0.15, missing_count * 0.03)
        raw = base + evidence_boost + memory_boost - missing_penalty
        return round(max(0.55, min(0.92, raw)), 2)

    def _recommend_next_best_actions(
        self,
        interaction: IngestedInteraction,
        org_context: OrgContext,
        analysis: OpportunityRisk,
        customer_id: str,
        domain: DecisionDomain,
    ) -> List[NextBestAction]:
        text = self._analysis_text(interaction)
        signals = self._detect_signals(text, domain)
        memory_bias = self._memory_bias_factors(customer_id, domain)
        evidence_pool = self._build_evidence_pool(org_context)
        missing_count = len(analysis.missing_information)

        action_templates: List[Dict[str, Any]] = []

        if domain == "saas_sales":
            # Always propose MAP when pain or timeline signals exist — core enterprise pattern.
            if signals.get("pain_workflow") or signals.get("timeline_pressure") or memory_bias.get("map", 0) > 0:
                action_templates.append({
                    "title": "Send a mutually agreed action plan (MAP) draft",
                    "summary": (
                        "Convert discovery insights into a 30/60-day MAP with named stakeholders, "
                        "success metrics (e.g., report time <15 min), and decision dates."
                    ),
                    "base_confidence": 0.82,
                    "memory_key": "map",
                    "keywords": ["map", "action plan", "stakeholder", "30", "60", "metric", "outcome"],
                    "rationale": (
                        "MAP acceptance correlates with +25% win probability (PB-SAAS-01). "
                        "Analysis flags quantifiable pain — MAP makes outcomes explicit for the champion."
                    ),
                })

            if signals.get("no_champion") or "champion" not in text:
                action_templates.append({
                    "title": "Draft a champion identification follow-up email",
                    "summary": (
                        "Ask who owns the outcome internally, what success looks like for them, "
                        "and offer a champion enablement kit (pitch deck + ROI one-pager)."
                    ),
                    "base_confidence": 0.79,
                    "memory_key": "champion",
                    "keywords": ["champion", "stakeholder", "enablement", "roi", "buyer"],
                    "rationale": (
                        "KB-SAAS-01 and CRM-SAAS-1 show deals stall 2.3× without a champion. "
                        "Champion enablement closes internal approvals 12 days faster (PB-SAAS-02)."
                    ),
                })

            if signals.get("security"):
                action_templates.append({
                    "title": "Initiate security fast-track packet (SOC2 + SSO)",
                    "summary": (
                        "Pre-fill security questionnaire and send SOC2/ISO + SSO audit trail docs "
                        "within 5 business days to avoid procurement slip."
                    ),
                    "base_confidence": 0.85,
                    "memory_key": "security",
                    "keywords": ["security", "soc2", "sso", "audit", "procurement", "compliance"],
                    "rationale": (
                        "Delayed security responses are the #2 slip reason (PB-SAAS-03). "
                        "DOC-SAAS-SSO shows 8-day average review when packet is complete upfront."
                    ),
                })

            if signals.get("competitor"):
                action_templates.append({
                    "title": "Propose a proof-of-value sprint vs. competitor",
                    "summary": (
                        "Offer a 2-week POV focused on reporting speed and CRM sync — "
                        "avoid feature bake-off, anchor on quantified ROI."
                    ),
                    "base_confidence": 0.80,
                    "memory_key": "qualification",
                    "keywords": ["competitor", "pov", "proof", "reporting", "roi", "analytics"],
                    "rationale": (
                        "KB-SAAS-03: POV-to-close rate is 34% higher than RFP-led cycles. "
                        "CRM-SAAS-1 notes competitor X — POV de-risks the evaluation."
                    ),
                })

            if signals.get("integration") or signals.get("pain_workflow"):
                action_templates.append({
                    "title": "Schedule a reporting + CRM sync demo",
                    "summary": (
                        "Demo executive reporting module (4hr → 15min) with live CRM sync — "
                        "addresses top buying criterion in 68% of won deals."
                    ),
                    "base_confidence": 0.77,
                    "memory_key": "qualification",
                    "keywords": ["report", "crm", "sync", "dashboard", "integrat"],
                    "rationale": (
                        "DOC-SAAS-REPORT and DOC-SAAS-API directly address the stated reporting pain. "
                        "Product-led demo accelerates champion internal selling."
                    ),
                })

            # Fallback actions when signals are sparse.
            if len(action_templates) < 2:
                action_templates.append({
                    "title": "Schedule a 20-minute stakeholder alignment call",
                    "summary": (
                        "Lock stakeholders and confirm timeline/budget constraints "
                        "so the next meeting doesn't stall."
                    ),
                    "base_confidence": 0.74,
                    "memory_key": "qualification",
                    "keywords": ["stakeholder", "timeline", "alignment", "meeting"],
                    "rationale": (
                        "KB-SAAS-02: multi-threaded deals convert at 41% vs 18% single-threaded. "
                        "Alignment call reduces stall risk flagged in analysis."
                    ),
                })

        elif domain == "customer_success":
            if signals.get("support_friction") or signals.get("usage_drop") or signals.get("renewal_risk"):
                action_templates.append({
                    "title": "Launch a 30-day at-risk recovery plan",
                    "summary": (
                        "Reconfirm value drivers, assign weekly adoption check-ins, "
                        "and escalate internally with customer consent."
                    ),
                    "base_confidence": 0.84,
                    "memory_key": "recovery",
                    "keywords": ["recovery", "adoption", "at-risk", "churn", "check-in"],
                    "rationale": (
                        "PB-CS-01: recovery within 10 days reduces churn ~18%. "
                        "CRM-CS-1 shows rising tickets + usage dip — classic leading indicators."
                    ),
                })

            action_templates.append({
                "title": "Create a health-check narrative for the customer",
                "summary": (
                    "Explain leading indicators (usage/support trends) and how they'll be "
                    "monitored during the recovery period with milestone targets."
                ),
                "base_confidence": 0.78,
                "memory_key": "recovery",
                "keywords": ["health", "usage", "support", "milestone", "adoption"],
                "rationale": (
                    "KB-CS-01 and DOC-CS-HEALTH provide explainable framing for at-risk behavior. "
                    "Transparent health narrative builds trust during recovery."
                ),
            })

            if signals.get("support_friction"):
                action_templates.append({
                    "title": "Identify failing workflows and target user groups",
                    "summary": (
                        "Run a 30-minute working session to map which workflows break, "
                        "for whom, and what 'good' looks like by day 30."
                    ),
                    "base_confidence": 0.73,
                    "memory_key": "qualification",
                    "keywords": ["workflow", "user", "support", "ticket", "broken"],
                    "rationale": (
                        "Analysis flags missing workflow detail — grounding the plan in specific "
                        "user pain prevents generic recovery steps that fail to move usage."
                    ),
                })

            if signals.get("expansion"):
                action_templates.append({
                    "title": "Schedule a quarterly executive business review (EBR)",
                    "summary": (
                        "Present ROI proof points, adoption milestones, and expansion options "
                        "to the economic buyer."
                    ),
                    "base_confidence": 0.76,
                    "memory_key": "recovery",
                    "keywords": ["ebr", "executive", "roi", "renew", "expand"],
                    "rationale": (
                        "KB-CS-02: EBRs reduce churn ~22% for accounts above $50K ARR. "
                        "Expansion signal detected — EBR converts health recovery into growth."
                    ),
                })

        else:
            action_templates.append({
                "title": "Tailor next steps using the domain playbook",
                "summary": "Map current context to known enterprise patterns and propose a safe next action.",
                "base_confidence": 0.70,
                "memory_key": "qualification",
                "keywords": ["playbook", "stakeholder", "outcome"],
                "rationale": "When context is incomplete, playbook-grounded steps reduce generic recommendations.",
            })

        # Cap at 4 actions, ensure at least 2 for primary domains.
        action_templates = action_templates[:4]
        if domain in ("saas_sales", "customer_success") and len(action_templates) < 2:
            action_templates.append({
                "title": "Draft a qualification follow-up email",
                "summary": "Gather missing context on constraints, stakeholders, and success metrics.",
                "base_confidence": 0.72,
                "memory_key": "qualification",
                "keywords": ["qualif", "discovery", "metric", "stakeholder"],
                "rationale": "Missing information in analysis — direct follow-up improves next recommendation quality.",
            })

        nbas: List[NextBestAction] = []
        for i, a in enumerate(action_templates):
            keywords = a.get("keywords", [])
            selected_evidence = self._select_evidence_for_action(evidence_pool, text, keywords, count=2)
            mem_key = a.get("memory_key", "qualification")
            mem_boost = memory_bias.get(mem_key, 0.0)
            confidence = self._calibrate_confidence(
                base=a["base_confidence"],
                evidence=selected_evidence,
                missing_count=missing_count,
                memory_boost=mem_boost,
            )

            # Enrich rationale with specific evidence IDs for explainability.
            evidence_refs = ", ".join(e.source.split(":")[-1] for e in selected_evidence[:2])
            rationale = f"{a['rationale']} Evidence: {evidence_refs}."

            nbas.append(
                NextBestAction(
                    action_id=str(uuid.uuid4()),
                    title=a["title"],
                    summary=a["summary"],
                    confidence=confidence,
                    evidence=selected_evidence,
                    rationale=rationale,
                    recommended_next_questions=[
                        analysis.missing_information[0] if analysis.missing_information else "What are the constraints?",
                        analysis.missing_information[1] if len(analysis.missing_information) > 1 else "Who are the stakeholders?",
                    ],
                )
            )

        return nbas

    def _compute_success_metrics(
        self,
        domain: DecisionDomain,
        analysis: OpportunityRisk,
        next_best_actions: List[NextBestAction],
        interaction: IngestedInteraction,
    ) -> Dict[str, Any]:
        """Domain-specific KPI estimates — business-facing, not model internals."""
        text = self._analysis_text(interaction)
        signals = self._detect_signals(text, domain)
        top_confidence = next_best_actions[0].confidence if next_best_actions else 0.7
        missing_penalty = min(0.15, len(analysis.missing_information) * 0.02)

        if domain == "saas_sales":
            win_base = 0.42
            if signals.get("pain_workflow"):
                win_base += 0.08
            if signals.get("timeline_pressure"):
                win_base += 0.05
            if signals.get("no_champion"):
                win_base -= 0.12
            if signals.get("security"):
                win_base -= 0.03
            win_prob = round(min(0.78, max(0.25, win_base + top_confidence * 0.15 - missing_penalty)), 2)

            champion_days = 14 if signals.get("no_champion") else 7
            if any("MAP" in a.title or "action plan" in a.title.lower() for a in next_best_actions):
                champion_days = max(5, champion_days - 5)

            return {
                "win_probability": {
                    "current_estimate": f"{int(win_prob * 100)}%",
                    "estimated_impact": f"Win Probability: +{int((top_confidence - 0.7) * 30)}% with top action",
                    "interpretation": "Based on champion status, pain quantification, and playbook alignment.",
                },
                "time_to_champion": {
                    "current_estimate": f"{champion_days} days",
                    "estimated_impact": "Time-to-Champion: -5 days with MAP + enablement kit",
                    "interpretation": "Days until a named internal champion is confirmed.",
                },
                "deal_velocity": {
                    "current_estimate": "45–60 days" if signals.get("security") else "30–45 days",
                    "estimated_impact": "Sales Cycle: -12 days with security fast-track",
                    "interpretation": "Estimated close timeline assuming MAP acceptance.",
                },
            }

        if domain == "customer_success":
            churn_base = 0.35 if signals.get("renewal_risk") or signals.get("usage_drop") else 0.18
            if signals.get("support_friction"):
                churn_base += 0.10
            churn_risk = round(min(0.65, max(0.10, churn_base - top_confidence * 0.12 + missing_penalty)), 2)

            return {
                "churn_risk": {
                    "current_estimate": f"{int(churn_risk * 100)}%",
                    "estimated_impact": f"Churn Risk Reduction: -{int(top_confidence * 18)}% with recovery plan",
                    "interpretation": "Based on usage trends, support volume, and renewal proximity.",
                },
                "health_score": {
                    "current_estimate": f"{max(35, int(100 - churn_risk * 100))}/100",
                    "estimated_impact": "Health Score: +12 pts after 30-day adoption plan",
                    "interpretation": "Composite of usage, support, and milestone attainment.",
                },
                "renewal_confidence": {
                    "current_estimate": f"{int((1 - churn_risk) * 100)}%",
                    "estimated_impact": "Renewal Confidence: +15% with EBR cadence",
                    "interpretation": "Likelihood of renewal at current trajectory.",
                },
            }

        return {
            "decision_quality": {
                "current_estimate": f"{int(top_confidence * 100)}%",
                "estimated_impact": "Actionability: improves with more enterprise context",
                "interpretation": "Generic domain — provide richer interaction text for sharper KPIs.",
            },
        }

    def _make_natural_language_summary(
        self,
        analysis: OpportunityRisk,
        next_best_actions: List[NextBestAction],
        success_metrics: Dict[str, Any],
    ) -> str:
        opp = analysis.opportunities[0] if analysis.opportunities else ""
        miss = analysis.missing_information[0] if analysis.missing_information else ""
        top_action = next_best_actions[0].title if next_best_actions else "next steps"

        metric_hint = ""
        first_metric = next(iter(success_metrics.values()), None)
        if isinstance(first_metric, dict) and first_metric.get("estimated_impact"):
            metric_hint = f" Expected impact: {first_metric['estimated_impact']}."

        return (
            f"Proposed path: {opp} "
            f"(We're missing: {miss}). "
            f"Top action: {top_action}.{metric_hint} "
            f"Next best actions focus on turning uncertainty into concrete, evidence-backed steps."
        )

    def _overall_confidence(self, next_best_actions: List[NextBestAction]) -> float:
        if not next_best_actions:
            return 0.0
        return sum(a.confidence for a in next_best_actions) / len(next_best_actions)
