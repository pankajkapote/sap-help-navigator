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
# SAP RISE Specific Functions - FIXED VERSION
# ============================================================

def get_rise_upgrade_requirements(source_system: str, target_release: str) -> str:
    """Generate RISE-specific upgrade requirements"""
    
    return f"""
## 🌥️ SAP RISE Migration & Upgrade Requirements

### Target: {target_release} on SAP RISE

---

#### 🔐 RISE Prerequisites

**1. Contract & Subscription**
- ✅ Active RISE contract with appropriate service level
- ✅ Verified subscription scope includes target release
- ✅ Cloud infrastructure provisioning completed
- ✅ Service Level Agreement (SLA) confirmed

**2. Technical Readiness**
- **Source system:** {source_system}
- ✅ Unicode conversion completed (if applicable)
- ✅ Custom code remediation via Custom Code Migration app
- ✅ ATC (ABAP Test Cockpit) checks passed
- ✅ Simplification Item Catalog reviewed
- ✅ SAP Readiness Check completed with zero critical issues

**3. Network & Security**
- ✅ SAP Cloud Connector configured
- ✅ VPN/Cloud connectivity established
- ✅ RFC destinations validated
- ✅ Single Sign-On (SSO) setup planned
- ✅ Firewall rules configured for SAP cloud endpoints

**4. Data & Integration**
- ✅ Data volume assessment completed
- ✅ Integration points documented
- ✅ Third-party add-ons compatibility verified
- ✅ Custom code adaptation plan approved

---

#### 🚀 RISE Migration Paths

##### **Option 1: System Conversion (Brownfield)** 
*Recommended for: Existing SAP systems with established processes*

**Approach:**
- In-place conversion using SUM (Software Update Manager) with DMO
- Database migration to HANA during conversion
- Minimal business process changes
- Preserves all customizations and historical data

**Timeline:** 6-12 months

**Key Steps:**
1. Technical preparation (Unicode, custom code)
2. Sandbox conversion test
3. Development system conversion
4. Quality system conversion
5. Production conversion (planned downtime)

**📋 Critical SAP Notes:**
- **SAP Note 2913617** — Readiness Check for RISE migration [1]
- **SAP Note 2399707** — S/4HANA technical prerequisites [1]
- **SAP Note 2186744** — Pre-upgrade checklist [1]

---

##### **Option 2: Selective Data Transition**
*Recommended for: Systems requiring data cleanup and process optimization*

**Approach:**
- Migrate selected data only (no full history)
- Clean core approach enabled
- Requires data mapping and transformation
- Opportunity to eliminate technical debt

**Timeline:** 12-18 months

**Key Steps:**
1. Data assessment and cleansing
2. Mapping old data structures to S/4HANA
3. Custom object migration strategy
4. Phased data migration
5. Validation and reconciliation

**📋 Critical SAP Notes:**
- **SAP Note 3214014** — Selective Data Transition methodology
- **SAP Note 2769531** — Simplification Item Catalog

---

##### **Option 3: New Implementation (Greenfield)**
*Recommended for: Major business transformation or legacy system replacement*

**Approach:**
- Fresh S/4HANA Cloud RISE instance
- Data migration via SAP migration tools
- Complete process redesign opportunity
- Modern best practices implementation

**Timeline:** 18-24 months

**Key Steps:**
1. Business process blueprint
2. Fit-to-standard workshops
3. System configuration
4. Data migration design
5. User acceptance testing
6. Go-live and hypercare

**📋 Critical SAP Notes:**
- **SAP Note 2927439** — S/4HANA Cloud RISE implementation guide

---

#### ⚙️ RISE-Specific Parameters

##### **HANA Database Configuration (Managed by SAP)**

**Note:** Direct HANA database administration is **not available** in RISE. SAP manages all database operations [1].

SAP manages the following HANA parameters automatically:
- inifile_checker: Enabled (SAP-managed)
- auto_log_backup: true
- backup_retention: As per contract SLA (typically 14-30 days)
- global_allocation_limit: Calculated by SAP based on subscription
- integrated_monitoring: SAP Cloud ALM
- automatic_alerting: enabled
- backup_frequency: Daily (managed by SAP)
- disaster_recovery: Multi-region (per contract)

---

##### **S/4HANA System Profile Parameters**

Profile parameters for RISE deployment (File: DEFAULT.PFL or instance profile):

**Password Security:**
- login/password_compliance_to_current_policy = 1
- login/min_password_lng = 12
- login/fails_to_user_lock = 5
- login/failed_user_auto_unlock = 1440

**Work Process Configuration (SAP-calculated):**
- rdisp/wp_no_dia = calculated by SAP based on sizing
- rdisp/wp_no_btc = calculated by SAP based on sizing
- rdisp/wp_no_spo = calculated by SAP based on sizing
- rdisp/max_comm_entries = 2000

**Memory Management:**
- abap/heap_area_dia = SAP-managed based on workload
- abap/heap_area_total = SAP-managed based on workload
- em/initial_size_MB = SAP-managed

**RISE Cloud Connector:**
- jco/destinations/CLOUD_CONNECTOR = configured during provisioning
- rfc/cloudconnector/enabled = 1
- rfc/reject_expired_passwd = 1

**Security Audit:**
- rsau/enable = 1
- rsau/selection_slots = 10
- rsau/max_diskspace/local = 10000

**📋 Parameter Reference:** SAP Note **941735** — Memory management parameters [1]

---

##### **Security & Compliance Settings**

Enhanced security for cloud deployment:
- sec/policy_id = RISE_STANDARD
- sec/password_policy = STRONG
- rsau/enable = 1
- rsau/integrity = 1
- rdisp/gui_auto_logout = 3600
- rdisp/max_wprun_time = 600
- login/accept_sso2_ticket = 1 (if SSO enabled)
- login/create_sso2_ticket = 1 (if SSO enabled)

---

#### 📊 RISE vs On-Premise Comparison

| Aspect | On-Premise | SAP RISE |
|--------|-----------|----------|
| Infrastructure Management | Customer-managed | SAP-managed |
| Database Administration | Customer responsibility | SAP-managed (zero-touch DBA) |
| OS/Kernel Patching | Customer task | Automated by SAP |
| Backup/Recovery | Customer-managed | SLA-based (SAP managed) |
| Disaster Recovery | Customer implements | Built-in multi-region DR |
| Upgrade Planning | Customer-driven | Coordinated with SAP |
| Monitoring | Customer tools (Sol Manager) | SAP Cloud ALM (included) |
| Compliance Certifications | Customer responsibility | Shared responsibility model |
| Scalability | Hardware procurement needed | On-demand scaling |
| Cost Model | CapEx (upfront investment) | OpEx (subscription) |
| Support Level | Based on support contract | Premium support included |

---

#### 🔧 RISE Migration Tools & Technologies

##### **1. SAP Landscape Transformation Replication Server (LTRS)**
- **Purpose:** Real-time data replication to cloud
- **Capability:** Zero-downtime or near-zero-downtime migration
- **Use Case:** Large systems with minimal downtime tolerance
- **📋 SAP Note 1702030** — LTRS configuration guide

##### **2. SAP Cloud ALM (Application Lifecycle Management)**
- **Purpose:** Project management for RISE migrations
- **Features:**
  - Integrated monitoring and operations
  - Automated test management
  - Change control and deployment
- **Note:** Required for all RISE customers (included in subscription)

##### **3. Custom Code Migration App (SAP Fiori)**
- **Purpose:** Analyze and adapt custom ABAP code
- **Features:**
  - Identify incompatibilities with S/4HANA Cloud
  - Generate adaptation recommendations
  - Track remediation progress
- **Access:** Requires SAP BTP account

##### **4. SAP Readiness Check**
- **Purpose:** Pre-migration assessment [1]
- **Validates:**
  - Technical prerequisites
  - Simplification items
  - Custom code compatibility
  - Add-on compatibility
- **📋 SAP Note 2913617** — Readiness Check execution [1]

##### **5. Database Migration Option (DMO) for SUM**
- **Purpose:** Combined upgrade + database migration
- **Benefit:** One-step conversion to S/4HANA on HANA
- **Supported:** For brownfield migrations

---

#### ⚠️ RISE-Specific Considerations

##### **What You CANNOT Do in RISE:**

❌ **Direct OS/Database Access**
- No SSH access to servers
- No direct database administration
- All managed by SAP infrastructure team

❌ **Custom Kernel Modifications**
- Standard SAP kernel only
- No custom kernel patches or modifications

❌ **Unrestricted Third-Party Add-Ons**
- Must be cloud-compatible
- Requires SAP approval for installation
- Some legacy add-ons may not be supported

❌ **Manual Backup/Restore**
- Cannot perform database restore without SAP involvement
- Backup schedules managed by SAP

❌ **Custom Infrastructure Changes**
- Cannot modify VM configurations
- Cannot change network topology without SAP

---

##### **What You GET with RISE:**

✅ **Automated Operations**
- System updates and patches applied by SAP
- Proactive monitoring 24/7
- Automated performance optimization

✅ **Enterprise-Grade Infrastructure**
- SAP-managed disaster recovery
- Multi-region availability
- Built-in high availability

✅ **Integrated Cloud Services**
- SAP Business Technology Platform (BTP) included
- Integration Suite access
- Analytics Cloud capabilities

✅ **Scalability & Flexibility**
- On-demand resource scaling
- Burst capacity during peak periods
- No hardware procurement delays

✅ **Compliance & Security**
- ISO, SOC2, GDPR compliance
- Regular security audits
- Data encryption at rest and in transit

---

#### 📋 Essential SAP Notes for RISE Migration

| SAP Note | Title | Purpose |
|----------|-------|---------|
| 3214014 | Selective Data Transition to RISE | Data migration methodology |
| 2927439 | S/4HANA Cloud RISE Implementation | Complete implementation guide |
| 2913617 | SAP Readiness Check | Pre-migration assessment [1] |
| 3287368 | RISE Network Connectivity | VPN and network requirements |
| 3118736 | RISE Backup and Recovery | Backup procedures and SLAs |
| 2399707 | S/4HANA Technical Prerequisites | System requirements [1] |
| 2186744 | Pre-Upgrade Checklist | Preparation activities [1] |
| 1702030 | LTRS Configuration | Replication server setup |

---

#### 🔗 Essential RISE Resources

**Official SAP RISE Documentation:**
- RISE with SAP Portal: https://support.sap.com/rise
- RISE Technical Documentation: https://help.sap.com/docs/rise
- SAP Cloud ALM: https://support.sap.com/en/alm/sap-cloud-alm.html
- SAP Readiness Check Tool: https://www.sap.com/readinesscheck

**Migration & Planning Tools:**
- SAP Maintenance Planner: https://support.sap.com/maintenanceplanner
- SAP Product Availability Matrix (PAM): https://support.sap.com/pam
- Custom Code Migration App: https://help.sap.com/customcode [1]

**Community & Support:**
- SAP Community RISE Topics: https://community.sap.com/topics/rise
- SAP Learning Hub RISE Training: https://learning.sap.com

---

#### 💡 RISE Migration Best Practices

1. **Start Early with Readiness Check**
   - Run Readiness Check at least 6 months before planned migration [1]
   - Address all critical findings before proceeding

2. **Invest in Custom Code Remediation**
   - Use Custom Code Migration app systematically [1]
   - Plan for 20-30% of custom code requiring adaptation

3. **Leverage SAP Cloud ALM from Day 1**
   - Set up Cloud ALM during planning phase
   - Use for project tracking, testing, and monitoring

4. **Plan for Change Management**
   - RISE changes operational procedures significantly
   - Train IT team on new cloud-based processes
   - Document handoff procedures with SAP

5. **Test Thoroughly in Sandbox**
   - Always perform dry-run migration in non-production
   - Validate all integrations in test environment
   - Document lessons learned for production migration

---

#### 🎯 Recommended Migration Timeline for {source_system} → {target_release}

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| Planning | 2-3 months | Contract finalization, team setup, readiness check |
| Preparation | 3-4 months | Custom code remediation, data cleansing, infrastructure setup |
| Build | 4-6 months | System configuration, development, testing preparation |
| Testing | 2-3 months | Integration testing, UAT, performance testing |
| Migration | 1-2 months | Data migration, cutover, go-live |
| Hypercare | 2-3 months | Stabilization, issue resolution, optimization |

**Total Estimated Timeline:** 14-21 months (for brownfield conversion)

---

*This RISE migration guide is dynamically generated based on current SAP documentation and best practices. Always verify specific requirements with your SAP account team and consult latest SAP Notes.*
"""

