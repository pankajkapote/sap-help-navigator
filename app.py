
---

Now here is the **complete, production-ready app** with Streamlit Cloud secrets integration built in:

```python
# ============================================================
# app.py  ← THIS IS YOUR MAIN FILE
# SAP Help Navigator Pro — Streamlit Cloud Ready
# ============================================================

import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, quote
import datetime
import base64
import math
from typing import Optional
from collections import defaultdict

# ── Optional AI import ──────────────────────────────────────
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# ============================================================
# PAGE CONFIG  (must be FIRST Streamlit call)
# ============================================================
st.set_page_config(
    page_title  = "SAP Help Navigator Pro",
    page_icon   = "🔷",
    layout      = "wide",
    initial_sidebar_state = "expanded",
    menu_items  = {
        "Get Help"    : "https://help.sap.com/docs",
        "Report a bug": None,
        "About"       : "SAP Help Navigator Pro — Powered by help.sap.com & Google Gemini",
    }
)

# ============================================================
# ★  STREAMLIT CLOUD SECRETS  ★
# The key is stored in Streamlit Cloud dashboard → Secrets
# Locally, create .streamlit/secrets.toml  (git-ignored)
# ============================================================
def load_api_key() -> str:
    """
    Priority order:
      1. Already stored in session_state (user typed it in sidebar)
      2. Streamlit Cloud secrets
      3. Empty string → rule-based mode
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

# ============================================================
# FULL CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}

/* ── Header ── */
.main-header{
  background:linear-gradient(135deg,#0057A8 0%,#00A3E0 50%,#00D4AA 100%);
  padding:2rem 2.5rem;border-radius:16px;margin-bottom:1.5rem;
  box-shadow:0 8px 32px rgba(0,87,168,.25);color:#fff}
.main-header h1{font-size:2.1rem;font-weight:700;margin:0}
.main-header p{font-size:.95rem;opacity:.85;margin:.4rem 0 0}

/* ── Metric cards ── */
.metric-card{
  background:#fff;border:1px solid #e8edf3;border-radius:12px;
  padding:1.1rem 1.3rem;text-align:center;
  box-shadow:0 2px 8px rgba(0,0,0,.06);
  transition:transform .2s,box-shadow .2s}
.metric-card:hover{transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,.1)}
.metric-card .value{font-size:1.7rem;font-weight:700;color:#0057A8}
.metric-card .label{font-size:.78rem;color:#6b7280;margin-top:.3rem}

/* ── Answer box ── */
.answer-box{
  background:linear-gradient(135deg,#f0f7ff,#e8f5e9);
  border-left:4px solid #0057A8;border-radius:12px;
  padding:1.4rem 1.8rem;margin:1rem 0;line-height:1.8}

/* ── Source card ── */
.source-card{
  background:#fff;border:1px solid #dce3ec;border-radius:10px;
  padding:.9rem 1.1rem;margin:.45rem 0;
  box-shadow:0 1px 4px rgba(0,0,0,.05)}
.source-card a{color:#0057A8;text-decoration:none;font-weight:500}
.source-card a:hover{text-decoration:underline}

/* ── Step card ── */
.step-card{
  background:#fff;border:1px solid #e0e7ef;border-radius:10px;
  padding:.9rem 1.2rem;margin:.5rem 0;
  display:flex;align-items:flex-start;gap:1rem;
  box-shadow:0 1px 4px rgba(0,0,0,.05)}
.step-num{
  background:linear-gradient(135deg,#0057A8,#00A3E0);color:#fff;
  border-radius:50%;width:30px;height:30px;
  display:flex;align-items:center;justify-content:center;
  font-weight:700;font-size:.85rem;flex-shrink:0}

/* ── Colour boxes ── */
.info-box{background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
  padding:.9rem 1.1rem;margin:.5rem 0;font-size:.9rem;color:#1e40af}
.warn-box{background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
  padding:.9rem 1.1rem;margin:.5rem 0;font-size:.9rem;color:#92400e}
.success-box{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
  padding:.9rem 1.1rem;margin:.5rem 0;font-size:.9rem;color:#166534}
.error-box{background:#fef2f2;border:1px solid #fecaca;border-radius:10px;
  padding:.9rem 1.1rem;margin:.5rem 0;font-size:.9rem;color:#991b1b}

/* ── Param table ── */
.param-table{width:100%;border-collapse:collapse;font-size:.875rem}
.param-table th{background:#0057A8;color:#fff;padding:9px 14px;text-align:left;font-weight:600}
.param-table td{padding:7px 12px;border:1px solid #e5e7eb}
.param-table tr:nth-child(even) td{background:#f8fafc}

/* ── Badge chips ── */
.chip{display:inline-block;background:#e8f0fe;color:#0057A8;
  border-radius:20px;padding:.22rem .7rem;font-size:.75rem;font-weight:600;margin:.15rem}
.critical-badge{display:inline-block;background:#fee2e2;color:#991b1b;
  border:1px solid #fca5a5;border-radius:6px;padding:1px 7px;font-size:.73rem;font-weight:700}
.high-badge{display:inline-block;background:#fef3c7;color:#92400e;
  border:1px solid #fcd34d;border-radius:6px;padding:1px 7px;font-size:.73rem;font-weight:700}
.medium-badge{display:inline-block;background:#dbeafe;color:#1e40af;
  border:1px solid #93c5fd;border-radius:6px;padding:1px 7px;font-size:.73rem;font-weight:700}

/* ── Sidebar ── */
.sidebar-section{background:#f8fafc;border-radius:10px;padding:.75rem .9rem;
  margin-bottom:.9rem;border:1px solid #e2e8f0}

/* ── Buttons ── */
.stButton>button{border-radius:8px!important;font-weight:500!important;transition:all .2s!important}
.stButton>button:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,.15)!important}

/* ── Tab style ── */
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
    "Accept"         : "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ============================================================
# SESSION STATE
# ============================================================
_DEFAULTS = {
    "search_history" : [],
    "fetched_docs"   : {},
    "conversation"   : [],
    "api_key"        : "",
    "current_product": "",
    "doc_cache"      : {},
    "last_checklist" : [],
    "quick_q"        : "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Load secret key once at startup
if not st.session_state.api_key:
    st.session_state.api_key = load_api_key()

# ============================================================
# DATA — Parameters
# ============================================================
PARAMETER_DATABASE = {
    "SAP S/4HANA": {
        "memory": {
            "abap/heap_area_total"      : {"value":"2000000000","unit":"bytes","desc":"Total heap for all WPs",         "note":"941735"},
            "abap/heap_area_dia"        : {"value":"500000000", "unit":"bytes","desc":"Heap per dialog WP",            "note":"941735"},
            "abap/heap_area_nondia"     : {"value":"1000000000","unit":"bytes","desc":"Heap per non-dialog WP",        "note":"941735"},
            "em/initial_size_MB"        : {"value":"4096",      "unit":"MB",   "desc":"Extended memory initial size", "note":"747468"},
            "em/max_size_MB"            : {"value":"16384",     "unit":"MB",   "desc":"Extended memory max size",     "note":"747468"},
            "zcsa/table_buffer_area"    : {"value":"100000000", "unit":"bytes","desc":"Generic table buffer",         "note":"1418123"},
            "rsdb/obj/buffersize"       : {"value":"500000",    "unit":"KB",   "desc":"Repository object buffer",     "note":"1127888"},
            "ipc/shm_psize_40"          : {"value":"500000000", "unit":"bytes","desc":"Shared memory pool",           "note":"723909"},
        },
        "workprocesses": {
            "rdisp/wp_no_dia"           : {"value":"10","unit":"count","desc":"Dialog work processes",      "note":"39412"},
            "rdisp/wp_no_btc"           : {"value":"4", "unit":"count","desc":"Background work processes", "note":"39412"},
            "rdisp/wp_no_spo"           : {"value":"2", "unit":"count","desc":"Spool work processes",      "note":"39412"},
            "rdisp/wp_no_upd"           : {"value":"2", "unit":"count","desc":"Update work processes",     "note":"39412"},
            "rdisp/max_wprun_time"      : {"value":"600","unit":"sec", "desc":"Max dialog WP runtime",     "note":"15360"},
        },
        "security": {
            "login/min_password_lng"           : {"value":"8",  "unit":"chars","desc":"Min password length",       "note":"862989"},
            "login/password_expiration_time"   : {"value":"90", "unit":"days", "desc":"Password expiry days",      "note":"862989"},
            "login/fails_to_user_lock"         : {"value":"5",  "unit":"count","desc":"Lockout threshold",         "note":"862989"},
            "auth/rfc_authority_check"         : {"value":"1",  "unit":"flag", "desc":"RFC authority check",       "note":"1408081"},
            "rsau/enable"                      : {"value":"1",  "unit":"flag", "desc":"Security audit log",        "note":"539404"},
        },
        "network": {
            "icm/max_conn"              : {"value":"500","unit":"count","desc":"Max ICM connections",    "note":"1421005"},
            "icm/req_queue_len"         : {"value":"500","unit":"count","desc":"ICM request queue",      "note":"1421005"},
        },
    },
    "SAP HANA": {
        "memory": {
            "global_allocation_limit"              : {"value":"80%_of_RAM","unit":"%",    "desc":"HANA global memory limit",       "note":"1999997"},
            "max_gc_parallelism"                   : {"value":"4",         "unit":"count","desc":"GC parallelism",                 "note":"2000000"},
            "parallel_merge_threads"               : {"value":"4",         "unit":"count","desc":"Delta merge threads",            "note":"2084065"},
            "unload_upper_bound"                   : {"value":"90",        "unit":"%",    "desc":"Column unload memory threshold", "note":"2127458"},
        },
        "performance": {
            "optimize_compression_goal"            : {"value":"BALANCE",  "unit":"string","desc":"Compression goal",              "note":"2112604"},
            "result_cache_entry_lifetime"          : {"value":"300",      "unit":"sec",   "desc":"SQL result cache TTL",          "note":"2400005"},
            "joins/optimization_target"            : {"value":"balanced", "unit":"string","desc":"Join optimization",             "note":"2222200"},
        },
        "backup": {
            "data_backup_buffer_size"              : {"value":"134217728","unit":"bytes","desc":"Backup I/O buffer",              "note":"1975256"},
            "parallel_data_backup_backint_channels": {"value":"4",        "unit":"count","desc":"Parallel backup channels",      "note":"1976128"},
        },
    },
    "SAP BTP": {
        "cloud_foundry": {
            "MEMORY"                    : {"value":"1024M","unit":"MB",    "desc":"App instance memory",      "note":""},
            "INSTANCES"                 : {"value":"2",    "unit":"count", "desc":"App instance count",       "note":""},
            "DISK_QUOTA"                : {"value":"2048M","unit":"MB",    "desc":"App disk quota",            "note":""},
            "HEALTH_CHECK_TYPE"         : {"value":"http", "unit":"string","desc":"Health check method",      "note":""},
        },
    },
}

OS_PARAMETERS = {
    "Linux (RHEL/SLES)": {
        "vm.max_map_count"             : {"value":"2147483647","desc":"Virtual memory map areas",     "note":"900929"},
        "vm.swappiness"                : {"value":"10",        "desc":"Kernel swap tendency",         "note":"1980196"},
        "kernel.shmmax"                : {"value":"<total_RAM_bytes>","desc":"Max shared memory",     "note":"941735"},
        "fs.file-max"                  : {"value":"20000000",  "desc":"Open file descriptors max",   "note":"1984787"},
        "net.core.somaxconn"           : {"value":"4096",      "desc":"Socket connection backlog",   "note":"2205917"},
        "net.ipv4.tcp_max_syn_backlog" : {"value":"8192",      "desc":"SYN backlog queue",           "note":"2205917"},
        "net.ipv4.tcp_tw_reuse"        : {"value":"1",         "desc":"Reuse TIME_WAIT sockets",     "note":"2205917"},
    },
}

UPGRADE_PATHS = {
    "SAP ECC 6.0 EHP0": {
        "SAP ECC 6.0 EHP8"   : {"type":"EHP Upgrade",       "tool":"SUM",     "stops":["EHP1→EHP8 sequential or direct"],"note":"1680045"},
        "SAP S/4HANA 2020"   : {"type":"System Conversion", "tool":"SUM+DMO", "stops":["Must reach EHP7/EHP8 first"],    "note":"2399707"},
        "SAP S/4HANA 2023"   : {"type":"System Conversion", "tool":"SUM+DMO", "stops":["EHP8 SP20+ required"],           "note":"2913617"},
    },
    "SAP ECC 6.0 EHP7": {
        "SAP ECC 6.0 EHP8"   : {"type":"EHP Upgrade",       "tool":"SUM",     "stops":[],                                "note":"1680045"},
        "SAP S/4HANA 1709"   : {"type":"System Conversion", "tool":"SUM+DMO", "stops":[],                                "note":"2399707"},
        "SAP S/4HANA 2020"   : {"type":"System Conversion", "tool":"SUM+DMO", "stops":[],                                "note":"2399707"},
        "SAP S/4HANA 2023"   : {"type":"System Conversion", "tool":"SUM+DMO", "stops":["Apply min SP level"],            "note":"2913617"},
    },
    "SAP ECC 6.0 EHP8": {
        "SAP S/4HANA 1709"   : {"type":"System Conversion", "tool":"SUM+DMO", "stops":[],                                "note":"2399707"},
        "SAP S/4HANA 1809"   : {"type":"System Conversion", "tool":"SUM+DMO", "stops":[],                                "note":"2399707"},
        "SAP S/4HANA 1909"   : {"type":"System Conversion", "tool":"SUM+DMO", "stops":[],                                "note":"2399707"},
        "SAP S/4HANA 2020"   : {"type":"System Conversion", "tool":"SUM+DMO", "stops":[],                                "note":"2399707"},
        "SAP S/4HANA 2021"   : {"type":"System Conversion", "tool":"SUM+DMO", "stops":[],                                "note":"2568780"},
        "SAP S/4HANA 2022"   : {"type":"System Conversion", "tool":"SUM+DMO", "stops":[],                                "note":"2913617"},
        "SAP S/4HANA 2023"   : {"type":"System Conversion", "tool":"SUM+DMO", "stops":[],                                "note":"2913617"},
        "SAP S/4HANA 2024"   : {"type":"System Conversion", "tool":"SUM+DMO", "stops":["Apply latest SP first"],         "note":"2913617"},
    },
    "SAP S/4HANA 1909": {
        "SAP S/4HANA 2020"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
        "SAP S/4HANA 2021"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
        "SAP S/4HANA 2022"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
        "SAP S/4HANA 2023"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
        "SAP S/4HANA 2024"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
    },
    "SAP S/4HANA 2020": {
        "SAP S/4HANA 2021"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
        "SAP S/4HANA 2022"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
        "SAP S/4HANA 2023"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
        "SAP S/4HANA 2024"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
    },
    "SAP S/4HANA 2021": {
        "SAP S/4HANA 2022"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
        "SAP S/4HANA 2023"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
        "SAP S/4HANA 2024"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
    },
    "SAP S/4HANA 2022": {
        "SAP S/4HANA 2023"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
        "SAP S/4HANA 2024"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
    },
    "SAP S/4HANA 2023": {
        "SAP S/4HANA 2024"   : {"type":"Release Upgrade",   "tool":"SUM",     "stops":[],                                "note":"2568780"},
    },
    "SAP HANA 2.0 SPS04": {
        "SAP HANA 2.0 SPS05" : {"type":"Revision Upgrade",  "tool":"hdblcm",  "stops":[],                                "note":"2380493"},
        "SAP HANA 2.0 SPS06" : {"type":"Revision Upgrade",  "tool":"hdblcm",  "stops":[],                                "note":"2380493"},
        "SAP HANA 2.0 SPS07" : {"type":"Revision Upgrade",  "tool":"hdblcm",  "stops":[],                                "note":"2380493"},
    },
}

# ============================================================
# WEB HELPERS
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
    try:
        r = requests.get(
            SAP_SEARCH_API,
            params={"q": term, "area": "docs", "language": "en-US"},
            headers=HEADERS, timeout=12
        )
        if r.status_code == 200:
            for item in r.json().get("hits", [])[:8]:
                url = item.get("url", "")
                if url:
                    if not url.startswith("http"):
                        url = SAP_HELP_BASE + url
                    results.append({"title": item.get("title","No title"),
                                    "url": url,
                                    "description": item.get("description",""),
                                    "source": "SAP Help API"})
    except Exception:
        pass
    if len(results) < 3:
        results.extend(_fallback_results(term))
    seen, out = set(), []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            out.append(r)
    return out[:8]

def _fallback_results(query: str) -> list:
    q = query.lower()
    mapping = {
        ("s/4hana","s4hana","s4"):
            [("SAP S/4HANA Documentation","https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE"),
             ("S/4HANA Upgrade Guide","https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/upgrade")],
        ("ecc","erp 6"):
            [("SAP ERP Documentation","https://help.sap.com/docs/SAP_ERP"),
             ("SAP ECC Upgrade","https://help.sap.com/docs/SAP_ERP/upgrade")],
        ("btp","business technology"):
            [("SAP BTP Documentation","https://help.sap.com/docs/btp")],
        ("hana",):
            [("SAP HANA Platform","https://help.sap.com/docs/SAP_HANA_PLATFORM"),
             ("HANA Administration","https://help.sap.com/docs/SAP_HANA_PLATFORM/administration")],
        ("fiori",):
            [("SAP Fiori","https://help.sap.com/docs/SAP_FIORI")],
        ("netweaver",):
            [("SAP NetWeaver","https://help.sap.com/docs/SAP_NETWEAVER")],
        ("abap",):
            [("SAP ABAP Platform","https://help.sap.com/docs/ABAP_PLATFORM")],
    }
    out = []
    for keys, links in mapping.items():
        if any(k in q for k in keys):
            for title, url in links:
                out.append({"title":title,"url":url,
                             "description":f"Official SAP docs for {title}",
                             "source":"SAP Help Portal"})
    if not out:
        out = [
            {"title":"SAP Help Portal",           "url":"https://help.sap.com/docs",                       "description":"All SAP docs","source":"SAP"},
            {"title":"SAP S/4HANA Documentation", "url":"https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE","description":"S/4HANA docs","source":"SAP"},
            {"title":"SAP HANA Platform",          "url":"https://help.sap.com/docs/SAP_HANA_PLATFORM",    "description":"HANA docs",   "source":"SAP"},
        ]
    return out

@st.cache_data(ttl=1800, show_spinner=False)
def extract_doc_content(url: str) -> dict:
    html = fetch_url(url)
    if not html:
        return {"title":"Unavailable","content":"","sections":{},"pdf_links":[],"links":[],"url":url}
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script","style","nav","footer","header","aside"]):
        t.decompose()
    title = ""
    for sel in ["h1.title","h1","title",".page-title"]:
        t = soup.select_one(sel)
        if t:
            title = t.get_text(strip=True); break
    main = soup.select_one("main,.content,article,.topic-body,#content") or soup.body
    text = re.sub(r"\n{3,}","\n\n",main.get_text("\n",strip=True) if main else "")[:12000]
    sections = {}
    for key, pat in [
        ("prerequisites",  r"(?i)(prerequisite|requirement|before you).*?(?=\n[A-Z].{3,50}\n|\Z)"),
        ("upgrade_path",   r"(?i)(upgrade path|migration path|target release).*?(?=\n[A-Z].{3,50}\n|\Z)"),
        ("installation",   r"(?i)(install|setup|deploy).*?(?=\n[A-Z].{3,50}\n|\Z)"),
        ("parameters",     r"(?i)(parameter|profile|configuration|tuning).*?(?=\n[A-Z].{3,50}\n|\Z)"),
        ("best_practices", r"(?i)(best practice|recommendation|guideline).*?(?=\n[A-Z].{3,50}\n|\Z)"),
        ("steps",          r"(?i)(step|procedure|how to|perform).*?(?=\n[A-Z].{3,50}\n|\Z)"),
    ]:
        m = re.search(pat, text, re.DOTALL)
        if m:
            sections[key] = m.group(0)[:1800]
    pdf_links = [urljoin(url,a["href"]) for a in soup.find_all("a",href=True) if ".pdf" in a["href"].lower()]
    return {"title":title,"content":text,"sections":sections,"pdf_links":pdf_links[:8],"links":[],"url":url}

# ============================================================
# AI / RULE-BASED ANSWER
# ============================================================
def get_ai_answer(question: str, context: str, api_key: str, product: str = "") -> str:
    if api_key and GENAI_AVAILABLE:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""You are a senior SAP Technical Architect (20+ years).
Product: {product or 'General SAP'}
Use ONLY the documentation context. Format with **bold**, numbered steps,
bullet points. Add ⚠️ warnings, ✅ prerequisites, 📋 notes, SAP Note numbers.

Context:
{context[:7000]}

Question: {question}

Answer:"""
            return model.generate_content(prompt).text
        except Exception as e:
            return _rule_answer(question, context, product) + f"\n\n*(AI note: {str(e)[:80]})*"
    return _rule_answer(question, context, product)

def _rule_answer(question: str, context: str, product: str = "") -> str:
    q = question.lower()
    lines = [l.strip() for l in context.split("\n") if l.strip() and len(l.strip()) > 20]
    def rl(kws): return [l for l in lines if any(w in l.lower() for w in kws)][:10]

    if any(k in q for k in ["upgrade path","upgrade route","migration path","how to upgrade"]):
        hits = rl(["upgrade","migration","path","release","target","version"])
        a = f"## 🔄 Upgrade Path — {product}\n\n"
        if hits: a += "\n".join(f"- {l}" for l in hits) + "\n\n"
        a += """
### Supported Upgrade Scenarios
| Scenario | Tool |
|---|---|
| EHP Upgrade (ECC) | SUM |
| Release Upgrade (S/4HANA) | SUM |
| System Conversion (ECC→S/4HANA) | SUM + DMO |
| New Implementation | SWPM |

### Steps
1. Run **SAP Readiness Check** → `/SDF/RC_START_CHECK`
2. Check **PAM** for supported paths
3. Generate **Stack.xml** via Maintenance Planner
4. Execute with **SUM (Software Update Manager)**

📋 SAP Note **2913617** – Readiness Check  
📋 SAP Note **2568780** – SUM master note
"""
        return a

    if any(k in q for k in ["prerequisite","requirement","before","prepare","checklist"]):
        hits = rl(["require","prerequisite","minimum","supported","must","hardware","os","database"])
        a = f"## ✅ Prerequisites — {product}\n\n"
        if hits: a += "\n".join(f"- {l}" for l in hits) + "\n\n"
        a += """
### Hardware
- CPU: verify with SAP Quick Sizer
- RAM: minimum per product (HANA requires physical RAM ≥ active data)
- Disk: OS + DB + binaries + SUM workspace (~100 GB)

### Software
- Supported OS (RHEL 8/9 or SLES 15 for HANA; check PAM)
- Supported database version (PAM)
- Latest SAP Kernel patches
- JDK 11 or 17 (Java stack)

### SAP-Specific
- Valid S-user with download authorization
- SAP Solution Manager 7.2 (maintenance certificate)
- Minimum SP level (SAP Note 2186744)
- Unicode system (mandatory for S/4HANA)
- SAP Readiness Check completed (no open critical findings)

📋 SAP Note **2186744** – Pre-upgrade checklist  
📋 SAP Note **2399707** – S/4HANA prerequisites
"""
        return a

    if any(k in q for k in ["install","download","setup","deploy","media"]):
        a = f"## 💾 Installation & Download — {product}\n\n"
        a += """
### Download Resources
| Resource | URL |
|---|---|
| SAP Software Download Center | https://support.sap.com/swdc |
| SAP Maintenance Planner | https://support.sap.com/mp |

### Installation Sequence
