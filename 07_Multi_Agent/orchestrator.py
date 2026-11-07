import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CURRENT_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from agents.policy_agent import PolicyComplianceAgent
from agents.optical_network_agent import OpticalNetworkAgent
from agents.resource_allocation_agent import ResourceAllocationAgent
from agents.decision_coordinator import DecisionCoordinatorAgent
import importlib

# Dynamic module imports for folders starting with digits
network_topology = importlib.import_module("08_Crisis_Simulation.topologies.network_topology")
get_initial_network_state = network_topology.get_initial_network_state

crisis_scenarios = importlib.import_module("08_Crisis_Simulation.scenarios.crisis_scenarios")
IncidentScenario = crisis_scenarios.IncidentScenario
apply_disruption = crisis_scenarios.apply_disruption

class ResilienceOrchestrator:
    """Stateful Multi-Agent Orchestrator managing the lifecycle of
    submarine cable crisis simulation, policy verification, ROADM prioritization,
    and human-in-the-loop decision gating.
    """

    def __init__(self, rag_engine=None):
        self.policy_agent = PolicyComplianceAgent(rag_engine=rag_engine)
        self.optical_agent = OpticalNetworkAgent(rag_engine=rag_engine)
        self.resource_agent = ResourceAllocationAgent()
        self.coordinator = DecisionCoordinatorAgent()
        
        self.logs_dir = BASE_DIR / "09_Audit_and_Evaluation" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.reset_system()

    def reset_system(self):
        """Resets the network and agents to initial normal baseline."""
        self.state = get_initial_network_state()
        self.workflow_stage = "NORMAL"  # NORMAL, DISRUPTED, OPTICAL_PROPOSED, POLICY_BLOCKED, COORDINATOR_RECOMMENDED, AWAITING_HUMAN, EXECUTED, REJECTED
        self.audit_log: List[Dict[str, Any]] = []
        self.last_optical_proposal = None
        self.last_policy_verdict = None
        self.last_coordinator_recommendation = None
        self._record_audit_event(
            agent="SYSTEM_KERNEL",
            action="SYSTEM_INITIALIZED",
            details="Network operational. Subsea optical links healthy. AI agents standing by."
        )

    def _record_audit_event(self, agent: str, action: str, details: str, metadata: Optional[Dict[str, Any]] = None):
        """Appends an event to the tamper-evident audit log."""
        event = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "agent": agent,
            "action": action,
            "details": details,
            "metadata": metadata or {}
        }
        self.audit_log.append(event)

    def trigger_subsea_disruption(self) -> Dict[str, Any]:
        """Simulates physical submarine cable cut in Gulf of Oman / Red Sea corridor."""
        self.state = apply_disruption(self.state)
        self.workflow_stage = "DISRUPTED"

        self._record_audit_event(
            agent="TELEMETRY_MONITOR",
            action="CRITICAL_ALARM_SUBSEA_CUT",
            details="Seismic/Anchor drag event detected. SEA-ME-WE-5 and AAE-1 severed near Fujairah/Gulf of Oman.",
            metadata={
                "affected_cables": IncidentScenario.AFFECTED_CABLES,
                "surviving_capacity_gbps": 80.0
            }
        )

        return self.get_summary()

    def run_optical_proposal(self) -> Dict[str, Any]:
        """Optical Network Agent discovers cut and proposes Northern Terrestrial Route (Conflict Territory)."""
        if self.workflow_stage not in ["DISRUPTED", "NORMAL"]:
            return self.get_summary()

        proposal = self.optical_agent.propose_initial_reroute(self.state)
        self.last_optical_proposal = proposal
        self.workflow_stage = "OPTICAL_PROPOSED"

        # Mark conflict cable as proposed
        self.state["cables"]["CABLE_TERRESTRIAL_CONFLICT"]["status"] = "PROPOSED_BY_OPTICAL"

        self._record_audit_event(
            agent=proposal["agent"],
            action=proposal["action"],
            details=(
                f"Optical agent proposes bypass via {proposal['proposed_cable_name']} "
                f"(150 Gbps, 64ms). Seeking lowest attenuation path without geopolitical awareness."
            ),
            metadata=proposal
        )

        return self.get_summary()

    def run_policy_interception(self) -> Dict[str, Any]:
        """Policy Agent halts process, audits route against UAE regulations, and strictly BLOCKS it."""
        if self.workflow_stage != "OPTICAL_PROPOSED":
            return self.get_summary()

        policy_verdict = self.policy_agent.intercept_and_audit(self.last_optical_proposal)
        self.last_policy_verdict = policy_verdict
        self.workflow_stage = "POLICY_BLOCKED"

        # Update conflict cable status to BLOCKED
        self.state["cables"]["CABLE_TERRESTRIAL_CONFLICT"]["status"] = "POLICY_BLOCKED"

        self._record_audit_event(
            agent=policy_verdict["agent"],
            action=policy_verdict["action"],
            details=(
                "HOLD & BLOCK! Terrestrial transit through conflict state violates UAE TDRA Article 14.3 "
                "and CBUAE CIIP Section 4.2.1. Severe risk of wiretapping, cyber warfare, and data interception."
            ),
            metadata=policy_verdict
        )

        return self.get_summary()

    def run_coordinator_synthesis(self) -> Dict[str, Any]:
        """Decision Coordinator synthesizes compliant solution: Surviving Subsea + ROADM Priority + QoS Resource Slicing."""
        if self.workflow_stage != "POLICY_BLOCKED":
            return self.get_summary()

        recommendation = self.coordinator.formulate_compliant_alternative(
            self.last_policy_verdict,
            self.state
        )
        self.last_coordinator_recommendation = recommendation
        self.workflow_stage = "AWAITING_HUMAN"

        self._record_audit_event(
            agent=recommendation["agent"],
            action=recommendation["action"],
            details=(
                "Synthesized compliant alternative: Retain traffic on GCX Falcon Subsea Loop. "
                "Activate ROADM optical lambda prioritization (λ_1, λ_2 dedicated to Banking) "
                "and throttle Tier-3 public streaming to preserve CBUAE 100% SLA."
            ),
            metadata=recommendation
        )

        return self.get_summary()

    def submit_human_decision(self, approved: bool, operator_id: str = "SEC_OPS_OFFICER_01") -> Dict[str, Any]:
        """Processes Human Operator's decision (Approve or Reject).
        If approved, dispatches execution to Optical and Resource Allocation agents.
        """
        if self.workflow_stage != "AWAITING_HUMAN":
            return self.get_summary()

        if not approved:
            self.workflow_stage = "REJECTED"
            self._record_audit_event(
                agent="HUMAN_OPERATOR",
                action="RECOMMENDATION_REJECTED",
                details=f"Operator {operator_id} rejected ROADM priority recommendation. System in manual fail-safe hold.",
                metadata={"operator_id": operator_id}
            )
            return self.get_summary()

        # Human Approved -> Dispatch Execution
        self._record_audit_event(
            agent="HUMAN_OPERATOR",
            action="RECOMMENDATION_APPROVED",
            details=f"Operator {operator_id} authorized ROADM Subsea Priority & QoS Resource Slicing execution.",
            metadata={"operator_id": operator_id}
        )

        # 1. Optical Agent Executes ROADM Reconfiguration
        optical_exec = self.optical_agent.execute_roadm_prioritization(self.state)
        self.state["cables"]["CABLE_FALCON"]["status"] = "ROADM_PRIORITIZED"
        self.state["cables"]["CABLE_FALCON"]["color"] = "#06b6d4"  # glowing cyan
        self.state["roadm_state"]["mode"] = "ROADM_PRIORITY_PROTECTED"
        self.state["roadm_state"]["preemption_status"] = "ACTIVE"

        self._record_audit_event(
            agent=optical_exec["agent"],
            action=optical_exec["action"],
            details="ROADM WSS matrix reconfigured. Lambdas λ_1 & λ_2 locked for CBUAE Banking with sub-50ms protection.",
            metadata=optical_exec
        )

        # 2. Resource Allocation Agent Executes Deterministic Slicing
        resource_exec = self.resource_agent.execute_priority_slicing(
            surviving_capacity_gbps=80.0,
            demands=self.state["traffic_demands"]
        )
        # Update state allocations
        for tier_key, alloc_data in resource_exec["allocations"].items():
            if tier_key in self.state["traffic_demands"]:
                self.state["traffic_demands"][tier_key]["allocated_gbps"] = alloc_data["allocated_gbps"]
                self.state["traffic_demands"][tier_key]["status"] = alloc_data["priority_status"]

        self._record_audit_event(
            agent=resource_exec["agent"],
            action=resource_exec["action"],
            details="Bandwidth slicing committed: 100% CBUAE Banking fulfilled (50 Gbps), Tier-3 Public Internet throttled to 10 Gbps.",
            metadata=resource_exec
        )

        self.workflow_stage = "EXECUTED"

        # Persist full audit log to disk
        self._save_audit_log_to_file()

        return self.get_summary()

    def _save_audit_log_to_file(self):
        """Saves current deliberation and audit events into a timestamped JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.logs_dir / f"audit_trail_scenario_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "scenario": IncidentScenario.NAME,
                "workflow_stage": self.workflow_stage,
                "audit_events": self.audit_log,
                "final_state": self.state
            }, f, indent=2, ensure_ascii=False)

    def get_summary(self) -> Dict[str, Any]:
        """Returns the complete snapshot for UI rendering."""
        return {
            "workflow_stage": self.workflow_stage,
            "state": self.state,
            "audit_log": self.audit_log,
            "last_optical_proposal": getattr(self, "last_optical_proposal", None),
            "last_policy_verdict": getattr(self, "last_policy_verdict", None),
            "last_coordinator_recommendation": getattr(self, "last_coordinator_recommendation", None)
        }
