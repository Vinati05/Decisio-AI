from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

try:
    from backend.ai_platform import MemoryStore, MockKnowledge, PlannerAgent
except ModuleNotFoundError:  # pragma: no cover - container fallback
    from ai_platform import MemoryStore, MockKnowledge, PlannerAgent

app = FastAPI(
    title="Nexora Studio",
    description="Agentic Decision Intelligence platform demo with planner orchestration, evidence, human-in-the-loop, and memory.",
)

memory_store = MemoryStore()
knowledge = MockKnowledge()
planner = PlannerAgent(knowledge=knowledge, memory=memory_store)


@app.get("/")
def root():
    return {
        "name": "Nexora Studio",
        "status": "running",
        "experience": "agentic decision intelligence",
    }


def _to_jsonable(obj: Any) -> Any:
    # Dataclasses have __dict__ but nested dataclasses/lists need recursion.
    if hasattr(obj, "__dict__") and not isinstance(obj, (str, int, float, bool, dict, list)):
        return _to_jsonable(obj.__dict__)
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(v) for v in obj]
    return obj


@app.post("/workflow/start")
def workflow_start(payload: Dict[str, Any]) -> JSONResponse:
    """Ingest an interaction + gather org context + produce next-best actions.

    Human review gate: returned actions are *proposed* and not executed.
    """
    required = ["customer_id", "interaction_text"]
    missing_fields = [f for f in required if f not in payload]
    if missing_fields:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing required fields", "missing": missing_fields},
        )

    result = planner.run_workflow(payload)
    return JSONResponse(content=_to_jsonable(result))


@app.post("/workflow/review")
def workflow_review(payload: Dict[str, Any]) -> JSONResponse:
    """Human-in-the-loop decision."""
    required = ["review_id", "status"]
    missing_fields = [f for f in required if f not in payload]
    if missing_fields:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing required fields", "missing": missing_fields},
        )

    review_id = str(payload["review_id"])
    status = str(payload["status"]).lower()
    if status not in ("approved", "rejected"):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid status", "allowed": ["approved", "rejected"]},
        )

    reviewer_notes = payload.get("reviewer_notes")

    memory_store.update_review(
        review_id=review_id,
        status=status,
        reviewer_notes=reviewer_notes,
    )

    # Learn from outcome (bias future recommendations).
    # We need customer_id/domain/run_id; easiest: scan stored runs.
    learned = False
    for run in memory_store._runs.values():  # type: ignore[attr-defined]
        hr = run.human_review
        if hr.review_id == review_id:
            memory_store.learn_from_outcome(
                customer_id=run.customer_id,
                domain=run.domain,
                run_id=run.run_id,
                review_status=status,
                reviewer_notes=reviewer_notes,
            )
            learned = True
            break

    return JSONResponse(
        content={
            "review_id": review_id,
            "status": status,
            "learned_from_outcome": learned,
            "reviewed_at": datetime.utcnow().isoformat() + "Z",
        }
    )


@app.get("/memory/{customer_id}")
def get_memory(customer_id: str) -> JSONResponse:
    return JSONResponse(content=memory_store.get_memory(customer_id))


# Back-compat demo endpoint (frontend currently calls this).
@app.get("/planner/run")
def planner_run() -> Dict[str, Any]:
    # Provide deterministic mock payload so the old UI still shows something.
    payload = {
        "customer_id": "CUST-1001",
        "domain": "saas_sales",
        "source_type": "meeting_notes",
        "interaction_text": "We have a problem with slow reporting and unclear champion. The customer is asking for faster updates.",
    }
    result = planner.run_workflow(payload)
    data = _to_jsonable(result)

    # Convert into legacy UI schema (recommendation/headline/reason/timeline/pillars).
    # Keep it human-ish rather than raw agent output.
    nba0 = data["next_best_actions"][0]
    analysis = data["analysis"]
    headline = nba0.get("title")
    reason = nba0.get("summary")
    timeline = [
        analysis["opportunities"][0] if analysis.get("opportunities") else "Start with discovery.",
        nba0.get("evidence", [{}])[0].get("excerpt", "Use enterprise evidence to ground decisions."),
        nba0.get("recommended_next_questions", ["Confirm constraints and stakeholders."])[0],
    ]
    pillars = [
        {"title": "Opportunity", "copy": (analysis.get("opportunities") or [""])[0]},
        {"title": "Risk", "copy": (analysis.get("risks") or [""])[0]},
        {"title": "Next", "copy": nba0.get("recommended_next_questions", [""])[0]},
    ]

    return {
        "recommendation": headline,
        "confidence": float(nba0.get("confidence", 0.8)),
        "reason": reason,
        "moment": "Proposed next step (provisional until approved).",
        "next_step": nba0.get("title"),
        "spark": data["explanation_bundle"]["natural_language_summary"],
        "headline": headline,
        "description": nba0.get("summary"),
        "focus": "Evidence-backed next best action",
        "timeline": timeline,
        "pillars": pillars,
        "mood": "Human-first planning",
        "accent": "Evidence & review",
        "signal": "next-best-action",
        "signal_label": "Needs review",
    }


