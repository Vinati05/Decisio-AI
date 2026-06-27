
A polished, judge-friendly demo experience with a premium visual identity and a storytelling-driven interaction layer.

Run:
```bash
docker compose up --build
```

Highlights:
- Premium visual direction with a cinematic, editorial feel
- Dynamic planner recommendations with a more human, narrative tone
- A persistent "spark" experience that lets the demo feel memorable

Backend: http://localhost:8000/docs
Frontend: http://localhost:3000

---

## Layer 1 Completed

Layer 1 deepens business intelligence and **robust dynamic ingestion** without changing architecture or breaking existing flows (ingestion, planner orchestration, human-in-the-loop review, memory, frontend compatibility).

### What improved

| Area | Change |
|------|--------|
| **Dynamic ingestion** | `CustomerInteraction` input schema supports raw text, email (subject/from/body), transcripts (`Speaker: text`), and meeting notes (date/context/notes). `_preprocess_interaction` detects format and extracts participants, topics, action items, sentiment, and open questions |
| **MockKnowledge** | 12 SaaS Sales entries (3 articles, 3 playbooks, 3 product docs, 3 CRM events) + 7 Customer Success entries with detailed excerpts for evidence linking |
| **Business analysis** | Nuanced keyword heuristics + ingestion enrichment (participants, open questions, sentiment) + memory bias from past approvals/rejections |
| **Recommendations** | 2–4 scenario-specific Next Best Actions with relevance-scored evidence and calibrated confidence (0.55–0.92) |
| **Success metrics** | Domain KPIs on `WorkflowStartResult.success_metrics` and `explanation_bundle.success_metrics` |
| **Memory & learning** | `learn_from_outcome` stores KPI snapshots; `get_memory` returns insights, approval rate, and KPI history |

### Example inputs (`examples/`)

Three ready-to-run payloads:

```bash
# Email-style input
curl -s -X POST http://localhost:8000/workflow/start \
  -H "Content-Type: application/json" \
  -d @examples/email_input.json | python3 -m json.tool

# Transcript-style input (Speaker: lines)
curl -s -X POST http://localhost:8000/workflow/start \
  -H "Content-Type: application/json" \
  -d @examples/transcript_input.json | python3 -m json.tool

# Meeting notes with date + attendees
curl -s -X POST http://localhost:8000/workflow/start \
  -H "Content-Type: application/json" \
  -d @examples/meeting_notes_input.json | python3 -m json.tool
```

**Ingestion enrichment in response** (`explanation_bundle.ingestion_enrichment`):

```json
{
  "detected_format": "email",
  "participants": ["Jordan Lee, VP Operations <jordan.lee@acmecorp.com>"],
  "topics": ["reporting pain", "champion gap", "competitive", "security", "timeline"],
  "action_items_mentioned": ["a mutual action plan by end of month"],
  "sentiment": "mixed",
  "open_questions": ["Who on your side can help us build an internal business case?"]
}
```

### Example: SaaS Sales workflow start (raw text — still supported)

```bash
curl -s -X POST http://localhost:8000/workflow/start \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-1001",
    "domain": "saas_sales",
    "source_type": "meeting_notes",
    "interaction_text": "VP Ops wants faster reporting (4hr manual). No champion yet. Competitor X mentioned. IT asked about SSO."
  }' | python3 -m json.tool
```

**Sample output (abbreviated):**

```json
{
  "success_metrics": {
    "win_probability": {
      "current_estimate": "58%",
      "estimated_impact": "Win Probability: +3% with top action",
      "interpretation": "Based on champion status, pain quantification, and playbook alignment."
    },
    "time_to_champion": {
      "current_estimate": "9 days",
      "estimated_impact": "Time-to-Champion: -5 days with MAP + enablement kit"
    }
  },
  "next_best_actions": [
    {
      "title": "Send a mutually agreed action plan (MAP) draft",
      "confidence": 0.86,
      "evidence": [
        { "label": "Mutual action plan (MAP) after discovery", "source": "playbook:PB-SAAS-01" },
        { "label": "Discovery call: VP Ops wants faster reporting...", "source": "crm_event:CRM-SAAS-1" }
      ],
      "rationale": "MAP acceptance correlates with +25% win probability (PB-SAAS-01)... Evidence: PB-SAAS-01, CRM-SAAS-1."
    },
    {
      "title": "Initiate security fast-track packet (SOC2 + SSO)",
      "confidence": 0.88
    }
  ],
  "explanation_bundle": {
    "success_metrics": { "...": "..." },
    "natural_language_summary": "Proposed path: Quantify the reporting/workflow pain... Expected impact: Win Probability: +3% with top action."
  }
}
```

