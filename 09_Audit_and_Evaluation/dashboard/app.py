import sys
from pathlib import Path

# Configure module import paths
DASHBOARD_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DASHBOARD_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
if str(PROJECT_ROOT / "07_Multi_Agent") not in sys.path:
    sys.path.append(str(PROJECT_ROOT / "07_Multi_Agent"))

import html
import json
import os
import pickle
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import orchestrator as orch_module
from config import DOC_DIRS, INDEX_FILE, METADATA_FILE, MODEL_PATH, N_CTX

ResilienceOrchestrator = orch_module.ResilienceOrchestrator

# ------------------------------------------------------------------------------
# PAGE CONFIGURATION (Left Sidebar Expanded, Wide Proportional NOC Layout)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Submarine Cable Resilience Orchestrator | National NOC",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = [
    "Crisis Overview",
    "AI Agent Monitoring",
    "Decision & Recommendation",
    "Knowledge Base Evidence",
    "Audit Trail",
]

# Session State Initialization (Version 6: Left Text-Box Nav + ArcGIS Satellite)
if "orchestrator" not in st.session_state or getattr(st.session_state.orchestrator, "version", 0) != 6:
    st.session_state.orchestrator = ResilienceOrchestrator()
    st.session_state.orchestrator.version = 6

if "current_page" not in st.session_state or st.session_state.current_page not in PAGES:
    st.session_state.current_page = PAGES[0]

if "kb_query_result" not in st.session_state:
    st.session_state.kb_query_result = None

orch: ResilienceOrchestrator = st.session_state.orchestrator
current_stage: str = orch.workflow_stage
state: Dict[str, Any] = orch.state
cables: Dict[str, Dict[str, Any]] = state["cables"]
nodes: Dict[str, Dict[str, Any]] = state["nodes"]
demands: Dict[str, Dict[str, Any]] = state["traffic_demands"]
roadm_state: Dict[str, Any] = state["roadm_state"]

now_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")


# ------------------------------------------------------------------------------
# MARITIME & CONTINENTAL WAYPOINTS FOR ARCGIS SATELLITE ROUTING
# ------------------------------------------------------------------------------
SATELLITE_ROUTE_WAYPOINTS: Dict[str, List[Tuple[float, float]]] = {
    "CABLE_SMW5": [
        (25.1288, 56.3565),  # Fujairah CLS
        (24.45, 58.10),      # Gulf of Oman
        (23.5880, 58.3829),  # Muscat CLS
        (21.40, 60.35),      # Arabian Sea Off Oman
        (14.35, 53.40),      # North of Socotra
        (12.25, 46.40),      # Gulf of Aden
        (11.5721, 43.1456),  # Djibouti Hub
        (12.68, 43.32),      # Bab el-Mandeb Strait
        (16.80, 40.65),      # Southern Red Sea
        (21.80, 37.90),      # Central Red Sea
        (27.10, 34.55),      # Northern Red Sea
        (29.9668, 32.5498),  # Suez Corridor
        (31.55, 32.25),      # Port Said Mediterranean
        (34.55, 24.20),      # South of Crete
        (37.95, 15.62),      # Strait of Messina
        (41.15, 9.75),       # Tyrrhenian Sea
        (43.2965, 5.3698),   # Marseille EU
    ],
    "CABLE_AAE1": [
        (25.1288, 56.3565),  # Fujairah CLS
        (24.10, 60.40),      # Eastern Gulf of Oman
        (21.15, 66.20),      # Northern Arabian Sea
        (18.9220, 72.8347),  # Mumbai Gateway
        (16.10, 62.10),      # Central Arabian Sea
        (12.70, 54.80),      # Arabian Sea South Corridor
        (11.75, 47.90),      # Gulf of Aden East
        (11.5721, 43.1456),  # Djibouti Hub
        (15.60, 41.35),      # Red Sea East Channel
        (20.90, 38.55),      # Red Sea Mid-East
        (26.35, 35.15),      # Red Sea North-East
        (29.9668, 32.5498),  # Suez Corridor
        (32.30, 31.30),      # Eastern Med
        (35.60, 22.40),      # Ionian Sea
        (38.75, 9.30),       # South of Sardinia
        (43.2965, 5.3698),   # Marseille EU
    ],
    "CABLE_FALCON": [
        (24.4539, 54.3773),  # Abu Dhabi Core
        (25.25, 54.45),      # Arabian Gulf Offshore
        (25.2048, 55.2708),  # Dubai Core
        (26.05, 55.85),      # Arabian Gulf Approach
        (26.42, 56.42),      # Strait of Hormuz Maritime Channel
        (25.75, 56.62),      # East Musandam Sea
        (25.1288, 56.3565),  # Fujairah CLS
        (24.30, 57.35),      # Batinah Offshore
        (23.5880, 58.3829),  # Muscat CLS
    ],
    "CABLE_TERRESTRIAL_GCC": [
        (24.4539, 54.3773),  # Abu Dhabi
        (24.20, 50.80),      # Eastern Arabia Fiber
        (24.7136, 46.6753),  # Riyadh Node
        (26.90, 40.20),      # Northwest GCC Fiber
        (29.10, 35.20),      # Aqaba / Sinai Approach
        (29.9668, 32.5498),  # Suez Interconnect
    ],
    "CABLE_TERRESTRIAL_CONFLICT": [
        (25.2048, 55.2708),  # Dubai
        (29.60, 48.40),      # Northern Gulf Landfall
        (33.3152, 44.3661),  # Conflict Transit Node
        (37.80, 38.20),      # Northern Overland Corridor
        (41.00, 28.95),      # Bosphorus Crossing
        (44.40, 14.50),      # Adriatic Overland
        (43.2965, 5.3698),   # Marseille EU
    ],
}


def smooth_polyline(coords: List[Tuple[float, float]], subdivisions: int = 5) -> Tuple[List[float], List[float]]:
    if len(coords) < 2:
        return [c[0] for c in coords], [c[1] for c in coords]
    lats: List[float] = []
    lons: List[float] = []
    for i in range(len(coords) - 1):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]
        start_s = 0 if i == 0 else 1
        for s in range(start_s, subdivisions + 1):
            t = s / subdivisions
            lats.append(lat1 + (lat2 - lat1) * t)
            lons.append(lon1 + (lon2 - lon1) * t)
    return lats, lons


def build_dashed_segments(
    lats: List[float], lons: List[float], draw_len: int = 2, gap_len: int = 2
) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    d_lats: List[Optional[float]] = []
    d_lons: List[Optional[float]] = []
    idx = 0
    n = len(lats)
    while idx < n - 1:
        end_idx = min(idx + draw_len + 1, n)
        for j in range(idx, end_idx):
            d_lats.append(lats[j])
            d_lons.append(lons[j])
        d_lats.append(None)
        d_lons.append(None)
        idx += draw_len + gap_len
    return d_lats, d_lons


def render_sparkline_svg(points: List[float], stroke_color: str) -> str:
    w, h = 92, 30
    if not points or len(points) < 2:
        return ""
    min_v, max_v = min(points), max(points)
    span = (max_v - min_v) if max_v != min_v else 1.0
    coords = []
    for idx, val in enumerate(points):
        x = (idx / (len(points) - 1)) * (w - 6) + 3
        y = h - 5 - ((val - min_v) / span) * (h - 10)
        coords.append((x, y))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    area = f"3,{h-3} " + poly + f" {w-3},{h-3}"
    lx, ly = coords[-1]
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        f'<polygon points="{area}" fill="{stroke_color}" fill-opacity="0.14" />'
        f'<polyline points="{poly}" fill="none" stroke="{stroke_color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.4" fill="{stroke_color}" />'
        f'</svg>'
    )


# ------------------------------------------------------------------------------
# CACHED KNOWLEDGE BASE & LOCAL AIR-GAPPED LLM HELPERS
# ------------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_kb_metadata() -> Tuple[List[Dict[str, Any]], int]:
    chunks: List[Dict[str, Any]] = []
    faiss_count = 0
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "rb") as f:
                data = pickle.load(f)
                if isinstance(data, list):
                    chunks = data
        except Exception:
            chunks = []
    if INDEX_FILE.exists():
        try:
            import faiss
            idx = faiss.read_index(str(INDEX_FILE))
            faiss_count = int(idx.ntotal)
        except Exception:
            faiss_count = len(chunks)
    else:
        faiss_count = len(chunks)
    return chunks, faiss_count


@st.cache_resource(show_spinner=False)
def load_local_llm(ctx_size: int = N_CTX):
    if not MODEL_PATH.exists():
        return None
    from llama_cpp import Llama
    threads = max(4, min((os.cpu_count() or 4) - 2, 8))
    return Llama(model_path=str(MODEL_PATH), n_ctx=ctx_size, n_threads=threads, verbose=False)


def format_llm_markdown(text: str) -> str:
    """Safely prepares LLM Markdown output for native Streamlit rendering so that
    angle-bracket expressions such as '<50 ms' or '<Tier-1>' are never swallowed
    or stripped as raw HTML tags while preserving bolding, lists, and paragraphs.
    """
    if not text:
        return ""
    cleaned = text.strip()
    parts = re.split(r"(`+[^`]*`+)", cleaned)
    for idx in range(0, len(parts), 2):
        parts[idx] = parts[idx].replace("<", r"\<")
    return "".join(parts)


_QUERY_STOPWORDS = {
    "what", "why", "how", "when", "where", "which", "who", "are", "is", "was",
    "were", "the", "and", "for", "with", "under", "during", "through", "into",
    "from", "that", "this", "these", "those", "does", "can", "should", "would",
    "could", "apply", "support", "rules", "systems", "state",
}


def retrieve_relevant_chunks(query: str, chunks: List[Dict[str, Any]], top_k: int = 4) -> List[Dict[str, Any]]:
    if not chunks or not query.strip():
        return []
    raw_tokens = [tok for tok in re.findall(r"[a-z0-9\.\-]+", query.lower()) if len(tok) > 2]
    tokens = [tok for tok in raw_tokens if tok not in _QUERY_STOPWORDS] or raw_tokens
    if not tokens:
        return chunks[:top_k]

    scored = []
    for item in chunks:
        text_lower = item.get("text", "").lower()
        src_lower = item.get("source", "").lower()
        cat_lower = item.get("category", "").lower()
        score = 0.0
        for tok in tokens:
            is_spec_code = bool(re.search(r"\d", tok)) or tok in {
                "tdra", "cbuae", "ciip", "roadm", "itu", "itu-t", "icpc", "otn", "wdm", "swift", "rtgs"
            }
            weight = 2.4 if is_spec_code else 1.0
            cnt = text_lower.count(tok)
            if cnt:
                score += weight * (1.0 + min(cnt, 5) * 0.35)
            if tok in src_lower or tok in cat_lower:
                score += weight * 1.6
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]


@st.cache_data(show_spinner=False)
def scan_document_inventory() -> List[Dict[str, str]]:
    label_map = {
        "CBUAE_Banking": "CBUAE Banking",
        "TDRA_Telecom": "UAE TDRA Telecom",
        "ITU_T_Optical": "ITU-T Optical",
        "ICPC_Submarine": "ICPC Submarine",
    }
    records: List[Dict[str, str]] = []
    for key, folder in DOC_DIRS.items():
        if folder.exists():
            for fp in sorted(folder.iterdir()):
                if fp.is_file() and fp.suffix.lower() in [".pdf", ".txt", ".md"]:
                    size_kb = fp.stat().st_size / 1024.0
                    size_str = f"{size_kb / 1024.0:.2f} MB" if size_kb >= 1024 else f"{size_kb:.0f} KB"
                    records.append({
                        "Domain": label_map.get(key, key),
                        "Document Reference": fp.name,
                        "Type": fp.suffix.upper().lstrip("."),
                        "Size": size_str,
                    })
    return records


# ------------------------------------------------------------------------------
# DYNAMIC NETWORK METRICS
# ------------------------------------------------------------------------------
operational_statuses = {"OPERATIONAL", "ROADM_PRIORITIZED"}
total_subsea_routes = sum(1 for c in cables.values() if c["is_subsea"])
active_subsea_routes = sum(1 for c in cables.values() if c["is_subsea"] and c["status"] in operational_statuses)
operational_routes = sum(1 for c in cables.values() if c["status"] in operational_statuses)
total_routes = len(cables)

