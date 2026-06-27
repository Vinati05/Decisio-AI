from __future__ import annotations

from typing import Any, Dict

from orchestration.tools.base import BaseTool, ToolMetadata


class BusinessRuleTool(BaseTool):
    name = "business_rules"

    def __init__(self, rules: Dict[str, Any]) -> None:
        self.rules = rules

    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.name,
            description="Load domain-specific business rules and confidence thresholds",
            tags=["rules", "config"],
        )

    def execute(self, domain: str, **_: Any) -> Dict[str, Any]:
        return self.rules.get(domain, {})

    def health(self) -> Dict[str, Any]:
        return {"ok": bool(self.rules), "tool": self.name, "domains": list(self.rules.keys())}