### Example: Memory after approval

```bash
# Approve a run (use review_id from workflow/start response)
curl -s -X POST http://localhost:8000/workflow/review \
  -H "Content-Type: application/json" \
  -d '{"review_id": "<REVIEW_ID>", "status": "approved", "reviewer_notes": "MAP approach worked last time"}'

# Check learned insights
curl -s http://localhost:8000/memory/CUST-1001 | python3 -m json.tool
```

**Sample memory response:**

```json
{
  "learned_insights": [
    "Past approvals favor: Send a mutually agreed action plan (MAP) draft (1 approved run(s) on record).",
    "Observed KPI movement on 'win_probability': Win Probability: +3% with top action (latest approved run)."
  ],
  "outcome_summary": { "total_runs": 1, "approved": 1, "rejected": 0, "approval_rate": 1.0 },
  "kpi_history": { "win_probability": ["Win Probability: +3% with top action"] }
}
```

### Sample interaction scenarios

1. **SaaS — reporting pain + no champion + competitor** → MAP draft, champion follow-up, POV sprint, security packet (when SSO mentioned)
2. **SaaS — sparse context** → stakeholder alignment call + qualification email
3. **Customer Success — tickets + usage dip** → 30-day recovery plan, health narrative, workflow discovery session

Re-run the same customer after approval to see memory-biased confidence and analysis adjustments.

---

## Layer 2 Completed: Real Retrieval & Multi-Source Reasoning

Layer 2 modernizes the knowledge base with real file ingestion, an SQLite CRM database simulation, dynamic configurable rules, and a **Dual-Engine Vector Store** featuring ChromaDB and Sentence-Transformers (with a zero-dependency, pure-Python TF-IDF cosine-similarity fallback).

### What improved

| Area | Change |
|------|--------|
| **Knowledge Base Ingestion** | Dynamic loaders in `KnowledgeBase` parse real files from `backend/knowledge/` (supporting YAML/JSON structure) for articles, playbooks, and product documentation. |
| **Dual-Engine Vector Store** | Ephemeral ChromaDB client embeds and indexes documents using `all-MiniLM-L6-v2`. If ChromaDB/PyTorch fail to install or initialize, the system seamlessly falls back to a pure-Python TF-IDF vectorizer + Cosine Similarity search. |
| **SQLite CRM Simulator** | CRM updates are seeded and stored in a local SQLite database (`crm.db`) on startup. Planner queries this simulator via customer ID to trace actual account history. |
| **Configurable Business Rules** | Domain rules, priorities, minimum relevance filters, and confidence clamps are managed in `backend/config/business_rules.yaml`. The Planner respects these parameters. |
| **Grounded Citations & Relevance** | Rationale for recommendations explicitly cites retrieved documents and their relevance score (e.g., `PB-SAAS-03 (Relevance: 0.51)`). |

### Example Query and Retrieved Evidence

Request:
```bash
curl -s -X POST http://127.0.0.1:8000/workflow/start \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-1001",
    "domain": "saas_sales",
    "interaction_text": "discovery and mutual action plan security SOC2 review SSO crm sync competitor"
  }' | python3 -m json.tool
```

Sample output:
```json
{
  "next_best_actions": [
    {
      "title": "Initiate security fast-track packet (SOC2 + SSO)",
      "confidence": 0.73,
      "evidence": [
        {
          "label": "Mutual action plan (MAP) after discovery",
          "excerpt": "...",
          "source": "playbook:PB-SAAS-03",
          "relevance": 0.51
        }
      ],
      "rationale": "Delayed security responses are the #2 slip reason (PB-SAAS-03). DOC-SAAS-SSO shows 8-day average review when packet is complete upfront. Grounded in: PB-SAAS-03 (Relevance: 0.51), CRM-SAAS-2 (Relevance: 1.00)."
    }
  ]
}
```

