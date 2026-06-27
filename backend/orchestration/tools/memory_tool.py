from __future__ import annotations

from typing import Any, Dict, List, Tuple

from orchestration.tools.base import BaseTool, ToolMetadata


class MemoryTool(BaseTool):
    name = "memory"

    def __init__(self, memory_store: Any) -> None:
        self.memory = memory_store

    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.name,
            description="Read/write shared memory — lessons, approvals, KPI trends",
            tags=["memory", "learning"],
        )

    def execute(self, operation: str = "get", **kwargs: Any) -> Any:
        if operation == "get":
            return self.memory.get_memory(kwargs["customer_id"])
        if operation == "lessons":
            return self.memory.get_lessons_for_customer(kwargs["customer_id"], kwargs["domain"])
        if operation == "put_interaction":
            self.memory.put_interaction(kwargs["interaction"])
            return {"stored": True}
        if operation == "put_run":
            self.memory.put_run(kwargs["result"])
            return {"stored": True}
        raise ValueError(f"Unknown memory operation: {operation}")

    def health(self) -> Dict[str, Any]:
        return {"ok": hasattr(self.memory, "get_memory"), "tool": self.name}
