from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from orchestration.agents.base import BaseAgent

if TYPE_CHECKING:
    from orchestration.registries.tools import ToolRegistry


class AgentRegistry:
    """Dynamic agent resolution — adding a domain agent is one registration line."""

    _agents: Dict[str, BaseAgent] = {}
    _factories: Dict[str, Callable[[], BaseAgent]] = {}

    @classmethod
    def register(cls, name: str, agent: BaseAgent) -> None:
        cls._agents[name] = agent

    @classmethod
    def register_factory(cls, name: str, factory: Callable[[], BaseAgent]) -> None:
        cls._factories[name] = factory

    @classmethod
    def get(cls, name: str) -> Optional[BaseAgent]:
        if name in cls._agents:
            return cls._agents[name]
        if name in cls._factories:
            agent = cls._factories[name]()
            cls._agents[name] = agent
            return agent
        return None

    @classmethod
    def list_agents(cls) -> List[str]:
        return sorted(set(cls._agents.keys()) | set(cls._factories.keys()))

    @classmethod
    def clear(cls) -> None:
        cls._agents.clear()
        cls._factories.clear()


def register_default_agents(engine: Any, tool_registry: "ToolRegistry") -> None:
    from orchestration.agents.analyzer import AnalyzerAgent
    from orchestration.agents.explainer import ExplainerAgent
    from orchestration.agents.memory_agent import MemoryAgent
    from orchestration.agents.recommender import RecommenderAgent
    from orchestration.agents.retriever import RetrieverAgent

    AgentRegistry.register("analyzer", AnalyzerAgent(engine))
    AgentRegistry.register("retriever", RetrieverAgent(engine, tool_registry))
    AgentRegistry.register("recommender", RecommenderAgent(engine))
    AgentRegistry.register("explainer", ExplainerAgent(engine))
    AgentRegistry.register("memory", MemoryAgent(engine, tool_registry))

    # Domain extension point — staffing agent registered without modifying Planner
    try:
        from orchestration.domains.staffing.agent import StaffingDomainAgent

        AgentRegistry.register("staffing_domain", StaffingDomainAgent(engine))
    except ImportError:
        pass
