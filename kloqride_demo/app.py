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
API_BASE           = os.getenv("API_BASE",            "https://kridebackend-production.up.railway.app")
ADMIN_PHONE        = os.getenv("ADMIN_PHONE",         "0000000000")
ADMIN_PASSWORD_API = os.getenv("ADMIN_PASSWORD_API",  "secret")

def get_admin_token():
    try:
        res = requests.post(
            f"{API_BASE}/auth/password/login",
            json={"phone": ADMIN_PHONE, "password": ADMIN_PASSWORD_API, "role": "rider"},
            timeout=10)
        if res.status_code == 200:
            return res.json().get("access_token", "")
    except Exception:
        return ""
    return ""

if "admin_token" not in st.session_state or not st.session_state.admin_token:
    st.session_state.admin_token = get_admin_token()

ADMIN_TOKEN = st.session_state.admin_token

def api_get(endpoint, params=None):
    token = st.session_state.get("admin_token", ADMIN_TOKEN)
    try:
        res = requests.get(f"{API_BASE}{endpoint}", params=params,
                           headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def api_post(endpoint, data=None):
    try:
        res = requests.post(f"{API_BASE}{endpoint}", json=data,
                            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, timeout=10)
        return res.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def api_patch(endpoint, data=None):
    try:
        res = requests.patch(f"{API_BASE}{endpoint}", json=data,
                             headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, timeout=10)
        return res.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def api_delete(endpoint):
    try:
        res = requests.delete(f"{API_BASE}{endpoint}",
                              headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, timeout=10)
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
        "Trip Tracking", "Ride History", "Send Notification", "Activate Promo",
        "Driver Online Log", "Rider Onboarding",
        "Driver Document Upload", "Driver Performance", "Driver Payments",
        "Vehicle Management", "Promotions", "Revenue Reports",
        "Notifications", "Pricing & Fees", "Block Management"
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
                result = api_post("/admin/notifications/broadcast",
                                  {"title": title, "message": message, "role": role_map.get(audience)})
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
    page_title("⚙️ Pricing & Fees")
    data = api_get("/pricing/")
    if not data:
        st.error("❌ Could not load pricing.")
        return
    pricing = data.get("pricing",[])
    surge   = data.get("surge",{})
    c1,c2 = st.columns(2)
    with c1: st.markdown(metric("Commission %", f"{surge.get('commission_pct',10)}%","","purple"), unsafe_allow_html=True)
    with c2: st.markdown(metric("Surge Active", "🔴 ON" if surge.get("manual_surge_active") else "⚫ OFF","","amber"), unsafe_allow_html=True)
    st.markdown("---")
    if pricing:
        st.dataframe(pd.DataFrame(pricing), use_container_width=True, hide_index=True)

def page_promotions():
    page_title("🎁 Promotions")
    st.info("Promotions are managed locally. Use Activate Promo to create new ones.")

def page_activate_promo():
    page_title("🏷️ Activate Promo Code")
    if "active_promos" not in st.session_state:
        st.session_state.active_promos = []
    with st.form("promo_form", clear_on_submit=True):
        c1,c2,c3 = st.columns(3)
        code      = c1.text_input("Code").strip().upper()
        disc_type = c2.selectbox("Type", ["Percentage","Flat"])
        disc_val  = c3.number_input("Value", min_value=1, value=10)
        auto      = st.checkbox("Auto-Apply on booking")
        if st.form_submit_button("🚀 Activate", type="primary"):
            if code:
                st.session_state.active_promos.append({
                    "code":code,"discount":f"{disc_val}%" if disc_type=="Percentage" else f"₹{disc_val}",
                    "auto_apply":auto,"created":datetime.now().strftime("%d %b %Y %H:%M")})
                st.success(f"✅ {code} activated!")
    for p in st.session_state.active_promos:
        st.markdown(f"**{p['code']}** — {p['discount']} {'⚡ AUTO' if p['auto_apply'] else '✋ MANUAL'} · {p['created']}")

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
    }
    routing.get(page, page_overview)()
