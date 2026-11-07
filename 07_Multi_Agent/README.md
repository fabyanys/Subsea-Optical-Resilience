# 07 - Multi-Agent Architecture

Modul ini mengimplementasikan 4 Specialized Agents dan 1 Orchestrator Controller.

### Agen & Tanggung Jawab:
1. **Policy & Compliance Agent (`agents/policy_agent.py`)**:
   - Menganalisis batasan hukum, kepatuhan regulasi CBUAE (SLA perbankan), dan regulasi TDRA.
2. **Optical Network Technical Agent (`agents/optical_network_agent.py`)**:
   - Memeriksa kondisi fisik & logis jaringan (OTN layer, DWDM wavelength, landing stations Fujairah/Dubai).
3. **Resource Allocation Agent (`agents/resource_allocation_agent.py`)**:
   - Menghitung matematis alokasi bandwidth, pemotongan beban non-kritis (throttling), dan jalur proteksi cadangan.
4. **Decision Coordinator (`agents/decision_coordinator.py`)**:
   - Mengonsolidasikan input dari ketiga agen, menyeimbangkan trade-off, dan memformulasikan rekomendasi final.
5. **Orchestrator (`orchestrator.py`)**:
   - Mengendalikan alur kerja interaksi agen (menggunakan LangGraph / StateGraph).