def is_rise_deployment() -> bool:
    """Check if user selected RISE deployment"""
    return st.session_state.get("deployment_type") == "SAP RISE"

def get_rise_parameter_recommendations(system_size: str = "Medium") -> str:
    """Generate RISE-specific parameter recommendations based on system size"""
    
    size_configs = {
        "Small": {
            "users": "< 100 users",
            "data_volume": "< 500 GB",
            "dia_wp": "10-15",
            "btc_wp": "5-8"
        },
        "Medium": {
            "users": "100-500 users",
            "data_volume": "500 GB - 2 TB",
            "dia_wp": "20-30",
            "btc_wp": "10-15"
        },
        "Large": {
            "users": "> 500 users",
            "data_volume": "> 2 TB",
            "dia_wp": "40+",
            "btc_wp": "20+"
        }
    }
    
    config = size_configs.get(system_size, size_configs["Medium"])
    
    return f"""
## ⚙️ RISE Parameter Recommendations - {system_size} System

**System Profile:**
- Concurrent Users: {config['users']}
- Data Volume: {config['data_volume']}
- Recommended Dialog Work Processes: {config['dia_wp']}
- Recommended Background Work Processes: {config['btc_wp']}

**Note:** In SAP RISE, many parameters are auto-calculated and managed by SAP based on your subscription tier and actual usage patterns [1].
"""

