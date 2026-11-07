# Telecom & Critical Infrastructure Resilience Multi-Agent AI System
### Subsea Cable Crisis Orchestration, Sovereign Data Protection & Optical Wavelength Management

An autonomous Multi-Agent AI System designed to orchestrate the recovery and priority resource allocation of critical submarine telecommunications cables during physical breaks and geopolitical crises. The system enforces strict compliance with United Arab Emirates sovereign regulations (**CBUAE** banking regulations and **TDRA** telecommunications laws) alongside international photonic and subsea cable standards (**ITU-T** optical recommendations and **ICPC** government best practices). 

The platform utilizes **Local RAG + Local LLM (Llama-3.2-1B-Instruct GGUF)** to ensure total data sovereignty and the ability to operate in air-gapped, offline emergency command environments.

---

## System Architecture

```text
                 [ User Interface / Interactive Dashboard ]
                                    │
                                    ▼
                   [ Orchestrator / Main Controller ]
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
 [ Policy & Compliance ]   [ Optical Network ]   [ Resource Allocation ]
  • CBUAE Circular 1/2026   • ITU-T G.872 / G.709 • CBUAE Tier-1 SLA (100%)
  • TDRA Federal Law 3/2003 • ITU-T G.873.1 (<50ms)• Dynamic Lambda Slicing
  • NESA CIIP Clause 4.2.1  • DWDM Grid (G.694.1) • Non-essential Throttling
          │                         │                         │
          └─────────────────────────┼─────────────────────────┘
                                    │
                                    ▼
                        [ Decision Coordinator ]
                       • Sovereign Subsea Corridors
                       • Multi-Carrier Restoration
                                    │
                                    ▼
                       [ Final Decision & Audit Log ]
                       • Immutable Regulatory Proofs
                       • Article-by-Article Citations
                                    │
                                    ▼
                         [ Streamlit Dashboard ]
```

---

## Directory Structure & Regulatory Inventory

```text
Telecom_Resilience_AI/
│
├── 01_UAE_Banking_Regulations/        # CBUAE Operational Risk (Cir. 1/2026), Outsourcing (Cir. 14/2021), CIIP Policy
├── 02_UAE_Telecom_Regulations/        # TDRA Telecom Law (Decree No. 3/2003), International Cable Regulations V1.0
├── 03_ITU_T_Optical_Standards/        # ITU-T G.709 (2025), G.872 (2024), G.873.1 (2020), G.7703 ASON, G.694.1
├── 04_Submarine_Cable_Best_Practices/ # ICPC Best Practices V1.2, ICPC FADs Annex, ITU-T G Supplement 41 (2024)
│
├── 05_Knowledge_Base/                 # Regulatory text extraction, semantic chunking & FAISS vector indexing
│   ├── processed_chunks/              # Serialized chunk registry (chunks_summary.json)
│   ├── vector_db/                     # FAISS IndexFlatIP (cosine similarity) & metadata
│   ├── raw_docs/                      # Supplementary raw documents
│   └── ingest.py                      # Automated PDF/TXT parsing and indexing pipeline
│
├── 06_RAG_System/                     # Local LLM (Llama GGUF) + Local Embeddings + RAG Engine
│   ├── download_model.py              # Automated downloader for Llama-3.2-1B-Instruct GGUF
│   ├── rag_engine.py                  # Local retrieval-augmented generation engine
│   └── test_rag.py                    # Interactive CLI verification script
│
├── 07_Multi_Agent/                    # 4 Specialized Agents + Orchestrator
│   └── agents/
│       ├── policy_agent.py            # Regulatory Guardian & Sovereign Cybersecurity Auditor
│       ├── optical_network_agent.py   # Optical Layer Technical Specialist (DWDM, APS, OSNR)
│       ├── resource_allocation_agent.py # Mathematical QoS & Priority Slicing Optimizer
│       └── decision_coordinator.py    # Chief Incident Commander & Restoration Orchestrator
│
├── 08_Crisis_Simulation/              # UAE submarine cable topology, crisis scenario definitions & routing
│   ├── topologies/                    # GeoJSON and network models (Fujairah CLS, Dubai CLS, Abu Dhabi CLS)
│   └── scenarios/                     # Simulated cut scenarios (e.g. FUJAIRAH_SUBSEA_CUT)
│
├── 09_Audit_and_Evaluation/           # Audit trail logging, quantitative metrics & Streamlit GUI
│   ├── dashboard/                     # Full-featured interactive Streamlit monitoring dashboard
│   ├── evaluation_metrics/            # Latency, compliance score, and SLA delivery benchmarks
│   └── logs/                          # Immutable JSON audit trails with regulatory article citations
│
├── models/                            # Local model storage (Llama-3.2-1B-Instruct-Q4_K_M.gguf)
├── REGULATORY_COMPLIANCE_FRAMEWORK.md  # Comprehensive multi-agency regulatory and technical compliance guide
├── config.py                          # Unified system-wide configuration
├── requirements.txt                   # Complete Python dependencies
├── .env.example                       # Environment variables template
└── README.md                          # Main project documentation
```

