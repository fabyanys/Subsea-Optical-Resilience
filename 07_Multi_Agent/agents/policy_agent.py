import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from typing import Dict, Any, List

class PolicyComplianceAgent:
    """Agent 1: Policy & Compliance Agent.
    Specializes in evaluating route proposals against UAE Sovereign Laws,
    TDRA National Telecom Security Directives, and CBUAE Banking Regulations.
    Acts as the security and compliance firewall before any optical rerouting occurs.
    """

    def __init__(self, rag_engine=None):
        self.rag_engine = rag_engine
        self.agent_name = "Policy & Compliance Agent"
        self.agent_role = "Regulatory Guardian & Sovereign Cybersecurity Auditor"

    def intercept_and_audit(self, optical_proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Intercepts optical reroute proposals, puts the process on HOLD,
        and evaluates data sovereignty and geopolitical compliance.
        """
        proposed_path = optical_proposal.get("proposed_path", [])
        proposed_cable = optical_proposal.get("proposed_cable_name", "")

        # Detect conflict country transit
        has_conflict_transit = "CONFLICT_TRANSIT_NODE" in proposed_path or "Conflict" in proposed_cable

        if has_conflict_transit:
            # FATAL REGULATORY VIOLATION
            violations = [
                {
                    "framework": "UAE TDRA Telecommunications Regulatory Authority",
                    "article": "Article 14.3 - Critical Telecom Infrastructure Sovereignty",
                    "ruling": "STRICT VIOLATION",
                    "legal_text": "Routing UAE sovereign, civilian, or commercial telecommunications data through adversarial or unapproved foreign jurisdictions poses unacceptable cyber warfare, foreign interception, and BGP manipulation risks."
                },
                {
                    "framework": "Central Bank of the UAE (CBUAE)",
                    "article": "CIIP Policy Section 4.2.1 - In-Transit Financial Data Jurisdiction",
                    "ruling": "STRICT VIOLATION (Zero-Tolerance)",
                    "legal_text": "All banking transactions, RTGS settlement data, and SWIFT packets originating in the UAE are classified as Critical Information Infrastructure and must never traverse hostile border transit points where lawful wiretapping by adversarial entities can compromise financial confidentiality."
                }
            ]

            return {
                "agent": self.agent_name,
                "role": self.agent_role,
                "action": "INTERCEPT_AND_BLOCK",
                "verdict": "REJECTED & BLOCKED",
                "interception_status": "PROPOSAL HALTED - REROUTING ABORTED",
                "reason": (
                    "Proposed route crosses a territory in active geopolitical conflict with the UAE. "
                    "This creates catastrophic risks of electronic eavesdropping, deep packet inspection (DPI), "
                    "and sovereign data sabotage."
                ),
                "violations_found": violations,
                "escalation_target": "Decision Coordinator Agent",
                "escalation_message": (
                    "Terrestrial rerouting through conflict territory is legally barred and cannot proceed. "
                    "Requesting Decision Coordinator to provide a fully compliant alternative strategy "
                    "using surviving subsea infrastructure or approved allied corridors."
                ),
                "compliance_score": 0.0
            }
        else:
            return {
                "agent": self.agent_name,
                "role": self.agent_role,
                "action": "APPROVE_COMPLIANT_ROUTE",
                "verdict": "APPROVED",
                "compliance_score": 100.0,
                "violations_found": []
            }
