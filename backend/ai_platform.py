from __future__ import annotations

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


@dataclass
class IngestedInteraction:
    interaction_id: str
    customer_id: str
    domain: DecisionDomain
    source_type: Literal["email", "meeting_notes", "transcript", "crm_update", "conversation"]
    raw_text: str
    canonical_text: str
    ingested_at: str


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
        lessons = []
        for (cid, _domain), items in self._lessons.items():
            if cid == customer_id:
                lessons.extend(items)

        return {
            "customer_id": customer_id,
            "saved_lessons_learned": lessons,
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
        self._lessons[key].append(
            {
                "run_id": run_id,
                "review_status": review_status,
                "reviewer_notes": reviewer_notes,
                "learned_at": datetime.utcnow().isoformat() + "Z",
            }
        )

    def get_lessons_for_customer(self, customer_id: str, domain: DecisionDomain) -> List[Dict[str, Any]]:
        return list(self._lessons.get((customer_id, domain), []))


class MockKnowledge:
    """Hard-coded knowledge so the hackathon demo works offline."""

    def __init__(self) -> None:
        # Keep small; just enough to produce explainable evidence.
        self._articles = {
            "saas_sales": [
                {
                    "id": "KB-SAAS-01",
                    "title": "Discovery: qualify pain + champion",
                    "excerpt": "Focus on pain severity, urgency, current workaround, and identify a champion.",
                },
            ],
            "customer_success": [
                {
                    "id": "KB-CS-01",
                    "title": "Health scoring: leading indicators",
                    "excerpt": "Usage drops and support escalations often precede churn.",
                },
            ],
        }

        self._playbooks = {
            "saas_sales": [
                {
                    "id": "PB-SAAS-01",
                    "title": "Mutual action plan (MAP) after discovery",
                    "excerpt": "Propose 30/60-day outcomes, confirm stakeholders, and agree on next meeting agenda.",
                }
            ],
            "customer_success": [
                {
                    "id": "PB-CS-01",
                    "title": "At-risk account recovery",
                    "excerpt": "Reconfirm value drivers, execute an adoption plan, and escalate internally with customer consent.",
                }
            ],
        }

        self._product_docs = {
            "saas_sales": [
                {
                    "id": "DOC-SAAS-API",
                    "title": "CRM sync integration",
                    "excerpt": "Syncs meeting outcomes and notes into CRM fields to keep stakeholders aligned.",
                }
            ],
            "customer_success": [
                {
                    "id": "DOC-CS-HEALTH",
                    "title": "Health dashboard",
                    "excerpt": "Shows usage trends and correlates them with support and adoption milestones.",
                }
            ],
        }

        self._crm_history = {
            "saas_sales": [
                {
                    "id": "CRM-1",
                    "timestamp": "2026-06-10",
                    "text": "Call summary: customer wants faster reporting; no clear champion identified.",
                },
            ],
            "customer_success": [
                {
                    "id": "CRM-2",
                    "timestamp": "2026-06-12",
                    "text": "Support tickets rising; product usage dipped last 2 weeks.",
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
        customer_id = str(payload["customer_id"])
        domain = payload.get("domain", "saas_sales")
        domain = domain if domain in ("saas_sales", "customer_success", "staffing", "energy") else "saas_sales"

        source_type = payload.get("source_type", "meeting_notes")
        raw_text = str(payload.get("interaction_text", ""))

        interaction = self._ingest_interaction(
            customer_id=customer_id,
            domain=domain,  # type: ignore[arg-type]
            source_type=source_type,
            raw_text=raw_text,
        )
        self.memory.put_interaction(interaction)

        org_context = self.knowledge.get_context(domain)  # type: ignore[arg-type]

        analysis = self._analyze_business_context(interaction, org_context, domain)  # type: ignore[arg-type]

        next_best_actions = self._recommend_next_best_actions(
            interaction=interaction,
            org_context=org_context,
            analysis=analysis,
            customer_id=customer_id,
            domain=domain,  # type: ignore[arg-type]
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

        explanation_bundle = {
            "evidence_summary": {
                "num_articles": len(org_context.knowledge_articles),
                "num_playbooks": len(org_context.playbooks),
                "num_product_docs": len(org_context.product_docs),
                "num_crm_events": len(org_context.crm_history),
            },
            "natural_language_summary": self._make_natural_language_summary(analysis, next_best_actions),
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
        )
        self.memory.put_run(result)
        return result

    def _ingest_interaction(
        self,
        customer_id: str,
        domain: DecisionDomain,
        source_type: str,
        raw_text: str,
    ) -> IngestedInteraction:
        canonical = raw_text.strip()
        # Very small normalization: this makes ingestion feel "real".
        if not canonical:
            canonical = "(No interaction text provided)"

        return IngestedInteraction(
            interaction_id=str(uuid.uuid4()),
            customer_id=customer_id,
            domain=domain,
            source_type=source_type if source_type in ("email", "meeting_notes", "transcript", "crm_update", "conversation") else "meeting_notes",
            raw_text=raw_text,
            canonical_text=canonical,
            ingested_at=datetime.utcnow().isoformat() + "Z",
        )

    def _analyze_business_context(self, interaction: IngestedInteraction, org_context: OrgContext, domain: DecisionDomain) -> OpportunityRisk:
        text = interaction.canonical_text.lower()
        lessons = self.memory.get_lessons_for_customer(interaction.customer_id, domain)
        _ = lessons  # used for biasing; currently we only use presence to slightly adjust.

        opportunities: List[str] = []
        risks: List[str] = []
        missing: List[str] = []

        if domain == "saas_sales":
            if "pain" in text or "problem" in text or "report" in text or "slow" in text:
                opportunities.append("Align on the most painful workflow and quantify impact (time saved / risk reduced).")
                missing.append("What metric defines success for this customer (e.g., time-to-report, accuracy, adoption)?")
            else:
                opportunities.append("Start with a tight discovery to confirm urgency and desired outcomes.")
                missing.append("Which stakeholder is the decision maker/champion?")

            risks.append("Without a champion and measurable outcome, meetings may stall after discovery.")

        elif domain == "customer_success":
            if "ticket" in text or "issue" in text or "escalat" in text:
                opportunities.append("Turn support friction into a recovery plan tied to value drivers.")
                missing.append("Which workflows are currently failing and for whom?")
            else:
                opportunities.append("Reconfirm value drivers and check leading indicators for at-risk behavior.")
                missing.append("What usage milestone did the customer expect by now?")

            risks.append("If usage continues to dip, churn risk rises before a formal renewal signal.")

        else:
            opportunities.append("Use a domain playbook to identify next-step stakeholders and outcomes.")
            missing.append("Provide key context needed to tailor recommendations.")
            risks.append("Missing enterprise context can lead to generic or non-actionable guidance.")

        # Always include a missing-info prompt.
        missing.append("Any constraints: timeline, budget, internal approvals, or security/security-review items?")

        return OpportunityRisk(
            opportunities=opportunities,
            risks=risks,
            missing_information=missing,
        )

    def _recommend_next_best_actions(
        self,
        interaction: IngestedInteraction,
        org_context: OrgContext,
        analysis: OpportunityRisk,
        customer_id: str,
        domain: DecisionDomain,
    ) -> List[NextBestAction]:
        # Build evidence pool from mock enterprise sources.
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

        # Choose top 3 evidence items deterministically.
        evidence_pool = evidence_pool[:3] if evidence_pool else [
            EvidenceItem(label="No enterprise evidence", excerpt="(mock)", source="none")
        ]

        # Domain-specific NBA templates.
        if domain == "saas_sales":
            actions = [
                {
                    "title": "Send a mutually agreed action plan (MAP) draft",
                    "summary": "Turn the meeting insights into a 30/60-day MAP, including stakeholders and success metrics.",
                    "confidence": 0.84,
                    "rationale": "MAP drafts follow the enterprise playbook pattern and address missing champion/metrics explicitly.",
                },
                {
                    "title": "Draft a qualification follow-up email",
                    "summary": "Ask for decision maker (champion) and the success metric that defines the outcome.",
                    "confidence": 0.78,
                    "rationale": "The analysis flags missing champion/metrics; the follow-up email is the next best information-gathering step.",
                },
                {
                    "title": "Schedule a 20-minute stakeholder alignment call",
                    "summary": "Lock stakeholders and confirm timeline constraints so the next meeting doesn't stall.",
                    "confidence": 0.74,
                    "rationale": "The risk notes meetings may stall; alignment scheduling reduces that risk early.",
                },
            ]
        elif domain == "customer_success":
            actions = [
                {
                    "title": "Propose an at-risk recovery plan",
                    "summary": "Reconfirm value drivers, map the next adoption milestone, and outline escalation steps with consent.",
                    "confidence": 0.82,
                    "rationale": "Recovery plans match the customer success playbook and respond to the churn risk framing.",
                },
                {
                    "title": "Create a health-check narrative",
                    "summary": "Explain leading indicators (usage/support) and how they'll be monitored during the recovery period.",
                    "confidence": 0.76,
                    "rationale": "Health scoring appears in the mock knowledge base and supports explainable confidence.",
                },
                {
                    "title": "Ask for the failing workflow + target users",
                    "summary": "Identify which workflows are breaking and for whom so the plan is grounded in reality.",
                    "confidence": 0.71,
                    "rationale": "The analysis includes a missing-info question; asking it directly improves actionability.",
                },
            ]
        else:
            actions = [
                {
                    "title": "Tailor next steps using the domain playbook",
                    "summary": "Map current context to known enterprise patterns and propose a safe next action.",
                    "confidence": 0.7,
                    "rationale": "When context is incomplete, playbook-grounded steps reduce generic recommendations.",
                }
            ]

        nbas: List[NextBestAction] = []
        for i, a in enumerate(actions):
            selected_evidence = evidence_pool[:2]  # keep it tight & human-readable
            nbas.append(
                NextBestAction(
                    action_id=str(uuid.uuid4()),
                    title=a["title"],
                    summary=a["summary"],
                    confidence=a["confidence"],
                    evidence=selected_evidence,
                    rationale=a["rationale"],
                    recommended_next_questions=[
                        analysis.missing_information[0] if analysis.missing_information else "What are the constraints?",
                        analysis.missing_information[1] if len(analysis.missing_information) > 1 else "Who are the stakeholders?",
                    ],
                )
            )

        return nbas

    def _make_natural_language_summary(self, analysis: OpportunityRisk, next_best_actions: List[NextBestAction]) -> str:
        opp = next((o for o in analysis.opportunities), "")
        miss = analysis.missing_information[0] if analysis.missing_information else ""
        return (
            f"Proposed path: {opp} "
            f"(We’re missing: {miss}). "
            f"Next best actions focus on turning that uncertainty into concrete steps." 
        )

    def _overall_confidence(self, next_best_actions: List[NextBestAction]) -> float:
        if not next_best_actions:
            return 0.0
        return sum(a.confidence for a in next_best_actions) / len(next_best_actions)

