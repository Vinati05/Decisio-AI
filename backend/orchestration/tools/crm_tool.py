from __future__ import annotations

from typing import Any, Dict, List

from orchestration.tools.base import BaseTool, ToolMetadata


class CRMTool(BaseTool):
    name = "crm_lookup"

    def __init__(self, crm_simulator: Any) -> None:
        self.crm = crm_simulator

    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.name,
            description="Query SQLite CRM simulator for customer history",
            tags=["retrieval", "crm"],
        )

    def execute(self, customer_id: str, domain: str, **_: Any) -> List[Dict[str, Any]]:
        return self.crm.query_by_customer_id(customer_id, domain)

    def health(self) -> Dict[str, Any]:
        return {"ok": self.crm.conn is not None, "tool": self.name}
