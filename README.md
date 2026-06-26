
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
