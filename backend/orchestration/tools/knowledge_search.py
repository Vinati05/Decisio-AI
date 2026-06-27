from __future__ import annotations

from typing import Any, Dict, List, Tuple

from orchestration.tools.base import BaseTool, ToolMetadata


class KnowledgeSearchTool(BaseTool):
    name = "knowledge_search"

    def __init__(self, knowledge_base: Any) -> None:
        self.kb = knowledge_base

    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.name,
            description="Semantic search over articles, playbooks, and product docs",
            tags=["retrieval", "knowledge"],
        )

    def execute(
        self,
        query: str,
        domain: str,
        top_k: int = 6,
        **_: Any,
    ) -> List[Tuple[Dict[str, Any], float]]:
        return self.kb.semantic_search(query, domain, top_k=top_k)

    def health(self) -> Dict[str, Any]:
        ok = hasattr(self.kb, "semantic_search")
        return {"ok": ok, "tool": self.name, "engine": "chroma" if getattr(self.kb, "use_chroma", False) else "tfidf"}
