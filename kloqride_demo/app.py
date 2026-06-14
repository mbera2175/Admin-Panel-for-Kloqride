import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import math
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

# ── Backend API ───────────────────────────────────────────────────────────────
API_BASE              = os.getenv("API_BASE", "http://13.232.171.208:8000")
ADMIN_EMAIL_API       = os.getenv("ADMIN_EMAIL_API", "")
ADMIN_PASSWORD_API    = os.getenv("ADMIN_PASSWORD_API", "")

def get_admin_token():
    try:
        res = requests.post(
            f"{API_BASE}/auth/admin/login",
            json={"email": ADMIN_EMAIL_API, "password": ADMIN_PASSWORD_API},
            timeout=10)
        if res.status_code == 200:
            return res.json().get("token", "")
    except Exception:
        return ""
    return ""

if "admin_token" not in st.session_state or not st.session_state.admin_token:
    st.session_state.admin_token = get_admin_token()

def _auth_headers():
    token = st.session_state.get("admin_token", "")
    return {"Authorization": f"Bearer {token}"}

def api_get(endpoint, params=None):
    try:
        res = requests.get(f"{API_BASE}{endpoint}", params=params,
                           headers=_auth_headers(), timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def api_post(endpoint, data=None):
    try:
        res = requests.post(f"{API_BASE}{endpoint}", json=data,
                            headers=_auth_headers(), timeout=10)
        return res.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def api_patch(endpoint, data=None):
    try:
        res = requests.patch(f"{API_BASE}{endpoint}", json=data,
                             headers=_auth_headers(), timeout=10)
        return res.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def api_delete(endpoint):
    try:
        res = requests.delete(f"{API_BASE}{endpoint}",
                              headers=_auth_headers(), timeout=10)
        return res.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# ── Data dir ──────────────────────────────────────────────────────────────────
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(exist_ok=True)

def load_data(filename):
    try:
        fp = DATA_DIR / filename
        if fp.exists():
            with open(fp, "r") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading data: {e}")
    return None

def save_data(filename, data):
    try:
        with open(DATA_DIR / filename, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KRide | Admin Dashboard",
    page_icon="🚖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
footer {visibility: hidden;}
.metric-card {
    background: white; border-radius: 12px; padding: 18px 20px;
    border-left: 4px solid #FF6B00;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 8px;
}
.metric-card.green  { border-left-color: #34A853; }
.metric-card.amber  { border-left-color: #FBBC04; }
.metric-card.red    { border-left-color: #EA4335; }
.metric-card.purple { border-left-color: #7F77DD; }
.m-label { font-size: 11px; color: #888; font-weight: 500;
           text-transform: uppercase; letter-spacing: 0.5px; }
.m-value { font-size: 1.7rem; font-weight: 700; color: #111; margin: 2px 0; }
.m-delta { font-size: 12px; }
.up   { color: #34A853; }
.down { color: #EA4335; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 20px;
         font-size: 12px; font-weight: 600; }
.b-active  { background:#E6F4EA; color:#137333; }
.b-idle    { background:#FEF3CD; color:#856404; }
.b-offline { background:#FCE8E6; color:#9A0000; }
.alert { background:#FEF3CD; border-left:4px solid #FBBC04;
         padding:10px 14px; border-radius:0 8px 8px 0;
         font-size:13px; color:#5c4200; margin-bottom:16px; }
button[kind="primary"], button[data-testid="baseButton-primary"] {
    background-color: #E85F00 !important; color: white !important;
    border-color: #E85F00 !important; }
button[kind="primary"]:hover { background-color: #CC4E00 !important; }
section[data-testid="stSidebar"] { background-color: #F2F2F2; }
section[data-testid="stSidebar"] button {
    background-color: #F2F2F2; color: #111; border-radius: 8px; }
section[data-testid="stSidebar"] div.stButton {
    margin-top: -8px !important; margin-bottom: -4px !important; }
section[data-testid="stSidebar"] button:hover { background-color: #E8E8E8; }
section[data-testid="stSidebar"] button[kind="primary"] {
    background-color: #FF6B00 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ── Credentials ───────────────────────────────────────────────────────────────
USERS = {
    os.getenv("ADMIN_EMAIL", "admin@kride.com"): {
        "password": os.getenv("ADMIN_PASSWORD", "admin123"),
        "name": "Admin", "role": "Admin"
    },
    os.getenv("OPS_EMAIL", "ops@kride.com"): {
        "password": os.getenv("OPS_PASSWORD", "ops123"),
        "name": "Ops Manager", "role": "Operations"
    },
}
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))

# ── Colors ────────────────────────────────────────────────────────────────────
BLUE = "#FF6B00"; GREEN = "#34A853"; AMBER = "#FBBC04"; RED = "#EA4335"; PURPLE = "#7F77DD"

def metric(label, value, delta="", color="blue"):
    cls = {"blue": "", "green": "green", "amber": "amber", "red": "red", "purple": "purple"}[color]
    d_html = (f'<div class="m-delta {"up" if "+" in str(delta) or "▲" in str(delta) else "down"}">{delta}</div>'
              if delta else '<div class="m-delta">&nbsp;</div>')
    return f"""<div class="metric-card {cls}">
        <div class="m-label">{label}</div>
        <div class="m-value">{value}</div>
        {d_html}</div>"""

def page_title(title, subtitle=""):
    sub = f"<div style='font-size:13px;color:rgba(255,255,255,0.9);margin-top:6px;'>{subtitle}</div>" if subtitle else ""
    st.markdown(f"""
    <div style='background:#E85F00;border-radius:10px;padding:18px 22px;margin-bottom:16px;
                box-shadow:0 4px 6px rgba(0,0,0,0.1);'>
        <div style='font-size:1.6rem;font-weight:800;color:#fff;'>{title}</div>
        {sub}
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def show_login():
    c1, c2, c3 = st.columns([1, 1.3, 1])
    with c2:
        st.markdown("""
        <div style='text-align:center;margin-top:50px;margin-bottom:24px;'>
          <div style='font-size:3rem;font-weight:900;color:#FF6B00;'>🚖 KRide</div>
          <div style='color:#888;font-size:0.95rem;margin-top:4px;'>Admin Dashboard</div>
        </div>""", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("#### Sign in")
            email    = st.text_input("Email", placeholder="admin@kride.com")
            password = st.text_input("Password", type="password")
            ok = st.form_submit_button("Login →", use_container_width=True, type="primary")
            if ok:
                if email in USERS and USERS[email]["password"] == password:
                    st.session_state.logged_in  = True
                    st.session_state.user        = USERS[email]
                    st.session_state.user_email  = email
                    st.session_state.login_time  = datetime.now()
                    st.query_params["u"]          = email
                    st.success(f"Welcome, {USERS[email]['name']}!")
                    st.rerun()
                else:
                    st.error("❌ Wrong email or password.")

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
def show_sidebar():
    user = st.session_state.user
    st.sidebar.markdown(f"""
    <div style='padding:10px 0 16px;'>
      <div style='font-size:1.4rem;font-weight:900;color:#FF6B00;'>🚖 KRide</div>
      <div style='margin-top:12px;padding:10px 12px;background:#FFF0E6;border-radius:8px;'>
        <div style='font-size:13px;font-weight:600;'>{user['name']}</div>
        <div style='font-size:11px;color:#888;'>{user['role']}</div>
      </div>
    </div>""", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "Overview"

    pages = [
        "Overview", "Live Search Feed", "Search Heatmap", "Live Map",
        "Trip Tracking", "Ride History", "Send Notification", "Schedule Notification",
        "Broadcast History", "Activate Promo", "Driver Online Log", "Rider Onboarding",
        "Driver Document Upload", "Driver Performance", "Driver Payments",
        "Vehicle Management", "Promotions", "Revenue Reports",
        "Notifications", "Pricing & Fees", "Block Management",
        "Cancellation Config", "Wallet Management", "Withdrawal Requests",
        "Trip Disputes", "SOS Alerts", "Cash Collection", "Referral Config",
        "Delete User", "EV Stats", "Reviews", "Commission Report", "Cancellation Reasons"
    ]

    for p in pages:
        btn_type = "primary" if st.session_state.nav_page == p else "secondary"
        if st.sidebar.button(p, type=btn_type, use_container_width=True, key=f"nav_{p}"):
            st.session_state.nav_page = p
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div style='font-size:11px;color:#aaa;text-align:center;'>
        KRide Admin · {datetime.now().strftime("%d %b %Y %H:%M")}
    </div>""", unsafe_allow_html=True)

    if st.sidebar.button("Logout", use_container_width=True, key="logout_btn"):
        for k in ["logged_in", "user", "user_email", "login_time", "admin_token"]:
            st.session_state[k] = None if k != "logged_in" else False
        st.query_params.clear()
        st.rerun()

    return st.session_state.nav_page

# ══════════════════════════════════════════════════════════════════════════════
#  OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
def page_overview():
    page_title("📊 Overview", f"{datetime.now().strftime('%A, %d %B %Y')} · KRide Operations")

    data = api_get("/admin/overview")
    if not data:
        st.error("❌ Could not connect to backend.")
        return

    users   = data.get("users",   {})
    trips   = data.get("trips",   {})
    revenue = data.get("revenue", {})

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric("Total Riders",     str(users.get("riders", 0)),          "", "blue"),   unsafe_allow_html=True)
    with c2: st.markdown(metric("Total Drivers",    str(users.get("drivers", 0)),         "", "green"),  unsafe_allow_html=True)
    with c3: st.markdown(metric("Active Drivers",   str(users.get("active_drivers", 0)),  "", "amber"),  unsafe_allow_html=True)
    with c4: st.markdown(metric("Pending Approval", str(users.get("pending_approval", 0)),"", "red"),    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric("Total Trips",   str(trips.get("total", 0)),     "", "blue"),   unsafe_allow_html=True)
    with c2: st.markdown(metric("Completed",     str(trips.get("completed", 0)), "", "green"),  unsafe_allow_html=True)
    with c3: st.markdown(metric("Active Now",    str(trips.get("active", 0)),    "", "amber"),  unsafe_allow_html=True)
    with c4: st.markdown(metric("Cancelled",     str(trips.get("cancelled", 0)), "", "red"),    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric("Today's Trips",    str(trips.get("today", 0)),                    "", "blue"),   unsafe_allow_html=True)
    with c2: st.markdown(metric("Today's Revenue",  f"₹{revenue.get('today', 0):,.2f}",            "", "green"),  unsafe_allow_html=True)
    with c3: st.markdown(metric("Total Revenue",    f"₹{revenue.get('total', 0):,.2f}",            "", "green"),  unsafe_allow_html=True)
    with c4: st.markdown(metric("Total Commission", f"₹{revenue.get('total_commission', 0):,.2f}", "", "purple"), unsafe_allow_html=True)

    st.markdown("---")

    # Block status overview
    c1, c2 = st.columns(2)
    with c1: st.markdown(metric("Blocked Riders",  str(users.get("blocked_riders", 0)),  "", "red"),  unsafe_allow_html=True)
    with c2: st.markdown(metric("Blocked Drivers", str(users.get("blocked_drivers", 0)), "", "red"),  unsafe_allow_html=True)

    st.markdown("---")

    rev_data = api_get("/admin/revenue", params={"days": 30})
    if rev_data and rev_data.get("daily_breakdown"):
        daily = pd.DataFrame(rev_data["daily_breakdown"])
        col1, col2 = st.columns(2)
        with col1:
            fig = px.line(daily, x="date", y="revenue", title="Daily Revenue — Last 30 Days",
                          markers=True, color_discrete_sequence=[BLUE])
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(l=10,r=10,t=40,b=10))
            fig.update_traces(line_width=2.5)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(daily, x="date", y=["trips", "commission"],
                         title="Daily Trips & Commission",
                         color_discrete_map={"trips": GREEN, "commission": PURPLE},
                         barmode="group")
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  BLOCK MANAGEMENT — NEW PAGE (separate rider vs driver blocking)
# ══════════════════════════════════════════════════════════════════════════════
def page_block_management():
    page_title("🔒 Block Management",
               "Block riders and drivers independently — blocking a driver does NOT block them as a rider")

    tab1, tab2 = st.tabs(["🏍️ Block Riders", "🚗 Block Drivers"])

    # ── TAB 1: Block Riders ───────────────────────────────────────────────────
    with tab1:
        st.subheader("Rider Accounts")
        st.markdown("""
        <div class="alert">
            ℹ️ Blocking a rider only prevents them from <b>booking rides</b>.
            If they are also a driver (same phone), their driver account is NOT affected.
        </div>""", unsafe_allow_html=True)

        users_data = api_get("/admin/users", params={"limit": 200})
        if not users_data:
            st.error("❌ Could not load users.")
            return

        users = users_data.get("users", [])
        # Show users who have rider accounts
        rider_users = [u for u in users if u.get("has_rider_account")]

        search = st.text_input("🔍 Search by name or phone", key="bm_rider_search")
        if search:
            rider_users = [u for u in rider_users if
                           search.lower() in u["full_name"].lower() or
                           search in str(u.get("phone", ""))]

        st.caption(f"Showing {len(rider_users)} riders")

        for u in rider_users:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                blocked = u.get("rider_blocked", False)
                status = "🔴 Blocked as Rider" if blocked else "🟢 Active as Rider"
                st.markdown(f"""
                <div style='padding:8px 0;'>
                  <b>{u['full_name']}</b>
                  <span style='color:#888;font-size:12px;margin-left:8px;'>{u.get('phone','')}</span>
                  <span style='margin-left:12px;font-size:12px;'>{status}</span>
                </div>""", unsafe_allow_html=True)
            with col2:
                # Get rider_id from backend
                rider_data = api_get(f"/admin/users") or {}
                rider_id = u.get("id")
                if st.button("🔴 Block", key=f"blk_rider_{u['id']}", use_container_width=True):
                    result = api_patch(f"/admin/riders/{rider_id}/block")
                    if result:
                        st.success(f"✅ {u['full_name']} blocked as rider!")
                        st.rerun()
                    else:
                        st.error("Failed.")
            with col3:
                if st.button("🟢 Unblock", key=f"ublk_rider_{u['id']}", use_container_width=True):
                    result = api_patch(f"/admin/riders/{rider_id}/block")
                    if result:
                        st.success(f"✅ {u['full_name']} unblocked as rider!")
                        st.rerun()
                    else:
                        st.error("Failed.")

    # ── TAB 2: Block Drivers ──────────────────────────────────────────────────
    with tab2:
        st.subheader("Driver Accounts")
        st.markdown("""
        <div class="alert">
            ℹ️ Blocking a driver only prevents them from <b>accepting rides</b>.
            If they are also a rider (same phone), their rider account is NOT affected.
        </div>""", unsafe_allow_html=True)

        drv_data = api_get("/admin/drivers", params={"limit": 200})
        if not drv_data:
            st.error("❌ Could not load drivers.")
            return

        drivers = drv_data.get("drivers", [])

        search2 = st.text_input("🔍 Search by name or phone", key="bm_driver_search")
        if search2:
            drivers = [d for d in drivers if
                       search2.lower() in d["full_name"].lower() or
                       search2 in str(d.get("phone", ""))]

        st.caption(f"Showing {len(drivers)} drivers")

        for d in drivers:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                blocked = d.get("is_blocked", False)
                status  = "🔴 Blocked as Driver" if blocked else "🟢 Active as Driver"
                st.markdown(f"""
                <div style='padding:8px 0;'>
                  <b>{d['full_name']}</b>
                  <span style='color:#888;font-size:12px;margin-left:8px;'>{d.get('phone','')}</span>
                  <span style='margin-left:12px;font-size:12px;'>{status}</span>
                </div>""", unsafe_allow_html=True)
            with col2:
                if st.button("🔴 Block", key=f"blk_drv_{d['id']}", use_container_width=True):
                    result = api_patch(f"/admin/drivers/{d['id']}/block")
                    if result:
                        st.success(f"✅ {d['full_name']} blocked as driver!")
                        st.rerun()
                    else:
                        st.error("Failed.")
            with col3:
                if st.button("🟢 Unblock", key=f"ublk_drv_{d['id']}", use_container_width=True):
                    result = api_patch(f"/admin/drivers/{d['id']}/block")
                    if result:
                        st.success(f"✅ {d['full_name']} unblocked as driver!")
                        st.rerun()
                    else:
                        st.error("Failed.")

# ══════════════════════════════════════════════════════════════════════════════
#  LIVE SEARCH FEED — now uses real trip data from backend
# ══════════════════════════════════════════════════════════════════════════════
def page_live_search_feed():
    page_title("🔴 Live Search Feed", "Real-time ride requests from backend")

    if st.button("🔄 Refresh"):
        st.rerun()

    # Fetch real active + recent trips
    trip_data = api_get("/admin/trips", params={"limit": 100})
    if not trip_data:
        st.error("❌ Could not load trip data.")
        return

    trips = trip_data.get("trips", [])
    if not trips:
        st.info("No trips found yet.")
        return

    # KPIs
    total     = len(trips)
    matched   = sum(1 for t in trips if t["status"] in ["accepted","arrived","started","completed"])
    searching = sum(1 for t in trips if t["status"] == "requested")
    no_driver = sum(1 for t in trips if t["status"] == "cancelled" and
                    (t.get("cancel_reason","") or "").lower().startswith("no driver"))
    cancelled = sum(1 for t in trips if t["status"] == "cancelled")
    match_rate = (matched / total * 100) if total > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.markdown(metric("Total",      str(total)),                          unsafe_allow_html=True)
    with c2: st.markdown(metric("Matched",    str(matched),   f"{match_rate:.0f}%","green"), unsafe_allow_html=True)
    with c3: st.markdown(metric("Searching",  str(searching), "","amber"),           unsafe_allow_html=True)
    with c4: st.markdown(metric("Cancelled",  str(cancelled), "","red"),             unsafe_allow_html=True)
    with c5: st.markdown(metric("Completed",  str(sum(1 for t in trips if t["status"]=="completed")), "","blue"), unsafe_allow_html=True)

    st.markdown("---")

    status_icon  = {"requested":"🔍","accepted":"✅","arrived":"📍","started":"🛣️","completed":"✅","cancelled":"❌"}
    status_bg    = {"requested":"#FEF3CD","accepted":"#E6F4EA","arrived":"#E6F4EA",
                    "started":"#E6F4EA","completed":"#E6F4EA","cancelled":"#FCE8E6"}
    status_color = {"requested":"#856404","accepted":"#137333","arrived":"#137333",
                    "started":"#137333","completed":"#137333","cancelled":"#9A0000"}
    vtype_icon   = {"bike":"🏍️","auto":"🛺","toto":"🛺","mini":"🚗","sedan":"🚗",
                    "suv":"🚙","cab_ac":"🚖","cab_non_ac":"🚕","ambulance":"🚑"}

    # Filters
    f1, f2, f3 = st.columns(3)
    s_f = f1.selectbox("Status", ["All","requested","accepted","started","completed","cancelled"], key="lsf_s")
    v_f = f2.selectbox("Vehicle", ["All","bike","auto","toto","mini","sedan","suv","cab_ac","cab_non_ac"], key="lsf_v")
    ph_f= f3.text_input("🔍 Search rider phone", key="lsf_ph")

    filtered = trips
    if s_f != "All": filtered = [t for t in filtered if t["status"] == s_f]
    if v_f != "All": filtered = [t for t in filtered if str(t.get("vehicle_type","")) == v_f]
    if ph_f:
        filtered = [t for t in filtered if
                    ph_f in str((t.get("rider") or {}).get("phone",""))]

    st.subheader(f"📡 Live Feed ({len(filtered)} trips)")

    for t in filtered[:20]:
        s      = t["status"]
        rider  = t.get("rider")  or {}
        driver = t.get("driver") or {}
        vt     = str(t.get("vehicle_type",""))
        fare   = t.get("actual_fare") or t.get("estimated_fare") or 0
        time_s = str(t.get("requested_at",""))[:16].replace("T"," ")

        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:14px 18px;
                    margin-bottom:10px;border-left:4px solid {status_color.get(s,"#ccc")};
                    box-shadow:0 1px 6px rgba(0,0,0,0.04);'>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <div>
                    <div style='font-weight:700;font-size:14px;'>
                        {status_icon.get(s,"🔴")} {rider.get("name","Unknown")}
                        <span style='color:#aaa;font-size:12px;font-weight:400;'>
                            ({rider.get("phone","—")})
                        </span>
                    </div>
                    <div style='font-size:12px;color:#555;margin-top:2px;'>
                        📍 {t.get("pickup_address","—")} → {t.get("drop_address","—")}
                    </div>
                    <div style='font-size:12px;color:#888;margin-top:2px;'>
                        Driver: {driver.get("name","—") if driver else "—"}
                        &nbsp;·&nbsp;
                        Trip: #{t.get("trip_code","—")}
                    </div>
                </div>
                <div style='text-align:right;'>
                    <span style='background:{status_bg.get(s,"#f5f5f5")};
                                 color:{status_color.get(s,"#888")};
                                 padding:3px 10px;border-radius:20px;
                                 font-size:11px;font-weight:600;'>{s.upper()}</span>
                    <div style='font-size:11px;color:#aaa;margin-top:4px;'>{time_s}</div>
                    <div style='font-size:13px;font-weight:700;color:#FF6B00;margin-top:2px;'>
                        ₹{fare:.0f}
                    </div>
                </div>
            </div>
            <div style='margin-top:8px;font-size:12px;color:#666;'>
                {vtype_icon.get(vt,"🚗")} {vt.replace("_"," ").title()}
                &nbsp;·&nbsp;
                {t.get("distance_km",0)} km
                &nbsp;·&nbsp;
                {t.get("payment_method","—")}
            </div>
        </div>""", unsafe_allow_html=True)

    # Full table
    st.markdown("---")
    rows = [{
        "Trip Code"   : t.get("trip_code",""),
        "Rider"       : (t.get("rider") or {}).get("name","—"),
        "Phone"       : (t.get("rider") or {}).get("phone","—"),
        "Pickup"      : t.get("pickup_address",""),
        "Drop"        : t.get("drop_address",""),
        "Vehicle"     : str(t.get("vehicle_type","")),
        "Fare (₹)"    : t.get("actual_fare") or t.get("estimated_fare") or 0,
        "Status"      : t.get("status",""),
        "Driver"      : (t.get("driver") or {}).get("name","—"),
        "Requested At": str(t.get("requested_at",""))[:16],
    } for t in filtered]
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, height=400, hide_index=True)
    st.download_button("📥 Download CSV", df.to_csv(index=False),
                       "live_search_feed.csv", "text/csv", type="primary")

# ══════════════════════════════════════════════════════════════════════════════
#  TRIP TRACKING
# ══════════════════════════════════════════════════════════════════════════════
def page_trips():
    page_title("🛣️ Trip Tracking & Analytics")
    data = api_get("/admin/trips", params={"limit": 200})
    if not data:
        st.error("❌ Could not load trips.")
        return
    trips = data.get("trips", [])
    if not trips:
        st.info("No trips found.")
        return
    df = pd.DataFrame(trips)
    df["Date"]   = df["requested_at"].apply(lambda x: str(x)[:10])
    df["Time"]   = df["requested_at"].apply(lambda x: str(x)[11:16])
    df["Rider"]  = df["rider"].apply(lambda x: x["name"] if x else "—")
    df["Driver"] = df["driver"].apply(lambda x: x["name"] if x else "—")
    df["Fare"]   = df["actual_fare"].fillna(df["estimated_fare"])
    comp = df[df["status"]=="completed"]
    canc = df[df["status"]=="cancelled"]
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(metric("Total",     str(len(df))),                        unsafe_allow_html=True)
    with c2: st.markdown(metric("Completed", str(len(comp)),"","green"),           unsafe_allow_html=True)
    with c3: st.markdown(metric("Cancelled", str(len(canc)),"","red"),             unsafe_allow_html=True)
    with c4: st.markdown(metric("Revenue",   f"₹{comp['Fare'].sum():,.0f}","","green"), unsafe_allow_html=True)
    with c5: st.markdown(metric("Avg Fare",  f"₹{comp['Fare'].mean():.0f}" if len(comp)>0 else "₹0"), unsafe_allow_html=True)
    st.markdown("---")
    s_f = st.selectbox("Status", ["All","completed","cancelled","requested","accepted","started"])
    filtered = df if s_f=="All" else df[df["status"]==s_f]
    cols = [c for c in ["trip_code","Date","Time","Rider","Driver","vehicle_type",
                         "pickup_address","drop_address","Fare","status","payment_method"]
            if c in filtered.columns]
    st.dataframe(filtered[cols].reset_index(drop=True), use_container_width=True, height=400)
    st.download_button("Download CSV", filtered.to_csv(index=False),
                       "trips.csv", "text/csv", type="primary")

# ══════════════════════════════════════════════════════════════════════════════
#  DRIVER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
def page_drivers():
    page_title("👥 Driver Management")
    data = api_get("/admin/drivers")
    if not data:
        st.error("❌ Could not load drivers.")
        return
    drivers = data.get("drivers", [])
    if not drivers:
        st.info("No drivers registered yet.")
        return
    total    = len(drivers)
    approved = sum(1 for d in drivers if d["is_approved"])
    online   = sum(1 for d in drivers if d["is_online"])
    on_trip  = sum(1 for d in drivers if d.get("is_on_trip"))
    blocked  = sum(1 for d in drivers if d.get("is_blocked"))
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(metric("Total",    str(total),    "","blue"),   unsafe_allow_html=True)
    with c2: st.markdown(metric("Approved", str(approved), "","green"),  unsafe_allow_html=True)
    with c3: st.markdown(metric("Pending",  str(total-approved),"","amber"), unsafe_allow_html=True)
    with c4: st.markdown(metric("Online",   str(online),   "","purple"), unsafe_allow_html=True)
    with c5: st.markdown(metric("Blocked",  str(blocked),  "","red"),    unsafe_allow_html=True)
    st.markdown("---")
    tab1, tab2 = st.tabs(["📊 Fleet", "🔘 Approve/Suspend"])
    with tab1:
        search = st.text_input("🔍 Search", key="drv_s")
        filtered = [d for d in drivers if not search or
                    search.lower() in d["full_name"].lower() or search in str(d.get("phone",""))]
        for d in filtered:
            v = d.get("vehicle") or {}
            v_str  = f"{v.get('brand','')} {v.get('model','')}".strip() or "—"
            status = "🟢 Online" if d["is_online"] else ("🔵 On Trip" if d.get("is_on_trip") else "⚫ Offline")
            blocked_badge = ("<span style='color:#EA4335;font-size:11px;font-weight:600;'> 🔴 Blocked</span>"
                             if d.get("is_blocked") else "")
            appr_badge = ("✅ Approved" if d["is_approved"] else "⏳ Pending")
            st.markdown(f"""
            <div style='padding:8px 12px;background:white;border-radius:10px;margin-bottom:6px;
                        border:1px solid #eee;'>
                <b>{d['full_name']}</b>{blocked_badge}
                <span style='color:#888;font-size:12px;margin-left:8px;'>
                    {d.get('phone','')} · {d.get('city','')} · {v_str}
                </span>
                <span style='float:right;font-size:12px;'>
                    {status} · {appr_badge} · ⭐{d.get('avg_rating',0)} · {d.get('total_trips',0)} trips
                </span>
            </div>""", unsafe_allow_html=True)
    with tab2:
        for d in drivers:
            col1, col2 = st.columns([3,1])
            with col1:
                st.markdown(f"**{d['full_name']}** — {d.get('phone','')} — {'✅ Approved' if d['is_approved'] else '⏳ Pending'}")
            with col2:
                lbl = "🔴 Suspend" if d["is_approved"] else "✅ Approve"
                if st.button(lbl, key=f"appr_{d['id']}", use_container_width=True):
                    result = api_patch(f"/admin/drivers/{d['id']}/approve")
                    if result:
                        st.success(result.get("message","Done"))
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  LIVE MAP
# ══════════════════════════════════════════════════════════════════════════════
def page_live_map():
    page_title("🗺️ Live Map / GPS Tracking")
    if st.button("🔄 Refresh"):
        st.rerun()
    data = api_get("/admin/drivers")
    if not data:
        st.error("❌ Could not load data.")
        return
    drivers = data.get("drivers", [])
    located = [d for d in drivers if d.get("current_lat") and d.get("current_lng")]
    online  = [d for d in drivers if d["is_online"]]
    on_trip = [d for d in drivers if d.get("is_on_trip")]
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(metric("On Map",  str(len(located)),        "","blue"),  unsafe_allow_html=True)
    with c2: st.markdown(metric("Online",  str(len(online)),         "","green"), unsafe_allow_html=True)
    with c3: st.markdown(metric("On Trip", str(len(on_trip)),        "","purple"),unsafe_allow_html=True)
    with c4: st.markdown(metric("Offline", str(len(drivers)-len(online)),"","red"), unsafe_allow_html=True)
    st.markdown("---")
    clat = sum(d["current_lat"] for d in located)/len(located) if located else 23.23
    clng = sum(d["current_lng"] for d in located)/len(located) if located else 87.85
    m = folium.Map(location=[clat, clng], zoom_start=12)
    for d in located:
        color = "blue" if d.get("is_on_trip") else ("green" if d["is_online"] else "gray")
        folium.Marker(
            location=[d["current_lat"], d["current_lng"]],
            tooltip=f"{d['full_name']} — {'On Trip' if d.get('is_on_trip') else ('Online' if d['is_online'] else 'Offline')}",
            icon=folium.Icon(color=color, icon="car", prefix="fa")
        ).add_to(m)
    if not located:
        st.info("📍 No drivers with GPS data yet.")
    st_folium(m, width=None, height=500, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  REVENUE
# ══════════════════════════════════════════════════════════════════════════════
def page_revenue():
    page_title("💰 Revenue & Earnings Reports")
    period = st.radio("Period", ["Last 7 days","Last 30 days","Last 60 days"], horizontal=True)
    n = {"Last 7 days":7,"Last 30 days":30,"Last 60 days":60}[period]
    data = api_get("/admin/revenue", params={"days": n})
    if not data:
        st.error("❌ Could not load revenue data.")
        return
    daily = pd.DataFrame(data.get("daily_breakdown", []))
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(metric("Total Revenue",    f"₹{data.get('total_revenue',0):,.2f}","","green"),  unsafe_allow_html=True)
    with c2: st.markdown(metric("Total Trips",      str(data.get('total_trips',0))),                     unsafe_allow_html=True)
    with c3: st.markdown(metric("Total Commission", f"₹{data.get('total_commission',0):,.2f}","","purple"), unsafe_allow_html=True)
    if len(daily)==0:
        st.info("No revenue data yet.")
        return
    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(daily, x="date", y="revenue", title=f"Revenue ({period})",
                      markers=True, color_discrete_sequence=[BLUE])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(daily, x="date", y=["trips","commission"],
                     title="Trips & Commission",
                     color_discrete_map={"trips":GREEN,"commission":PURPLE}, barmode="group")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(daily.sort_values("date",ascending=False).reset_index(drop=True),
                 use_container_width=True, height=320)
    st.download_button("Download CSV", daily.to_csv(index=False),
                       f"revenue_{n}d.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════════════
def page_notifications():
    page_title("🔔 Notifications & Alerts")
    overview  = api_get("/admin/overview") or {}
    drv_data  = api_get("/admin/drivers")  or {}
    trip_data = api_get("/admin/trips", params={"limit": 100}) or {}
    drivers   = drv_data.get("drivers", [])
    trips     = trip_data.get("trips",  [])
    rev       = overview.get("revenue", {})
    alerts = []
    pending = [d for d in drivers if not d["is_approved"]]
    if pending:
        alerts.append({"Title": f"⏳ {len(pending)} Driver(s) Awaiting Approval",
                       "Description": ", ".join(d["full_name"] for d in pending[:3]),
                       "Priority": "High", "Time": "Now"})
    low_rated = [d for d in drivers if d.get("avg_rating",5)<4.0 and d.get("total_trips",0)>5]
    for d in low_rated[:3]:
        alerts.append({"Title": f"⭐ Low Rating — {d['full_name']}",
                       "Description": f"Rating: {d.get('avg_rating',0)} · {d.get('total_trips',0)} trips",
                       "Priority": "Medium", "Time": "Recent"})
    cancelled = [t for t in trips if t.get("status")=="cancelled"]
    if cancelled:
        alerts.append({"Title": f"❌ {len(cancelled)} Cancelled Trips",
                       "Description": f"Out of last {len(trips)} trips",
                       "Priority": "High" if len(cancelled)>10 else "Low", "Time": "Today"})
    active = [t for t in trips if t.get("status") in ["requested","accepted","arrived","started"]]
    if active:
        alerts.append({"Title": f"🚖 {len(active)} Active Trip(s) Right Now",
                       "Description": "Trips currently in progress",
                       "Priority": "Low", "Time": "Now"})
    blocked_riders  = overview.get("users", {}).get("blocked_riders", 0)
    blocked_drivers = overview.get("users", {}).get("blocked_drivers", 0)
    if blocked_riders or blocked_drivers:
        alerts.append({"Title": f"🔒 {blocked_riders} Blocked Riders · {blocked_drivers} Blocked Drivers",
                       "Description": "Go to Block Management to review",
                       "Priority": "Medium", "Time": "Now"})
    prio_colors = {"High":"#FF6D01","Medium":"#FBBC04","Low":"#34A853"}
    prio_bg     = {"High":"#FFF3E0","Medium":"#FEF3CD","Low":"#E6F4EA"}
    for a in alerts:
        c = prio_colors.get(a["Priority"],"#ccc")
        b = prio_bg.get(a["Priority"],"#f9f9f9")
        st.markdown(f"""
        <div style='background:{b};border-left:4px solid {c};padding:14px 18px;
                    border-radius:0 10px 10px 0;margin-bottom:10px;'>
            <div style='font-size:14px;font-weight:700;'>{a['Title']}</div>
            <div style='font-size:13px;color:#555;margin-top:4px;'>{a['Description']}</div>
            <div style='font-size:11px;color:#888;margin-top:4px;'>
                <span style='background:{c};color:white;padding:2px 8px;border-radius:12px;
                             font-size:11px;'>{a['Priority']}</span>
                &nbsp; {a['Time']}
            </div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SEND NOTIFICATION
# ══════════════════════════════════════════════════════════════════════════════
def page_send_notification():
    page_title("📢 Send Notification")
    if "sent_notifs" not in st.session_state:
        st.session_state.sent_notifs = []
    with st.form("sn_form", clear_on_submit=True):
        audience = st.selectbox("Send To", ["All (Riders + Drivers)","All Drivers","All Riders"])
        title    = st.text_input("Title", placeholder="e.g. 🎉 Special Offer!")
        message  = st.text_area("Message", height=100)
        if st.form_submit_button("🚀 Send", type="primary", use_container_width=True):
            if not title or not message:
                st.error("Fill in both title and message.")
            else:
                role_map = {"All Drivers":"driver","All Riders":"rider","All (Riders + Drivers)":None}
                result = api_post("/admin/notifications/broadcast-scheduled",
                                  {"title": title, "message": message, "target": role_map.get(audience)})
                if result:
                    st.success(f"✅ Sent! {result.get('message','')}")
                    st.session_state.sent_notifs.insert(0,
                        {"To": audience,"Title": title,"Message": message,
                         "Sent At": datetime.now().strftime("%Y-%m-%d %H:%M")})
                else:
                    st.error("Failed to send.")
    if st.session_state.sent_notifs:
        st.markdown("---")
        st.subheader("📬 Sent History")
        for n in st.session_state.sent_notifs:
            st.markdown(f"""
            <div style='background:white;border-radius:10px;padding:14px 18px;
                        margin-bottom:8px;border:1px solid #eee;'>
                <b>{n['Title']}</b> → <i>{n['To']}</i>
                <div style='font-size:12px;color:#555;'>{n['Message']}</div>
                <div style='font-size:11px;color:#aaa;'>{n['Sent At']}</div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  RIDER ONBOARDING
# ══════════════════════════════════════════════════════════════════════════════
def page_rider_onboarding():
    page_title("🧑‍💼 Rider Onboarding")
    data = api_get("/admin/users", params={"limit": 200})
    if not data:
        st.error("❌ Could not load riders.")
        return
    users = data.get("users", [])
    if not users:
        st.info("No riders registered yet.")
        return
    rows = [{"ID": u["id"], "Name": u["full_name"], "Phone": u["phone"],
             "Email": u.get("email","—"),
             "Wallet": f"₹{u.get('wallet_balance',0):,.2f}",
             "Has Rider Account": "✅" if u.get("has_rider_account") else "❌",
             "Has Driver Account": "✅" if u.get("has_driver_account") else "❌",
             "Rider Blocked": "🔴" if u.get("rider_blocked") else "🟢",
             "Joined": str(u.get("created_at",""))[:10]}
            for u in users]
    df = pd.DataFrame(rows)
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(metric("Total Users", str(len(df))), unsafe_allow_html=True)
    with c2: st.markdown(metric("With Rider Account", str(df["Has Rider Account"].eq("✅").sum()),"","green"), unsafe_allow_html=True)
    with c3: st.markdown(metric("With Driver Account", str(df["Has Driver Account"].eq("✅").sum()),"","blue"), unsafe_allow_html=True)
    st.markdown("---")
    search = st.text_input("🔍 Search by phone", key="ro_search")
    if search:
        df = df[df["Phone"].astype(str).str.contains(search, na=False)]
    st.dataframe(df, use_container_width=True, height=400, hide_index=True)
    st.download_button("📥 Download", df.to_csv(index=False), "riders.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════════════
#  DRIVER DOCUMENT UPLOAD, DRIVER PERFORMANCE, VEHICLE MGMT,
#  SEARCH HEATMAP, DRIVER ONLINE LOG, PRICING, PROMOTIONS,
#  DRIVER PAYMENTS, ACTIVATE PROMO, RIDE HISTORY — kept from original
# ══════════════════════════════════════════════════════════════════════════════

# Import these from original file logic (abbreviated wrappers that call API)
def page_driver_document_upload():
    page_title("📄 Driver Documents")
    data = api_get("/admin/drivers")
    if not data:
        st.error("❌ Could not load drivers.")
        return
    drivers = data.get("drivers", [])
    for d in drivers:
        with st.expander(f"{'✅' if d['is_approved'] else '⏳'} {d['full_name']} · {d.get('phone','')}"):
            st.json({k: v for k,v in d.items() if "url" in k or k in ["license_number","aadhar_number"]})
            ca, cs = st.columns(2)
            with ca:
                if not d["is_approved"]:
                    if st.button("✅ Approve", key=f"apdoc_{d['id']}", type="primary"):
                        result = api_patch(f"/admin/drivers/{d['id']}/approve")
                        if result:
                            st.success(f"✅ {d['full_name']} approved!")
                            st.rerun()
            with cs:
                if d["is_approved"]:
                    if st.button("🔴 Suspend", key=f"spdoc_{d['id']}"):
                        result = api_patch(f"/admin/drivers/{d['id']}/approve")
                        if result:
                            st.warning(f"🔴 {d['full_name']} suspended.")
                            st.rerun()

def page_driver_performance():
    page_title("📈 Driver Performance")
    data = api_get("/admin/drivers")
    if not data:
        st.error("❌ Could not load drivers.")
        return
    drivers = data.get("drivers",[])
    rows = [{"Name": d["full_name"], "Phone": d.get("phone",""),
             "City": d.get("city",""), "Rating": d.get("avg_rating",0),
             "Trips": d.get("total_trips",0),
             "Earnings": f"₹{d.get('total_earnings',0):,.0f}",
             "Status": "Online" if d["is_online"] else "Offline",
             "Approved": "✅" if d["is_approved"] else "⏳",
             "Blocked": "🔴" if d.get("is_blocked") else "🟢"}
            for d in sorted(drivers, key=lambda x: x.get("total_trips",0), reverse=True)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

def page_vehicle_mgmt():
    page_title("🚗 Vehicle Management")
    data = api_get("/admin/drivers")
    if not data:
        st.error("❌ Could not load data.")
        return
    drivers = data.get("drivers",[])
    with_v = [d for d in drivers if d.get("vehicle")]
    rows = [{"Driver": d["full_name"], "Phone": d.get("phone",""),
             "Type": (d["vehicle"] or {}).get("type",""),
             "Brand/Model": f"{(d['vehicle'] or {}).get('brand','')} {(d['vehicle'] or {}).get('model','')}".strip(),
             "RC": (d["vehicle"] or {}).get("rc_number","—"),
             "Insurance": "✅" if d.get("insurance_url") else "❌",
             "Approved": "✅" if d["is_approved"] else "⏳"}
            for d in with_v]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

def page_search_heatmap():
    page_title("🔥 Search Demand Heatmap")
    trip_data = api_get("/admin/trips", params={"limit": 200})
    if not trip_data:
        st.error("❌ Could not load data.")
        return
    trips = trip_data.get("trips",[])
    pickup_pts = [[t["pickup_lat"],t["pickup_lng"]] for t in trips
                  if t.get("pickup_lat") and t.get("pickup_lng")]
    clat = sum(p[0] for p in pickup_pts)/len(pickup_pts) if pickup_pts else 23.23
    clng = sum(p[1] for p in pickup_pts)/len(pickup_pts) if pickup_pts else 87.85
    m = folium.Map(location=[clat,clng], zoom_start=12, tiles="CartoDB dark_matter")
    if pickup_pts:
        HeatMap(pickup_pts, radius=15, blur=10).add_to(m)
        st.info(f"📍 Showing {len(pickup_pts)} pickup points from {len(trips)} trips")
    else:
        st.info("No GPS data yet.")
    st_folium(m, width=None, height=550, use_container_width=True)

def page_driver_online_log():
    page_title("⏱️ Driver Online Log")
    if st.button("🔄 Refresh"):
        st.rerun()
    data = api_get("/admin/drivers")
    if not data:
        st.error("❌ Could not load data.")
        return
    drivers = data.get("drivers",[])
    rows = [{"Name": d["full_name"], "Phone": d.get("phone",""),
             "City": d.get("city",""),
             "Status": "On Trip" if d.get("is_on_trip") else ("Online" if d["is_online"] else "Offline"),
             "Approved": "✅" if d["is_approved"] else "⏳",
             "Blocked": "🔴" if d.get("is_blocked") else "🟢",
             "Rating": d.get("avg_rating",0),
             "Trips": d.get("total_trips",0),
             "Lat": d.get("current_lat",""), "Lng": d.get("current_lng","")}
            for d in drivers]
    df = pd.DataFrame(rows)
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(metric("Total", str(len(drivers))), unsafe_allow_html=True)
    with c2: st.markdown(metric("Online", str(sum(1 for d in drivers if d["is_online"])),"","green"), unsafe_allow_html=True)
    with c3: st.markdown(metric("On Trip", str(sum(1 for d in drivers if d.get("is_on_trip"))),"","blue"), unsafe_allow_html=True)
    with c4: st.markdown(metric("Offline", str(sum(1 for d in drivers if not d["is_online"])),"","red"), unsafe_allow_html=True)
    st.markdown("---")
    st.dataframe(df, use_container_width=True, hide_index=True)

def page_pricing_config():
    page_title("⚙️ Pricing & Fees", "Edit fares, commission, and surge — changes apply in real time")
    data = api_get("/pricing/")
    if not data:
        st.error("❌ Could not load pricing.")
        return

    pricing = data.get("pricing", [])
    surge   = data.get("surge", {})

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(metric("Active Surge Multiplier", f"{surge.get('active_multiplier', 1.0)}x", "", "purple"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric("Manual Surge", "🔴 ON" if surge.get("manual_surge_active") else "⚫ OFF", "", "amber"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric("Scheduled Surge", "🔴 ON" if surge.get("schedule_surge_active") else "⚫ OFF", "", "amber"), unsafe_allow_html=True)

    st.markdown("---")
    tab1, tab2 = st.tabs(["💰 Edit Fares & Commission", "⚡ Surge Control"])

    # ── TAB 1: Edit Fares ──────────────────────────────────────────────────
    with tab1:
        if not pricing:
            st.warning("No pricing data found.")
        else:
            cities = sorted(set(p["city"] for p in pricing))
            sel_city = st.selectbox("City", cities, key="pricing_city")

            city_rows = [p for p in pricing if p["city"] == sel_city]
            vehicles = sorted(set(p["vehicle_type"] for p in city_rows))
            sel_vehicle = st.selectbox("Vehicle Type", vehicles, key="pricing_vehicle")

            v_rows = [p for p in city_rows if p["vehicle_type"] == sel_vehicle]
            services = sorted(set(p["service_type"] for p in v_rows))
            sel_service = st.selectbox("Service Type", services, key="pricing_service")

            cfg = next((p for p in v_rows if p["service_type"] == sel_service), None)

            if cfg:
                st.markdown(f"**Editing: {sel_vehicle} · {sel_service} · {sel_city}**")
                with st.form("edit_pricing_form"):
                    fc1, fc2 = st.columns(2)
                    with fc1:
                        base_fare   = st.number_input("Base Fare (₹)", min_value=0.0, value=float(cfg["base_fare"]), step=1.0)
                        per_km_fare = st.number_input("Per KM Fare (₹)", min_value=0.0, value=float(cfg["per_km_fare"]), step=0.5)
                        per_min_fare= st.number_input("Per Minute Fare (₹)", min_value=0.0, value=float(cfg["per_min_fare"]), step=0.1)
                    with fc2:
                        min_fare    = st.number_input("Minimum Fare (₹)", min_value=0.0, value=float(cfg["min_fare"]), step=1.0)
                        commission_type = st.selectbox("Commission Type", ["percent", "flat"],
                                                        index=0 if cfg.get("commission_type","percent")=="percent" else 1)
                        commission_value = st.number_input("Commission Value", min_value=0.0,
                                                             value=float(cfg.get("commission_value",10)), step=0.5)

                    submitted = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
                    if submitted:
                        result = api_patch("/pricing/vehicle", {
                            "city": sel_city,
                            "vehicle_type": sel_vehicle,
                            "service_type": sel_service,
                            "base_fare": base_fare,
                            "per_km_fare": per_km_fare,
                            "per_min_fare": per_min_fare,
                            "min_fare": min_fare,
                            "commission_type": commission_type,
                            "commission_value": commission_value,
                        })
                        if result and "message" in result:
                            st.success(result["message"])
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to update: {result}")

            st.markdown("---")
            st.markdown("##### All Pricing Configs")
            st.dataframe(pd.DataFrame(pricing), use_container_width=True, hide_index=True)

    # ── TAB 2: Surge Control ─────────────────────────────────────────────────
    with tab2:
        st.markdown("##### Manual Surge")
        with st.form("manual_surge_form"):
            mc1, mc2 = st.columns(2)
            with mc1:
                manual_active = st.checkbox("Enable Manual Surge", value=surge.get("manual_surge_active", False))
            with mc2:
                manual_mult = st.number_input("Manual Surge Multiplier", min_value=1.0, max_value=5.0, step=0.1,
                                               value=float(surge.get("manual_surge_multiplier", 1.0)))
            if st.form_submit_button("💾 Save Manual Surge", type="primary"):
                result = api_patch("/pricing/surge", {
                    "manual_surge_active": manual_active,
                    "manual_surge_multiplier": manual_mult,
                })
                if result:
                    st.success(result.get("message", "Updated ✅"))
                    st.rerun()

        st.markdown("---")
        st.markdown("##### Scheduled Surge (e.g. peak hours)")
        with st.form("schedule_surge_form"):
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                sched_active = st.checkbox("Enable Scheduled Surge", value=surge.get("schedule_surge_active", False))
            with sc2:
                sched_start = st.number_input("Start Hour (0-23)", min_value=0, max_value=23,
                                               value=int(surge.get("schedule_start_hour", 8)))
            with sc3:
                sched_end = st.number_input("End Hour (0-23)", min_value=0, max_value=23,
                                             value=int(surge.get("schedule_end_hour", 10)))
            sched_mult = st.number_input("Scheduled Surge Multiplier", min_value=1.0, max_value=5.0, step=0.1,
                                          value=float(surge.get("schedule_surge_multiplier", 1.0)))
            if st.form_submit_button("💾 Save Scheduled Surge", type="primary"):
                result = api_patch("/pricing/surge", {
                    "schedule_surge_active": sched_active,
                    "schedule_start_hour": sched_start,
                    "schedule_end_hour": sched_end,
                    "schedule_surge_multiplier": sched_mult,
                })
                if result:
                    st.success(result.get("message", "Updated ✅"))
                    st.rerun()

        st.markdown("---")
        st.markdown("##### Auto Surge (based on demand)")
        with st.form("auto_surge_form"):
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                auto_active = st.checkbox("Enable Auto Surge", value=surge.get("auto_surge_active", False))
            with ac2:
                auto_threshold = st.number_input("Demand Threshold (pending rides)", min_value=1,
                                                  value=int(surge.get("auto_surge_threshold", 10)))
            with ac3:
                auto_mult = st.number_input("Auto Surge Multiplier", min_value=1.0, max_value=5.0, step=0.1,
                                             value=float(surge.get("auto_surge_multiplier", 1.0)))
            if st.form_submit_button("💾 Save Auto Surge", type="primary"):
                result = api_patch("/pricing/surge", {
                    "auto_surge_active": auto_active,
                    "auto_surge_threshold": auto_threshold,
                    "auto_surge_multiplier": auto_mult,
                })
                if result:
                    st.success(result.get("message", "Updated ✅"))
                    st.rerun()

def page_promotions():
    page_title("🎁 Promotions", "All promo codes — toggle active/inactive or delete")
    data = api_get("/promos/")
    if not data:
        st.error("❌ Could not load promos.")
        return
    promos = data.get("promos", [])
    if not promos:
        st.info("No promo codes yet. Create one in 'Activate Promo'.")
        return

    for p in promos:
        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
            with c1:
                st.markdown(f"**{p['code']}**")
                st.caption(p.get("description", ""))
            with c2:
                st.markdown(f"💰 {p['discount_display']}")
                st.caption("Auto-apply ✅" if p["is_auto_apply"] else "Manual")
            with c3:
                st.caption(f"Min fare: ₹{p.get('min_fare', 0)}")
                st.caption(f"Vehicle: {p.get('vehicle_type') or 'All'}")
            with c4:
                used = p.get("used_count", 0)
                max_u = p.get("max_uses", 0)
                st.caption(f"Used: {used} / {'∞' if max_u==0 else max_u}")
                st.caption(f"Expiry: {p.get('expiry_date') or 'Never'}")
            with c5:
                status = "🟢 Active" if p["is_active"] else "🔴 Inactive"
                st.markdown(status)
                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    if st.button("Toggle", key=f"toggle_{p['id']}", use_container_width=True):
                        result = api_patch(f"/promos/{p['id']}/toggle")
                        if result:
                            st.success(result.get("message", "Updated"))
                            st.rerun()
                with bcol2:
                    if st.button("Delete", key=f"delete_{p['id']}", use_container_width=True):
                        result = api_delete(f"/promos/{p['id']}")
                        if result:
                            st.success(result.get("message", "Deleted"))
                            st.rerun()

def page_activate_promo():
    page_title("🏷️ Create Promo Code", "Create a new promo code — saved to database immediately")

    vehicle_types = ["All", "bike", "auto", "toto", "ac_cab", "non_ac_cab", "ambulance"]

    with st.form("promo_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            code = st.text_input("Promo Code").strip().upper()
            disc_type = st.selectbox("Discount Type", ["percentage", "flat"])
            disc_val = st.number_input("Discount Value", min_value=1.0,
                                        value=10.0,
                                        help="% if percentage, ₹ if flat")
            min_fare = st.number_input("Minimum Fare (₹)", min_value=0.0, value=0.0)
        with c2:
            description = st.text_input("Description")
            vehicle = st.selectbox("Applicable Vehicle Type", vehicle_types)
            max_uses = st.number_input("Max Uses (0 = unlimited)", min_value=0, value=0)
            expiry = st.date_input("Expiry Date (optional)", value=None)

        auto_apply = st.checkbox("Auto-Apply on booking (no code entry needed)", value=True)

        if st.form_submit_button("🚀 Create Promo", type="primary", use_container_width=True):
            if not code:
                st.error("Promo code is required.")
            else:
                payload = {
                    "code": code,
                    "description": description,
                    "discount_type": disc_type,
                    "discount_value": disc_val,
                    "is_auto_apply": auto_apply,
                    "max_uses": int(max_uses),
                    "min_fare": min_fare,
                    "vehicle_type": None if vehicle == "All" else vehicle,
                }
                if expiry:
                    payload["expiry_date"] = expiry.strftime("%Y-%m-%d")

                result = api_post("/promos/", payload)
                if result and "message" in result:
                    st.success(result["message"])
                elif result and "detail" in result:
                    st.error(f"❌ {result['detail']}")
                else:
                    st.error(f"❌ Failed: {result}")

    st.markdown("---")
    st.markdown("##### Existing Promos")
    data = api_get("/promos/")
    if data and data.get("promos"):
        st.dataframe(pd.DataFrame(data["promos"])[["code","description","discount_display","is_auto_apply","is_active","used_count","max_uses","vehicle_type","expiry_date"]],
                      use_container_width=True, hide_index=True)

def page_driver_payments():
    page_title("💸 Driver Payments")
    data = api_get("/admin/drivers")
    if not data:
        st.error("❌ Could not load data.")
        return
    drivers = data.get("drivers",[])
    rows = [{"Name": d["full_name"], "Phone": d.get("phone",""),
             "Total Earnings": f"₹{d.get('total_earnings',0):,.2f}",
             "Total Trips": d.get("total_trips",0),
             "City": d.get("city","")}
            for d in sorted(drivers, key=lambda x: x.get("total_earnings",0), reverse=True)]
    c1,c2 = st.columns(2)
    with c1: st.markdown(metric("Total Drivers", str(len(drivers))), unsafe_allow_html=True)
    with c2: st.markdown(metric("Total Paid Out",
        f"₹{sum(d.get('total_earnings',0) for d in drivers):,.0f}","","green"), unsafe_allow_html=True)
    st.markdown("---")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

def page_ride_history():
    page_title("🧾 Ride History")
    data = api_get("/admin/users", params={"limit": 200})
    if not data:
        st.error("❌ Could not load riders.")
        return
    users = data.get("users",[])
    names = [f"{u['full_name']} — {u['phone']}" for u in users]
    if not names:
        st.info("No riders yet.")
        return
    sel   = st.selectbox("Select Rider", names)
    rider = users[names.index(sel)]
    st.markdown(f"**{rider['full_name']}** · {rider['phone']} · Wallet: ₹{rider.get('wallet_balance',0):,.2f}")
    trips_data = api_get("/admin/trips", params={"limit":200})
    all_trips  = trips_data.get("trips",[]) if trips_data else []
    rtips = [t for t in all_trips if
             t.get("rider") and t["rider"].get("phone")==rider["phone"]]
    if not rtips:
        st.info("No trips for this rider yet.")
        return
    rows = [{"Date": str(t.get("requested_at",""))[:10],
             "Trip": t.get("trip_code",""),
             "From": t.get("pickup_address",""), "To": t.get("drop_address",""),
             "Fare": t.get("actual_fare") or t.get("estimated_fare") or 0,
             "Status": t.get("status","")}
            for t in rtips]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  CANCELLATION CONFIG
# ══════════════════════════════════════════════════════════════════════════════
def page_cancellation_config():
    page_title("⚙️ Cancellation Config", "Set free waiting minutes and cancellation charges")
    data = api_get("/admin/overview")
    with st.form("cancel_config_form"):
        st.markdown("##### Cancellation Settings")
        c1, c2 = st.columns(2)
        with c1:
            free_minutes = st.number_input("Free Waiting Minutes", min_value=0, value=5, step=1,
                help="Driver waits this many minutes for free before charges apply")
        with c2:
            charge_amount = st.number_input("Cancellation Charge (₹)", min_value=0.0, value=10.0, step=1.0,
                help="Charge applied when rider cancels after driver arrives")
        is_active = st.checkbox("Enable Cancellation Charges", value=True)
        if st.form_submit_button("💾 Save", type="primary", use_container_width=True):
            result = api_patch("/admin/config/cancellation", {
                "free_minutes": int(free_minutes),
                "charge_amount": float(charge_amount),
                "is_active": is_active
            })
            if result and "message" in result:
                st.success(result["message"])
            else:
                st.error(f"Failed: {result}")

# ══════════════════════════════════════════════════════════════════════════════
#  BROADCAST NOTIFICATION HISTORY
# ══════════════════════════════════════════════════════════════════════════════
def page_broadcast_history():
    page_title("📬 Broadcast History", "All sent and scheduled notifications")
    if st.button("🔄 Refresh"):
        st.rerun()
    data = api_get("/admin/notifications/broadcast-history")
    if not data:
        st.error("❌ Could not load notifications.")
        return
    notifs = data.get("notifications", [])
    if not notifs:
        st.info("No broadcasts sent yet.")
        return
    sent     = [n for n in notifs if n["is_sent"]]
    pending  = [n for n in notifs if not n["is_sent"]]
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(metric("Total", str(len(notifs))), unsafe_allow_html=True)
    with c2: st.markdown(metric("Sent", str(len(sent)), "", "green"), unsafe_allow_html=True)
    with c3: st.markdown(metric("Scheduled", str(len(pending)), "", "amber"), unsafe_allow_html=True)
    st.markdown("---")
    for n in notifs:
        status_color = "#34A853" if n["is_sent"] else "#FBBC04"
        status_text  = "✅ Sent" if n["is_sent"] else "⏳ Scheduled"
        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:14px 18px;
                    margin-bottom:8px;border-left:4px solid {status_color};
                    box-shadow:0 1px 6px rgba(0,0,0,0.04);'>
            <div style='font-weight:700;font-size:14px;'>{n["title"]}</div>
            <div style='font-size:13px;color:#555;margin-top:4px;'>{n["message"]}</div>
            <div style='font-size:12px;color:#888;margin-top:6px;'>
                Target: {n["target"]} · {status_text} ·
                Sent to: {n.get("total_sent", 0)} users ·
                {str(n.get("sent_at") or n.get("scheduled_at") or "")[:16]}
            </div>
        </div>""", unsafe_allow_html=True)
        if not n["is_sent"]:
            if st.button(f"🚀 Send Now", key=f"send_now_{n['id']}"):
                result = api_post(f"/admin/notifications/send-now/{n['id']}")
                if result:
                    st.success(result.get("message", "Sent!"))
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  SCHEDULE NOTIFICATION
# ══════════════════════════════════════════════════════════════════════════════
def page_schedule_notification():
    page_title("📅 Schedule Notification", "Schedule a broadcast for a future date and time")
    with st.form("schedule_notif_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            title    = st.text_input("Title", placeholder="e.g. Weekend Special Offer!")
            target   = st.selectbox("Send To", ["all", "riders", "drivers"])
            notif_type = st.selectbox("Type", ["promotional", "system", "alert"])
        with c2:
            message  = st.text_area("Message", height=100)
            sched_date = st.date_input("Schedule Date")
            sched_time = st.time_input("Schedule Time")
        if st.form_submit_button("📅 Schedule", type="primary", use_container_width=True):
            if not title or not message:
                st.error("Fill in both title and message.")
            else:
                from datetime import datetime
                scheduled_at = datetime.combine(sched_date, sched_time).isoformat()
                result = api_post("/admin/notifications/broadcast-scheduled", {
                    "title": title,
                    "message": message,
                    "target": target,
                    "notif_type": notif_type,
                    "scheduled_at": scheduled_at
                })
                if result and "message" in result:
                    st.success(f"✅ Scheduled for {scheduled_at}")
                else:
                    st.error(f"Failed: {result}")

# ══════════════════════════════════════════════════════════════════════════════
#  WALLET MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
def page_wallet_management():
    page_title("💳 Wallet Management", "View and manage rider and driver wallets")
    tab1, tab2 = st.tabs(["👤 Rider Wallets", "🚗 Driver Wallets"])

    with tab1:
        data = api_get("/admin/users", params={"limit": 200})
        if not data:
            st.error("❌ Could not load users.")
            return
        users = data.get("users", [])
        search = st.text_input("🔍 Search by name or phone", key="wallet_rider_search")
        if search:
            users = [u for u in users if search.lower() in u["full_name"].lower()
                     or search in str(u.get("phone", ""))]
        total_wallet = sum(u.get("wallet_balance", 0) for u in users)
        st.markdown(metric("Total Wallet Balance", f"₹{total_wallet:,.2f}", "", "green"), unsafe_allow_html=True)
        st.markdown("---")
        rows = [{"Name": u["full_name"], "Phone": u.get("phone", ""),
                 "Wallet (₹)": u.get("wallet_balance", 0),
                 "Joined": str(u.get("created_at", ""))[:10]} for u in users]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with tab2:
        data = api_get("/admin/drivers")
        if not data:
            st.error("❌ Could not load drivers.")
            return
        drivers = data.get("drivers", [])
        search2 = st.text_input("🔍 Search by name or phone", key="wallet_driver_search")
        if search2:
            drivers = [d for d in drivers if search2.lower() in d["full_name"].lower()
                       or search2 in str(d.get("phone", ""))]
        total_driver_wallet = sum(d.get("wallet_balance", 0) for d in drivers)
        st.markdown(metric("Total Driver Wallet Balance", f"₹{total_driver_wallet:,.2f}", "", "green"), unsafe_allow_html=True)
        st.markdown("---")
        rows2 = [{"Name": d["full_name"], "Phone": d.get("phone", ""),
                  "Wallet (₹)": d.get("wallet_balance", 0),
                  "Total Earnings (₹)": d.get("total_earnings", 0),
                  "Total Trips": d.get("total_trips", 0)} for d in drivers]
        st.dataframe(pd.DataFrame(rows2), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
#  WITHDRAWAL REQUESTS
# ══════════════════════════════════════════════════════════════════════════════
def page_withdrawals():
    page_title("💸 Withdrawal Requests", "Approve or reject driver withdrawal requests")
    if st.button("🔄 Refresh"):
        st.rerun()
    data = api_get("/admin/withdrawals")
    if not data:
        st.error("❌ Could not load withdrawals.")
        return
    withdrawals = data.get("withdrawals", [])
    if not withdrawals:
        st.info("No withdrawal requests yet.")
        return
    pending  = [w for w in withdrawals if w["status"] == "pending"]
    approved = [w for w in withdrawals if w["status"] == "approved"]
    rejected = [w for w in withdrawals if w["status"] == "rejected"]
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(metric("Pending", str(len(pending)), "", "amber"), unsafe_allow_html=True)
    with c2: st.markdown(metric("Approved", str(len(approved)), "", "green"), unsafe_allow_html=True)
    with c3: st.markdown(metric("Rejected", str(len(rejected)), "", "red"), unsafe_allow_html=True)
    st.markdown("---")
    for w in withdrawals:
        status_color = {"pending": "#FBBC04", "approved": "#34A853", "rejected": "#EA4335"}.get(w["status"], "#ccc")
        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:14px 18px;
                    margin-bottom:8px;border-left:4px solid {status_color};'>
            <b>{w.get("driver_name", "Driver")}</b> — ₹{w.get("amount", 0):,.2f}
            <span style='color:#888;font-size:12px;margin-left:8px;'>
                {w.get("method", "")} · {w.get("upi_id") or w.get("account_number", "")}
            </span>
            <span style='float:right;font-size:12px;color:{status_color};font-weight:600;'>
                {w["status"].upper()}
            </span>
        </div>""", unsafe_allow_html=True)
        if w["status"] == "pending":
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve", key=f"appr_w_{w['id']}", type="primary", use_container_width=True):
                    result = api_patch(f"/admin/withdrawals/{w['id']}/approve")
                    if result:
                        st.success("Approved!")
                        st.rerun()
            with col2:
                if st.button("❌ Reject", key=f"rej_w_{w['id']}", use_container_width=True):
                    result = api_patch(f"/admin/withdrawals/{w['id']}/reject")
                    if result:
                        st.warning("Rejected.")
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  TRIP DISPUTES
# ══════════════════════════════════════════════════════════════════════════════
def page_disputes():
    page_title("⚖️ Trip Disputes", "View and resolve trip disputes")
    if st.button("🔄 Refresh"):
        st.rerun()
    data = api_get("/admin/disputes")
    if not data:
        st.error("❌ Could not load disputes.")
        return
    disputes = data.get("disputes", [])
    if not disputes:
        st.info("No disputes yet.")
        return
    open_d    = [d for d in disputes if d["status"] == "open"]
    resolved  = [d for d in disputes if d["status"] == "resolved"]
    c1, c2 = st.columns(2)
    with c1: st.markdown(metric("Open", str(len(open_d)), "", "red"), unsafe_allow_html=True)
    with c2: st.markdown(metric("Resolved", str(len(resolved)), "", "green"), unsafe_allow_html=True)
    st.markdown("---")
    for d in disputes:
        status_color = "#EA4335" if d["status"] == "open" else "#34A853"
        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:14px 18px;
                    margin-bottom:8px;border-left:4px solid {status_color};'>
            <b>Trip #{d.get("trip_code", d.get("trip_id", ""))}</b>
            <span style='color:#888;font-size:12px;margin-left:8px;'>
                {d.get("raised_by_name", "")} · {str(d.get("created_at", ""))[:10]}
            </span>
            <div style='font-size:13px;color:#555;margin-top:4px;'>{d.get("reason", "")}</div>
        </div>""", unsafe_allow_html=True)
        if d["status"] == "open":
            resolution = st.text_input("Resolution note", key=f"res_{d['id']}")
            if st.button("✅ Resolve", key=f"resolve_{d['id']}", type="primary"):
                result = api_patch(f"/admin/disputes/{d['id']}/resolve",
                                   {"resolution": resolution})
                if result:
                    st.success("Dispute resolved!")
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  SOS ALERTS
# ══════════════════════════════════════════════════════════════════════════════
def page_sos():
    page_title("🆘 SOS Alerts", "Emergency alerts from riders and drivers")
    if st.button("🔄 Refresh"):
        st.rerun()
    data = api_get("/admin/sos")
    if not data:
        st.error("❌ Could not load SOS alerts.")
        return
    alerts = data.get("sos_alerts", [])
    if not alerts:
        st.info("✅ No active SOS alerts.")
        return
    active   = [a for a in alerts if a["status"] == "active"]
    resolved = [a for a in alerts if a["status"] == "resolved"]
    c1, c2 = st.columns(2)
    with c1: st.markdown(metric("🔴 Active", str(len(active)), "", "red"), unsafe_allow_html=True)
    with c2: st.markdown(metric("✅ Resolved", str(len(resolved)), "", "green"), unsafe_allow_html=True)
    st.markdown("---")
    for a in alerts:
        status_color = "#EA4335" if a["status"] == "active" else "#34A853"
        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:14px 18px;
                    margin-bottom:8px;border-left:4px solid {status_color};'>
            <b>🆘 {a.get("raised_by_name", "Unknown")}</b>
            <span style='color:#888;font-size:12px;margin-left:8px;'>
                Trip #{a.get("trip_id", "—")} · {str(a.get("created_at", ""))[:16]}
            </span>
            <div style='font-size:12px;color:#555;margin-top:4px;'>
                📍 Lat: {a.get("lat", "—")} · Lng: {a.get("lng", "—")}
            </div>
            <span style='font-size:12px;color:{status_color};font-weight:600;'>
                {a["status"].upper()}
            </span>
        </div>""", unsafe_allow_html=True)
        if a["status"] == "active":
            if st.button("✅ Mark Resolved", key=f"sos_{a['id']}", type="primary"):
                result = api_patch(f"/admin/sos/{a['id']}/resolve")
                if result:
                    st.success("SOS resolved!")
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  CASH COLLECTION REPORT
# ══════════════════════════════════════════════════════════════════════════════
def page_cash_collection():
    page_title("💵 Cash Collection Report", "All cash collected by drivers")
    trip_data = api_get("/admin/trips", params={"limit": 500})
    if not trip_data:
        st.error("❌ Could not load trips.")
        return
    trips = trip_data.get("trips", [])
    cash_trips = [t for t in trips if t.get("payment_method") == "cash"]
    collected  = [t for t in cash_trips if t.get("cash_collected")]
    pending    = [t for t in cash_trips if not t.get("cash_collected") and t.get("status") == "completed"]
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric("Total Cash Trips", str(len(cash_trips))), unsafe_allow_html=True)
    with c2: st.markdown(metric("Collected", str(len(collected)), "", "green"), unsafe_allow_html=True)
    with c3: st.markdown(metric("Pending Collection", str(len(pending)), "", "amber"), unsafe_allow_html=True)
    total_cash = sum(t.get("actual_fare") or t.get("estimated_fare") or 0 for t in collected)
    with c4: st.markdown(metric("Total Collected", f"₹{total_cash:,.0f}", "", "green"), unsafe_allow_html=True)
    st.markdown("---")
    rows = [{"Trip Code": t.get("trip_code", ""),
             "Driver": (t.get("driver") or {}).get("name", "—"),
             "Rider": (t.get("rider") or {}).get("name", "—"),
             "Amount (₹)": t.get("actual_fare") or t.get("estimated_fare") or 0,
             "Collected": "✅" if t.get("cash_collected") else "⏳",
             "Date": str(t.get("completed_at") or t.get("requested_at") or "")[:10]}
            for t in cash_trips]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.download_button("📥 Download CSV", pd.DataFrame(rows).to_csv(index=False),
                       "cash_collection.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════════════
#  REFERRAL CONFIG
# ══════════════════════════════════════════════════════════════════════════════
def page_referral_config():
    page_title("🎁 Referral Config", "Set referral bonus amounts for riders and drivers")
    with st.form("referral_form"):
        c1, c2 = st.columns(2)
        with c1:
            referrer_bonus = st.number_input("Referrer Bonus (₹)", min_value=0.0, value=50.0, step=5.0,
                help="Amount given to person who referred")
            referee_bonus  = st.number_input("Referee Bonus (₹)", min_value=0.0, value=30.0, step=5.0,
                help="Amount given to new user who was referred")
        with c2:
            min_trips      = st.number_input("Min Trips to Unlock Bonus", min_value=1, value=1, step=1)
            is_active      = st.checkbox("Enable Referral Program", value=True)
        if st.form_submit_button("💾 Save", type="primary", use_container_width=True):
            result = api_patch("/admin/config/referral", {
                "referrer_bonus": referrer_bonus,
                "referee_bonus": referee_bonus,
                "min_trips": int(min_trips),
                "is_active": is_active
            })
            if result and "message" in result:
                st.success(result["message"])
            else:
                st.error(f"Failed: {result}")

# ══════════════════════════════════════════════════════════════════════════════
#  DELETE USER
# ══════════════════════════════════════════════════════════════════════════════
def page_delete_user():
    page_title("🗑️ Delete User", "Permanently delete rider or driver accounts")
    st.warning("⚠️ This action is permanent and cannot be undone!")
    data = api_get("/admin/users", params={"limit": 500})
    if not data:
        st.error("❌ Could not load users.")
        return
    users = data.get("users", [])
    search = st.text_input("🔍 Search by name or phone")
    if search:
        users = [u for u in users if search.lower() in u["full_name"].lower()
                 or search in str(u.get("phone", ""))]
    for u in users:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{u['full_name']}** — {u.get('phone', '')} — {u.get('role', '')}")
        with col2:
            if st.button("🗑️ Delete", key=f"del_{u['id']}", type="primary", use_container_width=True):
                result = api_delete(f"/admin/users/{u['id']}")
                if result and "message" in result:
                    st.success(f"✅ {u['full_name']} deleted!")
                    st.rerun()
                else:
                    st.error(f"Failed: {result}")

# ══════════════════════════════════════════════════════════════════════════════
#  EV VEHICLE STATS
# ══════════════════════════════════════════════════════════════════════════════
def page_ev_stats():
    page_title("⚡ EV Vehicle Stats", "Electric vehicle drivers vs non-EV")
    data = api_get("/admin/drivers")
    if not data:
        st.error("❌ Could not load drivers.")
        return
    drivers = data.get("drivers", [])
    ev      = [d for d in drivers if d.get("fuel_type") == "ev"]
    non_ev  = [d for d in drivers if d.get("fuel_type") != "ev"]
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(metric("Total Drivers", str(len(drivers))), unsafe_allow_html=True)
    with c2: st.markdown(metric("⚡ EV Drivers", str(len(ev)), "", "green"), unsafe_allow_html=True)
    with c3: st.markdown(metric("⛽ Non-EV Drivers", str(len(non_ev)), "", "amber"), unsafe_allow_html=True)
    st.markdown("---")
    if ev:
        fig = px.pie(values=[len(ev), len(non_ev)], names=["EV", "Non-EV"],
                     title="EV vs Non-EV Drivers",
                     color_discrete_sequence=["#34A853", "#EA4335"])
        st.plotly_chart(fig, use_container_width=True)
    rows = [{"Name": d["full_name"], "Phone": d.get("phone", ""),
             "Vehicle Type": d.get("vehicle_type", ""),
             "Fuel Type": d.get("fuel_type", ""),
             "Online": "🟢" if d["is_online"] else "⚫",
             "Trips": d.get("total_trips", 0)} for d in drivers]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  REVIEWS
# ══════════════════════════════════════════════════════════════════════════════
def page_reviews():
    page_title("⭐ Reviews", "Rider and driver ratings and comments")
    tab1, tab2 = st.tabs(["🚗 Driver Reviews", "👤 Rider Reviews"])

    with tab1:
        data = api_get("/admin/ratings", params={"role": "driver", "limit": 200})
        if not data:
            st.error("❌ Could not load driver reviews.")
            return
        ratings = data.get("ratings", [])
        if not ratings:
            st.info("No driver reviews yet.")
        else:
            total   = len(ratings)
            avg     = round(sum(r["score"] for r in ratings) / total, 2) if total > 0 else 0
            five    = sum(1 for r in ratings if r["score"] == 5)
            one     = sum(1 for r in ratings if r["score"] == 1)
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(metric("Total Reviews", str(total)), unsafe_allow_html=True)
            with c2: st.markdown(metric("Average Rating", f"⭐ {avg}", "", "green"), unsafe_allow_html=True)
            with c3: st.markdown(metric("5 Star", str(five), "", "green"), unsafe_allow_html=True)
            with c4: st.markdown(metric("1 Star", str(one), "", "red"), unsafe_allow_html=True)
            st.markdown("---")
            search = st.text_input("🔍 Search by driver name", key="drv_review_search")
            if search:
                ratings = [r for r in ratings if search.lower() in r["rated_name"].lower()]
            for r in ratings:
                stars = "⭐" * r["score"] + "☆" * (5 - r["score"])
                color = "#34A853" if r["score"] >= 4 else ("#FBBC04" if r["score"] == 3 else "#EA4335")
                st.markdown(f"""
                <div style='background:white;border-radius:10px;padding:14px 18px;
                            margin-bottom:8px;border-left:4px solid {color};
                            box-shadow:0 1px 6px rgba(0,0,0,0.04);'>
                    <div style='display:flex;justify-content:space-between;'>
                        <div>
                            <b>{r["rated_name"]}</b>
                            <span style='color:#888;font-size:12px;margin-left:8px;'>
                                rated by {r["rater_name"]}
                            </span>
                        </div>
                        <div style='font-size:18px;'>{stars}</div>
                    </div>
                    <div style='font-size:13px;color:#555;margin-top:6px;'>
                        {r.get("comment") or "<i>No comment</i>"}
                    </div>
                    <div style='font-size:11px;color:#aaa;margin-top:4px;'>
                        Trip #{r["trip_code"]} · {r["created_at"]}
                    </div>
                </div>""", unsafe_allow_html=True)

    with tab2:
        data = api_get("/admin/ratings", params={"role": "rider", "limit": 200})
        if not data:
            st.error("❌ Could not load rider reviews.")
            return
        ratings = data.get("ratings", [])
        if not ratings:
            st.info("No rider reviews yet.")
        else:
            total   = len(ratings)
            avg     = round(sum(r["score"] for r in ratings) / total, 2) if total > 0 else 0
            c1, c2 = st.columns(2)
            with c1: st.markdown(metric("Total Reviews", str(total)), unsafe_allow_html=True)
            with c2: st.markdown(metric("Average Rating", f"⭐ {avg}", "", "green"), unsafe_allow_html=True)
            st.markdown("---")
            search2 = st.text_input("🔍 Search by rider name", key="rider_review_search")
            if search2:
                ratings = [r for r in ratings if search2.lower() in r["rated_name"].lower()]
            for r in ratings:
                stars = "⭐" * r["score"] + "☆" * (5 - r["score"])
                color = "#34A853" if r["score"] >= 4 else ("#FBBC04" if r["score"] == 3 else "#EA4335")
                st.markdown(f"""
                <div style='background:white;border-radius:10px;padding:14px 18px;
                            margin-bottom:8px;border-left:4px solid {color};
                            box-shadow:0 1px 6px rgba(0,0,0,0.04);'>
                    <div style='display:flex;justify-content:space-between;'>
                        <div>
                            <b>{r["rated_name"]}</b>
                            <span style='color:#888;font-size:12px;margin-left:8px;'>
                                rated by {r["rater_name"]}
                            </span>
                        </div>
                        <div style='font-size:18px;'>{stars}</div>
                    </div>
                    <div style='font-size:13px;color:#555;margin-top:6px;'>
                        {r.get("comment") or "<i>No comment</i>"}
                    </div>
                    <div style='font-size:11px;color:#aaa;margin-top:4px;'>
                        Trip #{r["trip_code"]} · {r["created_at"]}
                    </div>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  COMMISSION & PAYMENT BREAKDOWN
# ══════════════════════════════════════════════════════════════════════════════
def page_commission():
    page_title("💰 Commission & Payment Breakdown", "Driver earnings, company commission, promo payouts")
    if st.button("🔄 Refresh"):
        st.rerun()

    trip_data = api_get("/admin/trips", params={"limit": 500})
    if not trip_data:
        st.error("❌ Could not load trips.")
        return
    trips = [t for t in trip_data.get("trips", []) if t.get("status") == "completed"]

    total_fare       = sum(t.get("actual_fare") or 0 for t in trips)
    total_commission = sum(t.get("platform_fee") or 0 for t in trips)
    total_earnings   = sum(t.get("driver_earnings") or 0 for t in trips)
    total_promo      = sum(t.get("promo_discount") or 0 for t in trips)
    cash_trips       = [t for t in trips if t.get("payment_method") == "cash"]
    online_trips     = [t for t in trips if t.get("payment_method") != "cash"]

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric("Total Revenue", f"₹{total_fare:,.0f}", "", "green"), unsafe_allow_html=True)
    with c2: st.markdown(metric("Company Commission", f"₹{total_commission:,.0f}", "", "purple"), unsafe_allow_html=True)
    with c3: st.markdown(metric("Driver Earnings", f"₹{total_earnings:,.0f}", "", "blue"), unsafe_allow_html=True)
    with c4: st.markdown(metric("Promo Discounts", f"₹{total_promo:,.0f}", "", "amber"), unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1: st.markdown(metric("Cash Trips", str(len(cash_trips))), unsafe_allow_html=True)
    with c2: st.markdown(metric("Online Trips", str(len(online_trips))), unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 Trip Payment Details")

    rows = []
    for t in trips:
        actual_fare    = t.get("actual_fare") or 0
        promo_discount = t.get("promo_discount") or 0
        commission     = t.get("platform_fee") or 0
        driver_earn    = t.get("driver_earnings") or 0
        payment_method = t.get("payment_method", "")
        net_rider_fare = max(0, actual_fare - promo_discount)

        if payment_method == "cash":
            cash_collected   = net_rider_fare
            company_pays     = max(0, driver_earn - cash_collected)
        else:
            cash_collected   = 0
            company_pays     = 0

        rows.append({
            "Trip Code"        : t.get("trip_code", ""),
            "Driver"           : (t.get("driver") or {}).get("name", "—"),
            "Rider"            : (t.get("rider") or {}).get("name", "—"),
            "Actual Fare (₹)"  : actual_fare,
            "Promo Discount (₹)": promo_discount,
            "Promo Code"       : t.get("promo_code") or "—",
            "Net Rider Pays (₹)": net_rider_fare,
            "Commission (₹)"   : commission,
            "Driver Earns (₹)" : driver_earn,
            "Payment"          : payment_method,
            "Cash Collected (₹)": cash_collected,
            "Company Pays Driver (₹)": company_pays,
            "Date"             : str(t.get("completed_at") or "")[:10],
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, height=400, hide_index=True)
    st.download_button("📥 Download CSV", df.to_csv(index=False),
                       "commission_report.csv", "text/csv", type="primary")

# ══════════════════════════════════════════════════════════════════════════════
#  CANCELLATION REASONS
# ══════════════════════════════════════════════════════════════════════════════
def page_cancellation_reasons():
    page_title("❌ Cancellation Reasons", "Why trips were cancelled")
    if st.button("🔄 Refresh"):
        st.rerun()

    trip_data = api_get("/admin/trips", params={"limit": 500, "status": "cancelled"})
    if not trip_data:
        st.error("❌ Could not load trips.")
        return
    trips = trip_data.get("trips", [])
    if not trips:
        st.info("No cancelled trips yet.")
        return

    by_rider  = [t for t in trips if t.get("cancelled_by") == "rider"]
    by_driver = [t for t in trips if t.get("cancelled_by") == "driver"]
    by_system = [t for t in trips if t.get("cancelled_by") == "system"]

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric("Total Cancelled", str(len(trips))), unsafe_allow_html=True)
    with c2: st.markdown(metric("By Rider", str(len(by_rider)), "", "amber"), unsafe_allow_html=True)
    with c3: st.markdown(metric("By Driver", str(len(by_driver)), "", "red"), unsafe_allow_html=True)
    with c4: st.markdown(metric("By System", str(len(by_system)), "", "purple"), unsafe_allow_html=True)

    st.markdown("---")

    # Pie chart
    import plotly.express as px
    fig = px.pie(
        values=[len(by_rider), len(by_driver), len(by_system)],
        names=["Rider", "Driver", "System"],
        title="Cancellation by Who",
        color_discrete_sequence=["#FBBC04", "#EA4335", "#7F77DD"]
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Cancellation Details")

    rows = [{"Trip Code"     : t.get("trip_code", ""),
             "Cancelled By"  : t.get("cancelled_by", "—"),
             "Reason"        : t.get("cancel_reason", "—"),
             "Rider"         : (t.get("rider") or {}).get("name", "—"),
             "Driver"        : (t.get("driver") or {}).get("name", "—"),
             "Vehicle"       : str(t.get("vehicle_type", "")),
             "Date"          : str(t.get("cancelled_at") or t.get("requested_at") or "")[:16]}
            for t in trips]

    df = pd.DataFrame(rows)
    cancelled_by_filter = st.selectbox("Filter by", ["All", "rider", "driver", "system"])
    if cancelled_by_filter != "All":
        df = df[df["Cancelled By"] == cancelled_by_filter]
    st.dataframe(df, use_container_width=True, height=400, hide_index=True)
    st.download_button("📥 Download CSV", df.to_csv(index=False),
                       "cancellation_reasons.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTER
# ══════════════════════════════════════════════════════════════════════════════
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "login_time" not in st.session_state:
    st.session_state.login_time = None

# Session timeout
if st.session_state.logged_in and st.session_state.login_time:
    elapsed = (datetime.now() - st.session_state.login_time).total_seconds() / 60
    if elapsed > SESSION_TIMEOUT_MINUTES:
        st.session_state.logged_in = False
        st.warning("⏰ Session expired. Please log in again.")

if not st.session_state.logged_in:
    _u = st.query_params.get("u", "")
    if _u and _u in USERS:
        st.session_state.logged_in  = True
        st.session_state.user        = USERS[_u]
        st.session_state.user_email  = _u
        st.session_state.login_time  = datetime.now()
        st.rerun()
    else:
        show_login()
else:
    page = show_sidebar()
    routing = {
        "Overview"               : page_overview,
        "Live Search Feed"       : page_live_search_feed,
        "Search Heatmap"         : page_search_heatmap,
        "Live Map"               : page_live_map,
        "Trip Tracking"          : page_trips,
        "Ride History"           : page_ride_history,
        "Send Notification"      : page_send_notification,
        "Schedule Notification"  : page_schedule_notification,
        "Broadcast History"      : page_broadcast_history,
        "Activate Promo"         : page_activate_promo,
        "Driver Online Log"      : page_driver_online_log,
        "Rider Onboarding"       : page_rider_onboarding,
        "Driver Document Upload" : page_driver_document_upload,
        "Driver Performance"     : page_driver_performance,
        "Driver Payments"        : page_driver_payments,
        "Vehicle Management"     : page_vehicle_mgmt,
        "Promotions"             : page_promotions,
        "Revenue Reports"        : page_revenue,
        "Notifications"          : page_notifications,
        "Pricing & Fees"         : page_pricing_config,
        "Block Management"       : page_block_management,
        "Cancellation Config"    : page_cancellation_config,
        "Wallet Management"      : page_wallet_management,
        "Withdrawal Requests"    : page_withdrawals,
        "Trip Disputes"          : page_disputes,
        "SOS Alerts"             : page_sos,
        "Cash Collection"        : page_cash_collection,
        "Referral Config"        : page_referral_config,
        "Delete User"            : page_delete_user,
        "EV Stats", "Reviews", "Commission Report", "Cancellation Reasons"               : page_ev_stats,
    }
    routing.get(page, page_overview)()
