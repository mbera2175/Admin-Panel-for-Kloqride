import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE           = os.getenv("API_BASE", "http://localhost:8000")
ADMIN_EMAIL_API    = os.getenv("ADMIN_EMAIL_API", "")
ADMIN_PASSWORD_API = os.getenv("ADMIN_PASSWORD_API", "")
ADMIN_EMAIL        = os.getenv("ADMIN_EMAIL", "")
ADMIN_PASSWORD     = os.getenv("ADMIN_PASSWORD", "")
SESSION_TIMEOUT    = int(os.getenv("SESSION_TIMEOUT_MINUTES", "120"))

BLUE="#FF6B00"; GREEN="#34A853"; AMBER="#FBBC04"; RED="#EA4335"; PURPLE="#7F77DD"

def get_admin_token():
    try:
        res = requests.post(f"{API_BASE}/auth/admin/login",
            json={"email": ADMIN_EMAIL_API, "password": ADMIN_PASSWORD_API}, timeout=10)
        if res.status_code == 200:
            return res.json().get("token", "")
    except: return ""
    return ""

if "admin_token" not in st.session_state or not st.session_state.get("admin_token"):
    st.session_state.admin_token = get_admin_token()

def _headers():
    return {"Authorization": f"Bearer {st.session_state.get('admin_token','')}"}

def api_get(ep, params=None):
    try:
        r = requests.get(f"{API_BASE}{ep}", params=params, headers=_headers(), timeout=15)
        if r.status_code == 200: return r.json()
        return None
    except Exception as e:
        st.error(f"API Error: {e}"); return None

def api_post(ep, data=None):
    try:
        r = requests.post(f"{API_BASE}{ep}", json=data, headers=_headers(), timeout=15)
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}"); return None

def api_patch(ep, data=None):
    try:
        r = requests.patch(f"{API_BASE}{ep}", json=data, headers=_headers(), timeout=15)
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}"); return None

def api_delete(ep):
    try:
        r = requests.delete(f"{API_BASE}{ep}", headers=_headers(), timeout=15)
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}"); return None

