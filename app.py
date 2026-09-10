# ============================================================
# app.py — SAP Help Navigator Pro
# Complete single-file Streamlit application
# Deploy on Streamlit Cloud: share.streamlit.io
# ============================================================

import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, quote
import datetime
import math
from typing import Optional
from collections import defaultdict

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# ============================================================
# PAGE CONFIG  ← must be the very first Streamlit call
# ============================================================
st.set_page_config(
    page_title="SAP Help Navigator Pro",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://help.sap.com/docs",
        "About": "SAP Help Navigator Pro — Powered by help.sap.com & Google Gemini",
    },
)

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}

.main-header{
  background:linear-gradient(135deg,#0057A8 0%,#00A3E0 50%,#00D4AA 100%);
  padding:2rem 2.5rem;border-radius:16px;margin-bottom:1.5rem;
  box-shadow:0 8px 32px rgba(0,87,168,.25);color:#fff}
.main-header h1{font-size:2.1rem;font-weight:700;margin:0}
.main-header p{font-size:.95rem;opacity:.85;margin:.4rem 0 0}

.metric-card{
  background:#fff;border:1px solid #e8edf3;border-radius:12px;
  padding:1.1rem 1.3rem;text-align:center;
  box-shadow:0 2px 8px rgba(0,0,0,.06);transition:transform .2s,box-shadow .2s}
.metric-card:hover{transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,.1)}
.metric-card .value{font-size:1.7rem;font-weight:700;color:#0057A8}
.metric-card .label{font-size:.78rem;color:#6b7280;margin-top:.3rem}

.answer-box{
  background:linear-gradient(135deg,#f0f7ff,#e8f5e9);
  border-left:4px solid #0057A8;border-radius:12px;
  padding:1.4rem 1.8rem;margin:1rem 0;line-height:1.8}

.source-card{
  background:#fff;border:1px solid #dce3ec;border-radius:10px;
  padding:.9rem 1.1rem;margin:.45rem 0;box-shadow:0 1px 4px rgba(0,0,0,.05)}
.source-card a{color:#0057A8;text-decoration:none;font-weight:500}
.source-card a:hover{text-decoration:underline}

.step-card{
  background:#fff;border:1px solid #e0e7ef;border-radius:10px;
  padding:.9rem 1.2rem;margin:.5rem 0;
  display:flex;align-items:flex-start;gap:1rem;
  box-shadow:0 1px 4px rgba(0,0,0,.05)}
.step-num{
  background:linear-gradient(135deg,#0057A8,#00A3E0);color:#fff;
  border-radius:50%;width:30px;height:30px;min-width:30px;
  display:flex;align-items:center;justify-content:center;
  font-weight:700;font-size:.85rem}

.info-box{background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
  padding:.9rem 1.1rem;margin:.5rem 0;font-size:.9rem;color:#1e40af}
.warn-box{background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
  padding:.9rem 1.1rem;margin:.5rem 0;font-size:.9rem;color:#92400e}
.success-box{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
  padding:.9rem 1.1rem;margin:.5rem 0;font-size:.9rem;color:#166534}
.error-box{background:#fef2f2;border:1px solid #fecaca;border-radius:10px;
  padding:.9rem 1.1rem;margin:.5rem 0;font-size:.9rem;color:#991b1b}

.param-table{width:100%;border-collapse:collapse;font-size:.875rem}
.param-table th{background:#0057A8;color:#fff;padding:9px 14px;
  text-align:left;font-weight:600}
.param-table td{padding:7px 12px;border:1px solid #e5e7eb}
.param-table tr:nth-child(even) td{background:#f8fafc}

.chip{display:inline-block;background:#e8f0fe;color:#0057A8;
  border-radius:20px;padding:.22rem .7rem;font-size:.75rem;font-weight:600;margin:.15rem}
.critical-badge{display:inline-block;background:#fee2e2;color:#991b1b;
  border:1px solid #fca5a5;border-radius:6px;padding:1px 7px;font-size:.73rem;font-weight:700}
.high-badge{display:inline-block;background:#fef3c7;color:#92400e;
  border:1px solid #fcd34d;border-radius:6px;padding:1px 7px;font-size:.73rem;font-weight:700}
.medium-badge{display:inline-block;background:#dbeafe;color:#1e40af;
  border:1px solid #93c5fd;border-radius:6px;padding:1px 7px;font-size:.73rem;font-weight:700}

.sidebar-section{background:#f8fafc;border-radius:10px;padding:.75rem .9rem;
  margin-bottom:.9rem;border:1px solid #e2e8f0}

.stButton>button{border-radius:8px!important;font-weight:500!important;
  transition:all .2s!important}
.stButton>button:hover{transform:translateY(-1px);
  box-shadow:0 4px 12px rgba(0,0,0,.15)!important}
.stTabs [role="tab"]{font-weight:600;font-size:.88rem}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONSTANTS
# ============================================================
SAP_HELP_BASE  = "https://help.sap.com"
SAP_SEARCH_API = "https://help.sap.com/http.svc/search"
SAP_DOCS_API   = "https://help.sap.com/docs"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ============================================================
# SESSION STATE DEFAULTS
# ============================================================
_DEFAULTS = {
    "search_history":  [],
    "fetched_docs":    {},
    "conversation":    [],
    "api_key":         "",
    "current_product": "",
    "doc_cache":       {},
    "last_checklist":  [],
    "quick_q":         "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ============================================================
# LOAD GEMINI API KEY FROM STREAMLIT SECRETS
# ============================================================
def load_api_key() -> str:
    """
    Load Gemini API key.
    Priority: session_state → Streamlit secrets → empty string
    """
    if st.session_state.get("api_key"):
        return st.session_state["api_key"]
    try:
        key = st.secrets.get("gemini_api_key", "")
        if key:
            return key
    except Exception:
        pass
    return ""

# Load key once at startup
if not st.session_state.api_key:
    st.session_state.api_key = load_api_key()

# ============================================================
# PARAMETER DATABASE
# ============================================================
PARAMETER_DATABASE = {
    "SAP S/4HANA": {
        "memory": {
            "abap/heap_area_total":       {"value": "2000000000",  "unit": "bytes",   "desc": "Total heap memory for all work processes",    "note": "941735"},
            "abap/heap_area_dia":         {"value": "500000000",   "unit": "bytes",   "desc": "Heap area per dialog work process",           "note": "941735"},
            "abap/heap_area_nondia":      {"value": "1000000000",  "unit": "bytes",   "desc": "Heap area per non-dialog work process",       "note": "941735"},
            "em/initial_size_MB":         {"value": "4096",        "unit": "MB",      "desc": "Extended memory initial size",                "note": "747468"},
            "em/max_size_MB":             {"value": "16384",       "unit": "MB",      "desc": "Extended memory maximum size",                "note": "747468"},
            "zcsa/table_buffer_area":     {"value": "100000000",   "unit": "bytes",   "desc": "Generic table buffer size",                   "note": "1418123"},
            "rsdb/obj/buffersize":        {"value": "500000",      "unit": "KB",      "desc": "Repository object buffer",                    "note": "1127888"},
            "ipc/shm_psize_40":           {"value": "500000000",   "unit": "bytes",   "desc": "Shared memory pool size",                     "note": "723909"},
            "abap/buffersize":            {"value": "600000",      "unit": "KB",      "desc": "ABAP program buffer size",                    "note": "103747"},
            "ztta/roll_extension_dia":    {"value": "2000000000",  "unit": "bytes",   "desc": "Roll extension for dialog work processes",    "note": "96098"},
        },
        "workprocesses": {
            "rdisp/wp_no_dia":            {"value": "10",  "unit": "count",   "desc": "Number of dialog work processes",                    "note": "39412"},
            "rdisp/wp_no_btc":            {"value": "4",   "unit": "count",   "desc": "Number of background work processes",                "note": "39412"},
            "rdisp/wp_no_spo":            {"value": "2",   "unit": "count",   "desc": "Number of spool work processes",                     "note": "39412"},
            "rdisp/wp_no_upd":            {"value": "2",   "unit": "count",   "desc": "Number of update work processes",                    "note": "39412"},
            "rdisp/wp_no_upd2":           {"value": "1",   "unit": "count",   "desc": "Number of update-2 work processes",                  "note": "39412"},
            "rdisp/wp_no_enq":            {"value": "1",   "unit": "count",   "desc": "Number of enqueue work processes",                   "note": "39412"},
            "rdisp/max_wprun_time":       {"value": "600", "unit": "seconds", "desc": "Maximum dialog work process runtime",                "note": "15360"},
            "rdisp/appc_timeout":         {"value": "300", "unit": "seconds", "desc": "APPC/RFC timeout value",                             "note": ""},
        },
        "performance": {
            "rdisp/scheduler/prio_high":  {"value": "70",      "unit": "%",       "desc": "High priority queue threshold",                  "note": "1515190"},
            "enque/table_size":           {"value": "8388608", "unit": "bytes",   "desc": "Enqueue lock table size",                        "note": "185684"},
            "icm/max_conn":               {"value": "500",     "unit": "count",   "desc": "Maximum ICM connections",                        "note": "1421005"},
            "icm/req_queue_len":          {"value": "500",     "unit": "count",   "desc": "ICM request queue length",                       "note": "1421005"},
            "icm/keep_alive_timeout":     {"value": "60",      "unit": "seconds", "desc": "HTTP keep-alive timeout",                        "note": "1421005"},
            "abap/shared_objects_size_MB":{"value": "512",     "unit": "MB",      "desc": "Shared objects memory area",                     "note": "1101726"},
        },
        "security": {
            "login/min_password_lng":               {"value": "8",   "unit": "chars",   "desc": "Minimum password length",                  "note": "862989"},
            "login/password_expiration_time":        {"value": "90",  "unit": "days",    "desc": "Password expiry in days",                  "note": "862989"},
            "login/fails_to_session_end":            {"value": "3",   "unit": "count",   "desc": "Failed logons to end session",             "note": "862989"},
            "login/fails_to_user_lock":              {"value": "5",   "unit": "count",   "desc": "Failed logons to lock user",               "note": "862989"},
            "login/password_change_waittime":        {"value": "1",   "unit": "days",    "desc": "Min days between password changes",        "note": "862989"},
            "auth/rfc_authority_check":              {"value": "1",   "unit": "flag",    "desc": "Enable RFC authority check",               "note": "1408081"},
            "rec/client":                            {"value": "ALL", "unit": "string",  "desc": "Security audit log clients",               "note": "539404"},
            "rsau/enable":                           {"value": "1",   "unit": "flag",    "desc": "Enable security audit log",                "note": "539404"},
            "login/no_automatic_user_sapstar":       {"value": "1",   "unit": "flag",    "desc": "Disable SAP* auto-login",                  "note": "68048"},
        },
        "network": {
            "icm/server_port_0":          {"value": "PROT=HTTP,PORT=8000",   "unit": "string", "desc": "ICM HTTP port",                     "note": ""},
            "icm/server_port_1":          {"value": "PROT=HTTPS,PORT=44300", "unit": "string", "desc": "ICM HTTPS port",                    "note": ""},
            "ms/server_port_0":           {"value": "PROT=HTTP,PORT=8101",   "unit": "string", "desc": "Message server HTTP port",          "note": "519018"},
        },
    },
    "SAP HANA": {
        "memory": {
            "global_allocation_limit":                {"value": "80%_of_RAM",   "unit": "%",       "desc": "HANA global memory allocation limit",        "note": "1999997"},
            "max_gc_parallelism":                     {"value": "4",            "unit": "count",   "desc": "Garbage collection parallelism",              "note": "2000000"},
            "parallel_merge_threads":                 {"value": "4",            "unit": "count",   "desc": "Delta merge parallel threads",                "note": "2084065"},
            "unload_upper_bound":                     {"value": "90",           "unit": "%",       "desc": "Memory threshold for column store unload",    "note": "2127458"},
            "max_memory_estimation_for_queries":      {"value": "10737418240",  "unit": "bytes",   "desc": "Per-query memory cap",                        "note": "2222200"},
        },
        "performance": {
            "optimize_compression_goal":              {"value": "BALANCE",   "unit": "string",  "desc": "Compression optimization goal",                 "note": "2112604"},
            "result_cache_entry_lifetime":            {"value": "300",       "unit": "seconds", "desc": "SQL result cache time-to-live",                 "note": "2400005"},
            "joins/optimization_target":              {"value": "balanced",  "unit": "string",  "desc": "Join optimization strategy",                    "note": "2222200"},
            "tables/use_cs_for_column_compression":   {"value": "true",      "unit": "bool",    "desc": "Enable column compression",                     "note": "2112604"},
        },
        "backup": {
            "data_backup_buffer_size":                {"value": "134217728", "unit": "bytes",   "desc": "Backup I/O buffer size",                        "note": "1975256"},
            "parallel_data_backup_backint_channels":  {"value": "4",         "unit": "count",   "desc": "Parallel backup channels",                      "note": "1976128"},
            "max_recovery_backint_channels":          {"value": "4",         "unit": "count",   "desc": "Maximum parallel recovery channels",            "note": "1976128"},
        },
        "security": {
            "password_layout":                        {"value": "A1a",   "unit": "string", "desc": "Password complexity requirement",                    "note": ""},
            "minimum_password_length":                {"value": "8",     "unit": "chars",  "desc": "Minimum password length",                           "note": ""},
            "password_expire_days":                   {"value": "182",   "unit": "days",   "desc": "Password expiry days",                              "note": ""},
            "enable_user_self_service":               {"value": "false", "unit": "bool",   "desc": "Disable self-service password reset",               "note": ""},
        },
    },
    "SAP BTP": {
        "cloud_foundry": {
            "MEMORY":                     {"value": "1024M",    "unit": "MB",     "desc": "App instance memory quota",                         "note": ""},
            "INSTANCES":                  {"value": "2",        "unit": "count",  "desc": "Number of app instances",                           "note": ""},
            "DISK_QUOTA":                 {"value": "2048M",    "unit": "MB",     "desc": "App disk quota",                                    "note": ""},
            "HEALTH_CHECK_TYPE":          {"value": "http",     "unit": "string", "desc": "App health check method",                           "note": ""},
            "HEALTH_CHECK_HTTP_ENDPOINT": {"value": "/health",  "unit": "string", "desc": "Health check endpoint",                             "note": ""},
        },
    },
    "SAP NetWeaver": {
        "abap": {
            "abap/buffersize":            {"value": "600000",       "unit": "KB",   "desc": "ABAP program buffer",                             "note": "103747"},
            "abap/shared_objects_size_MB":{"value": "512",          "unit": "MB",   "desc": "Shared objects memory area",                      "note": "1101726"},
            "abap/heap_area_total":       {"value": "2000000000",   "unit": "bytes","desc": "Total heap memory",                               "note": "941735"},
            "abap/use_openssl":           {"value": "1",            "unit": "flag", "desc": "Use OpenSSL for RFC encryption",                  "note": "510007"},
        },
        "messaging": {
            "ms/server_port_0":           {"value": "PROT=HTTP,PORT=8101", "unit": "string", "desc": "Message server HTTP port",               "note": "519018"},
            "ms/max_clients":             {"value": "500",                  "unit": "count",  "desc": "Maximum message server clients",         "note": ""},
        },
    },
}

OS_PARAMETERS = {
    "Linux (RHEL/SLES)": {
        "vm.max_map_count":               {"value": "2147483647",       "desc": "Virtual memory map areas",           "note": "900929"},
        "vm.swappiness":                  {"value": "10",               "desc": "Kernel swap tendency (low for SAP)", "note": "1980196"},
        "kernel.shmmax":                  {"value": "<total_RAM_bytes>","desc": "Maximum shared memory segment",      "note": "941735"},
        "kernel.shmmni":                  {"value": "32768",            "desc": "Maximum shared memory identifiers",  "note": "941735"},
        "kernel.shmall":                  {"value": "1152921504606846975","desc": "Total shared memory pages",        "note": "941735"},
        "fs.file-max":                    {"value": "20000000",         "desc": "System-wide open file descriptor max","note": "1984787"},
        "net.core.somaxconn":             {"value": "4096",             "desc": "Maximum socket connection backlog",  "note": "2205917"},
        "net.ipv4.tcp_max_syn_backlog":   {"value": "8192",             "desc": "SYN backlog queue depth",            "note": "2205917"},
        "net.ipv4.tcp_tw_reuse":          {"value": "1",                "desc": "Reuse TIME_WAIT sockets",            "note": "2205917"},
        "net.ipv4.tcp_fin_timeout":       {"value": "20",               "desc": "TCP FIN timeout seconds",            "note": "2205917"},
        "net.ipv4.tcp_keepalive_time":    {"value": "300",              "desc": "TCP keepalive interval",             "note": "2205917"},
        "vm.dirty_bytes":                 {"value": "629145600",        "desc": "Dirty memory bytes before writeback","note": "2205917"},
        "vm.dirty_background_bytes":      {"value": "314572800",        "desc": "Background writeback threshold",     "note": "2205917"},
    },
    "Windows Server": {
        "TcpTimedWaitDelay":              {"value": "30",   "desc": "TCP TIME_WAIT delay in seconds",  "note": ""},
        "MaxUserPort":                    {"value": "65534","desc": "Maximum user port number",         "note": ""},
        "MaxHashTableSize":               {"value": "65536","desc": "TCP hash table size",              "note": ""},
    },
}

# ============================================================
# UPGRADE PATH MATRIX
# ============================================================
UPGRADE_PATHS = {
    "SAP ECC 6.0 EHP0": {
        "SAP ECC 6.0 EHP8":   {"type": "EHP Upgrade",       "tool": "SUM",     "stops": ["Intermediate EHPs may be required"], "note": "1680045"},
        "SAP S/4HANA 2020":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": ["Must reach EHP7/EHP8 first"],        "note": "2399707"},
        "SAP S/4HANA 2023":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": ["EHP8 SP20+ required"],               "note": "2913617"},
    },
    "SAP ECC 6.0 EHP7": {
        "SAP ECC 6.0 EHP8":   {"type": "EHP Upgrade",       "tool": "SUM",     "stops": [],                                    "note": "1680045"},
        "SAP S/4HANA 1709":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": [],                                    "note": "2399707"},
        "SAP S/4HANA 2020":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": [],                                    "note": "2399707"},
        "SAP S/4HANA 2022":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": [],                                    "note": "2913617"},
        "SAP S/4HANA 2023":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": ["Apply minimum SP level first"],      "note": "2913617"},
    },
    "SAP ECC 6.0 EHP8": {
        "SAP S/4HANA 1511":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": [],                                    "note": "2399707"},
        "SAP S/4HANA 1610":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": [],                                    "note": "2399707"},
        "SAP S/4HANA 1709":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": [],                                    "note": "2399707"},
        "SAP S/4HANA 1809":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": [],                                    "note": "2399707"},
        "SAP S/4HANA 1909":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": [],                                    "note": "2399707"},
        "SAP S/4HANA 2020":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": [],                                    "note": "2399707"},
        "SAP S/4HANA 2021":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2022":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": [],                                    "note": "2913617"},
        "SAP S/4HANA 2023":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": [],                                    "note": "2913617"},
        "SAP S/4HANA 2024":   {"type": "System Conversion", "tool": "SUM+DMO", "stops": ["Apply latest SP first"],             "note": "2913617"},
    },
    "SAP S/4HANA 1709": {
        "SAP S/4HANA 1809":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 1909":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2020":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2021":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2022":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2023":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2024":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
    },
    "SAP S/4HANA 1809": {
        "SAP S/4HANA 1909":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2020":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2021":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2022":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2023":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2024":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
    },
    "SAP S/4HANA 1909": {
        "SAP S/4HANA 2020":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2021":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2022":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2023":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2024":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
    },
    "SAP S/4HANA 2020": {
        "SAP S/4HANA 2021":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2022":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2023":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2024":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
    },
    "SAP S/4HANA 2021": {
        "SAP S/4HANA 2022":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2023":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2024":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
    },
    "SAP S/4HANA 2022": {
        "SAP S/4HANA 2023":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
        "SAP S/4HANA 2024":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
    },
    "SAP S/4HANA 2023": {
        "SAP S/4HANA 2024":   {"type": "Release Upgrade",   "tool": "SUM",     "stops": [],                                    "note": "2568780"},
    },
    "SAP HANA 1.0 SPS12": {
        "SAP HANA 2.0 SPS04": {"type": "Database Upgrade",  "tool": "hdblcm",  "stops": ["Full backup required first"],        "note": "2380493"},
        "SAP HANA 2.0 SPS05": {"type": "Database Upgrade",  "tool": "hdblcm",  "stops": ["Via SPS04 first"],                   "note": "2380493"},
        "SAP HANA 2.0 SPS07": {"type": "Database Upgrade",  "tool": "hdblcm",  "stops": ["Via SPS04 then SPS06"],              "note": "2380493"},
    },
    "SAP HANA 2.0 SPS04": {
        "SAP HANA 2.0 SPS05": {"type": "Revision Upgrade",  "tool": "hdblcm",  "stops": [],                                    "note": "2380493"},
        "SAP HANA 2.0 SPS06": {"type": "Revision Upgrade",  "tool": "hdblcm",  "stops": [],                                    "note": "2380493"},
        "SAP HANA 2.0 SPS07": {"type": "Revision Upgrade",  "tool": "hdblcm",  "stops": [],                                    "note": "2380493"},
    },
    "SAP HANA 2.0 SPS05": {
        "SAP HANA 2.0 SPS06": {"type": "Revision Upgrade",  "tool": "hdblcm",  "stops": [],                                    "note": "2380493"},
        "SAP HANA 2.0 SPS07": {"type": "Revision Upgrade",  "tool": "hdblcm",  "stops": [],                                    "note": "2380493"},
    },
    "SAP HANA 2.0 SPS06": {
        "SAP HANA 2.0 SPS07": {"type": "Revision Upgrade",  "tool": "hdblcm",  "stops": [],                                    "note": "2380493"},
    },
    "SAP Solution Manager 7.1": {
        "SAP Solution Manager 7.2": {"type": "Release Upgrade", "tool": "SUM", "stops": ["SP10 minimum recommended"],          "note": "2383326"},
    },
    "SAP NetWeaver 7.4": {
        "SAP NetWeaver 7.5":        {"type": "Release Upgrade", "tool": "SUM", "stops": [],                                    "note": "2568780"},
        "SAP ABAP Platform 1909":   {"type": "Release Upgrade", "tool": "SUM", "stops": [],                                    "note": "2568780"},
    },
    "SAP NetWeaver 7.5": {
        "SAP ABAP Platform 1909":   {"type": "Release Upgrade", "tool": "SUM", "stops": [],                                    "note": "2568780"},
        "SAP ABAP Platform 2022":   {"type": "Release Upgrade", "tool": "SUM", "stops": [],                                    "note": "2568780"},
    },
}

# ============================================================
# SAP PRODUCT LIST
# ============================================================
SAP_PRODUCTS = [
    "", "SAP S/4HANA", "SAP ECC / ERP 6.0", "SAP HANA",
    "SAP BTP", "SAP Fiori", "SAP Solution Manager",
    "SAP NetWeaver", "SAP ABAP Platform", "SAP Business One",
    "SAP SuccessFactors", "SAP Ariba", "SAP PI/PO",
    "SAP GRC", "SAP BW/4HANA", "SAP Integration Suite",
    "SAP HCM", "SAP CRM", "SAP SRM", "SAP IBP",
    "SAP Data Intelligence", "SAP Concur",
]

# ============================================================
# WEB FETCHING HELPERS
# ============================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_url(url: str) -> Optional[str]:
    """Fetch a URL and return HTML text, or None on failure."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception:
        return None

def search_sap_help(query: str, product: str = "") -> list:
    """Search SAP Help Portal and return list of result dicts."""
    results = []
    term = f"{product} {query}".strip() if product else query

    # Strategy 1: SAP Help search API
    try:
        r = requests.get(
            SAP_SEARCH_API,
            params={"q": term, "area": "docs", "language": "en-US", "state": "PRODUCTION"},
            headers=HEADERS, timeout=12,
        )
        if r.status_code == 200:
            data = r.json()
            for item in data.get("hits", data.get("results", []))[:8]:
                url = item.get("url", item.get("link", ""))
                if url:
                    if not url.startswith("http"):
                        url = SAP_HELP_BASE + url
                    results.append({
                        "title":       item.get("title", item.get("name", "SAP Document")),
                        "url":         url,
                        "description": item.get("description", item.get("summary", "")),
                        "source":      "SAP Help API",
                    })
    except Exception:
        pass

    # Strategy 2: Scrape SAP docs page
    if len(results) < 3:
        try:
            html = fetch_url(f"{SAP_DOCS_API}?q={quote(term)}")
            if html:
                soup = BeautifulSoup(html, "html.parser")
                for a in soup.select("a[href*='/docs/']")[:10]:
                    href = a.get("href", "")
                    if not href.startswith("http"):
                        href = SAP_HELP_BASE + href
                    text = a.get_text(strip=True)
                    if text and len(text) > 10:
                        results.append({
                            "title": text, "url": href,
                            "description": "", "source": "SAP Docs",
                        })
        except Exception:
            pass

    # Strategy 3: Curated fallback links
    if len(results) < 2:
        results.extend(_fallback_results(term))

    # Deduplicate
    seen, out = set(), []
    for item in results:
        if item["url"] not in seen:
            seen.add(item["url"])
            out.append(item)
    return out[:8]

def _fallback_results(query: str) -> list:
    """Return curated SAP Help links based on keywords."""
    q = query.lower()
    mapping = {
        ("s/4hana", "s4hana", "s4"): [
            ("SAP S/4HANA Documentation",       "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE"),
            ("S/4HANA Upgrade Guide",            "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/upgrade"),
            ("S/4HANA Installation Guide",       "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/installation"),
        ],
        ("ecc", "erp 6", "erp6", "ehp"): [
            ("SAP ERP Documentation",            "https://help.sap.com/docs/SAP_ERP"),
            ("SAP ECC Upgrade Guide",            "https://help.sap.com/docs/SAP_ERP/upgrade"),
        ],
        ("btp", "business technology platform"): [
            ("SAP BTP Documentation",            "https://help.sap.com/docs/btp"),
            ("BTP Account Setup",                "https://help.sap.com/docs/btp/sap-business-technology-platform/setting-up-your-account"),
        ],
        ("hana",): [
            ("SAP HANA Platform",                "https://help.sap.com/docs/SAP_HANA_PLATFORM"),
            ("SAP HANA Administration Guide",    "https://help.sap.com/docs/SAP_HANA_PLATFORM/administration"),
            ("SAP HANA Installation Guide",      "https://help.sap.com/docs/SAP_HANA_PLATFORM/installation"),
        ],
        ("fiori",): [
            ("SAP Fiori Documentation",          "https://help.sap.com/docs/SAP_FIORI"),
            ("Fiori Apps Library",               "https://fioriappslibrary.hana.ondemand.com/"),
        ],
        ("solution manager", "solman"): [
            ("SAP Solution Manager",             "https://help.sap.com/docs/SAP_SOLUTION_MANAGER"),
        ],
        ("netweaver",): [
            ("SAP NetWeaver",                    "https://help.sap.com/docs/SAP_NETWEAVER"),
            ("NetWeaver Admin Guide",            "https://help.sap.com/docs/SAP_NETWEAVER/administration"),
        ],
        ("abap",): [
            ("SAP ABAP Platform",                "https://help.sap.com/docs/ABAP_PLATFORM"),
            ("ABAP Development Guide",           "https://help.sap.com/docs/ABAP_PLATFORM/development"),
        ],
        ("pi", "po", "integration"): [
            ("SAP Integration Suite",            "https://help.sap.com/docs/SAP_INTEGRATION_SUITE"),
            ("SAP PI/PO Documentation",          "https://help.sap.com/docs/SAP_NETWEAVER_PI"),
        ],
        ("grc",): [
            ("SAP GRC Documentation",            "https://help.sap.com/docs/SAP_GRC"),
        ],
        ("bw", "bw/4hana"): [
            ("SAP BW/4HANA Documentation",       "https://help.sap.com/docs/SAP_BW4HANA"),
        ],
        ("successfactors",): [
            ("SAP SuccessFactors Documentation", "https://help.sap.com/docs/SAP_SUCCESSFACTORS_HXM_SUITE"),
        ],
    }
    out = []
    for keywords, links in mapping.items():
        if any(kw in q for kw in keywords):
            for title, url in links:
                out.append({
                    "title": title, "url": url,
                    "description": f"Official SAP documentation for {title}",
                    "source": "SAP Help Portal",
                })
    if not out:
        out = [
            {"title": "SAP Help Portal",           "url": "https://help.sap.com/docs",                        "description": "Browse all SAP documentation",     "source": "SAP"},
            {"title": "SAP S/4HANA Documentation", "url": "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE",  "description": "S/4HANA on-premise documentation", "source": "SAP"},
            {"title": "SAP HANA Platform",          "url": "https://help.sap.com/docs/SAP_HANA_PLATFORM",     "description": "SAP HANA documentation",           "source": "SAP"},
            {"title": "SAP BTP Documentation",      "url": "https://help.sap.com/docs/btp",                   "description": "BTP documentation",                "source": "SAP"},
        ]
    return out

@st.cache_data(ttl=1800, show_spinner=False)
def extract_doc_content(url: str) -> dict:
    """Fetch a SAP Help URL and extract structured content."""
    html = fetch_url(url)
    if not html:
        return {"title": "Unavailable", "content": "", "sections": {}, "pdf_links": [], "url": url}

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Extract title
    title = ""
    for sel in ["h1.title", "h1", "title", ".page-title", ".document-title"]:
        t = soup.select_one(sel)
        if t:
            title = t.get_text(strip=True)
            break

    # Extract main content
    main = (soup.select_one("main, .content, article, .topic-body, #content, .help-content")
            or soup.body)
    text = main.get_text("\n", strip=True) if main else soup.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)[:12000]

    # Extract topic sections using regex
    sections = {}
    patterns = {
        "prerequisites":  r"(?i)(prerequisite|system requirement|before you (?:begin|start)).*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
        "upgrade_path":   r"(?i)(upgrade path|upgrade route|migration path|target release).*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
        "installation":   r"(?i)(install|setup|deploy|provisioning).*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
        "parameters":     r"(?i)(parameter|profile|configuration|tuning|sizing).*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
        "best_practices": r"(?i)(best practice|recommendation|guideline|important note).*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
        "steps":          r"(?i)(step|procedure|how to|task|perform|execute).*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
        "dependencies":   r"(?i)(depend|compatib|kernel|patch|component version).*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text, re.DOTALL)
        if m:
            sections[key] = m.group(0)[:2000]

    # Find PDF download links
    pdf_links = [
        urljoin(url, a["href"])
        for a in soup.find_all("a", href=True)
        if ".pdf" in a["href"].lower()
    ]

    return {
        "title":     title,
        "content":   text,
        "sections":  sections,
        "pdf_links": pdf_links[:8],
        "url":       url,
    }

# ============================================================
# AI ANSWER ENGINE
# ============================================================
def get_ai_answer(question: str, context: str, api_key: str, product: str = "") -> str:
    """Generate answer using Gemini AI or rule-based fallback."""
    if api_key and GENAI_AVAILABLE:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""You are a senior SAP Technical Architect with 20+ years of experience.
You specialize in SAP upgrades, installations, system administration, and best practices.
Product context: {product or 'General SAP'}

INSTRUCTIONS:
- Use ONLY the provided SAP documentation context to answer
- Structure response with **bold headings**, numbered steps, bullet lists
- Add ⚠️ for warnings, ✅ for prerequisites, 📋 for notes
- Include relevant SAP Note numbers when applicable
- Include code blocks for commands and parameters
- Be specific, actionable, and precise

--- SAP DOCUMENTATION CONTEXT ---
{context[:7000]}
--- END CONTEXT ---

Question: {question}

Provide a detailed, well-structured answer:"""
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            err_msg = str(e)
            fallback = _rule_based_answer(question, context, product)
            if "quota" in err_msg.lower() or "limit" in err_msg.lower():
                return fallback + "\n\n> ⚠️ *Gemini API rate limit reached. Showing rule-based answer.*"
            return fallback + f"\n\n> ⚠️ *AI unavailable: {err_msg[:80]}*"
    return _rule_based_answer(question, context, product)

def _rule_based_answer(question: str, context: str, product: str = "") -> str:
    """Generate structured answer using keyword matching when no AI available."""
    q = question.lower()
    lines = [l.strip() for l in context.split("\n") if l.strip() and len(l.strip()) > 25]

    def get_relevant(keywords: list) -> list:
        return [l for l in lines if any(w in l.lower() for w in keywords)][:10]

    # ── Upgrade Path ──────────────────────────────────────────
    if any(k in q for k in ["upgrade path", "upgrade route", "migration path",
                              "how to upgrade", "upgrade from", "target release",
                              "upgrade scenario"]):
        hits = get_relevant(["upgrade", "migration", "path", "release", "target", "version", "SPS", "SP"])
        ans = f"## 🔄 Upgrade Path — {product}\n\n"
        if hits:
            ans += "**From SAP documentation:**\n" + "\n".join(f"- {l}" for l in hits) + "\n\n"
        ans += """
### Supported SAP Upgrade Scenarios

| Scenario | Description | Tool |
|---|---|---|
| **EHP Upgrade** | ECC → higher Enhancement Package | SUM |
| **Release Upgrade** | S/4HANA X → S/4HANA Y | SUM |
| **System Conversion** | ECC/AnyDB → S/4HANA + HANA | SUM + DMO |
| **New Implementation** | Greenfield S/4HANA | SWPM |
| **Selective Data Transition** | Hybrid approach | LTMC + SUM |

### Key Steps
1. Run **SAP Readiness Check** — Transaction `/SDF/RC_START_CHECK`
2. Check **PAM** for supported upgrade paths
3. Generate **Stack.xml** via SAP Maintenance Planner
4. Execute upgrade with **SUM (Software Update Manager)**
5. Handle **SPDD** (dictionary) and **SPAU** (repository) adjustments

📋 **SAP Note 2913617** — SAP Readiness Check for S/4HANA
📋 **SAP Note 2568780** — SUM master note
📋 **SAP Note 2399707** — S/4HANA technical prerequisites
🔗 [PAM](https://apps.support.sap.com/sap/support/pam) | [Maintenance Planner](https://support.sap.com/mp)
"""
        return ans

    # ── Prerequisites ─────────────────────────────────────────
    if any(k in q for k in ["prerequisite", "requirement", "before", "prepare",
                              "checklist", "readiness", "minimum"]):
        hits = get_relevant(["require", "prerequisite", "minimum", "supported",
                              "must", "hardware", "software", "os", "database"])
        ans = f"## ✅ Prerequisites & Requirements — {product}\n\n"
        if hits:
            ans += "**From SAP documentation:**\n" + "\n".join(f"- {l}" for l in hits) + "\n\n"
        ans += """
### 🖥️ Hardware Requirements
- **CPU**: Verify with SAP Quick Sizer (service.sap.com/quicksizer)
- **RAM**: Minimum per product; SAP HANA requires physical RAM ≥ active dataset size
- **Disk**: OS + DB + SAP binaries + SUM workspace (~100 GB) + backups
- **Network**: 1 Gbps minimum; 10 Gbps recommended for SAP HANA

### 💻 Software Requirements
- Supported **OS**: RHEL 8/9 or SLES 15 for HANA (verify exact version in PAM)
- Supported **Database**: check PAM compatibility matrix for exact versions
- Latest **SAP Kernel** patches (64-bit Unicode)
- **JDK 11 or 17** for Java stack / Fiori / BTP components

### 🔧 SAP-Specific Prerequisites
- Valid **S-user** with download authorization
- **SAP Solution Manager 7.2** — maintenance certificate required by SUM
- Minimum **Support Package** level (see SAP Note 2186744)
- **Unicode-enabled** system (mandatory for S/4HANA)
- Completed **SAP Readiness Check** with no open Critical findings

### 📋 Key SAP Notes
- **SAP Note 2186744** — Pre-upgrade checklist
- **SAP Note 2399707** — S/4HANA technical prerequisites
- **SAP Note 2913617** — SAP Readiness Check
- **SAP Note 19466**   — Operating system requirements
"""
        return ans

    # ── Installation / Download ───────────────────────────────
    if any(k in q for k in ["install", "download", "setup", "deploy",
                              "sapinst", "swpm", "media", "dvd"]):
        hits = get_relevant(["install", "download", "sapinst", "setup", "deploy", "media"])
        ans = f"## 💾 Installation & Download Guide — {product}\n\n"
        if hits:
            ans += "**From SAP documentation:**\n" + "\n".join(f"- {l}" for l in hits) + "\n\n"
        ans += """
### 📥 Download Resources
| Resource | URL | Requires |
|---|---|---|
| SAP Software Download Center | https://support.sap.com/swdc | S-user + download auth |
| SAP Maintenance Planner | https://support.sap.com/mp | S-user |
| SAP ONE Support Launchpad | https://launchpad.support.sap.com | S-user |

### 📦 Required Download Components
```bash
1. SAP Application — Installation Exports / DVDs
2. SAP Kernel — 64-bit Unicode (latest patch level)
3. SAP Host Agent — version 7.22+
4. Database — vendor-specific installer
5. SUM — Software Update Manager (for upgrades)
6. SWPM — Software Provisioning Manager (fresh install)
7. Stack.xml — Generate via Maintenance Planner (NOT manually)

### 🚀 Installation Sequence (SWPM)
```bash
1. Prepare OS (filesystem, OS users, kernel parameters)
2. Install database software
3. Run SWPM: ./sapinst  (or sapinst.exe on Windows)
4. Apply latest SAP Kernel patches
5. Configure ICM, SNC, SSL certificates
6. Apply Support Packages via SPAM / SAINT
7. Post-installation configuration (RZ10, SM59, STMS)

📋 SAP Note 1680045 — Installation best practices
📋 SAP Note 2393060 — sapinst / SWPM troubleshooting
📋 SAP Note 1639498 — How to download SAP software
"""
return ans

# ── Parameters ────────────────────────────────────────────
if any(k in q for k in ["parameter", "profile", "config", "tuning", "memory", "sizing", "rz10", "buffer", "work process"]):
    hits = get_relevant(["parameter", "profile", "memory", "buffer", "rdisp", "abap/", "icm/"])
    ans = f"## ⚙️ Parameter Recommendations — {product}\n\n"
    if hits:
        ans += "**From SAP documentation:**\n" + "\n".join(f"- {l}" for l in hits) + "\n\n"
        ans += """
🔧 Key ABAP Instance Profile Parameters (DEFAULT.PFL)
# Memory Settings
abap/heap_area_total       = 2000000000    # Total heap for all WPs
abap/heap_area_dia         = 500000000     # Heap per dialog WP
em/initial_size_MB         = 4096          # Extended memory initial
em/max_size_MB             = 16384         # Extended memory maximum
ztta/roll_extension_dia    = 2000000000    # Roll extension for dialog

# Work Process Counts
rdisp/wp_no_dia            = 10            # Dialog WPs (users/20)
rdisp/wp_no_btc            = 4             # Background WPs
rdisp/wp_no_spo            = 2             # Spool WPs
rdisp/wp_no_upd            = 2             # Update WPs
rdisp/max_wprun_time       = 600           # Max dialog runtime (sec)

# Buffer Settings
zcsa/table_buffer_area     = 100000000     # Generic table buffer
rsdb/obj/buffersize        = 500000        # Repository object buffer
abap/buffersize            = 600000        # ABAP program buffer

# Security Settings
login/min_password_lng     = 8             # Minimum password length
login/fails_to_user_lock   = 5             # Lockout threshold
rsau/enable                = 1             # Enable security audit log

🗄️ SAP HANA Parameters (global.ini)
[memorymanager]
global_allocation_limit     = <80% of total RAM in MB>
unload_upper_bound          = 90

[joins]
optimization_target         = balanced

[sql]
result_cache_entry_lifetime = 300

🐧 OS Kernel Parameters (/etc/sysctl.conf)

vm.max_map_count            = 2147483647
vm.swappiness               = 10
kernel.shmmax               = <total RAM in bytes>
kernel.shmmni               = 32768
fs.file-max                 = 20000000
net.core.somaxconn          = 4096
net.ipv4.tcp_max_syn_backlog = 8192

🔧 Key Transactions

| Transaction | Purpose |
|---|---|
| **RZ10** | Maintain instance / default profiles |
| **RZ11** | Parameter documentation and valid values |
| **ST02** | Buffer hit rates — tune based on swap rates |
| **SM50/SM66** | Work process utilization monitoring |

📋 SAP Note 941735 — Memory management parameters
📋 SAP Note 2222200 — Recommended SAP HANA settings
📋 SAP Note 1984787 — OS parameters for SAP on Linux
"""
return ans

# ── Dependencies ──────────────────────────────────────────
if any(k in q for k in ["depend", "compatib", "stack", "component",
    "kernel version", "patch level", "version matrix"]):
    hits = get_relevant(["depend", "compatib", "kernel", "patch", "component", "version", "SP"])
    ans = f"## 🔗 Dependencies & Compatibility — {product}\n\n"
    if hits:
        ans += "**From SAP documentation:**\n" + "\n".join(f"- {l}" for l in hits) + "\n\n"
        ans += """
🔗 Standard Component Dependency Matrix
COMPONENT
MINIMUM VERSION
NOTES
SAP Kernel
Latest patch level
Always use latest stable
SAP Host Agent
7.22+
Required for SUM and SWPM
SAP Solution Manager
7.2 SP12+
Maintenance certificate required
Java Runtime
JDK 11 or 17
NetWeaver Java / Fiori
SAP HANA
2.0 SPS05+
For S/4HANA 2021 and later
ICU Library
Match kernel version
Unicode support


🔍 How to Check Compatibility
PAM (Product Availability Matrix):
apps.support.sap.com/sap/support/pam
SAP Maintenance Planner:
Validates all component combinations automatically
Transaction SAINT:
Lists all installed add-ons with exact version numbers
Transaction SPAM:
Shows current Support Package level per component
📋 SAP Note 2379811 — Supported HANA revisions for S/4HANA
📋 SAP Note 1707976 — Kernel dependency overview
"""
return ans

# ── Best Practices ────────────────────────────────────────
if any(k in q for k in ["best practice", "recommendation", "guideline",
"tip", "advice", "approach"]):
    ans = f"## 🌟 Best Practices — {product}\n\n"
    ans += """
🔄 Upgrade & Migration Best Practices
Always upgrade DEV → QAS → PRD — never skip environments
Maintain 2 verified backups before production upgrade (test restore!)
Use SAP Maintenance Planner for stack.xml — never create manually
Schedule upgrades in a planned maintenance window with rollback plan
Run SAP Readiness Check and resolve ALL Critical findings first
Perform a dry-run upgrade on a sandbox copy before production
Keep SUM running under <sid>adm user — never as root
⚡ Performance Best Practices
Right-size memory using SAP Quick Sizer + actual workload data
Monitor weekly with SAP EarlyWatch Alert (Solution Manager)
Run HANA Mini Checks monthly (SAP Note 1999993)
Monitor ABAP buffers with ST02 — tune when swap rate > 1%
Archive old transaction data using ILM / Data Archiving (AS_AFW)
Use table partitioning for HANA tables > 500 million rows
🛡️ Security Best Practices
Review HotNews SAP Security Notes every Patch Tuesday
No S_DEVELOP authorization in production systems
Enable Security Audit Log (SM19 / RSAU_CONFIG) in all systems
Enforce SNC for all RFC and SAP GUI connections
Use Communication users for RFC service accounts only
Regularly run SAP Security Optimization Service checks
🔧 Operations Best Practices
Implement monitoring via SAP Solution Manager or SAP Focused Run
HANA backups: Full daily + log backup every 15-30 minutes
Test HA/DR failover procedure at least quarterly
Maintain a transport strategy — use CTS+ or gCTS
Document all runbooks for critical batch jobs (SM37)
Schedule database statistics updates (DB20 / DBACOCKPIT)
📚 Key Reference Documents
DOCUMENT
WHERE TO FIND
SAP Master Guide
help.sap.com → your product → Master Guide
SAP Security Guide
help.sap.com → your product → Security
SAP Operations Guide
help.sap.com → your product → Operations
SAP Sizing Guide
service.sap.com/sizing
SAP Best Practices
rapid.sap.com/bp


📋 SAP Note 1999993 — HANA Mini Checks
🔗 SAP Best Practices Explorer
"""
return ans

# ── Upgrade Plan ──────────────────────────────────────────
if any(k in q for k in ["plan", "step", "procedure", "how to",
"phase", "project", "roadmap", "execute"]):
    ans = f"## 📋 Upgrade Project Plan — {product}\n\n"
    ans += """
Phase 1: Assessment & Planning (Weeks 1–3)
System inventory: release, SP level, add-ons (SPAM / SAINT)
Run SAP Readiness Check: /SDF/RC_START_CHECK — resolve all findings
Review Product Availability Matrix (PAM) for target release support
Custom code analysis via SCMA / ATC / Custom Code Migration App
Hardware sizing validation with SAP Quick Sizer
Interface and integration mapping (SM59, WE20, SOAMANAGER)
Define project scope, risks, timeline, team RACI matrix
Phase 2: Infrastructure & Downloads (Weeks 4–6)
Prepare target OS — verify PAM compatibility (RHEL 8/9 or SLES 15)
Apply OS kernel parameters (/etc/sysctl.conf — SAP Note 900929)
Install / upgrade database software
Download SUM (latest version) from support.sap.com/swdc
Download target release installation media from SWDC
Generate Stack.xml via SAP Maintenance Planner
Prepare SUM staging directory (minimum 100 GB free space)
Perform dry-run upgrade on sandbox system
Phase 3: System Preparation (Weeks 7–8)
Apply minimum prerequisite Support Package (SAP Note 2186744)
Complete all custom code remediations (zero critical ATC findings)
Freeze transport landscape — import all pending transports (STMS)
Full database backup and verify restore on secondary system
Export SAP profiles: backup /usr/sap/<SID>/SYS/profile/
Document configuration: RZ10, SM59, STMS, SM30
Run SUM EXTRACTONLY phase: ./STARTUP EXTRACTONLY
Fix ALL ERRORS reported by SUM before proceeding
Stakeholder go / no-go confirmation
Phase 4: Upgrade Execution (Maintenance Window / Downtime)
Announce maintenance window — lock all non-admin users
Start SUM: cd <SUM_DIR> && ./STARTUP (ABAP mode)
Monitor via SUM Web UI: https://<host>:1129/lmsl/sumabap/<SID>/doc/
Handle SPDD prompt — adjust Data Dictionary modifications
Handle SPAU prompt — adjust Repository object modifications
Database migration via DMO (if AnyDB → SAP HANA conversion)
Verify system starts correctly after SUM completion
Phase 5: Post-Upgrade & Validation (Weeks 9–10)
Apply latest SAP Kernel patches (64-bit Unicode)
Run RUTPOADAPT — post-upgrade adaptation report
Apply recommended post-upgrade SAP Notes
Performance testing and parameter tuning (RZ10, ST05, ST02)
Smoke testing: FI, MM, SD, HCM, PP core business transactions
Security review and authorization profile adjustment (SU25)
User Acceptance Testing (UAT) sign-off from business
Phase 6: Go-Live & Stabilization (Weeks 11–12+)
Production cutover — follow approved cutover checklist
Re-activate transport routes (STMS)
Intensive hypercare monitoring: SM50, SM66, ST05, DBACOCKPIT
Performance comparison vs pre-upgrade baseline
Interface reconnection and integration verification
End-user communication and training sessions
Project closure, lessons learned, documentation update
📋 SAP Note 2568780 — SUM documentation
📋 SAP Note 2622660 — SUM best practices
📋 SAP Note 2176227 — Disk space requirements for SUM
"""
return ans

# ── Downloads / PDFs ──────────────────────────────────────
if any(k in q for k in ["download", "pdf", "where to find", "guide", "document"]):
    ans = f"## ⬇️ Downloads & Documentation — {product}\n\n"
    ans += """
📥 SAP Software Download Center
RESOURCE
URL
ACCESS
SAP Software Download Center
https://support.sap.com/swdc
S-user required
SAP ONE Support Launchpad
https://launchpad.support.sap.com
S-user required
SAP Maintenance Planner
https://support.sap.com/mp
S-user required
SAP Help Portal PDFs
https://help.sap.com/docs
Public access
SAP Best Practices
https://rapid.sap.com/bp/
Public access


📄 How to Download SAP Guide PDFs
1. Go to https://help.sap.com/docs
2. Search for your product (e.g. "SAP S/4HANA 2023")
3. Click on the product tile
4. Navigate to Installation / Upgrade / Administration guide
5. Click the PDF icon (download) at top right of guide page

📦 What to Download for an Upgrade
1. SUM (Software Update Manager) — search "SUM" in SWDC
2. Target release Installation Exports (all required DVDs)
3. SAP Kernel 64-bit Unicode — latest patch level
4. SAP Host Agent — latest version
5. Database-specific components (e.g. HANA installer for DMO)
6. Stack.xml — MUST be generated via Maintenance Planner

🔑 Getting Download Access
S-user must have "Software Downloads" role
Request via: https://support.sap.com/en/my-support/users.html
SAP Note 1639498 — How to request download authorization
"""
return ans

#── Generic fallback ──────────────────────────────────────
hits = [l for l in lines if len(l) > 40][:12]
ans = f"## 📖 SAP Documentation Answer — {product}\n\n"
ans += f"Your question: {question}\n\n"
if hits:
    ans += "Extracted from SAP Help Portal documentation:\n\n"
    ans += "\n\n".join(hits[:8])
else:
    ans += f"""### 💡 Suggested Next Steps
SAP Help Portal — Search for {product or question}
SAP Community — Real-world answers at community.sap.com
SAP Support Notes — Technical details at launchpad.support.sap.com
Try a more specific question — Include product version and exact topic
Select a product in the sidebar and use the Quick Questions buttons for best results.
"""
return ans

#============================================================
#PRE-UPGRADE CHECKLIST GENERATOR
#============================================================
def generate_checklist(source: str, target: str, opts: dict) -> list:
    """Generate a prioritized pre-upgrade checklist."""
    items = [
        # System Assessment
        {
            "cat": "System Assessment", "icon": "🔍", "pri": "Critical",
            "task": "Run SAP Readiness Check",
            "detail": "Execute /SDF/RC_START_CHECK – resolve ALL Critical and High findings before proceeding",
            "tool": "Transaction /SDF/RC_START_CHECK", "note": "2913617"
        },
        {"cat": "System Assessment", "icon": "🔍", "pri": "Critical",
        "task": f"Verify {source} meets minimum SP prerequisite for {target}",
        "detail": "Check SAP Note 2186744 for exact minimum SP level; apply if not met",
        "tool": "SPAM / SE01", "note": "2186744"},
        {"cat": "System Assessment", "icon": "🔍", "pri": "High",
        "task": "Check Product Availability Matrix (PAM)",
        "detail": "Confirm OS version, DB version, and all components are supported for target release",
        "tool": "apps.support.sap.com/sap/support/pam", "note": ""},
        {"cat": "System Assessment", "icon": "🔍", "pri": "High",
        "task": "List all installed Add-ons and Industry Solutions",
        "detail": "Use SAINT to list all installed products; verify each has upgrade path to target",
        "tool": "Transaction SAINT", "note": ""},
        {"cat": "System Assessment", "icon": "🔍", "pri": "Medium",
        "task": "Review open support messages and known issues",
        "detail": "Check SAP Support Portal for open incidents that may affect the upgrade",
        "tool": "support.sap.com", "note": ""},
        # Custom Code
        {"cat": "Custom Code", "icon": "🖊️", "pri": "Critical",
        "task": "Run Custom Code Migration Analysis",
        "detail": "Use SCMA / ATC / Custom Code Migration Fiori App — remediate all critical findings",
        "tool": "Transaction SCMA / ATC", "note": "2190420"},
        {"cat": "Custom Code", "icon": "🖊️", "pri": "High",
        "task": "Scan for obsolete ABAP syntax in Z/Y namespaces",
        "detail": "Run program RS_ABAP_SOURCE_SCAN for syntax errors and incompatible statements",
        "tool": "RS_ABAP_SOURCE_SCAN", "note": ""},
        {"cat": "Custom Code", "icon": "🖊️", "pri": "High",
        "task": "Document all custom modifications",
        "detail": "Export list of all Z/Y tables, BADIs, user exits, enhancements, custom reports",
        "tool": "SE16N, SPDD, SPAU", "note": ""},
        # Infrastructure
        {"cat": "Infrastructure", "icon": "🖥️", "pri": "Critical",
        "task": "Validate hardware sizing for target release",
        "detail": "Run SAP Quick Sizer; verify minimum RAM, CPU cores, and disk space requirements",
        "tool": "service.sap.com/quicksizer", "note": "1652093"},
        {"cat": "Infrastructure", "icon": "🖥️", "pri": "Critical",
        "task": "Ensure ≥ 100 GB free disk space for SUM workspace",
        "detail": "SUM requires dedicated staging space throughout entire upgrade duration",
        "tool": "df -h (Linux)", "note": "2176227"},
        {"cat": "Infrastructure", "icon": "🖥️", "pri": "High",
        "task": "Verify and update OS kernel parameters",
        "detail": "Set vm.max_map_count=2147483647, kernel.shmmax, fs.file-max per SAP Note 900929",
        "tool": "/etc/sysctl.conf", "note": "900929"},
        {"cat": "Infrastructure", "icon": "🖥️", "pri": "High",
        "task": "Confirm OS version is supported for target release",
        "detail": "RHEL 8/9 or SLES 15 required for HANA 2.0; verify exact versions in PAM",
        "tool": "PAM", "note": "1984787"},
        # Backup
        {"cat": "Backup & Recovery", "icon": "💾", "pri": "Critical",
        "task": "Full verified database backup with restore test",
        "detail": "Complete backup AND restore test to a secondary system before starting upgrade",
        "tool": "BRTOOLS / hdbsql BACKUP DATA / DBACOCKPIT", "note": ""},
        {"cat": "Backup & Recovery", "icon": "💾", "pri": "Critical",
        "task": "Export and archive all SAP profile files",
        "detail": "Copy entire /usr/sap/<SID>/SYS/profile/ directory to secure backup location",
        "tool": "RZ10 export / OS file copy", "note": ""},
        {"cat": "Backup & Recovery", "icon": "💾", "pri": "High",
        "task": "Document current system configuration",
        "detail": "Export/screenshot: RZ10 params, SM59 RFCs, STMS routes, SM30 key tables",
        "tool": "RZ10, SM59, STMS, SM30", "note": ""},
        # Downloads
        {"cat": "Software Downloads", "icon": "⬇️", "pri": "Critical",
        "task": "Download latest SUM (Software Update Manager) from SWDC",
        "detail": "Go to support.sap.com/swdc → Support Packages & Patches → SUM → download latest",
        "tool": "support.sap.com/swdc", "note": "2568780"},
        {"cat": "Software Downloads", "icon": "⬇️", "pri": "Critical",
        "task": f"Download all {target} installation/upgrade media",
        "detail": "Download all required installation exports, kernel, and database components",
        "tool": "SAP Software Download Center", "note": ""},
        {"cat": "Software Downloads", "icon": "⬇️", "pri": "Critical",
        "task": "Generate Stack.xml via SAP Maintenance Planner",
        "detail": "NEVER create stack.xml manually — always use Maintenance Planner to generate it",
        "tool": "support.sap.com/mp", "note": "2383326"},
        {"cat": "Software Downloads", "icon": "⬇️", "pri": "High",
        "task": "Download latest SAP Kernel (64-bit Unicode)",
        "detail": "Get latest patch-level kernel for target release; apply after upgrade completes",
        "tool": "SAP SWDC → Kernel section", "note": ""},
        # Access
        {"cat": "Access & Licensing", "icon": "🔑", "pri": "Critical",
        "task": "Confirm S-user download authorization is active",
        "detail": "S-user needs Software Downloads role; test actual download access before upgrade day",
        "tool": "support.sap.com user management", "note": ""},
        {"cat": "Access & Licensing", "icon": "🔑", "pri": "Critical",
        "task": "Obtain valid maintenance certificate from Solution Manager",
        "detail": "SUM requires a current maintenance certificate — generate via SolMan LMDB",
        "tool": "SAP Solution Manager → LMDB", "note": "1979523"},
        {"cat": "Access & Licensing", "icon": "🔑", "pri": "High",
        "task": "Freeze transport landscape before upgrade start",
        "detail": "Lock TMS import queues; import ALL pending transports before starting SUM",
        "tool": "Transaction STMS", "note": ""},
        # Communication
        {"cat": "Communication", "icon": "📣", "pri": "High",
        "task": "Notify all stakeholders of downtime window",
        "detail": "Send formal downtime notification minimum 5 business days in advance",
        "tool": "Email / calendar invite", "note": ""},
        {"cat": "Communication", "icon": "📣", "pri": "Medium",
        "task": "Prepare rollback plan and escalation contacts",
        "detail": "Define rollback decision point time, rollback procedure, and SAP support contacts",
        "tool": "Project documentation", "note": ""},
]

# Optional items based on system characteristics
if opts.get("has_custom_code"):
    items.append({
        "cat": "Custom Code", "icon": "🖊️", "pri": "Critical",
        "task": "Complete ALL custom code remediations before SUM EXTRACTONLY",
        "detail": "Zero critical ATC findings required; all high findings must be documented and accepted",
        "tool": "SCMA / ATC / Eclipse ADT", "note": "2190420",
    })
if opts.get("has_interfaces"):
    items.append({
        "cat": "Integration", "icon": "🔗", "pri": "High",
        "task": "Document all RFC / iDoc / Web Service interface connections",
        "detail": "List SM59 RFC destinations, WE20 iDoc partners, SOAMANAGER Web Services",
        "tool": "SM59, WE20, SOAMANAGER", "note": "",
    })
    items.append({
        "cat": "Integration", "icon": "🔗", "pri": "High",
        "task": "Coordinate maintenance window with all interface counterpart systems",
        "detail": "Notify upstream / downstream systems; plan reconnection sequence after upgrade",
        "tool": "Project coordination", "note": "",
    })
if opts.get("ha_required"):
    items.append({
        "cat": "High Availability", "icon": "🛡️", "pri": "High",
        "task": "Plan HA cluster failover procedure for upgrade downtime window",
        "detail": "Define cluster failover and rollback procedure for Pacemaker / MSCS / HANA SR",
        "tool": "Pacemaker / MSCS / hdbnsutil -sr_state", "note": "1872602",
    })
if opts.get("non_unicode"):
    items.append({
        "cat": "System Assessment", "icon": "🔍", "pri": "Critical",
        "task": "Plan Unicode conversion — mandatory for S/4HANA target",
        "detail": "S/4HANA requires Unicode system; combine Unicode conversion with SUM using UCCHECK",
        "tool": "UCCHECK / SUM", "note": "73606",
    })
return items
#============================================================
#    HTML REPORT GENERATOR
#============================================================
def generate_html_report(product: str, question: str, answer: str,
sources: list, checklist: list) -> str:
    """Build a self-contained downloadable HTML report."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# Build checklist table if provided
checklist_section = ""
if checklist:
    rows = ""
    for item in checklist:
        pc = {"Critical": "#fee2e2", "High": "#fef3c7", "Medium": "#dbeafe"}.get(item["pri"], "#f1f5f9")
        note_html = (
        f'<a href="https://launchpad.support.sap.com/#/notes/{item["note"]}" target="_blank">'
        f'Note {item["note"]}</a>'
        ) if item.get("note") else "—"
rows += (
f'<tr>'
f'<td style="background:{pc};padding:6px 10px;border:1px solid #e5e7eb;'
f'white-space:nowrap;font-weight:600">{item["pri"]}</td>'
f'<td style="padding:6px 10px;border:1px solid #e5e7eb">{item["cat"]}</td>'
f'<td style="padding:6px 10px;border:1px solid #e5e7eb;font-weight:600">{item["task"]}</td>'
f'<td style="padding:6px 10px;border:1px solid #e5e7eb;font-size:.85em;'
f'color:#374151">{item["detail"]}</td>'
f'<td style="padding:6px 10px;border:1px solid #e5e7eb;font-size:.85em">{item["tool"]}</td>'
f'<td style="padding:6px 10px;border:1px solid #e5e7eb;font-size:.85em">{note_html}</td>'
f'</tr>'
)
checklist_section = f"""
<div class="section">
<h2>📋 Pre-Upgrade Checklist ({len(checklist)} items)</h2>
<table style="width:100%;border-collapse:collapse;font-size:.85rem">
<thead>
<tr style="background:#0057A8;color:#fff">
<th style="padding:8px 12px">Priority</th>
<th style="padding:8px 12px">Category</th>
<th style="padding:8px 12px">Task</th>
<th style="padding:8px 12px">Detail</th>
<th style="padding:8px 12px">Tool / Transaction</th>
<th style="padding:8px 12px">SAP Note</th>
</tr>
</thead>
<tbody>{rows}</tbody>
</table>
</div>"""

# Build sources list
sources_html = "".join(
f'<li style="margin:.4rem 0">'
f'<a href="{s["url"]}" target="_blank"><strong>{s["title"]}</strong></a>'
f'{"<br><small style=\'color:#6b7280\'>" + s.get("description","")[:100] + "</small>" if s.get("description") else ""}'
f'</li>'
for s in sources
)

# Escape answer for safe HTML embedding
answer_escaped = answer.replace("<", "&lt;").replace(">", "&gt;")

return f"""<!DOCTYPE html><html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SAP Help Navigator Report — {product}</title>
<style>
body {{
font-family: 'Segoe UI', Arial, sans-serif;
margin: 0; padding: 0;
background: #f8fafc; color: #1e293b; line-height: 1.6;
}}
.header {{
background: linear-gradient(135deg, #0057A8, #00A3E0);
color: #fff; padding: 2rem 3rem;
}}
.header h1 {{ margin: 0; font-size: 1.7rem; }}
.header p {{ margin: .3rem 0 0; opacity: .85; }}
.section {{
background: #fff; margin: 1.5rem 2rem;
padding: 1.5rem 2rem; border-radius: 12px;
box-shadow: 0 2px 8px rgba(0,0,0,.07);
}}
h2 {{
color: #0057A8;
border-bottom: 2px solid #e0e7ef;
padding-bottom: .4rem; margin-top: 0;
}}
.answer-box {{
background: #f0f7ff; border-left: 4px solid #0057A8;
padding: 1rem 1.5rem; border-radius: 8px;
white-space: pre-wrap; font-size: .9rem;
}}
.footer {{
text-align: center; padding: 1.5rem;
color: #94a3b8; font-size: .8rem;
}}
a {{ color: #0057A8; }}
@media print {{
.section {{ box-shadow: none; border: 1px solid #e5e7eb; }}
}}
</style>
</head>
<body>
<div class="header">
<h1>🔷 SAP Help Navigator Pro — Report</h1>
<p>
Product: <strong>{product or "General SAP"}</strong>
&nbsp;·&nbsp; Generated: {now}
&nbsp;·&nbsp;
<a href="https://help.sap.com/docs" style="color:#fff" target="_blank">
help.sap.com
</a>
</p>
</div>

<div class="section">
<h2>❓ Question</h2>
<p style="font-size:1.05rem;font-weight:500">{question}</p>
</div>

<div class="section">
<h2>💡 Answer</h2>
<div class="answer-box">{answer_escaped}</div>
</div>

{checklist_section}

<div class="section">
<h2>🔗 Source Documents ({len(sources)})</h2>
<ul style="padding-left:1.5rem;line-height:2">
{sources_html}
</ul>
</div>

<div class="footer">
SAP Help Navigator Pro
&nbsp;·&nbsp; {now}
&nbsp;·&nbsp; For internal use only
&nbsp;·&nbsp; Data from
<a href="https://help.sap.com/docs">help.sap.com</a>
</div>
</body>
</html>"""

#============================================================
# SIDEBAR
#============================================================
def render_sidebar():
    with st.sidebar:
        st.markdown("### 🔹 SAP Help Navigator")
        st.markdown("---")

        # API Key Status Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        if st.session_state.api_key:
            try:
                from_secrets = bool(st.secrets.get("gemini_api_key", ""))
            except Exception:
                from_secrets = False

            if from_secrets:
                st.success("🤖 **Gemini AI Active**\n\n*Key loaded from Streamlit Secrets*")
            else:
                st.success("🤖 **Gemini AI Active**\n\n*Key entered manually*")
        else:
            st.warning("📐 **Rule-based Mode**\n\nAdd Gemini key for AI-powered answers")
manual_key = st.text_input(
"Enter Gemini API Key",
type="password",
placeholder="AIzaSy...",
key="manual_key_input",
help="Get a free key at aistudio.google.com",
)
if manual_key:
    st.session_state.api_key = manual_key
    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Product Selector
st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
st.markdown("**📦 SAP Product**")
idx = (SAP_PRODUCTS.index(st.session_state.current_product)
if st.session_state.current_product in SAP_PRODUCTS else 0)
selected = st.selectbox(
"Select product",
SAP_PRODUCTS,
index=idx,
key="product_selector",
label_visibility="collapsed",
)
if selected != st.session_state.current_product:
    st.session_state.current_product = selected

custom = st.text_input(
"Or type custom product",
placeholder="e.g. SAP Fieldglass",
key="custom_product",
)
if custom:
    st.session_state.current_product = custom
    st.markdown('</div>', unsafe_allow_html=True)

# Quick Question Buttons
st.markdown("**⚡ Quick Questions**")
quick_questions = {
"🔄 Upgrade Path": "What are the supported upgrade paths and upgrade routes?",
"✅ Prerequisites": "What are the system prerequisites and requirements?",
"💾 Installation": "Provide complete step-by-step installation guide",
"⚙️ Parameters": "What are the recommended profile parameters and configurations?",
"🔗 Dependencies": "What are the component dependencies and compatibility requirements?",
"📋 Upgrade Plan": "Generate a complete detailed upgrade project plan with all phases and steps",
"🌟 Best Practices": "What are the best practices and SAP recommendations?",
"⬇️ Downloads": "Where can I download the software, patches, and documentation PDFs?",
}
for label, q in quick_questions.items():
    if st.button(label, use_container_width=True, key=f"qbtn_{label[:5]}"):
        st.session_state.quick_q = q
        st.rerun()

# Recent Search History
if st.session_state.search_history:
    st.markdown("---")
    st.markdown("**🕘 Recent Searches**")
for h in reversed(st.session_state.search_history[-5:]):
    st.caption(f"• {h[:38]}{'…' if len(h) > 38 else ''}")

# Footer
st.markdown("---")
st.markdown(
"<div style='font-size:.72rem;color:#6b7280;text-align:center;line-height:1.6'>"
"📄 Data: <a href='https://help.sap.com/docs' target='_blank'>help.sap.com</a><br>"
"🤖 AI: <a href='https://aistudio.google.com' target='_blank'>Google Gemini</a><br>"
"🔒 For internal / authorized use only"
"</div>",
unsafe_allow_html=True,
)
#============================================================
#HEADER
#============================================================
def render_header():
    product = st.session_state.current_product
    mode_txt = "🤖 Gemini AI Active" if st.session_state.api_key else "📐 Rule-based Mode"
    docs_count = len(st.session_state.fetched_docs)
    qa_count = len(st.session_state.conversation)
    st.markdown(
    f"""<div class="main-header">
<h1>🔷 SAP Help Navigator Pro</h1>
<p>
Intelligent SAP Documentation Assistant &nbsp;·&nbsp;
Product: <strong>{product or "Select a product in sidebar →"}</strong>
&nbsp;·&nbsp; {mode_txt}
&nbsp;·&nbsp; {docs_count} docs fetched &nbsp;·&nbsp; {qa_count} Q&amp;A
&nbsp;·&nbsp;
<a href="https://help.sap.com/docs" target="_blank" style="color:#fff">
help.sap.com ↗
</a>
</p>
</div>""",
unsafe_allow_html=True,
)

#============================================================
#TAB 1 SEARCH & ASK
#============================================================
def tab_search_and_ask(product: str):
    st.markdown("### 🔍 Search SAP Documentation & Ask Questions")
    st.markdown(
'<div class="info-box">💡 Ask any question about your SAP product. '
'The tool searches live SAP Help Portal documentation and generates '
'detailed structured answers. Select a product in the sidebar first for best results.</div>',
unsafe_allow_html=True,
)

col_q, col_btn = st.columns([5, 1])
with col_q:
    default_q = st.session_state.pop("quick_q", "")
    question = st.text_input(
    "Your question",
    value=default_q,
    placeholder="e.g. What are the prerequisites for upgrading SAP S/4HANA 2022 to 2023?",
    key="main_question",
    label_visibility="collapsed",
    )
with col_btn:
    go = st.button("🔍 Search", type="primary", use_container_width=True)

# Suggestion buttons
st.markdown("**💡 Suggested questions:**")
sugs = [
"Upgrade path ECC to S/4HANA",
"HANA memory parameters",
"SUM upgrade steps",
"S/4HANA 2023 prerequisites",
"HANA backup best practices",
"BTP setup and configuration",
]
sug_cols = st.columns(len(sugs))
for i, sug in enumerate(sugs):
    with sug_cols[i]:
        if st.button(sug, key=f"sug_{i}"):
            st.session_state.quick_q = sug
            st.rerun()

if go and question:
    # Add to search history
    if question not in st.session_state.search_history:
        st.session_state.search_history.append(question)

# Search for documents
with st.spinner("🔍 Searching SAP Help Portal…"):
    results = search_sap_help(question, product)

# Fetch document content
with st.spinner("📄 Reading SAP documentation…"):
    context = ""
    for res in results[:3]:
        url = res["url"]
if url not in st.session_state.doc_cache:
    doc = extract_doc_content(url)
    st.session_state.doc_cache[url] = doc
    st.session_state.fetched_docs[url] = doc
    doc = st.session_state.doc_cache[url]
    context += (
    f"\n\n=== SOURCE: {doc.get('title', '')} ===\n"
    f"{doc.get('content', '')[:3000]}"
    )

# Generate answer
with st.spinner("🤖 Generating answer…"):
    answer = get_ai_answer(question, context, st.session_state.api_key, product)

# Save to conversation history
st.session_state.conversation.append({
"question": question,
"answer": answer,
"sources": results,
"product": product,
})

# Determine icon from question type
q_lower = question.lower()
icon = next(
(ic for kw, ic in [
("upgrade", "🔄"), ("prerequisite", "✅"), ("install", "💾"),
("parameter", "⚙️"), ("depend", "🔗"), ("best practice", "🌟"),
("download", "⬇️"), ("plan", "📋"), ("hana", "🗄️"),
] if kw in q_lower),
"📖",
)

# Display answer
st.markdown(f"### {icon} Answer")
st.markdown(
f'<div class="answer-box">{answer}</div>',
unsafe_allow_html=True,
)

# Display source documents
if results:
    st.markdown("### 🔗 Source Documents from SAP Help Portal")
for r in results[:6]:
    st.markdown(
    f'<div class="source-card">'
    f'<a href="{r["url"]}" target="_blank">📄 {r["title"]}</a><br>'
    f'<small style="color:#6b7280">'
    f'{r.get("description", "")[:120]}'
    f'</small><br>'
    f'<small style="color:#94a3b8">'
    f'Source: {r.get("source", "SAP Help Portal")} &nbsp;·&nbsp; '
    f'<a href="{r["url"]}" target="_blank" style="color:#94a3b8">'
    f'{r["url"][:65]}…</a>'
    f'</small>'
    f'</div>',
    unsafe_allow_html=True,
    )

# Display PDF links found
all_pdfs = list({
pdf
for doc in st.session_state.fetched_docs.values()
for pdf in doc.get("pdf_links", [])
})
if all_pdfs:
    st.markdown("### 📥 PDF Documents Found")
    for pdf in all_pdfs[:6]:
        filename = pdf.split("/")[-1] or "document.pdf"
        st.markdown(
        f'<div class="source-card">'
        f'📕 <a href="{pdf}" target="_blank">{filename}</a>'
        f'</div>',
        unsafe_allow_html=True,
        )
#============================================================
#2 DOCUMENT VIEWER
#============================================================
def tab_document_viewer(product: str):
    st.markdown("### 📄 SAP Document Viewer")
    st.markdown(
    '<div class="info-box">📄 Paste any SAP Help Portal URL to fetch and '
    'parse the document. The tool extracts key sections and lets you ask '
    'specific questions about the document content.</div>',
    unsafe_allow_html=True,
    )

col_url, col_btn = st.columns([4, 1])
with col_url:
    url_input = st.text_input(
    "SAP Help Portal URL",
    placeholder="https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/...",
    key="doc_url_input",
    )
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📥 Fetch Document", use_container_width=True) and url_input:
        with st.spinner("📄 Fetching document content…"):
            doc = extract_doc_content(url_input)
            st.session_state.fetched_docs[url_input] = doc
            st.session_state.doc_cache[url_input] = doc
if doc.get("title"):
    st.success(f"✅ Fetched: {doc['title'][:60]}")
else:
    st.warning("⚠️ Document fetched but title not found. Check URL.")

if not st.session_state.fetched_docs:
    st.markdown(
    '<div class="info-box">📄 No documents fetched yet. '
    'Use the Search & Ask to search for topics, '
    'or paste a SAP Help Portal URL above.</div>',
    unsafe_allow_html=True,
    )
return

# Document selector
selected_url = st.selectbox(
"Select a fetched document to view",
list(st.session_state.fetched_docs.keys()),
format_func=lambda u: st.session_state.fetched_docs[u].get("title", u)[:70],
)
doc = st.session_state.fetched_docs[selected_url]

# Document header
col_title, col_link = st.columns([3, 1])
with col_title:
    st.markdown(f"#### 📄 {doc.get('title', 'Document')}")
with col_link:
    st.markdown(
    f'<a href="{selected_url}" target="_blank">'
    f'🔗 Open on SAP Help Portal</a>',
    unsafe_allow_html=True,
    )

# Section tabs if sections were detected
sections = doc.get("sections", {})
if sections:
st.markdown("##### 📑 Detected Document Sections")
sec_tab_labels = [f"📌 {s.replace('_', ' ').title()}" for s in sections]
sec_tabs = st.tabs(sec_tab_labels)
for i, (sec_name, sec_content) in enumerate(sections.items()):
with sec_tabs[i]:
st.markdown(sec_content)

# PDF links found in document
col_content, col_links = st.columns([3, 1])
with col_content:
with st.expander("📖 View Full Document Text"):
st.text_area(
"Document content",
doc.get("content", "No content extracted")[:5000],
height=350,
label_visibility="collapsed",
)
with col_links:
if doc.get("pdf_links"):
st.markdown("**📥 PDFs in this doc:**")
for pdf in doc["pdf_links"][:5]:
fn = pdf.split("/")[-1]
st.markdown(
f'<a href="{pdf}" target="_blank" style="font-size:.82rem">'
f'📕 {fn[:30]}</a>',
unsafe_allow_html=True,
)

# Ask a question about this specific document
st.markdown("---")
st.markdown("#### ❓ Ask a Question About This Document")
doc_question = st.text_input(
"Your question about this document",
placeholder="e.g. What installation steps are described here?",
key="doc_specific_question",
)
if st.button("💬 Get Answer", key="doc_ask_btn") and doc_question:
with st.spinner("Generating answer from document content…"):
doc_answer = get_ai_answer(
doc_question,
doc.get("content", ""),
st.session_state.api_key,
product,
)
st.markdown(
f'<div class="answer-box">{doc_answer}</div>',
unsafe_allow_html=True,
)
st.session_state.conversation.append({
"question": doc_question,
"answer": doc_answer,
"sources": [{"title": doc.get("title", ""), "url": selected_url,
"description": ""}],
"product": product,
})
#============================================================
#3 UPGRADE PLANNER
#============================================================
def tab_upgrade_planner(product: str):
st.markdown("### 📋 SAP Upgrade Project Planner")
st.markdown(
'<div class="info-box">📋 Fill in your upgrade scenario details to generate '
'a complete, phased upgrade project plan with detailed steps, '
'key SAP Notes, and downloadable reports.</div>',
unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
src_release = st.text_input("Source Release",
placeholder="e.g. SAP ECC 6.0 EHP8", key="up_src")
src_db = st.selectbox("Source Database",
["", "SAP HANA", "Oracle", "MS SQL Server",
"IBM DB2", "MaxDB", "Sybase ASE"], key="up_sdb")
with col2:
tgt_release = st.text_input("Target Release",
placeholder="e.g. SAP S/4HANA 2023", key="up_tgt")
tgt_db = st.selectbox("Target Database",
["", "SAP HANA", "Oracle", "MS SQL Server"], key="up_tdb")
with col3:
os_plat = st.selectbox("OS Platform",
["", "Linux RHEL 8", "Linux RHEL 9",
"Linux SLES 15", "Windows Server 2022", "IBM AIX"],
key="up_os")
timeline = st.selectbox("Project Timeline",
["", "3 months", "6 months",
"9 months", "12 months", "18 months"],
key="up_tl")

col_a, col_b = st.columns(2)
with col_a:
sys_size = st.selectbox("System Size",
["", "Small (<100 users)", "Medium (100–500)",
"Large (500–2000)", "Enterprise (2000+)"], key="up_sz")
has_cc = st.checkbox("Has Custom Code / Z-Developments", value=True, key="up_cc")
with col_b:
has_if = st.checkbox("Has Interface Connections", value=True, key="up_if")
ha_req = st.checkbox("High Availability Required", value=False, key="up_ha")
non_uc = st.checkbox("Non-Unicode System", value=False, key="up_uc")

if st.button("🚀 Generate Complete Upgrade Plan", type="primary", use_container_width=True):
        if not src_release or not tgt_release:
            st.warning("⚠️ Please enter both Source Release and Target Release.")
            return

        context = (
            f"Upgrade from {src_release} ({src_db}) to {tgt_release} ({tgt_db}). "
            f"OS: {os_plat}. Timeline: {timeline}. Size: {sys_size}. "
            f"Custom code: {has_cc}. Interfaces: {has_if}. HA: {ha_req}. "
            f"Non-Unicode: {non_uc}."
        )
        upgrade_q = f"Generate detailed upgrade project plan from {src_release} to {tgt_release}"

        with st.spinner("📋 Building your upgrade plan…"):
            ai_plan = get_ai_answer(
                upgrade_q, context,
                st.session_state.api_key,
                f"{src_release} → {tgt_release}",
            )

        st.markdown("---")
        st.markdown(f"## 📋 Upgrade Plan: **{src_release}** → **{tgt_release}**")

        # Timeline visual bar
        if timeline:
            months_match = re.search(r"\d+", timeline)
            months = int(months_match.group()) if months_match else 6
            st.markdown("#### 🗓️ Project Timeline Overview")
            phase_data = [
                ("Assessment",    15, "#0057A8"),
                ("Infrastructure",15, "#00A3E0"),
                ("Preparation",   20, "#0096C7"),
                ("Execution",     15, "#0077B6"),
                ("Validation",    20, "#00B4D8"),
                ("Go-Live",       15, "#023E8A"),
            ]
            tl_cols = st.columns(len(phase_data))
            for i, (ph_name, ph_pct, ph_color) in enumerate(phase_data):
                ph_weeks = max(1, round(months * 4 * ph_pct / 100))
                with tl_cols[i]:
                    st.markdown(
                        f'<div style="background:{ph_color};color:#fff;border-radius:10px;'
                        f'padding:.6rem .4rem;text-align:center;font-size:.78rem;font-weight:600">'
                        f'{ph_name}<br>'
                        f'<span style="font-size:1.05rem;font-weight:700">~{ph_weeks}w</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        st.markdown("<br>", unsafe_allow_html=True)

        # Six phase expanders
        phases = [
            ("🔍 Phase 1: Assessment & Planning", [
                "System inventory: current release, SP level, add-ons (SPAM / SAINT)",
                "Run SAP Readiness Check: Transaction /SDF/RC_START_CHECK — resolve ALL findings",
                "Review Product Availability Matrix (PAM) for target release compatibility",
                "Custom code analysis via SCMA / ATC / Custom Code Migration Fiori App",
                "Hardware sizing validation with SAP Quick Sizer (service.sap.com/quicksizer)",
                "Interface and integration mapping: SM59, WE20, SOAMANAGER",
                "Define project scope, risks, timeline, and team RACI matrix",
                "Stakeholder alignment and project kick-off",
            ]),
            ("📥 Phase 2: Infrastructure & Downloads", [
                f"Prepare target OS: {os_plat or 'Linux RHEL 8/9 or SLES 15'} — verify PAM support",
                "Apply OS kernel parameters per SAP Note 900929 (/etc/sysctl.conf)",
                f"Install / upgrade database: {tgt_db or 'SAP HANA'} to supported version",
                "Download SUM (latest version) from support.sap.com/swdc",
                f"Download {tgt_release} installation media and kernel from SWDC",
                "Generate Stack.xml via SAP Maintenance Planner (support.sap.com/mp)",
                "Prepare SUM staging directory — minimum 100 GB free disk space",
                "Perform dry-run upgrade on copy of production (strongly recommended)",
            ]),
            ("🔧 Phase 3: System Preparation", [
                "Apply minimum prerequisite Support Package (SAP Note 2186744)",
                "Complete ALL custom code remediations — zero critical ATC findings required",
                "Freeze transport landscape (STMS) — import all pending transports first",
                "Full database backup with verified restore test on secondary system",
                "Export SAP profiles: backup /usr/sap/<SID>/SYS/profile/ directory",
                "Document system configuration: RZ10, SM59, STMS, SM30",
                "Run SUM EXTRACTONLY phase: ./STARTUP EXTRACTONLY",
                "Resolve ALL ERRORS shown in SUM pre-check before proceeding",
                "Formal go / no-go approval from all stakeholders",
            ]),
            ("⚡ Phase 4: Upgrade Execution (Downtime Window)", [
                "Send final maintenance window notification to all users",
                "Lock all non-admin users — start of planned downtime",
                "Start SUM upgrade: cd <SUM_DIR> && ./STARTUP (ABAP mode)",
                "Monitor via SUM Web UI: https://<host>:1129/lmsl/sumabap/<SID>/doc/",
                "Handle SPDD prompt: adjust Data Dictionary modifications",
                "Handle SPAU prompt: adjust Repository object modifications",
                "Database migration via DMO if converting from AnyDB to SAP HANA",
                "Monitor SUM phases: MAIN_SHDIMP → MAIN_NEWBAS → MAIN_UPG → MAIN_POST → CLEANUP",
                "Verify system starts correctly after SUM completes",
            ]),
            ("✅ Phase 5: Post-Upgrade & Validation", [
                "Apply latest SAP Kernel patches (64-bit Unicode, latest patch level)",
                "Run RUTPOADAPT post-upgrade adaptation report",
                "Apply recommended post-upgrade corrections and SAP Notes",
                "Performance baseline testing and parameter tuning (RZ10, ST05, ST02)",
                "Smoke testing of all core business transactions: FI, MM, SD, HCM, PP",
                "Security review and authorization profile adjustment (SU25 / SU24)",
                "User Acceptance Testing (UAT) with formal sign-off from business owners",
                "Interface reconnection testing and end-to-end integration validation",
            ]),
            ("🚀 Phase 6: Go-Live & Stabilization", [
                "Execute production cutover following the approved cutover checklist",
                "Re-activate transport routes and import queues (STMS)",
                "Intensive hypercare monitoring: SM50, SM66, ST05, ST22, DBACOCKPIT",
                "Daily performance comparison vs pre-upgrade baseline for first 2 weeks",
                "Interface monitoring: SM58, WE05, SXMB_MONI",
                "End-user support desk activation and communication",
                "Hypercare period: minimum 2 weeks intensive, 4 weeks for large systems",
                "Project closure: lessons learned, documentation update, knowledge transfer",
            ]),
        ]

        for phase_title, phase_steps in phases:
            with st.expander(phase_title, expanded=True):
                for i, step in enumerate(phase_steps, 1):
                    st.markdown(
                        f'<div class="step-card">'
                        f'<div class="step-num">{i}</div>'
                        f'<div style="line-height:1.65">{step}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        # AI enhanced plan
        st.markdown("---")
        st.markdown("#### 🤖 AI-Enhanced Recommendations")
        st.markdown(
            f'<div class="answer-box">{ai_plan}</div>',
            unsafe_allow_html=True,
        )

        # Key SAP Notes section
        st.markdown("---")
        st.markdown("#### 📋 Key SAP Notes for This Upgrade")
        key_notes = [
            ("2568780",  "SUM (Software Update Manager) Master Note"),
            ("2913617",  "SAP Readiness Check for S/4HANA"),
            ("2399707",  "S/4HANA Technical Prerequisites"),
            ("2383326",  "SAP Maintenance Planner supported scenarios"),
            ("2186744",  "Pre-upgrade checklist and minimum SP levels"),
            ("2176227",  "Disk space requirements for SUM workspace"),
            ("2622660",  "SUM best practices and recommendations"),
            ("1680045",  "Installation and upgrade best practices"),
            ("941735",   "Memory management parameters"),
            ("900929",   "OS kernel parameters for SAP on Linux"),
            ("2190420",  "Custom Code Migration — SCMA / ATC"),
            ("1979523",  "Software Lifecycle Platform overview"),
        ]
        note_cols = st.columns(3)
        for i, (note_num, note_desc) in enumerate(key_notes):
            with note_cols[i % 3]:
                st.markdown(
                    f'<div class="source-card" style="padding:.6rem 1rem">'
                    f'<a href="https://launchpad.support.sap.com/#/notes/{note_num}" '
                    f'target="_blank">📋 SAP Note {note_num}</a><br>'
                    f'<small style="color:#374151">{note_desc}</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # Save to conversation
        st.session_state.conversation.append({
            "question": upgrade_q,
            "answer":   ai_plan,
            "sources":  [],
            "product":  f"{src_release} → {tgt_release}",
        })

# ============================================================
# 4  UPGRADE MATRIX
# ============================================================
def tab_upgrade_matrix():
    st.markdown("### 🔄 SAP Upgrade Path Matrix")
    st.markdown(
        '<div class="info-box">📊 Select your source release to see all supported '
        'upgrade target versions, upgrade type, required tool, mandatory intermediate '
        'stops, and the key SAP Note reference for each path.</div>',
        unsafe_allow_html=True,
    )

    source_options = list(UPGRADE_PATHS.keys())
    selected_source = st.selectbox(
        "Select your current (source) release",
        source_options,
        key="matrix_source",
    )

    if selected_source not in UPGRADE_PATHS:
        return

    targets = UPGRADE_PATHS[selected_source]
    st.markdown(
        f"#### {len(targets)} supported upgrade target(s) from **{selected_source}**"
    )

    # Color map for upgrade types
    type_colors = {
        "System Conversion": "#fee2e2",
        "Release Upgrade":   "#e0f2fe",
        "EHP Upgrade":       "#f0fdf4",
        "Database Upgrade":  "#fef3c7",
        "Revision Upgrade":  "#f5f3ff",
    }

    # Build HTML table
    rows_html = ""
    for tgt, info in targets.items():
        stops_html = (
            " → ".join(
                f'<span style="background:#fef3c7;padding:2px 8px;border-radius:4px;'
                f'font-size:.78rem">{s}</span>'
                for s in info["stops"]
            )
            if info["stops"]
            else '<span style="color:#16a34a;font-weight:600">✅ Direct upgrade</span>'
        )
        note_html = (
            f'<a href="https://launchpad.support.sap.com/#/notes/{info["note"]}" '
            f'target="_blank">📋 {info["note"]}</a>'
        ) if info.get("note") else "—"
        type_bg = type_colors.get(info["type"], "#f8fafc")
        rows_html += (
            f'<tr>'
            f'<td style="padding:8px 14px;border:1px solid #e5e7eb;font-weight:600;'
            f'color:#0057A8">{tgt}</td>'
            f'<td style="padding:8px 14px;border:1px solid #e5e7eb;background:{type_bg}">'
            f'{info["type"]}</td>'
            f'<td style="padding:8px 14px;border:1px solid #e5e7eb;font-family:monospace;'
            f'font-size:.88rem">{info["tool"]}</td>'
            f'<td style="padding:8px 14px;border:1px solid #e5e7eb">{stops_html}</td>'
            f'<td style="padding:8px 14px;border:1px solid #e5e7eb">{note_html}</td>'
            f'</tr>'
        )

    st.markdown(
        f'<table style="width:100%;border-collapse:collapse;font-size:.875rem">'
        f'<thead><tr style="background:#0057A8;color:#fff">'
        f'<th style="padding:9px 14px;text-align:left">Target Release</th>'
        f'<th style="padding:9px 14px;text-align:left">Upgrade Type</th>'
        f'<th style="padding:9px 14px;text-align:left">Tool</th>'
        f'<th style="padding:9px 14px;text-align:left">Required Stops</th>'
        f'<th style="padding:9px 14px;text-align:left">Key SAP Note</th>'
        f'</tr></thead><tbody>{rows_html}</tbody></table>',
        unsafe_allow_html=True,
    )

    # Color legend
    st.markdown("<br>**Legend — Upgrade Types:**", unsafe_allow_html=True)
    leg_cols = st.columns(len(type_colors))
    for i, (utype, ucolor) in enumerate(type_colors.items()):
        with leg_cols[i]:
            st.markdown(
                f'<div style="background:{ucolor};border-radius:6px;padding:.3rem .6rem;'
                f'font-size:.78rem;font-weight:600;text-align:center;'
                f'border:1px solid #e5e7eb">{utype}</div>',
                unsafe_allow_html=True,
            )

    # Compatibility checker
    st.markdown("---")
    st.markdown("#### 🔍 Quick Compatibility Validator")
    st.markdown(
        '<div class="info-box">Check for blocking compatibility issues '
        'before starting your upgrade project.</div>',
        unsafe_allow_html=True,
    )
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        chk_db  = st.selectbox("Target Database",
                                ["SAP HANA", "Oracle", "MS SQL Server", "IBM DB2"],
                                key="chk_db")
    with cc2:
        chk_os  = st.selectbox("OS Platform",
                                ["Linux RHEL 8", "Linux RHEL 9", "Linux SLES 15",
                                 "Windows Server 2019", "Windows Server 2022"],
                                key="chk_os")
    with cc3:
        chk_tgt = st.selectbox("Target Release",
                                list(targets.keys()),
                                key="chk_tgt")

    if st.button("🔍 Check Compatibility", use_container_width=True):
        errors, warnings, infos = [], [], []

        # DB compatibility checks
        if "s/4hana" in chk_tgt.lower() and "hana" not in chk_db.lower():
            errors.append(
                f"SAP S/4HANA requires SAP HANA database. "
                f"You selected: {chk_db}. This is a hard blocker."
            )
        if "windows" in chk_os.lower() and "hana" in chk_db.lower():
            errors.append(
                "SAP HANA is NOT supported on Windows Server. "
                "Use Linux (RHEL 8/9 or SLES 15)."
            )
        if "2019" in chk_os and "hana" in chk_db.lower():
            warnings.append(
                "Windows Server 2019 is not supported for SAP HANA. "
                "Switch to RHEL or SLES."
            )
        if ("ecc" in selected_source.lower() or "erp" in selected_source.lower()):
            infos.append(
                "ECC → S/4HANA requires Simplification Item check "
                "(SAP Note 2121861)."
            )
            infos.append(
                "Unicode conversion required if source system is "
                "non-Unicode (SAP Note 73606)."
            )
            infos.append(
                "Run SAP Readiness Check (/SDF/RC_START_CHECK) on the "
                "source system before starting."
            )
        if "hana 1.0" in selected_source.lower():
            warnings.append(
                "HANA 1.0 → 2.0 requires careful revision path planning. "
                "Review SAP Note 2380493."
            )

        # Display results
        for e in errors:
            st.markdown(
                f'<div class="error-box">❌ <strong>BLOCKER:</strong> {e}</div>',
                unsafe_allow_html=True,
            )
        for w in warnings:
            st.markdown(
                f'<div class="warn-box">⚠️ <strong>WARNING:</strong> {w}</div>',
                unsafe_allow_html=True,
            )
        for i in infos:
            st.markdown(
                f'<div class="info-box">ℹ️ {i}</div>',
                unsafe_allow_html=True,
            )
        if not errors and not warnings:
            st.markdown(
                '<div class="success-box">✅ <strong>No immediate blocking '
                'compatibility issues detected.</strong> Proceed with a full '
                'SAP Readiness Check on your actual system to confirm.</div>',
                unsafe_allow_html=True,
            )

# ============================================================
# 5 — PARAMETERS
# ============================================================
def tab_parameters():
    st.markdown("### ⚙️ SAP Parameter Recommendation Engine")
    st.markdown(
        '<div class="info-box">⚙️ Select your product and system specifications '
        'to get dynamically sized parameter recommendations with SAP Note '
        'references. Download as a ready-to-use profile snippet.</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        param_prod = st.selectbox(
            "SAP Product",
            list(PARAMETER_DATABASE.keys()),
            key="param_prod",
        )
    with col2:
        cats = list(PARAMETER_DATABASE.get(param_prod, {}).keys())
        param_cat = st.selectbox("Category", cats, key="param_cat") if cats else None
    with col3:
        param_os = st.selectbox(
            "OS Platform (optional)",
            ["None"] + list(OS_PARAMETERS.keys()),
            key="param_os",
        )

    s1, s2, s3 = st.columns(3)
    with s1:
        ram_gb   = st.number_input("Total RAM (GB)",    min_value=16,  max_value=65536, value=256, step=16,  key="p_ram")
    with s2:
        n_users  = st.number_input("Concurrent Users",  min_value=1,   max_value=50000, value=200, step=50,  key="p_usr")
    with s3:
        n_cpu    = st.number_input("CPU Cores",         min_value=1,   max_value=512,   value=32,  step=4,   key="p_cpu")

    if st.button("⚙️ Generate Parameter Recommendations",
                 type="primary", use_container_width=True):```python
        params = PARAMETER_DATABASE.get(param_prod, {}).get(param_cat, {})

        if params:
            st.markdown(f"#### ⚙️ {param_prod} — {(param_cat or '').title()} Parameters")
            st.caption(
                f"Sized for: {ram_gb} GB RAM · {n_cpu} CPU cores · {n_users} concurrent users"
            )

            table_rows = ""
            snippet_lines = [
                f"# {param_prod} — {param_cat} Parameters",
                f"# Sized for: {ram_gb} GB RAM | {n_cpu} CPUs | {n_users} concurrent users",
                f"# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                f"# Reference: SAP Help Navigator Pro",
                "",
            ]

            for idx, (pname, pdata) in enumerate(params.items()):
                value = pdata["value"]
                unit  = pdata.get("unit", "")

                # Dynamic sizing calculations
                if "heap_area_total" in pname:
                    value = str(int(ram_gb * 0.30 * 1024 * 1024 * 1024))
                elif "heap_area_dia" in pname:
                    value = str(int(ram_gb * 0.05 * 1024 * 1024 * 1024))
                elif "heap_area_nondia" in pname:
                    value = str(int(ram_gb * 0.10 * 1024 * 1024 * 1024))
                elif "em/initial_size_MB" in pname:
                    value = str(max(2048, int(ram_gb * 0.10)))
                elif "em/max_size_MB" in pname:
                    value = str(max(4096, int(ram_gb * 0.25)))
                elif "ztta/roll_extension" in pname:
                    value = str(int(ram_gb * 0.08 * 1024 * 1024 * 1024))
                elif "wp_no_dia" in pname:
                    value = str(max(6, min(n_users // 20, 80)))
                elif "wp_no_btc" in pname:
                    value = str(max(2, n_cpu // 8))
                elif "wp_no_spo" in pname:
                    value = str(max(1, n_cpu // 16))
                elif "wp_no_upd" in pname and "upd2" not in pname:
                    value = str(max(2, n_cpu // 16))
                elif "icm/max_conn" in pname:
                    value = str(max(200, n_users * 3))
                elif "enque/table_size" in pname:
                    value = str(max(4194304, n_users * 1024))
                elif "global_allocation_limit" in pname and param_prod == "SAP HANA":
                    value = str(int(ram_gb * 0.80 * 1024))
                    unit  = "MB"
                elif "shared_objects_size_MB" in pname:
                    value = str(max(256, int(ram_gb * 0.02 * 1024)))

                note_html = (
                    f'<a href="https://launchpad.support.sap.com/#/notes/{pdata["note"]}" '
                    f'target="_blank" style="font-size:.82rem">📋 {pdata["note"]}</a>'
                ) if pdata.get("note") else "—"

                row_bg = "#f8fafc" if idx % 2 == 0 else "#ffffff"
                table_rows += (
                    f'<tr style="background:{row_bg}">'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;font-family:monospace;'
                    f'color:#0057A8;font-size:.84rem">{pname}</td>'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;font-family:monospace;'
                    f'font-weight:700;font-size:.84rem">{value}</td>'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;color:#6b7280;'
                    f'font-size:.82rem">{unit}</td>'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;'
                    f'font-size:.84rem">{pdata.get("desc", "")}</td>'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb">{note_html}</td>'
                    f'</tr>'
                )
                snippet_lines.append(
                    f"{pname:<45} = {value:<20}  # {pdata.get('desc', '')}"
                )

            st.markdown(
                f'<table class="param-table">'
                f'<thead><tr>'
                f'<th>Parameter Name</th>'
                f'<th>Recommended Value</th>'
                f'<th>Unit</th>'
                f'<th>Description</th>'
                f'<th>SAP Note</th>'
                f'</tr></thead>'
                f'<tbody>{table_rows}</tbody>'
                f'</table>',
                unsafe_allow_html=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="⬇️ Download as Profile Snippet (.txt)",
                data="\n".join(snippet_lines),
                file_name=(
                    f"sap_params_{param_prod.replace(' ', '_')}_"
                    f"{param_cat}_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
                ),
                mime="text/plain",
                use_container_width=True,
            )

        # OS Parameters section
        if param_os != "None":
            st.markdown(f"---\n#### 🐧 OS Kernel Parameters — {param_os}")
            st.caption(
                f"Calculated for: {ram_gb} GB RAM · {n_cpu} CPU cores"
            )
            os_params = OS_PARAMETERS.get(param_os, {})
            os_rows  = ""
            sysctl_lines = [
                f"# /etc/sysctl.conf — SAP recommended OS kernel parameters",
                f"# Platform: {param_os}",
                f"# System: {ram_gb} GB RAM | {n_cpu} CPUs | {n_users} users",
                f"# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                f"# Apply with: sysctl -p /etc/sysctl.conf",
                "",
            ]

            for idx, (pname, pdata) in enumerate(os_params.items()):
                val = pdata["value"]
                if "shmmax" in pname:
                    val = str(int(ram_gb * 1024 * 1024 * 1024))
                elif "shmall" in pname:
                    val = str(int(ram_gb * 1024 * 1024 * 1024 // 4096))

                note_html = (
                    f'<a href="https://launchpad.support.sap.com/#/notes/{pdata["note"]}" '
                    f'target="_blank" style="font-size:.82rem">📋 {pdata["note"]}</a>'
                ) if pdata.get("note") else "—"

                row_bg = "#f8fafc" if idx % 2 == 0 else "#ffffff"
                os_rows += (
                    f'<tr style="background:{row_bg}">'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;font-family:monospace;'
                    f'color:#374151;font-size:.84rem">{pname}</td>'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;font-family:monospace;'
                    f'font-weight:700;font-size:.84rem">{val}</td>'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;'
                    f'font-size:.84rem">{pdata.get("desc", "")}</td>'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb">{note_html}</td>'
                    f'</tr>'
                )
                sysctl_lines.append(
                    f"{pname:<45} = {val:<20}  # {pdata.get('desc', '')}"
                )

            st.markdown(
                f'<table style="width:100%;border-collapse:collapse;font-size:.875rem">'
                f'<thead><tr style="background:#374151;color:#fff">'
                f'<th style="padding:9px 14px;text-align:left">Parameter</th>'
                f'<th style="padding:9px 14px;text-align:left">Value</th>'
                f'<th style="padding:9px 14px;text-align:left">Description</th>'
                f'<th style="padding:9px 14px;text-align:left">SAP Note</th>'
                f'</tr></thead><tbody>{os_rows}</tbody></table>',
                unsafe_allow_html=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="⬇️ Download sysctl.conf Snippet",
                data="\n".join(sysctl_lines),
                file_name=(
                    f"sysctl_sap_{param_os.replace(' ', '_').replace('/', '_')}_"
                    f"{datetime.datetime.now().strftime('%Y%m%d')}.conf"
                ),
                mime="text/plain",
                use_container_width=True,
            )

        if not params and param_os == "None":
            st.markdown(
                '<div class="warn-box">⚠️ Please select a parameter category '
                'or an OS platform to generate recommendations.</div>',
                unsafe_allow_html=True,
            )

# ============================================================
# 6 — CHECKLIST
# ============================================================
def tab_checklist_ui():
    st.markdown("### ✅ Pre-Upgrade Checklist Generator")
    st.markdown(
        '<div class="info-box">📋 Generate a complete, prioritized pre-upgrade '
        'checklist tailored to your specific upgrade scenario. '
        'Download as CSV to use in Excel or your project management tool.</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        cl_src = st.text_input(
            "Source Release",
            value="SAP ECC 6.0 EHP8",
            key="cl_src",
        )
        cl_tgt = st.text_input(
            "Target Release",
            value="SAP S/4HANA 2023",
            key="cl_tgt",
        )
    with col2:
        cl_cc = st.checkbox("Has Custom Code / Z-Developments", value=True,  key="cl_cc")
        cl_if = st.checkbox("Has Interface Connections",        value=True,  key="cl_if")
        cl_ha = st.checkbox("High Availability Required",       value=False, key="cl_ha")
        cl_uc = st.checkbox("Non-Unicode System",               value=False, key="cl_uc")

    if st.button("📋 Generate Checklist", type="primary", use_container_width=True):
        opts = {
            "has_custom_code": cl_cc,
            "has_interfaces":  cl_if,
            "ha_required":     cl_ha,
            "non_unicode":     cl_uc,
        }
        checklist = generate_checklist(cl_src, cl_tgt, opts)
        st.session_state.last_checklist = checklist

        # Summary metrics
        total    = len(checklist)
        critical = sum(1 for x in checklist if x["pri"] == "Critical")
        high     = sum(1 for x in checklist if x["pri"] == "High")
        medium   = sum(1 for x in checklist if x["pri"] == "Medium")

        st.markdown(f"---\n#### 📋 {cl_src} → {cl_tgt} — Pre-Upgrade Checklist")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(
                f'<div class="metric-card"><div class="value">{total}</div>'
                f'<div class="label">Total Items</div></div>',
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="value" style="color:#dc2626">{critical}</div>'
                f'<div class="label">🔴 Critical</div></div>',
                unsafe_allow_html=True,
            )
        with m3:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="value" style="color:#d97706">{high}</div>'
                f'<div class="label">🟡 High</div></div>',
                unsafe_allow_html=True,
            )
        with m4:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="value" style="color:#2563eb">{medium}</div>'
                f'<div class="label">🔵 Medium</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Group items by category and render
        grouped = defaultdict(list)
        for item in checklist:
            grouped[item["cat"]].append(item)

        for cat_name, cat_items in grouped.items():
            cat_icon = cat_items[0].get("icon", "📌")
            with st.expander(
                f"{cat_icon} {cat_name} ({len(cat_items)} items)",
                expanded=True,
            ):
                for item in cat_items:
                    pri = item["pri"]
                    bg_color     = {"Critical": "#fee2e2", "High": "#fef3c7"}.get(pri, "#f0fdf4")
                    border_color = {"Critical": "#dc2626", "High": "#d97706"}.get(pri, "#2563eb")
                    badge_class  = {"Critical": "critical-badge", "High": "high-badge"}.get(
                        pri, "medium-badge"
                    )
                    note_link = (
                        f' &nbsp;·&nbsp; 🔗 <a href="https://launchpad.support.sap.com'
                        f'/#/notes/{item["note"]}" target="_blank">'
                        f'SAP Note {item["note"]}</a>'
                    ) if item.get("note") else ""

                    st.markdown(
                        f'<div style="background:{bg_color};border-left:4px solid {border_color};'
                        f'border-radius:8px;padding:.75rem 1rem;margin:.4rem 0">'
                        f'<strong>{item["task"]}</strong> '
                        f'<span class="{badge_class}">{pri}</span><br>'
                        f'<small style="color:#374151">{item["detail"]}</small><br>'
                        f'<small style="color:#6b7280">'
                        f'🔧 <em>{item["tool"]}</em>{note_link}'
                        f'</small>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        # CSV export
        csv_lines = [
            "Priority,Category,Task,Detail,Tool / Transaction,SAP Note"
        ]
        for item in checklist:
            csv_lines.append(
                f'"{item["pri"]}","{item["cat"]}","{item["task"]}",'
                f'"{item["detail"]}","{item["tool"]}","{item.get("note", "")}"'
            )

        st.download_button(
            label="⬇️ Download Checklist as CSV",
            data="\n".join(csv_lines),
            file_name=(
                f"sap_upgrade_checklist_"
                f"{cl_src.replace(' ', '_')}_to_"
                f"{cl_tgt.replace(' ', '_')}_"
                f"{datetime.datetime.now().strftime('%Y%m%d')}.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )

# ============================================================
# 7 — CONVERSATION HISTORY
# ============================================================
def tab_conversation():
    st.markdown("### 💬 Conversation History")
    st.markdown(
        '<div class="info-box">All questions and answers from this session are saved here. '
        'Use the Reports to export them as a formatted HTML report.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.conversation:
        st.markdown(
            '<div class="info-box">💬 No conversations yet. '
            'Use the Search & Ask to get started.</div>',
            unsafe_allow_html=True,
        )
        return

    col_info, col_clear = st.columns([4, 1])
    with col_info:
        st.markdown(
            f"**{len(st.session_state.conversation)} Q&A pair(s) in this session**"
        )
    with col_clear:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.conversation = []
            st.rerun()

    for i, entry in enumerate(reversed(st.session_state.conversation)):
        idx = len(st.session_state.conversation) - i
        product_badge = (
            f' <span class="chip">{entry.get("product", "SAP")}</span>'
            if entry.get("product") else ""
        )
        q_preview = entry["question"][:80]
        with st.expander(
            f"Q{idx}: {q_preview}{'…' if len(entry['question']) > 80 else ''}",
            expanded=(i == 0),
        ):
            st.markdown(
                f'**❓ Question:** {entry["question"]}{product_badge}',
                unsafe_allow_html=True,
            )
            st.markdown("**💡 Answer:**")
            st.markdown(
                f'<div class="answer-box">{entry["answer"]}</div>',
                unsafe_allow_html=True,
            )
            if entry.get("sources"):
                st.markdown("**🔗 Sources:**")
                for src in entry["sources"][:3]:
                    st.markdown(
                        f'<div class="source-card">'
                        f'<a href="{src["url"]}" target="_blank">📄 {src["title"]}</a>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

# ============================================================
# 8 — REPORTS
# ============================================================
def tab_reports():
    st.markdown("### 📄 Export Reports & Session Data")
    st.markdown(
        '<div class="info-box">📄 Generate a self-contained, print-ready HTML report '
        'combining your Q&A, pre-upgrade checklist, and source references. '
        'Also export the full session as JSON.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.conversation:
        st.markdown(
            '<div class="warn-box">⚠️ No Q&A data yet. '
            'Use the Search & Ask to ask questions first, '
            'then return here to generate your report.</div>',
            unsafe_allow_html=True,
        )
        return

    last_qa = st.session_state.conversation[-1]

    # Session summary cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="metric-card"><div class="value">'
            f'{len(st.session_state.conversation)}</div>'
            f'<div class="label">💬 Q&A Pairs</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="metric-card"><div class="value">'
            f'{len(st.session_state.fetched_docs)}</div>'
            f'<div class="label">📄 Docs Fetched</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        cl_count = len(st.session_state.get("last_checklist", []))
        st.markdown(
            f'<div class="metric-card"><div class="value">{cl_count}</div>'
            f'<div class="label">✅ Checklist Items</div></div>',
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f'<div class="metric-card"><div class="value">'
            f'{len(st.session_state.search_history)}</div>'
            f'<div class="label">🔍 Searches</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # HTML Report options
    st.markdown("#### 📄 HTML Report")
    rpt_col1, rpt_col2 = st.columns(2)
    with rpt_col1:
        include_checklist = st.checkbox(
            "Include pre-upgrade checklist in report",
            value=bool(st.session_state.get("last_checklist")),
            key="rpt_incl_cl",
        )
    with rpt_col2:
        use_all_qa = st.checkbox(
            "Include all Q&A pairs (unchecked = last Q&A only)",
            value=False,
            key="rpt_all_qa",
        )

    # Determine which Q&A entries to include
    qa_entries = st.session_state.conversation if use_all_qa else [last_qa]

    # Build combined question and answer strings
    if use_all_qa and len(qa_entries) > 1:
        combined_question = f"{len(qa_entries)} questions — see report for full list"
        combined_answer   = "\n\n---\n\n".join(
            f"**Q{i+1}: {e['question']}**\n\n{e['answer']}"
            for i, e in enumerate(qa_entries)
        )
    else:
        combined_question = last_qa["question"]
        combined_answer   = last_qa["answer"]

    # Deduplicated sources
    combined_sources = []
    seen_urls = set()
    for entry in qa_entries:
        for src in entry.get("sources", []):
            if src["url"] not in seen_urls:
                seen_urls.add(src["url"])
                combined_sources.append(src)

    if st.button("📄 Generate & Download HTML Report",
                 type="primary", use_container_width=True):
        checklist_data = (
            st.session_state.get("last_checklist", [])
            if include_checklist else []
        )
        html_content = generate_html_report(
            product   = last_qa.get("product", "SAP"),
            question  = combined_question,
            answer    = combined_answer,
            sources   = combined_sources[:15],
            checklist = checklist_data,
        )
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SAP_Help_Navigator_Report_{ts}.html"

        st.download_button(
            label     = f"⬇️ Download {filename}",
            data      = html_content,
            file_name = filename,
            mime      = "text/html",
            use_container_width=True,
        )
        with st.expander("👁️ Preview Report"):
            st.components.v1.html(html_content, height=550, scrolling=True)

    # JSON and CSV exports
    st.markdown("---")
    st.markdown("#### 📦 Export Session Data")
    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        if st.button("📦 Export Full Session as JSON", use_container_width=True):
            session_data = {
                "exported_at":    datetime.datetime.now().isoformat(),
                "product":        st.session_state.current_product,
                "total_qa_pairs": len(st.session_state.conversation),
                "conversation":   st.session_state.conversation,
                "search_history": st.session_state.search_history,
                "checklist":      st.session_state.get("last_checklist", []),
                "docs_fetched":   list(st.session_state.fetched_docs.keys()),
            }
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label     = "⬇️ Download session.json",
                data      = json.dumps(session_data, indent=2, default=str),
                file_name = f"sap_navigator_session_{ts}.json",
                mime      = "application/json",
                use_container_width=True,
            )

    with exp_col2:
        checklist_available = bool(st.session_state.get("last_checklist"))
        if st.button("📋 Export Checklist as CSV",
                     use_container_width=True,
                     disabled=not checklist_available):
            cl = st.session_state.get("last_checklist", [])
            csv_lines = ["Priority,Category,Task,Detail,Tool / Transaction,SAP Note"]
            for item in cl:
                csv_lines.append(
                    f'"{item["pri"]}","{item["cat"]}","{item["task"]}",'
                    f'"{item["detail"]}","{item["tool"]}","{item.get("note", "")}"'
                )
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label     = "⬇️ Download checklist.csv",
                data      = "\n".join(csv_lines),
                file_name = f"sap_upgrade_checklist_{ts}.csv",
                mime      = "text/csv",
                use_container_width=True,
            )

# ============================================================
# 9 — RESOURCES
# ============================================================
def tab_resources():
    st.markdown("### 📚 SAP Resource Library")
    st.markdown(
        '<div class="info-box">🔗 Curated collection of official SAP portals, '
        'essential SAP Notes organized by topic, and a guide finder tool '
        'to locate the exact documentation you need.</div>',
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 🔗 Official SAP Portals")
        portals = [
            ("🔷 SAP Help Portal",               "https://help.sap.com/docs",
             "All SAP product documentation — publicly accessible"),
            ("🛠️ SAP Support Portal",             "https://support.sap.com",
             "Support cases, SAP Notes, EarlyWatch Alert"),
            ("⬇️ SAP Software Download Center",  "https://support.sap.com/swdc",
             "Download SAP software, patches, SUM, SWPM"),
            ("📦 SAP Maintenance Planner",        "https://support.sap.com/mp",
             "Generate Stack.xml for system upgrades"),
            ("📊 Product Availability Matrix",    "https://apps.support.sap.com/sap/support/pam",
             "OS, database, and component compatibility"),
            ("🎓 SAP Learning Hub",               "https://learning.sap.com",
             "Official SAP training courses and certifications"),
            ("🌍 SAP Community",                  "https://community.sap.com",
             "Q&A, technical blogs, and discussions"),
            ("🚀 SAP Best Practices Explorer",    "https://rapid.sap.com/bp/",
             "Pre-built best practice content for S/4HANA"),
            ("🔑 SAP Launchpad (Notes / KBAs)",   "https://launchpad.support.sap.com",
             "SAP Notes, KBAs, system information"),
            ("📱 SAP Fiori Apps Library",         "https://fioriappslibrary.hana.ondemand.com",
             "Browse 2000+ SAP Fiori application details"),
            ("📐 SAP Quick Sizer",                "https://service.sap.com/quicksizer",
             "Hardware sizing estimation tool"),
            ("🔒 SAP Trust Center",               "https://www.sap.com/about/trust-center.html",
             "Security, compliance, and data privacy"),
        ]
        for name, url, desc in portals:
            st.markdown(
                f'<div class="source-card">'
                f'<a href="{url}" target="_blank">{name}</a><br>'
                f'<small style="color:#6b7280">{desc}</small><br>'
                f'<small style="color:#94a3b8">{url}</small>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_right:
        st.markdown("#### 📋 Essential SAP Notes by Topic")
        notes_by_topic = {
            "🔄 Upgrade & Migration": [
                ("2568780",  "SUM — Software Update Manager master note"),
                ("2913617",  "SAP Readiness Check for S/4HANA"),
                ("2399707",  "S/4HANA technical prerequisites"),
                ("2383326",  "SAP Maintenance Planner supported scenarios"),
                ("2186744",  "Pre-upgrade checklist and minimum SP levels"),
                ("2176227",  "Disk space requirements for SUM workspace"),
                ("2622660",  "SUM best practices and recommendations"),
                ("2121861",  "Simplification Items for S/4HANA"),
                ("73606",    "Unicode conversion for SAP systems"),
            ],
            "💾 Installation": [
                ("1680045",  "Installation best practices"),
                ("2393060",  "sapinst / SWPM troubleshooting"),
                ("1979523",  "Software Lifecycle Platform overview"),
                ("2235581",  "SAP HANA installation on Linux"),
                ("1639498",  "How to download SAP software"),
            ],
            "⚙️ Performance & Parameters": [
                ("941735",   "ABAP memory management parameters"),
                ("2222200",  "Recommended SAP HANA settings"),
                ("1984787",  "OS kernel parameters for SAP on Linux"),
                ("1999997",  "SAP HANA memory configuration FAQ"),
                ("103747",   "ABAP buffer tuning guidelines"),
                ("15360",    "Work process runtime parameters"),
                ("900929",   "OS parameters: vm.max_map_count etc."),
            ],
            "🛡️ Security": [
                ("1484000",  "SAP Security Guide overview"),
                ("862989",   "Login and password profile parameters"),
                ("1408081",  "RFC security — authority checks"),
                ("539404",   "Security Audit Log configuration"),
                ("68048",    "Default SAP* and DDIC password handling"),
                ("2216823",  "Security hardening recommendations"),
            ],
            "🗄️ SAP HANA": [
                ("2380493",  "SAP HANA upgrade paths and revisions"),
                ("1999993",  "SAP HANA Mini Checks (run monthly)"),
                ("2084065",  "HANA delta merge optimization"),
                ("2127458",  "HANA column store memory unload settings"),
                ("1975256",  "HANA backup buffer configuration"),
                ("1999880",  "HANA System Replication overview"),
            ],
        }

        for topic, notes in notes_by_topic.items():
            st.markdown(f"**{topic}**")
            for note_num, note_desc in notes:
                st.markdown(
                    f'<div class="source-card" style="padding:.5rem 1rem;margin:.2rem 0">'
                    f'<a href="https://launchpad.support.sap.com/#/notes/{note_num}" '
                    f'target="_blank">📋 SAP Note {note_num}</a>'
                    f' — {note_desc}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("")

    # Guide Finder
    st.markdown("---")
    st.markdown("#### 📥 SAP Guide Finder")
    st.markdown(
        '<div class="info-box">Search for specific SAP guide types '
        '(Installation, Upgrade, Security, etc.) for any SAP product.</div>',
        unsafe_allow_html=True,
    )

    gf1, gf2, gf3 = st.columns([2, 2, 1])
    with gf1:
        gf_product = st.selectbox(
            "Product",
            ["SAP S/4HANA", "SAP HANA", "SAP BTP",
             "SAP NetWeaver", "SAP Solution Manager",
             "SAP Fiori", "SAP ABAP Platform",
             "SAP BW/4HANA", "SAP Integration Suite"],
            key="gf_prod",
        )
    with gf2:
        gf_type = st.selectbox(
            "Guide Type",
            ["Master Guide", "Installation Guide", "Upgrade Guide",
             "Security Guide", "Administration Guide",
             "Operations Guide", "High Availability Guide",
             "Sizing Guide", "Tuning Guide", "Release Notes"],
            key="gf_type",
        )
    with gf3:
        st.markdown("<br>", unsafe_allow_html=True)
        gf_search = st.button("🔍 Find Guides", use_container_width=True)

    if gf_search:
        search_query = f"{gf_product} {gf_type}"
        with st.spinner(f"Searching for '{search_query}'…"):
            guide_results = search_sap_help(search_query, gf_product)
        if guide_results:
            st.markdown(f"**Results for '{search_query}':**")
            for gr in guide_results[:6]:
                st.markdown(
                    f'<div class="source-card">'
                    f'<a href="{gr["url"]}" target="_blank">📄 {gr["title"]}</a><br>'
                    f'<small style="color:#6b7280">'
                    f'{gr.get("description", "")[:110]}'
                    f'</small><br>'
                    f'<small style="color:#94a3b8">{gr["url"][:70]}</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info(
                f"No specific results found for '{search_query}'. "
                f"Try browsing [help.sap.com/docs](https://help.sap.com/docs) directly."
            )

# ============================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================
def main():
    render_header()
    render_sidebar()

    product = st.session_state.current_product

    # Top metrics row
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    with mc1:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="value">{len(st.session_state.fetched_docs)}</div>'
            f'<div class="label">📄 Docs Fetched</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with mc2:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="value">{len(st.session_state.conversation)}</div>'
            f'<div class="label">💬 Q&A Pairs</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with mc3:
        display_product = (
            (product[:13] + "…") if product and len(product) > 13
            else (product or "—")
        )
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="value" style="font-size:.88rem">{display_product}</div>'
            f'<div class="label">📦 Product</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with mc4:
        mode_label = "🤖 Gemini AI" if st.session_state.api_key else "📐 Rule-based"
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="value" style="font-size:.85rem">{mode_label}</div>'
            f'<div class="label">Answer Mode</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with mc5:
        cl_count = len(st.session_state.get("last_checklist", []))
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="value">{cl_count}</div>'
            f'<div class="label">✅ Checklist Items</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # All 9 tabs
    (t1, t2, t3, t4, t5,
     t6, t7, t8, t9) = st.tabs([
        "🔍 Search & Ask",
        "📄 Document Viewer",
        "📋 Upgrade Planner",
        "🔄 Upgrade Matrix",
        "⚙️ Parameters",
        "✅ Checklist",
        "💬 Conversation",
        "📄 Reports",
        "📚 Resources",
    ])

    with t1:
        tab_search_and_ask(product)
    with t2:
        tab_document_viewer(product)
    with t3:
        tab_upgrade_planner(product)
    with t4:
        tab_upgrade_matrix()
    with t5:
        tab_parameters()
    with t6:
        tab_checklist_ui()
    with t7:
        tab_conversation()
    with t8:
        tab_reports()
    with t9:
        tab_resources()


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    main()

