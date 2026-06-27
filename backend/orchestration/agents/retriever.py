from __future__ import annotations

from typing import Any, List

from orchestration.agents.base import BaseAgent
from orchestration.models.agent_models import AgentResult, RetrievedDocument, RetrievalResult, ToolUsageRecord
from orchestration.models.workflow_models import WorkflowContext
from orchestration.registries.tools import ToolRegistry


class RetrieverAgent(BaseAgent):
    """Orchestrates knowledge search, CRM, business rules, and memory retrieval."""

    name = "retriever"

    def __init__(self, engine: Any, tool_registry: ToolRegistry) -> None:
        self.engine = engine
        self.tools = tool_registry

    def execute(self, ctx: WorkflowContext) -> AgentResult:
        if ctx.interaction is None:
            return AgentResult(
                agent_name=self.name,
                success=False,
                decision="skipped",
                reason="No interaction to retrieve against",
            )

        tool_usage: List[ToolUsageRecord] = []
        errors: List[str] = []
        domain = ctx.domain
        customer_id = ctx.customer_id
        query_text = ctx.interaction.canonical_text

        domain_rules, dur, err = self.tools.execute("business_rules", domain=domain)
        tool_usage.append(
            ToolUsageRecord("business_rules", err is None, dur, summary=f"rules for {domain}", error=err)
        )
        min_rel = 0.50
        if isinstance(domain_rules, dict):
            min_rel = domain_rules.get("min_relevance_score", 0.50)

        # Knowledge search via tool
        search_results, dur, err = self.tools.execute(
            "knowledge_search", query=query_text, domain=domain, top_k=6
        )
        tool_usage.append(
            ToolUsageRecord(
                "knowledge_search",
                err is None,
                dur,
                summary=f"{len(search_results or [])} hits",
                error=err,
            )
        )
        if err:
            errors.append(f"knowledge_search: {err}")

        # CRM via tool — degrade gracefully
        crm_history, dur, err = self.tools.execute("crm_lookup", customer_id=customer_id, domain=domain)
        tool_usage.append(
            ToolUsageRecord(
                "crm_lookup",
                err is None,
                dur,
                summary=f"{len(crm_history or [])} events",
                error=err,
            )
        )
        if err:
            errors.append(f"crm_lookup: {err}")
            crm_history = []

        # Build OrgContext using existing retriever logic when available
        org_context = None
        try:
            if hasattr(self.engine, "retriever"):
                org_context = self.engine.retriever.retrieve(
                    query=query_text,
                    customer_id=customer_id,
                    domain=domain,  # type: ignore[arg-type]
                    min_relevance=min_rel,
                )
            else:
                org_context = self.engine.knowledge.get_context(domain)  # type: ignore[arg-type]
        except Exception as exc:
            errors.append(f"retriever: {exc}")
            org_context = self.engine.knowledge.get_context(domain)  # type: ignore[arg-type]

        ctx.org_context = org_context

        documents: List[RetrievedDocument] = []
        citations: List[str] = []
        relevance_scores: dict[str, float] = {}

        for a in org_context.knowledge_articles:
            doc = RetrievedDocument(
                label=a.get("title", "Article"),
                excerpt=a.get("excerpt", ""),
                source=f"knowledge_article:{a.get('id', 'KB')}",
                relevance=float(a.get("relevance", 1.0)),
                doc_type="knowledge_article",
            )
            documents.append(doc)
            citations.append(doc.source)
            relevance_scores[doc.source] = doc.relevance

        for p in org_context.playbooks:
            doc = RetrievedDocument(
                label=p.get("title", "Playbook"),
                excerpt=p.get("excerpt", ""),
                source=f"playbook:{p.get('id', 'PB')}",
                relevance=float(p.get("relevance", 1.0)),
                doc_type="playbook",
            )
            documents.append(doc)
            citations.append(doc.source)
            relevance_scores[doc.source] = doc.relevance

        for d in org_context.product_docs:
            doc = RetrievedDocument(
                label=d.get("title", "Doc"),
                excerpt=d.get("excerpt", ""),
                source=f"product_doc:{d.get('id', 'DOC')}",
                relevance=float(d.get("relevance", 1.0)),
                doc_type="product_doc",
            )
            documents.append(doc)
            citations.append(doc.source)
            relevance_scores[doc.source] = doc.relevance

        for c in org_context.crm_history:
            doc = RetrievedDocument(
                label=f"CRM {c.get('timestamp', '')}".strip(),
                excerpt=c.get("text", ""),
                source=f"crm_event:{c.get('id', 'CRM')}",
                relevance=float(c.get("relevance", 1.0)),
                doc_type="crm_event",
            )
            documents.append(doc)
            citations.append(doc.source)
            relevance_scores[doc.source] = doc.relevance

        retrieval_result = RetrievalResult(
            documents=documents,
            relevance_scores=relevance_scores,
            citations=citations[:12],
            retrieval_summary=(
                f"{len(documents)} documents "
                f"({len(org_context.playbooks)} playbooks, "
                f"{len(org_context.crm_history)} CRM events)"
            ),
            sources_used=list({d.doc_type for d in documents}),
            errors=errors,
        )
        ctx.retrieval_result = retrieval_result

        avg_rel = (
            sum(relevance_scores.values()) / len(relevance_scores) if relevance_scores else 0.5
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=round(avg_rel, 2),
            decision="retrieved",
            reason=retrieval_result.retrieval_summary,
            data=retrieval_result,
            tool_usage=tool_usage,
        )
