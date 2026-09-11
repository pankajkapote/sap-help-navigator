# ============================================================
# PART 1 OF 6 — Config, CSS, Constants, Session State
# SAP Help Navigator Pro
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
# PAGE CONFIG — must be FIRST Streamlit call
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
  box-shadow:0 2px 8px rgba(0,0,0,.06);
  transition:transform .2s,box-shadow .2s}
.metric-card:hover{transform:translateY(-3px);
  box-shadow:0 6px 20px rgba(0,0,0,.1)}
.metric-card .value{font-size:1.7rem;font-weight:700;color:#0057A8}
.metric-card .label{font-size:.78rem;color:#6b7280;margin-top:.3rem}

.answer-box{
  background:linear-gradient(135deg,#f0f7ff,#e8f5e9);
  border-left:4px solid #0057A8;border-radius:12px;
  padding:1.4rem 1.8rem;margin:1rem 0;line-height:1.8}

.source-card{
  background:#fff;border:1px solid #dce3ec;border-radius:10px;
  padding:.9rem 1.1rem;margin:.45rem 0;
  box-shadow:0 1px 4px rgba(0,0,0,.05)}
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
  border-radius:20px;padding:.22rem .7rem;
  font-size:.75rem;font-weight:600;margin:.15rem}
.critical-badge{display:inline-block;background:#fee2e2;color:#991b1b;
  border:1px solid #fca5a5;border-radius:6px;
  padding:1px 7px;font-size:.73rem;font-weight:700}
.high-badge{display:inline-block;background:#fef3c7;color:#92400e;
  border:1px solid #fcd34d;border-radius:6px;
  padding:1px 7px;font-size:.73rem;font-weight:700}
.medium-badge{display:inline-block;background:#dbeafe;color:#1e40af;
  border:1px solid #93c5fd;border-radius:6px;
  padding:1px 7px;font-size:.73rem;font-weight:700}

.sidebar-section{background:#f8fafc;border-radius:10px;
  padding:.75rem .9rem;margin-bottom:.9rem;border:1px solid #e2e8f0}

.stButton>button{border-radius:8px!important;
  font-weight:500!important;transition:all .2s!important}
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
    if st.session_state.get("api_key"):
        return st.session_state["api_key"]
    try:
        key = st.secrets.get("gemini_api_key", "")
        if key:
            return key
    except Exception:
        pass
    return ""

if not st.session_state.api_key:
    st.session_state.api_key = load_api_key()

# ============================================================
# PARAMETER DATABASE
# ============================================================
PARAMETER_DATABASE = {
    "SAP S/4HANA": {
        "memory": {
            "abap/heap_area_total":
                {"value":"2000000000","unit":"bytes",
                 "desc":"Total heap memory for all work processes","note":"941735"},
            "abap/heap_area_dia":
                {"value":"500000000","unit":"bytes",
                 "desc":"Heap area per dialog work process","note":"941735"},
            "abap/heap_area_nondia":
                {"value":"1000000000","unit":"bytes",
                 "desc":"Heap area per non-dialog work process","note":"941735"},
            "em/initial_size_MB":
                {"value":"4096","unit":"MB",
                 "desc":"Extended memory initial size","note":"747468"},
            "em/max_size_MB":
                {"value":"16384","unit":"MB",
                 "desc":"Extended memory maximum size","note":"747468"},
            "zcsa/table_buffer_area":
                {"value":"100000000","unit":"bytes",
                 "desc":"Generic table buffer size","note":"1418123"},
            "rsdb/obj/buffersize":
                {"value":"500000","unit":"KB",
                 "desc":"Repository object buffer","note":"1127888"},
            "ipc/shm_psize_40":
                {"value":"500000000","unit":"bytes",
                 "desc":"Shared memory pool size","note":"723909"},
            "abap/buffersize":
                {"value":"600000","unit":"KB",
                 "desc":"ABAP program buffer size","note":"103747"},
            "ztta/roll_extension_dia":
                {"value":"2000000000","unit":"bytes",
                 "desc":"Roll extension for dialog work processes","note":"96098"},
        },
        "workprocesses": {
            "rdisp/wp_no_dia":
                {"value":"10","unit":"count",
                 "desc":"Number of dialog work processes","note":"39412"},
            "rdisp/wp_no_btc":
                {"value":"4","unit":"count",
                 "desc":"Number of background work processes","note":"39412"},
            "rdisp/wp_no_spo":
                {"value":"2","unit":"count",
                 "desc":"Number of spool work processes","note":"39412"},
            "rdisp/wp_no_upd":
                {"value":"2","unit":"count",
                 "desc":"Number of update work processes","note":"39412"},
            "rdisp/wp_no_upd2":
                {"value":"1","unit":"count",
                 "desc":"Number of update-2 work processes","note":"39412"},
            "rdisp/wp_no_enq":
                {"value":"1","unit":"count",
                 "desc":"Number of enqueue work processes","note":"39412"},
            "rdisp/max_wprun_time":
                {"value":"600","unit":"seconds",
                 "desc":"Maximum dialog work process runtime","note":"15360"},
            "rdisp/appc_timeout":
                {"value":"300","unit":"seconds",
                 "desc":"APPC/RFC timeout value","note":""},
        },
        "performance": {
            "rdisp/scheduler/prio_high":
                {"value":"70","unit":"%",
                 "desc":"High priority queue threshold","note":"1515190"},
            "enque/table_size":
                {"value":"8388608","unit":"bytes",
                 "desc":"Enqueue lock table size","note":"185684"},
            "icm/max_conn":
                {"value":"500","unit":"count",
                 "desc":"Maximum ICM connections","note":"1421005"},
            "icm/req_queue_len":
                {"value":"500","unit":"count",
                 "desc":"ICM request queue length","note":"1421005"},
            "icm/keep_alive_timeout":
                {"value":"60","unit":"seconds",
                 "desc":"HTTP keep-alive timeout","note":"1421005"},
            "abap/shared_objects_size_MB":
                {"value":"512","unit":"MB",
                 "desc":"Shared objects memory area","note":"1101726"},
        },
        "security": {
            "login/min_password_lng":
                {"value":"8","unit":"chars",
                 "desc":"Minimum password length","note":"862989"},
            "login/password_expiration_time":
                {"value":"90","unit":"days",
                 "desc":"Password expiry in days","note":"862989"},
            "login/fails_to_session_end":
                {"value":"3","unit":"count",
                 "desc":"Failed logons to end session","note":"862989"},
            "login/fails_to_user_lock":
                {"value":"5","unit":"count",
                 "desc":"Failed logons to lock user","note":"862989"},
            "login/password_change_waittime":
                {"value":"1","unit":"days",
                 "desc":"Min days between password changes","note":"862989"},
            "auth/rfc_authority_check":
                {"value":"1","unit":"flag",
                 "desc":"Enable RFC authority check","note":"1408081"},
            "rec/client":
                {"value":"ALL","unit":"string",
                 "desc":"Security audit log clients","note":"539404"},
            "rsau/enable":
                {"value":"1","unit":"flag",
                 "desc":"Enable security audit log","note":"539404"},
            "login/no_automatic_user_sapstar":
                {"value":"1","unit":"flag",
                 "desc":"Disable SAP* auto-login","note":"68048"},
        },
        "network": {
            "icm/server_port_0":
                {"value":"PROT=HTTP,PORT=8000","unit":"string",
                 "desc":"ICM HTTP port","note":""},
            "icm/server_port_1":
                {"value":"PROT=HTTPS,PORT=44300","unit":"string",
                 "desc":"ICM HTTPS port","note":""},
            "ms/server_port_0":
                {"value":"PROT=HTTP,PORT=8101","unit":"string",
                 "desc":"Message server HTTP port","note":"519018"},
        },
    },
    "SAP HANA": {
        "memory": {
            "global_allocation_limit":
                {"value":"80%_of_RAM","unit":"%",
                 "desc":"HANA global memory allocation limit","note":"1999997"},
            "max_gc_parallelism":
                {"value":"4","unit":"count",
                 "desc":"Garbage collection parallelism","note":"2000000"},
            "parallel_merge_threads":
                {"value":"4","unit":"count",
                 "desc":"Delta merge parallel threads","note":"2084065"},
            "unload_upper_bound":
                {"value":"90","unit":"%",
                 "desc":"Memory threshold for column store unload","note":"2127458"},
            "max_memory_estimation_for_queries":
                {"value":"10737418240","unit":"bytes",
                 "desc":"Per-query memory cap","note":"2222200"},
        },
        "performance": {
            "optimize_compression_goal":
                {"value":"BALANCE","unit":"string",
                 "desc":"Compression optimization goal","note":"2112604"},
            "result_cache_entry_lifetime":
                {"value":"300","unit":"seconds",
                 "desc":"SQL result cache time-to-live","note":"2400005"},
            "joins/optimization_target":
                {"value":"balanced","unit":"string",
                 "desc":"Join optimization strategy","note":"2222200"},
            "tables/use_cs_for_column_compression":
                {"value":"true","unit":"bool",
                 "desc":"Enable column compression","note":"2112604"},
        },
        "backup": {
            "data_backup_buffer_size":
                {"value":"134217728","unit":"bytes",
                 "desc":"Backup I/O buffer size","note":"1975256"},
            "parallel_data_backup_backint_channels":
                {"value":"4","unit":"count",
                 "desc":"Parallel backup channels","note":"1976128"},
            "max_recovery_backint_channels":
                {"value":"4","unit":"count",
                 "desc":"Maximum parallel recovery channels","note":"1976128"},
        },
        "security": {
            "password_layout":
                {"value":"A1a","unit":"string",
                 "desc":"Password complexity requirement","note":""},
            "minimum_password_length":
                {"value":"8","unit":"chars",
                 "desc":"Minimum password length","note":""},
            "password_expire_days":
                {"value":"182","unit":"days",
                 "desc":"Password expiry days","note":""},
        },
    },
    "SAP BTP": {
        "cloud_foundry": {
            "MEMORY":
                {"value":"1024M","unit":"MB",
                 "desc":"App instance memory quota","note":""},
            "INSTANCES":
                {"value":"2","unit":"count",
                 "desc":"Number of app instances","note":""},
            "DISK_QUOTA":
                {"value":"2048M","unit":"MB",
                 "desc":"App disk quota","note":""},
            "HEALTH_CHECK_TYPE":
                {"value":"http","unit":"string",
                 "desc":"App health check method","note":""},
        },
    },
    "SAP NetWeaver": {
        "abap": {
            "abap/buffersize":
                {"value":"600000","unit":"KB",
                 "desc":"ABAP program buffer","note":"103747"},
            "abap/shared_objects_size_MB":
                {"value":"512","unit":"MB",
                 "desc":"Shared objects memory area","note":"1101726"},
            "abap/heap_area_total":
                {"value":"2000000000","unit":"bytes",
                 "desc":"Total heap memory","note":"941735"},
            "abap/use_openssl":
                {"value":"1","unit":"flag",
                 "desc":"Use OpenSSL for RFC encryption","note":"510007"},
        },
        "messaging": {
            "ms/server_port_0":
                {"value":"PROT=HTTP,PORT=8101","unit":"string",
                 "desc":"Message server HTTP port","note":"519018"},
            "ms/max_clients":
                {"value":"500","unit":"count",
                 "desc":"Maximum message server clients","note":""},
        },
    },
}

OS_PARAMETERS = {
    "Linux (RHEL/SLES)": {
        "vm.max_map_count":
            {"value":"2147483647","desc":"Virtual memory map areas","note":"900929"},
        "vm.swappiness":
            {"value":"10","desc":"Kernel swap tendency (low for SAP)","note":"1980196"},
        "kernel.shmmax":
            {"value":"<total_RAM_bytes>","desc":"Maximum shared memory segment","note":"941735"},
        "kernel.shmmni":
            {"value":"32768","desc":"Maximum shared memory identifiers","note":"941735"},
        "kernel.shmall":
            {"value":"1152921504606846975","desc":"Total shared memory pages","note":"941735"},
        "fs.file-max":
            {"value":"20000000","desc":"System-wide open file descriptor max","note":"1984787"},
        "net.core.somaxconn":
            {"value":"4096","desc":"Maximum socket connection backlog","note":"2205917"},
        "net.ipv4.tcp_max_syn_backlog":
            {"value":"8192","desc":"SYN backlog queue depth","note":"2205917"},
        "net.ipv4.tcp_tw_reuse":
            {"value":"1","desc":"Reuse TIME_WAIT sockets","note":"2205917"},
        "net.ipv4.tcp_fin_timeout":
            {"value":"20","desc":"TCP FIN timeout seconds","note":"2205917"},
        "net.ipv4.tcp_keepalive_time":
            {"value":"300","desc":"TCP keepalive interval","note":"2205917"},
        "vm.dirty_bytes":
            {"value":"629145600","desc":"Dirty memory bytes before writeback","note":"2205917"},
        "vm.dirty_background_bytes":
            {"value":"314572800","desc":"Background writeback threshold","note":"2205917"},
    },
    "Windows Server": {
        "TcpTimedWaitDelay":
            {"value":"30","desc":"TCP TIME_WAIT delay in seconds","note":""},
        "MaxUserPort":
            {"value":"65534","desc":"Maximum user port number","note":""},
        "MaxHashTableSize":
            {"value":"65536","desc":"TCP hash table size","note":""},
    },
}
# ============================================================
# PART 2 OF 6 — Upgrade Path Matrix + Web Helpers
# SAP Help Navigator Pro
# ============================================================

# ============================================================
# UPGRADE PATH MATRIX
# ============================================================
UPGRADE_PATHS = {
    "SAP ECC 6.0 EHP0": {
        "SAP ECC 6.0 EHP8":
            {"type":"EHP Upgrade","tool":"SUM",
             "stops":["Intermediate EHPs may be required"],"note":"1680045"},
        "SAP S/4HANA 2020":
            {"type":"System Conversion","tool":"SUM+DMO",
             "stops":["Must reach EHP7/EHP8 first"],"note":"2399707"},
        "SAP S/4HANA 2023":
            {"type":"System Conversion","tool":"SUM+DMO",
             "stops":["EHP8 SP20+ required"],"note":"2913617"},
    },
    "SAP ECC 6.0 EHP7": {
        "SAP ECC 6.0 EHP8":
            {"type":"EHP Upgrade","tool":"SUM","stops":[],"note":"1680045"},
        "SAP S/4HANA 1709":
            {"type":"System Conversion","tool":"SUM+DMO","stops":[],"note":"2399707"},
        "SAP S/4HANA 2020":
            {"type":"System Conversion","tool":"SUM+DMO","stops":[],"note":"2399707"},
        "SAP S/4HANA 2022":
            {"type":"System Conversion","tool":"SUM+DMO","stops":[],"note":"2913617"},
        "SAP S/4HANA 2023":
            {"type":"System Conversion","tool":"SUM+DMO",
             "stops":["Apply minimum SP level first"],"note":"2913617"},
    },
    "SAP ECC 6.0 EHP8": {
        "SAP S/4HANA 1511":
            {"type":"System Conversion","tool":"SUM+DMO","stops":[],"note":"2399707"},
        "SAP S/4HANA 1610":
            {"type":"System Conversion","tool":"SUM+DMO","stops":[],"note":"2399707"},
        "SAP S/4HANA 1709":
            {"type":"System Conversion","tool":"SUM+DMO","stops":[],"note":"2399707"},
        "SAP S/4HANA 1809":
            {"type":"System Conversion","tool":"SUM+DMO","stops":[],"note":"2399707"},
        "SAP S/4HANA 1909":
            {"type":"System Conversion","tool":"SUM+DMO","stops":[],"note":"2399707"},
        "SAP S/4HANA 2020":
            {"type":"System Conversion","tool":"SUM+DMO","stops":[],"note":"2399707"},
        "SAP S/4HANA 2021":
            {"type":"System Conversion","tool":"SUM+DMO","stops":[],"note":"2568780"},
        "SAP S/4HANA 2022":
            {"type":"System Conversion","tool":"SUM+DMO","stops":[],"note":"2913617"},
        "SAP S/4HANA 2023":
            {"type":"System Conversion","tool":"SUM+DMO","stops":[],"note":"2913617"},
        "SAP S/4HANA 2024":
            {"type":"System Conversion","tool":"SUM+DMO",
             "stops":["Apply latest SP first"],"note":"2913617"},
    },
    "SAP S/4HANA 1709": {
        "SAP S/4HANA 1809":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 1909":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2020":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2021":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2022":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2023":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2024":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
    },
    "SAP S/4HANA 1809": {
        "SAP S/4HANA 1909":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2020":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2021":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2022":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2023":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2024":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
    },
    "SAP S/4HANA 1909": {
        "SAP S/4HANA 2020":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2021":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2022":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2023":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2024":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
    },
    "SAP S/4HANA 2020": {
        "SAP S/4HANA 2021":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2022":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2023":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2024":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
    },
    "SAP S/4HANA 2021": {
        "SAP S/4HANA 2022":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2023":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2024":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
    },
    "SAP S/4HANA 2022": {
        "SAP S/4HANA 2023":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP S/4HANA 2024":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
    },
    "SAP S/4HANA 2023": {
        "SAP S/4HANA 2024":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
    },
    "SAP HANA 1.0 SPS12": {
        "SAP HANA 2.0 SPS04":
            {"type":"Database Upgrade","tool":"hdblcm",
             "stops":["Full backup required first"],"note":"2380493"},
        "SAP HANA 2.0 SPS05":
            {"type":"Database Upgrade","tool":"hdblcm",
             "stops":["Via SPS04 first"],"note":"2380493"},
        "SAP HANA 2.0 SPS07":
            {"type":"Database Upgrade","tool":"hdblcm",
             "stops":["Via SPS04 then SPS06"],"note":"2380493"},
    },
    "SAP HANA 2.0 SPS04": {
        "SAP HANA 2.0 SPS05":
            {"type":"Revision Upgrade","tool":"hdblcm","stops":[],"note":"2380493"},
        "SAP HANA 2.0 SPS06":
            {"type":"Revision Upgrade","tool":"hdblcm","stops":[],"note":"2380493"},
        "SAP HANA 2.0 SPS07":
            {"type":"Revision Upgrade","tool":"hdblcm","stops":[],"note":"2380493"},
    },
    "SAP HANA 2.0 SPS05": {
        "SAP HANA 2.0 SPS06":
            {"type":"Revision Upgrade","tool":"hdblcm","stops":[],"note":"2380493"},
        "SAP HANA 2.0 SPS07":
            {"type":"Revision Upgrade","tool":"hdblcm","stops":[],"note":"2380493"},
    },
    "SAP HANA 2.0 SPS06": {
        "SAP HANA 2.0 SPS07":
            {"type":"Revision Upgrade","tool":"hdblcm","stops":[],"note":"2380493"},
    },
    "SAP Solution Manager 7.1": {
        "SAP Solution Manager 7.2":
            {"type":"Release Upgrade","tool":"SUM",
             "stops":["SP10 minimum recommended"],"note":"2383326"},
    },
    "SAP NetWeaver 7.4": {
        "SAP NetWeaver 7.5":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP ABAP Platform 1909":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
    },
    "SAP NetWeaver 7.5": {
        "SAP ABAP Platform 1909":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
        "SAP ABAP Platform 2022":
            {"type":"Release Upgrade","tool":"SUM","stops":[],"note":"2568780"},
    },
}

# ============================================================
# WEB FETCHING HELPERS
# ============================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_url(url: str) -> Optional[str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception:
        return None

def search_sap_help(query: str, product: str = "") -> list:
    results = []
    term = f"{product} {query}".strip() if product else query

    # Strategy 1 — SAP Help search API
    try:
        r = requests.get(
            SAP_SEARCH_API,
            params={
                "q": term, "area": "docs",
                "language": "en-US", "state": "PRODUCTION"
            },
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
                        "title":       item.get("title",
                                       item.get("name", "SAP Document")),
                        "url":         url,
                        "description": item.get("description",
                                       item.get("summary", "")),
                        "source":      "SAP Help API",
                    })
    except Exception:
        pass

    # Strategy 2 — scrape SAP docs page
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

    # Strategy 3 — curated fallback
    if len(results) < 2:
        results.extend(_fallback_results(term))

    seen, out = set(), []
    for item in results:
        if item["url"] not in seen:
            seen.add(item["url"])
            out.append(item)
    return out[:8]

def _fallback_results(query: str) -> list:
    q = query.lower()
    mapping = {
        ("s/4hana","s4hana","s4"): [
            ("SAP S/4HANA Documentation",
             "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE"),
            ("S/4HANA Upgrade Guide",
             "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/upgrade"),
            ("S/4HANA Installation Guide",
             "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/installation"),
        ],
        ("ecc","erp 6","erp6","ehp"): [
            ("SAP ERP Documentation",
             "https://help.sap.com/docs/SAP_ERP"),
            ("SAP ECC Upgrade Guide",
             "https://help.sap.com/docs/SAP_ERP/upgrade"),
        ],
        ("btp","business technology platform"): [
            ("SAP BTP Documentation",
             "https://help.sap.com/docs/btp"),
            ("BTP Account Setup",
             "https://help.sap.com/docs/btp/sap-business-technology-platform/setting-up-your-account"),
        ],
        ("hana",): [
            ("SAP HANA Platform",
             "https://help.sap.com/docs/SAP_HANA_PLATFORM"),
            ("SAP HANA Administration Guide",
             "https://help.sap.com/docs/SAP_HANA_PLATFORM/administration"),
            ("SAP HANA Installation Guide",
             "https://help.sap.com/docs/SAP_HANA_PLATFORM/installation"),
        ],
        ("fiori",): [
            ("SAP Fiori Documentation",
             "https://help.sap.com/docs/SAP_FIORI"),
        ],
        ("solution manager","solman"): [
            ("SAP Solution Manager",
             "https://help.sap.com/docs/SAP_SOLUTION_MANAGER"),
        ],
        ("netweaver",): [
            ("SAP NetWeaver",
             "https://help.sap.com/docs/SAP_NETWEAVER"),
        ],
        ("abap",): [
            ("SAP ABAP Platform",
             "https://help.sap.com/docs/ABAP_PLATFORM"),
        ],
        ("pi","po","integration"): [
            ("SAP Integration Suite",
             "https://help.sap.com/docs/SAP_INTEGRATION_SUITE"),
        ],
        ("bw","bw/4hana"): [
            ("SAP BW/4HANA Documentation",
             "https://help.sap.com/docs/SAP_BW4HANA"),
        ],
        ("successfactors",): [
            ("SAP SuccessFactors Documentation",
             "https://help.sap.com/docs/SAP_SUCCESSFACTORS_HXM_SUITE"),
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
            {"title":"SAP Help Portal","url":"https://help.sap.com/docs",
             "description":"All SAP documentation","source":"SAP"},
            {"title":"SAP S/4HANA Documentation",
             "url":"https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE",
             "description":"S/4HANA docs","source":"SAP"},
            {"title":"SAP HANA Platform",
             "url":"https://help.sap.com/docs/SAP_HANA_PLATFORM",
             "description":"HANA docs","source":"SAP"},
        ]
    return out

@st.cache_data(ttl=1800, show_spinner=False)
def extract_doc_content(url: str) -> dict:
    html = fetch_url(url)
    if not html:
        return {
            "title":"Unavailable","content":"",
            "sections":{},"pdf_links":[],"url":url
        }
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style","nav","footer","header","aside"]):
        tag.decompose()

    title = ""
    for sel in ["h1.title","h1","title",".page-title",".document-title"]:
        t = soup.select_one(sel)
        if t:
            title = t.get_text(strip=True)
            break

    main = (
        soup.select_one(
            "main,.content,article,.topic-body,#content,.help-content"
        ) or soup.body
    )
    text = (
        main.get_text("\n", strip=True)
        if main else soup.get_text("\n", strip=True)
    )
    text = re.sub(r"\n{3,}", "\n\n", text)[:12000]

    sections = {}
    patterns = {
        "prerequisites":
            r"(?i)(prerequisite|system requirement|before you (?:begin|start))"
            r".*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
        "upgrade_path":
            r"(?i)(upgrade path|upgrade route|migration path|target release)"
            r".*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
        "installation":
            r"(?i)(install|setup|deploy|provisioning)"
            r".*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
        "parameters":
            r"(?i)(parameter|profile|configuration|tuning|sizing)"
            r".*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
        "best_practices":
            r"(?i)(best practice|recommendation|guideline|important note)"
            r".*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
        "steps":
            r"(?i)(step|procedure|how to|task|perform|execute)"
            r".*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
        "dependencies":
            r"(?i)(depend|compatib|kernel|patch|component version)"
            r".*?(?=\n[A-Z][^\n]{3,50}\n|\Z)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text, re.DOTALL)
        if m:
            sections[key] = m.group(0)[:2000]

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
# PART 3 OF 6 — AI Answer Engine + Checklist + HTML Report
# SAP Help Navigator Pro
# ============================================================

# ============================================================
# AI ANSWER ENGINE
# ============================================================
def get_ai_answer(
    question: str,
    context: str,
    api_key: str,
    product: str = ""
) -> str:
    """
    Generate answer using Gemini AI when API key is available.
    Falls back to rule-based answer generation if AI is unavailable.
    """
    if api_key and GENAI_AVAILABLE:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = (
                "You are a senior SAP Technical Architect with 20+ years of experience.\n"
                "You specialize in SAP upgrades, installations, system administration,\n"
                "basis operations, prerequisites, dependencies, and best practices.\n\n"
                f"Product context: {product or 'General SAP'}\n\n"
                "STRICT INSTRUCTIONS:\n"
                "- Use ONLY the provided SAP documentation context\n"
                "- Do not invent unsupported facts\n"
                "- Format with **bold headings**, numbered steps, and bullet lists\n"
                "- Use warning, prerequisite, note, and reference markers\n"
                "- Include SAP Note numbers when relevant\n"
                "- Use code blocks for commands and parameters where useful\n"
                "- Be practical and action-oriented\n"
                "- If data is missing, clearly say it is not in the context\n\n"
                "--- SAP DOCUMENTATION CONTEXT ---\n"
                f"{context[:7000]}\n"
                "--- END CONTEXT ---\n\n"
                f"Question: {question}\n\n"
                "Provide a detailed, structured answer:"
            )

            response = model.generate_content(prompt)
            if hasattr(response, "text") and response.text:
                return response.text

            return _rule_based_answer(question, context, product)

        except Exception as e:
            err      = str(e)
            fallback = _rule_based_answer(question, context, product)

            if "quota" in err.lower() or "limit" in err.lower():
                return (
                    fallback
                    + "\n\n> ⚠️ *Gemini API rate limit reached. "
                      "Showing rule-based answer instead.*"
                )

            return fallback + f"\n\n> ⚠️ *AI unavailable: {err[:100]}*"

    return _rule_based_answer(question, context, product)


# ============================================================
# RULE-BASED ANSWER GENERATOR
# ============================================================
def _rule_based_answer(
    question: str,
    context: str,
    product: str = ""
) -> str:
    """
    Fallback answer engine using keyword-based response templates
    and extracted documentation snippets.
    """
    q     = question.lower()
    lines = [
        l.strip() for l in context.split("\n")
        if l.strip() and len(l.strip()) > 25
    ]

    def relevant(keywords: list) -> list:
        return [
            l for l in lines
            if any(k in l.lower() for k in keywords)
        ][:12]

    # --------------------------------------------------------
    # Upgrade Path
    # --------------------------------------------------------
    if any(k in q for k in [
        "upgrade path", "upgrade route", "migration path",
        "how to upgrade", "upgrade from", "target release",
        "upgrade scenario"
    ]):
        hits   = relevant([
            "upgrade", "migration", "path",
            "release", "target", "version", "sps", "sp"
        ])
        answer = f"## 🔄 Upgrade Path — {product}\n\n"

        if hits:
            answer += (
                "**From SAP documentation:**\n"
                + "\n".join(f"- {h}" for h in hits)
                + "\n\n"
            )

        answer += (
            "\n### Supported SAP Upgrade Scenarios\n\n"
            "| Scenario | Description | Main Tool |\n"
            "|---|---|---|\n"
            "| **EHP Upgrade** | ECC to higher Enhancement Package | SUM |\n"
            "| **Release Upgrade** | S/4HANA X to S/4HANA Y | SUM |\n"
            "| **System Conversion** | ECC / AnyDB to S/4HANA + HANA | SUM + DMO |\n"
            "| **Greenfield** | Fresh implementation | SWPM |\n"
            "| **Selective Transition** | Partial migration / carve-out | Partner tooling |\n\n"
            "### Recommended Approach\n"
            "1. Run **SAP Readiness Check** using `/SDF/RC_START_CHECK`\n"
            "2. Validate supported path in **Product Availability Matrix (PAM)**\n"
            "3. Generate **Stack.xml** with SAP Maintenance Planner\n"
            "4. Use **SUM** for technical execution\n"
            "5. Plan **SPDD** and **SPAU** adjustment effort\n"
            "6. Test upgrade in sandbox before DEV/QAS/PRD sequence\n\n"
            "📋 **SAP Note 2913617** — SAP Readiness Check\n"
            "📋 **SAP Note 2568780** — Software Update Manager (SUM)\n"
            "📋 **SAP Note 2399707** — S/4HANA technical prerequisites\n"
            "🔗 **PAM:** https://apps.support.sap.com/sap/support/pam\n"
            "🔗 **Maintenance Planner:** https://support.sap.com/mp\n"
        )
        return answer

    # --------------------------------------------------------
    # Prerequisites
    # --------------------------------------------------------
    if any(k in q for k in [
        "prerequisite", "requirements", "requirement",
        "before", "prepare", "checklist", "readiness"
    ]):
        hits   = relevant([
            "require", "prerequisite", "minimum",
            "supported", "must", "hardware",
            "software", "os", "database"
        ])
        answer = f"## ✅ Prerequisites & Requirements — {product}\n\n"

        if hits:
            answer += (
                "**From SAP documentation:**\n"
                + "\n".join(f"- {h}" for h in hits)
                + "\n\n"
            )

        answer += (
            "\n### Hardware Prerequisites\n"
            "- CPU sizing must be validated using **SAP Quick Sizer**\n"
            "- Memory sizing must include application + database + growth\n"
            "- SUM staging requires approximately 100 GB free disk minimum\n"
            "- Backup space must be available for full DB backup and logs\n\n"
            "### Software Prerequisites\n"
            "- Supported **OS version** per PAM\n"
            "- Supported **database version** per PAM\n"
            "- Latest stable **SAP Kernel** patch level\n"
            "- Required **JDK version** for Java stacks / Fiori / BTP\n\n"
            "### SAP Technical Prerequisites\n"
            "- Valid **S-user** with download authorizations\n"
            "- Access to **SAP Software Download Center**\n"
            "- **SAP Solution Manager** for maintenance certificate / LMDB\n"
            "- Minimum **Support Package level** before upgrade\n"
            "- **Unicode** system required for S/4HANA\n"
            "- Successful **Readiness Check** with no unresolved critical blockers\n\n"
            "### Recommended Validation Tasks\n"
            "1. Check current release and SP level in **SPAM / SAINT**\n"
            "2. Review installed add-ons and industry solutions\n"
            "3. Verify interfaces and custom code impact\n"
            "4. Confirm backup and restore procedure works\n"
            "5. Validate kernel, host agent, and DB revision compatibility\n\n"
            "📋 **SAP Note 2186744** — Pre-upgrade checklist\n"
            "📋 **SAP Note 2399707** — S/4HANA prerequisites\n"
            "📋 **SAP Note 2913617** — SAP Readiness Check\n"
            "📋 **SAP Note 19466** — Operating system requirements\n"
        )
        return answer

    # --------------------------------------------------------
    # Installation / Download
    # --------------------------------------------------------
    if any(k in q for k in [
        "install", "installation", "download", "setup",
        "deploy", "sapinst", "swpm", "media"
    ]):
        hits   = relevant([
            "install", "download", "setup", "deploy",
            "media", "sapinst", "swpm"
        ])
        answer = f"## 💾 Installation & Download Guide — {product}\n\n"

        if hits:
            answer += (
                "**From SAP documentation:**\n"
                + "\n".join(f"- {h}" for h in hits)
                + "\n\n"
            )

        answer += (
            "\n### Download Sources\n\n"
            "| Resource | URL |\n"
            "|---|---|\n"
            "| SAP Software Download Center | https://support.sap.com/swdc |\n"
            "| SAP Maintenance Planner | https://support.sap.com/mp |\n"
            "| SAP Help Portal | https://help.sap.com/docs |\n"
            "| SAP Launchpad | https://launchpad.support.sap.com |\n\n"
            "### Common Files to Download\n"
            "1. Installation exports / DVDs\n"
            "2. SAP Kernel (64-bit Unicode)\n"
            "3. SAP Host Agent\n"
            "4. Database installation media\n"
            "5. SUM (for upgrade scenarios)\n"
            "6. SWPM / sapinst (for fresh installation)\n"
            "7. Stack.xml generated from Maintenance Planner\n\n"
            "### Standard Installation Flow\n"
            "Step 1 - Prepare operating system\n"
            "Step 2 - Create required filesystem layout\n"
            "Step 3 - Configure OS users and groups\n"
            "Step 4 - Install and prepare database\n"
            "Step 5 - Run SWPM (sapinst)\n"
            "Step 6 - Apply latest SAP kernel\n"
            "Step 7 - Complete post-installation setup\n"
            "Step 8 - Apply support packages if required\n\n"
            "### Post-Installation Checks\n"
            "- Verify services start correctly\n"
            "- Check work processes in **SM50**\n"
            "- Validate RFCs in **SM59**\n"
            "- Review profile parameters in **RZ10 / RZ11**\n"
            "- Confirm transport setup in **STMS**\n\n"
            "📋 **SAP Note 1680045** — Installation best practices\n"
            "📋 **SAP Note 2393060** — sapinst / SWPM troubleshooting\n"
            "📋 **SAP Note 1639498** — How to download SAP software\n"
        )
        return answer

    # --------------------------------------------------------
    # Parameters / Config
    # --------------------------------------------------------
    if any(k in q for k in [
        "parameter", "parameters", "profile",
        "config", "configuration", "tuning",
        "memory", "sizing", "rz10", "rz11",
        "work process", "buffer"
    ]):
        hits   = relevant([
            "parameter", "profile", "memory", "buffer",
            "rdisp", "abap/", "icm/", "login/"
        ])
        answer = f"## ⚙️ Parameter Recommendations — {product}\n\n"

        if hits:
            answer += (
                "**From SAP documentation:**\n"
                + "\n".join(f"- {h}" for h in hits)
                + "\n\n"
            )

        answer += (
            "\n### Common ABAP Profile Parameters\n\n"
            "Memory settings:\n"
            "  abap/heap_area_total       = 2000000000\n"
            "  abap/heap_area_dia         = 500000000\n"
            "  em/initial_size_MB         = 4096\n"
            "  em/max_size_MB             = 16384\n\n"
            "Work process counts:\n"
            "  rdisp/wp_no_dia            = 10\n"
            "  rdisp/wp_no_btc            = 4\n"
            "  rdisp/wp_no_spo            = 2\n"
            "  rdisp/wp_no_upd            = 2\n"
            "  rdisp/max_wprun_time       = 600\n\n"
            "Buffer settings:\n"
            "  zcsa/table_buffer_area     = 100000000\n"
            "  rsdb/obj/buffersize        = 500000\n"
            "  abap/buffersize            = 600000\n\n"
            "### Common HANA Parameters (global.ini)\n\n"
            "  [memorymanager]\n"
            "  global_allocation_limit    = 80 percent of physical RAM\n\n"
            "  [joins]\n"
            "  optimization_target        = balanced\n\n"
            "  [sql]\n"
            "  result_cache_entry_lifetime = 300\n\n"
            "### Common Linux OS Parameters (sysctl.conf)\n\n"
            "  vm.max_map_count           = 2147483647\n"
            "  vm.swappiness              = 10\n"
            "  kernel.shmmax              = total RAM bytes\n"
            "  fs.file-max                = 20000000\n"
            "  net.core.somaxconn         = 4096\n\n"
            "### Recommended Transactions\n"
            "- **RZ10** — Maintain profile parameters\n"
            "- **RZ11** — Display parameter documentation\n"
            "- **ST02** — Analyze buffer quality and swaps\n"
            "- **SM50 / SM66** — Work process monitoring\n"
            "- **DBACOCKPIT** — DB and HANA administration\n\n"
            "📋 **SAP Note 941735** — Memory management parameters\n"
            "📋 **SAP Note 2222200** — HANA recommended settings\n"
            "📋 **SAP Note 1984787** — OS parameters for SAP on Linux\n"
        )
        return answer

    # --------------------------------------------------------
    # Dependencies / Compatibility
    # --------------------------------------------------------
    if any(k in q for k in [
        "dependencies", "dependency", "compatibility",
        "compatible", "component", "kernel",
        "patch", "stack", "version matrix"
    ]):
        hits   = relevant([
            "depend", "compatib", "kernel",
            "patch", "component", "version",
            "support package", "sp"
        ])
        answer = f"## 🔗 Dependencies & Compatibility — {product}\n\n"

        if hits:
            answer += (
                "**From SAP documentation:**\n"
                + "\n".join(f"- {h}" for h in hits)
                + "\n\n"
            )

        answer += (
            "\n### Common Dependency Areas\n"
            "- **SAP Kernel** must match the target release requirements\n"
            "- **SAP Host Agent** should be upgraded to a supported level\n"
            "- **Database revision** must be supported for the target SAP product\n"
            "- **Operating system** must be listed in PAM for the target release\n"
            "- **Add-ons and industry solutions** must have valid upgrade paths\n"
            "- **Java / browser / Fiori front-end** dependencies may apply\n\n"
            "### Recommended Dependency Validation\n"
            "1. Review installed add-ons in **SAINT**\n"
            "2. Check SP stack levels in **SPAM**\n"
            "3. Validate OS and DB combination in **PAM**\n"
            "4. Generate and review **Maintenance Planner** stack\n"
            "5. Confirm latest kernel and host agent availability\n\n"
            "### Typical Compatibility Risks\n"
            "- Unsupported database revision\n"
            "- Old OS version not listed in PAM\n"
            "- Third-party interface dependencies not tested\n"
            "- Industry add-on not supported in target release\n"
            "- Kernel patch mismatch\n\n"
            "📋 **SAP Note 2379811** — Supported HANA revisions for S/4HANA\n"
            "📋 **SAP Note 1707976** — Kernel dependency overview\n"
            "🔗 **PAM:** https://apps.support.sap.com/sap/support/pam\n"
        )
        return answer

    # --------------------------------------------------------
    # Best Practices
    # --------------------------------------------------------
    if any(k in q for k in [
        "best practice", "best practices",
        "recommendation", "recommendations",
        "guideline", "guidelines", "tips"
    ]):
        answer = f"## 🌟 Best Practices — {product}\n\n"
        answer += (
            "### Upgrade Best Practices\n"
            "- Upgrade in the order Sandbox then DEV then QAS then PRD\n"
            "- Keep at least two verified backups before production upgrade\n"
            "- Always use **Maintenance Planner** for stack definition\n"
            "- Execute a dry run in sandbox before production execution\n"
            "- Resolve all **Readiness Check** critical issues first\n\n"
            "### Performance Best Practices\n"
            "- Validate sizing with **SAP Quick Sizer**\n"
            "- Review buffer swap rates in **ST02**\n"
            "- Monitor work processes in **SM50 / SM66**\n"
            "- Tune memory conservatively and validate after every change\n"
            "- Run HANA health and mini-checks regularly\n\n"
            "### Security Best Practices\n"
            "- Apply latest security-relevant kernel patches promptly\n"
            "- Enable **Security Audit Log** in all production systems\n"
            "- Restrict SAP_ALL and SAP_NEW usage in production\n"
            "- Use named RFC users with least privilege approach\n"
            "- Review default password and technical user policies\n\n"
            "### Operational Best Practices\n"
            "- Freeze transports before major upgrade window\n"
            "- Document rollback decision point and fallback plan\n"
            "- Keep business, basis, DB, OS, and security teams aligned\n"
            "- Maintain a detailed cutover checklist and rehearse it\n"
            "- Plan hypercare support period after every go-live\n\n"
            "📋 **SAP Note 1999993** — SAP HANA Mini Checks\n"
            "📋 **SAP Note 2622660** — SUM best practices\n"
            "🔗 **Best Practices Explorer:** https://rapid.sap.com/bp/\n"
        )
        return answer

    # --------------------------------------------------------
    # Upgrade Plan / Steps / Procedure
    # --------------------------------------------------------
    if any(k in q for k in [
        "plan", "steps", "step by step", "procedure",
        "phase", "project", "roadmap", "execution", "cutover"
    ]):
        answer = f"## 📋 Upgrade Project Plan — {product}\n\n"
        answer += (
            "### Phase 1: Assessment and Planning\n"
            "1. Inventory release, SP level, add-ons, and interfaces\n"
            "2. Run SAP Readiness Check\n"
            "3. Review target compatibility in PAM\n"
            "4. Estimate effort for custom code remediation\n"
            "5. Validate infrastructure sizing\n\n"
            "### Phase 2: Software Preparation\n"
            "6. Download SUM, kernel, and target media\n"
            "7. Generate Stack.xml via Maintenance Planner\n"
            "8. Prepare sandbox or rehearsal environment\n"
            "9. Define fallback and rollback approach\n\n"
            "### Phase 3: System Preparation\n"
            "10. Apply prerequisite support packages\n"
            "11. Remediate custom code findings\n"
            "12. Freeze transports\n"
            "13. Take full backup and perform restore test\n"
            "14. Run SUM EXTRACTONLY and fix all errors\n\n"
            "### Phase 4: Upgrade Execution\n"
            "15. Notify stakeholders and lock users\n"
            "16. Execute SUM\n"
            "17. Handle SPDD and SPAU adjustments\n"
            "18. Monitor DB, OS, and application logs throughout\n"
            "19. Validate successful technical completion\n\n"
            "### Phase 5: Validation and Testing\n"
            "20. Apply required post-upgrade SAP Notes\n"
            "21. Perform smoke testing of core transactions\n"
            "22. Run integration and UAT testing\n"
            "23. Tune parameters if needed\n\n"
            "### Phase 6: Go-Live and Hypercare\n"
            "24. Execute production cutover\n"
            "25. Re-enable transports and interfaces\n"
            "26. Monitor business processes closely\n"
            "27. Complete hypercare and hand over to operations\n\n"
            "📋 **SAP Note 2568780** — SUM documentation\n"
            "📋 **SAP Note 2186744** — Pre-upgrade checklist\n"
            "📋 **SAP Note 2913617** — Readiness Check\n"
        )
        return answer

    # --------------------------------------------------------
    # Download / PDF / Guides
    # --------------------------------------------------------
    if any(k in q for k in [
        "download", "pdf", "guide", "guides",
        "document", "where can i download"
    ]):
        answer = f"## ⬇️ Downloads & Documentation — {product}\n\n"
        answer += (
            "### Main Download Sources\n\n"
            "| Resource | URL |\n"
            "|---|---|\n"
            "| SAP Software Download Center | https://support.sap.com/swdc |\n"
            "| SAP Maintenance Planner | https://support.sap.com/mp |\n"
            "| SAP Help Portal | https://help.sap.com/docs |\n"
            "| SAP Launchpad | https://launchpad.support.sap.com |\n\n"
            "### Guide Types Available for Download\n"
            "- Installation Guide\n"
            "- Upgrade Guide\n"
            "- Administration Guide\n"
            "- Security Guide\n"
            "- Operations Guide\n"
            "- Master Guide\n"
            "- Release Notes\n\n"
            "### Typical Download Flow\n"
            "1. Open **https://help.sap.com/docs**\n"
            "2. Search for your SAP product and version\n"
            "3. Open the guide or topic\n"
            "4. Use the PDF or export option if available\n"
            "5. For software files use **https://support.sap.com/swdc**\n\n"
            "### Common Software Downloads\n"
            "- SUM (Software Update Manager)\n"
            "- SWPM (Software Provisioning Manager)\n"
            "- SAP Kernel (64-bit Unicode)\n"
            "- SAP Host Agent\n"
            "- Target release installation exports\n"
            "- Database client or installer\n\n"
            "📋 **SAP Note 1639498** — Download authorization and software access\n"
        )
        return answer

    # --------------------------------------------------------
    # Generic fallback
    # --------------------------------------------------------
    extracted = [l for l in lines if len(l) > 40][:10]
    answer    = f"## 📖 SAP Documentation Answer — {product}\n\n"
    answer   += f"**Question:** {question}\n\n"

    if extracted:
        answer += "**Relevant extracted content:**\n\n"
        answer += "\n\n".join(extracted)
    else:
        answer += (
            "No directly relevant documentation text was extracted "
            "for this query.\n\n"
            "### Suggested Next Steps\n"
            "- Search on **SAP Help Portal**: https://help.sap.com/docs\n"
            "- Check **SAP Community**: https://community.sap.com\n"
            "- Review **SAP Notes**: https://launchpad.support.sap.com\n"
        )

    return answer


# ============================================================
# CHECKLIST GENERATOR
# ============================================================
def generate_checklist(
    source: str,
    target: str,
    opts: dict
) -> list:
    """
    Generate a prioritized upgrade checklist based on source/target
    and optional scenario flags.
    """
    items = [
        {
            "cat": "System Assessment",
            "icon": "🔍",
            "pri": "Critical",
            "task": "Run SAP Readiness Check",
            "detail": (
                "Execute /SDF/RC_START_CHECK and resolve all "
                "Critical findings before proceeding"
            ),
            "tool": "Transaction /SDF/RC_START_CHECK",
            "note": "2913617",
        },
        {
            "cat": "System Assessment",
            "icon": "🔍",
            "pri": "Critical",
            "task": (
                f"Verify {source} meets minimum SP "
                f"prerequisite for {target}"
            ),
            "detail": (
                "Check required minimum support package level "
                "before upgrade execution"
            ),
            "tool": "SPAM / SE01",
            "note": "2186744",
        },
        {
            "cat": "System Assessment",
            "icon": "🔍",
            "pri": "High",
            "task": "Check Product Availability Matrix (PAM)",
            "detail": (
                "Validate OS, DB, and release compatibility "
                "for the target release"
            ),
            "tool": "apps.support.sap.com/sap/support/pam",
            "note": "",
        },
        {
            "cat": "System Assessment",
            "icon": "🔍",
            "pri": "High",
            "task": "Inventory installed add-ons and industry solutions",
            "detail": (
                "Identify all components that need upgrade "
                "path validation"
            ),
            "tool": "Transaction SAINT",
            "note": "",
        },
        {
            "cat": "Custom Code",
            "icon": "🖊️",
            "pri": "Critical",
            "task": "Run Custom Code Migration Analysis",
            "detail": (
                "Use SCMA / ATC to identify incompatible custom code "
                "and required remediation items"
            ),
            "tool": "SCMA / ATC",
            "note": "2190420",
        },
        {
            "cat": "Custom Code",
            "icon": "🖊️",
            "pri": "High",
            "task": "Analyze modifications and enhancement points",
            "detail": (
                "Document custom objects, exits, BADIs, Z/Y programs, "
                "and modified SAP objects"
            ),
            "tool": "SPAU / SPDD / SE80 / SE95",
            "note": "",
        },
        {
            "cat": "Infrastructure",
            "icon": "🖥️",
            "pri": "Critical",
            "task": "Validate hardware sizing",
            "detail": (
                "Confirm CPU, RAM, and disk requirements using "
                "SAP Quick Sizer and growth forecasts"
            ),
            "tool": "SAP Quick Sizer",
            "note": "1652093",
        },
        {
            "cat": "Infrastructure",
            "icon": "🖥️",
            "pri": "Critical",
            "task": "Ensure SUM workspace disk availability",
            "detail": (
                "Reserve at least 100 GB free space for "
                "SUM staging and logs"
            ),
            "tool": "OS disk checks / df -h",
            "note": "2176227",
        },
        {
            "cat": "Infrastructure",
            "icon": "🖥️",
            "pri": "High",
            "task": "Verify OS parameter tuning",
            "detail": (
                "Apply SAP-recommended kernel and memory parameters "
                "before upgrade"
            ),
            "tool": "/etc/sysctl.conf",
            "note": "900929",
        },
        {
            "cat": "Backup & Recovery",
            "icon": "💾",
            "pri": "Critical",
            "task": "Take full database backup",
            "detail": (
                "Create a full backup immediately before upgrade "
                "and confirm retention policy"
            ),
            "tool": "DBACOCKPIT / BRTOOLS / hdbsql",
            "note": "",
        },
        {
            "cat": "Backup & Recovery",
            "icon": "💾",
            "pri": "Critical",
            "task": "Perform restore validation",
            "detail": (
                "Verify backup can be successfully restored "
                "to a non-production environment"
            ),
            "tool": "Restore procedure test",
            "note": "",
        },
        {
            "cat": "Backup & Recovery",
            "icon": "💾",
            "pri": "High",
            "task": "Export profile and configuration files",
            "detail": (
                "Save current SAP profiles, kernel info, RFC definitions, "
                "and key technical settings"
            ),
            "tool": "RZ10 / filesystem copy / documentation",
            "note": "",
        },
        {
            "cat": "Software Downloads",
            "icon": "⬇️",
            "pri": "Critical",
            "task": "Download latest SUM",
            "detail": (
                "Get the latest supported SUM version from "
                "SAP Software Download Center"
            ),
            "tool": "support.sap.com/swdc",
            "note": "2568780",
        },
        {
            "cat": "Software Downloads",
            "icon": "⬇️",
            "pri": "Critical",
            "task": "Download target release media",
            "detail": (
                "Download installation exports, kernel, host agent, "
                "and required DB media"
            ),
            "tool": "SAP Software Download Center",
            "note": "",
        },
        {
            "cat": "Software Downloads",
            "icon": "⬇️",
            "pri": "Critical",
            "task": "Generate Stack.xml with Maintenance Planner",
            "detail": (
                "Use Maintenance Planner to generate correct "
                "stack definition file for upgrade"
            ),
            "tool": "support.sap.com/mp",
            "note": "2383326",
        },
        {
            "cat": "Access & Licensing",
            "icon": "🔑",
            "pri": "Critical",
            "task": "Confirm S-user authorizations",
            "detail": (
                "Ensure software download and note access is available "
                "before execution week"
            ),
            "tool": "SAP Support Portal",
            "note": "",
        },
        {
            "cat": "Access & Licensing",
            "icon": "🔑",
            "pri": "Critical",
            "task": "Validate maintenance certificate",
            "detail": (
                "Check that system maintenance and license "
                "prerequisites are current and valid"
            ),
            "tool": "Solution Manager / Maintenance Planner",
            "note": "1979523",
        },
        {
            "cat": "Change Control",
            "icon": "🚦",
            "pri": "High",
            "task": "Freeze transports before upgrade",
            "detail": (
                "Block normal transport movement and "
                "close critical change windows"
            ),
            "tool": "STMS / change management process",
            "note": "",
        },
        {
            "cat": "Testing",
            "icon": "🧪",
            "pri": "High",
            "task": "Prepare smoke test scenarios",
            "detail": (
                "Define critical business and technical validation "
                "steps for post-upgrade testing"
            ),
            "tool": "Test scripts / business process inventory",
            "note": "",
        },
        {
            "cat": "Communication",
            "icon": "📣",
            "pri": "Medium",
            "task": "Notify business and technical stakeholders",
            "detail": (
                "Publish downtime window, validation responsibilities, "
                "and escalation path"
            ),
            "tool": "Project communication plan",
            "note": "",
        },
    ]

    if opts.get("has_custom_code"):
        items.append({
            "cat": "Custom Code",
            "icon": "🖊️",
            "pri": "Critical",
            "task": "Complete critical custom code remediation",
            "detail": (
                "All critical ATC and migration findings must be "
                "resolved before execution starts"
            ),
            "tool": "ATC / ADT / remediation worklist",
            "note": "2190420",
        })

    if opts.get("has_interfaces"):
        items.append({
            "cat": "Interfaces",
            "icon": "🔗",
            "pri": "High",
            "task": "Inventory all system interfaces",
            "detail": (
                "List RFC, IDoc, API, middleware, file, "
                "and external integration dependencies"
            ),
            "tool": "SM59 / WE20 / PI-PO / Integration Suite",
            "note": "",
        })
        items.append({
            "cat": "Interfaces",
            "icon": "🔗",
            "pri": "High",
            "task": "Prepare interface validation plan",
            "detail": (
                "Define reconnect, retest, and fallback approach "
                "for all interfaces after upgrade"
            ),
            "tool": "Integration test plan",
            "note": "",
        })

    if opts.get("ha_required"):
        items.append({
            "cat": "High Availability",
            "icon": "🛡️",
            "pri": "High",
            "task": "Validate HA and DR upgrade procedure",
            "detail": (
                "Coordinate failover, replication, and recovery "
                "sequencing during planned maintenance"
            ),
            "tool": "HANA SR / cluster tooling / DR runbook",
            "note": "1872602",
        })

    if opts.get("non_unicode"):
        items.append({
            "cat": "Unicode",
            "icon": "🌐",
            "pri": "Critical",
            "task": "Plan Unicode conversion",
            "detail": (
                "S/4HANA target requires Unicode; "
                "plan and sequence conversion appropriately"
            ),
            "tool": "SUM / Unicode conversion planning",
            "note": "73606",
        })

    return items


# ============================================================
# HTML REPORT GENERATOR
# ============================================================
def generate_html_report(
    product: str,
    question: str,
    answer: str,
    sources: list,
    checklist: list
) -> str:
    """
    Generate a self-contained downloadable HTML report.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    checklist_html = ""
    if checklist:
        rows = ""
        for item in checklist:
            pri_color = {
                "Critical": "#fee2e2",
                "High":     "#fef3c7",
                "Medium":   "#dbeafe",
            }.get(item["pri"], "#f8fafc")

            note_html = (
                "<a href='https://launchpad.support.sap.com"
                f"/#/notes/{item[\"note\"]}' target='_blank'>"
                f"{item['note']}</a>"
            ) if item.get("note") else "—"

            rows += (
                "<tr>"
                f"<td style='background:{pri_color};"
                "padding:6px 10px;border:1px solid #e5e7eb;"
                f"font-weight:600'>{item['pri']}</td>"
                f"<td style='padding:6px 10px;"
                f"border:1px solid #e5e7eb'>{item['cat']}</td>"
                f"<td style='padding:6px 10px;"
                "border:1px solid #e5e7eb;"
                f"font-weight:600'>{item['task']}</td>"
                f"<td style='padding:6px 10px;"
                "border:1px solid #e5e7eb;"
                f"font-size:.85em;color:#374151'>{item['detail']}</td>"
                f"<td style='padding:6px 10px;"
                f"border:1px solid #e5e7eb;font-size:.85em'>"
                f"{item['tool']}</td>"
                f"<td style='padding:6px 10px;"
                f"border:1px solid #e5e7eb;font-size:.85em'>"
                f"{note_html}</td>"
                "</tr>"
            )

        checklist_html = (
            "<div class='section'>"
            f"<h2>Pre-Upgrade Checklist ({len(checklist)} items)</h2>"
            "<table style='width:100%;border-collapse:collapse;"
            "font-size:.85rem'>"
            "<thead><tr style='background:#0057A8;color:#fff'>"
            "<th style='padding:8px'>Priority</th>"
            "<th style='padding:8px'>Category</th>"
            "<th style='padding:8px'>Task</th>"
            "<th style='padding:8px'>Detail</th>"
            "<th style='padding:8px'>Tool</th>"
            "<th style='padding:8px'>SAP Note</th>"
            "</tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table></div>"
        )

    sources_html = ""
    for src in sources:
        desc     = src.get("description", "")
        desc_tag = (
            f"<br><small style='color:#6b7280'>{desc[:120]}</small>"
            if desc else ""
        )
        sources_html += (
            "<li style='margin:.45rem 0'>"
            f"<a href='{src['url']}' target='_blank'>"
            f"<strong>{src['title']}</strong></a>"
            f"{desc_tag}</li>"
        )

    safe_answer = (
        answer
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    html = (
        "<!DOCTYPE html>\n"
        "<html lang='en'>\n"
        "<head>\n"
        "<meta charset='UTF-8'>\n"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>\n"
        f"<title>SAP Help Navigator Report - {product}</title>\n"
        "<style>\n"
        "body{font-family:'Segoe UI',Arial,sans-serif;margin:0;"
        "background:#f8fafc;color:#1e293b;line-height:1.6}\n"
        ".header{background:linear-gradient(135deg,#0057A8,#00A3E0);"
        "color:#fff;padding:2rem 3rem}\n"
        ".header h1{margin:0;font-size:1.8rem}\n"
        ".header p{margin:.4rem 0 0;opacity:.85}\n"
        ".section{background:#fff;margin:1.5rem 2rem;padding:1.5rem 2rem;"
        "border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.07)}\n"
        "h2{color:#0057A8;border-bottom:2px solid #e0e7ef;"
        "padding-bottom:.4rem;margin-top:0}\n"
        ".answer-box{background:#f0f7ff;border-left:4px solid #0057A8;"
        "padding:1rem 1.4rem;border-radius:8px;white-space:pre-wrap}\n"
        ".footer{text-align:center;padding:1.5rem;"
        "color:#94a3b8;font-size:.8rem}\n"
        "a{color:#0057A8}\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        "<div class='header'>\n"
        "<h1>SAP Help Navigator Pro - Report</h1>\n"
        "<p>\n"
        f"Product: <strong>{product or 'General SAP'}</strong>"
        f" &nbsp;.&nbsp; Generated: {now}"
        " &nbsp;.&nbsp; "
        "<a href='https://help.sap.com/docs' target='_blank' "
        "style='color:#fff'>help.sap.com</a>\n"
        "</p>\n"
        "</div>\n"
        "<div class='section'>\n"
        "<h2>Question</h2>\n"
        f"<p style='font-size:1.05rem;font-weight:500'>{question}</p>\n"
        "</div>\n"
        "<div class='section'>\n"
        "<h2>Answer</h2>\n"
        f"<div class='answer-box'>{safe_answer}</div>\n"
        "</div>\n"
        f"{checklist_html}\n"
        "<div class='section'>\n"
        f"<h2>Source Documents ({len(sources)})</h2>\n"
        "<ul style='padding-left:1.5rem;line-height:1.9'>\n"
        f"{sources_html}\n"
        "</ul>\n"
        "</div>\n"
        "<div class='footer'>\n"
        f"SAP Help Navigator Pro &nbsp;.&nbsp; {now}"
        " &nbsp;.&nbsp; For internal use only"
        " &nbsp;.&nbsp; "
        "<a href='https://help.sap.com/docs'>help.sap.com</a>\n"
        "</div>\n"
        "</body>\n"
        "</html>"
    )

    return html

# ============================================================
# ============================================================
# PART 4 OF 6 — Sidebar, Header, Tab1 Search, Tab2 Doc Viewer
# SAP Help Navigator Pro
# ============================================================

def render_sidebar():
    with st.sidebar:
        st.markdown("### 🔷 SAP Help Navigator")
        st.markdown("---")

        # API Key Status
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        if st.session_state.api_key:
            try:
                from_secrets = bool(st.secrets.get("gemini_api_key", ""))
            except Exception:
                from_secrets = False
            if from_secrets:
                st.success(
                    "🤖 **Gemini AI Active**\n\n"
                    "*Key loaded from Streamlit Secrets*"
                )
            else:
                st.success(
                    "🤖 **Gemini AI Active**\n\n"
                    "*Key entered manually*"
                )
        else:
            st.warning(
                "📐 **Rule-based Mode**\n\n"
                "Add Gemini key for AI-powered answers"
            )
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
        idx = (
            SAP_PRODUCTS.index(st.session_state.current_product)
            if st.session_state.current_product in SAP_PRODUCTS else 0
        )
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
            "🔄 Upgrade Path":
                "What are the supported upgrade paths and upgrade routes?",
            "✅ Prerequisites":
                "What are the system prerequisites and requirements?",
            "💾 Installation":
                "Provide complete step-by-step installation guide",
            "⚙️ Parameters":
                "What are the recommended profile parameters and configurations?",
            "🔗 Dependencies":
                "What are the component dependencies and compatibility requirements?",
            "📋 Upgrade Plan":
                "Generate a complete detailed upgrade project plan with all phases",
            "🌟 Best Practices":
                "What are the best practices and SAP recommendations?",
            "⬇️ Downloads":
                "Where can I download the software, patches, and documentation PDFs?",
        }
        for label, q in quick_questions.items():
            if st.button(label, use_container_width=True,
                         key=f"qbtn_{label[:6]}"):
                st.session_state.quick_q = q
                st.rerun()

        # Recent Search History
        if st.session_state.search_history:
            st.markdown("---")
            st.markdown("**🕘 Recent Searches**")
            for h in reversed(st.session_state.search_history[-5:]):
                st.caption(
                    f"• {h[:38]}{'…' if len(h) > 38 else ''}"
                )

        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='font-size:.72rem;color:#6b7280;"
            "text-align:center;line-height:1.6'>"
            "📄 Data: <a href='https://help.sap.com/docs' "
            "target='_blank'>help.sap.com</a><br>"
            "🤖 AI: <a href='https://aistudio.google.com' "
            "target='_blank'>Google Gemini</a><br>"
            "🔒 For internal / authorized use only"
            "</div>",
            unsafe_allow_html=True,
        )


def render_header():
    product    = st.session_state.current_product
    mode_txt   = (
        "🤖 Gemini AI Active"
        if st.session_state.api_key
        else "📐 Rule-based Mode"
    )
    docs_count = len(st.session_state.fetched_docs)
    qa_count   = len(st.session_state.conversation)
    st.markdown(
        f'<div class="main-header">'
        f'<h1>🔷 SAP Help Navigator Pro</h1>'
        f'<p>'
        f'Intelligent SAP Documentation Assistant &nbsp;·&nbsp; '
        f'Product: <strong>'
        f'{product or "Select a product in sidebar →"}'
        f'</strong> &nbsp;·&nbsp; {mode_txt}'
        f' &nbsp;·&nbsp; {docs_count} docs fetched'
        f' &nbsp;·&nbsp; {qa_count} Q&amp;A'
        f' &nbsp;·&nbsp; '
        f'<a href="https://help.sap.com/docs" target="_blank" '
        f'style="color:#fff">help.sap.com ↗</a>'
        f'</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# TAB 1 — SEARCH & ASK
# ============================================================
def tab_search_and_ask(product: str):
    st.markdown("### 🔍 Search SAP Documentation & Ask Questions")
    st.markdown(
        '<div class="info-box">💡 Ask any question about your SAP product. '
        'The tool searches live SAP Help Portal documentation and generates '
        'detailed structured answers. Select a product in the sidebar '
        'first for best results.</div>',
        unsafe_allow_html=True,
    )

    col_q, col_btn = st.columns([5, 1])
    with col_q:
        default_q = st.session_state.pop("quick_q", "")
        question  = st.text_input(
            "Your question",
            value=default_q,
            placeholder=(
                "e.g. What are the prerequisites for upgrading "
                "SAP S/4HANA 2022 to 2023?"
            ),
            key="main_question",
            label_visibility="collapsed",
        )
    with col_btn:
        go = st.button("🔍 Search", type="primary",
                       use_container_width=True)

    # Suggestion pills
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
        if question not in st.session_state.search_history:
            st.session_state.search_history.append(question)

        with st.spinner("🔍 Searching SAP Help Portal…"):
            results = search_sap_help(question, product)

        with st.spinner("📄 Reading SAP documentation…"):
            context = ""
            for res in results[:3]:
                url = res["url"]
                if url not in st.session_state.doc_cache:
                    doc = extract_doc_content(url)
                    st.session_state.doc_cache[url]    = doc
                    st.session_state.fetched_docs[url] = doc
                doc = st.session_state.doc_cache[url]
                context += (
                    f"\n\n=== SOURCE: {doc.get('title','')} ===\n"
                    f"{doc.get('content','')[:3000]}"
                )

        with st.spinner("🤖 Generating answer…"):
            answer = get_ai_answer(
                question, context,
                st.session_state.api_key, product
            )

        st.session_state.conversation.append({
            "question": question,
            "answer":   answer,
            "sources":  results,
            "product":  product,
        })

        q_lower = question.lower()
        icon = next(
            (ic for kw, ic in [
                ("upgrade","🔄"), ("prerequisite","✅"),
                ("install","💾"), ("parameter","⚙️"),
                ("depend","🔗"), ("best practice","🌟"),
                ("download","⬇️"), ("plan","📋"),
                ("hana","🗄️"),
            ] if kw in q_lower),
            "📖",
        )

        st.markdown(f"### {icon} Answer")
        st.markdown(
            f'<div class="answer-box">{answer}</div>',
            unsafe_allow_html=True,
        )

        if results:
            st.markdown("### 🔗 Source Documents from SAP Help Portal")
            for r in results[:6]:
                st.markdown(
                    f'<div class="source-card">'
                    f'<a href="{r["url"]}" target="_blank">'
                    f'📄 {r["title"]}</a><br>'
                    f'<small style="color:#6b7280">'
                    f'{r.get("description","")[:120]}</small><br>'
                    f'<small style="color:#94a3b8">'
                    f'Source: {r.get("source","SAP Help Portal")}'
                    f' &nbsp;·&nbsp; '
                    f'<a href="{r["url"]}" target="_blank" '
                    f'style="color:#94a3b8">'
                    f'{r["url"][:65]}…</a>'
                    f'</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        all_pdfs = list({
            pdf
            for doc in st.session_state.fetched_docs.values()
            for pdf in doc.get("pdf_links", [])
        })
        if all_pdfs:
            st.markdown("### 📥 PDF Documents Found")
            for pdf in all_pdfs[:6]:
                fn = pdf.split("/")[-1] or "document.pdf"
                st.markdown(
                    f'<div class="source-card">'
                    f'📕 <a href="{pdf}" target="_blank">{fn}</a>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ============================================================
# TAB 2 — DOCUMENT VIEWER
# ============================================================
def tab_document_viewer(product: str):
    st.markdown("### 📄 SAP Document Viewer")
    st.markdown(
        '<div class="info-box">📄 Paste any SAP Help Portal URL to fetch '
        'and parse the document. The tool extracts key sections and lets '
        'you ask specific questions about the document content.</div>',
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
        if st.button("📥 Fetch Document",
                     use_container_width=True) and url_input:
            with st.spinner("📄 Fetching document content…"):
                doc = extract_doc_content(url_input)
                st.session_state.fetched_docs[url_input] = doc
                st.session_state.doc_cache[url_input]    = doc
            if doc.get("title"):
                st.success(f"✅ Fetched: {doc['title'][:60]}")
            else:
                st.warning(
                    "⚠️ Document fetched but title not found. Check URL."
                )

    if not st.session_state.fetched_docs:
        st.markdown(
            '<div class="info-box">📄 No documents fetched yet. '
            'Use the Search & Ask tab to search for topics, '
            'or paste a SAP Help Portal URL above.</div>',
            unsafe_allow_html=True,
        )
        return

    selected_url = st.selectbox(
        "Select a fetched document to view",
        list(st.session_state.fetched_docs.keys()),
        format_func=lambda u:
            st.session_state.fetched_docs[u].get("title", u)[:70],
    )
    doc = st.session_state.fetched_docs[selected_url]

    col_title, col_link = st.columns([3, 1])
    with col_title:
        st.markdown(f"#### 📄 {doc.get('title', 'Document')}")
    with col_link:
        st.markdown(
            f'<a href="{selected_url}" target="_blank">'
            f'🔗 Open on SAP Help Portal</a>',
            unsafe_allow_html=True,
        )

    sections = doc.get("sections", {})
    if sections:
        st.markdown("##### 📑 Detected Document Sections")
        sec_tabs = st.tabs(
            [f"📌 {s.replace('_', ' ').title()}" for s in sections]
        )
        for i, (sec_name, sec_content) in enumerate(sections.items()):
            with sec_tabs[i]:
                st.markdown(sec_content)

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
                    f'<a href="{pdf}" target="_blank" '
                    f'style="font-size:.82rem">📕 {fn[:30]}</a>',
                    unsafe_allow_html=True,
                )

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
            "answer":   doc_answer,
            "sources":  [{
                "title":       doc.get("title", ""),
                "url":         selected_url,
                "description": "",
            }],
            "product":  product,
        })
# ============================================================
# PART 5 OF 6 — Tab3 Upgrade Planner, Tab4 Matrix,
#                Tab5 Parameters, Tab6 Checklist
# SAP Help Navigator Pro
# ============================================================

# ============================================================
# TAB 3 — UPGRADE PLANNER
# ============================================================
def tab_upgrade_planner(product: str):
    st.markdown("### 📋 SAP Upgrade Project Planner")
    st.markdown(
        '<div class="info-box">📋 Fill in your upgrade scenario details '
        'to generate a complete phased upgrade project plan with detailed '
        'steps, timeline overview, and key SAP Notes.</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        src_release = st.text_input(
            "Source Release",
            placeholder="e.g. SAP ECC 6.0 EHP8", key="up_src"
        )
        src_db = st.selectbox(
            "Source Database",
            ["","SAP HANA","Oracle","MS SQL Server",
             "IBM DB2","MaxDB","Sybase ASE"],
            key="up_sdb"
        )
    with col2:
        tgt_release = st.text_input(
            "Target Release",
            placeholder="e.g. SAP S/4HANA 2023", key="up_tgt"
        )
        tgt_db = st.selectbox(
            "Target Database",
            ["","SAP HANA","Oracle","MS SQL Server"],
            key="up_tdb"
        )
    with col3:
        os_plat = st.selectbox(
            "OS Platform",
            ["","Linux RHEL 8","Linux RHEL 9",
             "Linux SLES 15","Windows Server 2022","IBM AIX"],
            key="up_os"
        )
        timeline = st.selectbox(
            "Project Timeline",
            ["","3 months","6 months",
             "9 months","12 months","18 months"],
            key="up_tl"
        )

    col_a, col_b = st.columns(2)
    with col_a:
        has_cc = st.checkbox(
            "Has Custom Code / Z-Developments",
            value=True, key="up_cc"
        )
        ha_req = st.checkbox(
            "High Availability Required",
            value=False, key="up_ha"
        )
    with col_b:
        has_if = st.checkbox(
            "Has Interface Connections",
            value=True, key="up_if"
        )
        non_uc = st.checkbox(
            "Non-Unicode System",
            value=False, key="up_uc"
        )

    if st.button(
        "🚀 Generate Complete Upgrade Plan",
        type="primary", use_container_width=True
    ):
        if not src_release or not tgt_release:
            st.warning(
                "⚠️ Please enter both Source Release and Target Release."
            )
            return

        context = (
            f"Upgrade from {src_release} ({src_db}) "
            f"to {tgt_release} ({tgt_db}). "
            f"OS: {os_plat}. Timeline: {timeline}. "
            f"Custom code: {has_cc}. Interfaces: {has_if}. "
            f"HA: {ha_req}. Non-Unicode: {non_uc}."
        )
        upgrade_q = (
            f"Generate detailed upgrade project plan "
            f"from {src_release} to {tgt_release}"
        )

        with st.spinner("📋 Building your upgrade plan…"):
            ai_plan = get_ai_answer(
                upgrade_q, context,
                st.session_state.api_key,
                f"{src_release} → {tgt_release}",
            )

        st.markdown("---")
        st.markdown(
            f"## 📋 Upgrade Plan: "
            f"**{src_release}** → **{tgt_release}**"
        )

        # Timeline visual
        if timeline:
            months_m = re.search(r"\d+", timeline)
            months = int(months_m.group()) if months_m else 6
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
            for i, (ph, pct, col) in enumerate(phase_data):
                wks = max(1, round(months * 4 * pct / 100))
                with tl_cols[i]:
                    st.markdown(
                        f'<div style="background:{col};color:#fff;'
                        f'border-radius:10px;padding:.6rem .4rem;'
                        f'text-align:center;font-size:.78rem;'
                        f'font-weight:600">'
                        f'{ph}<br>'
                        f'<span style="font-size:1.05rem;font-weight:700">'
                        f'~{wks}w</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        st.markdown("<br>", unsafe_allow_html=True)

        phases = [
            ("🔍 Phase 1: Assessment & Planning", [
                "System inventory: release, SP level, add-ons (SPAM/SAINT)",
                "SAP Readiness Check: /SDF/RC_START_CHECK — resolve ALL findings",
                "Review PAM for target release compatibility",
                "Custom code analysis via SCMA / ATC",
                "Hardware sizing validation with SAP Quick Sizer",
                "Interface mapping: SM59, WE20, SOAMANAGER",
                "Define project scope, risks, timeline, team RACI",
            ]),
            ("📥 Phase 2: Infrastructure & Downloads", [
                f"Prepare target OS: {os_plat or 'Linux RHEL 8/9 or SLES 15'}",
                "Apply OS kernel parameters (SAP Note 900929)",
                f"Install / upgrade database: {tgt_db or 'SAP HANA'}",
                "Download SUM (latest) from support.sap.com/swdc",
                f"Download {tgt_release} media from SWDC",
                "Generate Stack.xml via SAP Maintenance Planner",
                "Prepare SUM staging directory (min 100 GB free)",
                "Perform dry-run upgrade on sandbox copy",
            ]),
            ("🔧 Phase 3: System Preparation", [
                "Apply prerequisite Support Package (SAP Note 2186744)",
                "Complete ALL custom code remediations (zero critical ATC)",
                "Freeze transport landscape (STMS) — import all pending",
                "Full DB backup with verified restore test",
                "Export SAP profiles: /usr/sap/<SID>/SYS/profile/",
                "Document system config: RZ10, SM59, STMS, SM30",
                "Run SUM EXTRACTONLY: ./STARTUP EXTRACTONLY",
                "Fix ALL ERRORS in SUM pre-check before proceeding",
                "Formal go / no-go approval from stakeholders",
            ]),
            ("⚡ Phase 4: Upgrade Execution (Downtime Window)", [
                "Send final maintenance window notification to all users",
                "Lock all non-admin users — start of planned downtime",
                "Start SUM: cd <SUM_DIR> && ./STARTUP (ABAP mode)",
                "Monitor SUM UI: https://<host>:1129/lmsl/sumabap/<SID>/doc/",
                "Handle SPDD prompt: adjust Data Dictionary modifications",
                "Handle SPAU prompt: adjust Repository object modifications",
                "DMO database migration (if converting from AnyDB to HANA)",
                "Verify system starts correctly after SUM completes",
            ]),
            ("✅ Phase 5: Post-Upgrade & Validation", [
                "Apply latest SAP Kernel patches (64-bit Unicode)",
                "Run RUTPOADAPT post-upgrade adaptation report",
                "Apply recommended post-upgrade SAP Notes",
                "Performance testing and parameter tuning (RZ10, ST05)",
                "Smoke testing: FI, MM, SD, HCM, PP core transactions",
                "Security review and authorization adjustment (SU25/SU24)",
                "User Acceptance Testing (UAT) formal sign-off",
            ]),
            ("🚀 Phase 6: Go-Live & Stabilization", [
                "Production cutover per approved cutover checklist",
                "Re-activate transport routes (STMS)",
                "Intensive hypercare monitoring: SM50, SM66, ST05, DBACOCKPIT",
                "Performance comparison vs pre-upgrade baseline",
                "Interface reconnection and integration verification",
                "End-user communication and training",
                "Project closure, lessons learned, documentation update",
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

        st.markdown("---")
        st.markdown("#### 🤖 AI-Enhanced Recommendations")
        st.markdown(
            f'<div class="answer-box">{ai_plan}</div>',
            unsafe_allow_html=True,
        )

        # Key SAP Notes
        st.markdown("---")
        st.markdown("#### 📋 Key SAP Notes for This Upgrade")
        key_notes = [
            ("2568780", "SUM — Software Update Manager master note"),
            ("2913617", "SAP Readiness Check for S/4HANA"),
            ("2399707", "S/4HANA technical prerequisites"),
            ("2383326", "SAP Maintenance Planner scenarios"),
            ("2186744", "Pre-upgrade checklist and minimum SP levels"),
            ("2176227", "Disk space requirements for SUM workspace"),
            ("2622660", "SUM best practices and recommendations"),
            ("1680045", "Installation and upgrade best practices"),
            ("941735",  "Memory management parameters"),
            ("900929",  "OS kernel parameters for SAP on Linux"),
            ("2190420", "Custom Code Migration — SCMA / ATC"),
            ("1979523", "Software Lifecycle Platform overview"),
        ]
        note_cols = st.columns(3)
        for i, (n_num, n_desc) in enumerate(key_notes):
            with note_cols[i % 3]:
                st.markdown(
                    f'<div class="source-card" style="padding:.6rem 1rem">'
                    f'<a href="https://launchpad.support.sap.com/'
                    f'#/notes/{n_num}" target="_blank">'
                    f'📋 SAP Note {n_num}</a><br>'
                    f'<small style="color:#374151">{n_desc}</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.session_state.conversation.append({
            "question": upgrade_q,
            "answer":   ai_plan,
            "sources":  [],
            "product":  f"{src_release} → {tgt_release}",
        })


# ============================================================
# TAB 4 — UPGRADE MATRIX
# ============================================================
def tab_upgrade_matrix():
    st.markdown("### 🔄 SAP Upgrade Path Matrix")
    st.markdown(
        '<div class="info-box">📊 Select your source release to see all '
        'supported upgrade targets, upgrade type, tool, mandatory stops, '
        'and key SAP Note reference for each path.</div>',
        unsafe_allow_html=True,
    )

    selected_source = st.selectbox(
        "Select your current (source) release",
        list(UPGRADE_PATHS.keys()),
        key="matrix_source",
    )
    if selected_source not in UPGRADE_PATHS:
        return

    targets = UPGRADE_PATHS[selected_source]
    st.markdown(
        f"#### {len(targets)} supported upgrade target(s) "
        f"from **{selected_source}**"
    )

    type_colors = {
        "System Conversion": "#fee2e2",
        "Release Upgrade":   "#e0f2fe",
        "EHP Upgrade":       "#f0fdf4",
        "Database Upgrade":  "#fef3c7",
        "Revision Upgrade":  "#f5f3ff",
    }

    rows_html = ""
    for tgt, info in targets.items():
        stops_html = (
            " → ".join(
                f'<span style="background:#fef3c7;padding:2px 8px;'
                f'border-radius:4px;font-size:.78rem">{s}</span>'
                for s in info["stops"]
            )
            if info["stops"]
            else '<span style="color:#16a34a;font-weight:600">'
                 '✅ Direct upgrade</span>'
        )
        note_html = (
            f'<a href="https://launchpad.support.sap.com/'
            f'#/notes/{info["note"]}" target="_blank">'
            f'📋 {info["note"]}</a>'
        ) if info.get("note") else "—"
        type_bg = type_colors.get(info["type"], "#f8fafc")
        rows_html += (
            f'<tr>'
            f'<td style="padding:8px 14px;border:1px solid #e5e7eb;'
            f'font-weight:600;color:#0057A8">{tgt}</td>'
            f'<td style="padding:8px 14px;border:1px solid #e5e7eb;'
            f'background:{type_bg}">{info["type"]}</td>'
            f'<td style="padding:8px 14px;border:1px solid #e5e7eb;'
            f'font-family:monospace;font-size:.88rem">{info["tool"]}</td>'
            f'<td style="padding:8px 14px;border:1px solid #e5e7eb">'
            f'{stops_html}</td>'
            f'<td style="padding:8px 14px;border:1px solid #e5e7eb">'
            f'{note_html}</td>'
            f'</tr>'
        )

    st.markdown(
        f'<table style="width:100%;border-collapse:collapse;'
        f'font-size:.875rem">'
        f'<thead><tr style="background:#0057A8;color:#fff">'
        f'<th style="padding:9px 14px;text-align:left">Target Release</th>'
        f'<th style="padding:9px 14px;text-align:left">Upgrade Type</th>'
        f'<th style="padding:9px 14px;text-align:left">Tool</th>'
        f'<th style="padding:9px 14px;text-align:left">Required Stops</th>'
        f'<th style="padding:9px 14px;text-align:left">Key SAP Note</th>'
        f'</tr></thead><tbody>{rows_html}</tbody></table>',
        unsafe_allow_html=True,
    )

    # Legend
    st.markdown("<br>**Legend — Upgrade Types:**", unsafe_allow_html=True)
    leg_cols = st.columns(len(type_colors))
    for i, (utype, ucolor) in enumerate(type_colors.items()):
        with leg_cols[i]:
            st.markdown(
                f'<div style="background:{ucolor};border-radius:6px;'
                f'padding:.3rem .6rem;font-size:.78rem;font-weight:600;'
                f'text-align:center;border:1px solid #e5e7eb">'
                f'{utype}</div>',
                unsafe_allow_html=True,
            )

    # Compatibility checker
    st.markdown("---")
    st.markdown("#### 🔍 Quick Compatibility Validator")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        chk_db = st.selectbox(
            "Target Database",
            ["SAP HANA","Oracle","MS SQL Server","IBM DB2"],
            key="chk_db"
        )
    with cc2:
        chk_os = st.selectbox(
            "OS Platform",
            ["Linux RHEL 8","Linux RHEL 9","Linux SLES 15",
             "Windows Server 2019","Windows Server 2022"],
            key="chk_os"
        )
    with cc3:
        chk_tgt = st.selectbox(
            "Target Release",
            list(targets.keys()),
            key="chk_tgt"
        )

    if st.button("🔍 Check Compatibility", use_container_width=True):
        errors, warnings, infos = [], [], []
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
        if ("ecc" in selected_source.lower()
                or "erp" in selected_source.lower()):
            infos.append(
                "ECC → S/4HANA requires Simplification Item check "
                "(SAP Note 2121861)."
            )
            infos.append(
                "Unicode conversion required if source is non-Unicode "
                "(SAP Note 73606)."
            )
            infos.append(
                "Run SAP Readiness Check (/SDF/RC_START_CHECK) on "
                "source system before starting."
            )
        if "hana 1.0" in selected_source.lower():
            warnings.append(
                "HANA 1.0 → 2.0 requires careful revision path planning. "
                "Review SAP Note 2380493."
            )
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
# TAB 5 — PARAMETERS
# ============================================================
def tab_parameters():
    st.markdown("### ⚙️ SAP Parameter Recommendation Engine")
    st.markdown(
        '<div class="info-box">⚙️ Select your product and system '
        'specifications to get dynamically sized parameter recommendations '
        'with SAP Note references. Download as a ready-to-use '
        'profile snippet.</div>',
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
        param_cat = (
            st.selectbox("Category", cats, key="param_cat")
            if cats else None
        )
    with col3:
        param_os = st.selectbox(
            "OS Platform (optional)",
            ["None"] + list(OS_PARAMETERS.keys()),
            key="param_os",
        )

    s1, s2, s3 = st.columns(3)
    with s1:
        ram_gb  = st.number_input(
            "Total RAM (GB)", min_value=16,
            max_value=65536, value=256, step=16, key="p_ram"
        )
    with s2:
        n_users = st.number_input(
            "Concurrent Users", min_value=1,
            max_value=50000, value=200, step=50, key="p_usr"
        )
    with s3:
        n_cpu   = st.number_input(
            "CPU Cores", min_value=1,
            max_value=512, value=32, step=4, key="p_cpu"
        )

    if st.button(
        "⚙️ Generate Parameter Recommendations",
        type="primary", use_container_width=True
    ):
        params = PARAMETER_DATABASE.get(param_prod, {}).get(param_cat, {})

        if params:
            st.markdown(
                f"#### ⚙️ {param_prod} — "
                f"{(param_cat or '').title()} Parameters"
            )
            st.caption(
                f"Sized for: {ram_gb} GB RAM · "
                f"{n_cpu} CPU cores · {n_users} concurrent users"
            )

            table_rows   = ""
            snippet_lines = [
                f"# {param_prod} — {param_cat} Parameters",
                f"# Sized for: {ram_gb} GB RAM | "
                f"{n_cpu} CPUs | {n_users} concurrent users",
                f"# Generated: "
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "",
            ]

            for idx, (pname, pdata) in enumerate(params.items()):
                value = pdata["value"]
                unit  = pdata.get("unit", "")

                # Dynamic sizing
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
                    value = str(
                        int(ram_gb * 0.08 * 1024 * 1024 * 1024)
                    )
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
                elif (
                    "global_allocation_limit" in pname
                    and param_prod == "SAP HANA"
                ):
                    value = str(int(ram_gb * 0.80 * 1024))
                    unit  = "MB"
                elif "shared_objects_size_MB" in pname:
                    value = str(max(256, int(ram_gb * 0.02 * 1024)))

                note_html = (
                    f'<a href="https://launchpad.support.sap.com/'
                    f'#/notes/{pdata["note"]}" target="_blank" '
                    f'style="font-size:.82rem">📋 {pdata["note"]}</a>'
                ) if pdata.get("note") else "—"

                row_bg = "#f8fafc" if idx % 2 == 0 else "#ffffff"
                table_rows += (
                    f'<tr style="background:{row_bg}">'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;'
                    f'font-family:monospace;color:#0057A8;'
                    f'font-size:.84rem">{pname}</td>'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;'
                    f'font-family:monospace;font-weight:700;'
                    f'font-size:.84rem">{value}</td>'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;'
                    f'color:#6b7280;font-size:.82rem">{unit}</td>'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;'
                    f'font-size:.84rem">{pdata.get("desc","")}</td>'
                    f'<td style="padding:7px 12px;'
                    f'border:1px solid #e5e7eb">{note_html}</td>'
                    f'</tr>'
                )
                snippet_lines.append(
                    f"{pname:<45} = {value:<20}  "
                    f"# {pdata.get('desc','')}"
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
                    f"sap_params_"
                    f"{param_prod.replace(' ','_')}_"
                    f"{param_cat}_"
                    f"{datetime.datetime.now().strftime('%Y%m%d')}.txt"
                ),
                mime="text/plain",
                use_container_width=True,
            )

        # OS Parameters section
        if param_os != "None":
            st.markdown(
                f"---\n#### 🐧 OS Kernel Parameters — {param_os}"
            )
            st.caption(
                f"Calculated for: {ram_gb} GB RAM · {n_cpu} CPU cores"
            )
            os_params   = OS_PARAMETERS.get(param_os, {})
            os_rows     = ""
            sysctl_lines = [
                "# /etc/sysctl.conf — SAP recommended OS kernel parameters",
                f"# Platform: {param_os}",
                f"# System: {ram_gb} GB RAM | {n_cpu} CPUs | {n_users} users",
                f"# Generated: "
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "# Apply with: sysctl -p /etc/sysctl.conf",
                "",
            ]

            for idx, (pname, pdata) in enumerate(os_params.items()):
                val = pdata["value"]
                if "shmmax" in pname:
                    val = str(int(ram_gb * 1024 * 1024 * 1024))
                elif "shmall" in pname:
                    val = str(
                        int(ram_gb * 1024 * 1024 * 1024 // 4096)
                    )

                note_html = (
                    f'<a href="https://launchpad.support.sap.com/'
                    f'#/notes/{pdata["note"]}" target="_blank" '
                    f'style="font-size:.82rem">📋 {pdata["note"]}</a>'
                ) if pdata.get("note") else "—"

                row_bg = "#f8fafc" if idx % 2 == 0 else "#ffffff"
                os_rows += (
                    f'<tr style="background:{row_bg}">'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;'
                    f'font-family:monospace;color:#374151;'
                    f'font-size:.84rem">{pname}</td>'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;'
                    f'font-family:monospace;font-weight:700;'
                    f'font-size:.84rem">{val}</td>'
                    f'<td style="padding:7px 12px;border:1px solid #e5e7eb;'
                    f'font-size:.84rem">{pdata.get("desc","")}</td>'
                    f'<td style="padding:7px 12px;'
                    f'border:1px solid #e5e7eb">{note_html}</td>'
                    f'</tr>'
                )
                sysctl_lines.append(
                    f"{pname:<45} = {val:<20}  "
                    f"# {pdata.get('desc','')}"
                )

            st.markdown(
                f'<table style="width:100%;border-collapse:collapse;'
                f'font-size:.875rem">'
                f'<thead><tr style="background:#374151;color:#fff">'
                f'<th style="padding:9px 14px;text-align:left">'
                f'Parameter</th>'
                f'<th style="padding:9px 14px;text-align:left">Value</th>'
                f'<th style="padding:9px 14px;text-align:left">'
                f'Description</th>'
                f'<th style="padding:9px 14px;text-align:left">'
                f'SAP Note</th>'
                f'</tr></thead><tbody>{os_rows}</tbody></table>',
                unsafe_allow_html=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="⬇️ Download sysctl.conf Snippet",
                data="\n".join(sysctl_lines),
                file_name=(
                    f"sysctl_sap_"
                    f"{param_os.replace(' ','_').replace('/','_')}_"
                    f"{datetime.datetime.now().strftime('%Y%m%d')}.conf"
                ),
                mime="text/plain",
                use_container_width=True,
            )

        if not params and param_os == "None":
            st.markdown(
                '<div class="warn-box">⚠️ Please select a parameter '
                'category or an OS platform to generate '
                'recommendations.</div>',
                unsafe_allow_html=True,
            )


# ============================================================
# TAB 6 — CHECKLIST
# ============================================================
def tab_checklist_ui():
    st.markdown("### ✅ Pre-Upgrade Checklist Generator")
    st.markdown(
        '<div class="info-box">📋 Generate a complete, prioritized '
        'pre-upgrade checklist tailored to your specific upgrade scenario. '
        'Download as CSV to use in Excel or your project management '
        'tool.</div>',
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
        cl_cc = st.checkbox(
            "Has Custom Code / Z-Developments",
            value=True, key="cl_cc"
        )
        cl_if = st.checkbox(
            "Has Interface Connections",
            value=True, key="cl_if"
        )
        cl_ha = st.checkbox(
            "High Availability Required",
            value=False, key="cl_ha"
        )
        cl_uc = st.checkbox(
            "Non-Unicode System",
            value=False, key="cl_uc"
        )

    if st.button(
        "📋 Generate Checklist",
        type="primary", use_container_width=True
    ):
        opts = {
            "has_custom_code": cl_cc,
            "has_interfaces":  cl_if,
            "ha_required":     cl_ha,
            "non_unicode":     cl_uc,
        }
        checklist = generate_checklist(cl_src, cl_tgt, opts)
        st.session_state.last_checklist = checklist

        total    = len(checklist)
        critical = sum(1 for x in checklist if x["pri"] == "Critical")
        high     = sum(1 for x in checklist if x["pri"] == "High")
        medium   = sum(1 for x in checklist if x["pri"] == "Medium")

        st.markdown(
            f"---\n#### 📋 {cl_src} → {cl_tgt} — Pre-Upgrade Checklist"
        )

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="value">{total}</div>'
                f'<div class="label">Total Items</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="value" style="color:#dc2626">{critical}</div>'
                f'<div class="label">🔴 Critical</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with m3:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="value" style="color:#d97706">{high}</div>'
                f'<div class="label">🟡 High</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with m4:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="value" style="color:#2563eb">{medium}</div>'
                f'<div class="label">🔵 Medium</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

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
                    pri          = item["pri"]
                    bg_color     = {
                        "Critical": "#fee2e2",
                        "High":     "#fef3c7",
                    }.get(pri, "#f0fdf4")
                    border_color = {
                        "Critical": "#dc2626",
                        "High":     "#d97706",
                    }.get(pri, "#2563eb")
                    badge_class  = {
                        "Critical": "critical-badge",
                        "High":     "high-badge",
                    }.get(pri, "medium-badge")
                    note_link = (
                        f' &nbsp;·&nbsp; 🔗 '
                        f'<a href="https://launchpad.support.sap.com'
                        f'/#/notes/{item["note"]}" target="_blank">'
                        f'SAP Note {item["note"]}</a>'
                    ) if item.get("note") else ""

                    st.markdown(
                        f'<div style="background:{bg_color};'
                        f'border-left:4px solid {border_color};'
                        f'border-radius:8px;padding:.75rem 1rem;'
                        f'margin:.4rem 0">'
                        f'<strong>{item["task"]}</strong> '
                        f'<span class="{badge_class}">{pri}</span><br>'
                        f'<small style="color:#374151">'
                        f'{item["detail"]}</small><br>'
                        f'<small style="color:#6b7280">'
                        f'🔧 <em>{item["tool"]}</em>{note_link}'
                        f'</small>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        csv_lines = [
            "Priority,Category,Task,Detail,Tool / Transaction,SAP Note"
        ]
        for item in checklist:
            csv_lines.append(
                f'"{item["pri"]}","{item["cat"]}",'
                f'"{item["task"]}","{item["detail"]}",'
                f'"{item["tool"]}","{item.get("note","")}"'
            )

        st.download_button(
            label="⬇️ Download Checklist as CSV",
            data="\n".join(csv_lines),
            file_name=(
                f"sap_upgrade_checklist_"
                f"{cl_src.replace(' ','_')}_to_"
                f"{cl_tgt.replace(' ','_')}_"
                f"{datetime.datetime.now().strftime('%Y%m%d')}.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )
        # ============================================================
# PART 6 OF 6 — Tab7 Conversation, Tab8 Reports,
#                Tab9 Resources, main()
# SAP Help Navigator Pro
# ============================================================

# ============================================================
# TAB 7 — CONVERSATION HISTORY
# ============================================================
def tab_conversation():
    st.markdown("### 💬 Conversation History")
    st.markdown(
        '<div class="info-box">All questions and answers from this '
        'session are saved here. Use the Reports tab to export them '
        'as a formatted HTML report.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.conversation:
        st.markdown(
            '<div class="info-box">💬 No conversations yet. '
            'Use the Search &amp; Ask tab to get started.</div>',
            unsafe_allow_html=True,
        )
        return

    col_info, col_clear = st.columns([4, 1])
    with col_info:
        st.markdown(
            f"**{len(st.session_state.conversation)} "
            f"Q&A pair(s) in this session**"
        )
    with col_clear:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.conversation = []
            st.rerun()

    for i, entry in enumerate(reversed(st.session_state.conversation)):
        idx       = len(st.session_state.conversation) - i
        q_preview = entry["question"][:80]
        prod_badge = (
            f' <span class="chip">'
            f'{entry.get("product","SAP")}</span>'
            if entry.get("product") else ""
        )
        with st.expander(
            f"Q{idx}: {q_preview}"
            f"{'…' if len(entry['question']) > 80 else ''}",
            expanded=(i == 0),
        ):
            st.markdown(
                f'**❓ Question:** {entry["question"]}'
                f'{prod_badge}',
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
                        f'<a href="{src["url"]}" target="_blank">'
                        f'📄 {src["title"]}</a>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )


# ============================================================
# TAB 8 — REPORTS
# ============================================================
def tab_reports():
    st.markdown("### 📄 Export Reports & Session Data")
    st.markdown(
        '<div class="info-box">📄 Generate a self-contained, '
        'print-ready HTML report combining your Q&A, pre-upgrade '
        'checklist, and source references. Also export the full '
        'session as JSON.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.conversation:
        st.markdown(
            '<div class="warn-box">⚠️ No Q&amp;A data yet. '
            'Use the Search &amp; Ask tab to ask questions first, '
            'then return here to generate your report.</div>',
            unsafe_allow_html=True,
        )
        return

    last_qa = st.session_state.conversation[-1]

    # Summary metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="value">'
            f'{len(st.session_state.conversation)}</div>'
            f'<div class="label">💬 Q&amp;A Pairs</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="value">'
            f'{len(st.session_state.fetched_docs)}</div>'
            f'<div class="label">📄 Docs Fetched</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m3:
        cl_count = len(st.session_state.get("last_checklist", []))
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="value">{cl_count}</div>'
            f'<div class="label">✅ Checklist Items</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="value">'
            f'{len(st.session_state.search_history)}</div>'
            f'<div class="label">🔍 Searches</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Report options
    st.markdown("#### 📄 HTML Report Options")
    rpt_col1, rpt_col2 = st.columns(2)
    with rpt_col1:
        include_checklist = st.checkbox(
            "Include pre-upgrade checklist in report",
            value=bool(st.session_state.get("last_checklist")),
            key="rpt_incl_cl",
        )
    with rpt_col2:
        use_all_qa = st.checkbox(
            "Include all Q&A pairs "
            "(unchecked = last Q&A only)",
            value=False,
            key="rpt_all_qa",
        )

    qa_entries = (
        st.session_state.conversation
        if use_all_qa
        else [last_qa]
    )

    if use_all_qa and len(qa_entries) > 1:
        combined_question = (
            f"{len(qa_entries)} questions — see report for full list"
        )
        combined_answer = "\n\n---\n\n".join(
            f"**Q{i+1}: {e['question']}**\n\n{e['answer']}"
            for i, e in enumerate(qa_entries)
        )
    else:
        combined_question = last_qa["question"]
        combined_answer   = last_qa["answer"]

    combined_sources = []
    seen_urls = set()
    for entry in qa_entries:
        for src in entry.get("sources", []):
            if src["url"] not in seen_urls:
                seen_urls.add(src["url"])
                combined_sources.append(src)

    if st.button(
        "📄 Generate & Download HTML Report",
        type="primary", use_container_width=True
    ):
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
        ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SAP_Help_Navigator_Report_{ts}.html"

        st.download_button(
            label     = f"⬇️ Download {filename}",
            data      = html_content,
            file_name = filename,
            mime      = "text/html",
            use_container_width=True,
        )
        with st.expander("👁️ Preview Report"):
            st.components.v1.html(
                html_content, height=550, scrolling=True
            )

    # JSON and CSV exports
    st.markdown("---")
    st.markdown("#### 📦 Export Session Data")
    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        if st.button(
            "📦 Export Full Session as JSON",
            use_container_width=True
        ):
            session_data = {
                "exported_at":    datetime.datetime.now().isoformat(),
                "product":        st.session_state.current_product,
                "total_qa_pairs": len(st.session_state.conversation),
                "conversation":   st.session_state.conversation,
                "search_history": st.session_state.search_history,
                "checklist":      st.session_state.get(
                    "last_checklist", []
                ),
                "docs_fetched":   list(
                    st.session_state.fetched_docs.keys()
                ),
            }
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label     = "⬇️ Download session.json",
                data      = json.dumps(
                    session_data, indent=2, default=str
                ),
                file_name = f"sap_navigator_session_{ts}.json",
                mime      = "application/json",
                use_container_width=True,
            )

    with exp_col2:
        cl_available = bool(st.session_state.get("last_checklist"))
        if st.button(
            "📋 Export Checklist as CSV",
            use_container_width=True,
            disabled=not cl_available,
        ):
            cl = st.session_state.get("last_checklist", [])
            csv_lines = [
                "Priority,Category,Task,Detail,"
                "Tool / Transaction,SAP Note"
            ]
            for item in cl:
                csv_lines.append(
                    f'"{item["pri"]}","{item["cat"]}",'
                    f'"{item["task"]}","{item["detail"]}",'
                    f'"{item["tool"]}","'
                    f'{item.get("note","")}"'
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
# TAB 9 — RESOURCES
# ============================================================
def tab_resources():
    st.markdown("### 📚 SAP Resource Library")
    st.markdown(
        '<div class="info-box">🔗 Curated collection of official SAP '
        'portals, essential SAP Notes organised by topic, and a guide '
        'finder to locate exact documentation you need.</div>',
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 🔗 Official SAP Portals")
        portals = [
            ("🔷 SAP Help Portal",
             "https://help.sap.com/docs",
             "All SAP product documentation — publicly accessible"),
            ("🛠️ SAP Support Portal",
             "https://support.sap.com",
             "Support cases, SAP Notes, EarlyWatch Alert"),
            ("⬇️ SAP Software Download Center",
             "https://support.sap.com/swdc",
             "Download SAP software, patches, SUM, SWPM"),
            ("📦 SAP Maintenance Planner",
             "https://support.sap.com/mp",
             "Generate Stack.xml for system upgrades"),
            ("📊 Product Availability Matrix",
             "https://apps.support.sap.com/sap/support/pam",
             "OS, database, and component compatibility"),
            ("🎓 SAP Learning Hub",
             "https://learning.sap.com",
             "Official SAP training courses and certifications"),
            ("🌍 SAP Community",
             "https://community.sap.com",
             "Q&A, technical blogs, and discussions"),
            ("🚀 SAP Best Practices Explorer",
             "https://rapid.sap.com/bp/",
             "Pre-built best practice content for S/4HANA"),
            ("🔑 SAP Launchpad (Notes / KBAs)",
             "https://launchpad.support.sap.com",
             "SAP Notes, KBAs, system information"),
            ("📱 SAP Fiori Apps Library",
             "https://fioriappslibrary.hana.ondemand.com",
             "Browse 2000+ SAP Fiori application details"),
            ("📐 SAP Quick Sizer",
             "https://service.sap.com/quicksizer",
             "Hardware sizing estimation tool"),
            ("🔒 SAP Trust Center",
             "https://www.sap.com/about/trust-center.html",
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
                ("2568780", "SUM — Software Update Manager master note"),
                ("2913617", "SAP Readiness Check for S/4HANA"),
                ("2399707", "S/4HANA technical prerequisites"),
                ("2383326", "SAP Maintenance Planner scenarios"),
                ("2186744", "Pre-upgrade checklist and minimum SP levels"),
                ("2176227", "Disk space requirements for SUM workspace"),
                ("2622660", "SUM best practices and recommendations"),
                ("2121861", "Simplification Items for S/4HANA"),
                ("73606",   "Unicode conversion for SAP systems"),
            ],
            "💾 Installation": [
                ("1680045", "Installation best practices"),
                ("2393060", "sapinst / SWPM troubleshooting"),
                ("1979523", "Software Lifecycle Platform overview"),
                ("2235581", "SAP HANA installation on Linux"),
                ("1639498", "How to download SAP software"),
            ],
            "⚙️ Performance & Parameters": [
                ("941735",  "ABAP memory management parameters"),
                ("2222200", "Recommended SAP HANA settings"),
                ("1984787", "OS kernel parameters for SAP on Linux"),
                ("1999997", "SAP HANA memory configuration FAQ"),
                ("103747",  "ABAP buffer tuning guidelines"),
                ("15360",   "Work process runtime parameters"),
                ("900929",  "OS parameters: vm.max_map_count etc."),
            ],
            "🛡️ Security": [
                ("1484000", "SAP Security Guide overview"),
                ("862989",  "Login and password profile parameters"),
                ("1408081", "RFC security — authority checks"),
                ("539404",  "Security Audit Log configuration"),
                ("68048",   "Default SAP* and DDIC password handling"),
                ("2216823", "Security hardening recommendations"),
            ],
            "🗄️ SAP HANA": [
                ("2380493", "SAP HANA upgrade paths and revisions"),
                ("1999993", "SAP HANA Mini Checks (run monthly)"),
                ("2084065", "HANA delta merge optimization"),
                ("2127458", "HANA column store memory unload settings"),
                ("1975256", "HANA backup buffer configuration"),
                ("1999880", "HANA System Replication overview"),
            ],
        }

        for topic, notes in notes_by_topic.items():
            st.markdown(f"**{topic}**")
            for note_num, note_desc in notes:
                st.markdown(
                    f'<div class="source-card" '
                    f'style="padding:.5rem 1rem;margin:.2rem 0">'
                    f'<a href="https://launchpad.support.sap.com/'
                    f'#/notes/{note_num}" target="_blank">'
                    f'📋 SAP Note {note_num}</a>'
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
        'for any SAP product.</div>',
        unsafe_allow_html=True,
    )
    gf1, gf2, gf3 = st.columns([2, 2, 1])
    with gf1:
        gf_product = st.selectbox(
            "Product",
            [
                "SAP S/4HANA", "SAP HANA", "SAP BTP",
                "SAP NetWeaver", "SAP Solution Manager",
                "SAP Fiori", "SAP ABAP Platform",
                "SAP BW/4HANA", "SAP Integration Suite",
            ],
            key="gf_prod",
        )
    with gf2:
        gf_type = st.selectbox(
            "Guide Type",
            [
                "Master Guide", "Installation Guide",
                "Upgrade Guide", "Security Guide",
                "Administration Guide", "Operations Guide",
                "High Availability Guide", "Sizing Guide",
                "Tuning Guide", "Release Notes",
            ],
            key="gf_type",
        )
    with gf3:
        st.markdown("<br>", unsafe_allow_html=True)
        gf_search = st.button(
            "🔍 Find Guides", use_container_width=True
        )

    if gf_search:
        search_query = f"{gf_product} {gf_type}"
        with st.spinner(f"Searching for '{search_query}'…"):
            guide_results = search_sap_help(search_query, gf_product)
        if guide_results:
            st.markdown(f"**Results for '{search_query}':**")
            for gr in guide_results[:6]:
                st.markdown(
                    f'<div class="source-card">'
                    f'<a href="{gr["url"]}" target="_blank">'
                    f'📄 {gr["title"]}</a><br>'
                    f'<small style="color:#6b7280">'
                    f'{gr.get("description","")[:110]}</small><br>'
                    f'<small style="color:#94a3b8">'
                    f'{gr["url"][:70]}</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info(
                f"No results for '{search_query}'. "
                f"Try browsing "
                f"[help.sap.com/docs](https://help.sap.com/docs) "
                f"directly."
            )


# ============================================================
# MAIN — entry point
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
            f'<div class="value">'
            f'{len(st.session_state.fetched_docs)}</div>'
            f'<div class="label">📄 Docs Fetched</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with mc2:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="value">'
            f'{len(st.session_state.conversation)}</div>'
            f'<div class="label">💬 Q&amp;A Pairs</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with mc3:
        display_product = (
            (product[:13] + "…")
            if product and len(product) > 13
            else (product or "—")
        )
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="value" style="font-size:.88rem">'
            f'{display_product}</div>'
            f'<div class="label">📦 Product</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with mc4:
        mode_label = (
            "🤖 Gemini AI"
            if st.session_state.api_key
            else "📐 Rule-based"
        )
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="value" style="font-size:.85rem">'
            f'{mode_label}</div>'
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


if __name__ == "__main__":
    main()
    