### New Setup Instructions

All dependencies (including `chromadb`, `sentence-transformers`, `PyYAML`, `scikit-learn`, `numpy`) are defined in `backend/requirements.txt`.
To start the services:
```bash
docker compose up --build
```
On startup, the backend automatically initializes and seeds `crm.db` and downloads/sets up the semantic search embeddings model. If the environment does not support compiling/downloading large machine learning wheels, it falls back to the lightweight built-in TF-IDF engine.

---

## Ollama Local LLM Enhancement

The planner can now enhance the business analysis step and Next Best Action recommendations with a local Ollama model, while keeping the existing rule-based analyzer and recommendation templates as reliable fallbacks. By default, `PlannerAgent` uses `llama3.2`; choose another model with:

```bash
OLLAMA_MODEL=mistral docker compose up --build
```

If Ollama is not running, the model is not pulled, the container cannot reach the host Ollama daemon, or the model returns malformed structured output, the workflow automatically falls back to deterministic rule-based analysis and recommendations. The response includes `explanation_bundle.analysis_engine` and `explanation_bundle.recommendation_engine` so demos can show whether Ollama or the fallback path produced each stage.

Even when Ollama proposes recommendations, Decisio-AI still performs local evidence linking, confidence calibration, memory biasing, citation formatting, success metric calculation, and human-in-the-loop gating.

For local enhancement, install and run Ollama separately, then pull the default model:

```bash
ollama pull llama3.2
ollama serve
```

When running the backend in Docker and Ollama on the host, set `OLLAMA_HOST` if needed:

```bash
OLLAMA_HOST=http://host.docker.internal:11434 docker compose up --build
```

Fallback behavior means this is optional; `docker compose up --build` remains fully runnable without Ollama.

### Ollama troubleshooting

Check host Ollama first:

```bash
ollama list
ollama pull llama3.2
ollama serve
```

Then verify backend connectivity:

```bash
curl -s http://localhost:8000/ollama/health | python3 -m json.tool
```

Expected healthy response fields:

```json
{
  "ok": true,
  "model": "llama3.2",
  "model_available": true,
  "planner_enabled": true
}
```

Useful backend logs:

```text
[Ollama] Health check success host=http://host.docker.internal:11434 model=llama3.2 model_available=True
[Ollama] Planner enabled host=http://host.docker.internal:11434 model=llama3.2
[Ollama] Success analysis model=llama3.2
[Ollama] Success recommendations model=llama3.2
```

If you see `[Ollama] Connection failed`, confirm Ollama is running on the host and that Docker Compose includes `OLLAMA_HOST=http://host.docker.internal:11434`. If `model_available` is false, run `ollama pull llama3.2` or set `OLLAMA_MODEL` to a model shown by `ollama list`.

---

## Layer 3 Completed: Advanced Agent Orchestration & Extensibility

Layer 3 transforms `PlannerAgent` into a reusable orchestration engine. The Planner **never performs business reasoning directly** — it decides *what* runs, *in which order*, and *why*, based on confidence, interaction type, and domain.

### Architecture

```mermaid
flowchart TB
    subgraph Entry["API Layer (unchanged)"]
        WS["POST /workflow/start"]
        WR["POST /workflow/review"]
        MEM["GET /memory/{id}"]
    end

    PA["PlannerAgent<br/>(routing only)"]
    WO["WorkflowOrchestrator<br/>(state machine)"]

    subgraph Agents["Specialized Agents"]
        MA["MemoryAgent"]
        AA["AnalyzerAgent"]
        RA["RetrieverAgent"]
        REC["RecommenderAgent"]
        EA["ExplainerAgent"]
        DA["StaffingDomainAgent"]
    end

    subgraph Tools["Tool Registry"]
        KS["KnowledgeSearchTool"]
        CRM["CRMTool"]
        MT["MemoryTool"]
        BR["BusinessRuleTool"]
        DE["DraftEmailTool"]
    end

    subgraph Stores["Shared Stores"]
        KB["KnowledgeBase / ChromaDB"]
        DB["SQLite CRM"]
        MS["MemoryStore"]
        RULES["business_rules.yaml"]
    end

    HR["Human Review Gate"]
    LEARN["Memory Learning"]

    WS --> PA
    PA --> WO
    WO --> MA & AA & RA & REC & EA & DA
    RA --> KS & CRM & BR
    MA --> MT
    KS --> KB
    CRM --> DB
    MT --> MS
    BR --> RULES
    REC --> EA
    EA --> HR
    WR --> LEARN
    LEARN --> MS
```