st.set_page_config(page_title="KRide Admin", page_icon="🚖", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""<style>
footer{visibility:hidden}
.mc{background:white;border-radius:12px;padding:16px 20px;border-left:4px solid #FF6B00;
    box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:8px}
.mc.g{border-left-color:#34A853}.mc.a{border-left-color:#FBBC04}
.mc.r{border-left-color:#EA4335}.mc.p{border-left-color:#7F77DD}
.ml{font-size:11px;color:#888;font-weight:500;text-transform:uppercase;letter-spacing:.5px}
.mv{font-size:1.7rem;font-weight:700;color:#111;margin:2px 0}
.md{font-size:12px}.up{color:#34A853}.dn{color:#EA4335}
section[data-testid="stSidebar"]{background:#F2F2F2}
</style>""", unsafe_allow_html=True)

def metric(label, value, delta="", color="blue"):
    cls={"blue":"","green":"g","amber":"a","red":"r","purple":"p"}[color]
    d=f'<div class="md {"up" if "+" in str(delta) else "dn"}">{delta}</div>' if delta else '<div class="md">&nbsp;</div>'
    return f'<div class="mc {cls}"><div class="ml">{label}</div><div class="mv">{value}</div>{d}</div>'

def page_title(t, sub=""):
    s=f"<div style='font-size:13px;color:rgba(255,255,255,.9);margin-top:6px'>{sub}</div>" if sub else ""
    st.markdown(f"""<div style='background:#E85F00;border-radius:10px;padding:18px 22px;
        margin-bottom:16px;box-shadow:0 4px 6px rgba(0,0,0,.1)'>
        <div style='font-size:1.6rem;font-weight:800;color:#fff'>{t}</div>{s}</div>""",
        unsafe_allow_html=True)

USERS={ADMIN_EMAIL:{"password":ADMIN_PASSWORD,"name":"Admin","role":"Admin"}}

def show_login():
    c1,c2,c3=st.columns([1,1.3,1])
    with c2:
        st.markdown("""<div style='text-align:center;margin-top:50px;margin-bottom:24px'>
        <div style='font-size:3rem;font-weight:900;color:#FF6B00'>🚖 KRide</div>
        <div style='color:#888;font-size:.95rem;margin-top:4px'>Admin Dashboard</div>
        </div>""", unsafe_allow_html=True)
        with st.form("lf"):
            st.markdown("#### Sign in")
            email=st.text_input("Email")
            pwd=st.text_input("Password",type="password")
            if st.form_submit_button("Login →",use_container_width=True,type="primary"):
                if email in USERS and USERS[email]["password"]==pwd:
                    st.session_state.logged_in=True
                    st.session_state.user=USERS[email]
                    st.session_state.login_time=datetime.now()
                    st.rerun()
                else:
                    st.error("❌ Wrong email or password.")

PAGES=[
    "📊 Overview","🔴 Live Feed","🔥 Heatmap","🗺️ Live Map",
    "🛣️ Trips","🧾 Ride History","👥 Drivers","📄 Documents",
    "📈 Performance","💸 Driver Payments","🚗 Vehicles",
    "🧑 Riders","🔒 Block Management","⚙️ Pricing",
    "🎁 Promotions","🏷️ Create Promo","💰 Revenue",
    "🔔 Alerts","📢 Send Notification","📅 Schedule Notification",
    "📬 Broadcast History","⚙️ Cancellation Config","💳 Wallets",
    "💸 Withdrawals","⚖️ Disputes","🆘 SOS","💵 Cash Collection",
    "🎁 Referral Config","🗑️ Delete User","⚡ EV Stats",
    "⭐ Reviews","💰 Commission","❌ Cancellations"
]

def show_sidebar():
    user=st.session_state.user
    st.sidebar.markdown(f"""<div style='padding:10px 0 16px'>
    <div style='font-size:1.4rem;font-weight:900;color:#FF6B00'>🚖 KRide</div>
    <div style='margin-top:12px;padding:10px 12px;background:#FFF0E6;border-radius:8px'>
    <div style='font-size:13px;font-weight:600'>{user['name']}</div>
    <div style='font-size:11px;color:#888'>{user['role']}</div>
    </div></div>""", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    if "nav" not in st.session_state: st.session_state.nav="📊 Overview"
    for p in PAGES:
        t="primary" if st.session_state.nav==p else "secondary"
        if st.sidebar.button(p,type=t,use_container_width=True,key=f"n_{p}"):
            st.session_state.nav=p; st.rerun()
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"<div style='font-size:11px;color:#aaa;text-align:center'>{datetime.now().strftime('%d %b %Y %H:%M')}</div>",unsafe_allow_html=True)
    if st.sidebar.button("Logout",use_container_width=True):
        st.session_state.logged_in=False; st.rerun()
    return st.session_state.nav

def page_overview():
    page_title("📊 Overview", datetime.now().strftime('%A, %d %B %Y'))
    data = api_get("/admin/overview")
    if not data: st.error("❌ Cannot connect to backend."); return
    u=data.get("users",{}); t=data.get("trips",{}); r=data.get("revenue",{})
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(metric("Total Riders",str(u.get("riders",0))),unsafe_allow_html=True)
    with c2: st.markdown(metric("Total Drivers",str(u.get("drivers",0)),"","green"),unsafe_allow_html=True)
    with c3: st.markdown(metric("Online Drivers",str(u.get("active_drivers",0)),"","amber"),unsafe_allow_html=True)
    with c4: st.markdown(metric("Pending Approval",str(u.get("pending_approval",0)),"","red"),unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(metric("Total Trips",str(t.get("total",0))),unsafe_allow_html=True)
    with c2: st.markdown(metric("Completed",str(t.get("completed",0)),"","green"),unsafe_allow_html=True)
    with c3: st.markdown(metric("Active Now",str(t.get("active",0)),"","amber"),unsafe_allow_html=True)
    with c4: st.markdown(metric("Cancelled",str(t.get("cancelled",0)),"","red"),unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(metric("Today Trips",str(t.get("today",0))),unsafe_allow_html=True)
    with c2: st.markdown(metric("Today Revenue",f"₹{r.get('today',0):,.2f}","","green"),unsafe_allow_html=True)
    with c3: st.markdown(metric("Total Revenue",f"₹{r.get('total',0):,.2f}","","green"),unsafe_allow_html=True)
    with c4: st.markdown(metric("Total Commission",f"₹{r.get('total_commission',0):,.2f}","","purple"),unsafe_allow_html=True)
    rev=api_get("/admin/revenue",params={"days":30})
    if rev and rev.get("daily_breakdown"):
        daily=pd.DataFrame(rev["daily_breakdown"])
        c1,c2=st.columns(2)
        with c1:
            fig=px.line(daily,x="date",y="revenue",title="Revenue - Last 30 Days",markers=True,color_discrete_sequence=[BLUE])
            fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(fig,use_container_width=True)
        with c2:
            fig=px.bar(daily,x="date",y=["trips","commission"],title="Trips & Commission",
                color_discrete_map={"trips":GREEN,"commission":PURPLE},barmode="group")
            fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(fig,use_container_width=True)

def page_live_feed():
    page_title("🔴 Live Feed","Real-time ride requests")
    if st.button("🔄 Refresh",use_container_width=False): st.rerun()
    data=api_get("/admin/trips",params={"limit":200})
    if not data: st.error("❌ Cannot load trips."); return
    trips=data.get("trips",[])
    total=len(trips)
    completed=sum(1 for t in trips if t["status"]=="completed")
    searching=sum(1 for t in trips if t["status"]=="requested")
    active=sum(1 for t in trips if t["status"] in ["accepted","arrived","started"])
    cancelled=sum(1 for t in trips if t["status"]=="cancelled")
    c1,c2,c3,c4,c5=st.columns(5)
    with c1: st.markdown(metric("Total",str(total)),unsafe_allow_html=True)
    with c2: st.markdown(metric("Searching",str(searching),"","amber"),unsafe_allow_html=True)
    with c3: st.markdown(metric("Active",str(active),"","green"),unsafe_allow_html=True)
    with c4: st.markdown(metric("Completed",str(completed),"","green"),unsafe_allow_html=True)
    with c5: st.markdown(metric("Cancelled",str(cancelled),"","red"),unsafe_allow_html=True)
    st.markdown("---")
    c1,c2=st.columns(2)
    with c1: s_f=st.selectbox("Filter Status",["All","requested","accepted","arrived","started","completed","cancelled"])
    with c2: search=st.text_input("Search by trip code or rider name")
    filtered=[t for t in trips if s_f=="All" or t["status"]==s_f]
    if search:
        filtered=[t for t in filtered if
            search.lower() in str(t.get("trip_code","")).lower() or
            search.lower() in str((t.get("rider") or {}).get("name","")).lower()]
    status_icon={"requested":"🟡 Searching","accepted":"🟢 Accepted","arrived":"🔵 Arrived","started":"🚗 On Trip","completed":"✅ Completed","cancelled":"❌ Cancelled"}
    rows=[]
    for t in filtered:
        rider=t.get("rider") or {}
        driver=t.get("driver") or {}
        fare=t.get("actual_fare") or t.get("estimated_fare") or 0
        s=t.get("status","")
        # Get dispatch logs for this trip
        logs=api_get(f"/admin/trips/{t['id']}/dispatch-logs")
        log_list=logs.get("logs",[]) if logs else []
        notified_count=len(log_list)
        notified_drivers=", ".join([f"{l['driver_name']} ({l['driver_phone']})" for l in log_list]) if log_list else "—"
        accepted_driver=next((l for l in log_list if l["status"]=="accepted"),None)
        rows.append({
            "Trip Code"          : t.get("trip_code",""),
            "Date"               : str(t.get("requested_at",""))[:16],
            "Rider Name"         : rider.get("name","—"),
            "Rider Phone"        : rider.get("phone","—"),
            "Drivers Notified"   : notified_count,
            "Notified Drivers"   : notified_drivers,
            "Accepted By"        : driver.get("name","—") if driver else "—",
            "Driver Phone"       : driver.get("phone","—") if driver else "—",
            "Status"             : status_icon.get(s,s.upper()),
            "Pickup"             : str(t.get("pickup_address",""))[:40],
            "Drop"               : str(t.get("drop_address",""))[:40],
            "Fare (Rs.)"         : round(fare,0),
            "Payment"            : str(t.get("payment_method","")),
        })
    if rows:
        df=pd.DataFrame(rows)
        st.dataframe(df,use_container_width=True,height=550,hide_index=True)
        st.download_button("📥 Download CSV",df.to_csv(index=False),"live_feed.csv","text/csv")
    else:
        st.info("No trips found.")

def page_heatmap():
    page_title("🔥 Search Heatmap","Pickup demand locations")
    data=api_get("/admin/trips",params={"limit":500})
    if not data: st.error("❌ Cannot load data."); return
    trips=data.get("trips",[])
    pts=[[t["pickup_lat"],t["pickup_lng"]] for t in trips if t.get("pickup_lat") and t.get("pickup_lng")]
    clat=sum(p[0] for p in pts)/len(pts) if pts else 23.23
    clng=sum(p[1] for p in pts)/len(pts) if pts else 87.85
    m=folium.Map(location=[clat,clng],zoom_start=12,tiles="CartoDB dark_matter")
    if pts: HeatMap(pts,radius=15,blur=10).add_to(m)
    st.info(f"📍 {len(pts)} pickup points from {len(trips)} trips")
    st_folium(m,width=None,height=550,use_container_width=True)

def page_live_map():
    page_title("🗺️ Live Map","Driver GPS locations")
    if st.button("🔄 Refresh"): st.rerun()
    data=api_get("/admin/drivers")
    if not data: st.error("❌ Cannot load data."); return
    drivers=data.get("drivers",[])
    located=[d for d in drivers if d.get("current_lat") and d.get("current_lng")]
    online=[d for d in drivers if d["is_online"]]
    on_trip=[d for d in drivers if d.get("is_on_trip")]
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(metric("On Map",str(len(located))),unsafe_allow_html=True)
    with c2: st.markdown(metric("Online",str(len(online)),"","green"),unsafe_allow_html=True)
    with c3: st.markdown(metric("On Trip",str(len(on_trip)),"","purple"),unsafe_allow_html=True)
    with c4: st.markdown(metric("Offline",str(len(drivers)-len(online)),"","red"),unsafe_allow_html=True)
    clat=sum(d["current_lat"] for d in located)/len(located) if located else 23.23
    clng=sum(d["current_lng"] for d in located)/len(located) if located else 87.85
    m=folium.Map(location=[clat,clng],zoom_start=12)
    for d in located:
        color="blue" if d.get("is_on_trip") else ("green" if d["is_online"] else "gray")
        folium.Marker([d["current_lat"],d["current_lng"]],
            tooltip=f"{d['full_name']} — {'On Trip' if d.get('is_on_trip') else ('Online' if d['is_online'] else 'Offline')}",
            icon=folium.Icon(color=color,icon="car",prefix="fa")).add_to(m)
    st_folium(m,width=None,height=500,use_container_width=True)

def page_trips():
    page_title("🛣️ Trip Tracking")
    data=api_get("/admin/trips",params={"limit":200})
    if not data: st.error("❌ Cannot load trips."); return
    trips=data.get("trips",[])
    df=pd.DataFrame(trips)
    if df.empty: st.info("No trips yet."); return
    df["Rider"]=df["rider"].apply(lambda x: x["name"] if x else "—")
    df["Driver"]=df["driver"].apply(lambda x: x["name"] if x else "—")
    df["Fare"]=df["actual_fare"].fillna(df["estimated_fare"])
    df["Date"]=df["requested_at"].apply(lambda x: str(x)[:10])
    comp=df[df["status"]=="completed"]
    c1,c2,c3,c4,c5=st.columns(5)
    with c1: st.markdown(metric("Total",str(len(df))),unsafe_allow_html=True)
    with c2: st.markdown(metric("Completed",str(len(comp)),"","green"),unsafe_allow_html=True)
    with c3: st.markdown(metric("Cancelled",str(len(df[df["status"]=="cancelled"])),"","red"),unsafe_allow_html=True)
    with c4: st.markdown(metric("Revenue",f"₹{comp['Fare'].sum():,.0f}","","green"),unsafe_allow_html=True)
    with c5: st.markdown(metric("Avg Fare",f"₹{comp['Fare'].mean():.0f}" if len(comp)>0 else "₹0"),unsafe_allow_html=True)
    st.markdown("---")
    s_f=st.selectbox("Status",["All","completed","cancelled","requested","accepted","started"])
    filtered=df if s_f=="All" else df[df["status"]==s_f]
    cols=[c for c in ["trip_code","Date","Rider","Driver","vehicle_type","pickup_address","drop_address","Fare","status","payment_method","cancel_reason","cancelled_by"] if c in filtered.columns]
    st.dataframe(filtered[cols].reset_index(drop=True),use_container_width=True,height=400)
    st.download_button("📥 Download CSV",filtered.to_csv(index=False),"trips.csv","text/csv",type="primary")

def page_ride_history():
    page_title("🧾 Ride History","Per rider trip history")
    data=api_get("/admin/users",params={"limit":200})
    if not data: st.error("❌ Cannot load users."); return
    users=[u for u in data.get("users",[]) if u.get("role")=="rider"]
    names={u["id"]:f"{u['full_name']} ({u.get('phone','')})" for u in users}
    sel=st.selectbox("Select Rider",["-- Select --"]+list(names.values()))
    if sel=="-- Select --": return
    uid=[k for k,v in names.items() if v==sel]
    if not uid: return
    trips=api_get("/admin/trips",params={"limit":200})
    if not trips: return
    rider_trips=[t for t in trips.get("trips",[]) if t.get("rider") and t["rider"].get("name","") in sel]
    if not rider_trips: st.info("No trips found for this rider."); return
    comp=sum(1 for t in rider_trips if t["status"]=="completed")
    total_spend=sum((t.get("actual_fare") or t.get("estimated_fare") or 0) for t in rider_trips if t["status"]=="completed")
    c1,c2,c3=st.columns(3)
    with c1: st.markdown(metric("Total Trips",str(len(rider_trips))),unsafe_allow_html=True)
    with c2: st.markdown(metric("Completed",str(comp),"","green"),unsafe_allow_html=True)
    with c3: st.markdown(metric("Total Spend",f"₹{total_spend:,.0f}","","green"),unsafe_allow_html=True)
    rows=[{"Trip Code":t.get("trip_code",""),"Status":t["status"],
           "From":t.get("pickup_address",""),"To":t.get("drop_address",""),
           "Fare":t.get("actual_fare") or t.get("estimated_fare") or 0,
           "Payment":str(t.get("payment_method","")),
           "Date":str(t.get("requested_at",""))[:10]} for t in rider_trips]
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

def page_drivers():
    page_title("👥 Driver Management")
    data=api_get("/admin/drivers")
    if not data: st.error("❌ Cannot load drivers."); return
    drivers=data.get("drivers",[])
    online=sum(1 for d in drivers if d["is_online"])
    approved=sum(1 for d in drivers if d["is_approved"])
    pending=sum(1 for d in drivers if not d["is_approved"])
    blocked=sum(1 for d in drivers if d.get("is_blocked"))
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(metric("Total",str(len(drivers))),unsafe_allow_html=True)
    with c2: st.markdown(metric("Online",str(online),"","green"),unsafe_allow_html=True)
    with c3: st.markdown(metric("Pending",str(pending),"","amber"),unsafe_allow_html=True)
    with c4: st.markdown(metric("Blocked",str(blocked),"","red"),unsafe_allow_html=True)
    st.markdown("---")
    search=st.text_input("🔍 Search by name or phone")
    filtered=[d for d in drivers if not search or search.lower() in d["full_name"].lower() or search in str(d.get("phone",""))]
    for d in filtered:
        status_color="#34A853" if d["is_online"] else "#ccc"
        approved_color="#34A853" if d["is_approved"] else "#FBBC04"
        block_color="#EA4335" if d.get("is_blocked") else "#34A853"
        st.markdown(f"""<div style='background:white;border-radius:10px;padding:14px 18px;
            margin-bottom:8px;border-left:4px solid {status_color};
            box-shadow:0 1px 6px rgba(0,0,0,.04)'>
            <div style='display:flex;justify-content:space-between'>
                <div>
                    <b>{d['full_name']}</b>
                    <span style='color:#888;font-size:12px;margin-left:8px'>{d.get("phone","")}</span>
                    <div style='font-size:12px;color:#555;margin-top:2px'>
                        {d.get("vehicle_type","")} · {d.get("fuel_type","")} ·
                        ⭐{d.get("avg_rating",0):.1f} · {d.get("total_trips",0)} trips
                    </div>
                </div>
                <div style='text-align:right;font-size:11px'>
                    <span style='color:{approved_color}'>{"✅ Approved" if d["is_approved"] else "⏳ Pending"}</span><br>
                    <span style='color:{block_color}'>{"🔴 Blocked" if d.get("is_blocked") else "🟢 Active"}</span>
                </div>
            </div></div>""", unsafe_allow_html=True)
        cols=st.columns(4)
        with cols[0]:
            if not d["is_approved"]:
                if st.button("✅ Approve",key=f"app_{d['id']}",type="primary",use_container_width=True):
                    r=api_patch(f"/admin/drivers/{d['id']}/approve")
                    if r: st.success("Approved!"); st.rerun()
        with cols[1]:
            if st.button("🔴 Block" if not d.get("is_blocked") else "🟢 Unblock",key=f"blk_{d['id']}",use_container_width=True):
                r=api_patch(f"/admin/drivers/{d['id']}/block",{"block": not d.get("is_blocked",False)})
                if r: st.rerun()
        with cols[2]:
            if st.button("🗑️ Delete",key=f"del_{d['id']}",use_container_width=True):
                r=api_delete(f"/admin/drivers/{d['id']}")
                if r: st.success("Deleted!"); st.rerun()

def page_documents():
    page_title("📄 Driver Documents","View and verify uploaded documents")
    data=api_get("/admin/drivers")
    if not data: st.error("❌ Cannot load drivers."); return
    drivers=data.get("drivers",[])
    search=st.text_input("🔍 Search driver")
    filtered=[d for d in drivers if not search or search.lower() in d["full_name"].lower()]
    for d in filtered[:20]:
        with st.expander(f"📋 {d['full_name']} — {d.get('phone','')}"):
            docs=api_get(f"/documents/{d['id']}")
            if docs:
                for doc in docs:
                    c1,c2=st.columns([3,1])
                    with c1: st.markdown(f"**{doc.get('doc_type','')}** — {doc.get('status','')}")
                    with c2:
                        if doc.get("file_url"):
                            st.markdown(f"[View]({doc['file_url']})")
            else:
                st.info("No documents uploaded yet.")

def page_performance():
    page_title("📈 Driver Performance","Ratings, trips and earnings")
    data=api_get("/admin/drivers")
    if not data: st.error("❌ Cannot load data."); return
    drivers=data.get("drivers",[])
    rows=[{"Name":d["full_name"],"Phone":d.get("phone",""),
           "Rating":d.get("avg_rating",0),"Trips":d.get("total_trips",0),
           "Earnings":d.get("total_earnings",0),"Online":"🟢" if d["is_online"] else "⚫",
           "Status":"Approved" if d["is_approved"] else "Pending",
           "Vehicle":d.get("vehicle_type","")} for d in drivers]
    df=pd.DataFrame(rows).sort_values("Trips",ascending=False)
    c1,c2,c3=st.columns(3)
    with c1:
        fig=px.bar(df.head(10),x="Name",y="Trips",title="Top 10 Drivers by Trips",color_discrete_sequence=[BLUE])
        fig.update_layout(plot_bgcolor="white",paper_bgcolor="white")
        st.plotly_chart(fig,use_container_width=True)
    with c2:
        fig=px.bar(df.head(10),x="Name",y="Rating",title="Top 10 by Rating",color_discrete_sequence=[GREEN])
        fig.update_layout(plot_bgcolor="white",paper_bgcolor="white")
        st.plotly_chart(fig,use_container_width=True)
    with c3:
        fig=px.bar(df.head(10),x="Name",y="Earnings",title="Top 10 Earnings (₹)",color_discrete_sequence=[AMBER])
        fig.update_layout(plot_bgcolor="white",paper_bgcolor="white")
        st.plotly_chart(fig,use_container_width=True)
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.download_button("📥 Download CSV",df.to_csv(index=False),"performance.csv","text/csv")

def page_driver_payments():
    page_title("💸 Driver Payments","Earnings and withdrawal requests")
    tab1,tab2=st.tabs(["💰 Earnings","💸 Withdrawals"])
    with tab1:
        data=api_get("/admin/drivers")
        if not data: st.error("❌ Cannot load data."); return
        drivers=data.get("drivers",[])
        total=sum(d.get("total_earnings",0) for d in drivers)
        st.markdown(metric("Total Driver Earnings",f"₹{total:,.2f}","","green"),unsafe_allow_html=True)
        rows=[{"Name":d["full_name"],"Phone":d.get("phone",""),
               "Total Earnings":d.get("total_earnings",0),
               "Wallet Balance":d.get("wallet_balance",0),
               "Total Trips":d.get("total_trips",0)} for d in drivers]
        df=pd.DataFrame(rows).sort_values("Total Earnings",ascending=False)
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.download_button("📥 Download CSV",df.to_csv(index=False),"earnings.csv","text/csv")
    with tab2:
        data=api_get("/admin/withdrawals")
        if not data: st.error("❌ Cannot load withdrawals."); return
        withdrawals=data.get("withdrawals",[])
        if not withdrawals: st.info("No withdrawal requests."); return
        for w in withdrawals:
            s_color={"pending":"#FBBC04","approved":"#34A853","rejected":"#EA4335"}.get(w["status"],"#ccc")
            st.markdown(f"""<div style='background:white;border-radius:10px;padding:14px 18px;
                margin-bottom:8px;border-left:4px solid {s_color}'>
                <b>{w.get("driver_name","Driver")}</b> — ₹{w.get("amount",0):,.2f}
                <span style='color:#888;font-size:12px;margin-left:8px'>
                    {w.get("method","")} · {w.get("upi_id") or w.get("account_number","")}
                </span>
                <span style='float:right;font-size:12px;color:{s_color};font-weight:600'>
                    {w["status"].upper()}
                </span></div>""", unsafe_allow_html=True)
            if w["status"]=="pending":
                c1,c2=st.columns(2)
                with c1:
                    if st.button("✅ Approve",key=f"apw_{w['id']}",type="primary",use_container_width=True):
                        r=api_patch(f"/admin/withdrawals/{w['id']}/approve")
                        if r: st.success("Approved!"); st.rerun()
                with c2:
                    if st.button("❌ Reject",key=f"rjw_{w['id']}",use_container_width=True):
                        r=api_patch(f"/admin/withdrawals/{w['id']}/reject")
                        if r: st.warning("Rejected."); st.rerun()

def page_vehicles():
    page_title("🚗 Vehicle Management")
    data=api_get("/admin/drivers")
    if not data: st.error("❌ Cannot load data."); return
    drivers=data.get("drivers",[])
    rows=[{"Driver":d["full_name"],"Phone":d.get("phone",""),
           "Vehicle Type":d.get("vehicle_type",""),"Fuel":d.get("fuel_type",""),
           "Brand":d.get("vehicle_brand",""),"Model":d.get("vehicle_model",""),
           "Color":d.get("vehicle_color",""),"RC":d.get("rc_number",""),
           "Approved":"✅" if d["is_approved"] else "⏳"} for d in drivers]
    df=pd.DataFrame(rows)
    v_filter=st.selectbox("Filter by Vehicle Type",["All"]+list(df["Vehicle Type"].unique()))
    if v_filter!="All": df=df[df["Vehicle Type"]==v_filter]
    f_filter=st.selectbox("Filter by Fuel",["All"]+list(df["Fuel"].unique()))
    if f_filter!="All": df=df[df["Fuel"]==f_filter]
    st.dataframe(df,use_container_width=True,hide_index=True)
    c1,c2=st.columns(2)
    all_drivers=api_get("/admin/drivers")
    if all_drivers:
        d2=all_drivers.get("drivers",[])
        with c1:
            v_counts={}
            for d in d2: v=d.get("vehicle_type","unknown"); v_counts[v]=v_counts.get(v,0)+1
            fig=px.pie(values=list(v_counts.values()),names=list(v_counts.keys()),title="By Vehicle Type")
            st.plotly_chart(fig,use_container_width=True)
        with c2:
            f_counts={}
            for d in d2: f=d.get("fuel_type","unknown"); f_counts[f]=f_counts.get(f,0)+1
            fig=px.pie(values=list(f_counts.values()),names=list(f_counts.keys()),title="By Fuel Type",
                color_discrete_sequence=[GREEN,AMBER,BLUE,RED,PURPLE])
            st.plotly_chart(fig,use_container_width=True)

def page_riders():
    page_title("🧑 Rider Management")
    data=api_get("/admin/users",params={"limit":500})
    if not data: st.error("❌ Cannot load users."); return
    users=[u for u in data.get("users",[]) if u.get("role")=="rider"]
    search=st.text_input("🔍 Search by name or phone")
    if search: users=[u for u in users if search.lower() in u["full_name"].lower() or search in str(u.get("phone",""))]
    c1,c2=st.columns(2)
    with c1: st.markdown(metric("Total Riders",str(len(users))),unsafe_allow_html=True)
    with c2: st.markdown(metric("Total Wallet",f"₹{sum(u.get('wallet_balance',0) for u in users):,.2f}","","green"),unsafe_allow_html=True)
    st.markdown("---")
    for u in users[:50]:
        c1,c2,c3=st.columns([4,1,1])
        with c1:
            st.markdown(f"""<div style='padding:8px 0'>
                <b>{u['full_name']}</b>
                <span style='color:#888;font-size:12px;margin-left:8px'>{u.get("phone","")}</span>
                <div style='font-size:12px;color:#555'>
                    Wallet: ₹{u.get("wallet_balance",0):.2f} ·
                    Trips: {u.get("total_trips",0)} ·
                    Joined: {str(u.get("created_at",""))[:10]}
                </div></div>""", unsafe_allow_html=True)
        with c2:
            if st.button("🔴 Block",key=f"blkr_{u['id']}",use_container_width=True):
                r=api_patch(f"/admin/riders/{u['id']}/block",{"block":True})
                if r: st.rerun()
        with c3:
            if st.button("🟢 Unblock",key=f"ublkr_{u['id']}",use_container_width=True):
                r=api_patch(f"/admin/riders/{u['id']}/block",{"block":False})
                if r: st.rerun()

def page_block():
    page_title("🔒 Block Management","Block and unblock riders and drivers")
    tab1,tab2=st.tabs(["👤 Riders","🚗 Drivers"])
    with tab1:
        data=api_get("/admin/users",params={"limit":500})
        if not data: st.error("❌ Cannot load."); return
        users=[u for u in data.get("users",[]) if u.get("role")=="rider"]
        blocked=[u for u in users if u.get("is_blocked")]
        st.markdown(metric("Blocked Riders",str(len(blocked)),"","red"),unsafe_allow_html=True)
        search=st.text_input("🔍 Search",key="block_rider_search")
        if search: users=[u for u in users if search.lower() in u["full_name"].lower() or search in str(u.get("phone",""))]
        for u in users[:30]:
            c1,c2,c3=st.columns([4,1,1])
            with c1: st.markdown(f"**{u['full_name']}** — {u.get('phone','')} {'🔴' if u.get('is_blocked') else '🟢'}")
            with c2:
                if st.button("Block",key=f"br_{u['id']}",use_container_width=True):
                    api_patch(f"/admin/riders/{u['id']}/block",{"block":True}); st.rerun()
            with c3:
                if st.button("Unblock",key=f"ubr_{u['id']}",use_container_width=True):
                    api_patch(f"/admin/riders/{u['id']}/block",{"block":False}); st.rerun()
    with tab2:
        data=api_get("/admin/drivers")
        if not data: st.error("❌ Cannot load."); return
        drivers=data.get("drivers",[])
        blocked=[d for d in drivers if d.get("is_blocked")]
        st.markdown(metric("Blocked Drivers",str(len(blocked)),"","red"),unsafe_allow_html=True)
        search2=st.text_input("🔍 Search",key="block_driver_search")
        if search2: drivers=[d for d in drivers if search2.lower() in d["full_name"].lower() or search2 in str(d.get("phone",""))]
        for d in drivers[:30]:
            c1,c2,c3=st.columns([4,1,1])
            with c1: st.markdown(f"**{d['full_name']}** — {d.get('phone','')} {'🔴' if d.get('is_blocked') else '🟢'}")
            with c2:
                if st.button("Block",key=f"bd_{d['id']}",use_container_width=True):
                    api_patch(f"/admin/drivers/{d['id']}/block",{"block":True}); st.rerun()
            with c3:
                if st.button("Unblock",key=f"ubd_{d['id']}",use_container_width=True):
                    api_patch(f"/admin/drivers/{d['id']}/block",{"block":False}); st.rerun()

def page_pricing():
    page_title("⚙️ Pricing & Fees")
    data=api_get("/pricing/")
    if not data: st.error("❌ Cannot load pricing."); return
    pricings=data.get("pricings",[])
    tab1,tab2=st.tabs(["💰 Vehicle Pricing","📈 Surge Pricing"])
    with tab1:
        for p in pricings:
            with st.expander(f"🚗 {p.get('vehicle_type','')} — {p.get('city','')}"):
                with st.form(f"price_{p['id']}"):
                    c1,c2,c3,c4=st.columns(4)
                    with c1: base=st.number_input("Base Fare",value=float(p.get("base_fare",0)),key=f"bf_{p['id']}")
                    with c2: per_km=st.number_input("Per KM",value=float(p.get("per_km_fare",0)),key=f"km_{p['id']}")
                    with c3: per_min=st.number_input("Per Min",value=float(p.get("per_min_fare",0)),key=f"mn_{p['id']}")
                    with c4: min_fare=st.number_input("Min Fare",value=float(p.get("min_fare",0)),key=f"mf_{p['id']}")
                    comm=st.number_input("Commission %",value=float(p.get("commission_value",10)),key=f"cm_{p['id']}")
                    if st.form_submit_button("💾 Save",type="primary",use_container_width=True):
                        r=api_patch("/pricing/vehicle",{"pricing_id":p["id"],"base_fare":base,
                            "per_km_fare":per_km,"per_min_fare":per_min,"min_fare":min_fare,
                            "commission_value":comm})
                        if r: st.success("✅ Saved!")
    with tab2:
        surge=api_get("/pricing/")
        s=surge.get("surge",{}) if surge else {}
        with st.form("surge_form"):
            st.subheader("Manual Surge")
            c1,c2=st.columns(2)
            with c1: manual_active=st.checkbox("Enable Manual Surge",value=s.get("manual_surge_active",False))
            with c2: manual_mult=st.number_input("Multiplier",value=float(s.get("manual_surge_multiplier",1.5)),min_value=1.0,step=0.1)
            st.subheader("Auto Surge")
            c1,c2=st.columns(2)
            with c1: auto_active=st.checkbox("Enable Auto Surge",value=s.get("auto_surge_active",False))
            with c2:
                auto_thresh=st.number_input("Driver Threshold",value=int(s.get("auto_surge_threshold",5)),min_value=1)
                auto_mult=st.number_input("Auto Multiplier",value=float(s.get("auto_surge_multiplier",1.3)),min_value=1.0,step=0.1)
            if st.form_submit_button("💾 Save Surge",type="primary",use_container_width=True):
                r=api_patch("/pricing/surge",{"manual_surge_active":manual_active,
                    "manual_surge_multiplier":manual_mult,"auto_surge_active":auto_active,
                    "auto_surge_threshold":auto_thresh,"auto_surge_multiplier":auto_mult})
                if r: st.success("✅ Surge settings saved!")

def page_promotions():
    page_title("🎁 Promotions","Manage promo codes")
    if st.button("🔄 Refresh"): st.rerun()
    data=api_get("/promos/")
    if not data: st.error("❌ Cannot load promos."); return
    promos=data if isinstance(data,list) else data.get("promos",[])
    if not promos: st.info("No promo codes yet."); return
    active=sum(1 for p in promos if p.get("is_active"))
    c1,c2=st.columns(2)
    with c1: st.markdown(metric("Total Promos",str(len(promos))),unsafe_allow_html=True)
    with c2: st.markdown(metric("Active",str(active),"","green"),unsafe_allow_html=True)
    st.markdown("---")
    for p in promos:
        c1,c2,c3=st.columns([4,1,1])
        with c1:
            active_icon="🟢" if p.get("is_active") else "🔴"
            st.markdown(f"""**{p.get('code','')}** {active_icon}
            <div style='font-size:12px;color:#555'>{p.get('description','')} ·
            {p.get('discount_type','')} {p.get('discount_value','')} ·
            Used: {p.get('used_count',0)}/{p.get('max_uses',0)} ·
            Expires: {str(p.get('expiry_date',''))[:10]}</div>""",unsafe_allow_html=True)
        with c2:
            if st.button("Toggle",key=f"tog_{p['id']}",use_container_width=True):
                r=api_patch(f"/promos/{p['id']}/toggle")
                if r: st.rerun()
        with c3:
            if st.button("Delete",key=f"del_p_{p['id']}",use_container_width=True):
                r=api_delete(f"/promos/{p['id']}")
                if r: st.success("Deleted!"); st.rerun()

def page_create_promo():
    page_title("🏷️ Create Promo Code")
    with st.form("create_promo",clear_on_submit=True):
        c1,c2=st.columns(2)
        with c1:
            code=st.text_input("Promo Code",placeholder="e.g. SAVE50")
            discount_type=st.selectbox("Discount Type",["percent","flat"])
            discount_value=st.number_input("Discount Value",min_value=0.0,step=1.0)
            max_uses=st.number_input("Max Uses (0=unlimited)",min_value=0,value=100)
        with c2:
            description=st.text_input("Description")
            min_fare=st.number_input("Min Fare ₹",min_value=0.0,value=0.0)
            expiry=st.date_input("Expiry Date",value=datetime.now().date()+timedelta(days=30))
            vehicle_type=st.selectbox("Vehicle Type",["all","bike","auto","toto","ac_cab","non_ac_cab","ambulance"])
        if st.form_submit_button("✅ Create Promo",type="primary",use_container_width=True):
            if not code or not description:
                st.error("Fill in code and description.")
            else:
                r=api_post("/promos/",{"code":code.upper(),"description":description,
                    "discount_type":discount_type,"discount_value":discount_value,
                    "min_fare":min_fare,"max_uses":int(max_uses),
                    "expiry_date":str(expiry),"vehicle_type":vehicle_type,"is_active":True})
                if r and "id" in str(r): st.success(f"✅ Promo {code.upper()} created!")
                else: st.error(f"Failed: {r}")

def page_revenue():
    page_title("💰 Revenue Reports")
    n=st.selectbox("Period",{"7 Days":7,"14 Days":14,"30 Days":30,"90 Days":90}.keys())
    days={"7 Days":7,"14 Days":14,"30 Days":30,"90 Days":90}[n]
    data=api_get("/admin/revenue",params={"days":days})
    if not data: st.error("❌ Cannot load revenue."); return
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(metric("Total Revenue",f"₹{data.get('total_revenue',0):,.2f}","","green"),unsafe_allow_html=True)
    with c2: st.markdown(metric("Commission",f"₹{data.get('total_commission',0):,.2f}","","purple"),unsafe_allow_html=True)
    with c3: st.markdown(metric("Total Trips",str(data.get("total_trips",0))),unsafe_allow_html=True)
    with c4: st.markdown(metric("Avg Fare",f"₹{data.get('avg_fare',0):.2f}"),unsafe_allow_html=True)
    daily=data.get("daily_breakdown",[])
    if daily:
        df=pd.DataFrame(daily)
        fig=px.line(df,x="date",y="revenue",title=f"Revenue - Last {days} Days",markers=True,color_discrete_sequence=[BLUE])
        fig.update_layout(plot_bgcolor="white",paper_bgcolor="white")
        st.plotly_chart(fig,use_container_width=True)
        c1,c2=st.columns(2)
        with c1:
            fig2=px.bar(df,x="date",y="trips",title="Daily Trips",color_discrete_sequence=[GREEN])
            fig2.update_layout(plot_bgcolor="white",paper_bgcolor="white")
            st.plotly_chart(fig2,use_container_width=True)
        with c2:
            fig3=px.bar(df,x="date",y="commission",title="Daily Commission",color_discrete_sequence=[PURPLE])
            fig3.update_layout(plot_bgcolor="white",paper_bgcolor="white")
            st.plotly_chart(fig3,use_container_width=True)
        st.download_button("📥 Download CSV",df.to_csv(index=False),"revenue.csv","text/csv")

def page_alerts():
    page_title("🔔 System Alerts")
    tab1,tab2=st.tabs(["🆘 SOS Alerts","⚖️ Trip Disputes"])
    with tab1:
        if st.button("🔄 Refresh SOS"): st.rerun()
        data=api_get("/admin/sos")
        if not data: st.error("❌ Cannot load SOS."); return
        alerts=data.get("sos_alerts",[])
        active=[a for a in alerts if a["status"]=="active"]
        resolved=[a for a in alerts if a["status"]=="resolved"]
        c1,c2=st.columns(2)
        with c1: st.markdown(metric("🔴 Active",str(len(active)),"","red"),unsafe_allow_html=True)
        with c2: st.markdown(metric("✅ Resolved",str(len(resolved)),"","green"),unsafe_allow_html=True)
        for a in alerts:
            s_color="#EA4335" if a["status"]=="active" else "#34A853"
            st.markdown(f"""<div style='background:white;border-radius:10px;padding:14px;
                margin-bottom:8px;border-left:4px solid {s_color}'>
                <b>🆘 {a.get("raised_by_name","Unknown")}</b>
                <span style='color:#888;font-size:12px;margin-left:8px'>
                Trip #{a.get("trip_id","—")} · {str(a.get("created_at",""))[:16]}</span>
                <div style='font-size:12px;color:#555'>📍 {a.get("lat","—")}, {a.get("lng","—")}</div>
                </div>""", unsafe_allow_html=True)
            if a["status"]=="active":
                if st.button("✅ Resolve",key=f"sos_{a['id']}",type="primary"):
                    api_patch(f"/admin/sos/{a['id']}/resolve"); st.rerun()
    with tab2:
        if st.button("🔄 Refresh Disputes"): st.rerun()
        data=api_get("/admin/disputes")
        if not data: st.error("❌ Cannot load disputes."); return
        disputes=data.get("disputes",[])
        open_d=[d for d in disputes if d["status"]=="open"]
        c1,c2=st.columns(2)
        with c1: st.markdown(metric("Open",str(len(open_d)),"","red"),unsafe_allow_html=True)
        with c2: st.markdown(metric("Resolved",str(len(disputes)-len(open_d)),"","green"),unsafe_allow_html=True)
        for d in disputes:
            s_color="#EA4335" if d["status"]=="open" else "#34A853"
            st.markdown(f"""<div style='background:white;border-radius:10px;padding:14px;
                margin-bottom:8px;border-left:4px solid {s_color}'>
                <b>Trip #{d.get("trip_code",d.get("trip_id",""))}</b>
                <div style='font-size:13px;color:#555'>{d.get("reason","")}</div>
                </div>""", unsafe_allow_html=True)
            if d["status"]=="open":
                res=st.text_input("Resolution",key=f"res_{d['id']}")
                if st.button("✅ Resolve",key=f"disp_{d['id']}",type="primary"):
                    api_patch(f"/admin/disputes/{d['id']}/resolve",{"resolution":res}); st.rerun()

def page_send_notification():
    page_title("📢 Send Notification","Broadcast to riders or drivers instantly")
    with st.form("notif_form",clear_on_submit=True):
        title=st.text_input("Title",placeholder="e.g. Special Offer!")
        message=st.text_area("Message",height=100)
        audience=st.selectbox("Send To",["All Users","Riders Only","Drivers Only"])
        role_map={"All Users":"all","Riders Only":"riders","Drivers Only":"drivers"}
        if st.form_submit_button("📢 Send Now",type="primary",use_container_width=True):
            if not title or not message: st.error("Fill in both title and message.")
            else:
                r=api_post("/admin/notifications/broadcast",
                    {"title":title,"message":message,"target":role_map.get(audience,"all")})
                if r and "message" in str(r): st.success("✅ Notification sent!")
                else: st.error(f"Failed: {r}")

def page_schedule_notification():
    page_title("📅 Schedule Notification")
    with st.form("sched_notif",clear_on_submit=True):
        c1,c2=st.columns(2)
        with c1:
            title=st.text_input("Title")
            target=st.selectbox("Send To",["all","riders","drivers"])
            notif_type=st.selectbox("Type",["promotional","system","alert"])
        with c2:
            message=st.text_area("Message",height=100)
            sched_date=st.date_input("Date")
            sched_time=st.time_input("Time")
        if st.form_submit_button("📅 Schedule",type="primary",use_container_width=True):
            if not title or not message: st.error("Fill in title and message.")
            else:
                scheduled_at=datetime.combine(sched_date,sched_time).isoformat()
                r=api_post("/admin/notifications/broadcast-scheduled",
                    {"title":title,"message":message,"target":target,
                     "notif_type":notif_type,"scheduled_at":scheduled_at})
                if r and "message" in str(r): st.success(f"✅ Scheduled!")
                else: st.error(f"Failed: {r}")

def page_broadcast_history():
    page_title("📬 Broadcast History")
    if st.button("🔄 Refresh"): st.rerun()
    data=api_get("/admin/notifications/broadcast-history")
    if not data: st.error("❌ Cannot load."); return
    notifs=data.get("notifications",[])
    if not notifs: st.info("No broadcasts yet."); return
    sent=[n for n in notifs if n["is_sent"]]
    pending=[n for n in notifs if not n["is_sent"]]
    c1,c2,c3=st.columns(3)
    with c1: st.markdown(metric("Total",str(len(notifs))),unsafe_allow_html=True)
    with c2: st.markdown(metric("Sent",str(len(sent)),"","green"),unsafe_allow_html=True)
    with c3: st.markdown(metric("Scheduled",str(len(pending)),"","amber"),unsafe_allow_html=True)
    for n in notifs:
        s_color="#34A853" if n["is_sent"] else "#FBBC04"
        st.markdown(f"""<div style='background:white;border-radius:10px;padding:14px;
            margin-bottom:8px;border-left:4px solid {s_color}'>
            <b>{n["title"]}</b>
            <div style='font-size:13px;color:#555'>{n["message"]}</div>
            <div style='font-size:11px;color:#888'>
                Target: {n["target"]} · Sent: {n.get("total_sent",0)} users ·
                {"✅ Sent" if n["is_sent"] else "⏳ Scheduled"} ·
                {str(n.get("sent_at") or n.get("scheduled_at",""))[:16]}
            </div></div>""", unsafe_allow_html=True)
        if not n["is_sent"]:
            if st.button("🚀 Send Now",key=f"sn_{n['id']}"):
                r=api_post(f"/admin/notifications/send-now/{n['id']}")
                if r: st.success("Sent!"); st.rerun()

def page_cancellation_config():
    page_title("⚙️ Cancellation Config")
    with st.form("cancel_cfg"):
        c1,c2=st.columns(2)
        with c1:
            free_min=st.number_input("Free Waiting Minutes",min_value=0,value=5,step=1)
            charge=st.number_input("Cancellation Charge ₹",min_value=0.0,value=10.0,step=1.0)
        with c2:
            is_active=st.checkbox("Enable Charges",value=True)
        if st.form_submit_button("💾 Save",type="primary",use_container_width=True):
            r=api_patch("/admin/config/cancellation",
                {"free_minutes":int(free_min),"charge_amount":float(charge),"is_active":is_active})
            if r and "message" in str(r): st.success(r.get("message","Saved!"))
            else: st.error(f"Failed: {r}")

def page_wallets():
    page_title("💳 Wallet Management")
    tab1,tab2=st.tabs(["👤 Rider Wallets","🚗 Driver Wallets"])
    with tab1:
        data=api_get("/admin/users",params={"limit":500})
        if not data: return
        users=[u for u in data.get("users",[]) if u.get("role")=="rider"]
        total=sum(u.get("wallet_balance",0) for u in users)
        st.markdown(metric("Total Rider Wallet",f"₹{total:,.2f}","","green"),unsafe_allow_html=True)
        search=st.text_input("🔍 Search",key="wr_s")
        if search: users=[u for u in users if search.lower() in u["full_name"].lower() or search in str(u.get("phone",""))]
        rows=[{"Name":u["full_name"],"Phone":u.get("phone",""),"Wallet ₹":u.get("wallet_balance",0),"Trips":u.get("total_trips",0)} for u in users]
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    with tab2:
        data=api_get("/admin/drivers")
        if not data: return
        drivers=data.get("drivers",[])
        total=sum(d.get("wallet_balance",0) for d in drivers)
        st.markdown(metric("Total Driver Wallet",f"₹{total:,.2f}","","green"),unsafe_allow_html=True)
        rows=[{"Name":d["full_name"],"Phone":d.get("phone",""),"Wallet ₹":d.get("wallet_balance",0),"Earnings ₹":d.get("total_earnings",0),"Trips":d.get("total_trips",0)} for d in drivers]
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

def page_cash_collection():
    page_title("💵 Cash Collection Report")
    data=api_get("/admin/trips",params={"limit":500})
    if not data: return
    trips=[t for t in data.get("trips",[]) if t.get("payment_method")=="cash"]
    collected=[t for t in trips if t.get("cash_collected")]
    pending=[t for t in trips if not t.get("cash_collected") and t.get("status")=="completed"]
    total_cash=sum((t.get("actual_fare") or t.get("estimated_fare") or 0) for t in collected)
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(metric("Cash Trips",str(len(trips))),unsafe_allow_html=True)
    with c2: st.markdown(metric("Collected",str(len(collected)),"","green"),unsafe_allow_html=True)
    with c3: st.markdown(metric("Pending",str(len(pending)),"","amber"),unsafe_allow_html=True)
    with c4: st.markdown(metric("Total Cash",f"₹{total_cash:,.0f}","","green"),unsafe_allow_html=True)
    rows=[{"Trip Code":t.get("trip_code",""),"Driver":(t.get("driver") or {}).get("name","—"),
           "Rider":(t.get("rider") or {}).get("name","—"),
           "Amount ₹":t.get("actual_fare") or t.get("estimated_fare") or 0,
           "Collected":"✅" if t.get("cash_collected") else "⏳",
           "Date":str(t.get("completed_at") or t.get("requested_at",""))[:10]} for t in trips]
    df=pd.DataFrame(rows)
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.download_button("📥 Download CSV",df.to_csv(index=False),"cash_collection.csv","text/csv",type="primary")

def page_referral_config():
    page_title("🎁 Referral Config")
    with st.form("ref_cfg"):
        c1,c2=st.columns(2)
        with c1:
            ref_bonus=st.number_input("Referrer Bonus ₹",min_value=0.0,value=50.0,step=5.0)
            ref_ee_bonus=st.number_input("Referee Bonus ₹",min_value=0.0,value=30.0,step=5.0)
        with c2:
            min_trips=st.number_input("Min Trips",min_value=1,value=1,step=1)
            is_active=st.checkbox("Enable Referral Program",value=True)
        if st.form_submit_button("💾 Save",type="primary",use_container_width=True):
            r=api_patch("/admin/config/referral",
                {"referrer_bonus":ref_bonus,"referee_bonus":ref_ee_bonus,
                 "min_trips":int(min_trips),"is_active":is_active})
            if r and "message" in str(r): st.success(r.get("message","Saved!"))
            else: st.error(f"Failed: {r}")

def page_delete_user():
    page_title("🗑️ Delete User","Permanently delete accounts")
    st.warning("⚠️ This action is permanent and cannot be undone!")
    tab1,tab2=st.tabs(["👤 Riders","🚗 Drivers"])
    with tab1:
        data=api_get("/admin/users",params={"limit":500})
        if not data: return
        users=[u for u in data.get("users",[]) if u.get("role")=="rider"]
        search=st.text_input("🔍 Search",key="del_rider_s")
        if search: users=[u for u in users if search.lower() in u["full_name"].lower() or search in str(u.get("phone",""))]
        for u in users[:20]:
            c1,c2=st.columns([5,1])
            with c1: st.markdown(f"**{u['full_name']}** — {u.get('phone','')} — {u.get('role','')}")
            with c2:
                if st.button("🗑️",key=f"delr_{u['id']}",use_container_width=True):
                    r=api_delete(f"/admin/users/{u['id']}")
                    if r: st.success("Deleted!"); st.rerun()
    with tab2:
        data=api_get("/admin/drivers")
        if not data: return
        drivers=data.get("drivers",[])
        search2=st.text_input("🔍 Search",key="del_drv_s")
        if search2: drivers=[d for d in drivers if search2.lower() in d["full_name"].lower() or search2 in str(d.get("phone",""))]
        for d in drivers[:20]:
            c1,c2=st.columns([5,1])
            with c1: st.markdown(f"**{d['full_name']}** — {d.get('phone','')}")
            with c2:
                if st.button("🗑️",key=f"deld_{d['id']}",use_container_width=True):
                    r=api_delete(f"/admin/drivers/{d['id']}")
                    if r: st.success("Deleted!"); st.rerun()

def page_ev_stats():
    page_title("⚡ EV Stats","Electric vs Non-EV drivers")
    data=api_get("/admin/drivers")
    if not data: return
    drivers=data.get("drivers",[])
    ev=[d for d in drivers if d.get("fuel_type")=="ev"]
    non_ev=[d for d in drivers if d.get("fuel_type")!="ev"]
    c1,c2,c3=st.columns(3)
    with c1: st.markdown(metric("Total",str(len(drivers))),unsafe_allow_html=True)
    with c2: st.markdown(metric("⚡ EV",str(len(ev)),"","green"),unsafe_allow_html=True)
    with c3: st.markdown(metric("⛽ Non-EV",str(len(non_ev)),"","amber"),unsafe_allow_html=True)
    if drivers:
        fig=px.pie(values=[len(ev),len(non_ev)],names=["EV","Non-EV"],
            color_discrete_sequence=[GREEN,AMBER])
        st.plotly_chart(fig,use_container_width=True)
    rows=[{"Name":d["full_name"],"Vehicle":d.get("vehicle_type",""),"Fuel":d.get("fuel_type",""),
           "Online":"🟢" if d["is_online"] else "⚫","Trips":d.get("total_trips",0)} for d in drivers]
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

def page_reviews():
    page_title("⭐ Reviews","Driver and rider ratings")
    tab1,tab2=st.tabs(["🚗 Driver Reviews","👤 Rider Reviews"])
    with tab1:
        data=api_get("/admin/ratings",params={"role":"driver","limit":200})
        if not data: st.error("❌ Cannot load."); return
        ratings=data.get("ratings",[])
        if not ratings: st.info("No driver reviews yet."); return
        avg=round(sum(r["score"] for r in ratings)/len(ratings),2)
        c1,c2=st.columns(2)
        with c1: st.markdown(metric("Total Reviews",str(len(ratings))),unsafe_allow_html=True)
        with c2: st.markdown(metric("Average Rating",f"⭐{avg}","","green"),unsafe_allow_html=True)
        search=st.text_input("🔍 Search driver",key="rev_drv")
        if search: ratings=[r for r in ratings if search.lower() in r["rated_name"].lower()]
        for r in ratings:
            stars="⭐"*r["score"]+"☆"*(5-r["score"])
            color="#34A853" if r["score"]>=4 else ("#FBBC04" if r["score"]==3 else "#EA4335")
            st.markdown(f"""<div style='background:white;border-radius:10px;padding:14px;
                margin-bottom:6px;border-left:4px solid {color}'>
                <div style='display:flex;justify-content:space-between'>
                    <b>{r["rated_name"]}</b><div>{stars}</div>
                </div>
                <div style='font-size:12px;color:#555'>{r.get("comment") or "No comment"}</div>
                <div style='font-size:11px;color:#aaa'>By {r["rater_name"]} · Trip #{r["trip_code"]} · {r["created_at"]}</div>
                </div>""", unsafe_allow_html=True)
    with tab2:
        data=api_get("/admin/ratings",params={"role":"rider","limit":200})
        if not data: st.error("❌ Cannot load."); return
        ratings=data.get("ratings",[])
        if not ratings: st.info("No rider reviews yet."); return
        avg=round(sum(r["score"] for r in ratings)/len(ratings),2)
        c1,c2=st.columns(2)
        with c1: st.markdown(metric("Total Reviews",str(len(ratings))),unsafe_allow_html=True)
        with c2: st.markdown(metric("Average Rating",f"⭐{avg}","","green"),unsafe_allow_html=True)
        for r in ratings:
            stars="⭐"*r["score"]+"☆"*(5-r["score"])
            color="#34A853" if r["score"]>=4 else ("#FBBC04" if r["score"]==3 else "#EA4335")
            st.markdown(f"""<div style='background:white;border-radius:10px;padding:14px;
                margin-bottom:6px;border-left:4px solid {color}'>
                <div style='display:flex;justify-content:space-between'>
                    <b>{r["rated_name"]}</b><div>{stars}</div>
                </div>
                <div style='font-size:12px;color:#555'>{r.get("comment") or "No comment"}</div>
                <div style='font-size:11px;color:#aaa'>By {r["rater_name"]} · Trip #{r["trip_code"]} · {r["created_at"]}</div>
                </div>""", unsafe_allow_html=True)

def page_commission():
    page_title("💰 Commission Report","Payment breakdown per trip")
    data=api_get("/admin/trips",params={"limit":500})
    if not data: return
    trips=[t for t in data.get("trips",[]) if t.get("status")=="completed"]
    if not trips: st.info("No completed trips."); return
    total_fare=sum(t.get("actual_fare") or 0 for t in trips)
    total_comm=sum(t.get("platform_fee") or 0 for t in trips)
    total_earn=sum(t.get("driver_earnings") or 0 for t in trips)
    total_promo=sum(t.get("promo_discount") or 0 for t in trips)
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(metric("Revenue",f"₹{total_fare:,.0f}","","green"),unsafe_allow_html=True)
    with c2: st.markdown(metric("Commission",f"₹{total_comm:,.0f}","","purple"),unsafe_allow_html=True)
    with c3: st.markdown(metric("Driver Earnings",f"₹{total_earn:,.0f}","","blue"),unsafe_allow_html=True)
    with c4: st.markdown(metric("Promo Discounts",f"₹{total_promo:,.0f}","","amber"),unsafe_allow_html=True)
    rows=[]
    for t in trips:
        fare=t.get("actual_fare") or 0
        promo=t.get("promo_discount") or 0
        comm=t.get("platform_fee") or 0
        earn=t.get("driver_earnings") or 0
        method=t.get("payment_method","")
        net=max(0,fare-promo)
        cash_collect=net if method=="cash" else 0
        company_pay=max(0,earn-cash_collect) if method=="cash" else 0
        rows.append({"Trip":t.get("trip_code",""),"Driver":(t.get("driver") or {}).get("name","—"),
                     "Rider":(t.get("rider") or {}).get("name","—"),
                     "Fare ₹":fare,"Promo ₹":promo,"Net ₹":net,
                     "Commission ₹":comm,"Driver Earns ₹":earn,
                     "Payment":method,"Cash Collect ₹":cash_collect,
                     "Company Pays ₹":company_pay,
                     "Date":str(t.get("completed_at",""))[:10]})
    df=pd.DataFrame(rows)
    st.dataframe(df,use_container_width=True,height=400,hide_index=True)
    st.download_button("📥 Download CSV",df.to_csv(index=False),"commission.csv","text/csv",type="primary")

def page_cancellations():
    page_title("❌ Cancellation Reasons","Why trips were cancelled")
    data=api_get("/admin/trips",params={"limit":500})
    if not data: return
    trips=[t for t in data.get("trips",[]) if t.get("status")=="cancelled"]
    if not trips: st.info("No cancelled trips."); return
    by_rider=sum(1 for t in trips if t.get("cancelled_by")=="rider")
    by_driver=sum(1 for t in trips if t.get("cancelled_by")=="driver")
    by_system=sum(1 for t in trips if t.get("cancelled_by")=="system")
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(metric("Total",str(len(trips))),unsafe_allow_html=True)
    with c2: st.markdown(metric("By Rider",str(by_rider),"","amber"),unsafe_allow_html=True)
    with c3: st.markdown(metric("By Driver",str(by_driver),"","red"),unsafe_allow_html=True)
    with c4: st.markdown(metric("By System",str(by_system),"","purple"),unsafe_allow_html=True)
    fig=px.pie(values=[by_rider,by_driver,by_system],names=["Rider","Driver","System"],
        color_discrete_sequence=[AMBER,RED,PURPLE])
    st.plotly_chart(fig,use_container_width=True)
    rows=[{"Trip":t.get("trip_code",""),"Cancelled By":t.get("cancelled_by","—"),
           "Reason":t.get("cancel_reason","—"),
           "Rider":(t.get("rider") or {}).get("name","—"),
           "Driver":(t.get("driver") or {}).get("name","—"),
           "Date":str(t.get("cancelled_at") or t.get("requested_at",""))[:16]} for t in trips]
    df=pd.DataFrame(rows)
    f=st.selectbox("Filter",["All","rider","driver","system"])
    if f!="All": df=df[df["Cancelled By"]==f]
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.download_button("📥 Download CSV",df.to_csv(index=False),"cancellations.csv","text/csv")

def main():
    if "logged_in" not in st.session_state: st.session_state.logged_in=False
    if not st.session_state.logged_in: show_login(); return
    page=show_sidebar()
    routing={
        "📊 Overview":page_overview,
        "🔴 Live Feed":page_live_feed,
        "🔥 Heatmap":page_heatmap,
        "🗺️ Live Map":page_live_map,
        "🛣️ Trips":page_trips,
        "🧾 Ride History":page_ride_history,
        "👥 Drivers":page_drivers,
        "📄 Documents":page_documents,
        "📈 Performance":page_performance,
        "💸 Driver Payments":page_driver_payments,
        "🚗 Vehicles":page_vehicles,
        "🧑 Riders":page_riders,
        "🔒 Block Management":page_block,
        "⚙️ Pricing":page_pricing,
        "🎁 Promotions":page_promotions,
        "🏷️ Create Promo":page_create_promo,
        "💰 Revenue":page_revenue,
        "🔔 Alerts":page_alerts,
        "📢 Send Notification":page_send_notification,
        "📅 Schedule Notification":page_schedule_notification,
        "📬 Broadcast History":page_broadcast_history,
        "⚙️ Cancellation Config":page_cancellation_config,
        "💳 Wallets":page_wallets,
        "💸 Withdrawals":page_driver_payments,
        "⚖️ Disputes":page_alerts,
        "🆘 SOS":page_alerts,
        "💵 Cash Collection":page_cash_collection,
        "🎁 Referral Config":page_referral_config,
        "🗑️ Delete User":page_delete_user,
        "⚡ EV Stats":page_ev_stats,
        "⭐ Reviews":page_reviews,
        "💰 Commission":page_commission,
        "❌ Cancellations":page_cancellations,
    }
    routing.get(page,page_overview)()

if __name__=="__main__":
    main()
