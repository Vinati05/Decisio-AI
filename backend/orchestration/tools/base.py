from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("decisio.tools")


@dataclass
class ToolMetadata:
    name: str
    description: str
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)


class BaseTool(ABC):
    """Reusable capability — Planner never imports tools directly."""

    name: str = "base_tool"

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        ...

    @abstractmethod
    def metadata(self) -> ToolMetadata:
        ...

    def health(self) -> Dict[str, Any]:
        return {"ok": True, "tool": self.name}

    def run_safe(self, **kwargs: Any) -> tuple[Any, float, Optional[str]]:
        start = time.perf_counter()
        try:
            result = self.execute(**kwargs)
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "[Tool] %s finished duration_ms=%.1f decision=success",
                self.name,
                duration_ms,
            )
            return result, duration_ms, None
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.warning(
                "[Tool] %s failed duration_ms=%.1f error=%s",
                self.name,
                duration_ms,
                exc,
            )
            return None, duration_ms, str(exc)