---

## The Four Specialized Agents

1. **Policy & Compliance Agent (`policy_agent.py`)**:
   * Acts as a regulatory firewall before any optical or network rerouting is executed.
   * Audits proposed paths against **TDRA Article 14.3** and **CBUAE Circular 14/2021 Article 6**.
   * Automatically blocks rerouting plans traversing unauthorized foreign transit points or adversarial conflict zones.
2. **Optical Network Agent (`optical_network_agent.py`)**:
   * Evaluates physical transmission feasibility using **ITU-T G.872** and **ITU-T G.873.1**.
   * Validates optical power budgets ($-2.4\text{ dBm}$ optimal launch power), OSNR margins, and executes sub-50ms linear protection switching on dedicated DWDM wavelengths ($\lambda_1 = 1550.12\text{ nm}$).
3. **Resource Allocation Agent (`resource_allocation_agent.py`)**:
   * Enforces statutory priority under **CBUAE Circular 1/2026** (Operational Resilience for Critical Operations).
   * Allocates 100% guaranteed bandwidth ($50\text{ Gbps}$, $0\text{ Gbps}$ dropped) to Tier-1 financial systems (UAEFTS, RTGS, SWIFT) by preempting and throttling discretionary Tier-3 commercial traffic.
4. **Decision Coordinator Agent (`decision_coordinator.py`)**:
   * Orchestrates multi-agent consensus, selects compliant surviving subsea routes (e.g., GCX Falcon South landing at Dubai instead of severed Fujairah paths), and produces tamper-evident audit logs.

---

## Quickstart Guide

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/fabyanys/Subsea-Optical-Resilience.git
cd telecom-resilience-ai

# (Optional but recommended) Create and activate a virtual environment
# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# On Windows:
python -m venv venv
venv\Scripts\activate

# Install required Python dependencies
pip install -r requirements.txt
```

### 2. Ingest Regulatory Knowledge Base
Extracts text from all CBUAE, TDRA, ITU-T, and ICPC documents and builds the FAISS vector index:
```bash
python 05_Knowledge_Base/ingest.py
```

### 3. Launch the Interactive Dashboard
Launch the operator dashboard displaying real-time crisis telemetry, multi-agent reasoning, optical spectrum status, and audit logs:
```bash
streamlit run 09_Audit_and_Evaluation/dashboard/app.py --server.port 8501
```
*(On Windows environments, you can also launch directly via `run_dashboard.bat`)*

---

## Regulatory Compliance References
For detailed legal analysis, clause mappings, and standard cross-references, refer to [REGULATORY_COMPLIANCE_FRAMEWORK.md](REGULATORY_COMPLIANCE_FRAMEWORK.md) and the dedicated README files in each regulatory folder:
* [01 - UAE Banking Regulations (CBUAE & NESA)](01_UAE_Banking_Regulations/README.md)
* [02 - UAE Telecommunications Regulations (TDRA)](02_UAE_Telecom_Regulations/README.md)
* [03 - ITU-T Optical Transport Standards](03_ITU_T_Optical_Standards/README.md)
* [04 - Submarine Cable Best Practices (ICPC & ITU-T)](04_Submarine_Cable_Best_Practices/README.md)
* [05 - Knowledge Base Engine](05_Knowledge_Base/README.md)
