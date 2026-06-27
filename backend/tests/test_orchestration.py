from __future__ import annotations

import os
import sys
import unittest

# Ensure backend is on path when running tests from repo root or backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_platform import MemoryStore, MockKnowledge, PlannerAgent
from orchestration.registries.agents import AgentRegistry
from orchestration.registries.tools import ToolRegistry, register_default_tools
from orchestration.registries.workflows import WorkflowRegistry, register_default_workflows
from orchestration.workflow.states import WorkflowState, validate_transition


class TestWorkflowTransitions(unittest.TestCase):
    def test_valid_transitions(self):
        self.assertTrue(validate_transition(WorkflowState.INGESTED, WorkflowState.PREPROCESSED))
        self.assertTrue(validate_transition(WorkflowState.PREPROCESSED, WorkflowState.ANALYZED))
        self.assertTrue(validate_transition(WorkflowState.EXPLAINED, WorkflowState.WAITING_REVIEW))

    def test_invalid_transition(self):
        self.assertFalse(validate_transition(WorkflowState.INGESTED, WorkflowState.COMPLETED))


class TestRegistries(unittest.TestCase):
    def setUp(self):
        AgentRegistry.clear()
        WorkflowRegistry.clear()

    def test_tool_registry_register_and_execute(self):
        memory = MemoryStore()
        kb = MockKnowledge()
        from ai_platform import SQLiteCRMSimulator

        crm = SQLiteCRMSimulator(":memory:")
        tools = register_default_tools(kb, crm, memory, {"saas_sales": {}})
        self.assertIn("knowledge_search", tools.list_tools())
        self.assertIn("crm_lookup", tools.list_tools())
        data, _, err = tools.execute("business_rules", domain="saas_sales")
        self.assertIsNone(err)
        self.assertIsInstance(data, dict)

    def test_workflow_registry(self):
        register_default_workflows()
        names = WorkflowRegistry.list_workflows()
        self.assertIn("full_decision", names)
        self.assertIn("fast_faq", names)


class TestPlannerOrchestration(unittest.TestCase):
    def setUp(self):
        self.memory = MemoryStore()
        self.planner = PlannerAgent(knowledge=MockKnowledge(), memory=self.memory)

    def test_full_workflow_start(self):
        payload = {
            "customer_id": "CUST-1001",
            "domain": "saas_sales",
            "interaction_text": (
                "VP Ops wants faster reporting. No champion yet. Competitor mentioned. IT asked about SSO."
            ),
        }
        result = self.planner.run_workflow(payload)
        self.assertTrue(result.next_best_actions)
        self.assertIn("agent_trace", result.explanation_bundle)
        trace = result.explanation_bundle["agent_trace"]
        self.assertGreaterEqual(len(trace), 3)
        agent_names = [t["agent_name"] for t in trace]
        self.assertIn("analyzer", agent_names)
        self.assertIn("retriever", agent_names)
        self.assertIn("recommender", agent_names)

    def test_agent_trace_fields(self):
        payload = {
            "customer_id": "CUST-1001",
            "domain": "saas_sales",
            "interaction_text": "Discovery call about reporting pain and MAP timeline.",
        }
        result = self.planner.run_workflow(payload)
        trace = result.explanation_bundle["agent_trace"]
        for entry in trace:
            self.assertIn("agent_name", entry)
            self.assertIn("execution_order", entry)
            self.assertIn("duration_ms", entry)
            self.assertIn("decision", entry)
            self.assertIn("reason", entry)

    def test_fast_faq_routing(self):
        payload = {
            "customer_id": "CUST-1001",
            "domain": "saas_sales",
            "interaction_text": "What is our SSO policy?",
        }
        result = self.planner.run_workflow(payload)
        orch = result.explanation_bundle.get("orchestration", {})
        self.assertEqual(orch.get("route"), "fast_faq")
        agent_names = [t["agent_name"] for t in result.explanation_bundle["agent_trace"]]
        self.assertNotIn("recommender", agent_names)

    def test_staffing_domain(self):
        payload = {
            "customer_id": "CUST-STAFF-01",
            "domain": "staffing",
            "interaction_text": "Urgent open req for RN — need submittals by Friday. Background check pending.",
        }
        result = self.planner.run_workflow(payload)
        agent_names = [t["agent_name"] for t in result.explanation_bundle["agent_trace"]]
        self.assertIn("staffing_domain", agent_names)
        self.assertTrue(result.next_best_actions)


if __name__ == "__main__":
    unittest.main()
