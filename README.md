# 🚖 Kloq Ride — Operations Dashboard

A full-featured ride-hailing operations dashboard built with **Streamlit**, **Plotly**, and **Folium**.

## Features (13 Pages)

| # | Page | Description |
|---|---|---|
| 1 | **Overview** | KPI cards, revenue charts, top zones, payment methods |
| 2 | **Trip Tracking** | Trip analytics, heatmap, filterable trip table |
| 3 | **Driver Management** | Fleet overview, driver stats, add new drivers |
| 4 | **Revenue Reports** | Revenue trends, daily breakdown, CSV export |
| 5 | **Live Map** | Real-time GPS tracking with Folium map |
| 6 | **Notifications** | Alert system with priority filtering |
| 7 | **Ride History** | Customer-level trip history and spending trends |
| 8 | **Driver Performance** | Per-driver analytics, leaderboard, earnings |
| 9 | **Vehicle Management** | Fleet inventory, insurance tracking, service schedule |
| 10 | **Promotions** | Coupon management with usage progress bars |
| 11 | **Manage Driver** | Activate/deactivate drivers, document upload (DL, Aadhaar, Insurance) |
| 12 | **Send Notification** | Broadcast messages to riders and drivers |
| 13 | **Driver Online Log** | Track online/offline sessions and hours worked |

## Setup

```bash
pip install -r kloqride_demo/requirements.txt
```

## Run

```bash
cd kloqride_demo
streamlit run app.py
```

## Demo Accounts

| Email | Password | Role |
|---|---|---|
| admin@kloqride.com | admin123 | Admin |
| ops@kloqride.com | ops123 | Operations |
| driver@kloqride.com | driver123 | Driver |

## Tech Stack

- **Streamlit** — UI framework
- **Plotly** — Interactive charts
- **Folium** — Map visualization
- **Pandas** — Data processing

---

> ⚡ Demo mode — all data is generated in-memory for demonstration purposes.