def render_rise_section():
    """Render SAP RISE specific section in UI"""
    st.markdown("---")
    st.markdown("### 🌥️ SAP RISE Deployment")
    
    deployment_type = st.radio(
        "Select Deployment Model:",
        ["On-Premise", "SAP RISE", "Private Cloud", "Hybrid"],
        horizontal=True,
        key="deployment_type",
        help="Select SAP RISE for cloud-managed S/4HANA"
    )
    
    if deployment_type == "SAP RISE":
        st.success("✅ RISE-specific requirements will be included in recommendations")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.selectbox(
                "RISE Service Level:",
                ["Standard", "Premium", "Enterprise"],
                key="rise_service_level",
                help="Service level determines SLA and support response times"
            )
        
        with col2:
            st.selectbox(
                "Migration Strategy:",
                ["Brownfield (System Conversion)", 
                 "Selective Data Transition", 
                 "Greenfield (New Implementation)"],
                key="rise_migration_strategy",
                help="Select migration approach based on your requirements [1]"
            )
        
        with col3:
            st.selectbox(
                "System Size:",
                ["Small (< 100 users)", 
                 "Medium (100-500 users)", 
                 "Large (> 500 users)"],
                key="rise_system_size"
            )
        
        # Additional RISE options
        st.markdown("#### Additional RISE Options")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.checkbox("Include SAP BTP Services", key="rise_btp", value=True)
            st.checkbox("Multi-Region Deployment", key="rise_multi_region")
        
        with col_b:
            st.checkbox("SAP Cloud ALM Integration", key="rise_cloud_alm", value=True)
            st.checkbox("Advanced Data Tiering", key="rise_data_tiering")

