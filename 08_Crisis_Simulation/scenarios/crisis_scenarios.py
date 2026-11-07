"""Crisis Scenarios Definition and State Machine for Submarine Optical Incidents.
Includes the geopolitical conflict transit scenario and multi-agent workflow.
"""

from typing import Dict, Any, List

class IncidentScenario:
    ID = "GEOPOLITICAL_SUBSEA_CUT_01"
    NAME = "Dual Submarine Cable Cut in Gulf of Oman / Red Sea Corridor"
    DESCRIPTION = (
        "Seismic event and physical anchor drag severed SEA-ME-WE-5 and AAE-1 submarine cables. "
        "Surviving subsea bandwidth reduced significantly. Optical Network Agent seeks alternate routes."
    )

    AFFECTED_CABLES = ["CABLE_SMW5", "CABLE_AAE1"]
    
    # Conflict Territory Metadata
    CONFLICT_COUNTRY_NAME = "Hostile Geopolitical Adversary State"
    CONFLICT_RISK_DESCRIPTION = (
        "Traversing unvetted hostile terrestrial fiber creates severe vulnerabilities: "
        "state-sponsored traffic interception, BGP hijacking, wiretapping, and direct disruption."
    )
    
    # Regulatory Violations Triggered
    REGULATORY_VIOLATIONS = [
        {
            "regulation": "UAE TDRA Critical National Telecom Continuity Directive",
            "clause": "Article 14.3 (Prohibition of Hostile / Non-Allied Transit Routing)",
            "severity": "CRITICAL",
            "details": "Telecommunications carriers shall not route sovereign, governmental, or critical civilian data through adversarial jurisdictions lacking reciprocal security treaties."
        },
        {
            "regulation": "CBUAE Banking & Payment Systems CIIP Regulation (Version 1.0)",
            "clause": "Section 4.2.1 (Data Sovereignty & Financial In-Transit Encryption/Jurisdiction)",
            "severity": "FATAL_BLOCK",
            "details": "All UAE financial transactions, RTGS packets, and banking clearing feeds must strictly traverse secure, approved sovereign or allied corridors. Hostile corridor transit is strictly prohibited under federal penalty."
        }
    ]

    # Compliant Alternative Solution
    COMPLIANT_MITIGATION = {
        "solution_type": "Surviving Subsea Optical Corridor + ROADM Priority + QoS Resource Slicing",
        "optical_layer": (
            "Keep traffic on surviving subsea infrastructure (GCX Falcon Subsea Loop & Surviving Coastal Optical Segments). "
            "Reconfigure ROADM (Reconfigurable Optical Add-Drop Multiplexer) Wavelength Selective Switches (WSS) "
            "to pre-empt optical wavelengths (λ_1, λ_2, λ_3) dedicated exclusively to Tier-1 critical traffic with zero packet jitter."
        ),
        "resource_allocation_layer": (
            "Prioritize Tier-1 CBUAE Banking/SWIFT/RTGS at 100% bandwidth reservation (50 Gbps guaranteed). "
            "Allocate 20 Gbps to Tier-2 Government/Cloud. "
            "Aggressively throttle Tier-3 Public Internet (OTT streaming/social media) to prevent optical buffer overflow."
        ),
        "regulatory_status": "100% Compliant with TDRA and CBUAE CIIP Frameworks",
        "geopolitical_risk": "ZERO - Completely avoids hostile transit zones"
    }

def apply_disruption(state: Dict[str, Any]) -> Dict[str, Any]:
    """Applies the physical submarine cable disruption to the network state."""
    cables = state["cables"]
    
    # Cut SEA-ME-WE-5
    cables["CABLE_SMW5"]["status"] = "SEVERELY_CUT"
    cables["CABLE_SMW5"]["allocated_gbps"] = 0.0
    cables["CABLE_SMW5"]["latency_ms"] = 999.0
    cables["CABLE_SMW5"]["osnr_db"] = 0.0
    cables["CABLE_SMW5"]["ber"] = "1.0 (Link Down)"
    cables["CABLE_SMW5"]["color"] = "#ef4444"

    # Degrade AAE-1
    cables["CABLE_AAE1"]["status"] = "SEVERELY_CUT"
    cables["CABLE_AAE1"]["allocated_gbps"] = 0.0
    cables["CABLE_AAE1"]["latency_ms"] = 999.0
    cables["CABLE_AAE1"]["osnr_db"] = 0.0
    cables["CABLE_AAE1"]["ber"] = "1.0 (Link Down)"
    cables["CABLE_AAE1"]["color"] = "#ef4444"

    return state
