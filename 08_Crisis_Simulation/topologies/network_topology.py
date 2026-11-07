"""Network Topology Model for UAE Submarine & Terrestrial Optical Infrastructure.
Includes landing stations, submarine cable corridors, terrestrial backhauls,
ROADM nodes, and conflict-zone transit paths.
"""

from typing import Dict, List, Any

# Geolocation coordinates for optical nodes
NODES: Dict[str, Dict[str, Any]] = {
    "UAE_FUJAIRAH": {
        "name": "Fujairah Landing Station (CLS)",
        "lat": 25.1288,
        "lon": 56.3265,
        "country": "UAE",
        "type": "Primary Subsea Hub / CLS",
        "roadm_equipped": True,
        "role": "Critical Submarine Landing Gateway"
    },
    "UAE_DUBAI": {
        "name": "Dubai Datacenter Core (DXB)",
        "lat": 25.2048,
        "lon": 55.2708,
        "country": "UAE",
        "type": "Core Datacenter / CLS",
        "roadm_equipped": True,
        "role": "Financial & Cloud Core"
    },
    "UAE_ABU_DHABI": {
        "name": "Abu Dhabi Government & Banking Core (AUH)",
        "lat": 24.4539,
        "lon": 54.3773,
        "country": "UAE",
        "type": "CBUAE / Sovereign Core",
        "roadm_equipped": True,
        "role": "Central Bank RTGS / Government Operations"
    },
    "OMAN_MUSCAT": {
        "name": "Muscat Cable Landing Station",
        "lat": 23.5880,
        "lon": 58.3829,
        "country": "Oman",
        "type": "Subsea Transit CLS",
        "roadm_equipped": True,
        "role": "Regional Submarine Optical Hub"
    },
    "DJIBOUTI_HUB": {
        "name": "Djibouti Subsea Teleport",
        "lat": 11.5721,
        "lon": 43.1456,
        "country": "Djibouti",
        "type": "Red Sea Gateway",
        "roadm_equipped": True,
        "role": "Red Sea Optical Interconnect"
    },
    "EGYPT_SUEZ": {
        "name": "Suez / Zafarana Optical Corridor",
        "lat": 29.9668,
        "lon": 32.5498,
        "country": "Egypt",
        "type": "Transit Hub",
        "roadm_equipped": True,
        "role": "Suez Mediterranean Cross-over"
    },
    "MARSEILLE_EU": {
        "name": "Marseille European Core (MRS)",
        "lat": 43.2965,
        "lon": 5.3698,
        "country": "France",
        "type": "European Continental Gateway",
        "roadm_equipped": True,
        "role": "EU Interconnection Hub"
    },
    "MUMBAI_IND": {
        "name": "Mumbai Gateway (BOM)",
        "lat": 18.9220,
        "lon": 72.8347,
        "country": "India",
        "type": "Asian Gateway CLS",
        "roadm_equipped": True,
        "role": "Asia-Pacific Subsea Interconnect"
    },
    "GCC_SAUDI_RIYADH": {
        "name": "Riyadh GCC Terrestrial Node",
        "lat": 24.7136,
        "lon": 46.6753,
        "country": "Saudi Arabia",
        "type": "Terrestrial GCC Transit",
        "roadm_equipped": True,
        "role": "Southern GCC Terrestrial Backup"
    },
    "CONFLICT_TRANSIT_NODE": {
        "name": "Northern Hostile / Conflict Zone Corridor",
        "lat": 33.3152,
        "lon": 44.3661,
        "country": "Geopolitical Conflict State",
        "type": "Unvetted Terrestrial Corridor",
        "roadm_equipped": False,
        "role": "SANCTIONED / HIGH-RISK HOSTILE TRANSIT"
    }
}

