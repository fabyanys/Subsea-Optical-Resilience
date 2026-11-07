# Submarine Cable Resilience Orchestrator
## Minimalist Mission-Critical Multi-Page NOC Dashboard

A modern, minimalist, executive Network Operations Center (NOC) dashboard built with **Streamlit and Plotly** designed for the **ITU AI for Good Telecom Resilience Competition**.

---

### 📱 5-Page Architecture
1. **📊 Crisis Overview**:
   - High-level telemetry strip: *Active Submarine Routes*, *Operational Routes*, *Available Network Capacity*, and *Critical Services at Risk*.
   - **Tactical GIS Vector Topology Map**: Air-gapped Plotly vector map (zero external tile requests, no API key) with real-time glowing paths (Operational, Degraded, Disrupted, ROADM-prioritized).
   - **Network Health**: Radial Donut breakdown (Submarine Routes, Landing Stations, International Links, Capacity Utilization).
   - **Regional Connectivity**: Progress metrics for Middle East, Europe, Asia Pacific, and others.
   - **Network Performance Trend**: Multi-metric temporal line chart (Bandwidth in Cyan, Latency in Amber).
   - **Key Metrics**: Available capacity, average latency, utilization, and 99.9% service availability.
   - **Recent Network Events**: Real-time chronological incident feed.
2. **🤖 AI Agent Monitoring**:
   - Specialized 4-agent status cards (Optical Network Agent, Policy & Compliance Agent, Decision Coordinator Agent, Resource Allocation Agent).
   - Real-time deliberative communication terminal displaying step-by-step reasoning.
3. **⚖️ Decision & Recommendation**:
   - Restoration alternatives matrix:
     - *Alternative A: Northern Terrestrial Route* (Disqualified & Blocked by Policy due to UAE TDRA Art. 14.3 and CBUAE CIIP 4.2.1).
     - *Alternative B: Surviving Subsea Corridor + ROADM Priority* (Recommended & 100% Compliant).
   - Impact projections and trade-off analysis.
   - **Human-in-the-Loop NOC Commander Authorization Gate**: Interactive tactile buttons to authorize or reject execution.
4. **📚 Knowledge Base Evidence**:
   - Official legal corpora cards (CBUAE Banking, TDRA Telecom, ITU-T Standards, ICPC Best Practices).
   - Interactive Local LLM & RAG query console powered by `Llama-3.2-1B-Instruct GGUF` running 100% air-gapped on local CPU.
5. **📜 Audit Trail**:
   - Chronological tamper-evident audit ledger with timestamps and legal citations.
   - Direct JSON audit dossier export.

---

### 🚀 How to Run
```cmd
run_dashboard.bat
```
Or via Python:
```cmd
py -m streamlit run Telecom_Resilience_AI\09_Audit_and_Evaluation\dashboard\app.py --server.port 8501
```
Open in browser:
`http://localhost:8501`
