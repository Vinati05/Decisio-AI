- [x] Repo exploration (backend/main.py, frontend/server.js, docker-compose.yml)
- [x] Implement agentic core (MemoryStore, MockKnowledge, PlannerAgent) in backend/ai_platform.py
- [x] Add backend workflow endpoints in backend/main.py: /workflow/start, /workflow/review, /memory/{customer_id}
- [x] Fix & verify container actually serves updated OpenAPI (confirmed routes present in running container)
- [x] Verify end-to-end workflow via curl: start -> review -> memory learning
- [x] Upgrade frontend UI to match human-in-the-loop workflow (inputs, approve/reject, show evidence)
- [x] Update frontend styling/copy to feel human (not “AI dashboard”) while still showing evidence/confidence



## Layer 1: Strengthen Business Depth & Domain Modeling + Robust Dynamic Ingestion

**Goal**: Deepen domain knowledge + make ingestion handle real dynamic inputs (notes, transcripts, emails) intelligently. Fully backward-compatible.

- [x] **Enhance Ingestion**:
  - Improve input schema to support structured + unstructured dynamic content (raw text, email format, transcript format with speaker labels).
  - Add lightweight preprocessing (extract key entities, sentiment, action items) before passing to Planner.
- [x] Expand `MockKnowledge` with richer domain content (SaaS Sales primary).
- [x] Enhance `_analyze_business_context` to better leverage ingested dynamic data.
- [x] Improve `_recommend_next_best_actions` with stronger linking to ingested content.
- [x] Add domain-specific success metrics and KPI tracking in memory.
- [x] Add sample dynamic inputs (transcripts/emails) in `examples/` folder.
- [x] Update README with improved ingestion examples.



## Layer 2: Real Retrieval & Multi-Source Reasoning

**Goal**: Replace heavy mocking with actual retrieval to show enterprise-grade platform capability.

- [x] Introduce vector embeddings + simple vector store (ChromaDB or FAISS) for knowledge base.
- [x] Create a dedicated `RetrieverAgent` (or tool) that Planner can orchestrate.
- [x] Support multiple knowledge sources (e.g., load from JSON/YAML files or folder).
- [x] Add basic CRM simulation (SQLite or enhanced in-memory with query capability).
- [x] Implement configurable business rules per domain (YAML config).
- [x] Update Planner to dynamically decide retrieval strategy based on interaction.
- [x] Add retrieval evidence in explanations (source + relevance score).
- [x] Update README with retrieval demo examples.



## Layer 3: Advanced Agent Orchestration & Extensibility

**Goal**: Demonstrate a true reusable, planner-driven multi-agent system as required by the hackathon (Planner Agent dynamically orchestrating specialized agents).

- [ ] Refactor `PlannerAgent` to use a lightweight orchestration framework (LangGraph recommended for stateful workflows and human-in-the-loop, or simple step-based if time-constrained).
- [ ] Create specialized agents (each with clear responsibilities):
  - `AnalyzerAgent` (business context, opportunities/risks/missing info)
  - `RecommenderAgent` (generates explainable Next Best Actions with evidence)
  - `ExplainerAgent` (natural language summary, confidence, rationale)
  - `MemoryAgent` (handles learning and retrieval from shared memory)
- [ ] Define a clean **reusable Tool architecture**:
  - `search_knowledge`, `query_crm`, `generate_draft_email`, `get_memory_insights`, etc.
- [ ] Make the Planner dynamically decide which agents/tools to call based on:
  - Domain
  - Interaction type
  - Retrieved context
  - Confidence thresholds from business rules
- [ ] Add visible **agent trace / orchestration log** (in response or UI) showing the flow (for demo and explainability).
- [ ] Implement extensibility demo:
  - Easy way to add a new domain or agent (config + registration pattern).
  - Documentation example of adding a new "Staffing" domain agent.
- [ ] Update architecture documentation (README + diagram) showing Planner → Specialized Agents → Tools → Shared Memory pattern.



## Layer 4: UX & Human-in-the-Loop Polish

**Goal**: Create an intuitive, judge-friendly interface that clearly demonstrates human-in-the-loop review, explainability, and memory — as required in the workflow.

- [ ] Frontend improvements:
  - Rich input form supporting multiple source types (email, transcript with speaker labels, meeting notes).
  - Clear display of **ingestion enrichment** (participants, topics, sentiment, open questions).
  - **Evidence cards** with source, excerpt, and relevance score (collapsible).
  - Smooth approval/rejection flow with reviewer notes and immediate feedback.
  - Memory / History view showing learned insights and KPI improvements over time.
  - Domain selector + sample scenario loader.
- [ ] Visual enhancements:
  - Confidence gauges or progress bars.
  - Narrative "spark" summaries.
  - Agent trace visualization (optional but impressive).
- [ ] Add "Ask Clarifying Questions" feature (using LLM or predefined) before final recommendation.
- [ ] Polish UI to feel premium, cinematic, and human-first (as per current README tone).
- [ ] Prepare 5-minute demo script focusing on:
  - Dynamic ingestion → Retrieval → Analysis → Recommendation → Human Review → Memory Learning loop.




## Layer 5: Production-Ready + Innovation (Differentiation)

**Goal**: Show reusability, extensibility, measurable outcomes, and thoughtful engineering — key to the 70% Platform score.

- [ ] Persistence: Replace in-memory `MemoryStore` with SQLite (or PostgreSQL) for customer interactions, runs, reviews, and lessons.
- [ ] Full LLM Integration: Use Ollama (or Grok/OpenAI) across analysis + recommendations with configurable fallback.
- [ ] Evaluation Framework:
  - Add `/evaluate` endpoint that runs multiple simulated scenarios and computes metrics (acceptance rate, KPI improvement, win probability lift, etc.).
  - Document evaluation methodology clearly in README.
- [ ] Configurable Workflows: Expand `business_rules.yaml` + make Planner respect complex rules.
- [ ] Action Execution Stubs: Show how approved recommendations could trigger real actions (draft email, CRM update, calendar invite).
- [ ] Extensibility Showcase:
  - Easy registration of new agents/domains.
  - Example of adding a new domain (e.g., Staffing).
- [ ] Deployment & Documentation:
  - Clear setup instructions (local + one-click deploy options).
  - Architecture diagram (Planner + Agents + Tools + Memory + Retrieval).
  - 5-minute Architecture Walkthrough script/slides.
- [ ] Final Polish:
  - Excellent README with screenshots, video links, and business outcomes.
  - Add badges, project description, and evaluation methodology.




## Final Deliverables & Polish

- [ ] Record **5-minute Demo Video** (platform + SaaS Sales use case).
- [ ] Record **5-minute Architecture Walkthrough** explaining key decisions.
- [ ] Complete GitHub Repository:
  - Excellent README with setup, screenshots, architecture diagram.
  - Clear documentation of business domain, metrics, and evaluation approach.
  - Setup instructions (local + one-click deploy if possible).
- [ ] Add evaluation methodology section (how you measured success / simulated outcomes).


- [ ] Update README with demo + architecture walkthrough notes