# Cable Links Configuration
DEFAULT_CABLES: Dict[str, Dict[str, Any]] = {
    "CABLE_SMW5": {
        "id": "CABLE_SMW5",
        "name": "SEA-ME-WE-5 (Subsea Optical)",
        "type": "Submarine",
        "path_nodes": ["UAE_FUJAIRAH", "OMAN_MUSCAT", "DJIBOUTI_HUB", "EGYPT_SUEZ", "MARSEILLE_EU"],
        "total_capacity_gbps": 200.0,
        "allocated_gbps": 180.0,
        "latency_ms": 78.5,
        "osnr_db": 22.4,
        "ber": "1.2e-12",
        "status": "OPERATIONAL",  # OPERATIONAL, SEVERELY_CUT, DEGRADED, ROADM_RESTORED
        "roadm_supported": True,
        "geopolitical_risk": "None (International Waters & Safe CLS)",
        "is_subsea": True,
        "color": "#00d2ff"
    },
    "CABLE_AAE1": {
        "id": "CABLE_AAE1",
        "name": "AAE-1 (Asia-Africa-Europe 1 Subsea)",
        "type": "Submarine",
        "path_nodes": ["UAE_FUJAIRAH", "MUMBAI_IND", "DJIBOUTI_HUB", "EGYPT_SUEZ", "MARSEILLE_EU"],
        "total_capacity_gbps": 180.0,
        "allocated_gbps": 160.0,
        "latency_ms": 82.0,
        "osnr_db": 21.8,
        "ber": "1.5e-12",
        "status": "OPERATIONAL",
        "roadm_supported": True,
        "geopolitical_risk": "None (International Waters)",
        "is_subsea": True,
        "color": "#00b4d8"
    },
    "CABLE_FALCON": {
        "id": "CABLE_FALCON",
        "name": "GCX Falcon (Arabian Gulf Subsea Loop)",
        "type": "Submarine",
        "path_nodes": ["UAE_ABU_DHABI", "UAE_DUBAI", "UAE_FUJAIRAH", "OMAN_MUSCAT"],
        "total_capacity_gbps": 120.0,
        "allocated_gbps": 40.0,
        "latency_ms": 32.4,
        "osnr_db": 24.5,
        "ber": "0.8e-12",
        "status": "OPERATIONAL",
        "roadm_supported": True,
        "geopolitical_risk": "None (Territorial Waters & GCC Alliance)",
        "is_subsea": True,
        "color": "#10b981"
    },
    "CABLE_TERRESTRIAL_CONFLICT": {
        "id": "CABLE_TERRESTRIAL_CONFLICT",
        "name": "Northern Terrestrial Route (Conflict Territory Transit)",
        "type": "Terrestrial",
        "path_nodes": ["UAE_DUBAI", "CONFLICT_TRANSIT_NODE", "MARSEILLE_EU"],
        "total_capacity_gbps": 150.0,
        "allocated_gbps": 0.0,
        "latency_ms": 64.0,
        "osnr_db": 19.5,
        "ber": "3.1e-11",
        "status": "STANDBY",  # STANDBY, PROPOSED_BY_OPTICAL, POLICY_BLOCKED
        "roadm_supported": False,
        "geopolitical_risk": "CRITICAL: Traverses Hostile Territory (Cyber Warfare / Interception Risk)",
        "is_subsea": False,
        "color": "#ef4444"
    },
    "CABLE_TERRESTRIAL_GCC": {
        "id": "CABLE_TERRESTRIAL_GCC",
        "name": "GCC Terrestrial Southern Backhaul",
        "type": "Terrestrial",
        "path_nodes": ["UAE_ABU_DHABI", "GCC_SAUDI_RIYADH", "EGYPT_SUEZ"],
        "total_capacity_gbps": 60.0,
        "allocated_gbps": 50.0,
        "latency_ms": 95.0,
        "osnr_db": 18.2,
        "ber": "4.2e-11",
        "status": "OPERATIONAL",
        "roadm_supported": True,
        "geopolitical_risk": "Low (GCC Allied Transit)",
        "is_subsea": False,
        "color": "#f59e0b"
    }
}

def get_initial_network_state() -> Dict[str, Any]:
    """Returns a deep copy of the fresh network state."""
    import copy
    return {
        "nodes": copy.deepcopy(NODES),
        "cables": copy.deepcopy(DEFAULT_CABLES),
        "traffic_demands": {
            "Tier1_Critical_Banking": {
                "name": "CBUAE Critical Banking, RTGS & SWIFT",
                "demand_gbps": 50.0,
                "allocated_gbps": 50.0,
                "priority_level": 1,
                "max_allowed_latency_ms": 30.0,
                "sla_target": "99.999% Availability (Zero Outage)",
                "status": "PROTECTED"
            },
            "Tier2_Enterprise_Cloud": {
                "name": "Government & Enterprise Critical Cloud",
                "demand_gbps": 80.0,
                "allocated_gbps": 80.0,
                "priority_level": 2,
                "max_allowed_latency_ms": 80.0,
                "sla_target": "99.95% Availability",
                "status": "NORMAL"
            },
            "Tier3_Public_Internet": {
                "name": "Public Internet, OTT Video & Social Media",
                "demand_gbps": 220.0,
                "allocated_gbps": 220.0,
                "priority_level": 3,
                "max_allowed_latency_ms": 150.0,
                "sla_target": "Best Effort",
                "status": "NORMAL"
            }
        },
        "roadm_state": {
            "mode": "STANDARD_ROUTING",
            "active_wavelengths_allocated": 64,
            "banking_dedicated_lambdas": ["λ_1", "λ_2"],
            "preemption_status": "INACTIVE"
        }
    }