available_capacity_gbps = sum(
    c["total_capacity_gbps"] for c in cables.values() if c["status"] in operational_statuses
)
allocated_traffic_gbps = sum(d["allocated_gbps"] for d in demands.values())

if current_stage == "NORMAL":
    critical_services_at_risk = 0
    overall_health_pct = 96
    avg_latency_ms = 34.2
    utilization_pct = round((allocated_traffic_gbps / max(available_capacity_gbps, 1.0)) * 100)
    banking_sla_str = "99.999%"
    stage_label = "NORMAL OPERATIONS"
    stage_badge_class = "status-pill-ok"
elif current_stage == "EXECUTED":
    critical_services_at_risk = 0
    overall_health_pct = 88
    avg_latency_ms = 32.4
    utilization_pct = 89
    banking_sla_str = "99.999%"
    stage_label = "MITIGATION ACTIVE"
    stage_badge_class = "status-pill-cyan"
elif current_stage == "AWAITING_HUMAN":
    critical_services_at_risk = 2
    overall_health_pct = 44
    avg_latency_ms = 74.8
    utilization_pct = 98
    banking_sla_str = "PENDING GATE"
    stage_label = "AWAITING AUTHORIZATION"
    stage_badge_class = "status-pill-warn"
elif current_stage == "REJECTED":
    critical_services_at_risk = 3
    overall_health_pct = 38
    avg_latency_ms = 88.5
    utilization_pct = 99
    banking_sla_str = "MANUAL HOLD"
    stage_label = "QUARANTINE HOLD"
    stage_badge_class = "status-pill-crit"
else:
    critical_services_at_risk = 3
    overall_health_pct = 36
    avg_latency_ms = 86.0
    utilization_pct = 99
    banking_sla_str = "AT RISK"
    stage_label = "INCIDENT ACTIVE"
    stage_badge_class = "status-pill-crit"


