- [x] Repo exploration (backend/main.py, frontend/server.js, docker-compose.yml)
- [x] Implement agentic core (MemoryStore, MockKnowledge, PlannerAgent) in backend/ai_platform.py
- [x] Add backend workflow endpoints in backend/main.py: /workflow/start, /workflow/review, /memory/{customer_id}
- [x] Fix & verify container actually serves updated OpenAPI (confirmed routes present in running container)
- [x] Verify end-to-end workflow via curl: start -> review -> memory learning
- [x] Upgrade frontend UI to match human-in-the-loop workflow (inputs, approve/reject, show evidence)
- [x] Update frontend styling/copy to feel human (not “AI dashboard”) while still showing evidence/confidence



## Layer 1: Strengthen Business Depth & Domain Modeling (High Business Score Impact)

**Goal**: Deepen domain understanding, enrich knowledge base, improve analysis/recommendations, and add measurable success metrics. This layer keeps everything fully functional and backward-compatible.

- [ ] Choose **SaaS Sales** as primary domain and expand `MockKnowledge` with 8–12 realistic entries across categories (knowledge_articles, playbooks, product_docs, crm_history).
- [ ] Enhance `_analyze_business_context` to better detect opportunities, risks, and missing information with richer heuristics.
- [ ] Improve `_recommend_next_best_actions` to generate more specific, playbook-aligned actions with stronger evidence linking.
- [ ] Add domain-specific **success metrics** to `WorkflowStartResult` and `explanation_bundle` (e.g., Win Probability, Time-to-Champion, Churn Risk Reduction).
- [ ] Update `learn_from_outcome` and memory retrieval to track simulated KPIs for continuous improvement demonstration.
- [ ] Add 2–3 diverse sample interaction scenarios (in README or a new `examples/` folder) showing before/after memory improvement.
- [ ] Update README with Layer 1 achievements and screenshots of improved recommendations.



- [ ] Update README with demo + architecture walkthrough notes