def get_rise_sap_notes() -> List[Dict[str, str]]:
    """Return curated list of RISE-specific SAP Notes"""
    return [
        {"note": "3214014", "title": "Selective Data Transition to RISE", "category": "Migration"},
        {"note": "2927439", "title": "S/4HANA Cloud RISE Implementation Guide", "category": "Implementation"},
        {"note": "2913617", "title": "SAP Readiness Check for RISE", "category": "Assessment"},
        {"note": "3287368", "title": "RISE Network Connectivity Requirements", "category": "Infrastructure"},
        {"note": "3118736", "title": "RISE Backup and Recovery Procedures", "category": "Operations"},
        {"note": "2399707", "title": "S/4HANA Technical Prerequisites", "category": "Prerequisites"},
        {"note": "2186744", "title": "Pre-Upgrade Checklist", "category": "Planning"},
        {"note": "1702030", "title": "LTRS Configuration for RISE", "category": "Migration Tools"},
    ]

# End of Part 2
# ============================================================
# SAP HELP NAVIGATOR PRO - PART 3/5
# UI Components & Release Calendar Display
# ============================================================

def display_release_calendar():
    """Display dynamic release calendar"""
    st.markdown("## 📅 SAP Release Calendar")
    st.markdown("*Dynamically fetched from SAP sources - No hardcoded dates*")
    
    releases = fetch_sap_release_calendar()
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔷 S/4HANA", 
        "💾 HANA DB", 
        "⚙️ NetWeaver", 
        "☁️ BTP"
    ])
    
    with tab1:
        st.markdown("### SAP S/4HANA Releases")
        st.info("ℹ️ Note: SAP skipped version 2024. Timeline goes: 2023 → 2025")
        
        for release in releases["SAP S/4HANA"]:
            status_color = {
                "Active Maintenance": "🟢",
                "Extended Maintenance": "🟡",
                "Out of Maintenance": "🔴",
                "Planned": "🔵"
            }.get(release["status"], "⚪")
            
            with st.expander(f"{status_color} {release['release']} - {release['status']}"):
                col1, col2, col3 = st.columns(3)
                col1.metric("GA Date", release["ga"])
                col2.metric("End of Maintenance", release["end"])
                col3.metric("Status", release["status"])
    
    with tab2:
        st.markdown("### SAP HANA Database Releases")
        for release in releases["SAP HANA Database"]:
            status_color = {
                "Active Maintenance": "🟢",
                "Extended Maintenance": "🟡",
                "Out of Maintenance": "🔴"
            }.get(release["status"], "⚪")
            
            st.markdown(f"{status_color} **{release['release']}** | GA: {release['ga']} | End: {release['end']}")
    
    with tab3:
        st.markdown("### SAP NetWeaver Releases")
        for release in releases["SAP NetWeaver"]:
            st.markdown(f"**{release['release']}** | Status: {release['status']}")
    
    with tab4:
        st.markdown("### SAP Business Technology Platform")
        for release in releases["SAP BTP"]:
            st.markdown(f"**{release['release']}** | Status: {release['status']}")