# ------------------------------------------------------------------------------
# ENTERPRISE NOC CSS (Left Sidebar Pure Text + Active Box, Zero Circles)
# ------------------------------------------------------------------------------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"], .stApp {
        background-color: #060b14 !important;
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Clean Streamlit Chrome while keeping Sidebar Collapse/Expand Toggle Crisp & Responsive */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.4rem !important;
        pointer-events: none !important;
    }
    header[data-testid="stHeader"] button,
    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapseButton"] button {
        pointer-events: auto !important;
        color: #cbd5e1 !important;
    }
    [data-testid="stExpandSidebarButton"] {
        background: #0c1629 !important;
        border: 1px solid #1e3458 !important;
        border-radius: 8px !important;
        margin-left: 6px !important;
        margin-top: 4px !important;
    }
    [data-testid="stExpandSidebarButton"]:hover {
        border-color: #38bdf8 !important;
        color: #ffffff !important;
    }
    .stAppDeployButton,
    [data-testid="stAppDeployButton"],
    [data-testid="stMainMenu"],
    [data-testid="stToolbarActions"],
    [data-testid="stDecoration"],
    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
    }

    /* Full-Width Responsive Main Container (Expands Automatically When Sidebar Collapses) */
    [data-testid="stAppViewContainer"] {
        width: 100% !important;
        max-width: 100% !important;
    }
    section[data-testid="stMain"] {
        flex: 1 1 0% !important;
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stMain"] > div.block-container,
    [data-testid="stMainBlockContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        padding-top: 0.6rem !important;
        padding-bottom: 2.2rem !important;
        padding-left: 1.8rem !important;
        padding-right: 1.8rem !important;
    }

    /* Responsive Left Sidebar: Fixed 256px when Expanded, True 0px when Collapsed */
    [data-testid="stSidebar"] {
        background-color: #070d19 !important;
        border-right: 1px solid #15243d !important;
        transition: width 0.2s ease, min-width 0.2s ease, max-width 0.2s ease !important;
    }
    [data-testid="stSidebar"][aria-expanded="true"] {
        width: 256px !important;
        min-width: 256px !important;
        max-width: 256px !important;
    }
    [data-testid="stSidebar"][aria-expanded="false"] {
        width: 0px !important;
        min-width: 0px !important;
        max-width: 0px !important;
        margin-left: 0px !important;
        border-right: none !important;
        overflow: hidden !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.1rem !important;
        padding-left: 0.95rem !important;
        padding-right: 0.95rem !important;
        padding-bottom: 1.2rem !important;
    }

    /* ------------------------------------------------------------------
       LEFT SIDEBAR NAVIGATION MENU:
       - Zero circles / zero radio inputs
       - Inactive tab = pure clean text only
       - Active tab = crisp bordered box surrounding the text
       ------------------------------------------------------------------ */
    .st-key-sidebar_nav_menu {
        gap: 3px !important;
    }
    .st-key-sidebar_nav_menu div.stButton > button {
        justify-content: flex-start !important;
        text-align: left !important;
        padding: 0 13px !important;
        height: 38px !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        transition: all 0.14s ease !important;
    }
    .st-key-sidebar_nav_menu div.stButton > button div[data-testid="stMarkdownContainer"] {
        width: 100% !important;
        text-align: left !important;
    }
    /* Inactive Navigation Tab: Text only, no box, no circle */
    .st-key-sidebar_nav_menu div.stButton > button[kind="tertiary"] {
        background: transparent !important;
        border: 1px solid transparent !important;
        box-shadow: none !important;
        color: #94a3b8 !important;
        font-weight: 500 !important;
    }
    .st-key-sidebar_nav_menu div.stButton > button[kind="tertiary"]:hover {
        background: rgba(30, 58, 95, 0.28) !important;
        color: #e2e8f0 !important;
    }
    /* Active / Opened Navigation Tab: Highlighted Box Surrounding Text */
    .st-key-sidebar_nav_menu div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, rgba(14, 165, 233, 0.20) 0%, rgba(15, 23, 42, 0.55) 100%) !important;
        border: 1px solid #38bdf8 !important;
        box-shadow: 0 2px 12px rgba(14, 165, 233, 0.14) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Cohesive Bordered Cards in Main Workspace */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(180deg, #0b1425 0%, #08101e 100%) !important;
        border: 1px solid #182946 !important;
        border-radius: 12px !important;
        padding: 16px 18px !important;
        box-shadow: 0 8px 26px rgba(0, 0, 0, 0.32) !important;
    }

    /* Top Header Bar */
    .noc-topbar {
        background: linear-gradient(90deg, #0a1324 0%, #0d182e 55%, #0a1324 100%);
        border: 1px solid #182946;
        border-radius: 12px;
        padding: 12px 20px;
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        flex-wrap: wrap;
    }
    .brand-wrap {
        display: flex;
        align-items: center;
        gap: 13px;
    }
    .brand-mark {
        width: 34px;
        height: 34px;
        border-radius: 8px;
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.22) 0%, rgba(37, 99, 235, 0.30) 100%);
        border: 1px solid rgba(56, 189, 248, 0.45);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .brand-name {
        font-size: 15.5px;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .brand-sub {
        font-size: 11px;
        color: #7c93b2;
        margin-top: 2px;
    }

    /* Status Pills */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 5px 12px;
        border-radius: 999px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 10.5px;
        font-weight: 600;
        letter-spacing: 0.03em;
    }
    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
    }
    .status-pill-ok { background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4); color: #34d399; }
    .status-pill-ok .status-dot { background: #10b981; box-shadow: 0 0 6px #10b981; }
    .status-pill-cyan { background: rgba(6, 182, 212, 0.14); border: 1px solid rgba(34, 211, 238, 0.45); color: #22d3ee; }
    .status-pill-cyan .status-dot { background: #22d3ee; box-shadow: 0 0 6px #22d3ee; }
    .status-pill-warn { background: rgba(245, 158, 11, 0.14); border: 1px solid rgba(245, 158, 11, 0.45); color: #fbbf24; }
    .status-pill-warn .status-dot { background: #f59e0b; box-shadow: 0 0 6px #f59e0b; }
    .status-pill-crit { background: rgba(239, 68, 68, 0.14); border: 1px solid rgba(239, 68, 68, 0.45); color: #f87171; }
    .status-pill-crit .status-dot { background: #ef4444; box-shadow: 0 0 6px #ef4444; }

    .meta-chip {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #cbd5e1;
        background: #0f1b30;
        border: 1px solid #1e3254;
        padding: 5px 10px;
        border-radius: 7px;
    }

    /* Proportional KPI Cards */
    .kpi-card {
        background: linear-gradient(180deg, #0b1426 0%, #08101e 100%);
        border: 1px solid #182946;
        border-radius: 12px;
        padding: 15px 18px;
        height: 104px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.26);
    }
    .kpi-label {
        font-size: 11.5px;
        font-weight: 500;
        color: #8da2c0;
    }
    .kpi-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        gap: 8px;
    }
    .kpi-val {
        font-size: 26px;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.03em;
        line-height: 1.05;
    }
    .kpi-unit {
        font-size: 13px;
        font-weight: 500;
        color: #94a3b8;
        margin-left: 4px;
    }
    .kpi-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        margin-top: 5px;
    }
    .c-pos { color: #34d399; }
    .c-neg { color: #f87171; }
    .c-neu { color: #38bdf8; }

    /* Card Headers */
    .sec-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 9px;
        border-bottom: 1px solid #14233c;
    }
    .sec-title {
        font-size: 13.5px;
        font-weight: 600;
        color: #f1f5f9;
        letter-spacing: -0.01em;
    }
    .sec-sub {
        font-size: 11px;
        color: #64748b;
        margin-left: 8px;
        font-weight: 400;
    }
    .sec-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        font-weight: 500;
        color: #94a3b8;
        background: #0f1b30;
        border: 1px solid #1d3152;
        padding: 2px 8px;
        border-radius: 5px;
    }

    /* Tables */
    .noc-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }
    .noc-table th {
        text-align: left;
        font-size: 10.5px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #7c93b2;
        padding: 8px 10px;
        border-bottom: 1px solid #192b48;
    }
    .noc-table td {
        padding: 9px 10px;
        color: #cbd5e1;
        border-bottom: 1px solid #111e34;
        vertical-align: middle;
    }
    .noc-table tr:last-child td {
        border-bottom: none;
    }

    .badge-sm {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        font-weight: 600;
    }
    .b-ok { background: rgba(16, 185, 129, 0.14); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.32); }
    .b-cyan { background: rgba(6, 182, 212, 0.15); color: #22d3ee; border: 1px solid rgba(34, 211, 238, 0.35); }
    .b-warn { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.35); }
    .b-crit { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.35); }
    .b-muted { background: rgba(100, 116, 139, 0.15); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.3); }

    .mono { font-family: 'JetBrains Mono', monospace; }

    /* Collapsible Agent Description Drawers & Expanders */
    details.agent-drawer {
        margin-top: 10px;
        padding-top: 8px;
        border-top: 1px solid #14233c;
    }
    details.agent-drawer > summary {
        list-style: none;
        cursor: pointer;
        font-size: 11px;
        font-weight: 600;
        color: #38bdf8;
        display: flex;
        justify-content: space-between;
        align-items: center;
        user-select: none;
    }
    details.agent-drawer > summary::-webkit-details-marker {
        display: none;
    }
    details.agent-drawer > summary::after {
        content: "Show";
        font-family: 'JetBrains Mono', monospace;
        font-size: 9.5px;
        color: #7c93b2;
        background: #0f1b30;
        border: 1px solid #1e3254;
        padding: 1px 6px;
        border-radius: 4px;
    }
    details.agent-drawer[open] > summary::after {
        content: "Hide";
        color: #cbd5e1;
        border-color: #38bdf8;
    }
    details.agent-drawer .drawer-body {
        margin-top: 8px;
        font-size: 11.5px;
        line-height: 1.6;
        color: #94a3b8;
    }

    [data-testid="stExpander"] {
        background: #0a1324 !important;
        border: 1px solid #182946 !important;
        border-radius: 10px !important;
        margin-bottom: 10px !important;
    }
    [data-testid="stExpander"] summary {
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
    [data-testid="stExpander"] summary p {
        font-size: 12.5px !important;
        font-weight: 600 !important;
        color: #f1f5f9 !important;
    }

    /* Full Unclipped Local LLM Synthesis Container */
    .st-key-llm_synthesis_box {
        background: linear-gradient(180deg, #0b162a 0%, #081222 100%) !important;
        border: 1px solid #1d3557 !important;
        border-left: 3px solid #22d3ee !important;
        border-radius: 10px !important;
        padding: 16px 20px !important;
        margin-top: 10px !important;
        margin-bottom: 12px !important;
        max-height: none !important;
        height: auto !important;
        overflow: visible !important;
    }
    .st-key-llm_synthesis_box [data-testid="stMarkdownContainer"] {
        max-height: none !important;
        overflow: visible !important;
        word-break: normal !important;
        overflow-wrap: break-word !important;
    }
    .st-key-llm_synthesis_box [data-testid="stMarkdownContainer"] p,
    .st-key-llm_synthesis_box [data-testid="stMarkdownContainer"] li {
        font-size: 13.5px !important;
        line-height: 1.72 !important;
        color: #e2e8f0 !important;
    }
    .st-key-llm_synthesis_box [data-testid="stMarkdownContainer"] p {
        margin-bottom: 10px !important;
    }
    .st-key-llm_synthesis_box [data-testid="stMarkdownContainer"] p:last-child {
        margin-bottom: 0 !important;
    }
    .st-key-llm_synthesis_box [data-testid="stMarkdownContainer"] ul,
    .st-key-llm_synthesis_box [data-testid="stMarkdownContainer"] ol {
        margin-top: 4px !important;
        margin-bottom: 10px !important;
        padding-left: 20px !important;
    }
    .llm-meta-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        padding-bottom: 10px;
        margin-bottom: 10px;
        border-bottom: 1px solid #162946;
    }

    /* Standard Action Buttons (Outside Nav Menu) */
    .st-key-sim_controls div.stButton > button,
    section[data-testid="stMain"] div.stButton > button,
    section[data-testid="stMain"] div.stDownloadButton > button {
        border-radius: 8px !important;
        font-size: 12.5px !important;
        font-weight: 600 !important;
        height: 38px !important;
        padding: 0 14px !important;
        border: 1px solid #213757 !important;
        background: #0f1b30 !important;
        color: #e2e8f0 !important;
    }
    .st-key-sim_controls div.stButton > button:hover,
    section[data-testid="stMain"] div.stButton > button:hover {
        border-color: #38bdf8 !important;
        color: #ffffff !important;
    }
    .st-key-sim_controls div.stButton > button[kind="primary"],
    section[data-testid="stMain"] div.stButton > button[kind="primary"] {
        background: linear-gradient(180deg, #0284c7 0%, #0369a1 100%) !important;
        border: 1px solid #38bdf8 !important;
        color: #ffffff !important;
    }
    .st-key-sim_controls div.stButton > button[kind="primary"]:hover,
    section[data-testid="stMain"] div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(180deg, #0ea5e9 0%, #0284c7 100%) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------------------
# LEFT SIDEBAR: PURE TEXT NAVIGATION (WITH BOX ON ACTIVE TAB) + SIMULATION CONTROLS
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 2px 4px 12px 4px; border-bottom: 1px solid #15243d; margin-bottom: 12px;">
            <div style="font-size: 9.5px; font-weight: 600; letter-spacing: 0.09em; color: #38bdf8; text-transform: uppercase;">
                UAE Sovereign Telecom NOC
            </div>
            <div style="font-size: 13.5px; font-weight: 700; color: #f8fafc; margin-top: 3px;">
                Resilience Control Plane
            </div>
        </div>
        <div style="font-size: 10px; font-weight: 600; letter-spacing: 0.08em; color: #64748b; text-transform: uppercase; margin-bottom: 6px; padding-left: 4px;">
            Navigation
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Pure Text Navigation Items — Active Tab gets a Bordered Box, Inactive Tabs are Plain Text (Zero Circles)
    with st.container(key="sidebar_nav_menu"):
        for page_item in PAGES:
            is_active = st.session_state.current_page == page_item
            if st.button(
                page_item,
                key=f"nav_btn_{page_item}",
                type="primary" if is_active else "tertiary",
                width="stretch",
            ):
                if not is_active:
                    st.session_state.current_page = page_item
                    st.rerun()

    st.markdown(
        f"""
        <div style="margin-top: 16px; padding-top: 14px; border-top: 1px solid #15243d; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 10px; font-weight: 600; letter-spacing: 0.08em; color: #64748b; text-transform: uppercase;">
                Incident Simulator
            </span>
            <span class="mono" style="font-size: 9.5px; color: #94a3b8;">{current_stage}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Simulation Control Buttons in Left Sidebar
    with st.container(key="sim_controls"):
        if st.button(
            "Simulate Cable Cut",
            width="stretch",
            type="primary" if current_stage == "NORMAL" else "secondary",
            disabled=(current_stage != "NORMAL"),
        ):
            orch.trigger_subsea_disruption()
            st.rerun()

        if current_stage == "DISRUPTED":
            if st.button("Next: Optical Proposal", width="stretch", type="primary"):
                orch.run_optical_proposal()
                st.rerun()
        elif current_stage == "OPTICAL_PROPOSED":
            if st.button("Next: Policy Audit", width="stretch", type="primary"):
                orch.run_policy_interception()
                st.rerun()
        elif current_stage == "POLICY_BLOCKED":
            if st.button("Next: Coordinator Plan", width="stretch", type="primary"):
                orch.run_coordinator_synthesis()
                st.rerun()

        if current_stage in ["DISRUPTED", "OPTICAL_PROPOSED", "POLICY_BLOCKED"]:
            if st.button("Run Agent Deliberation", width="stretch"):
                if orch.workflow_stage == "DISRUPTED":
                    orch.run_optical_proposal()
                if orch.workflow_stage == "OPTICAL_PROPOSED":
                    orch.run_policy_interception()
                if orch.workflow_stage == "POLICY_BLOCKED":
                    orch.run_coordinator_synthesis()
                st.rerun()

        if current_stage == "AWAITING_HUMAN" and st.session_state.current_page != "Decision & Recommendation":
            if st.button("Open Decision Gate", width="stretch", type="primary"):
                st.session_state.current_page = "Decision & Recommendation"
                st.rerun()

        if st.button("Reset System", width="stretch"):
            st.session_state.orchestrator = ResilienceOrchestrator()
            st.session_state.orchestrator.version = 6
            st.rerun()

    # Subtle Architectural Watermark at Sidebar Bottom
    st.markdown(
        """
        <div style="margin-top: 26px; padding-top: 14px; border-top: 1px solid #111e34; text-align: center;">
            <svg viewBox="0 0 180 42" width="100%" height="38" style="opacity: 0.20;">
                <line x1="8" y1="38" x2="172" y2="38" stroke="#38bdf8" stroke-width="1"/>
                <rect x="24" y="21" width="10" height="17" fill="#1e3a5f"/>
                <rect x="38" y="15" width="12" height="23" fill="#1e3a5f"/>
                <path d="M 68 38 L 68 5 Q 88 13 82 38 Z" fill="#0284c7"/>
                <line x1="68" y1="3" x2="68" y2="38" stroke="#38bdf8" stroke-width="1.2"/>
                <rect x="98" y="19" width="14" height="19" fill="#1e3a5f"/>
                <polygon points="126,38 129,4 132,38" fill="#38bdf8"/>
                <rect x="140" y="23" width="11" height="15" fill="#1e3a5f"/>
            </svg>
            <div class="mono" style="font-size: 9px; color: #475569; letter-spacing: 0.08em; margin-top: 4px;">
                LOCAL AIR-GAPPED LLM ENGINE
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------------------
# TOP INSTITUTIONAL HEADER BAR
# ------------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="noc-topbar">
        <div class="brand-wrap">
            <div class="brand-mark">
                <svg width="19" height="19" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M2 9C5.5 9 6.5 5 10 5C13.5 5 14.5 13 18 13C20 13 21 11 22 10" stroke="#38bdf8" stroke-width="2" stroke-linecap="round"/>
                    <path d="M2 16C5.5 16 6.5 12 10 12C13.5 12 14.5 20 18 20C20 20 21 18 22 17" stroke="#0284c7" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </div>
            <div>
                <div class="brand-name">Submarine Cable Resilience Orchestrator</div>
                <div class="brand-sub">Autonomous Multi-Agent Optical Governance &amp; Sovereign Compliance Console</div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
            <div class="status-pill {stage_badge_class}">
                <span class="status-dot"></span>
                <span>{stage_label}</span>
            </div>
            <div class="meta-chip">{now_utc}</div>
            <div class="meta-chip">OP: NOC-CMD-01</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Contextual Executive Strip when Operator Decision is Pending
if current_stage == "AWAITING_HUMAN" and st.session_state.current_page != "Decision & Recommendation":
    with st.container(border=True):
        b_txt, b_act = st.columns([3.4, 1.0], vertical_alignment="center")
        with b_txt:
            st.markdown(
                """
                <div style="font-size: 12px; color: #fde68a;">
                    <span class="badge-sm b-warn" style="margin-right: 8px;">PENDING AUTHORIZATION</span>
                    Policy Agent blocked the Northern Terrestrial conflict route. Coordinator recommends <strong>GCX Falcon Subsea + ROADM Priority + QoS Slicing</strong>.
                </div>
                """,
                unsafe_allow_html=True,
            )
        with b_act:
            if st.button("Review & Authorize", key="banner_jump_gate", type="primary", width="stretch"):
                st.session_state.current_page = "Decision & Recommendation"
                st.rerun()


# ==============================================================================
# PAGE 1: CRISIS OVERVIEW (Large ArcGIS Satellite Map + Proportional NOC Grid)
# ==============================================================================
if st.session_state.current_page == "Crisis Overview":
    # Row 1: 4 Proportional KPI Cards
    k1, k2, k3, k4 = st.columns(4, gap="medium")

    subsea_spark = [3, 3, 3, 3, 3, 3, 3] if active_subsea_routes == 3 else [3, 3, 3, 3, 2, 1, 1]
    subsea_col = "#10b981" if active_subsea_routes == 3 else "#ef4444"
    subsea_sub = "+0 vs baseline (Healthy)" if active_subsea_routes == 3 else "-2 severed (SMW5, AAE-1)"
    subsea_cls = "c-pos" if active_subsea_routes == 3 else "c-neg"

    op_spark = [4, 4, 4, 4, 4, 4, 4] if operational_routes >= 4 else [4, 4, 4, 3, 2, 2, 2]
    op_col = "#38bdf8" if operational_routes >= 4 else ("#22d3ee" if current_stage == "EXECUTED" else "#f59e0b")
    op_sub = "4 active, 1 standby" if operational_routes >= 4 else (
        "ROADM lambda priority active" if current_stage == "EXECUTED" else "-2 international trunks cut"
    )
    op_cls = "c-pos" if operational_routes >= 4 else ("c-neu" if current_stage == "EXECUTED" else "c-neg")

    cap_spark = [560, 560, 560, 560, 560, 560, 560] if available_capacity_gbps > 200 else [560, 560, 520, 310, 180, 180, 180]
    cap_col = "#38bdf8" if available_capacity_gbps > 200 else ("#10b981" if current_stage == "EXECUTED" else "#ef4444")
    cap_sub = "100% nominal capacity" if available_capacity_gbps > 200 else (
        "Banking 50 Gbps guaranteed" if current_stage == "EXECUTED" else "-380 Gbps trunk loss"
    )
    cap_cls = "c-pos" if (available_capacity_gbps > 200 or current_stage == "EXECUTED") else "c-neg"

    risk_spark = [0, 0, 0, 0, 0, 0, 0] if critical_services_at_risk == 0 else [0, 0, 0, 1, 3, 3, critical_services_at_risk]
    risk_col = "#10b981" if critical_services_at_risk == 0 else "#f59e0b"
    risk_sub = "CBUAE RTGS protected" if critical_services_at_risk == 0 else f"{critical_services_at_risk} tiers degraded"
    risk_cls = "c-pos" if critical_services_at_risk == 0 else "c-neg"

    kpi_defs = [
        (k1, "Active Submarine Routes", str(active_subsea_routes), f"/ {total_subsea_routes}", subsea_sub, subsea_cls, subsea_spark, subsea_col),
        (k2, "Operational Corridors", str(operational_routes), f"/ {total_routes}", op_sub, op_cls, op_spark, op_col),
        (k3, "Available Network Capacity", f"{available_capacity_gbps:.0f}", "Gbps", cap_sub, cap_cls, cap_spark, cap_col),
        (k4, "Critical Services at Risk", str(critical_services_at_risk), "Tiers", risk_sub, risk_cls, risk_spark, risk_col),
    ]
    for col_k, lbl, val, unit, sub, cls_name, spk, scol in kpi_defs:
        with col_k:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{lbl}</div>
                    <div class="kpi-row">
                        <div>
                            <div class="kpi-val">{val}<span class="kpi-unit">{unit}</span></div>
                            <div class="kpi-sub {cls_name}">{sub}</div>
                        </div>
                        <div>{render_sparkline_svg(spk, scol)}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Row 2: Large Hero ArcGIS Satellite Topology Map (Left) + Balanced Right Stack
    col_map, col_right = st.columns([2.25, 1.0], gap="medium")

    with col_map:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="sec-head">
                    <div>
                        <span class="sec-title">Submarine &amp; Terrestrial Network Topology</span>
                        <span class="sec-sub">ArcGIS World Satellite Imagery &amp; Optical Telemetry</span>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <span class="sec-tag">ROADM: {roadm_state['mode']}</span>
                        <span class="sec-tag">ESRI SATELLITE</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            fig_map = go.Figure()

            for cid, cinfo in cables.items():
                waypoints = SATELLITE_ROUTE_WAYPOINTS.get(
                    cid, [(nodes[nid]["lat"], nodes[nid]["lon"]) for nid in cinfo["path_nodes"]]
                )
                s_lats, s_lons = smooth_polyline(waypoints, subdivisions=5)
                status = cinfo["status"]

                hover_txt = (
                    f"<b>{cinfo['name']}</b><br>"
                    f"Status: {status} | Medium: {cinfo['type']}<br>"
                    f"Capacity: {cinfo['total_capacity_gbps']:.0f} Gbps | Latency: {cinfo['latency_ms']} ms | OSNR: {cinfo['osnr_db']} dB<br>"
                    f"Jurisdiction: {cinfo['geopolitical_risk']}"
                )

                if status == "OPERATIONAL":
                    core_col = "#10b981" if cinfo["is_subsea"] else "#38bdf8"
                    glow_col = "rgba(16, 185, 129, 0.28)" if cinfo["is_subsea"] else "rgba(56, 189, 248, 0.24)"
                    fig_map.add_trace(
                        go.Scattermap(
                            lat=s_lats,
                            lon=s_lons,
                            mode="lines",
                            line=dict(width=10, color=glow_col),
                            hoverinfo="skip",
                            showlegend=False,
                        )
                    )
                    fig_map.add_trace(
                        go.Scattermap(
                            lat=s_lats,
                            lon=s_lons,
                            mode="lines",
                            line=dict(width=3.2, color=core_col),
                            hoverinfo="text",
                            text=hover_txt,
                            showlegend=False,
                        )
                    )
                    if cinfo["is_subsea"]:
                        fig_map.add_trace(
                            go.Scattermap(
                                lat=s_lats[6:-6:10],
                                lon=s_lons[6:-6:10],
                                mode="markers",
                                marker=dict(size=5, color="#a7f3d0", opacity=0.85, allowoverlap=True),
                                hoverinfo="skip",
                                showlegend=False,
                            )
                        )

                elif status == "ROADM_PRIORITIZED":
                    fig_map.add_trace(
                        go.Scattermap(
                            lat=s_lats,
                            lon=s_lons,
                            mode="lines",
                            line=dict(width=14, color="rgba(34, 211, 238, 0.34)"),
                            hoverinfo="skip",
                            showlegend=False,
                        )
                    )
                    fig_map.add_trace(
                        go.Scattermap(
                            lat=s_lats,
                            lon=s_lons,
                            mode="lines",
                            line=dict(width=4.5, color="#22d3ee"),
                            hoverinfo="text",
                            text=hover_txt,
                            showlegend=False,
                        )
                    )
                    fig_map.add_trace(
                        go.Scattermap(
                            lat=s_lats[4:-4:7],
                            lon=s_lons[4:-4:7],
                            mode="markers",
                            marker=dict(size=6, color="#ffffff", opacity=0.92, allowoverlap=True),
                            hoverinfo="skip",
                            showlegend=False,
                        )
                    )

                elif status in ["SEVERELY_CUT", "POLICY_BLOCKED", "PROPOSED_BY_OPTICAL"]:
                    seg_col = "#f59e0b" if status == "PROPOSED_BY_OPTICAL" else "#ef4444"
                    glow_seg = "rgba(245, 158, 11, 0.24)" if status == "PROPOSED_BY_OPTICAL" else "rgba(239, 68, 68, 0.25)"
                    d_lats, d_lons = build_dashed_segments(s_lats, s_lons, draw_len=2, gap_len=2)
                    fig_map.add_trace(
                        go.Scattermap(
                            lat=s_lats,
                            lon=s_lons,
                            mode="lines",
                            line=dict(width=8, color=glow_seg),
                            hoverinfo="text",
                            text=hover_txt,
                            showlegend=False,
                        )
                    )
                    fig_map.add_trace(
                        go.Scattermap(
                            lat=d_lats,
                            lon=d_lons,
                            mode="lines",
                            line=dict(width=3.4, color=seg_col),
                            hoverinfo="skip",
                            showlegend=False,
                        )
                    )

                else:
                    d_lats, d_lons = build_dashed_segments(s_lats, s_lons, draw_len=1, gap_len=3)
                    fig_map.add_trace(
                        go.Scattermap(
                            lat=d_lats,
                            lon=d_lons,
                            mode="lines",
                            line=dict(width=1.8, color="rgba(148, 163, 184, 0.55)"),
                            hoverinfo="text",
                            text=hover_txt,
                            showlegend=False,
                        )
                    )

            uae_nodes = [(nid, n) for nid, n in nodes.items() if n["country"] == "UAE"]
            allied_nodes = [(nid, n) for nid, n in nodes.items() if n["country"] != "UAE" and "CONFLICT" not in nid]
            conflict_nodes = [(nid, n) for nid, n in nodes.items() if "CONFLICT" in nid]

            # Allied Stations
            fig_map.add_trace(
                go.Scattermap(
                    lat=[n["lat"] for _, n in allied_nodes],
                    lon=[n["lon"] for _, n in allied_nodes],
                    mode="markers",
                    marker=dict(size=16, color="#10b981", opacity=0.28, allowoverlap=True),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
            fig_map.add_trace(
                go.Scattermap(
                    lat=[n["lat"] for _, n in allied_nodes],
                    lon=[n["lon"] for _, n in allied_nodes],
                    mode="markers+text",
                    marker=dict(size=8.5, color="#10b981", opacity=1.0, allowoverlap=True),
                    text=[
                        n["name"]
                        .split("(")[0]
                        .replace("Cable Landing Station", "")
                        .replace("Subsea Teleport", "")
                        .replace("Optical Corridor", "")
                        .replace("GCC Terrestrial Node", "")
                        .strip()
                        for _, n in allied_nodes
                    ],
                    textposition="top right",
                    textfont=dict(family="Inter, sans-serif", size=11, color="#f1f5f9"),
                    hoverinfo="text",
                    hovertext=[f"<b>{n['name']}</b><br>{n['country']} — {n['role']}" for _, n in allied_nodes],
                    showlegend=False,
                )
            )

            # UAE Sovereign Hub Halo + Distinct Non-Overlapping Labels
            fig_map.add_trace(
                go.Scattermap(
                    lat=[n["lat"] for _, n in uae_nodes],
                    lon=[n["lon"] for _, n in uae_nodes],
                    mode="markers",
                    marker=dict(size=24, color="#38bdf8", opacity=0.30, allowoverlap=True),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
            for nid, n in uae_nodes:
                lbl = "Fujairah CLS" if "FUJAIRAH" in nid else ("Dubai Core" if "DUBAI" in nid else "Abu Dhabi CBUAE")
                tpos = "top right" if "FUJAIRAH" in nid else ("top left" if "DUBAI" in nid else "bottom left")
                fig_map.add_trace(
                    go.Scattermap(
                        lat=[n["lat"]],
                        lon=[n["lon"]],
                        mode="markers+text",
                        marker=dict(size=10, color="#ffffff", opacity=1.0, allowoverlap=True),
                        text=[lbl],
                        textposition=tpos,
                        textfont=dict(family="Inter, sans-serif", size=11, color="#ffffff"),
                        hoverinfo="text",
                        hovertext=[f"<b>{n['name']}</b><br>UAE Sovereign Core — {n['role']}"],
                        showlegend=False,
                    )
                )

            # Conflict Transit Node
            fig_map.add_trace(
                go.Scattermap(
                    lat=[n["lat"] for _, n in conflict_nodes],
                    lon=[n["lon"] for _, n in conflict_nodes],
                    mode="markers",
                    marker=dict(size=20, color="#ef4444", opacity=0.28, allowoverlap=True),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
            fig_map.add_trace(
                go.Scattermap(
                    lat=[n["lat"] for _, n in conflict_nodes],
                    lon=[n["lon"] for _, n in conflict_nodes],
                    mode="markers+text",
                    marker=dict(size=9, color="#ef4444", opacity=1.0, allowoverlap=True),
                    text=["Conflict Territory"],
                    textposition="top right",
                    textfont=dict(family="Inter, sans-serif", size=11, color="#fecaca"),
                    hoverinfo="text",
                    hovertext=[f"<b>{n['name']}</b><br>{n['role']}" for _, n in conflict_nodes],
                    showlegend=False,
                )
            )

            # Subsea Cut Beacon in Gulf of Oman when Incident is Active
            if current_stage != "NORMAL":
                fig_map.add_trace(
                    go.Scattermap(
                        lat=[22.55],
                        lon=[59.65],
                        mode="markers+text",
                        marker=dict(size=26, color="#ef4444", opacity=0.38, allowoverlap=True),
                        text=["SUBSEA CUT (SMW5 & AAE-1)"],
                        textposition="bottom right",
                        textfont=dict(family="JetBrains Mono, monospace", size=10.5, color="#fecaca"),
                        hoverinfo="text",
                        hovertext=["<b>Subsea Fault Point</b><br>SEA-ME-WE-5 & AAE-1 Severed (0 Gbps)"],
                        showlegend=False,
                    )
                )
                fig_map.add_trace(
                    go.Scattermap(
                        lat=[22.55],
                        lon=[59.65],
                        mode="markers",
                        marker=dict(size=10, color="#ffffff", opacity=1.0, allowoverlap=True),
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )

            # Esri / ArcGIS World Imagery Satellite + Reference Boundaries Overlay (No API Key Needed)
            fig_map.update_layout(
                map=dict(
                    style="white-bg",
                    center=dict(lat=25.8, lon=41.5),
                    zoom=3.35,
                    layers=[
                        dict(
                            below="traces",
                            sourcetype="raster",
                            source=[
                                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                            ],
                        ),
                        dict(
                            below="traces",
                            sourcetype="raster",
                            opacity=0.50,
                            source=[
                                "https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
                            ],
                        ),
                    ],
                ),
                autosize=True,
                height=540,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="#060b14",
                hoverlabel=dict(
                    bgcolor="#091222",
                    bordercolor="#38bdf8",
                    font=dict(family="Inter, sans-serif", size=11.5, color="#f8fafc"),
                ),
            )

            st.plotly_chart(
                fig_map,
                width="stretch",
                theme=None,
                config={"responsive": True, "scrollZoom": True, "displayModeBar": True, "displaylogo": False},
            )

            st.markdown(
                """
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; padding-top: 10px; margin-top: 6px; border-top: 1px solid #14233c; font-size: 11px; color: #94a3b8;">
                    <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                        <span><span style="color: #10b981;">&#9679;</span> Operational Subsea</span>
                        <span><span style="color: #38bdf8;">&#9679;</span> Allied Terrestrial</span>
                        <span><span style="color: #22d3ee;">&#9679;</span> ROADM Prioritized</span>
                        <span><span style="color: #f59e0b;">&#9679;</span> Proposed Reroute</span>
                        <span><span style="color: #ef4444;">&#9679;</span> Severed / Blocked</span>
                    </div>
                    <div style="display: flex; gap: 14px; flex-wrap: wrap;">
                        <span><span style="color: #ffffff;">&#9679;</span> UAE Sovereign Core</span>
                        <span><span style="color: #ef4444;">&#9679;</span> Conflict Territory</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_right:
        # Card 1: Network Health Index
        with st.container(border=True):
            st.markdown(
                """
                <div class="sec-head">
                    <span class="sec-title">Network Health Index</span>
                    <span class="sec-tag">LIVE SCORE</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            donut_col = "#10b981" if overall_health_pct >= 85 else ("#22d3ee" if current_stage == "EXECUTED" else "#ef4444")
            subsea_str = "100%" if current_stage == "NORMAL" else ("Protected" if current_stage == "EXECUTED" else "33%")
            osnr_str = "22.9 dB" if current_stage == "NORMAL" else ("24.5 dB" if current_stage == "EXECUTED" else "18.8 dB")

            d_c1, d_c2 = st.columns([1.0, 1.25], vertical_alignment="center")
            with d_c1:
                fig_donut = go.Figure(
                    go.Pie(
                        values=[overall_health_pct, 100 - overall_health_pct],
                        hole=0.76,
                        sort=False,
                        direction="clockwise",
                        marker=dict(colors=[donut_col, "#13223a"], line=dict(width=0)),
                        textinfo="none",
                        hoverinfo="skip",
                    )
                )
                fig_donut.update_layout(
                    autosize=True,
                    showlegend=False,
                    height=158,
                    margin=dict(l=4, r=4, t=4, b=4),
                    paper_bgcolor="rgba(0,0,0,0)",
                    annotations=[
                        dict(
                            text=f"<b>{overall_health_pct}%</b><br><span style='font-size:10px;color:#8da2c0;'>Health</span>",
                            x=0.5,
                            y=0.5,
                            font=dict(family="Inter", size=18, color="#f8fafc"),
                            showarrow=False,
                        )
                    ],
                )
                st.plotly_chart(fig_donut, width="stretch", theme=None, config={"responsive": True, "displayModeBar": False})

            with d_c2:
                st.markdown(
                    f"""
                    <div style="font-size: 11.5px; line-height: 2.25; color: #cbd5e1;">
                        <div style="display:flex; justify-content:space-between;">
                            <span>Subsea Integrity</span><strong class="mono">{subsea_str}</strong>
                        </div>
                        <div style="display:flex; justify-content:space-between;">
                            <span>Landing Stations</span><strong class="mono">100%</strong>
                        </div>
                        <div style="display:flex; justify-content:space-between;">
                            <span>Optical OSNR</span><strong class="mono">{osnr_str}</strong>
                        </div>
                        <div style="display:flex; justify-content:space-between;">
                            <span>Utilization</span><strong class="mono">{utilization_pct}%</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"""
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #13223a;">
                    <div style="background: #0d182c; border: 1px solid #182a49; border-radius: 7px; padding: 8px 10px;">
                        <div style="font-size: 10px; color: #7c93b2;">Core Latency</div>
                        <div class="mono" style="font-size: 13.5px; font-weight: 700; color: #f8fafc; margin-top: 2px;">{avg_latency_ms:.1f} ms</div>
                    </div>
                    <div style="background: #0d182c; border: 1px solid #182a49; border-radius: 7px; padding: 8px 10px;">
                        <div style="font-size: 10px; color: #7c93b2;">Banking Tier-1 SLA</div>
                        <div class="mono" style="font-size: 13.5px; font-weight: 700; color: #34d399; margin-top: 2px;">{banking_sla_str}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Card 2: Regional Corridor Availability
        with st.container(border=True):
            st.markdown(
                """
                <div class="sec-head">
                    <span class="sec-title">Regional Connectivity</span>
                    <span class="sec-tag">BY CORRIDOR</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if current_stage == "NORMAL":
                reg_rows = [
                    ("Arabian Gulf & UAE Core", 99, "#10b981"),
                    ("GCC Allied Backhaul", 96, "#38bdf8"),
                    ("Europe Gateway (Marseille)", 94, "#38bdf8"),
                    ("Asia-Pacific (Mumbai)", 92, "#10b981"),
                ]
            elif current_stage == "EXECUTED":
                reg_rows = [
                    ("Arabian Gulf (GCX Falcon)", 99, "#22d3ee"),
                    ("GCC Allied Backhaul", 94, "#10b981"),
                    ("Europe Sovereign Slice", 78, "#38bdf8"),
                    ("Asia-Pacific Gateway", 64, "#f59e0b"),
                ]
            else:
                reg_rows = [
                    ("Arabian Gulf & UAE Core", 92, "#10b981"),
                    ("GCC Allied Backhaul", 84, "#f59e0b"),
                    ("Europe (SMW5 Disrupted)", 28, "#ef4444"),
                    ("Asia-Pacific (AAE-1 Cut)", 24, "#ef4444"),
                ]

            reg_html = ""
            for r_lbl, r_val, r_col in reg_rows:
                reg_html += f"""
                <div style="margin-bottom: 13px;">
                    <div style="display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 5px;">
                        <span style="color: #cbd5e1;">{r_lbl}</span>
                        <span class="mono" style="color: {r_col}; font-weight: 600;">{r_val}%</span>
                    </div>
                    <div style="background: #13223a; border-radius: 4px; height: 7px; overflow: hidden;">
                        <div style="background: {r_col}; width: {r_val}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
                """
            st.markdown(reg_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Row 3: 3 Balanced Analytical Cards (Performance Trend, Service Priority QoS, Recent Events)
    b1, b2, b3 = st.columns([1.25, 1.2, 1.05], gap="medium")

    with b1:
        with st.container(border=True):
            st.markdown(
                """
                <div class="sec-head">
                    <span class="sec-title">Network Performance Trend</span>
                    <span class="sec-tag">24 HOURS</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            hours = [f"{h:02d}:00" for h in range(0, 24, 2)]
            if current_stage == "NORMAL":
                cap_s = [545, 550, 555, 560, 558, 560, 560, 558, 560, 560, 560, 560]
                lat_s = [35, 34, 34, 33, 35, 34, 34, 35, 34, 34, 34, 34]
            elif current_stage == "EXECUTED":
                cap_s = [555, 560, 560, 555, 560, 560, 560, 180, 180, 180, 180, 180]
                lat_s = [34, 34, 33, 34, 35, 34, 34, 86, 74, 39, 33, 32]
            else:
                cap_s = [555, 560, 560, 555, 560, 560, 560, 180, 180, 180, 180, 180]
                lat_s = [34, 34, 33, 34, 35, 34, 34, 82, 88, 86, 87, 86]

            fig_tr = go.Figure()
            fig_tr.add_trace(
                go.Scatter(
                    x=hours,
                    y=cap_s,
                    mode="lines",
                    name="Capacity (Gbps)",
                    line=dict(color="#38bdf8", width=2.2),
                    fill="tozeroy",
                    fillcolor="rgba(56, 189, 248, 0.08)",
                )
            )
            fig_tr.add_trace(
                go.Scatter(
                    x=hours,
                    y=lat_s,
                    mode="lines",
                    name="Latency (ms)",
                    line=dict(color="#f59e0b", width=2.0),
                )
            )
            fig_tr.update_layout(
                autosize=True,
                height=195,
                margin=dict(l=0, r=6, t=6, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(family="Inter", size=10, color="#94a3b8"),
                ),
                xaxis=dict(showgrid=False, tickfont=dict(family="JetBrains Mono", size=9, color="#64748b")),
                yaxis=dict(showgrid=True, gridcolor="#14233c", tickfont=dict(family="JetBrains Mono", size=9, color="#64748b")),
            )
            st.plotly_chart(fig_tr, width="stretch", theme=None, config={"responsive": True, "displayModeBar": False})

    with b2:
        with st.container(border=True):
            st.markdown(
                """
                <div class="sec-head">
                    <span class="sec-title">Service Priority &amp; QoS Allocation</span>
                    <span class="sec-tag">SLA TIERS</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            qos_html = ""
            for t_info in demands.values():
                dem = t_info["demand_gbps"]
                alloc = t_info["allocated_gbps"]
                pct = min(100.0, (alloc / max(dem, 1.0)) * 100.0)
                t_st = t_info["status"]
                if "PROTECTED" in t_st or "GUARANTEED" in t_st or pct >= 99.0:
                    b_col = "#22d3ee" if t_info["priority_level"] == 1 else "#10b981"
                    b_cls = "b-cyan" if t_info["priority_level"] == 1 else "b-ok"
                elif pct >= 25.0:
                    b_col = "#f59e0b"
                    b_cls = "b-warn"
                else:
                    b_col = "#ef4444"
                    b_cls = "b-crit"

                qos_html += f"""
                <div style="margin-bottom: 13px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-size: 11.5px; font-weight: 600; color: #f1f5f9;">P{t_info['priority_level']} — {t_info['name']}</span>
                        <span class="badge-sm {b_cls}">{alloc:.0f} / {dem:.0f} Gbps</span>
                    </div>
                    <div style="background: #13223a; border-radius: 4px; height: 7px; overflow: hidden;">
                        <div style="background: {b_col}; width: {max(pct, 4.0):.1f}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
                """
            st.markdown(qos_html, unsafe_allow_html=True)

    with b3:
        with st.container(border=True):
            st.markdown(
                """
                <div class="sec-head">
                    <span class="sec-title">Recent Network Events</span>
                    <span class="sec-tag">LIVE LOG</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            ev_html = ""
            for ev in list(reversed(orch.audit_log))[:4]:
                act = ev["action"]
                dot_c = (
                    "#ef4444"
                    if ("ALARM" in act or "BLOCK" in act or "REJECT" in act)
                    else ("#22d3ee" if ("ROADM" in act or "SLICING" in act or "APPROVED" in act) else "#38bdf8")
                )
                ts_short = ev["timestamp"].split(" ")[-1][:8]
                msg_short = ev["details"] if len(ev["details"]) <= 58 else ev["details"][:55] + "..."
                ev_html += f"""
                <div style="display: flex; gap: 9px; align-items: flex-start; margin-bottom: 10px; font-size: 11.5px; line-height: 1.45;">
                    <span style="color: {dot_c}; margin-top: 1px;">&#9679;</span>
                    <div>
                        <span class="mono" style="color: #64748b; font-size: 10.5px;">{ts_short}</span>
                        <span style="color: #cbd5e1; margin-left: 6px;">{msg_short}</span>
                    </div>
                </div>
                """
            st.markdown(ev_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Row 4: Full-Width Clean Cable Status Table
    with st.container(border=True):
        st.markdown(
            """
            <div class="sec-head">
                <span class="sec-title">Submarine &amp; Terrestrial Corridor Telemetry</span>
                <span class="sec-tag">OPTICAL LAYER</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        t_rows = ""
        for c in cables.values():
            st_c = c["status"]
            b_cls = (
                "b-ok"
                if st_c == "OPERATIONAL"
                else ("b-cyan" if st_c == "ROADM_PRIORITIZED" else ("b-warn" if st_c == "PROPOSED_BY_OPTICAL" else ("b-crit" if st_c in ["SEVERELY_CUT", "POLICY_BLOCKED"] else "b-muted")))
            )
            t_rows += (
                f"<tr>"
                f"<td style='font-weight:600;color:#f1f5f9;'>{c['name']}</td>"
                f"<td>{c['type']}</td>"
                f"<td class='mono'>{c['total_capacity_gbps']:.0f} Gbps</td>"
                f"<td class='mono'>{c['allocated_gbps']:.0f} Gbps</td>"
                f"<td class='mono'>{c['latency_ms']} ms</td>"
                f"<td class='mono'>{c['osnr_db']} dB</td>"
                f"<td style='color:#94a3b8;'>{c['geopolitical_risk']}</td>"
                f"<td><span class='badge-sm {b_cls}'>{st_c}</span></td>"
                f"</tr>"
            )

        st.markdown(
            f"""
            <table class="noc-table">
                <thead>
                    <tr>
                        <th>Corridor Name</th>
                        <th>Medium</th>
                        <th>Total Capacity</th>
                        <th>Active Load</th>
                        <th>Latency</th>
                        <th>OSNR</th>
                        <th>Jurisdiction Profile</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>{t_rows}</tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# PAGE 2: AI AGENT MONITORING (Full Agent Paragraphs with Collapsible Hide/Show)
# ==============================================================================
elif st.session_state.current_page == "AI Agent Monitoring":
    top_title_col, top_toggle_col = st.columns([2.6, 1.0], vertical_alignment="center")
    with top_title_col:
        st.markdown(
            """
            <div style="margin-bottom: 6px;">
                <span style="font-size: 15px; font-weight: 700; color: #f8fafc;">Multi-Agent AI Monitoring &amp; Deliberation Process</span>
                <span style="font-size: 12px; color: #64748b; margin-left: 10px;">Click any section or use the toggle to show/hide full agent explanations</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_toggle_col:
        show_full_paragraphs = st.toggle("Show Full Agent Paragraphs", value=False, key="toggle_agent_paragraphs")

    stage_rank = {
        "NORMAL": 0,
        "DISRUPTED": 1,
        "OPTICAL_PROPOSED": 2,
        "POLICY_BLOCKED": 3,
        "AWAITING_HUMAN": 5,
        "EXECUTED": 6,
        "REJECTED": 6,
    }
    cur_r = stage_rank.get(current_stage, 0)

    # Progressive Stage Bar: Hidden at NORMAL, each stage appears only when reached (No "Step" prefix)
    if cur_r > 0:
        all_stages = [
            (1, "Fault Detected"),
            (2, "Optical Proposal"),
            (3, "Policy Hold & Block"),
            (4, "Coordinator Synthesis"),
            (5, "Human Authorization Gate"),
            (6, "ROADM & QoS Executed" if current_stage != "REJECTED" else "Quarantine Hold"),
        ]
        reached_stages = [(r_id, lbl_s) for r_id, lbl_s in all_stages if cur_r >= r_id]
        p_cols = st.columns(len(reached_stages), gap="small")
        for col_idx, (r_id, lbl_s) in enumerate(reached_stages):
            with p_cols[col_idx]:
                is_latest = (r_id == cur_r) and current_stage not in ["EXECUTED", "REJECTED"]
                accent_c = (
                    "#ef4444"
                    if (r_id == 6 and current_stage == "REJECTED")
                    else ("#22d3ee" if is_latest else "#10b981")
                )
                badge_txt = "ACTIVE" if is_latest else "COMPLETED"
                st.markdown(
                    f"""
                    <div style="background: #0a1324; border: 1px solid {accent_c}; border-radius: 9px; padding: 10px 12px; display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                        <span style="font-size: 12px; font-weight: 600; color: #f8fafc;">{lbl_s}</span>
                        <span class="mono" style="font-size: 9.5px; color: {accent_c}; font-weight: 600;">{badge_txt}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 4 Specialized Agent Cards with Collapsible Full Role Paragraphs
    ag1, ag2, ag3, ag4 = st.columns(4, gap="medium")
    open_attr = "open" if show_full_paragraphs else ""

    agent_summary = [
        (
            ag1,
            "Optical Network Agent",
            "DWDM / ROADM",
            "WSS LOCKED" if current_stage == "EXECUTED" else ("PROPOSED" if orch.last_optical_proposal else "STANDBY"),
            "#38bdf8",
            "Proposal",
            "Northern Terrestrial" if orch.last_optical_proposal else "Monitoring Subsea",
            "ROADM",
            "λ_1, λ_2 Locked (38.5 ms)" if current_stage == "EXECUTED" else "Standard 64-Ch",
            (
                "Monitors physical-layer DWDM spectrum, Optical Signal-to-Noise Ratio (OSNR), Bit Error Rate (BER), "
                "and Loss of Signal (LOS) alarms across subsea landing stations. Automatically calculates high-capacity "
                "physical bypass routes upon fiber cuts and executes ROADM Wavelength Selective Switch (WSS) matrix "
                "reconfiguration for sub-50ms optical protection."
            ),
        ),
        (
            ag2,
            "Policy & Compliance Agent",
            "LEGAL FIREWALL",
            "BLOCKED" if orch.last_policy_verdict else "STANDBY",
            "#ef4444" if orch.last_policy_verdict else "#64748b",
            "Verdict",
            "HOLD & REJECT" if orch.last_policy_verdict else "Compliant",
            "Basis",
            "TDRA 14.3 & CBUAE 4.2.1",
            (
                "Operates as the autonomous national security and regulatory compliance firewall. Intercepts every "
                "optical reroute proposal before physical switching occurs, places non-compliant routes on immediate HOLD, "
                "audits foreign transit jurisdictions against UAE TDRA Article 14.3 and CBUAE CIIP Policy Section 4.2.1, "
                "and escalates blocked proposals to the Decision Coordinator."
            ),
        ),
        (
            ag3,
            "Decision Coordinator Agent",
            "STRATEGIC ARBITER",
            "DISPATCHED" if current_stage == "EXECUTED" else ("READY" if orch.last_coordinator_recommendation else "STANDBY"),
            "#22d3ee" if orch.last_coordinator_recommendation else "#64748b",
            "Route",
            "GCX Falcon Subsea" if orch.last_coordinator_recommendation else "Nominal",
            "Gate",
            current_stage.replace("_", " "),
            (
                "Resolves multi-objective deadlocks when physical bandwidth optimization conflicts with sovereign "
                "data-residency laws. Synthesizes compliant alternatives that retain traffic on surviving subsea cables "
                "using ROADM optical wavelength priority and QoS resource allocation, presents recommendations to the "
                "Human Operator, and dispatches approved execution orders."
            ),
        ),
        (
            ag4,
            "Resource Allocation Agent",
            "QOS SCHEDULER",
            "ACTIVE" if current_stage == "EXECUTED" else "STANDBY",
            "#10b981" if current_stage == "EXECUTED" else "#64748b",
            "Banking P1",
            "50 Gbps (100% SLA)",
            "Public P3",
            "10 Gbps Throttled" if current_stage == "EXECUTED" else "220 Gbps Nominal",
            (
                "Enforces deterministic Quality of Service (QoS) bandwidth slicing and egress interface rate policing "
                "when total submarine capacity drops. Guarantees 100% throughput (50.0 Gbps, zero packet loss) in Queue-0 "
                "for Tier-1 CBUAE RTGS and SWIFT financial settlements while throttling best-effort Tier-3 public streaming."
            ),
        ),
    ]

    for col_a, name_a, role_a, badge_a, col_hex, k1_l, k1_v, k2_l, k2_v, full_desc in agent_summary:
        with col_a:
            st.markdown(
                f"""
                <div style="background: linear-gradient(180deg, #0b1425 0%, #08101e 100%); border: 1px solid #182946; border-top: 3px solid {col_hex}; border-radius: 12px; padding: 15px 16px;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span class="mono" style="font-size: 9.5px; color: #7c93b2;">{role_a}</span>
                            <span class="mono" style="font-size: 9.5px; color: {col_hex}; border: 1px solid {col_hex}; padding: 1px 6px; border-radius: 4px;">{badge_a}</span>
                        </div>
                        <div style="font-size: 13.5px; font-weight: 700; color: #f8fafc; margin-top: 8px; margin-bottom: 10px;">{name_a}</div>
                    </div>
                    <div style="border-top: 1px solid #14233c; padding-top: 9px; font-size: 11.5px; line-height: 1.7;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #7c93b2;">{k1_l}</span>
                            <strong style="color: #e2e8f0;">{k1_v}</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #7c93b2;">{k2_l}</span>
                            <strong class="mono" style="color: #cbd5e1; font-size: 10.5px;">{k2_v}</strong>
                        </div>
                    </div>
                    <details class="agent-drawer" {open_attr}>
                        <summary>Agent Role &amp; Responsibilities</summary>
                        <div class="drawer-body">{full_desc}</div>
                    </details>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Progressive Collapsible Deliberation Narrative: Appears ONLY as each stage occurs (No "Step" prefix)
    if current_stage == "NORMAL":
        with st.container(border=True):
            st.markdown(
                """
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; font-size: 12.5px; color: #94a3b8;">
                    <span>All submarine optical corridors (<span class="mono">SEA-ME-WE-5</span>, <span class="mono">AAE-1</span>, <span class="mono">GCX Falcon</span>) are operating normally. Live deliberation stages will appear here automatically once an incident is triggered.</span>
                    <span class="badge-sm b-ok">STANDBY</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        with st.container(border=True):
            st.markdown(
                """
                <div class="sec-head">
                    <div>
                        <span class="sec-title">Live Multi-Agent Deliberation Narrative</span>
                        <span class="sec-sub">Click any header below to hide or expand its full operational report</span>
                    </div>
                    <span class="sec-tag">PROGRESSIVE LOG</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 1. Fault Detection (Appears when incident starts)
            with st.expander(
                "Subsea Fault Detection — SEA-ME-WE-5 & AAE-1 Severed",
                expanded=show_full_paragraphs,
            ):
                st.markdown(
                    """
                    <div style="font-size: 12.5px; line-height: 1.7; color: #cbd5e1;">
                        Optical telemetry transponders at Fujairah Landing Station detected simultaneous Loss of Signal (LOS) across
                        <strong>SEA-ME-WE-5</strong> (200.0 Gbps) and <strong>AAE-1</strong> (180.0 Gbps) in the Gulf of Oman / Red Sea corridor,
                        reducing total international capacity by <strong>380.0 Gbps</strong> and triggering autonomous multi-agent recovery.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # 2. Optical Network Agent (Appears ONLY when Optical Proposal has executed)
            if orch.last_optical_proposal:
                prop = orch.last_optical_proposal
                with st.expander(
                    "Optical Network Agent — Terrestrial Reroute Proposal (150 Gbps, 64 ms)",
                    expanded=show_full_paragraphs,
                ):
                    st.markdown(
                        f"""
                        <div style="font-size: 12.5px; line-height: 1.7; color: #cbd5e1;">
                            <p style="margin: 0 0 8px 0;">
                                <strong style="color: #38bdf8;">Proposed Action ({prop['action']}):</strong> Optimizing strictly for physical-layer throughput and lowest attenuation, the Optical Network Agent proposed shifting traffic overland via <strong>{prop['proposed_cable_name']}</strong> (<span class="mono">{' -> '.join(prop['proposed_path'])}</span>), offering <strong>150.0 Gbps</strong> free capacity, <strong>64.0 ms</strong> optical latency, <strong>19.5 dB</strong> OSNR, and <span class="mono">3.1e-11</span> BER.
                            </p>
                            <p style="margin: 0;">
                                <strong style="color: #38bdf8;">Technical Rationale:</strong> {prop['technical_justification']} Forwarded to the Policy &amp; Compliance Agent for pre-execution verification.
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # 3. Policy & Compliance Agent (Appears ONLY when Policy Interception has executed)
            if orch.last_policy_verdict:
                verdict = orch.last_policy_verdict
                viol_html = "".join(
                    f"<li style='margin-bottom: 6px;'><strong style='color: #fca5a5;'>{v['framework']} — {v['article']} ({v['ruling']}):</strong> {v['legal_text']}</li>"
                    for v in verdict.get("violations_found", [])
                )
                with st.expander(
                    "Policy & Compliance Agent — Regulatory Hold & Block",
                    expanded=show_full_paragraphs,
                ):
                    st.markdown(
                        f"""
                        <div style="font-size: 12.5px; line-height: 1.7; color: #cbd5e1;">
                            <p style="margin: 0 0 8px 0;">
                                <strong style="color: #f87171;">Interception &amp; Mandatory Hold ({verdict['interception_status']}):</strong>
                                The Policy &amp; Compliance Agent intercepted the Optical Network Agent's terrestrial reroute command and placed switching execution on immediate hold. {verdict['reason']}
                            </p>
                            <ul style="margin: 6px 0 10px 18px; color: #e2e8f0;">
                                {viol_html}
                            </ul>
                            <p style="margin: 0;">
                                <strong style="color: #f87171;">Escalation to Decision Coordinator:</strong> {verdict['escalation_message']}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # 4. Decision Coordinator Agent (Appears ONLY when Coordinator Synthesis has executed)
            if orch.last_coordinator_recommendation:
                rec = orch.last_coordinator_recommendation
                sol = rec["proposed_solution"]
                sla = rec["sla_and_impact_projection"]
                with st.expander(
                    "Decision Coordinator Agent — Compliant Subsea & ROADM Synthesis",
                    expanded=show_full_paragraphs,
                ):
                    st.markdown(
                        f"""
                        <div style="font-size: 12.5px; line-height: 1.7; color: #cbd5e1;">
                            <p style="margin: 0 0 8px 0;">
                                <strong style="color: #22d3ee;">Strategic Multi-Domain Rationale:</strong> {rec['strategic_rationale']}
                            </p>
                            <p style="margin: 0 0 8px 0;">
                                <strong style="color: #22d3ee;">Synthesized Restoration Architecture:</strong> Retain sovereign data transmission on <strong>{sol['primary_cable']}</strong> backed by <strong>{sol['backup_allied_cable']}</strong>. Concurrently activate <strong>{sol['optical_mechanism']}</strong> at the optical layer and <strong>{sol['resource_mechanism']}</strong> at the packet scheduling layer.
                            </p>
                            <p style="margin: 0;">
                                <strong style="color: #22d3ee;">Projected Service Outcome &amp; Human Gate Handoff:</strong> Tier-1 Banking: <span class="mono">{sla['Tier1_Banking_Fulfillment']}</span> | Tier-2 Cloud: <span class="mono">{sla['Tier2_Enterprise_Cloud']}</span> | Tier-3 Public: <span class="mono">{sla['Tier3_Public_Internet']}</span> | Subsea Latency: <span class="mono">{sla['expected_latency_ms']} ms</span>. Submitted to the Human Operator for executive authorization.
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # 5. Post-Decision Execution (Appears ONLY after Human Operator Approves or Rejects)
            if current_stage == "EXECUTED":
                with st.expander(
                    "Authorized Execution — ROADM WSS Reconfigured (38.5 ms) & QoS Bandwidth Slicing Active",
                    expanded=show_full_paragraphs,
                ):
                    st.markdown(
                        """
                        <div style="font-size: 12.5px; line-height: 1.7; color: #cbd5e1;">
                            <p style="margin: 0 0 8px 0;">
                                <strong style="color: #34d399;">Optical Network Agent Command Execution:</strong> Upon receiving Human Operator authorization (<span class="mono">NOC_COMMANDER_01</span>), the Optical Network Agent reconfigured the ROADM Wavelength Selective Switch (WSS) matrix on <strong>GCX Falcon Subsea Loop</strong> in <strong>38.5 ms</strong> (compliant with ITU-T G.808.1 sub-50ms protection switching and ITU-T G.872). Dedicated optical channels <span class="mono">λ_1 (1550.12 nm)</span> and <span class="mono">λ_2 (1550.92 nm)</span> were locked exclusively for CBUAE RTGS and SWIFT banking traffic (<span class="mono">-2.4 dBm</span> optical power, <span class="mono">0.8e-12</span> error-free BER).
                            </p>
                            <p style="margin: 0;">
                                <strong style="color: #34d399;">Resource Allocation Agent Command Execution:</strong> Deterministic strict-priority QoS slicing was committed across the 80.0 Gbps surviving sovereign slice: <strong>50.0 Gbps (100% SLA)</strong> guaranteed to Tier-1 CBUAE Banking, <strong>20.0 Gbps</strong> allocated to Tier-2 Government &amp; Enterprise Cloud core operations, and Tier-3 Public Internet/OTT video rate-policed to <strong>10.0 Gbps</strong>.
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            elif current_stage == "REJECTED":
                with st.expander(
                    "Manual Quarantine Hold — Operator Rejected Automated Mitigation",
                    expanded=show_full_paragraphs,
                ):
                    st.markdown(
                        """
                        <div style="font-size: 12.5px; line-height: 1.65; color: #fca5a5;">
                            The Human Operator rejected the automated mitigation proposal. Both the Optical Network Agent and Resource Allocation Agent remain held in fail-safe manual quarantine awaiting manual NOC override.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    c_trace, c_roadm = st.columns([1.25, 1.0], gap="medium")

    with c_trace:
        with st.container(border=True):
            st.markdown(
                """
                <div class="sec-head">
                    <span class="sec-title">Inter-Agent Decision Handoff</span>
                    <span class="sec-tag">SUMMARY</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            handoff_rows = []
            if orch.last_optical_proposal:
                handoff_rows.append(("Optical Network Agent", "PROPOSED", "b-warn", "Reroute via Northern Terrestrial (150 Gbps, 64 ms)"))
            if orch.last_policy_verdict:
                handoff_rows.append(("Policy & Compliance", "BLOCKED", "b-crit", "Blocked: conflict transit violates TDRA 14.3 & CBUAE 4.2.1"))
            if orch.last_coordinator_recommendation:
                handoff_rows.append(("Decision Coordinator", "RECOMMENDED", "b-cyan", "Retain GCX Falcon subsea + ROADM priority + QoS slicing"))
            if current_stage == "EXECUTED":
                handoff_rows.append(("Execution Dispatch", "COMMITTED", "b-ok", "Operator approved; Optical ROADM & QoS active"))
            elif current_stage == "REJECTED":
                handoff_rows.append(("Execution Dispatch", "REJECTED", "b-crit", "Operator rejected; system in manual hold"))

            if handoff_rows:
                h_html = ""
                for ag_n, st_t, b_c, msg_t in handoff_rows:
                    h_html += (
                        f"<tr>"
                        f"<td style='font-weight:600;color:#f1f5f9;'>{ag_n}</td>"
                        f"<td><span class='badge-sm {b_c}'>{st_t}</span></td>"
                        f"<td style='color:#cbd5e1;'>{msg_t}</td>"
                        f"</tr>"
                    )
                st.markdown(
                    f"""
                    <table class="noc-table">
                        <thead>
                            <tr>
                                <th>Agent</th>
                                <th>Verdict</th>
                                <th>Outcome</th>
                            </tr>
                        </thead>
                        <tbody>{h_html}</tbody>
                    </table>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div style="padding: 16px 4px; font-size: 12px; color: #64748b;">
                        No inter-agent handoffs recorded yet. Handoff entries appear dynamically as each agent executes.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with c_roadm:
        with st.container(border=True):
            st.markdown(
                """
                <div class="sec-head">
                    <span class="sec-title">ROADM Wavelength &amp; QoS Matrix</span>
                    <span class="sec-tag">ITU-T G.808.1</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            active_lock = current_stage == "EXECUTED"
            st.markdown(
                f"""
                <table class="noc-table">
                    <thead>
                        <tr>
                            <th>Channel</th>
                            <th>Service Tier</th>
                            <th>Slice</th>
                            <th>State</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="mono">λ_1 (1550.12nm)</td>
                            <td>CBUAE RTGS Banking</td>
                            <td class="mono">50 Gbps</td>
                            <td><span class="badge-sm {'b-cyan' if active_lock else 'b-ok'}">{'LOCKED' if active_lock else 'NOMINAL'}</span></td>
                        </tr>
                        <tr>
                            <td class="mono">λ_2 (1550.92nm)</td>
                            <td>SWIFT Settlement</td>
                            <td class="mono">Dedicated</td>
                            <td><span class="badge-sm {'b-cyan' if active_lock else 'b-ok'}">{'LOCKED' if active_lock else 'NOMINAL'}</span></td>
                        </tr>
                        <tr>
                            <td class="mono">λ_3 (1551.72nm)</td>
                            <td>Gov &amp; Cloud Core</td>
                            <td class="mono">{'20 Gbps' if active_lock else '80 Gbps'}</td>
                            <td><span class="badge-sm b-ok">{'SHARED' if active_lock else 'NOMINAL'}</span></td>
                        </tr>
                        <tr>
                            <td class="mono">λ_4 (1552.52nm)</td>
                            <td>Public Internet</td>
                            <td class="mono">{'10 Gbps' if active_lock else '220 Gbps'}</td>
                            <td><span class="badge-sm {'b-warn' if active_lock else 'b-ok'}">{'THROTTLED' if active_lock else 'NOMINAL'}</span></td>
                        </tr>
                    </tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )


# ==============================================================================
# PAGE 3: DECISION & RECOMMENDATION
# ==============================================================================
elif st.session_state.current_page == "Decision & Recommendation":
    d_col1, d_col2 = st.columns(2, gap="medium")

    with d_col1:
        with st.container(border=True):
            st.markdown(
                """
                <div class="sec-head">
                    <span class="sec-title" style="color: #f87171;">Option A: Northern Terrestrial Reroute</span>
                    <span class="badge-sm b-crit">BLOCKED BY POLICY AGENT</span>
                </div>
                <table class="noc-table" style="margin-bottom: 12px;">
                    <tbody>
                        <tr><td style="color:#7c93b2;">Proposed By</td><td>Optical Network Agent (Shortest Path)</td></tr>
                        <tr><td style="color:#7c93b2;">Corridor Path</td><td class="mono">Dubai -> Conflict State -> Marseille</td></tr>
                        <tr><td style="color:#7c93b2;">Capacity / Latency</td><td class="mono">150.0 Gbps &nbsp;|&nbsp; 64.0 ms</td></tr>
                        <tr><td style="color:#7c93b2;">Sovereignty Risk</td><td style="color:#f87171; font-weight:600;">CRITICAL — Hostile Jurisdiction Transit</td></tr>
                        <tr><td style="color:#7c93b2;">Legal Ruling</td><td>Violates UAE TDRA Art. 14.3 &amp; CBUAE CIIP 4.2.1</td></tr>
                    </tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )

    with d_col2:
        with st.container(border=True):
            st.markdown(
                """
                <div class="sec-head">
                    <span class="sec-title" style="color: #34d399;">Option B: Surviving Subsea + ROADM + QoS</span>
                    <span class="badge-sm b-ok">COORDINATOR RECOMMENDED</span>
                </div>
                <table class="noc-table" style="margin-bottom: 12px;">
                    <tbody>
                        <tr><td style="color:#7c93b2;">Proposed By</td><td>Decision Coordinator Agent</td></tr>
                        <tr><td style="color:#7c93b2;">Corridor Path</td><td class="mono">GCX Falcon Subsea + Allied GCC Backhaul</td></tr>
                        <tr><td style="color:#7c93b2;">Protected Slice</td><td class="mono">80.0 Gbps &nbsp;|&nbsp; 32.4 ms (OSNR 24.5 dB)</td></tr>
                        <tr><td style="color:#7c93b2;">Sovereignty Risk</td><td style="color:#34d399; font-weight:600;">NONE — Sovereign &amp; Allied Waters</td></tr>
                        <tr><td style="color:#7c93b2;">Mitigation Action</td><td>ROADM (λ_1, λ_2) + 100% Banking QoS Guarantee</td></tr>
                    </tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        gate_st = (
            ("AWAITING OPERATOR DECISION", "b-warn")
            if current_stage == "AWAITING_HUMAN"
            else (("APPROVED & DISPATCHED", "b-ok") if current_stage == "EXECUTED" else (
                ("REJECTED — MANUAL HOLD", "b-crit") if current_stage == "REJECTED" else ("SIMULATION STANDBY", "b-muted")
            ))
        )
        st.markdown(
            f"""
            <div class="sec-head">
                <div>
                    <span class="sec-title">Human-in-the-Loop Executive Authorization Gate</span>
                    <span class="sec-sub">Dispatches Commands to Optical Network Agent &amp; Resource Allocation Agent</span>
                </div>
                <span class="badge-sm {gate_st[1]}">{gate_st[0]}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        rec_prompt = (
            orch.last_coordinator_recommendation["human_decision_prompt"]
            if orch.last_coordinator_recommendation
            else (
                "Recommended Action Plan:\n"
                "1. Retain traffic on surviving subsea optical fiber (GCX Falcon Subsea Loop).\n"
                "2. Prioritize optical transmission in ROADM (lock wavelengths λ_1 & λ_2 in <50 ms).\n"
                "3. Prioritize CBUAE Banking (50 Gbps, 100% SLA) in Resource Allocation; throttle Tier-3 to 10 Gbps."
            )
        )
        st.markdown(
            f"""
            <div style="background: #0c172a; border: 1px solid #1a2e4f; border-radius: 8px; padding: 14px 16px; margin-bottom: 14px; font-size: 12.5px; line-height: 1.7; color: #e2e8f0;">
                {"<br>".join(rec_prompt.splitlines())}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if current_stage == "AWAITING_HUMAN":
            btn_a, btn_r = st.columns(2, gap="medium")
            with btn_a:
                if st.button(
                    "Approve & Dispatch to Optical and Resource Agents",
                    type="primary",
                    width="stretch",
                ):
                    orch.submit_human_decision(approved=True, operator_id="NOC_COMMANDER_01")
                    st.rerun()
            with btn_r:
                if st.button("Reject Recommendation & Hold", width="stretch"):
                    orch.submit_human_decision(approved=False, operator_id="NOC_COMMANDER_01")
                    st.rerun()
        elif current_stage == "EXECUTED":
            st.markdown(
                """
                <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.38); border-radius: 8px; padding: 12px 16px; font-size: 12.5px; color: #a7f3d0;">
                    <strong>DISPATCH COMPLETE:</strong> Commands executed by <strong>Optical Network Agent</strong> (ROADM WSS λ_1, λ_2 locked in 38.5 ms) and <strong>Resource Allocation Agent</strong> (50 Gbps Banking guaranteed; Tier-3 throttled to 10 Gbps).
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            c_info, c_run = st.columns([2.4, 1.0], vertical_alignment="center")
            with c_info:
                st.markdown(
                    '<div style="font-size: 12px; color: #94a3b8;">Run the cable cut simulation and agent deliberation to activate human decision buttons.</div>',
                    unsafe_allow_html=True,
                )
            with c_run:
                if st.button("Simulate & Deliberate Now", type="primary", width="stretch"):
                    if orch.workflow_stage == "NORMAL":
                        orch.trigger_subsea_disruption()
                    if orch.workflow_stage == "DISRUPTED":
                        orch.run_optical_proposal()
                    if orch.workflow_stage == "OPTICAL_PROPOSED":
                        orch.run_policy_interception()
                    if orch.workflow_stage == "POLICY_BLOCKED":
                        orch.run_coordinator_synthesis()
                    st.rerun()


# ==============================================================================
# PAGE 4: KNOWLEDGE BASE EVIDENCE
# ==============================================================================
elif st.session_state.current_page == "Knowledge Base Evidence":
    kb_chunks, faiss_ntotal = load_kb_metadata()
    doc_inventory = scan_document_inventory()

    kb1, kb2, kb3, kb4 = st.columns(4, gap="medium")
    for col_kb, l_kb, v_kb, s_kb in [
        (kb1, "Regulatory Corpora", "4", "CBUAE, TDRA, ITU-T, ICPC"),
        (kb2, "Official Documents", str(len(doc_inventory)), "Indexed PDF Standards"),
        (kb3, "Vector Chunks", f"{faiss_ntotal:,}", "FAISS 384-Dim Database"),
        (kb4, "Local LLM Engine", "Llama-3.2-1B", f"{N_CTX:,} Ctx · Offline GGUF"),
    ]:
        with col_kb:
            st.markdown(
                f"""
                <div class="kpi-card" style="height: 92px;">
                    <div class="kpi-label">{l_kb}</div>
                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <div class="kpi-val" style="font-size:22px;">{v_kb}</div>
                        <div class="kpi-sub c-neu">{s_kb}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    presets = [
        "Why is routing UAE telecommunications traffic through a conflict state prohibited under TDRA and CBUAE rules?",
        "How do ITU-T G.872 and G.808.1 support ROADM optical wavelength protection during a submarine cable cut?",
        "What resilience obligations apply to Critical Information Infrastructure financial systems in the UAE?",
    ]
    if "kb_custom_prompt" not in st.session_state:
        st.session_state.kb_custom_prompt = presets[0]

    def _sync_kb_preset() -> None:
        st.session_state.kb_custom_prompt = st.session_state.kb_preset_select

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="sec-head">
                <div>
                    <span class="sec-title">Local Air-Gapped RAG &amp; LLM Verification</span>
                    <span class="sec-sub">Full Untruncated Regulatory &amp; Optical Standard Synthesis ({N_CTX:,}-Token Context Window)</span>
                </div>
                <span class="sec-tag">OFFLINE CPU · GGUF</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        q_col1, q_col2 = st.columns([1.0, 1.35], gap="medium")
        with q_col1:
            st.selectbox(
                "Preset Verification Scenario",
                presets,
                index=0,
                key="kb_preset_select",
                on_change=_sync_kb_preset,
            )
        with q_col2:
            q_input = st.text_input(
                "Custom or Selected Prompt",
                key="kb_custom_prompt",
            )

        act_col1, act_col2, _ = st.columns([0.28, 0.18, 0.54], gap="small")
        with act_col1:
            run_kb_btn = st.button("Run Local RAG & LLM Query", type="primary", width="stretch")
        with act_col2:
            if st.session_state.kb_query_result is not None:
                if st.button("Clear Output", width="stretch"):
                    st.session_state.kb_query_result = None
                    st.rerun()

        if run_kb_btn and q_input.strip():
            matched = retrieve_relevant_chunks(q_input, kb_chunks, top_k=4)
            ctx_str = "\n\n".join(
                f"[{i+1}] Source: {c.get('source', 'Standard')} ({c.get('category', 'Corpus')})\n{c.get('text', '').strip()}"
                for i, c in enumerate(matched)
            )
            with st.spinner("Synthesizing complete response with local Llama-3.2-1B-Instruct..."):
                llm = load_local_llm(N_CTX)
                if llm is not None:
                    resp = llm.create_chat_completion(
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are an authoritative UAE Telecom & Regulatory Compliance Specialist. "
                                    "Answer directly in formal English based on the provided UAE TDRA, CBUAE CIIP, "
                                    "ITU-T optical networking standards, and ICPC submarine cable best practices. "
                                    "Structure your analysis clearly in 2 to 4 complete paragraphs or concise bullet points, "
                                    "without meta-introductions, and ensure every point ends with a complete sentence."
                                ),
                            },
                            {
                                "role": "user",
                                "content": f"Reference Evidence:\n{ctx_str}\n\nVerification Question: {q_input.strip()}",
                            },
                        ],
                        max_tokens=900,
                        temperature=0.15,
                    )
                    choice = resp["choices"][0]
                    ans = choice["message"]["content"].strip()
                    finish_reason = choice.get("finish_reason", "stop")
                    comp_tokens = resp.get("usage", {}).get("completion_tokens", len(ans.split()))
                    st.session_state.kb_query_result = {
                        "query": q_input.strip(),
                        "answer": ans,
                        "finish_reason": finish_reason,
                        "completion_tokens": comp_tokens,
                        "matched": matched,
                    }
                else:
                    st.warning("Local GGUF model file was not found in the configured models directory.")

        kb_res = st.session_state.kb_query_result
        if kb_res is not None:
            is_complete = kb_res.get("finish_reason") == "stop"
            status_badge_cls = "b-ok" if is_complete else "b-warn"
            status_badge_txt = "COMPLETE SYNTHESIS" if is_complete else "MAX TOKEN LIMIT REACHED"

            with st.container(border=True, key="llm_synthesis_box"):
                st.markdown(
                    f"""
                    <div class="llm-meta-bar">
                        <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                            <span class="mono" style="font-size:10.5px; font-weight:600; color:#22d3ee; letter-spacing:0.04em;">LOCAL LLM SYNTHESIS</span>
                            <span style="font-size:11.5px; color:#94a3b8;">Query: <strong style="color:#cbd5e1;">{html.escape(kb_res['query'])}</strong></span>
                        </div>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span class="badge-sm {status_badge_cls}">{status_badge_txt}</span>
                            <span class="sec-tag">{kb_res['completion_tokens']} TOKENS</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(format_llm_markdown(kb_res["answer"]))

            matched_list = kb_res.get("matched", [])
            if matched_list:
                st.markdown(
                    f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; margin: 14px 0 8px 0;">
                        <span style="font-size:12.5px; font-weight:600; color:#cbd5e1;">Retrieved Supporting Corpus Passages (Full Untruncated Excerpts)</span>
                        <span class="sec-tag">{len(matched_list)} PASSAGES RETRIEVED</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                cat_labels = {
                    "CBUAE_Banking": "CBUAE Banking Regulation",
                    "TDRA_Telecom": "UAE TDRA Telecom Policy",
                    "ITU_T_Optical": "ITU-T Optical Standard",
                    "ICPC_Submarine": "ICPC Submarine Best Practice",
                }
                for idx_m, m_ch in enumerate(matched_list, start=1):
                    src_name = m_ch.get("source", "Document")
                    cat_raw = m_ch.get("category", "Corpus")
                    cat_disp = cat_labels.get(cat_raw, cat_raw)
                    chunk_no = m_ch.get("chunk_id", idx_m)
                    full_passage = re.sub(r"\s+\n", "\n", m_ch.get("text", "").strip())
                    with st.expander(f"[{idx_m}] {src_name}  —  {cat_disp} (Chunk #{chunk_no})", expanded=(idx_m == 1)):
                        st.markdown(format_llm_markdown(full_passage))

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    kb_left, kb_right = st.columns([1.0, 1.35], gap="medium")
    with kb_left:
        with st.container(border=True):
            st.markdown(
                """
                <div class="sec-head">
                    <span class="sec-title">Core Regulatory &amp; Technical Decision Basis</span>
                    <span class="sec-tag">MANDATES</span>
                </div>
                <div style="font-size: 12.5px; line-height: 1.68; color: #cbd5e1;">
                    <div style="padding-bottom: 10px; margin-bottom: 10px; border-bottom: 1px solid #13223a;">
                        <strong style="color:#f87171;">UAE TDRA Federal Law Art. 14.3:</strong>
                        Prohibits routing sovereign or domestic telecommunications traffic across conflict-zone jurisdictions where foreign interception or physical sabotage risks exist.
                    </div>
                    <div style="padding-bottom: 10px; margin-bottom: 10px; border-bottom: 1px solid #13223a;">
                        <strong style="color:#38bdf8;">CBUAE CIIP Section 4.2.1:</strong>
                        Mandates 99.999% continuous availability and strict sovereign jurisdictional integrity for Tier-1 RTGS and SWIFT financial settlement corridors.
                    </div>
                    <div>
                        <strong style="color:#34d399;">ITU-T G.808.1 &amp; G.872:</strong>
                        Defines sub-50 ms optical protection switching and ROADM Wavelength Selective Switch (WSS) deterministic lambda preemption on surviving submarine cables.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with kb_right:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="sec-head">
                    <span class="sec-title">Indexed Official Standards Inventory</span>
                    <span class="sec-tag">{len(doc_inventory)} FILES</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if doc_inventory:
                st.dataframe(pd.DataFrame(doc_inventory), width="stretch", height=250, hide_index=True)


# ==============================================================================
# PAGE 5: AUDIT TRAIL
# ==============================================================================
elif st.session_state.current_page == "Audit Trail":
    with st.container(border=True):
        st.markdown(
            """
            <div class="sec-head">
                <div>
                    <span class="sec-title">Chronological Decision &amp; Execution Audit Trail</span>
                    <span class="sec-sub">Tamper-Evident Multi-Agent &amp; Operator Record</span>
                </div>
                <span class="sec-tag">COMPLIANCE LEDGER</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        f1, f2, f3 = st.columns([1.0, 1.6, 0.8], gap="medium", vertical_alignment="bottom")
        entity_list = ["All Entities"] + sorted({e["agent"] for e in orch.audit_log})
        with f1:
            sel_ent = st.selectbox("Entity Filter", entity_list, index=0)
        with f2:
            kw_q = st.text_input("Search Action or Details", value="")
        with f3:
            export_json = json.dumps(
                {
                    "system": "Submarine Cable Resilience Orchestrator",
                    "exported_utc": now_utc,
                    "workflow_stage": current_stage,
                    "audit_events": orch.audit_log,
                },
                indent=2,
                ensure_ascii=False,
            )
            st.download_button(
                label="Export Audit JSON",
                data=export_json,
                file_name=f"noc_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                width="stretch",
            )

        rows_audit = []
        for idx_e, item in enumerate(orch.audit_log, start=1):
            if sel_ent != "All Entities" and item["agent"] != sel_ent:
                continue
            if kw_q.strip():
                q_low = kw_q.strip().lower()
                if q_low not in item["action"].lower() and q_low not in item["details"].lower() and q_low not in item["agent"].lower():
                    continue
            rows_audit.append({
                "Seq": f"#{idx_e:03d}",
                "Timestamp": item["timestamp"],
                "Entity": item["agent"],
                "Action": item["action"],
                "Details": item["details"],
            })

        st.dataframe(pd.DataFrame(list(reversed(rows_audit))), width="stretch", hide_index=True)

        with st.expander("Inspect Raw Event Metadata (JSON)"):
            st.json(orch.audit_log)
