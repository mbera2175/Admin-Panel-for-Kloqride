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

# ── Backend API ───────────────────────────────────────────────────────────────
API_BASE = os.getenv("API_BASE", "https://kridebackend-production.up.railway.app")
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "0000000000")
ADMIN_PASSWORD_API = os.getenv("ADMIN_PASSWORD_API", "secret")

def get_admin_token():
    try:
        res = requests.post(
            f"{API_BASE}/auth/password/login",
            json={"phone": ADMIN_PHONE, "password": ADMIN_PASSWORD_API},
            timeout=10
        )
        if res.status_code == 200:
            return res.json().get("access_token", "")
    except Exception as e:
        return ""
    return ""

if "admin_token" not in st.session_state or not st.session_state.admin_token:
    st.session_state.admin_token = get_admin_token()

ADMIN_TOKEN = st.session_state.admin_token

def api_get(endpoint, params=None):
    token = st.session_state.get("admin_token", ADMIN_TOKEN)
    try:
        res = requests.get(
            f"{API_BASE}{endpoint}",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if res.status_code == 200:
            return res.json()
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def api_post(endpoint, data=None):
    try:
        res = requests.post(
            f"{API_BASE}{endpoint}",
            json=data,
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            timeout=10
        )
        return res.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def api_patch(endpoint):
    try:
        res = requests.patch(
            f"{API_BASE}{endpoint}",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            timeout=10
        )
        return res.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def api_delete(endpoint):
    try:
        res = requests.delete(
            f"{API_BASE}{endpoint}",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            timeout=10
        )
        return res.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# Load environment variables
load_dotenv()

# ── Data persistence helpers ──────────────────────────────────────────────────
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
DATA_DIR.mkdir(exist_ok=True)

def load_data(filename):
    """Load data from JSON file"""
    try:
        filepath = DATA_DIR / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading data: {e}")
    return None

def save_data(filename, data):
    """Save data to JSON file"""
    try:
        filepath = DATA_DIR / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ── Data persistence helpers ──────────────────────────────────────────────────
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
DATA_DIR.mkdir(exist_ok=True)

def load_data(filename):
    """Load data from JSON file"""
    try:
        filepath = DATA_DIR / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading data: {e}")
    return None

def save_data(filename, data):
    """Save data to JSON file"""
    try:
        filepath = DATA_DIR / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kloq Ride | Dashboard",
    page_icon="🚖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
footer {visibility: hidden;}
.metric-card {
    background: white;
    border-radius: 12px;
    padding: 18px 20px;
    border-left: 4px solid #FF6B00;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 8px;
}
.metric-card.green  { border-left-color: #34A853; }
.metric-card.amber  { border-left-color: #FBBC04; }
.metric-card.red    { border-left-color: #EA4335; }
.metric-card.purple { border-left-color: #7F77DD; }
.m-label { font-size: 11px; color: #888; font-weight: 500;
           text-transform: uppercase; letter-spacing: 0.5px; }
.m-value { font-size: 1.7rem; font-weight: 700; color: #111111; margin: 2px 0; }
.m-delta { font-size: 12px; }
.up   { color: #34A853; }
.down { color: #EA4335; }
.badge {
    display: inline-block; padding: 3px 10px;
    border-radius: 20px; font-size: 12px; font-weight: 600;
}
.b-active   { background:#E6F4EA; color:#137333; }
.b-idle     { background:#FEF3CD; color:#856404; }
.b-offline  { background:#FCE8E6; color:#9A0000; }
.b-comp     { background:#FFF0E6; color:#FF6B00; }
.b-canc     { background:#FCE8E6; color:#9A0000; }
.b-prog     { background:#FEF3CD; color:#856404; }
.alert { background:#FEF3CD; border-left:4px solid #FBBC04;
         padding:10px 14px; border-radius:0 8px 8px 0;
         font-size:13px; color:#5c4200; margin-bottom:16px; }

/* Global Primary Buttons (Login, Downloads, etc.) */
button[kind="primary"], button[data-testid="baseButton-primary"],
button[kind="primaryFormSubmit"], button[data-testid="baseButton-primaryFormSubmit"] {
    background-color: #E85F00 !important;
    color: white !important;
    border-color: #E85F00 !important;
}
button[kind="primary"]:hover, button[data-testid="baseButton-primary"]:hover,
button[kind="primaryFormSubmit"]:hover, button[data-testid="baseButton-primaryFormSubmit"]:hover {
    background-color: #CC4E00 !important;
    border-color: #CC4E00 !important;
}

/* Sidebar background */
section[data-testid="stSidebar"] {
    background-color: #F2F2F2;
}

/* Default sidebar buttons */
section[data-testid="stSidebar"] button {
    background-color: #F2F2F2;
    color: #111111;
    border-radius: 8px;
    margin-bottom: 0px !important;
    padding-top: 6px !important;
    padding-bottom: 6px !important;
}

/* Reduce gap between buttons using negative margins */
section[data-testid="stSidebar"] div.stButton {
    margin-top: -8px !important;
    margin-bottom: -4px !important;
}

/* Hover effect */
section[data-testid="stSidebar"] button:hover {
    background-color: #E8E8E8;
}

/* 🔥 ACTIVE (selected) nav button */
section[data-testid="stSidebar"] button[kind="primary"] {
    background-color: #FF6B00 !important;
    color: white !important;
    font-weight: 500;
}
/* Driver list — icon action buttons (pen/delete) */
button[title="View / manage documents"],
button[title="Delete this driver"] {
    padding: 4px 10px !important;
    min-height: 30px !important;
    height: 30px !important;
    max-height: 30px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    line-height: 1 !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Credentials from environment variables ────────────────────────────────────
USERS = {
    os.getenv('ADMIN_EMAIL', 'admin@kloqride.com'): {
        "password": os.getenv('ADMIN_PASSWORD', 'admin123'),
        "name": "Mahadeb Bera",
        "role": "Admin"
    },
    os.getenv('OPS_EMAIL', 'ops@kloqride.com'): {
        "password": os.getenv('OPS_PASSWORD', 'ops123'),
        "name": "Ops Manager",
        "role": "Operations"
    },
    os.getenv('DRIVER_EMAIL', 'driver@kloqride.com'): {
        "password": os.getenv('DRIVER_PASSWORD', 'driver123'),
        "name": "Ravi Kumar",
        "role": "Driver"
    }
}

SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '30'))

# ── Generate demo data (in memory — no DB) ───────────────────────────────────
@st.cache_data
def make_trips():
    zones   = ["Kolkata", "Park Street","Salt Lake","Howrah Station","New Town",
               "Esplanade","New Town","Dum Dum","Asansol","Barasat"]
    drivers = ["Ravi Kumar","Suresh Patra","Anup Das","Tamal Ghosh",
               "Mohan Roy","Bikash Sen","Pradip Mondal","Amit Pal"]
    statuses = ["Completed"]*6 + ["Cancelled","In Progress"]
    payments = ["UPI","Cash","UPI","Cash"]
    vehicle_types = ["Car","Car","Car","Bike","Bike","Auto"]
    riders = ["Arjun Sharma","Priya Das","Sneha Gupta","Rohit Mondal",
              "Anjali Sen","Vikram Sinha","Pooja Nath","Karan Dey",
              "Megha Roy","Sourav Pal","Nisha Banerjee","Aman Ghosh"]
    rows = []
    base = datetime.now() - timedelta(days=60)
    for i in range(350):
        t = base + timedelta(hours=random.randint(0, 1440))
        st_ = random.choice(statuses)
        vtype = random.choice(vehicle_types)
        fare = round(random.uniform(60, 480), 0) if st_ != "Cancelled" else 0
        if vtype == "Bike":
            fare = round(fare * 0.5, 0) if fare > 0 else 0
        elif vtype == "Auto":
            fare = round(fare * 0.7, 0) if fare > 0 else 0
        rows.append({
            "Trip ID":       f"KR-{2000+i}",
            "Date":          t.strftime("%Y-%m-%d"),
            "Time":          t.strftime("%H:%M"),
            "Rider":         random.choice(riders),
            "Pickup":        random.choice(zones),
            "Drop":          random.choice(zones),
            "Driver":        random.choice(drivers),
            "Vehicle Type":  vtype,
            "Fare (₹)":      fare,
            "Status":        st_,
            "Rating":        round(random.uniform(3.5,5.0),1) if st_=="Completed" else 0,
            "Payment":       random.choice(payments),
        })
    return pd.DataFrame(rows)

@st.cache_data
def make_drivers():
    names    = ["Ravi Kumar","Suresh Patra","Anup Das","Tamal Ghosh",
                "Mohan Roy","Bikash Sen","Pradip Mondal","Amit Pal"]
    zones    = ["Kolkata", "Howrah", "Salt Lake", "Durgapur", "Asansol"]
    statuses = ["Active","Active","Idle","Offline","Active","Idle","Active","Offline"]
    vehicles = ["Maruti Swift","Hyundai i20","Tata Indigo","Honda Amaze","WagonR"]
    rows = []
    for i, n in enumerate(names):
        rows.append({
            "ID":           i+1,
            "Name":         n,
            "Phone":        f"98{random.randint(10000000,99999999)}",
            "Zone":         random.choice(zones),
            "Status":       statuses[i],
            "Rating":       round(random.uniform(3.8,5.0),1),
            "Total Trips":  random.randint(20,320),
            "Vehicle":      random.choice(vehicles),
            "Joined":       (datetime.now()-timedelta(days=random.randint(30,400))).strftime("%d %b %Y"),
        })
    return pd.DataFrame(rows)

@st.cache_data
def make_revenue():
    rows = []
    for i in range(60):
        d = (datetime.now()-timedelta(days=60-i))
        trips = random.randint(30,80)
        comp  = int(trips*random.uniform(0.80,0.95))
        canc  = trips-comp
        avg   = round(random.uniform(140,200),0)
        rows.append({
            "Date":       d.strftime("%Y-%m-%d"),
            "Revenue":    round(comp*avg,0),
            "Trips":      trips,
            "Completed":  comp,
            "Cancelled":  canc,
            "Avg Fare":   avg,
        })
    return pd.DataFrame(rows)

trips_df   = make_trips()
drivers_df = make_drivers()
revenue_df = make_revenue()

@st.cache_data
def make_live_drivers():
    names = ["Ravi Kumar","Suresh Patra","Anup Das","Tamal Ghosh",
             "Mohan Roy","Bikash Sen","Pradip Mondal","Amit Pal"]
    vehicles = ["Maruti Swift","Hyundai i20","Tata Indigo","Honda Amaze",
                "WagonR","Maruti Dzire","Toyota Etios","Hyundai Xcent"]
    statuses = ["En Route","Waiting","On Trip","En Route","On Trip","Waiting","En Route","Offline"]
    passengers = ["","","Suman Roy","","Priya Sen","","",""]
    rows = []
    for i, n in enumerate(names):
        rows.append({
            "Name": n, "Vehicle": vehicles[i], "Status": statuses[i],
            "Lat": 22.57 + random.uniform(-0.08, 0.08),
            "Lon": 88.36 + random.uniform(-0.08, 0.08),
            "Speed": random.randint(0, 60) if statuses[i] != "Offline" else 0,
            "Passenger": passengers[i],
            "Last Update": (datetime.now() - timedelta(minutes=random.randint(0, 15))).strftime("%H:%M"),
            "Plate": f"WB-{random.randint(10,99)}-{random.choice('ABCDEFGH')}-{random.randint(1000,9999)}",
        })
    return pd.DataFrame(rows)

@st.cache_data
def make_notifications():
    types = [
        ("🚨 SOS Alert", "Driver Ravi Kumar triggered SOS near Howrah Station", "Critical", "SOS Alert"),
        ("🔧 Maintenance Due", "Vehicle WB-34-A-2345 service overdue by 3 days", "High", "Maintenance"),
        ("⭐ Low Rating", "Driver Suresh Patra received 2.1 rating on last trip", "High", "Low Rating"),
        ("💳 Payment Issue", "UPI payment failed for Trip KR-2048 — ₹320 pending", "Medium", "Payment"),
        ("👤 New Driver", "Ramesh Ghosh completed onboarding and is ready to go", "Low", "New Driver"),
        ("⚠️ Trip Anomaly", "Trip KR-2102 route deviation detected — 8km extra", "High", "Anomaly"),
        ("🔄 System Update", "Dashboard v1.1 deployed with new analytics module", "Low", "System"),
        ("🚨 SOS Alert", "Driver Anup Das triggered SOS near Park Street", "Critical", "SOS Alert"),
        ("💳 Payment Issue", "Cash collection mismatch — Driver Tamal Ghosh ₹450", "Medium", "Payment"),
        ("⭐ Low Rating", "Driver Mohan Roy avg rating dropped below 3.5 this week", "Medium", "Low Rating"),
        ("🔧 Maintenance Due", "Vehicle WB-21-C-8876 insurance expiring in 5 days", "High", "Maintenance"),
        ("👤 New Driver", "Sunil Mandal submitted documents for verification", "Low", "New Driver"),
        ("⚠️ Trip Anomaly", "Trip KR-2187 idle for 25 min at pickup location", "Medium", "Anomaly"),
        ("🔄 System Update", "Scheduled maintenance window: Tomorrow 2AM-4AM", "Low", "System"),
        ("🚨 SOS Alert", "Passenger reported safety concern on Trip KR-2201", "Critical", "SOS Alert"),
        ("💳 Payment Issue", "Card declined for customer Rina Das — Trip KR-2210", "Medium", "Payment"),
        ("🔧 Maintenance Due", "3 vehicles due for emission testing this week", "Medium", "Maintenance"),
        ("⭐ Low Rating", "Zone Asansol avg driver rating dropped to 3.2", "High", "Low Rating"),
        ("⚠️ Trip Anomaly", "Unusual surge in cancellations at Park Street zone", "High", "Anomaly"),
        ("🔄 System Update", "New payment gateway integration completed", "Low", "System"),
    ]
    rows = []
    for i, (title, desc, priority, typ) in enumerate(types):
        hrs_ago = random.randint(0, 48)
        rows.append({
            "Title": title, "Description": desc, "Priority": priority, "Type": typ,
            "Time": (datetime.now() - timedelta(hours=hrs_ago)).strftime("%Y-%m-%d %H:%M"),
            "Hours Ago": hrs_ago,
            "Read": random.choice([True, False, False]),
        })
    return pd.DataFrame(rows)

@st.cache_data
def make_customers():
    names = ["Suman Roy","Priya Sen","Rina Das","Amit Chatterjee","Neha Gupta",
             "Rahul Mondal","Sneha Banerjee","Vikram Singh","Anjali Sharma",
             "Deepak Pal","Kavita Ghosh","Rohit Mukherjee","Pooja Dey",
             "Arjun Bose","Meera Karmakar"]
    rows = []
    for i, n in enumerate(names):
        joined = datetime.now() - timedelta(days=random.randint(30, 365))
        rows.append({
            "ID": f"CUS-{100+i}", "Name": n,
            "Phone": f"98{random.randint(10000000,99999999)}",
            "Email": n.lower().replace(" ",".")+"@email.com",
            "Total Rides": random.randint(5, 80),
            "Total Spent": round(random.uniform(800, 15000), 0),
            "Avg Rating Given": round(random.uniform(3.5, 5.0), 1),
            "Member Since": joined.strftime("%d %b %Y"),
            "Joined Days": (datetime.now() - joined).days,
        })
    return pd.DataFrame(rows)

@st.cache_data
def make_vehicles():
    models = ["Maruti Swift","Hyundai i20","Tata Indigo","Honda Amaze",
              "WagonR","Maruti Dzire","Toyota Etios","Hyundai Xcent"]
    fuels = ["Petrol","Petrol","Diesel","Petrol","CNG","Diesel","Diesel","Petrol"]
    statuses = ["Active","Active","Needs Maintenance","Active","In Service","Active","Active","Needs Maintenance"]
    drivers = ["Ravi Kumar","Suresh Patra","Anup Das","Tamal Ghosh",
               "Mohan Roy","Bikash Sen","Pradip Mondal","Amit Pal"]
    rows = []
    for i in range(8):
        last_svc = datetime.now() - timedelta(days=random.randint(10, 120))
        ins_exp = datetime.now() + timedelta(days=random.randint(-10, 180))
        rows.append({
            "Vehicle ID": f"VH-{100+i}", "Model": models[i],
            "Plate": f"WB-{random.randint(10,99)}-{random.choice('ABCDEFGH')}-{random.randint(1000,9999)}",
            "Year": random.randint(2018, 2024), "Fuel": fuels[i],
            "Status": statuses[i], "Driver": drivers[i],
            "Odometer (km)": random.randint(15000, 120000),
            "Last Service": last_svc.strftime("%d %b %Y"),
            "Next Service Due": (last_svc + timedelta(days=90)).strftime("%d %b %Y"),
            "Insurance Expiry": ins_exp.strftime("%d %b %Y"),
            "Ins Days Left": (ins_exp - datetime.now()).days,
        })
    return pd.DataFrame(rows)

@st.cache_data
def make_promotions():
    promos = [
        ("FIRST50", "50% off on first ride", "%", 50, 0, 50, "Active"),
        ("RIDE20", "Flat ₹20 off on all rides", "₹", 20, 120, 500, "Active"),
        ("WEEKEND30", "30% off on weekend rides", "%", 30, 45, 200, "Active"),
        ("KOLKATA10", "₹10 off Kolkata zone rides", "₹", 10, 88, 300, "Active"),
        ("REFER100", "₹100 for every referral", "₹", 100, 34, 100, "Active"),
        ("HOLI25", "25% off Holi special", "%", 25, 200, 200, "Expired"),
        ("SUMMER15", "15% off summer rides", "%", 15, 0, 150, "Upcoming"),
        ("LOYALTY5", "5% cashback for 50+ rides", "%", 5, 67, 500, "Active"),
    ]
    rows = []
    for code, desc, disc_type, val, used, max_u, status in promos:
        start = datetime.now() - timedelta(days=random.randint(0, 30))
        end = start + timedelta(days=random.randint(15, 60))
        rows.append({
            "Code": code, "Description": desc, "Discount Type": disc_type,
            "Discount Value": val, "Used": used, "Max Uses": max_u,
            "Status": status,
            "Valid From": start.strftime("%d %b %Y"),
            "Valid To": end.strftime("%d %b %Y"),
        })
    return pd.DataFrame(rows)

@st.cache_data
def make_driver_onboarding():
    rows = []
    base = datetime.now() - timedelta(days=30)
    names = ["Ravi Kumar","Suresh Patra","Anup Das","Tamal Ghosh","Mohan Roy",
             "Bikash Sen","Pradip Mondal","Amit Pal","Sanjay Dutta","Rakesh Nag",
             "Debasis Kar","Arijit Jana","Partha Sarkar","Subir Mitra","Kamal Halder",
             "Pintu Barman","Gopal Mandal","Tushar Bose","Manoj Chatterjee","Biswajit Paul"]
    devices = ["Android","Android","Android","Android","iOS"]
    cities = ["Kolkata", "Howrah", "Salt Lake", "Durgapur", "Asansol"]
    sources = ["Google Play","Referral","Facebook Ad","Direct","App Store"]
    for i in range(120):
        d = base + timedelta(days=random.randint(0,30), hours=random.randint(0,23))
        installed = True
        logged_in = random.random() < 0.72
        completed_profile = logged_in and random.random() < 0.65
        doc_uploaded = completed_profile and random.random() < 0.55
        approved = doc_uploaded and random.random() < 0.80
        rows.append({
            "Driver ID": f"DRV-{5000+i}",
            "Name": random.choice(names),
            "Phone": f"98{random.randint(10000000,99999999)}",
            "City": random.choice(cities),
            "Device": random.choice(devices),
            "Source": random.choice(sources),
            "Install Date": d.strftime("%Y-%m-%d"),
            "Install Time": d.strftime("%H:%M"),
            "Installed": installed,
            "Logged In": logged_in,
            "Profile Complete": completed_profile,
            "Documents Uploaded": doc_uploaded,
            "Approved": approved,
        })
    return pd.DataFrame(rows)

@st.cache_data
def make_rider_onboarding():
    rows = []
    base = datetime.now() - timedelta(days=30)
    names = ["Arjun Sharma","Priya Das","Sneha Gupta","Rohit Mondal","Anjali Sen",
             "Vikram Sinha","Pooja Nath","Karan Dey","Megha Roy","Sourav Pal",
             "Nisha Banerjee","Aman Ghosh","Ritika Saha","Deepak Mukherjee","Swati Basu",
             "Tanmoy Haldar","Shreya Chakraborty","Rahul Biswas","Ananya Datta","Sudipta Kar",
             "Koushik Sarkar","Moumita Jana","Avik Pramanik","Piyali Sen","Debanjan Mitra"]
    devices = ["Android","Android","Android","iOS","iOS"]
    cities = ["Kolkata", "Howrah", "Salt Lake", "New Town", "Durgapur", "Asansol", "Siliguri", "Bardhaman"]
    sources = ["Google Play","App Store","Referral","Facebook Ad","Instagram Ad","Direct"]
    for i in range(250):
        d = base + timedelta(days=random.randint(0,30), hours=random.randint(0,23))
        installed = True
        logged_in = random.random() < 0.78
        profile_done = logged_in and random.random() < 0.70
        first_ride = profile_done and random.random() < 0.45
        rows.append({
            "Rider ID": f"RDR-{8000+i}",
            "Name": random.choice(names),
            "Phone": f"97{random.randint(10000000,99999999)}",
            "City": random.choice(cities),
            "Device": random.choice(devices),
            "Source": random.choice(sources),
            "Install Date": d.strftime("%Y-%m-%d"),
            "Install Time": d.strftime("%H:%M"),
            "Installed": installed,
            "Logged In": logged_in,
            "Profile Complete": profile_done,
            "First Ride Taken": first_ride,
        })
    return pd.DataFrame(rows)

@st.cache_data
def make_driver_payments():
    names = ["Ravi Kumar","Suresh Patra","Anup Das","Tamal Ghosh","Mohan Roy",
             "Bikash Sen","Pradip Mondal","Amit Pal","Sanjay Dutta","Rakesh Nag"]
    banks = ["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Punjab National Bank"]
    rows = []
    for i, n in enumerate(names):
        earnings = round(random.uniform(5000, 25000), 2)
        commission = round(earnings * 0.05, 2)
        rows.append({
            "Driver ID": f"DRV-{5000+i}",
            "Name": n,
            "Bank Name": random.choice(banks),
            "Account Number": f"XXXXXXXX{random.randint(1000,9999)}",
            "IFSC Code": f"{random.choice(['SBIN','HDFC','ICIC','UTIB','PUNB'])}000{random.randint(100,999)}",
            "Total Earnings (₹)": earnings,
            "Commission Owed (5%)": commission,
            "Net Payable": round(earnings - commission, 2)
        })
    return pd.DataFrame(rows)

live_drivers_df = make_live_drivers()
notifications_df = make_notifications()
customers_df = make_customers()
vehicles_df = make_vehicles()
promotions_df = make_promotions()
driver_onboarding_df = make_driver_onboarding()
rider_onboarding_df = make_rider_onboarding()
driver_payments_df = make_driver_payments()

@st.cache_data(ttl=300)
def make_search_heatmap_data():
    rows = []
    base = datetime.now() - timedelta(days=30)
    for i in range(1500):
        d = base + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        lat = 22.5726 + random.uniform(-0.15, 0.15)
        lon = 88.3639 + random.uniform(-0.15, 0.15)
        if random.random() < 0.3:
            lat = 22.555 + random.uniform(-0.02, 0.02)
            lon = 88.352 + random.uniform(-0.02, 0.02)
            loc = "Park Street / Maidan"
        elif random.random() < 0.2:
            lat = 22.652 + random.uniform(-0.02, 0.02)
            lon = 88.446 + random.uniform(-0.02, 0.02)
            loc = "Airport Area"
        elif random.random() < 0.2:
            lat = 22.580 + random.uniform(-0.02, 0.02)
            lon = 88.310 + random.uniform(-0.02, 0.02)
            loc = "Howrah Station"
        else:
            loc = random.choice(["Salt Lake", "New Town", "Dum Dum", "Ballygunge", "Jadavpur", "Esplanade"])
        rows.append({
            "Date": d.strftime("%Y-%m-%d"),
            "Time": d.strftime("%H:%M:%S"),
            "Lat": lat,
            "Lon": lon,
            "Location": loc
        })
    return pd.DataFrame(rows)

search_heatmap_df = make_search_heatmap_data()

# ── COLORS ────────────────────────────────────────────────────────────────────
BLUE="#FF6B00"; GREEN="#34A853"; AMBER="#FBBC04"; RED="#EA4335"; PURPLE="#7F77DD"

def metric(label, value, delta="", color="blue"):
    cls = {"blue":"","green":"green","amber":"amber","red":"red","purple":"purple"}[color]
    if delta:
        dcls = "up" if "+" in str(delta) or "▲" in str(delta) else "down"
        d_html = f'<div class="m-delta {dcls}">{delta}</div>'
    else:
        d_html = '<div class="m-delta">&nbsp;</div>'
    return f"""<div class="metric-card {cls}">
        <div class="m-label">{label}</div>
        <div class="m-value">{value}</div>
        {d_html}</div>"""

def page_title(title, subtitle=""):
    sub_html = f"<div style='font-size:13px;color:rgba(255,255,255,0.9);margin-top:6px;font-weight:500;'>{subtitle}</div>" if subtitle else ""
    st.markdown(f"""
    <div style='background:#E85F00;border-radius:10px;padding:18px 22px;margin-bottom:16px;
                box-shadow:0 4px 6px rgba(0,0,0,0.1);'>
        <div style='font-size:1.6rem;font-weight:800;color:#ffffff;'>{title}</div>
        {sub_html}
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def show_login():
    c1,c2,c3 = st.columns([1,1.3,1])
    with c2:
        st.markdown("""
        <div style='text-align:center;margin-top:50px;margin-bottom:24px;'>
          <div style='font-size:3rem;font-weight:900;color:#FF6B00;'>🚖 Kloq Ride</div>
          <div style='color:#888;font-size:0.95rem;margin-top:4px;'>
              Operations Dashboard · Kolkata Region
          </div>
        </div>""", unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown("#### Sign in to your account")
            email    = st.text_input("Email", placeholder="admin@kloqride.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
            ok = st.form_submit_button("Login →", use_container_width=True, type="primary")
            if ok:
                if email in USERS and USERS[email]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user = USERS[email]
                    st.session_state.user_email = email
                    st.session_state.login_time = datetime.now()
                    st.query_params["u"] = email
                    st.success(f"Welcome, {USERS[email]['name']}!")
                    st.rerun()
                else:
                    st.error("❌ Wrong email or password.")

        st.markdown("""
        <div style='background:#FFF0E6;border-radius:10px;padding:14px 16px;
                    margin-top:16px;font-size:13px;color:#FF6B00;text-align:center;'>
          <b>Demo accounts</b><br>
          admin@kloqride.com &nbsp;/&nbsp; admin123<br>
          ops@kloqride.com &nbsp;/&nbsp; ops123
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
def show_sidebar():
    user = st.session_state.user
    st.sidebar.markdown(f"""
    <div style='padding:10px 0 16px;'>
      <div style='font-size:1.4rem;font-weight:900;color:#FF6B00;'>🚖 Kloq Ride</div>
      <div style='margin-top:12px;padding:10px 12px;background:#FFF0E6;border-radius:8px;'>
        <div style='font-size:13px;font-weight:600;color:#111111;'>{user['name']}</div>
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
        "Driver Document Upload", "Driver Performance", "Driver Payments", "Vehicle Management",
        "Promotions", "Revenue Reports", "Notifications", "Pricing & Fees"
    ]

    for p in pages:
        btn_type = "primary" if st.session_state.nav_page == p else "secondary"
        if st.sidebar.button(p, type=btn_type, use_container_width=True, key=f"nav_btn_{p}"):
            st.session_state.nav_page = p
            st.rerun()
            
    page = st.session_state.nav_page

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div style='font-size:11px;color:#aaa;text-align:center;margin-top:8px;'>
        Demo data only · {datetime.now().strftime("%d %b %Y %H:%M")}
    </div>""", unsafe_allow_html=True)

    st.sidebar.markdown("""
    <style>
    /* Logout button — always orange */
    section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"][kind="secondary"]:last-of-type {
        background-color: #FF6B00 !important;
        color: white !important;
        border: 1px solid #FF6B00 !important;
    }
    section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"][kind="secondary"]:last-of-type:hover {
        background-color: #CC4E00 !important;
        border-color: #CC4E00 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.sidebar.button("Logout", use_container_width=True, key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.user_email = None
        st.session_state.login_time = None
        st.query_params.clear()  # ← clear URL param so auto-login doesn't re-trigger
        st.rerun()

    return page

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
def page_overview():
    page_title("📊 Overview", f"{datetime.now().strftime('%A, %d %B %Y')} · KloqRide Operations")

    # Fetch real data from backend
    data = api_get("/admin/overview")
    
    if not data:
        st.error("❌ Could not connect to backend. Check your API connection.")
        return

    users    = data.get("users", {})
    trips    = data.get("trips", {})
    revenue  = data.get("revenue", {})

    # Row 1 — Users & Drivers
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(metric("Total Riders",      str(users.get("riders", 0)),           "", "blue"),   unsafe_allow_html=True)
    with c2: st.markdown(metric("Total Drivers",     str(users.get("drivers", 0)),          "", "green"),  unsafe_allow_html=True)
    with c3: st.markdown(metric("Active Drivers",    str(users.get("active_drivers", 0)),   "", "amber"),  unsafe_allow_html=True)
    with c4: st.markdown(metric("Pending Approval",  str(users.get("pending_approval", 0)), "", "red"),    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 2 — Trips
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(metric("Total Trips",     str(trips.get("total", 0)),     "", "blue"),   unsafe_allow_html=True)
    with c2: st.markdown(metric("Completed",       str(trips.get("completed", 0)), "", "green"),  unsafe_allow_html=True)
    with c3: st.markdown(metric("Active Now",      str(trips.get("active", 0)),    "", "amber"),  unsafe_allow_html=True)
    with c4: st.markdown(metric("Cancelled",       str(trips.get("cancelled", 0)), "", "red"),    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 3 — Revenue
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(metric("Today's Trips",    str(trips.get("today", 0)),                    "", "blue"),   unsafe_allow_html=True)
    with c2: st.markdown(metric("Today's Revenue",  f"₹{revenue.get('today', 0):,.2f}",            "", "green"),  unsafe_allow_html=True)
    with c3: st.markdown(metric("Month Revenue",    f"₹{revenue.get('this_month', 0):,.2f}",       "", "green"),  unsafe_allow_html=True)
    with c4: st.markdown(metric("Total Commission", f"₹{revenue.get('total_commission', 0):,.2f}", "", "purple"), unsafe_allow_html=True)

    st.markdown("---")

    # Revenue chart — fetch daily breakdown
    rev_data = api_get("/admin/revenue", params={"days": 30})
    if rev_data and rev_data.get("daily_breakdown"):
        daily = pd.DataFrame(rev_data["daily_breakdown"])
        col1, col2 = st.columns(2)
        with col1:
            fig = px.line(daily, x="date", y="revenue",
                          title="Daily Revenue — Last 30 Days",
                          markers=True, color_discrete_sequence=[BLUE])
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(l=10,r=10,t=40,b=10), xaxis_title="", yaxis_title="₹")
            fig.update_traces(line_width=2.5)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(daily, x="date", y=["trips", "commission"],
                         title="Daily Trips & Commission",
                         color_discrete_map={"trips": GREEN, "commission": PURPLE},
                         barmode="group")
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(l=10,r=10,t=40,b=10), legend_title="")
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 2 — TRIP TRACKING
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
    df["requested_at"] = pd.to_datetime(df["requested_at"])
    df["Date"] = df["requested_at"].dt.strftime("%Y-%m-%d")
    df["Time"] = df["requested_at"].dt.strftime("%H:%M")
    df["Rider"] = df["rider"].apply(lambda x: x["name"] if x else "—")
    df["Driver"] = df["driver"].apply(lambda x: x["name"] if x else "—")
    df["Fare (₹)"] = df["actual_fare"].fillna(df["estimated_fare"])

    comp = df[df["status"]=="completed"]
    canc = df[df["status"]=="cancelled"]

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(metric("Total trips",   str(len(df))),                             unsafe_allow_html=True)
    with c2: st.markdown(metric("Completed",     str(len(comp)),  "", "green"),             unsafe_allow_html=True)
    with c3: st.markdown(metric("Cancelled",     str(len(canc)),  "", "red"),               unsafe_allow_html=True)
    with c4: st.markdown(metric("Total revenue", f"₹{comp['Fare (₹)'].sum():,.0f}", "", "green"), unsafe_allow_html=True)
    with c5: st.markdown(metric("Avg fare",      f"₹{comp['Fare (₹)'].mean():.0f}" if len(comp) > 0 else "₹0"), unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Trip Records")

    s_f = st.selectbox("Status", ["All","completed","cancelled","requested","accepted","started"])
    filtered = df if s_f == "All" else df[df["status"] == s_f]

    display_cols = ["trip_code","Date","Time","Rider","Driver","vehicle_type",
                    "pickup_address","drop_address","Fare (₹)","status","payment_method"]
    available = [c for c in display_cols if c in filtered.columns]
    st.dataframe(filtered[available].reset_index(drop=True),
                 use_container_width=True, height=400)
    st.caption(f"Showing {len(filtered)} of {len(df)} trips")

    csv = filtered.to_csv(index=False)
    st.download_button("Download trips (CSV)", csv, "kloqride_trips.csv", "text/csv", type="primary")

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 3 — DRIVER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
#  BATCH 1 — Three replacement functions
#  Replace each function in app.py with the matching one below
# ══════════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════════
#  REPLACE: page_drivers()
#  Find: def page_drivers(): ... until next def page_
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

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total     = len(drivers)
    approved  = sum(1 for d in drivers if d["is_approved"])
    online    = sum(1 for d in drivers if d["is_online"])
    on_trip   = sum(1 for d in drivers if d.get("is_on_trip"))
    pending   = total - approved

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(metric("Total Drivers",    str(total),    "", "blue"),   unsafe_allow_html=True)
    with c2: st.markdown(metric("Approved",         str(approved), "", "green"),  unsafe_allow_html=True)
    with c3: st.markdown(metric("Pending",          str(pending),  "", "amber"),  unsafe_allow_html=True)
    with c4: st.markdown(metric("Online Now",       str(online),   "", "purple"), unsafe_allow_html=True)
    with c5: st.markdown(metric("On Trip",          str(on_trip),  "", "blue"),   unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📊 Fleet Overview", "🔘 Approve / Suspend", "🏆 Leaderboard"])

    # ── TAB 1: Fleet Overview ─────────────────────────────────────────────────
    with tab1:
        search = st.text_input("🔍 Search by name or phone", key="drv_search")
        sf     = st.selectbox("Filter", ["All", "Approved", "Pending", "Online"], key="drv_filter")

        filtered = drivers
        if search:
            filtered = [d for d in filtered if
                search.lower() in d["full_name"].lower() or
                search in str(d.get("phone", ""))]
        if sf == "Approved": filtered = [d for d in filtered if d["is_approved"]]
        if sf == "Pending":  filtered = [d for d in filtered if not d["is_approved"]]
        if sf == "Online":   filtered = [d for d in filtered if d["is_online"]]

        rows_html = ""
        for d in filtered:
            v = d.get("vehicle") or {}
            v_str   = f"{v.get('brand','')} {v.get('model','')}".strip() or "—"
            status  = "🟢 Online" if d["is_online"] else ("🔵 On Trip" if d.get("is_on_trip") else "⚫ Offline")
            approved_badge = (
                "<span style='background:#E6F4EA;color:#137333;padding:2px 8px;"
                "border-radius:12px;font-size:11px;font-weight:600;'>✅ Approved</span>"
                if d["is_approved"] else
                "<span style='background:#FEF3CD;color:#856404;padding:2px 8px;"
                "border-radius:12px;font-size:11px;font-weight:600;'>⏳ Pending</span>"
            )
            rows_html += f"""<tr>
              <td style='padding:8px 10px;font-size:13px;font-weight:600;'>{d['full_name']}</td>
              <td style='padding:8px 10px;font-size:12px;'>{d.get('phone','—')}</td>
              <td style='padding:8px 10px;font-size:12px;'>{d.get('city','—')}</td>
              <td style='padding:8px 10px;font-size:12px;'>{v_str}</td>
              <td style='padding:8px 10px;font-size:12px;'>{d.get('avg_rating',0)} ⭐</td>
              <td style='padding:8px 10px;font-size:12px;'>{d.get('total_trips',0)}</td>
              <td style='padding:8px 10px;font-size:12px;'>{status}</td>
              <td style='padding:8px 10px;'>{approved_badge}</td>
            </tr>"""

        st.markdown(f"""
        <table style='width:100%;border-collapse:collapse;background:white;
                      border-radius:10px;overflow:hidden;border:0.5px solid #eee;'>
          <thead style='background:#FFF0E6;'>
            <tr>
              <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>Name</th>
              <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>Phone</th>
              <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>City</th>
              <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>Vehicle</th>
              <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>Rating</th>
              <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>Trips</th>
              <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>Status</th>
              <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>Approval</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)
        st.caption(f"Showing {len(filtered)} of {total} drivers")

        # Charts
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            v_types = {}
            for d in drivers:
                vt = (d.get("vehicle") or {}).get("type", "unknown")
                v_types[vt] = v_types.get(vt, 0) + 1
            vt_df = pd.DataFrame(list(v_types.items()), columns=["Type", "Count"])
            fig = px.pie(vt_df, names="Type", values="Count",
                         title="Fleet by Vehicle Type", hole=0.5)
            fig.update_layout(paper_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            cities = {}
            for d in drivers:
                c = d.get("city", "Unknown")
                cities[c] = cities.get(c, 0) + 1
            city_df = pd.DataFrame(list(cities.items()), columns=["City", "Drivers"])
            city_df = city_df.sort_values("Drivers", ascending=False).head(8)
            fig = px.bar(city_df, x="Drivers", y="City", orientation="h",
                         title="Drivers by City",
                         color_discrete_sequence=[BLUE])
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(l=10,r=10,t=40,b=10),
                              yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

    # ── TAB 2: Approve / Suspend ──────────────────────────────────────────────
    with tab2:
        st.subheader("Approve or Suspend Drivers")
        for d in drivers:
            driver_id   = d["id"]
            name        = d["full_name"]
            is_approved = d["is_approved"]
            phone       = d.get("phone", "")
            city        = d.get("city", "")

            col_info, col_action = st.columns([3, 1])
            with col_info:
                st.markdown(f"""
                <div style='padding:6px 0;'>
                  <span style='font-size:14px;font-weight:700;'>{name}</span>
                  <span style='font-size:12px;color:#888;margin-left:8px;'>
                    {phone} · {city}
                  </span>
                </div>""", unsafe_allow_html=True)
            with col_action:
                if not is_approved:
                    if st.button("✅ Approve", key=f"appr_{driver_id}",
                                 use_container_width=True, type="primary"):
                        result = api_patch(f"/admin/drivers/{driver_id}/approve")
                        if result:
                            st.success(f"✅ {name} approved!")
                            st.rerun()
                else:
                    if st.button("🔴 Suspend", key=f"susp_{driver_id}",
                                 use_container_width=True):
                        result = api_patch(f"/admin/drivers/{driver_id}/approve")
                        if result:
                            st.warning(f"🔴 {name} suspended.")
                            st.rerun()

    # ── TAB 3: Leaderboard ────────────────────────────────────────────────────
    with tab3:
        st.subheader("🏆 Top Drivers by Trips")
        sorted_drivers = sorted(drivers, key=lambda x: x.get("total_trips", 0), reverse=True)
        leaderboard = []
        for i, d in enumerate(sorted_drivers[:20], 1):
            leaderboard.append({
                "Rank"          : i,
                "Name"          : d["full_name"],
                "Phone"         : d.get("phone", ""),
                "City"          : d.get("city", ""),
                "Total Trips"   : d.get("total_trips", 0),
                "Total Earnings": f"₹{d.get('total_earnings', 0):,.0f}",
                "Avg Rating"    : f"{d.get('avg_rating', 0)} ⭐",
            })
        lb_df = pd.DataFrame(leaderboard)
        st.dataframe(lb_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  REPLACE: page_live_map()
#  Find: def page_live_map(): ... until next def page_
# ══════════════════════════════════════════════════════════════════════════════

def page_live_map():
    page_title("🗺️ Live Map / GPS Tracking")
    st.markdown(f"*Real driver locations · Updated {datetime.now().strftime('%H:%M:%S')}*")

    if st.button("🔄 Refresh Locations"):
        st.rerun()

    data = api_get("/admin/drivers")
    if not data:
        st.error("❌ Could not load driver data.")
        return

    drivers = data.get("drivers", [])

    # Only show drivers with location data
    located = [d for d in drivers if d.get("current_lat") and d.get("current_lng")]
    online  = [d for d in drivers if d["is_online"]]
    on_trip = [d for d in drivers if d.get("is_on_trip")]

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(metric("On Map",     str(len(located)),        "", "blue"),   unsafe_allow_html=True)
    with c2: st.markdown(metric("Online",     str(len(online)),         "", "green"),  unsafe_allow_html=True)
    with c3: st.markdown(metric("On Trip",    str(len(on_trip)),        "", "purple"), unsafe_allow_html=True)
    with c4: st.markdown(metric("Offline",    str(len(drivers)-len(online)), "", "red"), unsafe_allow_html=True)

    st.markdown("---")

    # Build folium map centered on Bardhaman/Kolkata
    center_lat = 23.23 if not located else sum(d["current_lat"] for d in located) / len(located)
    center_lng = 87.85 if not located else sum(d["current_lng"] for d in located) / len(located)
    m = folium.Map(location=[center_lat, center_lng], zoom_start=12, tiles="OpenStreetMap")

    if not located:
        st.info("📍 No drivers have shared their location yet. Drivers need to be online and have GPS active.")
    else:
        for d in located:
            lat   = d["current_lat"]
            lng   = d["current_lng"]
            name  = d["full_name"]
            phone = d.get("phone", "")
            v     = d.get("vehicle") or {}
            v_str = f"{v.get('brand','')} {v.get('model','')}".strip() or "—"
            rc    = v.get("rc_number") or "—"

            if d.get("is_on_trip"):
                status_str = "🔵 On Trip"
                pin_color  = "blue"
            elif d["is_online"]:
                status_str = "🟢 Online"
                pin_color  = "green"
            else:
                status_str = "⚫ Offline"
                pin_color  = "gray"

            popup_html = f"""
            <div style='font-family:sans-serif;min-width:180px;'>
                <b style='font-size:14px;'>{name}</b><br>
                <span style='color:#555;font-size:12px;'>📞 {phone}</span><br>
                <span style='font-size:12px;'>{"🏍️" if (vehicle or {}).get("type") == "bike" else "🛺" if (vehicle or {}).get("type") in ["auto","toto"] else "🚗"} {v_str} · {rc}</span><br>
                <span style='font-size:12px;'>Status: <b>{status_str}</b></span><br>
                <span style='font-size:12px;'>⭐ {d.get('avg_rating', 0)} · 
                🛣️ {d.get('total_trips', 0)} trips</span>
            </div>"""

            folium.Marker(
                location=[lat, lng],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{name} — {status_str}",
                icon=folium.Icon(color=pin_color, icon="car", prefix="fa")
            ).add_to(m)

    st_folium(m, width=None, height=500, use_container_width=True)

    st.markdown("""
    <div style='display:flex;gap:20px;justify-content:center;margin:10px 0 16px;'>
        <span>🟢 Online</span> <span>🔵 On Trip</span> <span>⚫ Offline</span>
    </div>""", unsafe_allow_html=True)

    if located:
        st.markdown("---")
        st.subheader("Driver Locations Table")
        loc_rows = [{
            "Name"       : d["full_name"],
            "Phone"      : d.get("phone", ""),
            "City"       : d.get("city", ""),
            "Vehicle"    : f"{(d.get('vehicle') or {}).get('brand','')} {(d.get('vehicle') or {}).get('model','')}".strip(),
            "Status"     : "On Trip" if d.get("is_on_trip") else ("Online" if d["is_online"] else "Offline"),
            "Lat"        : round(d["current_lat"], 5),
            "Lng"        : round(d["current_lng"], 5),
        } for d in located]
        st.dataframe(pd.DataFrame(loc_rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  REPLACE: page_vehicle_mgmt()
#  Find: def page_vehicle_mgmt(): ... until next def page_
# ══════════════════════════════════════════════════════════════════════════════

def page_vehicle_mgmt():
    page_title("🚗 Vehicle Management")

    data = api_get("/admin/drivers")
    if not data:
        st.error("❌ Could not load vehicle data.")
        return

    drivers = data.get("drivers", [])

    # Only drivers with vehicles
    with_vehicle = [d for d in drivers if d.get("vehicle")]

    total     = len(with_vehicle)
    approved  = sum(1 for d in with_vehicle if d["is_approved"])
    on_trip   = sum(1 for d in with_vehicle if d.get("is_on_trip"))
    ins_uploaded = sum(1 for d in with_vehicle if d.get("insurance_url"))

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(metric("Total Vehicles",     str(total),        "", "blue"),   unsafe_allow_html=True)
    with c2: st.markdown(metric("Approved Drivers",   str(approved),     "", "green"),  unsafe_allow_html=True)
    with c3: st.markdown(metric("Currently On Trip",  str(on_trip),      "", "purple"), unsafe_allow_html=True)
    with c4: st.markdown(metric("Insurance Uploaded", str(ins_uploaded), "", "amber"),  unsafe_allow_html=True)

    st.markdown("---")

    # ── Fleet Table ───────────────────────────────────────────────────────────
    st.subheader("Fleet Inventory")

    search = st.text_input("🔍 Search by name or RC number", key="veh_search")
    vtype  = st.selectbox("Filter by Vehicle Type",
                          ["All","bike","auto","toto","mini","sedan","suv","ambulance"],
                          key="veh_type_filter")

    filtered = with_vehicle
    if search:
        filtered = [d for d in filtered if
            search.lower() in d["full_name"].lower() or
            search.upper() in str((d.get("vehicle") or {}).get("rc_number", ""))]
    if vtype != "All":
        filtered = [d for d in filtered if
            (d.get("vehicle") or {}).get("type", "") == vtype]

    rows_html = ""
    for d in filtered:
        v       = d.get("vehicle") or {}
        ins_url = d.get("insurance_url")
        rc_exp  = v.get("rc_expiry_year")
        ins_badge = (
            "<span style='color:#34A853;font-weight:600;'>✅ Uploaded</span>"
            if ins_url else
            "<span style='color:#EA4335;font-weight:600;'>❌ Missing</span>"
        )
        rc_color = "#EA4335" if (rc_exp and rc_exp <= datetime.now().year) else "#34A853"
        approved_badge = (
            "<span style='color:#34A853;font-weight:600;'>✅</span>"
            if d["is_approved"] else
            "<span style='color:#FBBC04;font-weight:600;'>⏳</span>"
        )
        rows_html += f"""<tr>
          <td style='padding:8px 10px;font-size:13px;font-weight:600;'>{d['full_name']}</td>
          <td style='padding:8px 10px;font-size:12px;'>{d.get('phone','—')}</td>
          <td style='padding:8px 10px;font-size:12px;text-transform:capitalize;'>{v.get('type','—')}</td>
          <td style='padding:8px 10px;font-size:12px;'>{v.get('brand','—')} {v.get('model','—')}</td>
          <td style='padding:8px 10px;font-size:12px;'>{v.get('color','—')}</td>
          <td style='padding:8px 10px;font-size:12px;font-weight:600;'>{v.get('rc_number','—')}</td>
          <td style='padding:8px 10px;font-size:12px;color:{rc_color};font-weight:600;'>{rc_exp or '—'}</td>
          <td style='padding:8px 10px;'>{ins_badge}</td>
          <td style='padding:8px 10px;text-align:center;'>{approved_badge}</td>
        </tr>"""

    st.markdown(f"""
    <table style='width:100%;border-collapse:collapse;background:white;
                  border-radius:10px;overflow:hidden;border:0.5px solid #eee;'>
      <thead style='background:#FFF0E6;'>
        <tr>
          <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>Driver</th>
          <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>Phone</th>
          <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>Type</th>
          <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>Brand/Model</th>
          <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>Color</th>
          <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>RC Number</th>
          <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>RC Expiry</th>
          <th style='padding:10px;text-align:left;font-size:12px;color:#555;'>Insurance</th>
          <th style='padding:10px;text-align:center;font-size:12px;color:#555;'>Approved</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>""", unsafe_allow_html=True)
    st.caption(f"Showing {len(filtered)} of {total} vehicles")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        v_types = {}
        for d in with_vehicle:
            vt = (d.get("vehicle") or {}).get("type", "unknown")
            v_types[vt] = v_types.get(vt, 0) + 1
        vt_df = pd.DataFrame(list(v_types.items()), columns=["Type","Count"])
        fig = px.pie(vt_df, names="Type", values="Count",
                     title="Fleet by Vehicle Type", hole=0.5)
        fig.update_layout(paper_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        ins_data = {
            "Insurance": ["Uploaded", "Missing"],
            "Count"    : [ins_uploaded, total - ins_uploaded]
        }
        fig = go.Figure(go.Pie(
            labels=ins_data["Insurance"], values=ins_data["Count"],
            hole=0.5,
            marker_colors=[GREEN, RED],
            textinfo="label+percent"
        ))
        fig.update_layout(title="Insurance Status",
                          paper_bgcolor="white",
                          margin=dict(l=10,r=10,t=40,b=10),
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Export
    st.markdown("---")
    export_rows = [{
        "Driver"       : d["full_name"],
        "Phone"        : d.get("phone", ""),
        "Type"         : (d.get("vehicle") or {}).get("type", ""),
        "Brand"        : (d.get("vehicle") or {}).get("brand", ""),
        "Model"        : (d.get("vehicle") or {}).get("model", ""),
        "Color"        : (d.get("vehicle") or {}).get("color", ""),
        "RC Number"    : (d.get("vehicle") or {}).get("rc_number", ""),
        "Reg Year"     : (d.get("vehicle") or {}).get("registration_year", ""),
        "RC Expiry"    : (d.get("vehicle") or {}).get("rc_expiry_year", ""),
        "Insurance"    : "Yes" if d.get("insurance_url") else "No",
        "Approved"     : "Yes" if d["is_approved"] else "No",
    } for d in with_vehicle]

    import io as _io
    buf = _io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pd.DataFrame(export_rows).to_excel(writer, index=False, sheet_name="Vehicles")
    st.download_button("📥 Download Fleet (Excel)", data=buf.getvalue(),
                       file_name="kloqride_fleet.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       type="primary")

def page_driver_document_upload():
    import requests as _req
    import io as _io

    page_title("📄 Driver Documents", "View, verify and approve driver documents")

    # ── Fetch real drivers from backend ───────────────────────────────────────
    data = api_get("/admin/drivers")
    if not data:
        st.error("❌ Could not load drivers. Check API connection.")
        return

    real_drivers = data.get("drivers", [])
    if not real_drivers:
        st.info("No drivers registered yet.")
        return

    # ── KPI summary ───────────────────────────────────────────────────────────
    total      = len(real_drivers)
    approved   = sum(1 for d in real_drivers if d["is_approved"])
    pending    = total - approved
    online_now = sum(1 for d in real_drivers if d.get("is_online"))

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(metric("Total Drivers",    str(total),    "", "blue"),   unsafe_allow_html=True)
    with k2: st.markdown(metric("Approved",         str(approved), "", "green"),  unsafe_allow_html=True)
    with k3: st.markdown(metric("Pending Approval", str(pending),  "", "amber"),  unsafe_allow_html=True)
    with k4: st.markdown(metric("Online Now",       str(online_now),"","purple"), unsafe_allow_html=True)

    st.markdown("---")

    # ── Search + filter ───────────────────────────────────────────────────────
    sc, fc = st.columns([3, 1])
    with sc:
        search = st.text_input("🔍 Search by name or phone",
                               placeholder="e.g. Ravi or 98xxxxxxxx",
                               key="ddp_search")
    with fc:
        f_status = st.selectbox("Filter", ["All", "Pending", "Approved"],
                                key="ddp_filter")

    filtered = []
    for d in real_drivers:
        if search:
            if (search.lower() not in d["full_name"].lower() and
                search not in str(d.get("phone", ""))):
                continue
        if f_status == "Pending"  and d["is_approved"]: continue
        if f_status == "Approved" and not d["is_approved"]: continue
        filtered.append(d)

    st.caption(f"Showing {len(filtered)} of {total} drivers")
    st.markdown("---")

    # ── Doc config ────────────────────────────────────────────────────────────
    DOC_CONFIG = [
        {"key": "profile_pic",   "label": "👤 Profile Picture",  "api_key": "profile_pic",   "required": True},
        {"key": "dl_front",  "label": "🪪 DL — Front",        "api_key": "dl_front",      "required": True},
        {"key": "dl_back",   "label": "🪪 DL — Back",         "api_key": "dl_back",       "required": True},
        {"key": "rc_front",  "label": "📋 RC — Front",        "api_key": "rc_front",      "required": True},
        {"key": "rc_back",   "label": "📋 RC — Back",         "api_key": "rc_back",       "required": True},
        {"key": "aadhaar_front","label": "🆔 Aadhaar — Front","api_key": "aadhaar_front", "required": True},
        {"key": "aadhaar_back", "label": "🆔 Aadhaar — Back", "api_key": "aadhaar_back",  "required": True},
        {"key": "insurance", "label": "🛡️ Insurance",         "api_key": "insurance",     "required": True},
        {"key": "permit",    "label": "📄 Permit",            "api_key": "permit",        "required": False},
    ]
    REQUIRED_KEYS = [d["key"] for d in DOC_CONFIG if d["required"]]

    # ── Per-driver expander cards ─────────────────────────────────────────────
    for driver in filtered:
        driver_id   = driver["id"]
        name        = driver["full_name"]
        phone       = driver.get("phone", "")
        is_approved = driver["is_approved"]
        city        = driver.get("city", "N/A")
        state       = driver.get("state", "")
        vehicle     = driver.get("vehicle")
        v_str       = (f"{vehicle['brand']} {vehicle['model']} · {vehicle['color']}"
                       if vehicle else "No vehicle")

        # Status badge
        badge = ("<span style='background:#E6F4EA;color:#137333;padding:3px 10px;"
                 "border-radius:20px;font-size:11px;font-weight:600;'>✅ Approved</span>"
                 if is_approved else
                 "<span style='background:#FEF3CD;color:#856404;padding:3px 10px;"
                 "border-radius:20px;font-size:11px;font-weight:600;'>⏳ Pending</span>")

        with st.expander(
            f"{'✅' if is_approved else '⏳'}  {name}  ·  {phone}  ·  {city}",
            expanded=False
        ):
            # ── Driver info card ──────────────────────────────────────────────
            st.markdown(f"""
            <div style='background:#f8f9fa;border-radius:10px;
                        padding:12px 16px;margin-bottom:16px;'>
                <b style='font-size:15px;'>{name}</b>
                <span style='margin-left:12px;'>{badge}</span><br>
                <span style='font-size:12px;color:#666;'>
                📞 {phone} &nbsp;·&nbsp; 🚗 {v_str} &nbsp;·&nbsp;
                📍 {city}, {state}
                </span>
            </div>""", unsafe_allow_html=True)

            # ── Document text details ─────────────────────────────────────────
            st.markdown("#### 📋 Document Details")
            dc1, dc2, dc3 = st.columns(3)

            with dc1:
                st.markdown("**🪪 Driving Licence**")
                st.markdown(f"""
                <div style='background:#f0f4ff;border-radius:8px;padding:10px;font-size:12px;'>
                <b>DL Number:</b> {driver.get('license_number') or '—'}<br>
                <b>Expiry:</b> {driver.get('license_expiry') or '—'}
                </div>""", unsafe_allow_html=True)

            with dc2:
                st.markdown("**📋 RC (Registration)**")
                v = driver.get("vehicle") or {}
                st.markdown(f"""
                <div style='background:#f0fff4;border-radius:8px;padding:10px;font-size:12px;'>
                <b>RC Number:</b> {v.get('rc_number') or '—'}<br>
                <b>Reg Year:</b> {v.get('registration_year') or '—'}<br>
                <b>Expiry Year:</b> {v.get('rc_expiry_year') or '—'}
                </div>""", unsafe_allow_html=True)

            with dc3:
                st.markdown("**🆔 Aadhaar**")
                aadhar = driver.get("aadhar_number") or "—"
                # Mask middle digits for privacy
                if aadhar != "—" and len(aadhar) >= 8:
                    masked = aadhar[:4] + " **** " + aadhar[-4:]
                else:
                    masked = aadhar
                st.markdown(f"""
                <div style='background:#fff8f0;border-radius:8px;padding:10px;font-size:12px;'>
                <b>Aadhaar Number:</b><br>{masked}
                </div>""", unsafe_allow_html=True)

            st.markdown("---")

            # ── Fetch / cache document URLs ───────────────────────────────────
            cache_key = f"docs_cache_{driver_id}"
            if cache_key not in st.session_state:
                doc_data = api_get(f"/documents/{driver_id}")
                st.session_state[cache_key] = doc_data if doc_data else {}

            doc_data = st.session_state[cache_key]

            # Count uploaded docs
            uploaded_n = sum(1 for cfg in DOC_CONFIG if doc_data.get(cfg["key"]))
            total_n    = len(DOC_CONFIG)
            progress   = uploaded_n / total_n if total_n > 0 else 0
            bar_color  = "#34A853" if progress == 1.0 else "#FBBC04" if progress > 0.5 else "#EA4335"

            # Progress bar
            st.markdown(f"""
            <div style='margin-bottom:12px;'>
                <div style='display:flex;justify-content:space-between;margin-bottom:4px;'>
                    <span style='font-size:12px;font-weight:600;color:#333;'>
                        Documents Uploaded</span>
                    <span style='font-size:12px;color:{bar_color};font-weight:700;'>
                        {uploaded_n}/{total_n}</span>
                </div>
                <div style='background:#e0e0e0;border-radius:10px;height:8px;'>
                    <div style='background:{bar_color};width:{int(progress*100)}%;
                                height:8px;border-radius:10px;'></div>
                </div>
            </div>""", unsafe_allow_html=True)

            st.markdown("#### 📂 Document Images")

            # ── Document image grid ───────────────────────────────────────────
            cols_per_row = 3
            for i in range(0, len(DOC_CONFIG), cols_per_row):
                row_docs = DOC_CONFIG[i:i + cols_per_row]
                cols = st.columns(cols_per_row)

                for col, cfg in zip(cols, row_docs):
                    doc_url = doc_data.get(cfg["key"])
                    api_key = cfg["api_key"]
                    label   = cfg["label"]

                    with col:
                        st.markdown(f"**{label}**")

                        if doc_url:
                            # Show Cloudinary image
                            st.image(doc_url, use_container_width=True)
                            st.markdown(
                                f"<div style='font-size:10px;color:#34A853;"
                                f"text-align:center;'>✅ Uploaded</div>",
                                unsafe_allow_html=True)
                            st.markdown(
                                f"<a href='{doc_url}' target='_blank' "
                                f"style='font-size:10px;color:#4285F4;'>"
                                f"🔗 Open full size</a>",
                                unsafe_allow_html=True)

                            # Profile pic — admin-only replace
                            if cfg["key"] == "profile_pic":
                                st.markdown(
                                    "<div style='font-size:10px;color:#856404;"
                                    "background:#FEF3CD;border-radius:6px;"
                                    "padding:4px 8px;text-align:center;"
                                    "margin-top:4px;'>🔒 Admin-only replace</div>",
                                    unsafe_allow_html=True)
                        else:
                            st.markdown(
                                "<div style='background:#FCE8E6;border-radius:8px;"
                                "padding:8px;text-align:center;font-size:11px;"
                                "color:#9A0000;margin-bottom:6px;'>"
                                "❌ Not uploaded</div>",
                                unsafe_allow_html=True)

                        # Upload widget (always visible for replacement)
                        up_key   = f"up_{driver_id}_{api_key}"
                        new_file = st.file_uploader(
                            "Replace" if doc_url else "Upload",
                            type=["jpg", "jpeg", "png", "pdf"],
                            key=up_key,
                            label_visibility="collapsed"
                        )

                        if new_file is not None:
                            token = st.session_state.get("admin_token", "")
                            with st.spinner(f"Uploading {label}..."):
                                try:
                                    up_res = _req.post(
                                        f"{API_BASE}/documents/upload/{driver_id}/{api_key}",
                                        headers={"Authorization": f"Bearer {token}"},
                                        files={"file": (new_file.name,
                                                        new_file.read(),
                                                        new_file.type)},
                                        timeout=30
                                    )
                                    if up_res.status_code == 200:
                                        st.success(f"✅ {label} uploaded!")
                                        if cache_key in st.session_state:
                                            del st.session_state[cache_key]
                                        st.rerun()
                                    else:
                                        st.error(f"Upload failed ({up_res.status_code}): "
                                                 f"{up_res.json().get('detail', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Upload error: {e}")

            st.markdown("---")

            # ── Approve / Suspend buttons ─────────────────────────────────────
            required_uploaded = all(doc_data.get(k) for k in REQUIRED_KEYS)

            ca, cs, cr = st.columns([2, 2, 1])

            with ca:
                if not is_approved:
                    if required_uploaded:
                        if st.button("✅ Approve Driver",
                                     key=f"approve_{driver_id}",
                                     type="primary",
                                     use_container_width=True):
                            result = api_patch(f"/admin/drivers/{driver_id}/approve")
                            if result:
                                st.success(f"✅ {name} approved!")
                                st.rerun()
                            else:
                                st.error("Approval failed. Try again.")
                    else:
                        missing = [cfg["label"] for cfg in DOC_CONFIG
                                   if cfg["required"] and not doc_data.get(cfg["key"])]
                        st.warning(f"⏳ Missing: {', '.join(missing)}")
                else:
                    st.success("✅ Driver is Approved")

            with cs:
                if is_approved:
                    if st.button("🔴 Suspend Driver",
                                 key=f"suspend_{driver_id}",
                                 use_container_width=True):
                        result = api_patch(f"/admin/drivers/{driver_id}/approve")
                        if result:
                            st.warning(f"🔴 {name} suspended.")
                            st.rerun()
                        else:
                            st.error("Suspend failed.")

            with cr:
                if st.button("🔄", key=f"refresh_{driver_id}",
                             help="Refresh documents",
                             use_container_width=True):
                    if cache_key in st.session_state:
                        del st.session_state[cache_key]
                    st.rerun()

    # ── Export Excel ──────────────────────────────────────────────────────────
    st.markdown("---")
    export_rows = [{
        "ID"            : d["id"],
        "Name"          : d["full_name"],
        "Phone"         : d.get("phone", ""),
        "City"          : d.get("city", ""),
        "State"         : d.get("state", ""),
        "Vehicle"       : (f"{d['vehicle']['brand']} {d['vehicle']['model']}"
                           if d.get("vehicle") else ""),
        "RC Number"     : (d["vehicle"].get("rc_number") or ""
                           if d.get("vehicle") else ""),
        "DL Number"     : d.get("license_number") or "",
        "Aadhaar"       : d.get("aadhar_number") or "",
        "Approved"      : "Yes" if d["is_approved"] else "No",
        "Avg Rating"    : d.get("avg_rating", 0),
        "Total Trips"   : d.get("total_trips", 0),
        "Joined"        : str(d.get("created_at", ""))[:10],
    } for d in real_drivers]

    export_df = pd.DataFrame(export_rows)
    buf = _io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Drivers")

    st.download_button(
        "📥 Download All Drivers (Excel)",
        data=buf.getvalue(),
        file_name="kloqride_drivers.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 4 — REVENUE
# ══════════════════════════════════════════════════════════════════════════════
def page_revenue():
    page_title("💰 Revenue & Earnings Reports")

    period = st.radio("Period", ["Last 7 days","Last 30 days","Last 60 days"], horizontal=True)
    n = {"Last 7 days":7,"Last 30 days":30,"Last 60 days":60}[period]
    
    # Fetch real revenue data
    data = api_get("/admin/revenue", params={"days": n})
    if not data:
        st.error("❌ Could not load revenue data.")
        return

    daily = pd.DataFrame(data.get("daily_breakdown", []))

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(metric("Total revenue",   f"₹{data.get('total_revenue', 0):,.2f}", "", "green"), unsafe_allow_html=True)
    with c2: st.markdown(metric("Total trips",     str(data.get('total_trips', 0))),                      unsafe_allow_html=True)
    with c3: st.markdown(metric("Total commission",f"₹{data.get('total_commission', 0):,.2f}", "", "purple"), unsafe_allow_html=True)
    with c4: st.markdown(metric("Avg daily rev",   f"₹{daily['revenue'].mean():,.0f}" if len(daily) > 0 else "₹0"), unsafe_allow_html=True)
    with c5: st.markdown(metric("Period",          f"{n} days"), unsafe_allow_html=True)

    st.markdown("---")

    if len(daily) == 0:
        st.info("No revenue data found for this period. Start completing trips to see data here!")
        return

    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(daily, x="date", y="revenue",
                      title=f"Daily Revenue ({period})",
                      markers=True, color_discrete_sequence=[BLUE])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                          margin=dict(l=10,r=10,t=40,b=10), xaxis_title="", yaxis_title="₹")
        fig.update_traces(line_width=2.5)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(daily, x="date", y=["trips","commission"],
                     title=f"Trips & Commission ({period})",
                     color_discrete_map={"trips":GREEN,"commission":PURPLE},
                     barmode="group")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                          margin=dict(l=10,r=10,t=40,b=10), legend_title="")
        st.plotly_chart(fig, use_container_width=True)

    fig = px.area(daily, x="date", y="revenue",
                  title="Revenue Trend (Area Chart)",
                  color_discrete_sequence=[BLUE])
    fig.update_traces(fill="tozeroy", line_width=2)
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                      margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Daily Breakdown")
    st.dataframe(daily.sort_values("date", ascending=False).reset_index(drop=True),
                 use_container_width=True, height=320)

    csv = daily.to_csv(index=False)
    st.download_button(f"Download {period} report (CSV)", csv,
                       f"kloqride_revenue_{n}d.csv", "text/csv")



# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 6 — NOTIFICATIONS & ALERTS
# ══════════════════════════════════════════════════════════════════════════════
def page_notifications():
    page_title("🔔 Notifications & Alerts")

    # Fetch real data to generate smart alerts
    overview  = api_get("/admin/overview") or {}
    drv_data  = api_get("/admin/drivers")  or {}
    trip_data = api_get("/admin/trips", params={"limit": 100}) or {}

    drivers = drv_data.get("drivers", [])
    trips   = trip_data.get("trips",  [])
    rev     = overview.get("revenue", {})

    # ── Build smart alerts from real data ─────────────────────────────────────
    alerts = []

    # Pending driver approvals
    pending_drivers = [d for d in drivers if not d["is_approved"]]
    if pending_drivers:
        alerts.append({
            "Title"      : f"⏳ {len(pending_drivers)} Driver(s) Awaiting Approval",
            "Description": ", ".join(d["full_name"] for d in pending_drivers[:3]) +
                           (" and more..." if len(pending_drivers) > 3 else ""),
            "Type"       : "New Driver",
            "Priority"   : "High" if len(pending_drivers) > 2 else "Medium",
            "Time"       : "Now",
        })

    # Low rated drivers
    low_rated = [d for d in drivers
                 if d.get("avg_rating", 5) < 4.0 and d.get("total_trips", 0) > 5]
    for d in low_rated[:3]:
        alerts.append({
            "Title"      : f"⭐ Low Rating — {d['full_name']}",
            "Description": f"Rating: {d.get('avg_rating', 0)} · {d.get('total_trips', 0)} trips · {d.get('city', '')}",
            "Type"       : "Low Rating",
            "Priority"   : "Medium",
            "Time"       : "Recent",
        })

    # Recent cancellations
    cancelled = [t for t in trips if t.get("status") == "cancelled"]
    if cancelled:
        alerts.append({
            "Title"      : f"❌ {len(cancelled)} Cancelled Trips",
            "Description": f"Out of last {len(trips)} trips — "
                           f"{round(len(cancelled)/len(trips)*100 if trips else 0, 1)}% cancellation rate",
            "Type"       : "System",
            "Priority"   : "High" if len(cancelled) > 10 else "Low",
            "Time"       : "Today",
        })

    # Active trips right now
    active = [t for t in trips
              if t.get("status") in ["requested", "accepted", "arrived", "started"]]
    if active:
        alerts.append({
            "Title"      : f"🚖 {len(active)} Active Trip(s) Right Now",
            "Description": "Trips currently in progress on the platform",
            "Type"       : "System",
            "Priority"   : "Low",
            "Time"       : "Now",
        })

    # Approved drivers missing documents
    no_docs = [d for d in drivers
               if not d.get("dl_front_url") and d["is_approved"]]
    if no_docs:
        alerts.append({
            "Title"      : f"📄 {len(no_docs)} Approved Driver(s) Missing Documents",
            "Description": "These drivers are approved but haven't uploaded all documents yet",
            "Type"       : "System",
            "Priority"   : "High",
            "Time"       : "Check Now",
        })

    # Today's revenue
    today_rev = rev.get("today", 0)
    if today_rev > 0:
        alerts.append({
            "Title"      : f"💰 Today's Revenue: ₹{today_rev:,.2f}",
            "Description": f"Total platform commission earned: ₹{rev.get('total_commission', 0):,.2f}",
            "Type"       : "Payment",
            "Priority"   : "Low",
            "Time"       : "Today",
        })

    # Offline approved drivers
    offline_approved = [d for d in drivers
                        if d["is_approved"] and not d["is_online"]]
    if offline_approved:
        alerts.append({
            "Title"      : f"⚫ {len(offline_approved)} Approved Driver(s) Currently Offline",
            "Description": "These drivers are approved but not currently online",
            "Type"       : "System",
            "Priority"   : "Low",
            "Time"       : "Now",
        })

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total = len(alerts)
    high  = sum(1 for a in alerts if a["Priority"] == "High")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric("Total Alerts",     str(total)),                               unsafe_allow_html=True)
    with c2: st.markdown(metric("High Priority",    str(high),               "", "red"),       unsafe_allow_html=True)
    with c3: st.markdown(metric("Pending Drivers",  str(len(pending_drivers)),"", "amber"),    unsafe_allow_html=True)
    with c4: st.markdown(metric("Active Trips Now", str(len(active)),        "", "green"),     unsafe_allow_html=True)

    st.markdown("---")

    if st.button("🔄 Refresh Alerts"):
        st.rerun()

    # ── Filters ───────────────────────────────────────────────────────────────
    prio_colors = {"Critical": "#EA4335", "High": "#FF6D01",
                   "Medium":   "#FBBC04", "Low":  "#34A853"}
    prio_bg     = {"Critical": "#FCE8E6", "High": "#FFF3E0",
                   "Medium":   "#FEF3CD", "Low":  "#E6F4EA"}

    f1, f2 = st.columns(2)
    type_filter = f1.selectbox("Filter by Type",
        ["All", "New Driver", "Low Rating", "Payment", "System"],
        key="notif_type")
    prio_filter = f2.selectbox("Filter by Priority",
        ["All", "Critical", "High", "Medium", "Low"],
        key="notif_prio")

    filtered = alerts
    if type_filter != "All":
        filtered = [a for a in filtered if a["Type"] == type_filter]
    if prio_filter != "All":
        filtered = [a for a in filtered if a["Priority"] == prio_filter]

    if not filtered:
        st.success("✅ No alerts matching the filter. Platform looks healthy!")
    else:
        for a in filtered:
            border_c = prio_colors.get(a["Priority"], "#ccc")
            bg_c     = prio_bg.get(a["Priority"],     "#f9f9f9")
            st.markdown(f"""
            <div style='background:{bg_c};border-left:4px solid {border_c};
                        padding:14px 18px;border-radius:0 10px 10px 0;
                        margin-bottom:10px;'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                        <div style='font-size:14px;font-weight:700;color:#111111;'>
                            {a['Title']}
                        </div>
                        <div style='font-size:13px;color:#555;margin-top:4px;'>
                            {a['Description']}
                        </div>
                    </div>
                    <div style='text-align:right;min-width:80px;'>
                        <span style='background:{border_c};color:white;padding:3px 8px;
                                     border-radius:12px;font-size:11px;font-weight:600;'>
                            {a['Priority']}
                        </span>
                        <div style='font-size:11px;color:#888;margin-top:6px;'>
                            {a['Time']}
                        </div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.caption(f"Showing {len(filtered)} of {total} alerts")

    # ── Charts ────────────────────────────────────────────────────────────────
    if alerts:
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            type_counts = {}
            for a in alerts:
                type_counts[a["Type"]] = type_counts.get(a["Type"], 0) + 1
            tc_df = pd.DataFrame(list(type_counts.items()), columns=["Type", "Count"])
            fig = px.bar(tc_df, x="Count", y="Type", orientation="h",
                         title="Alerts by Type",
                         color_discrete_sequence=[BLUE])
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(l=10, r=10, t=40, b=10),
                              yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            prio_counts = {}
            for a in alerts:
                prio_counts[a["Priority"]] = prio_counts.get(a["Priority"], 0) + 1
            pc_df = pd.DataFrame(list(prio_counts.items()), columns=["Priority", "Count"])
            fig = go.Figure(go.Bar(
                x=pc_df["Priority"], y=pc_df["Count"],
                marker_color=[prio_colors.get(p, BLUE) for p in pc_df["Priority"]],
                text=pc_df["Count"], textposition="auto"
            ))
            fig.update_layout(title="Alerts by Priority",
                              plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
def page_ride_history():
    page_title("🧾 Ride History — Customer View")

    # Fetch real riders from backend
    users_data = api_get("/admin/users", params={"role": "rider", "limit": 200})
    if not users_data:
        st.error("❌ Could not load riders.")
        return

    riders = users_data.get("users", [])
    if not riders:
        st.info("No riders registered yet.")
        return

    # Search by phone
    phone_search = st.text_input(
        "🔍 Search Rider by Phone",
        placeholder="Enter full or partial phone number",
        key="rh_phone")

    if phone_search:
        riders = [r for r in riders if phone_search in str(r.get("phone", ""))]
        if not riders:
            st.warning("No rider found with that phone number.")
            return

    rider_names = [f"{r['full_name']} — {r['phone']}" for r in riders]
    selected    = st.selectbox("Select Rider", rider_names, key="rh_select")
    rider       = riders[rider_names.index(selected)]

    # ── Rider profile card ─────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#FFF0E6,#FFF0E6);
                border-radius:12px;padding:20px 24px;margin:12px 0 20px;
                border:1px solid #d4e0f7;'>
        <div style='display:flex;justify-content:space-between;
                    align-items:center;flex-wrap:wrap;'>
            <div>
                <div style='font-size:1.3rem;font-weight:800;color:#111111;'>
                    👤 {rider['full_name']}
                </div>
                <div style='font-size:13px;color:#555;margin-top:4px;'>
                    📱 {rider['phone']} &nbsp;·&nbsp;
                    ✉️ {rider.get('email') or '—'}
                </div>
                <div style='font-size:12px;color:#888;margin-top:2px;'>
                    Member since {str(rider.get('created_at',''))[:10]}
                </div>
            </div>
            <div style='text-align:right;'>
                <div style='font-size:11px;color:#888;'>RIDER ID</div>
                <div style='font-size:1.1rem;font-weight:700;color:#FF6B00;'>
                    #{rider['id']}
                </div>
                <div style='font-size:12px;margin-top:4px;'>
                    💰 Wallet: ₹{rider.get('wallet_balance', 0):,.2f}
                </div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Fetch real trips ───────────────────────────────────────────────────────
    trips_data = api_get("/admin/trips", params={"limit": 200})
    all_trips  = trips_data.get("trips", []) if trips_data else []

    # Filter trips for this rider by phone
    rider_trips = [t for t in all_trips
                   if t.get("rider") and
                   t["rider"].get("phone") == rider["phone"]]

    completed   = [t for t in rider_trips if t["status"] == "completed"]
    cancelled   = [t for t in rider_trips if t["status"] == "cancelled"]
    total_spent = sum(t.get("actual_fare") or t.get("estimated_fare") or 0
                      for t in completed)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric("Total Rides",  str(len(rider_trips))),                    unsafe_allow_html=True)
    with c2: st.markdown(metric("Completed",    str(len(completed)),  "", "green"),        unsafe_allow_html=True)
    with c3: st.markdown(metric("Cancelled",    str(len(cancelled)),  "", "red"),          unsafe_allow_html=True)
    with c4: st.markdown(metric("Total Spent",  f"₹{total_spent:,.0f}", "", "blue"),       unsafe_allow_html=True)

    st.markdown("---")

    if not rider_trips:
        st.info("No trips found for this rider yet.")
        return

    # ── Build dataframe ────────────────────────────────────────────────────────
    rows = []
    for t in rider_trips:
        rows.append({
            "Date"      : str(t.get("requested_at", ""))[:10],
            "Time"      : str(t.get("requested_at", ""))[11:16],
            "Trip Code" : t.get("trip_code", "—"),
            "Pickup"    : t.get("pickup_address", "—"),
            "Drop"      : t.get("drop_address",   "—"),
            "Driver"    : (t.get("driver") or {}).get("name", "—"),
            "Fare (₹)"  : t.get("actual_fare") or t.get("estimated_fare") or 0,
            "Payment"   : t.get("payment_method", "—"),
            "Status"    : t.get("status", "—"),
        })
    rt_df = pd.DataFrame(rows)

    # ── Charts ─────────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        rt_df["Month"] = pd.to_datetime(rt_df["Date"],
                                         errors="coerce").dt.to_period("M").astype(str)
        monthly = (rt_df[rt_df["Status"] == "completed"]
                   .groupby("Month")["Fare (₹)"].sum().reset_index())
        if not monthly.empty:
            fig = px.line(monthly, x="Month", y="Fare (₹)",
                          title=f"Monthly Spending — {rider['full_name']}",
                          markers=True, color_discrete_sequence=[BLUE])
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(l=10, r=10, t=40, b=10),
                              xaxis_title="", yaxis_title="₹")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No completed trips to chart yet.")

    with col2:
        status_counts = rt_df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        colors_map = {
            "completed": GREEN, "cancelled": RED,
            "requested": AMBER, "accepted":  BLUE, "started": PURPLE
        }
        fig = go.Figure(go.Pie(
            labels=status_counts["Status"],
            values=status_counts["Count"],
            hole=0.5,
            marker_colors=[colors_map.get(s, BLUE)
                           for s in status_counts["Status"]],
            textinfo="label+percent"
        ))
        fig.update_layout(title="Trip Status Breakdown",
                          paper_bgcolor="white",
                          margin=dict(l=10, r=10, t=40, b=10),
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # ── Trip table ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Trip History")
    st.dataframe(
        rt_df.sort_values("Date", ascending=False).reset_index(drop=True),
        use_container_width=True, height=350, hide_index=True)

    csv = rt_df.to_csv(index=False)
    st.download_button(
        f"📥 Download {rider['full_name']}'s rides (CSV)",
        csv,
        f"kloqride_{rider['full_name'].replace(' ', '_')}.csv",
        "text/csv")
    
#  PAGE 7 — RIDE HISTORY (CUSTOMER VIEW)
# ══════════════════════════════════════════════════════════════════════════════
def page_driver_performance():
    page_title("📈 Driver Performance Analytics")

    # Fetch real drivers and trips
    drv_data  = api_get("/admin/drivers")
    trip_data = api_get("/admin/trips", params={"limit": 200})

    if not drv_data or not trip_data:
        st.error("❌ Could not load data.")
        return

    drivers   = drv_data.get("drivers",  [])
    all_trips = trip_data.get("trips",   [])

    if not drivers:
        st.info("No drivers registered yet.")
        return

    # ── Driver selector ────────────────────────────────────────────────────────
    driver_names = [f"{d['full_name']} — {d.get('phone','')}" for d in drivers]
    selected     = st.selectbox("Select Driver", driver_names, key="dp_select")
    drv          = drivers[driver_names.index(selected)]
    driver_phone = drv.get("phone", "")

    # Filter trips for this driver by phone
    drv_trips = [t for t in all_trips
                 if t.get("driver") and
                 t["driver"].get("phone") == driver_phone]
    completed = [t for t in drv_trips if t["status"] == "completed"]
    cancelled = [t for t in drv_trips if t["status"] == "cancelled"]

    comp_rate  = (len(completed) / len(drv_trips) * 100) if drv_trips else 0
    total_earn = sum(t.get("driver_earnings") or 0 for t in completed)
    avg_fare   = (sum(t.get("actual_fare") or 0 for t in completed) / len(completed)
                  if completed else 0)

    # ── Driver profile card ────────────────────────────────────────────────────
    v          = drv.get("vehicle") or {}
    v_str      = f"{v.get('brand','')} {v.get('model','')}".strip() or "—"
    status_str = ("🔵 On Trip" if drv.get("is_on_trip") else
                  "🟢 Online"  if drv["is_online"]      else "⚫ Offline")
    approved   = "✅ Approved" if drv["is_approved"] else "⏳ Pending"

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#FFF0E6,#FFF0E6);
                border-radius:12px;padding:20px 24px;margin:12px 0 20px;
                border:1px solid #d4e0f7;'>
        <div style='display:flex;justify-content:space-between;
                    align-items:center;flex-wrap:wrap;'>
            <div>
                <div style='font-size:1.3rem;font-weight:800;color:#111111;'>
                    🚗 {drv['full_name']}
                </div>
                <div style='font-size:13px;color:#555;margin-top:4px;'>
                    {v_str} &nbsp;·&nbsp; {drv.get('city','—')} &nbsp;·&nbsp; {driver_phone}
                </div>
                <div style='font-size:12px;color:#888;margin-top:2px;'>
                    Joined {str(drv.get('created_at',''))[:10]}
                </div>
            </div>
            <div style='text-align:right;'>
                <div style='font-size:13px;font-weight:600;'>{status_str}</div>
                <div style='font-size:12px;margin-top:4px;'>{approved}</div>
                <div style='font-size:1.1rem;font-weight:700;
                            color:#FF6B00;margin-top:4px;'>
                    {drv.get('avg_rating', 0)} ⭐
                </div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── KPIs ───────────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.markdown(metric("Total Trips",       str(len(drv_trips))),                  unsafe_allow_html=True)
    with c2: st.markdown(metric("Completion Rate",   f"{comp_rate:.0f}%",  "", "green"),    unsafe_allow_html=True)
    with c3: st.markdown(metric("Avg Rating",        f"{drv.get('avg_rating', 0)} ⭐", "", "amber"), unsafe_allow_html=True)
    with c4: st.markdown(metric("Total Earnings",    f"₹{total_earn:,.0f}", "", "green"),   unsafe_allow_html=True)
    with c5: st.markdown(metric("Avg Fare",          f"₹{avg_fare:.0f}",   "", "purple"),   unsafe_allow_html=True)

    st.markdown("---")

    # ── Charts ─────────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        # All drivers comparison by trips
        driver_stats = []
        for d in drivers:
            d_phone = d.get("phone", "")
            d_trips = [t for t in all_trips
                       if t.get("driver") and
                       t["driver"].get("phone") == d_phone and
                       t["status"] == "completed"]
            driver_stats.append({
                "Driver"  : d["full_name"],
                "Trips"   : len(d_trips),
                "Earnings": sum(t.get("driver_earnings") or 0 for t in d_trips),
            })
        ds_df = pd.DataFrame(driver_stats).sort_values(
            "Trips", ascending=False).head(10)

        colors = [GREEN if d == drv["full_name"] else "#D4E0F7"
                  for d in ds_df["Driver"]]
        fig = go.Figure(go.Bar(
            x=ds_df["Driver"], y=ds_df["Trips"],
            marker_color=colors,
            text=ds_df["Trips"], textposition="auto"
        ))
        fig.update_layout(title="Trip Comparison — Top 10 Drivers",
                          plot_bgcolor="white", paper_bgcolor="white",
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Trip status breakdown for selected driver
        if drv_trips:
            status_counts = {}
            for t in drv_trips:
                s = t["status"]
                status_counts[s] = status_counts.get(s, 0) + 1
            sc_df = pd.DataFrame(list(status_counts.items()),
                                 columns=["Status", "Count"])
            colors_map = {
                "completed": GREEN, "cancelled": RED,
                "requested": AMBER, "accepted":  BLUE, "started": PURPLE
            }
            fig = go.Figure(go.Pie(
                labels=sc_df["Status"], values=sc_df["Count"], hole=0.55,
                marker_colors=[colors_map.get(s, BLUE) for s in sc_df["Status"]],
                textinfo="label+percent"
            ))
            fig.update_layout(
                title=f"Trip Status — {drv['full_name']}",
                paper_bgcolor="white",
                margin=dict(l=10, r=10, t=40, b=10),
                showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trips found for this driver yet.")

    # ── Earnings over time ─────────────────────────────────────────────────────
    if completed:
        earn_rows = []
        for t in completed:
            earn_rows.append({
                "Date"    : str(t.get("completed_at") or t.get("requested_at", ""))[:10],
                "Earnings": t.get("driver_earnings") or 0,
            })
        earn_df = pd.DataFrame(earn_rows)
        daily_earn = earn_df.groupby("Date")["Earnings"].sum().reset_index()
        daily_earn = daily_earn.sort_values("Date")

        fig = px.area(daily_earn, x="Date", y="Earnings",
                      title=f"Daily Earnings — {drv['full_name']}",
                      color_discrete_sequence=[GREEN])
        fig.update_traces(fill="tozeroy", line_width=2)
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                          margin=dict(l=10, r=10, t=40, b=10),
                          xaxis_title="", yaxis_title="₹")
        st.plotly_chart(fig, use_container_width=True)

    # ── Leaderboard ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🏆 Driver Leaderboard")

    leaderboard = []
    for i, row in enumerate(
        sorted(driver_stats, key=lambda x: x["Trips"], reverse=True)[:20], 1
    ):
        leaderboard.append({
            "Rank"    : i,
            "Driver"  : row["Driver"],
            "Trips"   : row["Trips"],
            "Earnings": f"₹{row['Earnings']:,.0f}",
        })
    lb_df = pd.DataFrame(leaderboard)
    st.dataframe(lb_df, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 10 — PROMOTIONS & OFFERS
# ══════════════════════════════════════════════════════════════════════════════
def page_promotions():
    page_title("🎁 Promotions & Offers")

    df = promotions_df.copy()
    active_p = len(df[df["Status"]=="Active"])
    total_used = df["Used"].sum()
    upcoming = len(df[df["Status"]=="Upcoming"])
    expired = len(df[df["Status"]=="Expired"])

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(metric("Active Promos", str(active_p), "", "green"), unsafe_allow_html=True)
    with c2: st.markdown(metric("Total Redemptions", str(total_used), "", "blue"), unsafe_allow_html=True)
    with c3: st.markdown(metric("Upcoming", str(upcoming), "", "purple"), unsafe_allow_html=True)
    with c4: st.markdown(metric("Expired", str(expired), "", "red"), unsafe_allow_html=True)

    st.markdown("---")

    # Promo cards grid
    status_colors = {"Active":"#34A853","Expired":"#EA4335","Upcoming":"#FF6B00"}
    status_bg = {"Active":"#E6F4EA","Expired":"#FCE8E6","Upcoming":"#FFF0E6"}

    cols = st.columns(2)
    for i, (_, r) in enumerate(df.iterrows()):
        with cols[i % 2]:
            s_color = status_colors.get(r["Status"], "#888")
            s_bg = status_bg.get(r["Status"], "#f5f5f5")
            disc_text = f"{r['Discount Value']}%" if r["Discount Type"]=="%" else f"₹{r['Discount Value']}"
            pct_used = (r["Used"]/r["Max Uses"]*100) if r["Max Uses"] > 0 else 0
            bar_color = GREEN if pct_used < 70 else (AMBER if pct_used < 90 else RED)
            st.markdown(f"""
            <div style='background:white;border-radius:12px;padding:18px 20px;margin-bottom:14px;
                        border:1px solid #eee;box-shadow:0 2px 8px rgba(0,0,0,0.04);'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                        <span style='background:#111111;color:#fff;padding:4px 12px;border-radius:6px;
                                     font-family:monospace;font-size:14px;font-weight:700;letter-spacing:1px;'>{r['Code']}</span>
                        <span class="badge" style="background:{s_bg};color:{s_color};margin-left:8px;">{r['Status']}</span>
                    </div>
                    <div style='font-size:1.4rem;font-weight:800;color:#FF6B00;'>{disc_text}</div>
                </div>
                <div style='font-size:13px;color:#555;margin:10px 0 6px;'>{r['Description']}</div>
                <div style='font-size:11px;color:#888;'>Valid: {r['Valid From']} → {r['Valid To']}</div>
                <div style='margin-top:10px;'>
                    <div style='font-size:11px;color:#888;margin-bottom:4px;'>Usage: {r['Used']}/{r['Max Uses']}</div>
                    <div style='background:#eee;border-radius:4px;height:8px;overflow:hidden;'>
                        <div style='background:{bar_color};height:100%;width:{pct_used:.0f}%;border-radius:4px;'></div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    # Redemption chart
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(go.Bar(
            x=df["Code"], y=df["Used"],
            marker_color=[status_colors.get(s, BLUE) for s in df["Status"]],
            text=df["Used"], textposition="auto"
        ))
        fig.update_layout(title="Redemptions by Promo Code", plot_bgcolor="white",
                          paper_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = go.Figure(go.Bar(
            x=df["Code"], y=df["Max Uses"]-df["Used"],
            marker_color=[PURPLE]*len(df),
            text=(df["Max Uses"]-df["Used"]).apply(lambda x: str(max(x,0))), textposition="auto"
        ))
        fig.update_layout(title="Remaining Uses by Code", plot_bgcolor="white",
                          paper_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("All Promotions")
    st.dataframe(df[["Code","Description","Discount Type","Discount Value","Used","Max Uses","Status","Valid From","Valid To"]].reset_index(drop=True),
                 use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 11 — MANAGE DRIVER (Activate / Documents)
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 12 — SEND NOTIFICATION
# ══════════════════════════════════════════════════════════════════════════════
def page_send_notification():
    page_title("📢 Send Notification", "Broadcast messages to all riders, drivers, or both — filter by city or location")

    # Initialize sent notifications history
    if "sent_notifications" not in st.session_state:
        st.session_state.sent_notifications = [
            {"To": "All Drivers", "Title": "🛠️ Scheduled Maintenance", "Message": "App will be under maintenance tomorrow 2AM-4AM. Please plan accordingly.",
             "Target": "All Cities", "Location": "All Locations",
             "Sent At": (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"), "Sent By": "Admin"},
            {"To": "All Riders", "Title": "🎉 Weekend Offer!", "Message": "Get 20% off on all rides this weekend! Use code WEEKEND30.",
             "Target": "Kolkata", "Location": "All Locations",
             "Sent At": (datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M"), "Sent By": "Admin"},
            {"To": "All (Riders + Drivers)", "Title": "🚗 New Feature Alert", "Message": "Live GPS tracking is now available for all trips. Stay safe!",
             "Target": "All Cities", "Location": "All Locations",
             "Sent At": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), "Sent By": "Admin"},
            {"To": "All Drivers", "Title": "⚠️ Heavy Rain Warning", "Message": "Heavy rain expected in Kolkata area. Drive carefully and avoid waterlogged routes.",
             "Target": "Kolkata", "Location": "Howrah Station",
             "Sent At": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"), "Sent By": "Ops Manager"},
        ]

    sent = st.session_state.sent_notifications

    # City & location options
    cities = ["All Cities", "Kolkata", "Howrah", "Salt Lake", "New Town", "Durgapur", "Asansol", "Siliguri", "Bardhaman"]
    locations = ["All Locations", "Park Street", "Salt Lake", "Howrah Station", "New Town", "Durgapur",
                 "Esplanade", "New Town", "Dum Dum", "Asansol", "Barasat",
                 "Sealdah", "Kalyani", "Memari", "Galsi", "Kalna"]

    # Metrics
    total_sent = len(sent)
    to_drivers = sum(1 for n in sent if "Driver" in n["To"])
    to_riders = sum(1 for n in sent if "Rider" in n["To"])
    city_targeted = sum(1 for n in sent if n.get("Target", "All Cities") != "All Cities")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric("Total Sent", str(total_sent)), unsafe_allow_html=True)
    with c2: st.markdown(metric("To Drivers", str(to_drivers), "", "green"), unsafe_allow_html=True)
    with c3: st.markdown(metric("To Riders", str(to_riders), "", "purple"), unsafe_allow_html=True)
    with c4: st.markdown(metric("City Targeted", str(city_targeted), "", "amber"), unsafe_allow_html=True)

    st.markdown("---")

    # Compose notification form
    st.subheader("✍️ Compose Notification")
    with st.form("send_notif_form", clear_on_submit=True):
        audience = st.selectbox("Send To", ["All (Riders + Drivers)", "All Drivers", "All Riders"])

        row_target = st.columns(2)
        target_city = row_target[0].selectbox("🏙️ Target City", cities,
                                               help="Send to users in a specific city, or 'All Cities' for everyone")
        target_location = row_target[1].selectbox("📍 Target Location / Zone", locations,
                                                   help="Narrow down to a specific zone within the city")

        title = st.text_input("Notification Title", placeholder="e.g. 🎉 Special Weekend Offer!")
        message = st.text_area("Message", placeholder="Type your notification message here...", height=120)
        priority = st.selectbox("Priority", ["Normal", "Urgent", "Low"])

        # Preview targeting
        target_preview = ""
        if target_city != "All Cities" and target_location != "All Locations":
            target_preview = f"📍 **{target_location}**, {target_city}"
        elif target_city != "All Cities":
            target_preview = f"🏙️ **{target_city}** (all locations)"
        elif target_location != "All Locations":
            target_preview = f"📍 **{target_location}** (all cities)"
        else:
            target_preview = "🌐 **All Cities & Locations**"

        st.markdown(f"**Target:** {audience} → {target_preview}")

        col_a, col_b = st.columns([1, 3])
        with col_a:
            submitted = st.form_submit_button("🚀 Send Notification", type="primary", use_container_width=True)

        if submitted:
            if not title.strip() or not message.strip():
                st.error("❌ Please fill in both Title and Message.")
            else:
                new_notif = {
                    "To": audience, "Title": title, "Message": message,
                    "Target": target_city, "Location": target_location,
                    "Sent At": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Sent By": st.session_state.user["name"],
                }
                # Send real notification via API
                role_map = {
                    "All Drivers": "driver",
                    "All Riders": "rider",
                    "All (Riders + Drivers)": None
                }
                api_result = api_post("/admin/notifications/broadcast", {
                    "title": title,
                    "message": message,
                    "role": role_map.get(audience)
                })
                
                st.session_state.sent_notifications.insert(0, new_notif)
                if api_result:
                    st.success(f"✅ Notification sent to **{audience}**! {api_result.get('message', '')}")
                else:
                    st.warning("⚠️ Notification saved locally but API connection failed.")
            

                # Show recipient count (simulated)
                if audience == "All Drivers":
                    count = len(drivers_df)
                elif audience == "All Riders":
                    count = len(customers_df)
                else:
                    count = len(drivers_df) + len(customers_df)
                # Reduce count if city/location targeted
                if target_city != "All Cities":
                    count = max(1, count // len(cities))
                if target_location != "All Locations":
                    count = max(1, count // 3)
                st.info(f"📨 Delivered to **{count} recipients** in {target_preview} (Demo mode)")

    st.markdown("---")

    # Sent notification history
    st.subheader("📬 Sent Notifications")

    # Filter history
    hist_f1, hist_f2 = st.columns(2)
    hist_aud = hist_f1.selectbox("Filter by Audience", ["All", "All Drivers", "All Riders", "All (Riders + Drivers)"], key="sn_aud")
    hist_city = hist_f2.selectbox("Filter by City", ["All"] + cities[1:], key="sn_city")

    display_sent = sent.copy()
    if hist_aud != "All":
        display_sent = [n for n in display_sent if n["To"] == hist_aud]
    if hist_city != "All":
        display_sent = [n for n in display_sent if n.get("Target", "All Cities") == hist_city]

    if not display_sent:
        st.info("No notifications match the selected filters.")
    else:
        audience_colors = {
            "All Drivers": ("#34A853", "#E6F4EA"),
            "All Riders": ("#7F77DD", "#F0EEFF"),
            "All (Riders + Drivers)": ("#FF6B00", "#FFF0E6"),
        }
        for n in display_sent:
            a_color, a_bg = audience_colors.get(n["To"], ("#888", "#f5f5f5"))
            target_txt = n.get("Target", "All Cities")
            loc_txt = n.get("Location", "All Locations")
            geo_badge = ""
            if target_txt != "All Cities":
                geo_badge += f"<span style='background:#FEF3CD;color:#856404;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:600;margin-left:6px;'>🏙️ {target_txt}</span>"
            if loc_txt != "All Locations":
                geo_badge += f"<span style='background:#FFF0E6;color:#FF6B00;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:600;margin-left:6px;'>📍 {loc_txt}</span>"

            st.markdown(f"""
            <div style='background:white;border-radius:12px;padding:16px 20px;margin-bottom:10px;
                        border:1px solid #eee;box-shadow:0 1px 4px rgba(0,0,0,0.03);'>
                <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;'>
                    <div>
                        <div style='font-size:15px;font-weight:700;color:#111111;'>{n['Title']}</div>
                        <div style='font-size:13px;color:#555;margin-top:4px;'>{n['Message']}</div>
                        <div style='margin-top:6px;'>{geo_badge}</div>
                    </div>
                    <div style='text-align:right;'>
                        <span class="badge" style="background:{a_bg};color:{a_color};">{n['To']}</span>
                        <div style='font-size:11px;color:#888;margin-top:6px;'>{n['Sent At']}</div>
                        <div style='font-size:10px;color:#aaa;'>by {n['Sent By']}</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.caption(f"Showing {len(display_sent)} of {len(sent)} notifications")

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 13 — DRIVER ONLINE LOG
# ══════════════════════════════════════════════════════════════════════════════
def page_driver_online_log():
    page_title("⏱️ Driver Online Log", "Real-time online/offline status of all drivers")

    if st.button("🔄 Refresh"):
        st.rerun()

    # Fetch real drivers from backend
    data = api_get("/admin/drivers")
    if not data:
        st.error("❌ Could not load driver data.")
        return

    drivers = data.get("drivers", [])
    if not drivers:
        st.info("No drivers registered yet.")
        return

    # ── KPIs ───────────────────────────────────────────────────────────────────
    total    = len(drivers)
    online   = sum(1 for d in drivers if d["is_online"])
    on_trip  = sum(1 for d in drivers if d.get("is_on_trip"))
    offline  = total - online
    approved = sum(1 for d in drivers if d["is_approved"])

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.markdown(metric("Total Drivers", str(total)),                        unsafe_allow_html=True)
    with c2: st.markdown(metric("Online Now",    str(online),   "", "green"),        unsafe_allow_html=True)
    with c3: st.markdown(metric("On Trip",       str(on_trip),  "", "blue"),         unsafe_allow_html=True)
    with c4: st.markdown(metric("Offline",       str(offline),  "", "red"),          unsafe_allow_html=True)
    with c5: st.markdown(metric("Approved",      str(approved), "", "purple"),       unsafe_allow_html=True)

    st.markdown("---")

    # ── Filter ─────────────────────────────────────────────────────────────────
    f1, f2 = st.columns(2)
    status_filter = f1.selectbox(
        "Filter by Status",
        ["All", "Online", "On Trip", "Offline"],
        key="dol_status")
    search = f2.text_input(
        "🔍 Search by name or phone", key="dol_search")

    filtered = drivers
    if status_filter == "Online":
        filtered = [d for d in filtered if d["is_online"] and not d.get("is_on_trip")]
    elif status_filter == "On Trip":
        filtered = [d for d in filtered if d.get("is_on_trip")]
    elif status_filter == "Offline":
        filtered = [d for d in filtered if not d["is_online"]]
    if search:
        filtered = [d for d in filtered if
                    search.lower() in d["full_name"].lower() or
                    search in str(d.get("phone", ""))]

    st.caption(f"Showing {len(filtered)} of {total} drivers")
    st.markdown("---")

    # ── Driver status cards ────────────────────────────────────────────────────
    st.subheader("🟢 Current Driver Status")

    for d in filtered:
        name     = d["full_name"]
        phone    = d.get("phone", "")
        city     = d.get("city", "")
        v        = d.get("vehicle") or {}
        v_str    = f"{v.get('brand','')} {v.get('model','')}".strip() or "—"
        rating   = d.get("avg_rating", 0)
        trips    = d.get("total_trips", 0)
        earnings = d.get("total_earnings", 0)
        lat      = d.get("current_lat")
        lng      = d.get("current_lng")

        if d.get("is_on_trip"):
            status_str  = "🔵 On Trip"
            status_bg   = "#EEF2FF"
            status_color= "#3730A3"
            border_color= "#6366F1"
        elif d["is_online"]:
            status_str  = "🟢 Online"
            status_bg   = "#F0FDF4"
            status_color= "#166534"
            border_color= "#22C55E"
        else:
            status_str  = "⚫ Offline"
            status_bg   = "#F9FAFB"
            status_color= "#374151"
            border_color= "#D1D5DB"

        approved_badge = (
            "<span style='background:#E6F4EA;color:#137333;padding:2px 8px;"
            "border-radius:12px;font-size:10px;font-weight:600;'>✅ Approved</span>"
            if d["is_approved"] else
            "<span style='background:#FEF3CD;color:#856404;padding:2px 8px;"
            "border-radius:12px;font-size:10px;font-weight:600;'>⏳ Pending</span>"
        )

        location_str = (f"📍 {round(lat,4)}, {round(lng,4)}"
                        if lat and lng else "📍 No GPS data")

        st.markdown(f"""
        <div style='background:{status_bg};border-left:4px solid {border_color};
                    border-radius:0 10px 10px 0;padding:14px 18px;
                    margin-bottom:8px;'>
            <div style='display:flex;justify-content:space-between;
                        align-items:center;flex-wrap:wrap;'>
                <div>
                    <div style='font-size:14px;font-weight:700;color:#111111;'>
                        {name}
                        <span style='margin-left:8px;'>{approved_badge}</span>
                    </div>
                    <div style='font-size:12px;color:#555;margin-top:4px;'>
                        📞 {phone} &nbsp;·&nbsp; 🚗 {v_str} &nbsp;·&nbsp;
                        📍 {city}
                    </div>
                    <div style='font-size:11px;color:#888;margin-top:4px;'>
                        {location_str}
                    </div>
                </div>
                <div style='text-align:right;'>
                    <div style='font-size:14px;font-weight:700;
                                color:{status_color};'>{status_str}</div>
                    <div style='font-size:12px;color:#555;margin-top:4px;'>
                        ⭐ {rating} &nbsp;·&nbsp; 🛣️ {trips} trips
                    </div>
                    <div style='font-size:12px;color:#34A853;font-weight:600;'>
                        ₹{earnings:,.0f} earned
                    </div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── Charts ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        status_data = {
            "Status": ["Online", "On Trip", "Offline"],
            "Count" : [
                sum(1 for d in drivers if d["is_online"] and not d.get("is_on_trip")),
                on_trip,
                offline
            ]
        }
        fig = go.Figure(go.Pie(
            labels=status_data["Status"],
            values=status_data["Count"],
            hole=0.5,
            marker_colors=[GREEN, BLUE, "#D1D5DB"],
            textinfo="label+value"
        ))
        fig.update_layout(title="Driver Status Right Now",
                          paper_bgcolor="white",
                          margin=dict(l=10, r=10, t=40, b=10),
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Drivers by city with online status
        city_data = {}
        for d in drivers:
            c = d.get("city", "Unknown")
            if c not in city_data:
                city_data[c] = {"Online": 0, "Offline": 0}
            if d["is_online"]:
                city_data[c]["Online"] += 1
            else:
                city_data[c]["Offline"] += 1

        city_df = pd.DataFrame([
            {"City": c, "Online": v["Online"], "Offline": v["Offline"]}
            for c, v in city_data.items()
        ]).sort_values("Online", ascending=False).head(8)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Online",  x=city_df["City"], y=city_df["Online"],
            marker_color=GREEN))
        fig.add_trace(go.Bar(
            name="Offline", x=city_df["City"], y=city_df["Offline"],
            marker_color="#D1D5DB"))
        fig.update_layout(
            title="Online vs Offline by City",
            barmode="stack",
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)

    # ── Export ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    export_rows = [{
        "Name"    : d["full_name"],
        "Phone"   : d.get("phone", ""),
        "City"    : d.get("city", ""),
        "Status"  : ("On Trip" if d.get("is_on_trip") else
                     "Online"  if d["is_online"] else "Offline"),
        "Approved": "Yes" if d["is_approved"] else "No",
        "Rating"  : d.get("avg_rating", 0),
        "Trips"   : d.get("total_trips", 0),
        "Earnings": d.get("total_earnings", 0),
        "Lat"     : d.get("current_lat", ""),
        "Lng"     : d.get("current_lng", ""),
    } for d in drivers]

    csv = pd.DataFrame(export_rows).to_csv(index=False)
    st.download_button(
        "📥 Download Driver Status (CSV)",
        csv, "driver_online_log.csv", "text/csv", type="primary")

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 14 — ACTIVATE PROMO
# ══════════════════════════════════════════════════════════════════════════════
def page_activate_promo():
    page_title("🏷️ Activate Promo Code")

    # ── Session state init ────────────────────────────────────────────────────
    if "active_promos" not in st.session_state:
        st.session_state.active_promos = [
            {"code": "FIRST50",  "discount": "50%",  "type": "Percentage", "auto_apply": True,
             "min_fare": 0,  "vehicle": "All",  "status": "Active",
             "created": (datetime.now() - timedelta(days=5)).strftime("%d %b %Y %H:%M")},
            {"code": "RIDE20",   "discount": "₹20",  "type": "Flat",       "auto_apply": False,
             "min_fare": 100, "vehicle": "All",  "status": "Active",
             "created": (datetime.now() - timedelta(days=12)).strftime("%d %b %Y %H:%M")},
        ]

    promos = st.session_state.active_promos
    auto_count = sum(1 for p in promos if p["auto_apply"] and p["status"] == "Active")
    total_active = sum(1 for p in promos if p["status"] == "Active")

    # ── KPI cards ─────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(metric("Total Active Promos", str(total_active), "", "green"), unsafe_allow_html=True)
    with c2: st.markdown(metric("Auto-Apply Active", str(auto_count), "", "purple"), unsafe_allow_html=True)
    with c3: st.markdown(metric("Manual Only", str(total_active - auto_count), "", "amber"), unsafe_allow_html=True)

    st.markdown("---")

    # ── Auto-apply explainer ──────────────────────────────────────────────────
    st.markdown("""
    <div class="alert">
        ⚡ <strong>Auto-Apply</strong> — When enabled, the promo code is automatically applied
        to every new ride booked through the app. Riders don't need to enter the code manually.
    </div>""", unsafe_allow_html=True)

    # ── Create / Activate new promo ───────────────────────────────────────────
    st.subheader("➕ Create & Activate Promo Code")

    with st.form("activate_promo_form", clear_on_submit=True):
        row1 = st.columns([1, 1, 1])
        code = row1[0].text_input("Promo Code", placeholder="e.g. SUMMER25").strip().upper()
        disc_type = row1[1].selectbox("Discount Type", ["Percentage", "Flat"])
        disc_val = row1[2].number_input("Discount Value", min_value=1, max_value=100 if disc_type == "Percentage" else 5000, value=10)

        row2 = st.columns([1, 1, 1])
        min_fare = row2[0].number_input("Min Fare (₹) to qualify", min_value=0, value=0, step=10)
        vehicle_filter = row2[1].selectbox("Vehicle Type", ["All", "Car", "Bike", "Auto"])
        auto_apply = row2[2].selectbox("Auto-Apply on Booking?", ["Yes — apply automatically", "No — rider enters manually"])

        submitted = st.form_submit_button("🚀 Activate Promo Code", use_container_width=True, type="primary")

        if submitted:
            if not code:
                st.error("Please enter a promo code.")
            elif any(p["code"] == code and p["status"] == "Active" for p in promos):
                st.error(f"Promo code **{code}** is already active.")
            else:
                disc_display = f"{disc_val}%" if disc_type == "Percentage" else f"₹{disc_val}"
                new_promo = {
                    "code": code,
                    "discount": disc_display,
                    "type": disc_type,
                    "auto_apply": auto_apply.startswith("Yes"),
                    "min_fare": min_fare,
                    "vehicle": vehicle_filter,
                    "status": "Active",
                    "created": datetime.now().strftime("%d %b %Y %H:%M"),
                }
                st.session_state.active_promos.append(new_promo)
                auto_txt = "AUTO-APPLY ✅" if new_promo["auto_apply"] else "MANUAL"
                st.success(f"✅ Promo **{code}** ({disc_display} off) activated! Mode: **{auto_txt}**")
                st.rerun()

    # ── Active promo cards ────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Active Promo Codes")

    active_list = [p for p in promos if p["status"] == "Active"]
    if not active_list:
        st.info("No active promo codes. Create one above!")
    else:
        cols = st.columns(2)
        for i, p in enumerate(active_list):
            with cols[i % 2]:
                auto_badge = (
                    "<span style='background:#E6F4EA;color:#137333;padding:3px 10px;"
                    "border-radius:20px;font-size:11px;font-weight:600;'>⚡ AUTO-APPLY</span>"
                ) if p["auto_apply"] else (
                    "<span style='background:#FEF3CD;color:#856404;padding:3px 10px;"
                    "border-radius:20px;font-size:11px;font-weight:600;'>✋ MANUAL</span>"
                )
                vehicle_txt = f"🚗 {p['vehicle']}" if p["vehicle"] != "All" else "🚗 All vehicles"
                min_txt = f"Min fare: ₹{p['min_fare']}" if p["min_fare"] > 0 else "No min fare"

                st.markdown(f"""
                <div style='background:white;border-radius:12px;padding:18px 20px;margin-bottom:14px;
                            border:1px solid #eee;box-shadow:0 2px 8px rgba(0,0,0,0.04);'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <div>
                            <span style='background:#111111;color:#fff;padding:4px 12px;border-radius:6px;
                                         font-family:monospace;font-size:14px;font-weight:700;
                                         letter-spacing:1px;'>{p['code']}</span>
                            {auto_badge}
                        </div>
                        <div style='font-size:1.4rem;font-weight:800;color:#FF6B00;'>{p['discount']}</div>
                    </div>
                    <div style='display:flex;gap:16px;margin-top:12px;font-size:12px;color:#666;'>
                        <span>{vehicle_txt}</span>
                        <span>·</span>
                        <span>{min_txt}</span>
                        <span>·</span>
                        <span>{p['type']}</span>
                    </div>
                    <div style='font-size:11px;color:#aaa;margin-top:8px;'>Created: {p['created']}</div>
                </div>""", unsafe_allow_html=True)

                if st.button(f"❌ Deactivate {p['code']}", key=f"deactivate_{p['code']}_{i}", type="primary"):
                    for pp in st.session_state.active_promos:
                        if pp["code"] == p["code"] and pp["status"] == "Active":
                            pp["status"] = "Deactivated"
                    st.success(f"Promo **{p['code']}** has been deactivated.")
                    st.rerun()

    # ── Deactivated log ───────────────────────────────────────────────────────
    deactivated = [p for p in promos if p["status"] == "Deactivated"]
    if deactivated:
        st.markdown("---")
        with st.expander(f"🗂️ Deactivated Promos ({len(deactivated)})"):
            deact_df = pd.DataFrame(deactivated)
            st.dataframe(deact_df[["code","discount","type","vehicle","auto_apply","created"]].rename(
                columns={"code":"Code","discount":"Discount","type":"Type",
                         "vehicle":"Vehicle","auto_apply":"Was Auto-Apply","created":"Created"}
            ), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 15 — RIDER ONBOARDING
# ══════════════════════════════════════════════════════════════════════════════
def page_rider_onboarding():
    page_title("🧑‍💼 Rider Onboarding")

    # Fetch real riders from backend
    data = api_get("/admin/users", params={"role": "rider", "limit": 200})
    if not data:
        st.error("❌ Could not load rider data.")
        return

    real_users = data.get("users", [])
    if not real_users:
        st.info("No riders registered yet.")
        return

    # Build rows from real data
    rows = []
    for u in real_users:
        rows.append({
            "Rider ID"        : f"RDR-{u['id']}",
            "Name"            : u["full_name"],
            "Phone"           : u["phone"],
            "Email"           : u.get("email", "—"),
            "Install Date"    : str(u.get("created_at", ""))[:10],
            "Install Time"    : str(u.get("created_at", ""))[11:16],
            "Logged In"       : u.get("last_login") is not None,
            "Profile Complete" : u.get("full_name") is not None,
            "Wallet Balance"  : u.get("wallet_balance", 0),
            "is_active"       : u.get("is_active", True),
            "is_blocked"      : u.get("is_blocked", False),
            "user_id"         : u["id"],
        })
    df = pd.DataFrame(rows)

    total_installs  = len(df)
    total_logins    = int(df["Logged In"].sum())
    total_profiles  = int(df["Profile Complete"].sum())
    login_rate      = (total_logins / total_installs * 100) if total_installs > 0 else 0
    blocked_count   = int(df["is_blocked"].sum())

    # ── KPIs ───────────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.markdown(metric("Total Riders",    str(total_installs)),                        unsafe_allow_html=True)
    with c2: st.markdown(metric("Logged In",       str(total_logins),  f"{login_rate:.0f}%", "green"), unsafe_allow_html=True)
    with c3: st.markdown(metric("Profile Done",    str(total_profiles),"", "amber"),            unsafe_allow_html=True)
    with c4: st.markdown(metric("Active",          str(total_installs - blocked_count), "", "green"), unsafe_allow_html=True)
    with c5: st.markdown(metric("Blocked",         str(blocked_count), "", "red"),              unsafe_allow_html=True)

    st.markdown("---")

    # ── Charts ─────────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        # Daily registrations
        daily = df.groupby("Install Date").size().reset_index(name="Registrations")
        daily = daily.sort_values("Install Date")
        fig = px.bar(daily, x="Install Date", y="Registrations",
                     title="Daily Rider Registrations",
                     color_discrete_sequence=[BLUE])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                          margin=dict(l=10, r=10, t=40, b=10),
                          xaxis_title="", yaxis_title="Riders")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Onboarding funnel
        funnel_vals   = [total_installs, total_logins, total_profiles]
        funnel_labels = ["Registered", "Logged In", "Profile Complete"]
        fig = go.Figure(go.Funnel(
            y=funnel_labels, x=funnel_vals,
            marker=dict(color=[BLUE, GREEN, AMBER]),
            textinfo="value+percent initial"
        ))
        fig.update_layout(title="Onboarding Funnel",
                          paper_bgcolor="white",
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # ── Rider Table ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Rider Records")

    phone_search = st.text_input(
        "🔍 Search by Phone Number",
        placeholder="Enter full or partial phone number",
        key="ro_phone")

    f1, f2 = st.columns(2)
    status_f = f1.selectbox(
        "Status", ["All", "Active", "Blocked"], key="ro_status")
    login_f  = f2.selectbox(
        "Login Status", ["All", "Logged In", "Never Logged In"], key="ro_login")

    filtered = df.copy()
    if phone_search:
        filtered = filtered[
            filtered["Phone"].astype(str).str.contains(
                phone_search.strip(), na=False)]
    if status_f == "Active":
        filtered = filtered[filtered["is_blocked"] == False]
    elif status_f == "Blocked":
        filtered = filtered[filtered["is_blocked"] == True]
    if login_f == "Logged In":
        filtered = filtered[filtered["Logged In"] == True]
    elif login_f == "Never Logged In":
        filtered = filtered[filtered["Logged In"] == False]

    # Pagination
    records_per_page = st.selectbox(
        "Records per page", [10, 25, 50, 100], key="ro_rpp")

    if "ro_page_num" not in st.session_state:
        st.session_state.ro_page_num = 1

    total_records = len(filtered)
    total_pages   = max(1, (total_records - 1) // records_per_page + 1)

    if st.session_state.ro_page_num > total_pages:
        st.session_state.ro_page_num = 1

    start_idx  = (st.session_state.ro_page_num - 1) * records_per_page
    end_idx    = start_idx + records_per_page
    page_data  = filtered.iloc[start_idx:end_idx]

    st.dataframe(
        page_data[["Rider ID", "Name", "Phone", "Email",
                   "Install Date", "Logged In",
                   "Profile Complete", "Wallet Balance"]
                 ].reset_index(drop=True),
        use_container_width=True, height=380, hide_index=True)

    # Pagination controls
    col_prev, col_info, col_next, col_csv = st.columns([1, 2, 1, 1])
    with col_prev:
        if st.button("◀ Previous", key="ro_prev", use_container_width=True):
            if st.session_state.ro_page_num > 1:
                st.session_state.ro_page_num -= 1
                st.rerun()
    with col_info:
        st.markdown(
            f"<div style='text-align:center;padding:8px;'>"
            f"<b>Page {st.session_state.ro_page_num} of {total_pages}</b><br>"
            f"<small>{start_idx+1}–{min(end_idx, total_records)} "
            f"of {total_records}</small></div>",
            unsafe_allow_html=True)
    with col_next:
        if st.button("Next ▶", key="ro_next", use_container_width=True):
            if st.session_state.ro_page_num < total_pages:
                st.session_state.ro_page_num += 1
                st.rerun()
    with col_csv:
        csv = filtered.drop(columns=["is_active","is_blocked","user_id"],
                            errors="ignore").to_csv(index=False)
        st.download_button("📥 Download", csv, "riders.csv",
                           "text/csv", use_container_width=True)

    # ── Block / Unblock Rider ──────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔒 Block / Unblock Rider")

    selected_rider = st.selectbox(
        "Select Rider", df["Name"].tolist(), key="block_rider_select")
    rider_row = df[df["Name"] == selected_rider].iloc[0]
    rider_id  = int(rider_row["user_id"])
    is_blocked = bool(rider_row["is_blocked"])

    st.markdown(
        f"**Current status:** "
        f"{'🔴 Blocked' if is_blocked else '🟢 Active'}",
        unsafe_allow_html=False)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔴 Block Rider", key="block_rider_btn",
                     use_container_width=True):
            result = api_patch(f"/admin/users/{rider_id}/block")
            if result:
                st.success(f"✅ {selected_rider} blocked!")
                st.rerun()
            else:
                st.error("Failed to block rider.")
    with col2:
        if st.button("🟢 Unblock Rider", key="unblock_rider_btn",
                     use_container_width=True):
            result = api_patch(f"/admin/users/{rider_id}/block")
            if result:
                st.success(f"✅ {selected_rider} unblocked!")
                st.rerun()
            else:
                st.error("Failed to unblock rider.")

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 17 — LIVE SEARCH FEED
# ══════════════════════════════════════════════════════════════════════════════
def page_live_search_feed():
    page_title("🔴 Live Search Feed")

    # Generate fresh live search data every time (not cached — simulates real-time)
    zones = ["Kolkata", "Park Street","Salt Lake","Howrah Station","New Town",
             "Esplanade","New Town","Dum Dum","Asansol","Barasat",
             "Sealdah","Kalyani","Memari","Galsi","Kalna"]
    riders = ["Arjun Sharma","Priya Das","Sneha Gupta","Rohit Mondal","Anjali Sen",
              "Vikram Sinha","Pooja Nath","Karan Dey","Megha Roy","Sourav Pal",
              "Nisha Banerjee","Aman Ghosh","Ritika Saha","Deepak Mukherjee","Swati Basu"]
    vtypes = ["Car","Car","Car","Bike","Bike","Auto"]
    statuses_list = ["Matched","Matched","Matched","Matched","Searching","Searching","No Driver Found","Cancelled by Rider"]

    now = datetime.now()
    searches = []
    for i in range(50):
        t = now - timedelta(minutes=random.randint(0, 60), seconds=random.randint(0, 59))
        pickup = random.choice(zones)
        drop = random.choice([z for z in zones if z != pickup])
        vtype = random.choice(vtypes)
        base_fare = round(random.uniform(50, 400), 0)
        if vtype == "Bike": base_fare = round(base_fare * 0.5, 0)
        elif vtype == "Auto": base_fare = round(base_fare * 0.7, 0)
        search_status = random.choice(statuses_list)
        driver_pool = [
            ("Ravi Kumar", "9812345678"), ("Suresh Patra", "9823456789"), 
            ("Anup Das", "9834567890"), ("Tamal Ghosh", "9845678901"),
            ("Mohan Roy", "9856789012"), ("Bikash Sen", "9867890123"), 
            ("Pradip Mondal", "9878901234"), ("Amit Pal", "9889012345")
        ]
        pinged_sample = random.sample(driver_pool, 4)
        if search_status == "Matched":
            driver_name = pinged_sample[0][0]
        else:
            driver_name = "—"
            
        pinged_html = "".join([f"<li>{d[0]} <span style='color:#aaa;font-size:10px;'>({d[1]})</span></li>" for d in pinged_sample])

        searches.append({
            "Search ID": f"SRC-{9000+i}",
            "Time": t.strftime("%H:%M:%S"),
            "Rider": random.choice(riders),
            "Phone": f"97{random.randint(10000000,99999999)}",
            "Pickup": pickup,
            "Drop": drop,
            "Vehicle Type": vtype,
            "Fare Estimate (₹)": base_fare,
            "Status": search_status,
            "Driver Assigned": driver_name,
            "Drivers Pinged": 4,
            "Pinged HTML": pinged_html,
            "_sort_time": t,
        })

    searches.sort(key=lambda x: x["_sort_time"], reverse=True)
    df = pd.DataFrame(searches)
    df = df.drop(columns=["_sort_time"])

    matched = len(df[df["Status"]=="Matched"])
    searching = len(df[df["Status"]=="Searching"])
    no_driver = len(df[df["Status"]=="No Driver Found"])
    cancelled = len(df[df["Status"]=="Cancelled by Rider"])
    match_rate = (matched / len(df) * 100) if len(df) > 0 else 0

    # KPI cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.markdown(metric("Total Searches", str(len(df))), unsafe_allow_html=True)
    with c2: st.markdown(metric("Matched", str(matched), f"{match_rate:.0f}%", "green"), unsafe_allow_html=True)
    with c3: st.markdown(metric("Searching", str(searching), "", "amber"), unsafe_allow_html=True)
    with c4: st.markdown(metric("No Driver", str(no_driver), "", "red"), unsafe_allow_html=True)
    with c5: st.markdown(metric("Cancelled", str(cancelled), "", "red"), unsafe_allow_html=True)

    st.markdown("---")

    # Auto-refresh toggle
    col_r1, col_r2 = st.columns([3, 1])
    with col_r1:
        st.markdown("""
        <div class="alert">
            🔴 <strong>Live Feed</strong> — Showing ride searches from the last 60 minutes.
            Data refreshes automatically every 10 seconds when auto-refresh is enabled.
        </div>""", unsafe_allow_html=True)
    with col_r2:
        auto_refresh = st.checkbox("⟳ Auto-Refresh (10s)", value=False, key="lsf_auto")

    if auto_refresh:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=10000, limit=None, key="lsf_autorefresh")

    # Live feed cards
    st.subheader("📡 Live Feed")

    status_icon = {"Matched": "✅", "Searching": "🔍", "No Driver Found": "❌", "Cancelled by Rider": "🚫"}
    status_bg = {"Matched": "#E6F4EA", "Searching": "#FEF3CD", "No Driver Found": "#FCE8E6", "Cancelled by Rider": "#FCE8E6"}
    status_color = {"Matched": "#137333", "Searching": "#856404", "No Driver Found": "#9A0000", "Cancelled by Rider": "#9A0000"}
    vtype_icon = {"Car": "🚗", "Bike": "🏍️", "Auto": "🛺"}

    # Show latest 10 as cards
    for _, r in df.head(10).iterrows():
        s = r["Status"]
        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:14px 18px;margin-bottom:10px;
                    border-left:4px solid {status_color[s]};box-shadow:0 1px 6px rgba(0,0,0,0.04);'>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <div style='display:flex;align-items:center;gap:12px;'>
                    <span style='font-size:1.3rem;'>{status_icon[s]}</span>
                    <div>
                        <div style='font-weight:700;font-size:14px;color:#111111;'>
                            {r['Rider']} <span style='color:#aaa;font-weight:400;font-size:12px;'>({r['Phone']})</span>
                        </div>
                        <div style='font-size:12px;color:#555;margin-top:2px;'>
                            📍 {r['Pickup']} → {r['Drop']}
                        </div>
                    </div>
                </div>
                <div style='text-align:right;'>
                    <span style='background:{status_bg[s]};color:{status_color[s]};padding:3px 10px;
                                 border-radius:20px;font-size:11px;font-weight:600;'>{s}</span>
                    <div style='font-size:11px;color:#aaa;margin-top:4px;'>{r['Time']}</div>
                </div>
            </div>
            <div style='display:flex;gap:16px;margin-top:10px;font-size:12px;color:#666;'>
                <span>{vtype_icon.get(r['Vehicle Type'],'🚗')} {r['Vehicle Type']}</span>
                <span>·</span>
                <span>₹{r['Fare Estimate (₹)']:.0f} est.</span>
                <span>·</span>
                <span>Driver: {r['Driver Assigned']}</span>
            </div>
            <details style='margin-top: 10px; font-size: 11px; color: #555; cursor: pointer;'>
                <summary style='font-weight:600;'>📡 Pinged {r['Drivers Pinged']} Drivers (Click to view details)</summary>
                <ul style='margin-top: 5px; margin-bottom: 0; padding-left: 20px; line-height: 1.6;'>
                    {r['Pinged HTML']}
                </ul>
            </details>
        </div>""", unsafe_allow_html=True)

    # Full table
    st.markdown("---")
    st.subheader("All Searches")

    f1, f2, f3 = st.columns(3)
    s_f = f1.selectbox("Status", ["All","Matched","Searching","No Driver Found","Cancelled by Rider"], key="lsf_status")
    v_f = f2.selectbox("Vehicle Type", ["All","Car","Bike","Auto"], key="lsf_vtype")
    phone_search = f3.text_input("🔍 Search Phone", placeholder="Enter phone number", key="lsf_phone")

    filtered = df.copy()
    if s_f != "All": filtered = filtered[filtered["Status"] == s_f]
    if v_f != "All": filtered = filtered[filtered["Vehicle Type"] == v_f]
    if phone_search:
        filtered = filtered[filtered["Phone"].astype(str).str.contains(phone_search.strip(), na=False)]

    display_df = filtered.drop(columns=["Pinged HTML"], errors="ignore")
    st.dataframe(display_df.reset_index(drop=True), use_container_width=True, height=400, hide_index=True)
    st.caption(f"Showing {len(filtered)} of {len(df)} searches")

    csv = display_df.to_csv(index=False)
    st.download_button("Download Search Log (CSV)", csv, "live_search_feed.csv", "text/csv", type="primary")

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE — DRIVER PAYMENTS
# ══════════════════════════════════════════════════════════════════════════════
def page_driver_payments():
    page_title("💸 Driver Payments & Withdrawals")

    if st.button("🔄 Refresh"):
        st.rerun()

    # Fetch real withdrawal data
    data = api_get("/payments/admin/all")
    if not data:
        st.error("❌ Could not load payment data.")
        return

    withdrawals = data.get("withdrawals", [])
    total_paid  = data.get("total_paid",  0)
    total_count = data.get("total_count", 0)

    # Also fetch drivers for wallet balances
    drv_data = api_get("/admin/drivers") or {}
    drivers  = drv_data.get("drivers", [])
    total_wallet = sum(d.get("total_earnings", 0) for d in drivers)

    # ── KPIs ──────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric("Total Withdrawn",  f"₹{total_paid:,.2f}",  "", "green"),  unsafe_allow_html=True)
    with c2: st.markdown(metric("Total Requests",   str(total_count),       "", "blue"),   unsafe_allow_html=True)
    with c3: st.markdown(metric("Total Earnings",   f"₹{total_wallet:,.0f}","", "purple"), unsafe_allow_html=True)
    with c4: st.markdown(metric("Active Drivers",   str(len(drivers)),      "", "amber"),  unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2 = st.tabs(["💳 Withdrawal History", "👛 Driver Wallet Balances"])

    # ── TAB 1: Withdrawal History ──────────────────────────────────
    with tab1:
        if not withdrawals:
            st.info("No withdrawal requests yet.")
        else:
            # Search
            search = st.text_input("🔍 Search by driver name or phone",
                                   key="pay_search")
            method_f = st.selectbox("Filter by Method",
                                    ["All", "upi", "bank"], key="pay_method")

            filtered = withdrawals
            if search:
                filtered = [w for w in filtered if
                    search.lower() in w["driver_name"].lower() or
                    search in str(w["driver_phone"])]
            if method_f != "All":
                filtered = [w for w in filtered if w["method"] == method_f]

            st.caption(f"Showing {len(filtered)} of {total_count} withdrawals")

            for w in filtered:
                method_icon = "📱" if w["method"] == "upi" else "🏦"
                method_detail = (
                    f"UPI: {w['upi_id']}" if w["method"] == "upi"
                    else f"{w['bank_name']} · {w['account_number']} · {w['ifsc_code']}"
                )
                st.markdown(f"""
                <div style='background:white;border-radius:10px;
                            padding:14px 18px;margin-bottom:8px;
                            border:1px solid #eee;
                            box-shadow:0 1px 4px rgba(0,0,0,0.04);'>
                    <div style='display:flex;justify-content:space-between;
                                align-items:center;flex-wrap:wrap;'>
                        <div>
                            <div style='font-size:14px;font-weight:700;
                                        color:#111111;'>
                                {w['driver_name']}
                                <span style='font-size:12px;color:#888;
                                             margin-left:6px;'>
                                    {w['driver_phone']}
                                </span>
                            </div>
                            <div style='font-size:12px;color:#555;margin-top:4px;'>
                                {method_icon} {method_detail}
                            </div>
                            <div style='font-size:11px;color:#888;margin-top:2px;'>
                                {w['created_at']}
                            </div>
                        </div>
                        <div style='text-align:right;'>
                            <div style='font-size:1.2rem;font-weight:800;
                                        color:#34A853;'>
                                ₹{w['amount']:,.2f}
                            </div>
                            <span style='background:#E6F4EA;color:#137333;
                                         padding:2px 8px;border-radius:12px;
                                         font-size:11px;font-weight:600;'>
                                ✅ {w['status'].upper()}
                            </span>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

            # Export
            st.markdown("---")
            import io as _io
            export_rows = [{
                "Driver"        : w["driver_name"],
                "Phone"         : w["driver_phone"],
                "Amount (₹)"    : w["amount"],
                "Method"        : w["method"].upper(),
                "UPI/Bank"      : w["upi_id"] or w["bank_name"] or "",
                "Account"       : w["account_number"] or "",
                "IFSC"          : w["ifsc_code"] or "",
                "Status"        : w["status"],
                "Date"          : w["created_at"],
            } for w in withdrawals]

            buf = _io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                pd.DataFrame(export_rows).to_excel(
                    writer, index=False, sheet_name="Withdrawals")
            st.download_button(
                "📥 Download Withdrawal Report (Excel)",
                data=buf.getvalue(),
                file_name="kloqride_withdrawals.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary")

    # ── TAB 2: Driver Wallet Balances ──────────────────────────────
    with tab2:
        if not drivers:
            st.info("No drivers registered yet.")
        else:
            rows = [{
                "Name"           : d["full_name"],
                "Phone"          : d.get("phone", ""),
                "City"           : d.get("city", ""),
                "Wallet Balance" : f"₹{d.get('wallet_balance', 0) if 'wallet_balance' in d else 0:,.2f}",
                "Total Earnings" : f"₹{d.get('total_earnings', 0):,.0f}",
                "Total Trips"    : d.get("total_trips", 0),
                "Approved"       : "✅" if d["is_approved"] else "⏳",
            } for d in sorted(drivers,
                key=lambda x: x.get("total_earnings", 0), reverse=True)]

            st.dataframe(pd.DataFrame(rows),
                         use_container_width=True, hide_index=True)

            # Charts
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                top10 = sorted(drivers,
                    key=lambda x: x.get("total_earnings", 0),
                    reverse=True)[:10]
                fig = go.Figure(go.Bar(
                    x=[d["full_name"] for d in top10],
                    y=[d.get("total_earnings", 0) for d in top10],
                    marker_color=GREEN,
                    text=[f"₹{d.get('total_earnings',0):,.0f}" for d in top10],
                    textposition="auto"
                ))
                fig.update_layout(
                    title="Top 10 Earners",
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                trip_top = sorted(drivers,
                    key=lambda x: x.get("total_trips", 0),
                    reverse=True)[:10]
                fig = go.Figure(go.Bar(
                    x=[d["full_name"] for d in trip_top],
                    y=[d.get("total_trips", 0) for d in trip_top],
                    marker_color=BLUE,
                    text=[d.get("total_trips", 0) for d in trip_top],
                    textposition="auto"
                ))
                fig.update_layout(
                    title="Top 10 by Trips",
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 19 — PRICING & FEES
# ══════════════════════════════════════════════════════════════════════════════
def page_pricing_config():
    page_title("⚙️ Pricing & Fees",
               "Configure vehicle rates, surge pricing and platform commission")

    if st.button("🔄 Refresh"):
        st.rerun()

    # Fetch real pricing from backend
    data = api_get("/pricing/")
    if not data:
        st.error("❌ Could not load pricing config.")
        return

    pricing_list = data.get("pricing", [])
    surge        = data.get("surge",   {})

    # Convert to dict for easy access
    pricing_map = {p["vehicle_type"]: p for p in pricing_list}

    # ── KPIs ───────────────────────────────────────────────────────────────────
    active_mult = surge.get("active_multiplier", 1.0)
    comm_pct    = surge.get("commission_pct", 10.0)
    surge_on    = surge.get("manual_surge_active") or (
        surge.get("schedule_surge_active") and active_mult > 1.0)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric("Commission %",     f"{comm_pct}%",          "", "purple"), unsafe_allow_html=True)
    with c2: st.markdown(metric("Active Multiplier",f"{active_mult}x",       "", "amber"),  unsafe_allow_html=True)
    with c3: st.markdown(metric("Manual Surge",     "🔴 ON" if surge.get("manual_surge_active") else "⚫ OFF", "", "red" if surge.get("manual_surge_active") else "blue"), unsafe_allow_html=True)
    with c4: st.markdown(metric("Scheduled Surge",  "🟢 ON" if surge.get("schedule_surge_active") else "⚫ OFF", "", "green" if surge.get("schedule_surge_active") else "blue"), unsafe_allow_html=True)

    if active_mult > 1.0:
        st.markdown(f"""
        <div style='background:#FEF3CD;border-left:4px solid #FBBC04;
                    padding:10px 14px;border-radius:0 8px 8px 0;
                    font-size:13px;color:#5c4200;margin-bottom:12px;'>
            ⚡ <b>Surge pricing is ACTIVE</b> — Current multiplier:
            <b>{active_mult}x</b> — All fares are multiplied by this amount.
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(
        ["🚗 Vehicle Pricing", "⚡ Surge Control", "💰 Commission"])

    # ══════════════════════════════════════════════════════
    # TAB 1 — Vehicle Pricing
    # ══════════════════════════════════════════════════════
    with tab1:
        st.subheader("Set Fare Per Vehicle Type")
        st.caption("Changes apply immediately to all new trip estimates.")

        vehicle_types = ["bike", "auto", "toto", "mini", "sedan", "suv"]
        vehicle_icons = {
            "bike": "🏍️", "auto": "🛺", "toto": "🛺",
            "mini": "🚗", "sedan": "🚗", "suv": "🚙"
        }

        for vtype in vehicle_types:
            cfg = pricing_map.get(vtype, {})
            icon = vehicle_icons.get(vtype, "🚗")

            with st.expander(f"{icon} {vtype.upper()} — Base: ₹{cfg.get('base_fare', 0)} · ₹{cfg.get('per_km_fare', 0)}/km"):
                with st.form(f"pricing_form_{vtype}"):
                    c1, c2, c3, c4 = st.columns(4)
                    base   = c1.number_input("Base Fare (₹)",    value=float(cfg.get("base_fare",    0)), min_value=0.0, step=1.0, key=f"base_{vtype}")
                    per_km = c2.number_input("Per KM (₹)",       value=float(cfg.get("per_km_fare",  0)), min_value=0.0, step=0.5, key=f"km_{vtype}")
                    per_min= c3.number_input("Per Minute (₹)",   value=float(cfg.get("per_min_fare", 0)), min_value=0.0, step=0.1, key=f"min_{vtype}")
                    min_f  = c4.number_input("Min Fare (₹)",     value=float(cfg.get("min_fare",     0)), min_value=0.0, step=1.0, key=f"minf_{vtype}")

                    # Fare preview
                    example_km = 5
                    example_dur= 15
                    preview = max(
                        base + example_km * per_km + example_dur * per_min,
                        min_f)
                    st.markdown(
                        f"<div style='font-size:12px;color:#888;'>"
                        f"📊 Example — 5km, 15min trip: "
                        f"<b style='color:#34A853;'>₹{preview:.0f}</b></div>",
                        unsafe_allow_html=True)

                    if st.form_submit_button(
                            f"💾 Save {vtype.upper()} Pricing",
                            type="primary", use_container_width=True):
                        result = requests.patch(
                            f"{API_BASE}/pricing/vehicle",
                            json={
                                "vehicle_type": vtype,
                                "base_fare"   : base,
                                "per_km_fare" : per_km,
                                "per_min_fare": per_min,
                                "min_fare"    : min_f,
                            },
                            headers={"Authorization":
                                     f"Bearer {st.session_state.get('admin_token','')}"},
                            timeout=10
                        )
                        if result.status_code == 200:
                            st.success(f"✅ {vtype.upper()} pricing saved!")
                            st.rerun()
                        else:
                            st.error(f"Failed: {result.text}")

    # ══════════════════════════════════════════════════════
    # TAB 2 — Surge Control
    # ══════════════════════════════════════════════════════
    with tab2:
        st.subheader("⚡ Surge Pricing Control")

        col1, col2 = st.columns(2)

        # ── Manual Surge ──────────────────────────────────
        with col1:
            st.markdown("### 🔴 Manual Surge")
            st.markdown(
                "Turn surge ON/OFF instantly. "
                "Use during events, rain, or high demand.")

            with st.form("manual_surge_form"):
                manual_on = st.toggle(
                    "Manual Surge Active",
                    value=surge.get("manual_surge_active", False))
                manual_mult = st.slider(
                    "Manual Surge Multiplier",
                    min_value=1.0, max_value=3.0,
                    value=float(surge.get("manual_surge_multiplier", 1.5)),
                    step=0.1)
                st.markdown(
                    f"<div style='font-size:12px;color:#888;'>"
                    f"Example: ₹100 fare → "
                    f"<b>₹{100 * manual_mult:.0f}</b> with surge</div>",
                    unsafe_allow_html=True)

                if st.form_submit_button(
                        "💾 Save Manual Surge",
                        type="primary", use_container_width=True):
                    result = requests.patch(
                        f"{API_BASE}/pricing/surge",
                        json={
                            "manual_surge_active"    : manual_on,
                            "manual_surge_multiplier": manual_mult,
                        },
                        headers={"Authorization":
                                 f"Bearer {st.session_state.get('admin_token','')}"},
                        timeout=10
                    )
                    if result.status_code == 200:
                        st.success(
                            "✅ Manual surge " +
                            ("ACTIVATED 🔴" if manual_on else "deactivated ⚫"))
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.text}")

        # ── Scheduled Surge ───────────────────────────────
        with col2:
            st.markdown("### 🕐 Scheduled Surge")
            st.markdown(
                "Auto-activates surge during set hours every day.")

            with st.form("schedule_surge_form"):
                sched_on = st.toggle(
                    "Scheduled Surge Active",
                    value=surge.get("schedule_surge_active", False))
                sched_mult = st.slider(
                    "Scheduled Multiplier",
                    min_value=1.0, max_value=3.0,
                    value=float(surge.get("schedule_surge_multiplier", 1.3)),
                    step=0.1)

                hours = list(range(0, 24))
                hour_labels = [f"{h:02d}:00" for h in hours]

                start_h = st.selectbox(
                    "Start Hour",
                    hours,
                    index=surge.get("schedule_start_hour", 8),
                    format_func=lambda h: f"{h:02d}:00")
                end_h = st.selectbox(
                    "End Hour",
                    hours,
                    index=surge.get("schedule_end_hour", 10),
                    format_func=lambda h: f"{h:02d}:00")

                st.markdown(
                    f"<div style='font-size:12px;color:#888;'>"
                    f"Surge active: "
                    f"<b>{start_h:02d}:00 → {end_h:02d}:00</b> daily</div>",
                    unsafe_allow_html=True)

                if st.form_submit_button(
                        "💾 Save Schedule",
                        type="primary", use_container_width=True):
                    result = requests.patch(
                        f"{API_BASE}/pricing/surge",
                        json={
                            "schedule_surge_active"    : sched_on,
                            "schedule_surge_multiplier": sched_mult,
                            "schedule_start_hour"      : start_h,
                            "schedule_end_hour"        : end_h,
                        },
                        headers={"Authorization":
                                 f"Bearer {st.session_state.get('admin_token','')}"},
                        timeout=10
                    )
                    if result.status_code == 200:
                        st.success("✅ Schedule saved!")
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.text}")

    # ══════════════════════════════════════════════════════
    # TAB 3 — Commission
    # ══════════════════════════════════════════════════════
    with tab3:
        st.subheader("💰 Platform Commission")
        st.markdown(
            "This percentage is deducted from every completed trip fare. "
            "The rest goes to the driver's wallet.")

        with st.form("commission_form"):
            new_comm = st.slider(
                "Commission Percentage (%)",
                min_value=0.0, max_value=30.0,
                value=float(surge.get("commission_pct", 10.0)),
                step=0.5)

            st.markdown(f"""
            <div style='background:#FFF0E6;border-radius:10px;
                        padding:12px 16px;margin:10px 0;font-size:13px;'>
                <b>Example calculation for ₹200 fare:</b><br>
                Platform commission: <b style='color:#EA4335;'>
                    ₹{200 * new_comm / 100:.0f} ({new_comm}%)</b><br>
                Driver receives: <b style='color:#34A853;'>
                    ₹{200 - 200 * new_comm / 100:.0f}</b>
            </div>""", unsafe_allow_html=True)

            if st.form_submit_button(
                    "💾 Save Commission",
                    type="primary", use_container_width=True):
                result = requests.patch(
                    f"{API_BASE}/pricing/surge",
                    json={"commission_pct": new_comm},
                    headers={"Authorization":
                             f"Bearer {st.session_state.get('admin_token','')}"},
                    timeout=10
                )
                if result.status_code == 200:
                    st.success(
                        f"✅ Commission updated to {new_comm}%!")
                    st.rerun()
                else:
                    st.error(f"Failed: {result.text}")

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 20 — SEARCH HEATMAP
# ══════════════════════════════════════════════════════════════════════════════
def page_search_heatmap():
    page_title("🔥 Search Demand Heatmap",
               "Rider pickup & drop demand by location — real trip data")

    if st.button("🔄 Refresh"):
        st.rerun()

    # Fetch real trips from backend
    trip_data = api_get("/admin/trips", params={"limit": 200})
    if not trip_data:
        st.error("❌ Could not load trip data.")
        return

    trips = trip_data.get("trips", [])
    if not trips:
        st.info("No trips found yet.")
        return

    # ── KPIs ───────────────────────────────────────────────────────────────────
    total     = len(trips)
    completed = sum(1 for t in trips if t["status"] == "completed")
    cancelled = sum(1 for t in trips if t["status"] == "cancelled")
    with_coords = [t for t in trips
                   if t.get("pickup_lat") and t.get("pickup_lng")]

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric("Total Trips",      str(total)),                     unsafe_allow_html=True)
    with c2: st.markdown(metric("Completed",        str(completed), "", "green"),    unsafe_allow_html=True)
    with c3: st.markdown(metric("Cancelled",        str(cancelled), "", "red"),      unsafe_allow_html=True)
    with c4: st.markdown(metric("With GPS Data",    str(len(with_coords)), "", "blue"), unsafe_allow_html=True)

    st.markdown("---")

    # ── Map type selector ──────────────────────────────────────────────────────
    f1, f2 = st.columns(2)
    map_type    = f1.selectbox("Show",
        ["Pickup Locations", "Drop Locations", "Both"],
        key="hm_type")
    status_filter = f2.selectbox("Trip Status",
        ["All", "completed", "cancelled"],
        key="hm_status")

    # Apply status filter
    filtered = trips
    if status_filter != "All":
        filtered = [t for t in filtered if t["status"] == status_filter]

    if not filtered:
        st.info("No trips match the selected filter.")
        return

    # ── Build heatmap data ─────────────────────────────────────────────────────
    pickup_points = []
    drop_points   = []

    for t in filtered:
        if t.get("pickup_lat") and t.get("pickup_lng"):
            pickup_points.append([t["pickup_lat"], t["pickup_lng"]])
        if t.get("drop_lat") and t.get("drop_lng"):
            drop_points.append([t["drop_lat"], t["drop_lng"]])

    # Center map on average coordinates or default to Bardhaman
    all_lats = [p[0] for p in pickup_points + drop_points]
    all_lngs = [p[1] for p in pickup_points + drop_points]
    center_lat = sum(all_lats) / len(all_lats) if all_lats else 23.23
    center_lng = sum(all_lngs) / len(all_lngs) if all_lngs else 87.85

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=12,
        tiles="CartoDB dark_matter")

    if map_type in ["Pickup Locations", "Both"] and pickup_points:
        HeatMap(pickup_points, radius=15, blur=10,
                gradient={"0.4": "blue", "0.7": "lime", "1.0": "red"},
                name="Pickups").add_to(m)

    if map_type in ["Drop Locations", "Both"] and drop_points:
        HeatMap(drop_points, radius=15, blur=10,
                gradient={"0.4": "purple", "0.7": "orange", "1.0": "yellow"},
                name="Drops").add_to(m)

    if not pickup_points and not drop_points:
        st.warning("No GPS coordinates found in trip data. "
                   "Drivers need to update their location for heatmap data.")
    else:
        st.markdown(f"""
        <div style='background:#FEF3CD;border-left:4px solid #FBBC04;
                    padding:10px 14px;border-radius:0 8px 8px 0;
                    font-size:13px;color:#5c4200;margin-bottom:12px;'>
            📍 Showing <b>{len(pickup_points)}</b> pickup points and
            <b>{len(drop_points)}</b> drop points from
            <b>{len(filtered)}</b> trips.
        </div>""", unsafe_allow_html=True)

    st_folium(m, width=None, height=550, use_container_width=True)

    # ── Pickup address frequency table ─────────────────────────────────────────
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔝 Top Pickup Areas")
        pickup_addrs = {}
        for t in filtered:
            addr = t.get("pickup_address", "Unknown")
            # Shorten address to first part
            short = addr.split(",")[0].strip() if addr else "Unknown"
            pickup_addrs[short] = pickup_addrs.get(short, 0) + 1

        pickup_df = pd.DataFrame(
            list(pickup_addrs.items()), columns=["Area", "Pickups"]
        ).sort_values("Pickups", ascending=False).head(10)

        fig = px.bar(pickup_df, x="Pickups", y="Area", orientation="h",
                     color_discrete_sequence=[BLUE])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                          margin=dict(l=10, r=10, t=10, b=10),
                          yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🔝 Top Drop Areas")
        drop_addrs = {}
        for t in filtered:
            addr = t.get("drop_address", "Unknown")
            short = addr.split(",")[0].strip() if addr else "Unknown"
            drop_addrs[short] = drop_addrs.get(short, 0) + 1

        drop_df = pd.DataFrame(
            list(drop_addrs.items()), columns=["Area", "Drops"]
        ).sort_values("Drops", ascending=False).head(10)

        fig = px.bar(drop_df, x="Drops", y="Area", orientation="h",
                     color_discrete_sequence=[PURPLE])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                          margin=dict(l=10, r=10, t=10, b=10),
                          yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

    # ── Export ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    export_rows = [{
        "Trip Code"      : t.get("trip_code", ""),
        "Status"         : t.get("status", ""),
        "Pickup Address" : t.get("pickup_address", ""),
        "Pickup Lat"     : t.get("pickup_lat", ""),
        "Pickup Lng"     : t.get("pickup_lng", ""),
        "Drop Address"   : t.get("drop_address", ""),
        "Drop Lat"       : t.get("drop_lat", ""),
        "Drop Lng"       : t.get("drop_lng", ""),
        "Fare"           : t.get("actual_fare") or t.get("estimated_fare") or 0,
    } for t in filtered]

    csv = pd.DataFrame(export_rows).to_csv(index=False)
    st.download_button(
        "📥 Download Trip Coordinates (CSV)",
        csv, "kloqride_heatmap.csv", "text/csv", type="primary")

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTER
# ══════════════════════════════════════════════════════════════════════════════

if "pricing_config" not in st.session_state:
    st.session_state.pricing_config = {
        "Kolkata": {"Auto": {"base": 50.0, "per_km": 15.0}, "Bike": {"base": 30.0, "per_km": 8.0}, "Mini Car": {"base": 80.0, "per_km": 20.0}, "SUV": {"base": 120.0, "per_km": 30.0}, "platform_fee": 10.0},
        "Howrah": {"Auto": {"base": 40.0, "per_km": 15.0}, "Bike": {"base": 30.0, "per_km": 8.0}, "Mini Car": {"base": 70.0, "per_km": 18.0}, "SUV": {"base": 100.0, "per_km": 25.0}, "platform_fee": 7.0},
        "Salt Lake": {"Auto": {"base": 45.0, "per_km": 16.0}, "Bike": {"base": 35.0, "per_km": 9.0}, "Mini Car": {"base": 80.0, "per_km": 20.0}, "SUV": {"base": 110.0, "per_km": 28.0}, "platform_fee": 8.0},
        "Durgapur": {"Auto": {"base": 35.0, "per_km": 12.0}, "Bike": {"base": 25.0, "per_km": 7.0}, "Mini Car": {"base": 60.0, "per_km": 16.0}, "SUV": {"base": 90.0, "per_km": 22.0}, "platform_fee": 6.0},
        "Asansol": {"Auto": {"base": 30.0, "per_km": 10.0}, "Bike": {"base": 20.0, "per_km": 6.0}, "Mini Car": {"base": 50.0, "per_km": 15.0}, "SUV": {"base": 80.0, "per_km": 20.0}, "platform_fee": 5.0}
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "login_time" not in st.session_state:
    st.session_state.login_time = None

# Check for session timeout
if st.session_state.logged_in and st.session_state.login_time:
    elapsed_minutes = (datetime.now() - st.session_state.login_time).total_seconds() / 60
    if elapsed_minutes > SESSION_TIMEOUT_MINUTES:
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.user_email = None
        st.session_state.login_time = None
        st.warning(f"⏰ Session expired after {SESSION_TIMEOUT_MINUTES} minutes of inactivity. Please log in again.")

if not st.session_state.logged_in:
    _u = st.query_params.get("u", "")
    if _u and _u in USERS:
        st.session_state.logged_in = True
        st.session_state.user = USERS[_u]
        st.session_state.user_email = _u
        st.session_state.login_time = datetime.now()
        st.rerun()
    else:
        show_login()
    
else:
    page = show_sidebar()
    if   page == "Overview":           page_overview()
    elif page == "Trip Tracking":      page_trips()
    elif page == "Driver Document Upload": page_driver_document_upload()
    elif page == "Revenue Reports":    page_revenue()
    elif page == "Live Map":           page_live_map()
    elif page == "Search Heatmap":     page_search_heatmap()
    elif page == "Notifications":      page_notifications()
    elif page == "Ride History":       page_ride_history()
    elif page == "Driver Performance": page_driver_performance()
    elif page == "Vehicle Management": page_vehicle_mgmt()
    elif page == "Promotions":         page_promotions()
    elif page == "Activate Promo":     page_activate_promo()
    elif page == "Send Notification":  page_send_notification()
    elif page == "Driver Online Log":  page_driver_online_log()
    elif page == "Rider Onboarding":   page_rider_onboarding()
    elif page == "Live Search Feed":   page_live_search_feed()
    elif page == "Driver Payments":    page_driver_payments()
    elif page == "Pricing & Fees":     page_pricing_config()
