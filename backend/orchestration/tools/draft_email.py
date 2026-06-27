from __future__ import annotations

from typing import Any, Dict, List

from orchestration.tools.base import BaseTool, ToolMetadata


class DraftEmailTool(BaseTool):
    name = "draft_email"

    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.name,
            description="Prepare draft email payload for approved next-best actions",
            tags=["execution", "draft"],
        )

    def execute(
        self,
        action_titles: List[str],
        customer_id: str,
        domain: str,
        **_: Any,
    ) -> Dict[str, Any]:
        return {
            "type": "draft_email",
            "customer_id": customer_id,
            "domain": domain,
            "subjects": [f"Follow-up: {t}" for t in action_titles[:3]],
            "status": "draft_only",
            "human_gate": True,
        }

    def health(self) -> Dict[str, Any]:
        return {"ok": True, "tool": self.name}