### Workflow state machine

Explicit transitions (no nested function calls):

| State | Description |
|-------|-------------|
| `INGESTED` | Raw payload received |
| `PREPROCESSED` | Format detection + enrichment |
| `ANALYZED` | Business context, risks, opportunities |
| `RETRIEVED` | Knowledge + CRM + rules |
| `RECOMMENDED` | Next Best Actions |
| `EXPLAINED` | Executive narrative |
| `WAITING_REVIEW` | Human gate |
| `APPROVED` → `LEARNING` → `COMPLETED` | Post-review learning loop |

### Dynamic routing

| Route | When | Agents run |
|-------|------|------------|
| **full** | Standard meeting notes / email | memory → analyzer → retriever → recommender → explainer |
| **fast_faq** | Short FAQ-style question | retriever → explainer |
| **deep** | Low confidence (negative sentiment, sparse context) | Full pipeline with extra memory bias |
| **staffing** | `domain: staffing` | memory → staffing_domain → analyzer → retriever → recommender → explainer |

### Agent trace

Every `/workflow/start` response includes `explanation_bundle.agent_trace`:

```json
{
  "agent_trace": [
    {
      "agent_name": "analyzer",
      "execution_order": 2,
      "duration_ms": 12.4,
      "confidence": 0.78,
      "decision": "analyzed",
      "reason": "Detected 5 signals; 3 information gaps",
      "tool_usage": []
    }
  ],
  "orchestration": {
    "route": "full",
    "routing_reason": "Standard enterprise interaction pipeline"
  }
}
```

The frontend visualizes this trace in the **Agent orchestration trace** panel.

### How to add a new agent

1. Create `backend/orchestration/agents/my_agent.py` extending `BaseAgent`
2. Register with one line in `register_default_agents()`:

```python
AgentRegistry.register("my_agent", MyAgent(engine))
```

3. Add the agent name to a workflow in `register_default_workflows()`

### How to register a tool

```python
tool_registry.register(MyTool(dependency))
```

Tools implement `BaseTool`: `execute()`, `metadata()`, `health()`.

### How to add a domain (Staffing example)

Without modifying `PlannerAgent`:

1. Add rules to `backend/config/business_rules.yaml`
2. Add knowledge to `backend/knowledge/*.yaml`
3. Create `backend/orchestration/domains/staffing/agent.py`
4. Register in `register_default_agents()` and `register_default_workflows()`

```bash
curl -s -X POST http://localhost:8000/workflow/start \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-STAFF-01",
    "domain": "staffing",
    "interaction_text": "Urgent RN req — need submittals by Friday. Background check pending."
  }' | python3 -m json.tool
```

### Project structure (Layer 3)

```
backend/
├── ai_platform.py          # Backward-compatible facade + decision engine
├── main.py                 # Unchanged API endpoints
├── orchestration/
│   ├── agents/             # Analyzer, Retriever, Recommender, Explainer, Memory
│   ├── tools/              # KnowledgeSearch, CRM, Memory, BusinessRules, DraftEmail
│   ├── registries/         # AgentRegistry, ToolRegistry, WorkflowRegistry
│   ├── workflow/           # State machine + WorkflowOrchestrator
│   └── domains/staffing/   # Domain extension example
└── tests/test_orchestration.py
```

### Run tests

```bash
cd backend
python -m unittest tests.test_orchestration -v
```

Tests cover: workflow transitions, agent/tool registries, planner orchestration, agent trace, dynamic routing, and staffing domain.

### Backward compatibility

All existing endpoints, response shapes, retrieval, memory, business rules, Ollama integration, and human review remain unchanged. Layer 3 refactors **internally** — clients and the frontend continue to work without modification (with added trace visualization).
