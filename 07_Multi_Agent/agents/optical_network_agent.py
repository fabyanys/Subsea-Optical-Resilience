import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from typing import Dict, Any, List

class OpticalNetworkAgent:
    """Agent 2: Optical Network Technical Agent.
    Specializes in OTN layer, DWDM wavelengths, ITU-T protection switching,
    ROADM reconfiguration, and alternative cable path proposals.
    """

    def __init__(self, rag_engine=None):
        self.rag_engine = rag_engine
        self.agent_name = "Optical Network Agent"
        self.agent_role = "Physical & Optical Layer Engineer (DWDM/ROADM/OTN)"

    def propose_initial_reroute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Detects subsea cut and proposes rerouting via shortest high-capacity terrestrial path.
        NOTE: The Optical agent optimizes purely for bandwidth & latency, proposing
        the Northern Terrestrial Route which crosses a geopolitical conflict territory.
        """
        cables = state.get("cables", {})
        conflict_cable = cables.get("CABLE_TERRESTRIAL_CONFLICT", {})

        return {
            "agent": self.agent_name,
            "role": self.agent_role,
            "action": "PROPOSE_TERRESTRIAL_REROUTE",
            "detected_fault": "CRITICAL Loss of Signal (LOS) on SEA-ME-WE-5 and AAE-1 Subsea links.",
            "proposed_cable_id": "CABLE_TERRESTRIAL_CONFLICT",
            "proposed_cable_name": conflict_cable.get("name", "Northern Terrestrial Route"),
            "proposed_path": ["UAE_DUBAI", "CONFLICT_TRANSIT_NODE", "MARSEILLE_EU"],
            "metrics": {
                "available_capacity_gbps": 150.0,
                "latency_ms": 64.0,
                "osnr_db": 19.5,
                "ber": "3.1e-11"
            },
            "technical_justification": (
                "Northern Terrestrial Corridor provides 150 Gbps immediate bandwidth with lowest optical latency (64ms). "
                "Bypasses physical subsea damage in Red Sea / Gulf of Oman directly to European core nodes."
            ),
            "status": "PROPOSED_AWAITING_POLICY_APPROVAL"
        }

    def execute_roadm_prioritization(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Executes ROADM Dynamic Wavelength Switching and subsea optical prioritization
        upon receiving approved command from human operator and decision coordinator.
        """
        # Reconfigure ROADM lambdas on surviving subsea cable (GCX Falcon & Coastal links)
        allocated_lambdas = [
            {"lambda_id": "λ_1 (1550.12nm)", "service": "CBUAE Banking & RTGS", "protection": "1+1 Dedicated Wavelength", "status": "ACTIVE_LOCKED"},
            {"lambda_id": "λ_2 (1550.92nm)", "service": "SWIFT & Interbank Settlements", "protection": "1+1 Dedicated Wavelength", "status": "ACTIVE_LOCKED"},
            {"lambda_id": "λ_3 (1551.72nm)", "service": "Government Emergency & Cloud Core", "protection": "Shared High-Priority OTN", "status": "ACTIVE_RECONFIGURED"},
            {"lambda_id": "λ_4 (1552.52nm)", "service": "Enterprise Tier-2 Traffic", "protection": "Dynamic Restoration", "status": "ACTIVE_RESTRICTED"}
        ]

        return {
            "agent": self.agent_name,
            "role": self.agent_role,
            "action": "ROADM_WSS_RECONFIGURATION_EXECUTED",
            "standard_applied": "ITU-T G.808.1 (Generic Protection Switching) & ITU-T G.872 (Optical Transport Architecture)",
            "switch_time_ms": 38.5,  # Sub-50ms optical protection
            "target_cable": "CABLE_FALCON (Surviving Subsea Corridor)",
            "roadm_allocated_lambdas": allocated_lambdas,
            "telemetry": {
                "optical_power_dbm": -2.4,
                "ber": "0.8e-12 (Optimal Error-Free)",
                "osnr_margin_db": 6.8
            },
            "execution_status": "SUCCESSFUL: Optical Lambdas successfully preempted and locked for Critical Banking."
        }
