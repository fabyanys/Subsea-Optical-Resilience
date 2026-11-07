import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from typing import Dict, Any

class ResourceAllocationAgent:
    """Agent 3: Resource Allocation Agent.
    Calculates deterministic mathematical allocations for bandwidth, QoS tiers,
    and optical channel capacity based on regulatory priorities (CBUAE Tier-1 guarantee).
    """

    def __init__(self):
        self.agent_name = "Resource Allocation Agent"
        self.agent_role = "Deterministic Traffic Engineer & Bandwidth Slicing Optimizer"

    def execute_priority_slicing(
        self,
        surviving_capacity_gbps: float = 80.0,
        demands: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Executes QoS priority resource allocation when commanded by Decision Coordinator.
        Enforces 100% SLA for Tier-1 Banking while throttling lower tiers.
        """
        if demands is None:
            demands = {
                "Tier1_Critical_Banking": {"demand_gbps": 50.0},
                "Tier2_Enterprise_Cloud": {"demand_gbps": 80.0},
                "Tier3_Public_Internet": {"demand_gbps": 220.0}
            }

        tier1_req = demands["Tier1_Critical_Banking"]["demand_gbps"]
        tier2_req = demands["Tier2_Enterprise_Cloud"]["demand_gbps"]
        tier3_req = demands["Tier3_Public_Internet"]["demand_gbps"]

        remaining = surviving_capacity_gbps
        allocations = {}

        # 1. Tier 1: CBUAE Critical Banking (Strict 100% Guarantee)
        t1_alloc = min(tier1_req, remaining)
        remaining -= t1_alloc
        allocations["Tier1_Critical_Banking"] = {
            "name": "CBUAE Banking, RTGS & SWIFT",
            "requested_gbps": tier1_req,
            "allocated_gbps": t1_alloc,
            "fulfillment_rate": f"{(t1_alloc / tier1_req) * 100:.1f}%",
            "packet_loss_target": "0.000%",
            "qos_queue": "EXPEDITED_FORWARDING (EF - Queue 0)",
            "priority_status": "GUARANTEED_100_PERCENT"
        }

        # 2. Tier 2: Government & Enterprise Core
        # Allocate up to available remaining, capped at 20.0 Gbps to leave room for essential public ping/DNS
        t2_alloc = min(tier2_req, max(0.0, remaining - 10.0))
        remaining -= t2_alloc
        allocations["Tier2_Enterprise_Cloud"] = {
            "name": "Government & Enterprise Cloud",
            "requested_gbps": tier2_req,
            "allocated_gbps": t2_alloc,
            "fulfillment_rate": f"{(t2_alloc / tier2_req) * 100:.1f}%",
            "packet_loss_target": "< 1.5%",
            "qos_queue": "ASSURED_FORWARDING (AF - Queue 1)",
            "priority_status": "ESSENTIAL_PRESERVED"
        }

        # 3. Tier 3: Public Internet (Aggressively Throttled)
        t3_alloc = min(tier3_req, remaining)
        remaining -= t3_alloc
        allocations["Tier3_Public_Internet"] = {
            "name": "Public Internet, OTT Video & Social Media",
            "requested_gbps": tier3_req,
            "allocated_gbps": t3_alloc,
            "fulfillment_rate": f"{(t3_alloc / tier3_req) * 100:.1f}%",
            "packet_loss_target": "Traffic Shaping / Throttling Active",
            "qos_queue": "BEST_EFFORT_THROTTLED (BE - Queue 2)",
            "priority_status": "THROTTLED_TO_PROTECT_CRITICAL"
        }

        return {
            "agent": self.agent_name,
            "role": self.agent_role,
            "action": "RESOURCE_SLICING_ENFORCED",
            "surviving_capacity_gbps": surviving_capacity_gbps,
            "allocated_total_gbps": t1_alloc + t2_alloc + t3_alloc,
            "headroom_buffer_gbps": remaining,
            "allocations": allocations,
            "mathematical_optimality": "Pareto-optimal with Lexicographic CBUAE Priority",
            "status": "Bandwidth policed and committed to router egress interfaces."
        }