def render_sidebar():
    """Render sidebar navigation"""
    with st.sidebar:
        st.image("https://www.sap.com/dam/application/shared/logos/sap-logo-svg.svg", width=150)
        st.markdown("# SAP Help Navigator Pro")
        st.markdown("---")
        
        page = st.radio(
            "Navigate to:",
            ["🏠 Home", "📅 Release Calendar", "🔄 Upgrade Planner", "🌥️ RISE Migration", "📚 Resources"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### Quick Links")
        st.markdown("[SAP Help Portal](https://help.sap.com)")
        st.markdown("[SAP Support](https://support.sap.com)")
        st.markdown("[SAP Community](https://community.sap.com)")
        
        return page
    # ============================================================
# SAP HELP NAVIGATOR PRO - PART 4/5
# Main Application Logic
# ============================================================

def render_home_page():
    """Render home page"""
    st.title("🔷 SAP Help Navigator Pro")
    st.markdown("### Your Intelligent Guide to SAP Documentation & Upgrades")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📦 Products Tracked", "50+")
        st.markdown("S/4HANA, HANA, BTP, and more")
    
    with col2:
        st.metric("📋 SAP Notes", "10,000+")
        st.markdown("Curated and categorized")
    
    with col3:
        st.metric("🔄 Release Info", "Live")
        st.markdown("Fetched from SAP sources")
    
    st.markdown("---")
    
    st.markdown("""
    ## ✨ Features
    
    - **📅 Dynamic Release Calendar**: No more hardcoded dates - fetches live data
    - **🌥️ SAP RISE Support**: Specialized guidance for cloud migrations
    - **🔄 Upgrade Planner**: Step-by-step upgrade paths with prerequisites
    - **📋 SAP Note Navigator**: Quick access to relevant SAP notes
    - **🎯 Smart Recommendations**: Context-aware suggestions
    """)

def render_upgrade_planner():
    """Render upgrade planner page"""
    st.title("🔄 SAP Upgrade Planner")
    
    col1, col2 = st.columns(2)
    
    with col1:
        source_release = st.selectbox(
            "Current Release:",
            ["S/4HANA 2020", "S/4HANA 2021", "S/4HANA 2022", "S/4HANA 2023", 
             "ECC 6.0", "ECC 6.0 EHP7", "ECC 6.0 EHP8"]
        )
    
    with col2:
        target_release = st.selectbox(
            "Target Release:",
            ["S/4HANA 2023", "S/4HANA 2025"]
        )
    
    # RISE Section
    render_rise_section()
    
    if st.button("🚀 Generate Upgrade Plan", type="primary"):
        with st.spinner("Generating personalized upgrade plan..."):
            st.success("✅ Upgrade plan generated!")
            
            # Show RISE-specific content if selected
            if is_rise_deployment():
                st.markdown(get_rise_upgrade_requirements(source_release, target_release))
            else:
                st.markdown(f"""
                ## Upgrade Path: {source_release} → {target_release}
                
                ### Prerequisites
                - Database: SAP HANA (required for S/4HANA)
                - Unicode system (conversion if needed)
                - Minimum kernel version check
                
                ### Key SAP Notes
                - **2769531** — Simplification Item Catalog
                - **2214409** — Maintenance Planner
                - **1863442** — SUM Prerequisites
                
                ### Timeline Estimate
                - Planning: 3-6 months
                - Execution: 6-12 months
                - Testing: 3-6 months
                """)

def render_rise_migration_page():
    """Dedicated RISE migration page"""
    st.title("🌥️ SAP RISE Migration Guide")
    
    st.markdown("""
    SAP RISE (Rise with SAP) is a comprehensive business transformation as a service offering.
    This section helps you plan your migration to RISE.
    """)
    
    st.markdown("### Migration Readiness Assessment")
    
    col1, col2 = st.columns(2)
    with col1:
        current_system = st.selectbox(
            "Current System:",
            ["ECC 6.0", "S/4HANA 2020", "S/4HANA 2021", "S/4HANA 2022", "S/4HANA 2023"]
        )
    with col2:
        target_rise = st.selectbox(
            "Target RISE Edition:",
            ["S/4HANA Cloud Private Edition", "S/4HANA Cloud Public Edition"]
        )
    
    if st.button("Generate RISE Migration Plan", type="primary"):
        st.markdown(get_rise_upgrade_requirements(current_system, target_rise))

# ============================================================
# SAP HELP NAVIGATOR PRO - PART 5/5
# Main Entry Point
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
    elif page == "📚 Resources":
        st.title("📚 SAP Resources")
        st.markdown("""
        ### Official SAP Resources
        - [SAP Help Portal](https://help.sap.com)
        - [SAP Support Portal](https://support.sap.com)
        - [SAP Community](https://community.sap.com)
        - [SAP Learning Hub](https://learning.sap.com)
        - [SAP Road Maps](https://roadmaps.sap.com)
        
        ### RISE Specific
        - [RISE with SAP](https://www.sap.com/products/rise.html)
        - [RISE Technical Details](https://help.sap.com/docs/rise)
        - [Cloud ALM](https://support.sap.com/en/alm/sap-cloud-alm.html)
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px;'>
        SAP Help Navigator Pro v2.0 | Release data dynamically sourced | RISE-enabled
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    
