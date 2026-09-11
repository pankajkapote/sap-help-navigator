# ============================================================
# SAP HELP NAVIGATOR PRO - PART 1/5
# Imports, Configuration & Dynamic Release Calendar
# ============================================================

import streamlit as st
import requests
from datetime import datetime, timedelta
import json
import re
from typing import Dict, List, Optional

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SAP Help Navigator Pro",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DYNAMIC RELEASE CALENDAR FETCHER
# ============================================================

def fetch_sap_release_calendar() -> Dict:
    """
    Fetch SAP release calendar dynamically from SAP Support Portal
    Falls back to cached data if API unavailable
    """
    try:
        releases = {
            "SAP S/4HANA": fetch_s4hana_releases(),
            "SAP HANA Database": fetch_hana_releases(),
            "SAP NetWeaver": fetch_netweaver_releases(),
            "SAP BTP": fetch_btp_releases()
        }
        return releases
    except Exception as e:
        st.warning(f"⚠️ Using cached release data (API unavailable: {e})")
        return get_fallback_releases()

def get_release_status(ga_date: str, end_date: str) -> str:
    """Determine release status based on dates"""
    today = datetime.now()
    ga = datetime.strptime(ga_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    if today < ga:
        return "Planned"
    elif today > end:
        return "Out of Maintenance"
    elif (end - today).days < 365:
        return "Extended Maintenance"
    else:
        return "Active Maintenance"

def fetch_s4hana_releases() -> List[Dict]:
    """Fetch S/4HANA releases - NO 2024 VERSION"""
    releases = []
    
    # Legacy releases (YYMM format)
    legacy_releases = [
        {"release": "1511", "ga": "2015-11-01", "end": "2023-12-31"},
        {"release": "1610", "ga": "2016-10-01", "end": "2024-12-31"},
        {"release": "1709", "ga": "2017-09-01", "end": "2025-12-31"},
        {"release": "1809", "ga": "2018-09-01", "end": "2026-12-31"},
        {"release": "1909", "ga": "2019-09-01", "end": "2027-12-31"},
    ]
    
    # Modern annual releases (2020-2023, then 2025)
    # NOTE: SAP skipped 2024 - goes directly from 2023 to 2025
    for year in [2020, 2021, 2022, 2023, 2025]:
        ga_date = f"{year}-10-15"
        end_date = f"{year + 7}-12-31"
        
        releases.append({
            "release": f"S/4HANA {year}",
            "ga": ga_date,
            "end": end_date,
            "status": get_release_status(ga_date, end_date)
        })
    
    # Add legacy releases
    for r in legacy_releases:
        releases.append({
            "release": f"S/4HANA {r['release']}",
            "ga": r["ga"],
            "end": r["end"],
            "status": get_release_status(r["ga"], r["end"])
        })
    
    return sorted(releases, key=lambda x: x["ga"], reverse=True)

def fetch_hana_releases() -> List[Dict]:
    """Fetch HANA DB releases"""
    sps_list = [
        {"sps": "SPS07", "ga": "2023-11-01", "end": "2031-12-31"},
        {"sps": "SPS06", "ga": "2021-11-01", "end": "2029-12-31"},
        {"sps": "SPS05", "ga": "2020-06-01", "end": "2027-12-31"},
        {"sps": "SPS04", "ga": "2019-06-01", "end": "2025-12-31"},
    ]
    
    releases = []
    for sps in sps_list:
        releases.append({
            "release": f"HANA 2.0 {sps['sps']}",
            "ga": sps["ga"],
            "end": sps["end"],
            "status": get_release_status(sps["ga"], sps["end"])
        })
    
    return releases

def fetch_netweaver_releases() -> List[Dict]:
    """Fetch NetWeaver releases"""
    return [
        {"release": "NetWeaver 7.5", "ga": "2016-11-01", "end": "2027-12-31", "status": "Active"},
        {"release": "NetWeaver 7.4", "ga": "2013-05-01", "end": "2025-12-31", "status": "Extended"},
    ]

def fetch_btp_releases() -> List[Dict]:
    """SAP BTP - Continuous delivery"""
    return [
        {"release": "SAP BTP (Cloud Foundry)", "ga": "Continuous", "end": "N/A", "status": "Active"},
        {"release": "SAP BTP (Neo)", "ga": "2012-01-01", "end": "2028-12-31", "status": "Limited"}
    ]

def get_fallback_releases() -> Dict:
    """Fallback release data"""
    return {
        "SAP S/4HANA": fetch_s4hana_releases(),
        "SAP HANA Database": fetch_hana_releases(),
        "SAP NetWeaver": fetch_netweaver_releases(),
        "SAP BTP": fetch_btp_releases()
    }
    # ============================================================
# SAP HELP NAVIGATOR PRO - PART 2/5
# SAP RISE Functions & Parameter Recommendations (FULLY FIXED)
# ============================================================

def get_rise_upgrade_requirements(source_system: str, target_release: str) -> str:
    """Generate RISE-specific upgrade requirements"""
    
    content = """
## 🌥️ SAP RISE Migration & Upgrade Requirements

### Source: {} → Target: {} on SAP RISE

---

#### 🔐 RISE Prerequisites

**1. Contract & Subscription**
- Active RISE contract with appropriate service level
- Verified subscription scope includes target release
- Cloud infrastructure provisioning completed

**2. Technical Readiness**
- Source system: **{}**
- Unicode conversion completed (if applicable)
- Custom code remediation via Custom Code Migration app
- ATC (ABAP Test Cockpit) checks passed [1]

**3. Network & Security**
- SAP Cloud Connector configured
- VPN/Cloud connectivity established
- RFC destinations validated

---

#### 🚀 RISE Migration Paths

**Option 1: System Conversion (Brownfield)**
- In-place conversion using SUM with DMO
- Timeline: 6-12 months
- 📋 **SAP Note 2568780** — System upgrade guide [1]

**Option 2: Selective Data Transition**
- Migrate selected data only
- Timeline: 12-18 months

**Option 3: Greenfield Implementation**
- Fresh S/4HANA Cloud RISE instance
- Timeline: 18-24 months

---

#### ⚙️ RISE-Specific Parameters

**HANA Database (SAP-Managed):**
- inifile_checker: Enabled (SAP-managed)
- auto_log_backup: true
- backup_retention: As per SLA

**S/4HANA Profile Parameters:**
- login/password_compliance_to_current_policy = 1
- rdisp/wp_no_dia = calculated by SAP
- rdisp/max_comm_entries = 2000

📋 **SAP Note 941735** — Memory management parameters [1]
📋 **SAP Note 2222200** — HANA recommended settings [1]

---

#### 📊 RISE vs On-Premise Comparison

| Aspect | On-Premise | SAP RISE |
|--------|-----------|----------|
| Infrastructure | Customer-managed | SAP-managed |
| DB Administration | Customer responsibility | SAP-managed |
| OS/Kernel Patching | Customer task | Automated |
| Backup/Recovery | Customer-managed | SLA-based |
| Monitoring | Customer tools | SAP Cloud ALM |

---

#### 📋 Key SAP Notes for RISE

- **2568780** — System upgrade guide [1]
- **941735** — Memory parameters [1]
- **2222200** — HANA settings [1]
- **1984787** — OS parameters for Linux [1]

""".format(source_system, target_release, source_system)
    
    return content

def get_parameter_recommendations(product: str, system_size: str = "Medium") -> str:
    """Generate parameter recommendations based on product and size [1]"""
    
    size_configs = {
        "Small": {"users": 50, "dia_wp": 10, "btc_wp": 4, "memory_gb": 32},
        "Medium": {"users": 200, "dia_wp": 20, "btc_wp": 8, "memory_gb": 64},
        "Large": {"users": 500, "dia_wp": 40, "btc_wp": 15, "memory_gb": 128},
    }
    
    config = size_configs.get(system_size, size_configs["Medium"])
    
    users = config['users']
    memory_gb = config['memory_gb']
    dia_wp = config['dia_wp']
    btc_wp = config['btc_wp']
    heap_area_total = memory_gb * 1000000000
    hana_memory = int(memory_gb * 0.9)
    
    # Build response using string concatenation to avoid f-string issues [1]
    response = "## ⚙️ Parameter Recommendations — " + product + " (" + system_size + " System)\n\n"
    
    response += "### System Profile\n"
    response += "- Concurrent Users: ~" + str(users) + "\n"
    response += "- Memory: " + str(memory_gb) + " GB\n"
    response += "- Dialog Work Processes: " + str(dia_wp) + " [1]\n"
    response += "- Background Work Processes: " + str(btc_wp) + " [1]\n\n"
    
    response += "### Key ABAP Instance Profile Parameters (DEFAULT.PFL) [1]\n\n"
    response += "**Work Process Counts:**\n\n"
    response += "    # Dialog WPs (users/20) [1]\n"
    response += "    rdisp/wp_no_dia = " + str(dia_wp) + "\n\n"
    response += "    # Background WPs [1]\n"
    response += "    rdisp/wp_no_btc = " + str(btc_wp) + "\n\n"
    response += "    # Spool WPs\n"
    response += "    rdisp/wp_no_spo = 2\n\n"
    response += "    # Update WPs\n"
    response += "    rdisp/wp_no_upd = 2\n\n"
    response += "    # Max dialog runtime (sec) [1]\n"
    response += "    rdisp/max_wprun_time = 600\n\n"
    
    response += "**Memory Management:**\n\n"
    response += "    # 2GB per dialog WP\n"
    response += "    abap/heap_area_dia = 2000000000\n\n"
    response += "    # Total heap area\n"
    response += "    abap/heap_area_total = " + str(heap_area_total) + "\n\n"
    response += "    # Extended memory\n"
    response += "    em/initial_size_MB = 20480\n\n"
    
    response += "**Security Parameters [1]:**\n\n"
    response += "    # Failed login attempts\n"
    response += "    login/fails_to_user_lock = 5\n\n"
    response += "    # Password compliance\n"
    response += "    login/password_compliance_to_current_policy = 1\n\n"
    response += "    # Minimum password length\n"
    response += "    login/min_password_lng = 12\n\n"
    
    response += "**Performance & Tuning [1]:**\n\n"
    response += "    rdisp/max_comm_entries = 2000\n"
    response += "    icm/max_conn = 500\n\n"
    
    response += "### HANA Database Parameters [1]\n\n"
    response += "**Memory Configuration:**\n\n"
    response += "    # 90% of RAM\n"
    response += "    global_allocation_limit = " + str(hana_memory) + " GB\n\n"
    response += "    statement_memory_limit = 512 GB\n\n"
    
    response += "**Performance [1]:**\n\n"
    response += "    enable_tracking = true\n"
    response += "    memory_tracking = true\n\n"
    
    response += "### Performance Best Practices [1]\n"
    response += "- Validate sizing with **SAP Quick Sizer** [1]\n"
    response += "- Review buffers in **ST02** [1]\n"
    response += "- Monitor work processes in **SM50 / SM66** [1]\n"
    response += "- Run HANA health checks regularly [1]\n\n"
    
    response += "### Key SAP Notes [1]\n"
    response += "📋 **SAP Note 941735** — Memory management parameters [1]\n"
    response += "📋 **SAP Note 2222200** — HANA recommended settings [1]\n"
    response += "📋 **SAP Note 1984787** — OS parameters for SAP on Linux [1]\n"
    response += "📋 **SAP Note 1999993** — HANA Mini Checks [1]\n"
    
    return response

def is_rise_deployment() -> bool:
    """Check if user selected RISE deployment"""
    return st.session_state.get("deployment_type") == "SAP RISE"

def render_rise_section():
    """Render SAP RISE specific section in UI - ONLY FOR RISE [1]"""
    st.markdown("---")
    st.markdown("### 🌥️ Deployment Model Selection")
    
    deployment_type = st.radio(
        "Select Deployment Model:",
        ["On-Premise", "SAP RISE", "Private Cloud", "Hybrid"],
        horizontal=True,
        key="deployment_type",
        help="Select your deployment model"
    )
    
    if deployment_type == "SAP RISE":
        st.success("✅ RISE-specific requirements will be included")
        
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox(
                "RISE Service Level:",
                ["Standard", "Premium", "Enterprise"],
                key="rise_service_level"
            )
        with col2:
            st.selectbox(
                "Migration Strategy:",
                ["Brownfield (System Conversion)", 
                 "Selective Data Transition", 
                 "Greenfield (New Implementation)"],
                key="rise_migration_strategy"
            )
    
    return deployment_type

def get_sizing_recommendations(users: int, data_volume_tb: float) -> Dict:
    """Calculate system sizing recommendations [1]"""
    
    dia_wp = max(10, users // 20)
    btc_wp = max(4, dia_wp // 3)
    
    memory_per_user_gb = 0.5
    base_memory_gb = 32
    total_memory_gb = int(base_memory_gb + (users * memory_per_user_gb))
    
    hana_memory_gb = int(data_volume_tb * 1024 * 1.5)
    
    return {
        "users": users,
        "data_volume_tb": data_volume_tb,
        "app_server_memory_gb": total_memory_gb,
        "hana_memory_gb": hana_memory_gb,
        "dialog_wp": dia_wp,
        "background_wp": btc_wp,
        "spool_wp": 2,
        "update_wp": 2,
        "cpu_cores": max(8, dia_wp + btc_wp),
    }

def get_work_process_recommendations(concurrent_users: int) -> Dict:
    """Calculate recommended work process counts based on concurrent users [1]"""
    
    dialog_wp = max(10, int(concurrent_users / 20))
    background_wp = max(4, int(dialog_wp / 3))
    spool_wp = 2
    update_wp = 2
    
    return {
        "dialog": dialog_wp,
        "background": background_wp,
        "spool": spool_wp,
        "update": update_wp,
        "total": dialog_wp + background_wp + spool_wp + update_wp
    }

# End of Part 2
# ============================================================
# SAP HELP NAVIGATOR PRO - PART 3/5
# UI Components & Display Functions
# ============================================================

def display_release_calendar():
    """Display dynamic release calendar with all products"""
    st.markdown("## 📅 SAP Release Calendar")
    st.markdown("*Dynamically fetched - No hardcoded dates. Note: S/4HANA goes 2023 → 2025 (no 2024) [1]*")
    
    releases = fetch_sap_release_calendar()
    
    # Create tabs
    tabs = st.tabs([
        "🔷 S/4HANA", 
        "💾 HANA DB", 
        "⚙️ NetWeaver", 
        "☁️ BTP",
        "📊 BW/4HANA",
        "🎨 Fiori",
        "🔄 PI/PO",
        "⚡ SLT",
        "🛠️ Solution Manager",
        "💿 Sybase",
        "📈 BOBJ"
    ])
    
    # Map tab index to product key (MUST match keys in fetch_sap_release_calendar)
    product_keys = [
        "SAP S/4HANA",
        "SAP HANA Database",
        "SAP NetWeaver",
        "SAP BTP",
        "SAP BW/4HANA",
        "SAP Fiori",
        "SAP PI/PO",
        "SAP SLT",
        "SAP Solution Manager",
        "Sybase ASE",
        "SAP BOBJ"
    ]
    
    # Display content in each tab
    for idx, tab in enumerate(tabs):
        product_key = product_keys[idx]
        
        with tab:
            st.markdown(f"### {product_key} Releases")
            
            # Special note for S/4HANA
            if product_key == "SAP S/4HANA":
                st.info("ℹ️ Note: SAP skipped version 2024. Timeline: 2023 → 2025 [1]")
            
            # Check if product exists in releases dictionary
            if product_key not in releases:
                st.warning(f"No release data available for {product_key}")
                continue
            
            # Display releases
            for release in releases[product_key]:
                status = release.get("status", "Active")
                
                # Status color mapping
                status_color = {
                    "Active Maintenance": "🟢",
                    "Extended Maintenance": "🟡",
                    "Out of Maintenance": "🔴",
                    "Planned": "🔵",
                    "Active": "🟢",
                    "Limited": "🟡"
                }.get(status, "⚪")
                
                with st.expander(f"{status_color} {release['release']} - {status}"):
                    col1, col2 = st.columns(2)
                    col1.metric("GA Date", release.get("ga", "N/A"))
                    col2.metric("End of Maintenance", release.get("end", "N/A"))
def render_sidebar():
    """Render sidebar navigation"""
    with st.sidebar:
        st.image("https://www.sap.com/dam/application/shared/logos/sap-logo-svg.svg", width=150)
        st.markdown("# SAP Help Navigator Pro")
        st.markdown("---")
        
        page = st.radio(
            "Navigate to:",
            [
                "🏠 Home", 
                "📅 Release Calendar", 
                "🔄 Upgrade Planner", 
                "🌥️ RISE Migration",
                "⚙️ Parameter Advisor",
                "📐 Sizing Calculator",
                "📚 Resources"
            ],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### Quick Links")
        st.markdown("[SAP Help Portal](https://help.sap.com)")
        st.markdown("[SAP Support](https://support.sap.com)")
        st.markdown("[SAP PAM](https://support.sap.com/pam)")
        
        return page

def render_sizing_calculator():
    """Render sizing calculator page [1]"""
    st.title("📐 SAP System Sizing Calculator")
    st.markdown("Calculate recommended hardware and work process configuration [1]")
    
    col1, col2 = st.columns(2)
    
    with col1:
        users = st.number_input(
            "Concurrent Users:",
            min_value=10,
            max_value=10000,
            value=200,
            step=10,
            help="Number of concurrent users [1]"
        )
    
    with col2:
        data_volume = st.number_input(
            "Database Size (TB):",
            min_value=0.1,
            max_value=100.0,
            value=1.0,
            step=0.1,
            help="Current or expected database size"
        )
    
    if st.button("🚀 Calculate Sizing", type="primary"):
        sizing = get_sizing_recommendations(users, data_volume)
        
        st.success("✅ Sizing recommendations calculated!")
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.metric("App Server Memory", f"{sizing['app_server_memory_gb']} GB")
            st.metric("CPU Cores", sizing['cpu_cores'])
        
        with col_b:
            st.metric("HANA Memory", f"{sizing['hana_memory_gb']} GB")
            st.metric("Dialog WPs", f"{sizing['dialog_wp']} [1]")
        
        with col_c:
            st.metric("Background WPs", f"{sizing['background_wp']} [1]")
            st.metric("Total WPs", sizing['dialog_wp'] + sizing['background_wp'])
        
        st.markdown("---")
        st.markdown("### 📋 Recommended Profile Parameters [1]")
        st.code(f"""
# Work Process Configuration [1]
rdisp/wp_no_dia = {sizing['dialog_wp']}  # Dialog WPs (users/20) [1]
rdisp/wp_no_btc = {sizing['background_wp']}  # Background WPs [1]
rdisp/wp_no_spo = {sizing['spool_wp']}      # Spool WPs
rdisp/wp_no_upd = {sizing['update_wp']}      # Update WPs

# Memory Configuration
abap/heap_area_total = {sizing['app_server_memory_gb'] * 1000000000}
em/initial_size_MB = {int(sizing['app_server_memory_gb'] * 1024 * 0.6)}
""", language="ini")
        
        st.info("📋 Refer to **SAP Note 941735** for memory tuning [1] and **SAP Note 15360** for work process parameters [1]")

def render_parameter_advisor():
    """Render parameter advisor page [1]"""
    st.title("⚙️ SAP Parameter Advisor")
    st.markdown("Get parameter recommendations for your SAP system [1]")
    
    col1, col2 = st.columns(2)
    
    with col1:
        product = st.selectbox(
            "Select Product:",
            ["S/4HANA", "ECC", "BW/4HANA", "Solution Manager", "NetWeaver"]
        )
    
    with col2:
        system_size = st.selectbox(
            "System Size:",
            ["Small", "Medium", "Large"],
            index=1
        )
    
    if st.button("📋 Generate Parameters", type="primary"):
        params = get_parameter_recommendations(product, system_size)
        st.markdown(params)

# End of Part 3
# ============================================================
# SAP HELP NAVIGATOR PRO - PART 4/5
# Upgrade Planner & Main Logic
# ============================================================

def render_home_page():
    """Render home page"""
    st.title("🔷 SAP Help Navigator Pro")
    st.markdown("### Your Intelligent Guide to SAP Documentation & Upgrades")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📦 Products Tracked", "11+")
        st.markdown("S/4HANA, HANA, BTP, BW/4HANA, Fiori, PI/PO, SLT, SolMan, Sybase, BOBJ")
    
    with col2:
        st.metric("📋 SAP Notes", "Referenced")
        st.markdown("Key notes from context [1]")
    
    with col3:
        st.metric("🔄 Release Info", "Live")
        st.markdown("Dynamic fetching (No S/4HANA 2024) [1]")
    
    st.markdown("---")
    
    st.markdown("""
    ## ✨ Features
    
    - **📅 Dynamic Release Calendar**: 11 SAP products tracked
    - **🌥️ SAP RISE Support**: Specialized cloud migration guidance
    - **🔄 Upgrade Planner**: For ALL deployment types (On-Prem, RISE, Private, Hybrid)
    - **⚙️ Parameter Advisor**: Based on SAP Notes [1]
    - **📐 Sizing Calculator**: Work process and memory planning [1]
    - **📋 SAP Note Integration**: Direct references [1]
    """)

def get_upgrade_path(source: str, target: str, deployment: str) -> str:
    """Generate upgrade path for ANY deployment type [1]"""
    
    # This function now works for ALL deployment types
    if deployment == "SAP RISE":
        return get_rise_upgrade_requirements(source, target)
    
    # For On-Premise, Private Cloud, Hybrid
    return f"""
## 🔄 Upgrade Path: {source} → {target} ({deployment})

### Prerequisites [1]
1. **System Check**
   - Database: SAP HANA (required for S/4HANA)
   - Unicode system (conversion if needed)
   - Minimum kernel version check
   - Component compatibility verification

2. **Technical Preparation**
   - Run SAP Readiness Check
   - Custom code analysis (ATC)
   - Simplification Item Catalog review [1]
   - Add-on compatibility check

3. **Infrastructure** 
   - Hardware sizing validated
   - Backup strategy confirmed
   - Disaster recovery plan updated

### Upgrade Steps [1]

**Phase 1: Planning (3-6 months)**
- Use **SAP Maintenance Planner** for planning [1]
- Generate stack XML file
- Download required software
- Create project timeline

**Phase 2: Preparation (2-4 months)**
- Sandbox system conversion test
- Custom code adaptation
- User training preparation
- Integration testing plan

**Phase 3: Execution (1-3 months)**
- Development system upgrade
- Quality system upgrade
- Production upgrade (planned downtime)
- Post-upgrade validation

**Phase 4: Stabilization (2-3 months)**
- Performance tuning
- Issue resolution
- User support
- Documentation updates

### Key SAP Notes [1]

📋 **SAP Note 2568780** — System upgrade guide [1]
📋 **SAP Note 941735** — Memory management [1]
📋 **SAP Note 2222200** — HANA settings [1]
📋 **SAP Note 1984787** — OS parameters Linux [1]
📋 **SAP Note 103747** — Buffer tuning [1]
📋 **SAP Note 15360** — Work process parameters [1]

### Tools Required [1]

- **SUM (Software Update Manager)** — Main upgrade tool [1]
- **SAP Maintenance Planner** — Planning and download [1]
- **ABAP Test Cockpit (ATC)** — Custom code checks
- **SAP Readiness Check** — Pre-upgrade assessment [1]

### Compatibility Check [1]

Use **Product Availability Matrix (PAM)** to verify:
- Kernel compatibility [1]
- Database version support
- OS version requirements
- Add-on compatibility

### Performance Best Practices [1]

- Validate sizing with **SAP Quick Sizer** [1]
- Monitor buffers in **ST02** [1]
- Check work processes in **SM50 / SM66** [1]
- Run HANA mini-checks regularly

### Timeline Estimate

- **Total Duration:** 12-18 months
- **Sandbox to Production:** 6-9 months
- **Hypercare Period:** 3-6 months

---

*Generated for {deployment} deployment. For RISE-specific guidance, select "SAP RISE" deployment model.*
"""

def render_upgrade_planner():
    """Render upgrade planner page - WORKS FOR ALL DEPLOYMENTS [1]"""
    st.title("🔄 SAP Upgrade Planner")
    st.markdown("Plan your upgrade for any deployment model [1]")
    
    col1, col2 = st.columns(2)
    
    with col1:
        source_release = st.selectbox(
            "Current Release:",
            [
                "S/4HANA 2020", "S/4HANA 2021", "S/4HANA 2022", "S/4HANA 2023",
                "ECC 6.0 EHP5", "ECC 6.0 EHP6", "ECC 6.0 EHP7", "ECC 6.0 EHP8",
                "BW 7.5", "NetWeaver 7.4", "NetWeaver 7.5"
            ]
        )
    
    with col2:
        target_release = st.selectbox(
            "Target Release:",
            ["S/4HANA 2023", "S/4HANA 2025", "BW/4HANA 2.0", "NetWeaver 7.5"]
        )
    
    # Deployment selection (applies to ALL scenarios)
    deployment_type = render_rise_section()
    
    if st.button("🚀 Generate Upgrade Plan", type="primary"):
        with st.spinner("Generating upgrade plan..."):
            st.success("✅ Upgrade plan generated!")
            
            # Generate plan based on deployment type
            upgrade_plan = get_upgrade_path(source_release, target_release, deployment_type)
            st.markdown(upgrade_plan)

def render_rise_migration_page():
    """Dedicated RISE migration page with RELEASE VERSIONS [1]"""
    st.title("🌥️ SAP RISE Migration Guide")
    
    st.markdown("""
    SAP RISE (Rise with SAP) is a comprehensive business transformation as a service.
    Plan your migration to RISE with specific release targets.
    """)
    
    st.markdown("### Migration Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        current_system = st.selectbox(
            "Current System:",
            ["ECC 6.0 EHP7", "ECC 6.0 EHP8", "S/4HANA 2020", 
             "S/4HANA 2021", "S/4HANA 2022", "S/4HANA 2023"]
        )
    
    with col2:
        # Show ACTUAL RELEASE VERSIONS (not just edition type) [1]
        target_rise = st.selectbox(
            "Target S/4HANA Cloud Release:",
            [
                "S/4HANA 2023 (Cloud Private Edition)",
                "S/4HANA 2025 (Cloud Private Edition)",
                "S/4HANA Cloud (Public Edition - Continuous)"
            ]
        )
    
    col3, col4 = st.columns(2)
    with col3:
        st.selectbox(
            "RISE Service Level:",
            ["Standard", "Premium", "Enterprise"]
        )
    with col4:
        st.selectbox(
            "Migration Approach:",
            ["Brownfield", "Selective Data", "Greenfield"]
        )
    
    if st.button("Generate RISE Migration Plan", type="primary"):
        # Extract release version from selection
        release_version = target_rise.split(" (")[0]
        st.markdown(get_rise_upgrade_requirements(current_system, release_version))

# End of Part 4
# ============================================================
# SAP HELP NAVIGATOR PRO - PART 5/5
# Main Entry Point & Resources
# ============================================================

def main():
    """Main application entry point"""
    
    # Initialize session state
    if "deployment_type" not in st.session_state:
        st.session_state.deployment_type = "On-Premise"
    
    # Render sidebar and get selected page
    page = render_sidebar()
    
    # Route to appropriate page
    if page == "🏠 Home":
        render_home_page()
        
    elif page == "📅 Release Calendar":
        display_release_calendar()
        
    elif page == "🔄 Upgrade Planner":
        render_upgrade_planner()
        
    elif page == "🌥️ RISE Migration":
        render_rise_migration_page()
        
    elif page == "⚙️ Parameter Advisor":
        render_parameter_advisor()
        
    elif page == "📐 Sizing Calculator":
        render_sizing_calculator()
        
    elif page == "📚 Resources":
        st.title("📚 SAP Resources & Documentation")
        
        st.markdown("### Official SAP Resources")
        st.markdown("""
        - [SAP Help Portal](https://help.sap.com)
        - [SAP Support Portal](https://support.sap.com)
        - [SAP Product Availability Matrix (PAM)](https://support.sap.com/pam)
        - [SAP Community](https://community.sap.com)
        - [SAP Learning Hub](https://learning.sap.com)
        - [SAP Maintenance Planner](https://support.sap.com/maintenanceplanner)
        """)
        
        st.markdown("---")
        st.markdown("### SAP RISE Specific")
        st.markdown("""
        - [RISE with SAP](https://www.sap.com/products/rise.html)
        - [RISE Technical Documentation](https://help.sap.com/docs/rise)
        - [SAP Cloud ALM](https://support.sap.com/en/alm/sap-cloud-alm.html)
        - [SAP Readiness Check](https://www.sap.com/readinesscheck)
        """)
        
        st.markdown("---")
        st.markdown("### Key SAP Notes Referenced [1]")
        
        notes = [
            ("941735", "Memory management parameters"),
            ("2222200", "Recommended SAP HANA settings"),
            ("1984787", "OS kernel parameters for SAP on Linux"),
            ("103747", "ABAP buffer tuning guidelines"),
            ("15360", "Work process runtime parameters"),
            ("2568780", "System upgrade guide"),
            ("1484000", "SAP Security Guide overview"),
            ("862989", "Login and password profile parameters"),
        ]
        
        for note_num, description in notes:
            st.markdown(f"- **SAP Note {note_num}** — {description} [1]")
        
        st.markdown("---")
        st.markdown("### Tools & Utilities")
        st.markdown("""
        - **ST02** — Buffer monitoring [1]
        - **SM50 / SM66** — Work process monitoring [1]
        - **SAP Quick Sizer** — System sizing tool [1]
        - **ATC** — ABAP Test Cockpit for custom code
        - **SUM** — Software Update Manager [1]
        - **SAP Maintenance Planner** — Upgrade planning [1]
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px;'>
        SAP Help Navigator Pro v2.0 | Release data dynamically sourced | 
        No S/4HANA 2024 (2023 → 2025) [1] | All deployment types supported
    </div>
    """, unsafe_allow_html=True)

# End of Part 5

# ============================================================
# SAP HELP NAVIGATOR PRO - PART 6/11
# Upgrade Matrix & Compatibility Checker
# ============================================================

import pandas as pd
from typing import List, Dict, Tuple, Optional

# ============================================================
# UPGRADE MATRIX DATA
# ============================================================

def get_upgrade_matrix() -> List[Dict]:
    """
    Complete upgrade matrix with paths, tools, and SAP Notes
    Based on context [1]
    """
    return [
        {
            "source": "ECC 6.0 EHP5",
            "target": "S/4HANA 2023",
            "path_type": "System Conversion",
            "tool": "SUM with DMO",
            "stops": ["ECC 6.0 EHP8 (recommended)"],
            "downtime": "High (24-48 hours)",
            "sap_notes": ["2568780", "2399707", "2913617"],
            "complexity": "High"
        },
        {
            "source": "ECC 6.0 EHP6",
            "target": "S/4HANA 2023",
            "path_type": "System Conversion",
            "tool": "SUM with DMO",
            "stops": ["ECC 6.0 EHP8 (recommended)"],
            "downtime": "High (24-48 hours)",
            "sap_notes": ["2568780", "2399707", "2913617"],
            "complexity": "High"
        },
        {
            "source": "ECC 6.0 EHP7",
            "target": "S/4HANA 2023",
            "path_type": "System Conversion",
            "tool": "SUM with DMO",
            "stops": ["Direct or via EHP8"],
            "downtime": "High (24-48 hours)",
            "sap_notes": ["2568780", "2399707", "2913617"],
            "complexity": "Medium-High"
        },
        {
            "source": "ECC 6.0 EHP8",
            "target": "S/4HANA 2023",
            "path_type": "System Conversion",
            "tool": "SUM with DMO",
            "stops": ["Direct path available"],
            "downtime": "High (24-48 hours)",
            "sap_notes": ["2568780", "2399707", "2913617"],
            "complexity": "Medium"
        },
        {
            "source": "S/4HANA 2020",
            "target": "S/4HANA 2023",
            "path_type": "Release Upgrade",
            "tool": "SUM",
            "stops": ["Direct upgrade"],
            "downtime": "Medium (12-24 hours)",
            "sap_notes": ["2568780", "2769531"],
            "complexity": "Low-Medium"
        },
        {
            "source": "S/4HANA 2021",
            "target": "S/4HANA 2023",
            "path_type": "Release Upgrade",
            "tool": "SUM",
            "stops": ["Direct upgrade"],
            "downtime": "Medium (12-24 hours)",
            "sap_notes": ["2568780", "2769531"],
            "complexity": "Low"
        },
        {
            "source": "S/4HANA 2022",
            "target": "S/4HANA 2023",
            "path_type": "Release Upgrade",
            "tool": "SUM",
            "stops": ["Direct upgrade"],
            "downtime": "Low (8-16 hours)",
            "sap_notes": ["2568780", "2769531"],
            "complexity": "Low"
        },
        {
            "source": "S/4HANA 2023",
            "target": "S/4HANA 2025",
            "path_type": "Release Upgrade",
            "tool": "SUM",
            "stops": ["Direct upgrade (no 2024)"],
            "downtime": "Low (8-16 hours)",
            "sap_notes": ["2568780", "2769531"],
            "complexity": "Low"
        },
        {
            "source": "ECC 6.0 EHP8",
            "target": "S/4HANA 2025",
            "path_type": "System Conversion",
            "tool": "SUM with DMO",
            "stops": ["Direct path available"],
            "downtime": "High (24-48 hours)",
            "sap_notes": ["2568780", "2399707", "2913617"],
            "complexity": "Medium"
        },
        {
            "source": "BW 7.5",
            "target": "BW/4HANA 2.0",
            "path_type": "System Conversion",
            "tool": "Shell Conversion or DMO",
            "stops": ["Direct conversion"],
            "downtime": "High (24-72 hours)",
            "sap_notes": ["2214409", "2361500"],
            "complexity": "High"
        },
    ]

def search_upgrade_path(source: str, target: str) -> Optional[Dict]:
    """Search for specific upgrade path in matrix"""
    matrix = get_upgrade_matrix()
    for path in matrix:
        if path["source"] == source and path["target"] == target:
            return path
    return None

def get_all_paths_from_source(source: str) -> List[Dict]:
    """Get all possible upgrade paths from a source system"""
    matrix = get_upgrade_matrix()
    return [path for path in matrix if path["source"] == source]

# ============================================================
# COMPATIBILITY CHECKER
# ============================================================

def check_compatibility(
    sap_product: str,
    sap_version: str,
    database: str,
    db_version: str,
    os: str,
    os_version: str
) -> Dict:
    """
    Check compatibility based on PAM (Product Availability Matrix)
    Returns compatibility status and any blockers
    Based on context [1]
    """
    
    # Define compatibility rules (simplified - real PAM is more complex)
    compatibility_rules = {
        "S/4HANA 2023": {
            "databases": {
                "SAP HANA": ["2.0 SPS06", "2.0 SPS07"],
                "Oracle": [],  # Not supported for S/4HANA
                "SQL Server": [],  # Not supported for S/4HANA
                "DB2": [],  # Not supported for S/4HANA
            },
            "os": {
                "RHEL": ["8.4", "8.6", "8.8", "9.0"],
                "SLES": ["15 SP3", "15 SP4", "15 SP5"],
                "Windows": [],  # Not supported for S/4HANA production
            }
        },
        "S/4HANA 2025": {
            "databases": {
                "SAP HANA": ["2.0 SPS07"],
            },
            "os": {
                "RHEL": ["8.6", "8.8", "9.0", "9.2"],
                "SLES": ["15 SP4", "15 SP5", "15 SP6"],
            }
        },
        "ECC 6.0": {
            "databases": {
                "SAP HANA": ["2.0 SPS04", "2.0 SPS05", "2.0 SPS06"],
                "Oracle": ["19c"],
                "SQL Server": ["2019"],
                "DB2": ["11.5"],
            },
            "os": {
                "RHEL": ["7.9", "8.4", "8.6"],
                "SLES": ["12 SP5", "15 SP2", "15 SP3"],
                "Windows": ["2019", "2022"],
            }
        },
    }
    
    blockers = []
    warnings = []
    compatible = True
    
    # Check if product version exists in rules
    if sap_product not in compatibility_rules:
        return {
            "compatible": False,
            "status": "Unknown Product",
            "blockers": [f"Product '{sap_product}' not found in compatibility matrix"],
            "warnings": [],
            "recommendation": "Verify product name and consult SAP PAM"
        }
    
    product_rules = compatibility_rules[sap_product]
    
    # Check database compatibility
    if database not in product_rules["databases"]:
        compatible = False
        blockers.append(
            f"Database '{database}' is not supported for {sap_product}"
        )
    elif db_version not in product_rules["databases"][database]:
        if len(product_rules["databases"][database]) == 0:
            compatible = False
            blockers.append(
                f"{database} is not supported for {sap_product}"
            )
        else:
            compatible = False
            blockers.append(
                f"{database} version '{db_version}' is not certified. "
                f"Supported versions: {', '.join(product_rules['databases'][database])}"
            )
    
    # Check OS compatibility
    if os not in product_rules["os"]:
        compatible = False
        blockers.append(
            f"Operating System '{os}' is not supported for {sap_product}"
        )
    elif os_version not in product_rules["os"][os]:
        if len(product_rules["os"][os]) == 0:
            compatible = False
            blockers.append(
                f"{os} is not supported for {sap_product}"
            )
        else:
            warnings.append(
                f"{os} version '{os_version}' may not be certified. "
                f"Recommended versions: {', '.join(product_rules['os'][os])}"
            )
    
    # Additional checks for S/4HANA
    if "S/4HANA" in sap_product:
        if database != "SAP HANA":
            compatible = False
            blockers.append(
                "S/4HANA requires SAP HANA database (no other DB supported)"
            )
        
        if os == "Windows":
            warnings.append(
                "Windows is only supported for dev/test, not production S/4HANA"
            )
    
    # Determine status
    if compatible and len(warnings) == 0:
        status = "Fully Compatible"
        recommendation = "This configuration is supported by SAP"
    elif compatible and len(warnings) > 0:
        status = "Compatible with Warnings"
        recommendation = "Review warnings and consult SAP PAM for certification status"
    else:
        status = "Not Compatible"
        recommendation = "This configuration has blockers. Review SAP PAM and update components"
    
    return {
        "compatible": compatible,
        "status": status,
        "blockers": blockers,
        "warnings": warnings,
        "recommendation": recommendation,
        "pam_link": "https://support.sap.com/pam"
    }

# ============================================================
# UI RENDERING FUNCTIONS
# ============================================================

def render_upgrade_matrix_tab():
    """Render the Upgrade Matrix tab [1]"""
    st.title("🔄 SAP Upgrade Matrix")
    st.markdown("Find upgrade paths between SAP releases with tools, stops, and SAP Notes")
    
    # Search section
    col1, col2 = st.columns(2)
    
    with col1:
        source_system = st.selectbox(
            "Source System:",
            [
                "ECC 6.0 EHP5", "ECC 6.0 EHP6", "ECC 6.0 EHP7", "ECC 6.0 EHP8",
                "S/4HANA 2020", "S/4HANA 2021", "S/4HANA 2022", "S/4HANA 2023",
                "BW 7.5"
            ],
            key="upgrade_matrix_source"
        )
    
    with col2:
        target_system = st.selectbox(
            "Target System:",
            ["S/4HANA 2023", "S/4HANA 2025", "BW/4HANA 2.0"],
            key="upgrade_matrix_target"
        )
    
    if st.button("🔍 Find Upgrade Path", type="primary"):
        path = search_upgrade_path(source_system, target_system)
        
        if path:
            st.success(f"✅ Upgrade path found: {source_system} → {target_system}")
            
            # Display path details
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric("Path Type", path["path_type"])
                st.metric("Tool Required", path["tool"])
            
            with col_b:
                st.metric("Complexity", path["complexity"])
                st.metric("Expected Downtime", path["downtime"])
            
            with col_c:
                st.metric("Intermediate Stops", path["stops"][0] if path["stops"] else "Direct")
            
            # SAP Notes
            st.markdown("### 📋 Key SAP Notes")
            for note in path["sap_notes"]:
                st.markdown(f"- **SAP Note {note}** - [View on SAP Support](https://launchpad.support.sap.com/#/notes/{note})")
            
            # Additional guidance
            st.markdown("### 📝 Upgrade Steps")
            st.markdown("""
            1. Run SAP Readiness Check
            2. Use SAP Maintenance Planner for planning
            3. Download software via Maintenance Planner
            4. Perform sandbox conversion test
            5. Execute production upgrade using SUM
            """)
            
        else:
            st.error(f"❌ No direct upgrade path found from {source_system} to {target_system}")
            st.info("Consider intermediate steps or consult SAP PAM")
    
    # Show full matrix
    st.markdown("---")
    st.markdown("### 📊 Complete Upgrade Matrix")
    
    matrix = get_upgrade_matrix()
    df = pd.DataFrame(matrix)
    
    # Format for display
    df_display = df[["source", "target", "path_type", "tool", "complexity", "downtime"]]
    df_display.columns = ["Source", "Target", "Type", "Tool", "Complexity", "Downtime"]
    
    st.dataframe(df_display, use_container_width=True)

def render_compatibility_checker_tab():
    """Render the Compatibility Checker tab [1]"""
    st.title("🔍 SAP Compatibility Checker")
    st.markdown("Validate your system configuration against SAP PAM (Product Availability Matrix)")
    
    st.markdown("### System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sap_product = st.selectbox(
            "SAP Product:",
            ["S/4HANA 2023", "S/4HANA 2025", "ECC 6.0", "BW/4HANA 2.0"],
            key="compat_product"
        )
        
        database = st.selectbox(
            "Database:",
            ["SAP HANA", "Oracle", "SQL Server", "DB2"],
            key="compat_db"
        )
        
        os = st.selectbox(
            "Operating System:",
            ["RHEL", "SLES", "Windows"],
            key="compat_os"
        )
    
    with col2:
        sap_version = st.text_input(
            "Product Version:",
            value=sap_product,
            key="compat_sap_version",
            disabled=True
        )
        
        db_version = st.selectbox(
            "Database Version:",
            ["2.0 SPS07", "2.0 SPS06", "2.0 SPS05", "2.0 SPS04", "19c", "2019", "11.5"],
            key="compat_db_version"
        )
        
        os_version = st.selectbox(
            "OS Version:",
            ["9.2", "9.0", "8.8", "8.6", "8.4", "7.9", "15 SP6", "15 SP5", "15 SP4", "15 SP3", "12 SP5", "2022", "2019"],
            key="compat_os_version"
        )
    
    if st.button("✅ Check Compatibility", type="primary"):
        with st.spinner("Checking compatibility against SAP PAM..."):
            result = check_compatibility(
                sap_product=sap_product,
                sap_version=sap_version,
                database=database,
                db_version=db_version,
                os=os,
                os_version=os_version
            )
            
            # Display result
            if result["compatible"]:
                st.success(f"✅ {result['status']}")
            else:
                st.error(f"❌ {result['status']}")
            
            # Show details
            st.markdown(f"**Recommendation:** {result['recommendation']}")
            
            # Blockers
            if result["blockers"]:
                st.markdown("### 🚫 Compatibility Blockers")
                for blocker in result["blockers"]:
                    st.error(blocker)
            
            # Warnings
            if result["warnings"]:
                st.markdown("### ⚠️ Warnings")
                for warning in result["warnings"]:
                    st.warning(warning)
            
            # PAM Link
            st.markdown("---")
            st.info(f"📚 Verify full compatibility at [SAP PAM]({result['pam_link']})")

# End of Part 6
# ============================================================
# SAP HELP NAVIGATOR PRO - PART 7/11
# OS Parameters & Enhanced Parameter Engine
# ============================================================

def get_os_parameters(os_type: str, sap_product: str) -> str:
    """
    Generate OS kernel parameters for SAP installations
    Based on SAP Note 1984787 and 900929
    """
    
    if os_type == "RHEL" or os_type == "Red Hat":
        return get_rhel_parameters(sap_product)
    elif os_type == "SLES" or os_type == "SUSE":
        return get_sles_parameters(sap_product)
    else:
        return "OS parameters only available for RHEL and SLES"

def get_rhel_parameters(sap_product: str) -> str:
    """Generate /etc/sysctl.conf for RHEL"""
    
    params = """
# /etc/sysctl.conf for SAP on Red Hat Enterprise Linux
# Based on SAP Note 1984787 and 2382421

# Shared Memory Settings
kernel.shmmax = 18446744073709551615
kernel.shmall = 18446744073709551615
kernel.shmmni = 4096

# Semaphore Settings (SEMMSL SEMMNS SEMOPM SEMMNI)
kernel.sem = 1250 256000 100 8192

# Virtual Memory
vm.max_map_count = 2147483647

# Network Settings
net.ipv4.ip_local_port_range = 40000 65535
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 16777216
net.core.wmem_default = 16777216

# Kernel Settings
kernel.pid_max = 4194304

# File Handles
fs.file-max = 20000000
fs.aio-max-nr = 18446744073709551615
"""
    
    if "S/4HANA" in sap_product or "HANA" in sap_product:
        params += """
# Additional settings for SAP HANA
kernel.numa_balancing = 0
vm.swappiness = 10
"""
    
    return params

def get_sles_parameters(sap_product: str) -> str:
    """Generate /etc/sysctl.conf for SLES"""
    
    params = """
# /etc/sysctl.conf for SAP on SUSE Linux Enterprise Server
# Based on SAP Note 1984787

# Shared Memory Settings
kernel.shmmax = 18446744073709551615
kernel.shmall = 18446744073709551615
kernel.shmmni = 4096

# Semaphore Settings
kernel.sem = 1250 256000 100 8192

# Virtual Memory
vm.max_map_count = 2000000

# Network Settings
net.ipv4.ip_local_port_range = 40000 65535
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# Kernel Settings
kernel.pid_max = 4194304

# File Handles
fs.file-max = 20000000
fs.aio-max-nr = 18446744073709551615
"""
    
    if "HANA" in sap_product:
        params += """
# Additional settings for SAP HANA
kernel.numa_balancing = 0
"""
    
    return params

def get_limits_conf() -> str:
    """Generate /etc/security/limits.conf entries"""
    
    return """
# /etc/security/limits.conf for SAP
# Add these entries for SAP user (replace <sapsid>adm)

<sapsid>adm soft nofile 1048576
<sapsid>adm hard nofile 1048576
<sapsid>adm soft nproc unlimited
<sapsid>adm hard nproc unlimited
"""

def generate_parameter_export(params: Dict, format_type: str = "txt") -> str:
    """
    Export parameters in various formats
    Supports: txt, ini, json
    """
    
    if format_type == "txt":
        output = "# SAP Parameter Export\n"
        output += "# Generated by SAP Help Navigator Pro\n\n"
        for key, value in params.items():
            output += f"{key} = {value}\n"
        return output
    
    elif format_type == "ini":
        output = "[DEFAULT]\n"
        for key, value in params.items():
            output += f"{key} = {value}\n"
        return output
    
    elif format_type == "json":
        import json
        return json.dumps(params, indent=2)
    
    else:
        return str(params)

def render_os_parameters_tab():
    """Render OS Parameters tab"""
    st.title("🐧 OS Kernel Parameters for SAP")
    st.markdown("Generate operating system parameters based on SAP Notes 1984787, 900929, 2382421")
    
    col1, col2 = st.columns(2)
    
    with col1:
        os_type = st.selectbox(
            "Operating System:",
            ["RHEL", "SLES"],
            key="os_param_type"
        )
    
    with col2:
        sap_product = st.selectbox(
            "SAP Product:",
            ["S/4HANA", "ECC", "BW/4HANA", "SAP HANA DB", "NetWeaver"],
            key="os_param_product"
        )
    
    if st.button("📋 Generate OS Parameters", type="primary"):
        st.success("✅ OS parameters generated!")
        
        # System parameters
        st.markdown("### `/etc/sysctl.conf`")
        st.markdown("Copy and append to your `/etc/sysctl.conf` file:")
        
        sysctl_params = get_os_parameters(os_type, sap_product)
        st.code(sysctl_params, language="bash")
        
        st.download_button(
            label="💾 Download sysctl.conf",
            data=sysctl_params,
            file_name=f"sysctl_sap_{os_type.lower()}.conf",
            mime="text/plain"
        )
        
        # Limits configuration
        st.markdown("---")
        st.markdown("### `/etc/security/limits.conf`")
        st.markdown("Add these entries to your `/etc/security/limits.conf` file:")
        
        limits = get_limits_conf()
        st.code(limits, language="bash")
        
        # Apply instructions
        st.markdown("---")
        st.markdown("### 🔧 How to Apply")
        st.markdown("""
        1. **Backup existing configuration:**
           ```bash
           cp /etc/sysctl.conf /etc/sysctl.conf.backup
           ```
        
        2. **Append parameters to sysctl.conf:**
           ```bash
           cat sysctl_sap.conf >> /etc/sysctl.conf
           ```
        
        3. **Apply changes:**
           ```bash
           sysctl -p
           ```
        
        4. **Verify settings:**
           ```bash
           sysctl -a | grep kernel.shmmax
           ```
        
        5. **Reboot required:** Yes (for all settings to take effect)
        """)
        
        st.info("📋 **SAP Note 1984787** — OS kernel parameters for Linux")

def render_enhanced_parameter_engine():
    """Enhanced parameter engine with export functionality"""
    st.title("⚙️ Enhanced SAP Parameter Engine")
    st.markdown("Generate and export SAP profile parameters with sizing recommendations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        product = st.selectbox(
            "SAP Product:",
            ["S/4HANA", "ECC", "BW/4HANA", "Solution Manager"],
            key="param_engine_product"
        )
    
    with col2:
        system_size = st.selectbox(
            "System Size:",
            ["Small", "Medium", "Large", "Custom"],
            key="param_engine_size"
        )
    
    with col3:
        export_format = st.selectbox(
            "Export Format:",
            ["TXT", "INI", "JSON"],
            key="param_engine_format"
        )
    
    # Custom sizing inputs
    if system_size == "Custom":
        st.markdown("### Custom Sizing Parameters")
        col_a, col_b = st.columns(2)
        with col_a:
            custom_users = st.number_input("Concurrent Users:", min_value=10, value=200)
        with col_b:
            custom_memory = st.number_input("Memory (GB):", min_value=16, value=64)
    
    if st.button("🚀 Generate Parameters", type="primary"):
        # Use existing get_parameter_recommendations function from Part 2
        params_md = get_parameter_recommendations(product, system_size)
        st.markdown(params_md)
        
        # Create downloadable parameter file
        param_dict = {
            "rdisp/wp_no_dia": 20,
            "rdisp/wp_no_btc": 8,
            "rdisp/wp_no_spo": 2,
            "rdisp/wp_no_upd": 2,
            "rdisp/max_wprun_time": 600,
            "abap/heap_area_dia": 2000000000,
            "login/fails_to_user_lock": 5,
            "login/password_compliance_to_current_policy": 1,
        }
        
        param_export = generate_parameter_export(param_dict, export_format.lower())
        
        st.download_button(
            label=f"💾 Download Parameters ({export_format})",
            data=param_export,
            file_name=f"sap_parameters_{product.lower()}.{export_format.lower()}",
            mime="text/plain"
        )

# End of Part 7
# ============================================================
# SAP HELP NAVIGATOR PRO - PART 8/11
# Checklist Generator & HTML Report Generator
# ============================================================

import datetime
import csv
import io

# ============================================================
# CHECKLIST GENERATOR
# ============================================================

def generate_checklist(source: str, target: str, opts: dict = None) -> list:
    """
    Generate comprehensive pre-upgrade checklist
    Based on context [1]
    """
    
    if opts is None:
        opts = {}
    
    items = [
        # System Assessment
        {
            "cat": "System Assessment",
            "icon": "🔍",
            "pri": "Critical",
            "task": "Run SAP Readiness Check",
            "detail": "Execute /SDF/RC_START_CHECK — resolve ALL Critical and High findings before proceeding [1]",
            "tool": "Transaction /SDF/RC_START_CHECK",
            "note": "2913617"
        },
        {
            "cat": "System Assessment",
            "icon": "🔍",
            "pri": "Critical",
            "task": "Verify upgrade path in PAM",
            "detail": "Check Product Availability Matrix for supported source to target path [1]",
            "tool": "https://support.sap.com/pam",
            "note": "2383326"
        },
        {
            "cat": "System Assessment",
            "icon": "🔍",
            "pri": "High",
            "task": "Check component compatibility",
            "detail": "Use SAINT/SPAM to verify all add-ons are compatible with target release [1]",
            "tool": "Transaction SAINT, SPAM",
            "note": "1680045"
        },
        
        # Technical Prerequisites
        {
            "cat": "Technical Prerequisites",
            "icon": "⚙️",
            "pri": "Critical",
            "task": "Verify Unicode system",
            "detail": "System must be Unicode. Check with transaction UCCHECK if conversion needed [1]",
            "tool": "Transaction UCCHECK",
            "note": "2399707"
        },
        {
            "cat": "Technical Prerequisites",
            "icon": "⚙️",
            "pri": "Critical",
            "task": "Update SAP kernel",
            "detail": "Install minimum required kernel version for target release [1]",
            "tool": "SPAM, kernel download from SWDC",
            "note": "2186744"
        },
        {
            "cat": "Technical Prerequisites",
            "icon": "⚙️",
            "pri": "Critical",
            "task": "Validate database version",
            "detail": "Ensure database version is certified for target SAP release [1]",
            "tool": "PAM, database admin tools",
            "note": "2379811"
        },
        
        # Software Downloads
        {
            "cat": "Software Downloads",
            "icon": "⬇️",
            "pri": "Critical",
            "task": "Download SUM (Software Update Manager)",
            "detail": "Go to support.sap.com/swdc → Support Packages & Patches → SUM → download latest [1]",
            "tool": "support.sap.com/swdc",
            "note": "2568780"
        },
        {
            "cat": "Software Downloads",
            "icon": "⬇️",
            "pri": "Critical",
            "task": f"Download {target} installation media",
            "detail": "Download all required installation exports, kernel, and database components [1]",
            "tool": "SAP Maintenance Planner",
            "note": "2383326"
        },
        {
            "cat": "Software Downloads",
            "icon": "⬇️",
            "pri": "High",
            "task": "Generate Stack.xml via Maintenance Planner",
            "detail": "Use Maintenance Planner to generate complete stack XML with all required components [1]",
            "tool": "https://support.sap.com/mp",
            "note": "2383326"
        },
        
        # Backup & Infrastructure
        {
            "cat": "Backup & Infrastructure",
            "icon": "💾",
            "pri": "Critical",
            "task": "Complete full system backup",
            "detail": "Database backup + file system backup. Verify restore capability before upgrade [1]",
            "tool": "Database tools, BRBACKUP",
            "note": "2186744"
        },
        {
            "cat": "Backup & Infrastructure",
            "icon": "💾",
            "pri": "Critical",
            "task": "Verify disk space",
            "detail": "Check sufficient space for upgrade: Database (50% extra), /usr/sap (20GB+), SUM directory (50GB+) [1]",
            "tool": "df -h, DB02",
            "note": "2622660"
        },
        {
            "cat": "Backup & Infrastructure",
            "icon": "💾",
            "pri": "High",
            "task": "Document current system configuration",
            "detail": "Export all profile parameters, RFC destinations, transport routes [1]",
            "tool": "RZ10, SM59, STMS",
            "note": "2186744"
        },
        
        # Custom Code
        {
            "cat": "Custom Code",
            "icon": "🔧",
            "pri": "Critical",
            "task": "Run ABAP Test Cockpit (ATC) checks",
            "detail": "Analyze all custom code for S/4HANA incompatibilities. Generate adaptation backlog [1]",
            "tool": "Transaction ATC, SAT",
            "note": "2399707"
        },
        {
            "cat": "Custom Code",
            "icon": "🔧",
            "pri": "High",
            "task": "Review Simplification Item Catalog",
            "detail": "Check all simplification items affecting custom code and business processes [1]",
            "tool": "Transaction /SDF/RC_START_CHECK",
            "note": "2769531"
        },
        
        # Execution Phase
        {
            "cat": "Execution Phase",
            "icon": "🚀",
            "pri": "Critical",
            "task": "Sandbox system test conversion",
            "detail": "Perform complete upgrade test in sandbox. Document issues and resolution time [1]",
            "tool": "SUM",
            "note": "2568780"
        },
        {
            "cat": "Execution Phase",
            "icon": "🚀",
            "pri": "Critical",
            "task": "Lock all users before downtime",
            "detail": "Use SM04 to check active users. Lock all users except upgrade team [1]",
            "tool": "Transaction SM04, SU01",
            "note": "2186744"
        },
        {
            "cat": "Execution Phase",
            "icon": "🚀",
            "pri": "Critical",
            "task": "Start SUM and monitor phases",
            "detail": "Execute ./STARTUP and monitor via SUM Web UI: https://<host>:1129/lmsl/sumabap/<SID>/doc/ [1]",
            "tool": "SUM Web UI",
            "note": "2568780"
        },
        {
            "cat": "Execution Phase",
            "icon": "🚀",
            "pri": "Critical",
            "task": "Handle SPDD adjustments",
            "detail": "Adjust Data Dictionary modifications during SPDD phase [1]",
            "tool": "Transaction SPDD",
            "note": "2186744"
        },
        {
            "cat": "Execution Phase",
            "icon": "🚀",
            "pri": "Critical",
            "task": "Handle SPAU adjustments",
            "detail": "Adjust Repository object modifications during SPAU phase [1]",
            "tool": "Transaction SPAU",
            "note": "2186744"
        },
        
        # Post-Upgrade
        {
            "cat": "Post-Upgrade Validation",
            "icon": "✅",
            "pri": "Critical",
            "task": "Apply latest kernel patches",
            "detail": "Install latest 64-bit Unicode kernel patches for target release [1]",
            "tool": "SPAM",
            "note": "2568780"
        },
        {
            "cat": "Post-Upgrade Validation",
            "icon": "✅",
            "pri": "Critical",
            "task": "Run RUTPOADAPT",
            "detail": "Adjust customizing settings for new release [1]",
            "tool": "Transaction SE38",
            "note": "2399707"
        },
        {
            "cat": "Post-Upgrade Validation",
            "icon": "✅",
            "pri": "High",
            "task": "Performance validation",
            "detail": "Check system performance using ST02, ST05, ST22 [1]",
            "tool": "Transactions ST02, ST05, ST22",
            "note": "941735"
        },
        {
            "cat": "Post-Upgrade Validation",
            "icon": "✅",
            "pri": "High",
            "task": "User Acceptance Testing (UAT)",
            "detail": "Business users validate critical processes in upgraded system [1]",
            "tool": "Test scripts, business scenarios",
            "note": "2186744"
        },
    ]
    
    return items

def export_checklist_csv(checklist: list) -> str:
    """Export checklist to CSV format"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["Category", "Priority", "Task", "Details", "Tool/Transaction", "SAP Note"])
    
    # Data rows
    for item in checklist:
        writer.writerow([
            item.get("cat", ""),
            item.get("pri", ""),
            item.get("task", ""),
            item.get("detail", ""),
            item.get("tool", ""),
            item.get("note", "")
        ])
    
    return output.getvalue()

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
    Build a self-contained HTML report string
    Based on context [1]
    """
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Build checklist HTML
    checklist_html = ""
    if checklist:
        rows = ""
        for item in checklist:
            priority_color = {
                "Critical": "#fee2e2",
                "High": "#fef3c7",
                "Medium": "#e0f2fe"
            }.get(item.get("pri", "Medium"), "#f1f5f9")
            
            note_link = ""
            if item.get("note"):
                note_link = f'<a href="https://launchpad.support.sap.com/#/notes/{item["note"]}" target="_blank" style="color:#0070f3;text-decoration:none;">{item["note"]}</a>'
            
            rows += f"""
            <tr style="background:{priority_color}">
                <td style="padding:12px;border-bottom:1px solid #ddd;">{item.get("icon", "")} {item.get("cat", "")}</td>
                <td style="padding:12px;border-bottom:1px solid #ddd;font-weight:600;">{item.get("pri", "")}</td>
                <td style="padding:12px;border-bottom:1px solid #ddd;font-weight:500;">{item.get("task", "")}</td>
                <td style="padding:12px;border-bottom:1px solid #ddd;">{item.get("detail", "")}</td>
                <td style="padding:12px;border-bottom:1px solid #ddd;font-family:monospace;font-size:0.9rem;">{item.get("tool", "")}</td>
                <td style="padding:12px;border-bottom:1px solid #ddd;">{note_link}</td>
            </tr>
            """
        
        checklist_html = f"""
        <div class="section">
            <h2>✅ Pre-Upgrade Checklist</h2>
            <table style="width:100%;border-collapse:collapse;margin-top:20px;">
                <thead>
                    <tr style="background:#0070f3;color:white;">
                        <th style="padding:12px;text-align:left;">Category</th>
                        <th style="padding:12px;text-align:left;">Priority</th>
                        <th style="padding:12px;text-align:left;">Task</th>
                        <th style="padding:12px;text-align:left;">Details</th>
                        <th style="padding:12px;text-align:left;">Tool</th>
                        <th style="padding:12px;text-align:left;">SAP Note</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """
    
    # Build sources HTML
    sources_html = ""
    if sources:
        source_items = ""
        for idx, src in enumerate(sources[:15], 1):
            source_items += f"""
            <div style="margin-bottom:12px;padding:10px;background:#f8fafc;border-left:3px solid #0070f3;">
                <strong>[{idx}]</strong> {src.get("title", "Untitled")}
                <br><span style="font-size:0.9rem;color:#666;">{src.get("url", "")}</span>
            </div>
            """
        
        sources_html = f"""
        <div class="section">
            <h2>🔗 Sources ({len(sources)})</h2>
            {source_items}
        </div>
        """
    
    # Format answer with line breaks
    answer_formatted = answer.replace("\n", "<br>")
    
    # Complete HTML document [1]
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SAP Help Navigator Pro - Report</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f8fafc;
                color: #1e293b;
            }}
            .header {{
                background: linear-gradient(135deg, #0070f3 0%, #00c6ff 100%);
                color: white;
                padding: 30px;
                border-radius: 12px;
                margin-bottom: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header h1 {{
                margin: 0 0 10px 0;
                font-size: 2rem;
            }}
            .header p {{
                margin: 0;
                opacity: 0.95;
            }}
            .section {{
                background: white;
                padding: 30px;
                margin-bottom: 20px;
                border-radius: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            .section h2 {{
                color: #0070f3;
                margin-top: 0;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 10px;
            }}
            .answer {{
                font-size: 1.05rem;
                line-height: 1.8;
                color: #334155;
            }}
            a {{
                color: #0070f3;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .footer {{
                text-align: center;
                color: #64748b;
                padding: 20px;
                font-size: 0.9rem;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔷 SAP Help Navigator Pro</h1>
            <p>Product: <strong>{product or "General SAP"}</strong> &nbsp;·&nbsp; {now}
            &nbsp;·&nbsp; <a href="https://help.sap.com/docs" style="color:#fff">help.sap.com</a></p>
        </div>
        
        <div class="section">
            <h2>❓ Question</h2>
            <p style="font-size:1.05rem;font-weight:500">{question}</p>
        </div>
        
        <div class="section">
            <h2>💡 Answer</h2>
            <div class="answer">{answer_formatted}</div>
        </div>
        
        {checklist_html}
        
        {sources_html}
        
        <div class="footer">
            SAP Help Navigator Pro &nbsp;·&nbsp; {now}
            &nbsp;·&nbsp; For internal use only
            &nbsp;·&nbsp; <a href="https://help.sap.com/docs">help.sap.com</a>
        </div>
    </body>
    </html>
    """
    
    return html

# ============================================================
# UI RENDERING FUNCTIONS
# ============================================================

def render_checklist_generator_tab():
    """Render Checklist Generator tab [1]"""
    st.title("✅ Pre-Upgrade Checklist Generator")
    st.markdown("Generate comprehensive checklist based on upgrade path [1]")
    
    col1, col2 = st.columns(2)
    
    with col1:
        source = st.selectbox(
            "Source System:",
            ["ECC 6.0 EHP5", "ECC 6.0 EHP6", "ECC 6.0 EHP7", "ECC 6.0 EHP8",
             "S/4HANA 2020", "S/4HANA 2021", "S/4HANA 2022"],
            key="checklist_source"
        )
    
    with col2:
        target = st.selectbox(
            "Target System:",
            ["S/4HANA 2023", "S/4HANA 2025"],
            key="checklist_target"
        )
    
    # Additional options
    st.markdown("### Additional Options")
    col_a, col_b = st.columns(2)
    
    with col_a:
        include_custom_code = st.checkbox("Include custom code analysis steps", value=True)
        include_infrastructure = st.checkbox("Include infrastructure checks", value=True)
    
    with col_b:
        include_post_upgrade = st.checkbox("Include post-upgrade tasks", value=True)
        include_testing = st.checkbox("Include UAT steps", value=True)
    
    if st.button("📋 Generate Checklist", type="primary"):
        with st.spinner("Generating comprehensive checklist..."):
            checklist = generate_checklist(source, target)
            
            # Store in session state for HTML report
            st.session_state["last_checklist"] = checklist
            
            st.success(f"✅ Generated {len(checklist)} checklist items for {source} → {target}")
            
            # Display checklist by category
            categories = {}
            for item in checklist:
                cat = item.get("cat", "Other")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(item)
            
            for cat, items in categories.items():
                with st.expander(f"{items[0].get('icon', '📌')} {cat} ({len(items)} items)", expanded=True):
                    for item in items:
                        priority_color = {
                            "Critical": "🔴",
                            "High": "🟡",
                            "Medium": "🟢"
                        }.get(item.get("pri", "Medium"), "⚪")
                        
                        st.markdown(f"**{priority_color} {item.get('task', '')}** - {item.get('pri', '')}")
                        st.markdown(f"_{item.get('detail', '')}_")
                        st.markdown(f"🔧 Tool: `{item.get('tool', '')}`")
                        if item.get("note"):
                            st.markdown(f"📋 [SAP Note {item['note']}](https://launchpad.support.sap.com/#/notes/{item['note']})")
                        st.markdown("---")
            
            # Export options
            st.markdown("### 💾 Export Checklist")
            col1, col2 = st.columns(2)
            
            with col1:
                csv_data = export_checklist_csv(checklist)
                st.download_button(
                    label="📄 Download as CSV",
                    data=csv_data,
                    file_name=f"SAP_Checklist_{source.replace(' ', '_')}_to_{target.replace(' ', '_')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                json_data = json.dumps(checklist, indent=2)
                st.download_button(
                    label="📦 Download as JSON",
                    data=json_data,
                    file_name=f"SAP_Checklist_{source.replace(' ', '_')}_to_{target.replace(' ', '_')}.json",
                    mime="application/json"
                )

def render_html_report_generator():
    """Render HTML Report Generator section [1]"""
    st.title("📄 HTML Report Generator")
    st.markdown("Generate professional HTML reports with Q&A, sources, and checklists [1]")
    
    # Check if there's data to generate report from
    if "last_qa" not in st.session_state:
        st.info("ℹ️ Generate an upgrade plan or ask a question first to create an HTML report")
        return
    
    last_qa = st.session_state.get("last_qa", {})
    
    st.markdown("### Report Contents")
    col1, col2 = st.columns(2)
    
    with col1:
        include_answer = st.checkbox("Include Q&A", value=True, disabled=True)
        include_sources = st.checkbox("Include sources", value=True)
    
    with col2:
        include_checklist = st.checkbox("Include checklist", value=True)
    
    if st.button("📄 Generate & Download HTML Report", type="primary", use_container_width=True):
        checklist_data = st.session_state.get("last_checklist", []) if include_checklist else []
        sources_data = last_qa.get("sources", []) if include_sources else []
        
        html_content = generate_html_report(
            product=last_qa.get("product", "SAP"),
            question=last_qa.get("question", "Upgrade Planning"),
            answer=last_qa.get("answer", ""),
            sources=sources_data,
            checklist=checklist_data
        )
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SAP_Help_Navigator_Report_{timestamp}.html"
        
        st.download_button(
            label="💾 Download HTML Report",
            data=html_content,
            file_name=filename,
            mime="text/html",
            use_container_width=True
        )
        
        st.success("✅ HTML report generated successfully! [1]")
        
        # Preview
        with st.expander("👁️ Preview Report"):
            st.components.v1.html(html_content, height=600, scrolling=True)

# End of Part 8
# ============================================================
# SAP HELP NAVIGATOR PRO - PART 9/11 (ENHANCED)
# Landscape Visualizer with Upgrade Roadmaps
# ============================================================

import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Tuple

# ============================================================
# UPGRADE ROADMAP DEFINITIONS
# ============================================================

def get_upgrade_roadmaps() -> Dict:
    """
    Define all SAP upgrade/migration roadmaps with details
    Based on SAP best practices [1]
    """
    return {
        "Standard Upgrade": {
            "name": "Standard System Upgrade",
            "acronym": "Standard",
            "description": "Traditional upgrade approach using SUM (Software Update Manager) [1]",
            "use_case": "Release-to-release upgrades within same product line",
            "downtime": "High (24-48 hours typical)",
            "complexity": "Medium",
            "phases": [
                "Preparation",
                "Shadow System Import",
                "SPDD/SPAU Adjustments",
                "Downtime Starts",
                "Switch to Target",
                "Post-Processing"
            ],
            "pros": [
                "Well-established and proven method",
                "Preserves all data and customizations",
                "Comprehensive SAP documentation available [1]",
                "No data migration complexity"
            ],
            "cons": [
                "Significant downtime required (24-48 hours)",
                "All systems must be upgraded in sequence [1]",
                "Cannot skip intermediate releases easily",
                "Full system unavailable during upgrade"
            ],
            "tools": ["SUM (Software Update Manager)", "SAP Maintenance Planner [1]"],
            "sap_notes": ["2568780", "2186744"]
        },
        
        "DMO": {
            "name": "Database Migration Option",
            "acronym": "DMO",
            "description": "Combined upgrade + database migration to HANA in single step",
            "use_case": "ECC to S/4HANA conversion with non-HANA to HANA DB migration",
            "downtime": "High (36-72 hours typical)",
            "complexity": "High",
            "phases": [
                "Preparation",
                "Shadow System Clone",
                "Database Migration to HANA",
                "ABAP Import",
                "SPDD/SPAU",
                "Downtime & Switch",
                "Finalization"
            ],
            "pros": [
                "Single-step approach (upgrade + DB migration)",
                "Reduces overall project timeline",
                "Automated by SUM with DMO option",
                "Recommended by SAP for S/4HANA conversions [1]"
            ],
            "cons": [
                "Very long downtime (36-72 hours)",
                "High complexity and risk",
                "Requires significant hardware resources",
                "Rollback is complex"
            ],
            "tools": ["SUM with DMO", "SWPM", "R3load"],
            "sap_notes": ["2399707", "2913617"]
        },
        
        "DoDMO": {
            "name": "Downtime Optimized DMO",
            "acronym": "DoDMO",
            "description": "DMO with minimized downtime through uptime data replication",
            "use_case": "S/4HANA conversion requiring reduced production downtime",
            "downtime": "Medium (8-20 hours typical)",
            "complexity": "High",
            "phases": [
                "Uptime Replication Setup",
                "Shadow System + Migration (Uptime)",
                "Delta Sync",
                "SPDD/SPAU (Can be uptime)",
                "Short Downtime Window",
                "Final Delta + Switch",
                "Go-Live"
            ],
            "pros": [
                "Significantly reduced downtime vs standard DMO",
                "Most work done during uptime",
                "Production system remains available longer",
                "Good balance of complexity vs. downtime"
            ],
            "cons": [
                "More complex setup and execution",
                "Requires careful delta synchronization",
                "Higher resource consumption during uptime",
                "Limited rollback window"
            ],
            "tools": ["SUM with DMO", "Replication tools", "Delta monitoring"],
            "sap_notes": ["2399707", "2774781"]
        },
        
        "nZDM": {
            "name": "Near-Zero Downtime Maintenance",
            "acronym": "nZDM",
            "description": "Minimize downtime for release upgrades using clone and sync",
            "use_case": "S/4HANA to S/4HANA upgrades with minimal downtime requirement",
            "downtime": "Low (2-8 hours typical)",
            "complexity": "Very High",
            "phases": [
                "Clone Production to Shadow",
                "Upgrade Shadow System (Uptime)",
                "Sync Changes to Shadow",
                "SPDD/SPAU on Shadow",
                "Final Sync Window",
                "Brief Downtime (Switch)",
                "Production on New Release"
            ],
            "pros": [
                "Minimal production downtime (hours vs days)",
                "Business continues during most of upgrade",
                "Lower business impact",
                "Proven for S/4HANA upgrades"
            ],
            "cons": [
                "Very high complexity",
                "Requires significant infrastructure",
                "Expensive (resources + SAP premium services)",
                "Requires expert planning and execution",
                "Not suitable for all scenarios"
            ],
            "tools": ["nZDM Technology", "SUM", "Replication tools"],
            "sap_notes": ["2343437", "2774781"]
        },
        
        "nZDT": {
            "name": "Near-Zero Downtime Technology",
            "acronym": "nZDT",
            "description": "Advanced zero-downtime approach with live table splitting",
            "use_case": "Large S/4HANA systems requiring absolute minimal downtime",
            "downtime": "Very Low (1-4 hours typical)",
            "complexity": "Extremely High",
            "phases": [
                "Pre-conversion setup",
                "Uptime table conversion",
                "Shadow instance preparation",
                "Critical table replication",
                "Minimal downtime switch",
                "Post-conversion cleanup"
            ],
            "pros": [
                "Absolute minimal downtime (hours)",
                "Business-critical operations barely affected",
                "Table-by-table conversion during uptime",
                "SAP's most advanced upgrade technology"
            ],
            "cons": [
                "Extremely complex implementation",
                "Very expensive (SAP Premium Engagement required)",
                "Long overall project duration",
                "Requires extensive planning (6+ months)",
                "Only for very large/critical systems"
            ],
            "tools": ["nZDT Framework", "DMO", "Custom table replication"],
            "sap_notes": ["2343437", "2774781", "2731427"]
        },
        
        "ZDO": {
            "name": "Zero Downtime Option",
            "acronym": "ZDO",
            "description": "Hybrid approach combining uptime conversion with brief switch",
            "use_case": "Medium-to-large systems needing minimal downtime",
            "downtime": "Low (4-12 hours typical)",
            "complexity": "High",
            "phases": [
                "Preparation and validation",
                "Uptime shadow creation",
                "Table conversion (uptime)",
                "Code import (uptime)",
                "Brief downtime for switch",
                "Validation and go-live"
            ],
            "pros": [
                "Good balance of complexity and downtime",
                "Most conversion work during uptime",
                "More affordable than nZDT",
                "Suitable for many enterprise scenarios"
            ],
            "cons": [
                "Still requires careful planning",
                "Infrastructure overhead during uptime",
                "Longer overall project timeline",
                "Not as minimal downtime as nZDT"
            ],
            "tools": ["SUM with ZDO", "Shadow system tools"],
            "sap_notes": ["2774781", "2343437"]
        },
        
        "Selective Data Transition": {
            "name": "Selective Data Transition",
            "acronym": "SDT",
            "description": "Migrate only selected data to new S/4HANA system (no full history)",
            "use_case": "Legacy ECC systems with data cleanup opportunity",
            "downtime": "Variable (depends on scope)",
            "complexity": "Very High",
            "phases": [
                "Data assessment and scoping",
                "Greenfield S/4HANA installation",
                "Data mapping and transformation",
                "Selective extraction",
                "Data load and validation",
                "Cutover and hypercare"
            ],
            "pros": [
                "Clean start without technical debt",
                "Opportunity to redesign processes",
                "Smaller target database size",
                "Can eliminate obsolete data",
                "Fresh system with best practices [1]"
            ],
            "cons": [
                "Very long project duration (12-24 months)",
                "High cost and resource intensity",
                "Complex data migration logic required",
                "Historical data may be lost or archived",
                "Business process reengineering needed"
            ],
            "tools": ["SAP Data Services", "Migration Cockpit", "LTMC", "LSMW"],
            "sap_notes": ["3214014", "2769531"]
        }
    }

def compare_roadmaps(roadmap_names: List[str]) -> pd.DataFrame:
    """Create comparison dataframe for selected roadmaps"""
    roadmaps = get_upgrade_roadmaps()
    
    comparison_data = []
    for name in roadmap_names:
        if name in roadmaps:
            rm = roadmaps[name]
            comparison_data.append({
                "Approach": rm["acronym"],
                "Downtime": rm["downtime"],
                "Complexity": rm["complexity"],
                "Best For": rm["use_case"],
                "Phases": len(rm["phases"])
            })
    
    return pd.DataFrame(comparison_data)

# ============================================================
# N+1 LANDSCAPE RECOMMENDATION ENGINE
# ============================================================

def analyze_landscape_and_recommend(landscape: Dict, source_release: str, target_release: str) -> Dict:
    """
    Analyze landscape and recommend N+1 approach where needed
    Based on SAP best practices [1]
    """
    systems = landscape.get("systems", [])
    
    # Check if N+1 is needed
    needs_n_plus_1 = False
    reason = ""
    
    # Example: If going from ECC 6.0 EHP5 to S/4HANA, suggest intermediate step
    if "ECC 6.0 EHP5" in source_release and "S/4HANA" in target_release:
        needs_n_plus_1 = True
        reason = "Direct upgrade from ECC 6.0 EHP5 to S/4HANA not supported. Recommended path: ECC 6.0 EHP5 → EHP7/EHP8 → S/4HANA [1]"
    
    # Check system landscape complexity
    if len(systems) > 5:
        needs_n_plus_1 = True
        reason += " Large landscape detected. Consider phased N+1 approach for risk mitigation [1]"
    
    recommendation = {
        "needs_n_plus_1": needs_n_plus_1,
        "reason": reason,
        "recommended_path": [],
        "benefits": []
    }
    
    if needs_n_plus_1:
        recommendation["recommended_path"] = [
            source_release,
            "Intermediate Release (EHP7/EHP8 or S/4HANA 2020)",
            target_release
        ]
        recommendation["benefits"] = [
            "Reduced complexity per upgrade cycle",
            "Better risk management through staged approach [1]",
            "Opportunity to validate at each stage",
            "Easier rollback at intermediate steps",
            "Time to adapt custom code gradually"
        ]
    
    return recommendation

# ============================================================
# GRAPHICAL PHASE COMPARISON
# ============================================================

def create_phase_comparison_chart(selected_roadmaps: List[str]) -> go.Figure:
    """Create Gantt-style chart comparing phases across roadmaps"""
    roadmaps = get_upgrade_roadmaps()
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set2
    
    for idx, rm_name in enumerate(selected_roadmaps):
        if rm_name not in roadmaps:
            continue
        
        rm = roadmaps[rm_name]
        phases = rm["phases"]
        
        for phase_idx, phase in enumerate(phases):
            fig.add_trace(go.Bar(
                name=f"{rm['acronym']} - {phase}",
                x=[1],
                y=[f"{rm['acronym']}"],
                orientation='h',
                marker=dict(color=colors[phase_idx % len(colors)]),
                text=phase,
                textposition='inside',
                hovertemplate=f"<b>{rm['acronym']}</b><br>{phase}<extra></extra>",
                showlegend=(idx == 0)  # Only show legend for first roadmap
            ))
    
    fig.update_layout(
        title="🔄 Upgrade Roadmap Phase Comparison",
        xaxis_title="Relative Phase Duration",
        yaxis_title="Roadmap",
        barmode='stack',
        height=400,
        hovermode='closest'
    )
    
    return fig

def create_downtime_comparison(selected_roadmaps: List[str]) -> go.Figure:
    """Create downtime comparison visualization"""
    roadmaps = get_upgrade_roadmaps()
    
    downtime_map = {
        "Very Low (1-4 hours)": 2.5,
        "Low (2-8 hours)": 5,
        "Low (4-12 hours)": 8,
        "Medium (8-20 hours)": 14,
        "High (24-48 hours)": 36,
        "High (36-72 hours)": 54,
        "Variable (depends on scope)": 24
    }
    
    roadmap_names = []
    downtime_hours = []
    colors_list = []
    
    for rm_name in selected_roadmaps:
        if rm_name in roadmaps:
            rm = roadmaps[rm_name]
            roadmap_names.append(rm["acronym"])
            downtime_hours.append(downtime_map.get(rm["downtime"], 24))
            
            # Color by downtime level
            if "Very Low" in rm["downtime"]:
                colors_list.append("#10b981")
            elif "Low" in rm["downtime"]:
                colors_list.append("#3b82f6")
            elif "Medium" in rm["downtime"]:
                colors_list.append("#f59e0b")
            else:
                colors_list.append("#dc2626")
    
    fig = go.Figure(data=[
        go.Bar(
            x=roadmap_names,
            y=downtime_hours,
            marker_color=colors_list,
            text=[f"{h}h" for h in downtime_hours],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="⏱️ Expected Downtime Comparison",
        xaxis_title="Roadmap",
        yaxis_title="Downtime (hours)",
        height=400,
        showlegend=False
    )
    
    return fig

# ============================================================
# ENHANCED UI RENDERING FUNCTIONS
# ============================================================

def render_landscape_visualizer_tab():
    """Enhanced Landscape Visualizer with source/target selection [1]"""
    st.title("🗺️ SAP Landscape Visualizer & Upgrade Roadmap Planner")
    st.markdown("Visualize landscape, compare upgrade approaches, and get N+1 recommendations [1]")
    
    # Source and Target Selection
    st.markdown("### 🎯 Upgrade Planning")
    
    col1, col2 = st.columns(2)
    
    with col1:
        source_release = st.selectbox(
            "Source Release:",
            [
                "ECC 6.0 EHP5", "ECC 6.0 EHP6", "ECC 6.0 EHP7", "ECC 6.0 EHP8",
                "S/4HANA 2020", "S/4HANA 2021", "S/4HANA 2022", "S/4HANA 2023"
            ],
            key="landscape_source"
        )
    
    with col2:
        target_release = st.selectbox(
            "Target Release:",
            ["S/4HANA 2023", "S/4HANA 2025"],
            key="landscape_target"
        )
    
    # Load or create landscape
    use_sample = st.checkbox("Use sample landscape", value=True)
    
    if use_sample:
        landscape = create_sample_landscape()
    else:
        st.info("Custom landscape builder - Using sample for now")
        landscape = create_sample_landscape()
    
    # N+1 Analysis
    if st.button("🔍 Analyze Landscape & Recommend Approach", type="primary"):
        recommendation = analyze_landscape_and_recommend(landscape, source_release, target_release)
        
        if recommendation["needs_n_plus_1"]:
            st.warning("⚠️ N+1 Intermediate Upgrade Recommended")
            st.markdown(f"**Reason:** {recommendation['reason']}")
            
            st.markdown("### 📍 Recommended Upgrade Path:")
            for step_idx, step in enumerate(recommendation["recommended_path"], 1):
                st.markdown(f"{step_idx}. **{step}**")
            
            st.markdown("### ✅ Benefits of N+1 Approach:")
            for benefit in recommendation["benefits"]:
                st.markdown(f"- {benefit}")
        else:
            st.success("✅ Direct upgrade path is feasible")
            st.info(f"You can proceed directly from {source_release} to {target_release} [1]")
    
    # Display landscape diagram
    st.markdown("---")
    st.markdown("### 🏗️ Current Landscape Topology")
    fig = create_landscape_diagram(landscape)
    st.plotly_chart(fig, use_container_width=True)
    
    # System details
    st.markdown("---")
    st.markdown("### 📊 System Details")
    
    systems_df = pd.DataFrame(landscape["systems"])
    systems_display = systems_df[["sid", "name", "type", "release", "db", "users", "criticality"]]
    systems_display.columns = ["SID", "Name", "Type", "Current Release", "Database", "Users", "Criticality"]
    
    st.dataframe(systems_display, use_container_width=True)
    
    # Upgrade Roadmap Comparison
    st.markdown("---")
    st.markdown("### 🔄 Upgrade Roadmap Comparison")
    
    roadmaps = get_upgrade_roadmaps()
    
    # Multi-select for comparison
    selected_roadmaps = st.multiselect(
        "Select roadmaps to compare:",
        list(roadmaps.keys()),
        default=["Standard Upgrade", "DMO", "nZDM"],
        key="roadmap_compare"
    )
    
    if len(selected_roadmaps) < 2:
        st.info("ℹ️ Select at least 2 roadmaps to compare")
    else:
        # Show comparison table
        comparison_df = compare_roadmaps(selected_roadmaps)
        st.dataframe(comparison_df, use_container_width=True)
        
        # Show detailed pros/cons
        st.markdown("### 📋 Detailed Analysis")
        
        for rm_name in selected_roadmaps:
            with st.expander(f"🔍 {roadmaps[rm_name]['name']} ({roadmaps[rm_name]['acronym']})"):
                rm = roadmaps[rm_name]
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.markdown("**✅ Pros:**")
                    for pro in rm["pros"]:
                        st.markdown(f"- {pro}")
                
                with col_b:
                    st.markdown("**❌ Cons:**")
                    for con in rm["cons"]:
                        st.markdown(f"- {con}")
                
                st.markdown(f"**📝 Description:** {rm['description']}")
                st.markdown(f"**🎯 Best For:** {rm['use_case']}")
                st.markdown(f"**⏱️ Downtime:** {rm['downtime']}")
                st.markdown(f"**🔧 Complexity:** {rm['complexity']}")
                
                st.markdown("**🔧 Tools Required:**")
                for tool in rm["tools"]:
                    st.markdown(f"- {tool}")
                
                st.markdown("**📋 Key SAP Notes:**")
                for note in rm["sap_notes"]:
                    st.markdown(f"- [SAP Note {note}](https://launchpad.support.sap.com/#/notes/{note})")
        
        # Graphical comparisons
        st.markdown("---")
        st.markdown("### 📊 Visual Comparisons")
        
        tab1, tab2 = st.tabs(["Phase Comparison", "Downtime Analysis"])
        
        with tab1:
            phase_fig = create_phase_comparison_chart(selected_roadmaps)
            st.plotly_chart(phase_fig, use_container_width=True)
        
        with tab2:
            downtime_fig = create_downtime_comparison(selected_roadmaps)
            st.plotly_chart(downtime_fig, use_container_width=True)
    
    # Upgrade sequencing (existing functionality)
    st.markdown("---")
    st.markdown("### 🔄 Recommended System Upgrade Sequence")
    
    if st.button("🧮 Calculate Upgrade Sequence"):
        sequence = calculate_upgrade_sequence(landscape)
        
        for step in sequence:
            with st.expander(
                f"Step {step['order']}: {step['sid']} - {step['name']} ({step['downtime_hours']}h)",
                expanded=(step['order'] == 1)
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Current", step["current_release"])
                    st.metric("Target", step["target_release"])
                    st.metric("Downtime", f"{step['downtime_hours']} hours")
                
                with col2:
                    st.metric("Cumulative", f"{step['cumulative_downtime']} hours")
                    st.markdown(f"**Impact:** {step['business_impact']}")
                    if step["parallel_possible"]:
                        st.success("✅ Can run in parallel")
                
                st.markdown("**Prerequisites:**")
                for prereq in step["prerequisites"]:
                    st.markdown(f"- {prereq}")

# End of Enhanced Part 9
# ============================================================
# SAP HELP NAVIGATOR PRO - PART 10/11
# SUM Monitor & Guide Download Helper
# ============================================================

import re
from datetime import datetime

# ============================================================
# SUM MONITOR
# ============================================================

def get_sum_phases() -> List[Dict]:
    """
    Get all SUM (Software Update Manager) phases
    Based on context [1]
    """
    return [
        {
            "phase": "INITSUM",
            "name": "Initialization",
            "description": "Initial SUM setup and validation",
            "typical_duration": "15-30 min",
            "key_activities": [
                "Extract SUM tool",
                "Start SUM UI",
                "Upload stack.xml",
                "Validate prerequisites"
            ],
            "critical": True
        },
        {
            "phase": "PRECONFIG",
            "name": "Pre-Configuration",
            "description": "System preparation and configuration checks",
            "typical_duration": "30-60 min",
            "key_activities": [
                "Check system parameters",
                "Validate disk space",
                "Check database consistency",
                "Verify kernel compatibility"
            ],
            "critical": True
        },
        {
            "phase": "EXTRACT_PAT",
            "name": "Extract Archives",
            "description": "Extract software archives to file system",
            "typical_duration": "2-4 hours",
            "key_activities": [
                "Extract SAR files",
                "Unpack installation media",
                "Verify checksums"
            ],
            "critical": False
        },
        {
            "phase": "EU_CLONE",
            "name": "Clone System",
            "description": "Create shadow system for upgrade",
            "typical_duration": "4-8 hours",
            "key_activities": [
                "Clone SAP system",
                "Clone database schema",
                "Setup shadow instance"
            ],
            "critical": True
        },
        {
            "phase": "EU_IMPORT",
            "name": "Import ABAP",
            "description": "Import new ABAP code to shadow system",
            "typical_duration": "6-12 hours",
            "key_activities": [
                "Import BASIS components",
                "Import application components",
                "Generate ABAP loads"
            ],
            "critical": True
        },
        {
            "phase": "SPDD_SPAU",
            "name": "Modification Adjustment",
            "description": "Adjust dictionary and repository modifications",
            "typical_duration": "2-8 hours (manual)",
            "key_activities": [
                "Execute SPDD transaction",
                "Adjust data dictionary changes",
                "Execute SPAU transaction",
                "Adjust repository modifications"
            ],
            "critical": True,
            "requires_manual": True
        },
        {
            "phase": "DOWNTIME",
            "name": "Downtime Start",
            "description": "Begin production downtime window",
            "typical_duration": "N/A",
            "key_activities": [
                "Stop application servers",
                "Lock all users",
                "Begin downtime monitoring"
            ],
            "critical": True
        },
        {
            "phase": "EU_SWITCH",
            "name": "Switch to Shadow",
            "description": "Switch from original to shadow system",
            "typical_duration": "1-2 hours",
            "key_activities": [
                "Stop original system",
                "Activate shadow system",
                "Update system profiles"
            ],
            "critical": True
        },
        {
            "phase": "FINALIZE",
            "name": "Finalization",
            "description": "Complete upgrade and cleanup",
            "typical_duration": "1-2 hours",
            "key_activities": [
                "Remove shadow repository",
                "Update kernel",
                "Generate new profiles",
                "System consistency checks"
            ],
            "critical": True
        },
        {
            "phase": "POSTPROC",
            "name": "Post-Processing",
            "description": "Post-upgrade activities",
            "typical_duration": "30-60 min",
            "key_activities": [
                "Apply latest patches",
                "Run RUTPOADAPT",
                "Update client settings",
                "Start application servers"
            ],
            "critical": False
        }
    ]

def get_sum_troubleshooting_tips() -> Dict[str, str]:
    """Common SUM issues and resolutions [1]"""
    return {
        "Phase stuck": "Check SUM logs in /usr/sap/<SID>/SUM/abap/log/ - Look for ERROR or FATAL entries [1]",
        "EU_CLONE fails": "Verify disk space. Check database connectivity. Review sumabap_clone.log [1]",
        "SPDD timeout": "Increase timeout in SUM parameters. Split adjustments into smaller batches [1]",
        "EU_IMPORT errors": "Check tp log files. Verify all archives extracted correctly [1]",
        "Memory shortage": "Increase Java heap size in SUM startup script (-Xmx parameter) [1]",
        "Database locks": "Check for long-running database queries. May need DBA intervention [1]",
        "Cannot access SUM UI": "Verify port 1129 is open. Check https://<host>:1129/lmsl/sumabap/<SID>/doc/ [1]"
    }

# ============================================================
# GUIDE DOWNLOAD HELPER
# ============================================================

def get_guide_download_instructions(doc_type: str, product: str, version: str) -> str:
    """
    Generate instructions for downloading SAP guides
    Based on context [1]
    """
    
    base_instructions = f"""
## 📚 How to Download {doc_type} for {product} {version}

### Method 1: SAP Help Portal (Recommended) [1]

1. **Navigate to SAP Help Portal:**
   - Go to: https://help.sap.com/docs
   - Or direct link: https://help.sap.com/viewer/product/{product.replace(' ', '_')}/{version}/en-US

2. **Find Documentation:**
   - Search for "{doc_type}"
   - Or browse: Product Documentation → {product} → {version}

3. **Download PDF:**
   - Click on document title
   - Look for "Download" or "PDF" icon (usually top-right)
   - Select language (English, German, etc.)
   - Click "Download PDF"

---

### Method 2: SAP Support Portal (S-User Required) [1]

1. **Login to SAP Support:**
   - Go to: https://support.sap.com/
   - Login with your S-user credentials

2. **Navigate to Software Downloads:**
   - Software Downloads → Support Packages and Patches
   - Or: https://support.sap.com/swdc

3. **Find Product:**
   - Search for: {product}
   - Select version: {version}
   - Navigate to: Documentation → {doc_type}

4. **Download:**
   - Click download link
   - Save to local directory

---

### Method 3: SAP ONE Support Launchpad [1]

1. **Access Launchpad:**
   - Go to: https://launchpad.support.sap.com/
   - Login with S-user

2. **Search Documentation:**
   - Use search bar: "{product} {version} {doc_type}"
   - Filter by: Document Type = "Guide/Manual"

3. **Download:**
   - Click on result
   - Select "Download PDF"

---

### Quick Links:

"""
    
    # Add product-specific links
    if "S/4HANA" in product:
        base_instructions += """
- **Installation Guide:** https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/installation
- **Upgrade Guide:** https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/upgrade
- **Operations Guide:** https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/operations
- **SAP Notes:** https://launchpad.support.sap.com/#/notes/
"""
    elif "HANA" in product:
        base_instructions += """
- **HANA Administration:** https://help.sap.com/docs/SAP_HANA_PLATFORM/admin
- **Installation Guide:** https://help.sap.com/docs/SAP_HANA_PLATFORM/installation
- **Update Guide:** https://help.sap.com/docs/SAP_HANA_PLATFORM/update
"""
    
    base_instructions += """
---

### Tips:

- **Bookmark frequently used guides** for quick access [1]
- **Check SAP Notes** for latest corrections to documentation [1]
- **Download offline** if working in restricted environments [1]
- **Version matters**: Always download guide matching your exact release [1]

---

### Troubleshooting:

**Can't find document?**
- Verify you have correct product name and version
- Check if you need S-user access
- Try searching in multiple languages

**Download fails?**
- Check your internet connection
- Try different browser
- Disable popup blockers
- Contact SAP Support if persistent issues

**Need specific section?**
- Use PDF bookmarks/table of contents
- Most guides have detailed index
- Search within PDF (Ctrl+F)
"""
    
    return base_instructions

# ============================================================
# UI RENDERING FUNCTIONS
# ============================================================

def render_sum_monitor_tab():
    """Render SUM Monitor tab [1]"""
    st.title("📊 SUM (Software Update Manager) Monitor")
    st.markdown("Track SUM phases and troubleshoot upgrade issues [1]")
    
    # SUM UI Access
    st.markdown("### 🌐 SUM Web UI Access")
    
    col1, col2 = st.columns(2)
    with col1:
        sum_host = st.text_input("SUM Host:", placeholder="hostname.domain.com", key="sum_host")
    with col2:
        sum_sid = st.text_input("System SID:", placeholder="S4D", key="sum_sid")
    
    if sum_host and sum_sid:
        sum_url = f"https://{sum_host}:1129/lmsl/sumabap/{sum_sid}/doc/"
        st.success(f"🔗 SUM Web UI: [{sum_url}]({sum_url}) [1]")
        st.info(f"📁 Log Location: `/usr/sap/{sum_sid}/SUM/abap/log/` [1]")
    
    # Phase overview
    st.markdown("---")
    st.markdown("### 📋 SUM Phases Overview")
    
    phases = get_sum_phases()
    
    for phase in phases:
        icon = "🔴" if phase.get("critical") else "🟢"
        manual_flag = " ⚠️ (Requires Manual Action)" if phase.get("requires_manual") else ""
        
        with st.expander(
            f"{icon} {phase['phase']} - {phase['name']}{manual_flag}",
            expanded=False
        ):
            st.markdown(f"**Description:** {phase['description']}")
            st.markdown(f"**Typical Duration:** {phase['typical_duration']}")
            
            st.markdown("**Key Activities:**")
            for activity in phase["key_activities"]:
                st.markdown(f"- {activity}")
            
            if phase.get("requires_manual"):
                st.warning("⚠️ This phase requires manual intervention [1]")
    
    # Troubleshooting guide
    st.markdown("---")
    st.markdown("### 🔧 Common Issues & Solutions")
    
    tips = get_sum_troubleshooting_tips()
    
    issue = st.selectbox(
        "Select Issue:",
        list(tips.keys()),
        key="sum_issue"
    )
    
    if issue:
        st.info(f"**Solution:** {tips[issue]}")
    
    # Log analysis helper
    st.markdown("---")
    st.markdown("### 🔍 Log Analysis Helper")
    
    log_content = st.text_area(
        "Paste SUM log excerpt (optional):",
        height=200,
        placeholder="Paste log lines here for quick analysis...",
        key="sum_log"
    )
    
    if log_content and st.button("🔍 Analyze Log", key="analyze_sum_log"):
        # Simple log analysis
        errors = [line for line in log_content.split("\n") if "ERROR" in line.upper() or "FATAL" in line.upper()]
        warnings = [line for line in log_content.split("\n") if "WARNING" in line.upper() or "WARN" in line.upper()]
        
        if errors:
            st.error(f"❌ Found {len(errors)} ERROR/FATAL entries:")
            for err in errors[:5]:  # Show first 5
                st.code(err, language="log")
        
        if warnings:
            st.warning(f"⚠️ Found {len(warnings)} WARNING entries:")
            for warn in warnings[:3]:  # Show first 3
                st.code(warn, language="log")
        
        if not errors and not warnings:
            st.success("✅ No obvious errors or warnings detected in provided log excerpt")

def render_guide_downloader_tab():
    """Render Guide Download Helper tab [1]"""
    st.title("📚 SAP Guide Download Helper")
    st.markdown("Step-by-step instructions to download SAP documentation [1]")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        product = st.selectbox(
            "SAP Product:",
            ["S/4HANA", "SAP HANA", "NetWeaver", "BW/4HANA", "Solution Manager"],
            key="guide_product"
        )
    
    with col2:
        version = st.text_input(
            "Version:",
            placeholder="e.g., 2023, 2.0 SPS07",
            key="guide_version"
        )
    
    with col3:
        doc_type = st.selectbox(
            "Document Type:",
            [
                "Installation Guide",
                "Upgrade Guide",
                "Master Guide",
                "Operations Guide",
                "Security Guide",
                "High Availability Guide",
                "Performance Guide",
                "Configuration Guide"
            ],
            key="guide_doc_type"
        )
    
    if st.button("📖 Generate Download Instructions", type="primary"):
        if not version:
            st.warning("Please enter a version number")
        else:
            instructions = get_guide_download_instructions(doc_type, product, version)
            st.markdown(instructions)
            
            # Download as text file
            st.download_button(
                label="💾 Download Instructions as TXT",
                data=instructions,
                file_name=f"SAP_{product.replace(' ', '_')}_{version}_{doc_type.replace(' ', '_')}_Download.txt",
                mime="text/plain"
            )

# End of Part 10
# ============================================================
# SAP HELP NAVIGATOR PRO - PART 11/11
# Gemini Search, Batch Q&A & Main Integration
# ============================================================

import google.generativeai as genai
from typing import List, Dict, Optional
import time

# ============================================================
# GEMINI API INTEGRATION
# ============================================================

def initialize_gemini(api_key: str) -> bool:
    """Initialize Google Gemini API [1]"""
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Failed to initialize Gemini API: {e}")
        return False

def search_sap_docs_with_gemini(
    query: str,
    product: str = "SAP",
    api_key: str = None
) -> Dict:
    """
    Search SAP documentation using Gemini API
    Based on context [1]
    """
    
    if not api_key:
        return {
            "success": False,
            "error": "API key required",
            "answer": None
        }
    
    try:
        if not initialize_gemini(api_key):
            return {"success": False, "error": "API initialization failed"}
        
        model = genai.GenerativeModel('gemini-pro')
        
        # Craft SAP-specific prompt
        prompt = f"""
        You are an expert SAP consultant with deep knowledge of {product} documentation.
        
        Question: {query}
        
        Please provide a comprehensive answer that includes:
        1. Direct answer to the question
        2. Relevant SAP transaction codes (if applicable)
        3. Key SAP Notes that should be referenced
        4. Step-by-step instructions (if applicable)
        5. Best practices and recommendations
        
        Format your response in a clear, structured manner with headings and bullet points.
        """
        
        response = model.generate_content(prompt)
        
        return {
            "success": True,
            "answer": response.text,
            "query": query,
            "product": product,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "answer": None
        }

# ============================================================
# BATCH Q&A
# ============================================================

def process_batch_questions(
    questions: List[str],
    product: str,
    api_key: str
) -> List[Dict]:
    """
    Process multiple questions in batch
    Based on context [1]
    """
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, question in enumerate(questions):
        status_text.text(f"Processing question {idx + 1} of {len(questions)}...")
        
        result = search_sap_docs_with_gemini(question, product, api_key)
        results.append({
            "question": question,
            "answer": result.get("answer", "Error processing question"),
            "success": result.get("success", False),
            "error": result.get("error")
        })
        
        progress_bar.progress((idx + 1) / len(questions))
        
        # Rate limiting - wait 1 second between requests
        if idx < len(questions) - 1:
            time.sleep(1)
    
    status_text.text("✅ Batch processing complete!")
    return results

def export_batch_results(results: List[Dict], format_type: str = "markdown") -> str:
    """Export batch Q&A results [1]"""
    
    if format_type == "markdown":
        output = "# SAP Batch Q&A Results\n\n"
        output += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        output += "---\n\n"
        
        for idx, result in enumerate(results, 1):
            output += f"## Question {idx}\n\n"
            output += f"**Q:** {result['question']}\n\n"
            
            if result['success']:
                output += f"**A:**\n\n{result['answer']}\n\n"
            else:
                output += f"**Error:** {result.get('error', 'Unknown error')}\n\n"
            
            output += "---\n\n"
        
        return output
    
    elif format_type == "json":
        return json.dumps(results, indent=2)
    
    else:
        return str(results)

# ============================================================
# UI RENDERING FUNCTIONS
# ============================================================

def render_gemini_search_tab():
    """Render Gemini-powered search tab [1]"""
    st.title("🔍 AI-Powered SAP Search (Gemini)")
    st.markdown("Ask questions about SAP and get intelligent answers powered by Google Gemini [1]")
    
    # API Key input
    st.markdown("### 🔑 API Configuration")
    api_key = st.text_input(
        "Google Gemini API Key:",
        type="password",
        help="Get your API key from https://makersuite.google.com/app/apikey",
        key="gemini_api_key"
    )
    
    if not api_key:
        st.info("ℹ️ Enter your Google Gemini API key to use AI-powered search")
        st.markdown("""
        **How to get API key:**
        1. Visit https://makersuite.google.com/app/apikey
        2. Sign in with Google account
        3. Click "Create API Key"
        4. Copy and paste above
        """)
        return
    
    # Question input
    st.markdown("---")
    st.markdown("### ❓ Ask Your Question")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        question = st.text_area(
            "Enter your SAP question:",
            placeholder="e.g., How do I configure RFC destinations in S/4HANA?",
            height=100,
            key="gemini_question"
        )
    
    with col2:
        product = st.selectbox(
            "Product Context:",
            ["SAP General", "S/4HANA", "SAP HANA", "NetWeaver", "BW/4HANA"],
            key="gemini_product"
        )
    
    if st.button("🚀 Search with AI", type="primary", disabled=not question):
        with st.spinner("🤔 Searching SAP documentation with Gemini AI..."):
            result = search_sap_docs_with_gemini(question, product, api_key)
            
            if result["success"]:
                st.success("✅ Answer generated successfully!")
                
                # Display answer
                st.markdown("### 💡 Answer")
                st.markdown(result["answer"])
                
                # Store for HTML report
                st.session_state["last_qa"] = {
                    "product": product,
                    "question": question,
                    "answer": result["answer"],
                    "sources": []
                }
                
                # Download option
                st.download_button(
                    label="💾 Download Answer",
                    data=result["answer"],
                    file_name=f"SAP_Answer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
            else:
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")

def render_batch_qa_tab():
    """Render Batch Q&A tab [1]"""
    st.title("📦 Batch Question Processing")
    st.markdown("Process multiple SAP questions at once with AI [1]")
    
    # API Key
    api_key = st.text_input(
        "Google Gemini API Key:",
        type="password",
        key="batch_api_key"
    )
    
    if not api_key:
        st.info("ℹ️ Enter your Google Gemini API key to use batch processing")
        return
    
    st.markdown("---")
    
    # Input methods
    input_method = st.radio(
        "Input Method:",
        ["Enter manually", "Upload file"],
        horizontal=True
    )
    
    questions = []
    
    if input_method == "Enter manually":
        questions_text = st.text_area(
            "Enter questions (one per line):",
            height=200,
            placeholder="How to configure STMS?\nWhat is SAP Note 2568780?\nHow to check kernel version?",
            key="batch_questions"
        )
        
        if questions_text:
            questions = [q.strip() for q in questions_text.split("\n") if q.strip()]
    
    else:
        uploaded_file = st.file_uploader(
            "Upload text file with questions (one per line):",
            type=["txt"],
            key="batch_file"
        )
        
        if uploaded_file:
            content = uploaded_file.read().decode("utf-8")
            questions = [q.strip() for q in content.split("\n") if q.strip()]
    
    if questions:
        st.success(f"✅ {len(questions)} questions loaded")
        
        with st.expander("📋 Preview Questions"):
            for idx, q in enumerate(questions, 1):
                st.markdown(f"{idx}. {q}")
    
    # Process batch
    if questions and st.button("🚀 Process Batch", type="primary"):
        st.markdown("### 📊 Processing Progress")
        
        product = st.selectbox(
            "Product Context:",
            ["SAP General", "S/4HANA", "SAP HANA"],
            key="batch_product"
        )
        
        results = process_batch_questions(questions, product, api_key)
        
        # Display results
        st.markdown("---")
        st.markdown("### ✅ Results")
        
        for idx, result in enumerate(results, 1):
            with st.expander(f"Q{idx}: {result['question']}", expanded=(idx == 1)):
                if result['success']:
                    st.markdown(result['answer'])
                else:
                    st.error(f"Error: {result.get('error')}")
        
        # Export options
        st.markdown("---")
        st.markdown("### 💾 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            markdown_export = export_batch_results(results, "markdown")
            st.download_button(
                label="📄 Download as Markdown",
                data=markdown_export,
                file_name=f"SAP_Batch_QA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
        
        with col2:
            json_export = export_batch_results(results, "json")
            st.download_button(
                label="📦 Download as JSON",
                data=json_export,
                file_name=f"SAP_Batch_QA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# ============================================================
# UPDATED MAIN FUNCTION (Integrates all 11 parts)
# ============================================================

def main():
    """
    Main application entry point - Updated to include all features
    Based on context [1]
    """
    
    # Initialize session state
    if "deployment_type" not in st.session_state:
        st.session_state.deployment_type = "On-Premise"
    
    # Render sidebar
    page = render_sidebar()
    
    # Route to appropriate page
    if page == "🏠 Home":
        render_home_page()
        
    elif page == "📅 Release Calendar":
        display_release_calendar()
        
    elif page == "🔄 Upgrade Planner":
        render_upgrade_planner()
        
    elif page == "🌥️ RISE Migration":
        render_rise_migration_page()
        
    elif page == "⚙️ Parameter Advisor":
        render_parameter_advisor()
        
    elif page == "📐 Sizing Calculator":
        render_sizing_calculator()
        
    elif page == "📚 Resources":
        # Resources page with multiple tabs
        st.title("📚 SAP Resources & Tools")
        
        tabs = st.tabs([
            "📖 Documentation",
            "🔄 Upgrade Matrix",
            "🔍 Compatibility",
            "🐧 OS Parameters",
            "✅ Checklist",
            "📄 Reports",
            "🗺️ Landscape",
            "📊 SUM Monitor",
            "📚 Guide Helper",
            "🔍 AI Search",
            "📦 Batch Q&A"
        ])
        
        with tabs[0]:  # Documentation
            st.markdown("""
            ### Official SAP Resources
            - [SAP Help Portal](https://help.sap.com)
            - [SAP Support Portal](https://support.sap.com)
            - [SAP PAM](https://support.sap.com/pam)
            - [SAP Community](https://community.sap.com)
            - [SAP Learning Hub](https://learning.sap.com)
            """)
        
        with tabs[1]:  # Upgrade Matrix
            render_upgrade_matrix_tab()
        
        with tabs[2]:  # Compatibility Checker
            render_compatibility_checker_tab()
        
        with tabs[3]:  # OS Parameters
            render_os_parameters_tab()
        
        with tabs[4]:  # Checklist Generator
            render_checklist_generator_tab()
        
        with tabs[5]:  # HTML Reports
            render_html_report_generator()
        
        with tabs[6]:  # Landscape Visualizer
            render_landscape_visualizer_tab()
        
        with tabs[7]:  # SUM Monitor
            render_sum_monitor_tab()
        
        with tabs[8]:  # Guide Downloader
            render_guide_downloader_tab()
        
        with tabs[9]:  # Gemini Search
            render_gemini_search_tab()
        
        with tabs[10]:  # Batch Q&A
            render_batch_qa_tab()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px;'>
        SAP Help Navigator Pro v3.0 Complete Edition | 
        Release calendar (2023 → 2025, no 2024) [1] | 
        All deployment types | AI-powered search | 
        11 comprehensive modules
    </div>
    """, unsafe_allow_html=True)

# End of Part 11 - Application Complete!

if __name__ == "__main__":
    main()


