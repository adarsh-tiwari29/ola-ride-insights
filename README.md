<h1 align="center">Ola Ride Insights</h1>

<p align="center">
  <b>End-to-end analysis of 1,03,024 OLA ride bookings (Bengaluru, July 2024)</b><br>
  Data Cleaning → EDA → SQL → Power BI Dashboard → Streamlit App
</p>

<p align="center">
  <a href="https://ola-ride-insightss.streamlit.app/"><img src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg" alt="Open in Streamlit"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white">
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white">
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white">
  <img src="https://img.shields.io/badge/Power%20BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black">
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white">
  <img src="https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white">
</p>

---

## Live Demo

**[ola-ride-insightss.streamlit.app](https://ola-ride-insightss.streamlit.app/)**

**Domain:** Ride-sharing & Mobility Analytics

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Insights](#key-insights)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [1. Data Cleaning and Preprocessing](#1-data-cleaning-and-preprocessing)
- [2. SQL Analysis](#2-sql-analysis)
- [3. Power BI Dashboard](#3-power-bi-dashboard)
- [4. Streamlit App](#4-streamlit-app)
- [Recommendations](#recommendations)

---

## Project Overview

This project analyses one month of OLA ride bookings to understand **booking success, cancellations, revenue, vehicle performance and ratings**, and turns the findings into business recommendations.

| Metric | Value |
|---|---|
| Total bookings | **1,03,024** |
| Successful rides | **63,967** (62.1%) |
| Revenue (successful rides) | **₹3.51 Cr** |
| Driver cancellations | **17.9%** |
| Customer cancellations | **10.2%** |
| Driver not found | **9.8%** |
| Avg rating | **~4.0** |

---

## Key Insights

- **62.1% success rate.** Drivers cancel **17.9%** of bookings (1.8× customers at 10.2%) and **9.8%** find no driver, which comes to about **₹2.15 Cr** of quoted value lost in one month.
- **55% of customer cancellations are actually driver-caused** ("driver not moving", "driver asked to cancel").
- **Demand is flat:** ~3,300 bookings/day and ~4,300/hour. Mon–Wed only look higher because July 2024 had 5 of each.
- **Revenue ₹3.51 Cr:** Cash 55% · UPI 40% · Cards under 5%.
- **Auto trips average 10 km**, against ~25 km for every other vehicle type.
- **Ratings are uniform** (~4.0, range 3–5) across all vehicles.
- **Fare ≠ distance** (r ≈ 0). The top 1% of rides cost more than **₹640/km** against a **₹20/km** median, so they are flagged for audit.

---

## Project Structure

```
ola-ride-insights/
├── data/
│   ├── raw/OLA_DataSet.xlsx              # original file (sheet "July")
│   └── processed/
│       ├── ola_rides_clean.csv           # cleaned fact table (32 cols)
│       └── vehicle_types.csv             # vehicle dimension + icon URLs
├── notebooks/Ola_Ride_Insights_EDA.ipynb # EDA (15 charts)
├── src/clean.py                          # cleaning pipeline → CSV + SQLite DB
├── sql/
│   ├── 01_schema_mysql.sql               # MySQL table + LOAD DATA (optional)
│   └── 02_ola_queries.sql                # 10 brief questions + 10 insight queries
├── powerbi/OlaRideInsights.pbip          # Power BI project (5 pages)
├── app/app.py                            # Streamlit app
├── assets/powerbi_screens/               # Power BI page screenshots (fallback)
├── .streamlit/                           # theme + secrets example
└── requirements.txt
```

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/ola-ride-insights.git
cd ola-ride-insights

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build cleaned data (CSV + ola.db)
python src/clean.py

# 4. Launch the app → http://localhost:8501
python -m streamlit run app/app.py
```

> The notebook runs top-to-bottom with no errors (`Kernel → Restart & Run All`).

---

## 1. Data Cleaning and Preprocessing

| Step | What was done |
|---|---|
| **Source** | Only the `July` sheet (Sheet1/Sheet2 are scratch pivots) |
| **Duplicates** | None (by row or Booking_ID). Dedup kept as a safeguard |
| **Date/Time** | `Date` already holds the full timestamp → `Booking_Datetime`, `Booking_Date`, `Booking_Time`. `Time` dropped |
| **Missing values** | **Structural:** non-successful bookings have no TAT/payment/ratings. Text → `"Not Applicable"`, numeric left **NULL** so averages aren't dragged to 0 |
| **Derived features** | `Day`, `Day_Name`, `Weekday_Num`, `Is_Weekend`, `Hour`, `Time_Slot`, `Ride_Outcome`, `Is_Success`, `Is_Canceled`, `Revenue` (successful rides only), `Distance_Band`, `Fare_per_km` |

---

## 2. SQL Analysis

[`sql/02_ola_queries.sql`](sql/02_ola_queries.sql) runs unchanged on **MySQL 8** and **SQLite**.

| # | Question | Result |
|---|---|---|
| Q1 | All successful bookings | 63,967 rows |
| Q2 | Avg ride distance per vehicle | ~15.5 km all bookings (Auto 6.2) · **~25 km successful rides (Auto 10.0)** |
| Q3 | Rides cancelled by customers | **10,499** |
| Q4 | Top 5 customers by rides | CID954071 (5), then 4-ride ties |
| Q5 | Driver cancellations (personal & car issues) | **6,542** |
| Q6 | Max / min driver rating, Prime Sedan | **5.0 / 3.0** |
| Q7 | Rides paid by UPI | 25,881 rows |
| Q8 | Avg customer rating per vehicle | 3.99 – 4.01 (all ≈ 4.0) |
| Q9 | Total booking value of successful rides | **₹3,50,80,467** |
| Q10 | Incomplete rides with reason | 3,926 rows (Customer Demand 1,601 · Vehicle Breakdown 1,591 · Other 734) |

**Extra queries (X1–X10):** status share, peak hours, revenue by payment method, top customers by value, vehicle scorecard, cancellation reasons, high-cancel pickup zones, fare-per-km anomalies and daily trend.

**MySQL (optional):** run `01_schema_mysql.sql` (edit the CSV path), then `02_ola_queries.sql`.

---

## 3. Power BI Dashboard

5 pages built on the Ola slide template, with working left-nav buttons and synced **Booking Date** range + **Vehicle Type** slicers on every page.

| Page | Visuals |
|---|---|
| **Overall** | KPIs · Ride Volume Over Time · Booking Status Breakdown · Peak Demand by Hour |
| **Vehicle Type** | KPIs · Vehicle scorecard (icons, Total/Success Booking Value, Avg/Total Distance, Success %) · Top 5 Vehicle Types by Distance · Avg Distance |
| **Revenue** | KPIs · Revenue by Payment Method · Top 5 Customers by Booking Value · Ride Distance per Day |
| **Cancellation** | KPIs · Customer Cancellation Reasons · Driver Cancellation Reasons · Cancellations by Vehicle |
| **Ratings** | KPIs · Driver Ratings Distribution · Customer Ratings Distribution · Customer vs Driver Ratings |

**Data model:** `ola_rides` (fact, 21 DAX measures) ↔ `vehicle_types` (dimension, image URLs, sort order)

<details>
<summary><b>How to open the Power BI report</b></summary>

1. Run `python src/clean.py` (creates the CSVs).
2. Open `powerbi/OlaRideInsights.pbip` in Power BI Desktop.
3. **Transform data → Edit parameters → `DataFolder`** = full path to `data\processed\` (ending with `\`) → **Refresh**.
4. `File → Save as → .pbix` if you need a single file.

> If Desktop asks, enable *Options → Preview features → Power BI Project (.pbip) save option* and *Store reports using enhanced metadata format (PBIR)*.

**Embed in Streamlit:** Publish → Power BI Service → `File → Embed report → Publish to web` → copy the link → add it to `.streamlit/secrets.toml` as `POWERBI_EMBED_URL` (see `.example`), or paste it in the app.

</details>

---

## 4. Streamlit App

**Live:** [ola-ride-insightss.streamlit.app](https://ola-ride-insightss.streamlit.app/)

| Section | What it does |
|---|---|
| **Dashboard** | The same 5 views with KPIs and Plotly charts, a filtered-data browser and CSV download |
| **SQL Query Explorer** | Pick any query from the `.sql` file, view the SQL, run it live and download the result. Includes a read-only **custom SQL** editor |
| **Power BI Report** | Embedded "Publish to web" report (falls back to page screenshots if no link is set) |
| **Insights** | Key findings and recommendations |
| **Sidebar Filters** | Date range, vehicle, status, payment and ID search. Applies to the dashboard *and* the SQL queries (via a filtered temp view) |

**Deploy (Streamlit Community Cloud):** push to GitHub → *New app* → main file `app/app.py` → add `POWERBI_EMBED_URL` under *Secrets*. `ola.db` is rebuilt automatically from the CSV on first run.

---

## Recommendations

1. **Penalise driver-initiated cancellations** and auto-reassign stalled pickups (~24k rides/month at stake).
2. **Rebalance supply** into *Driver Not Found* zones with acceptance bonuses.
3. **Use a steady 24×7 supply plan** with light boosts at 08–10, 12 and 15–17 hrs.
4. **Offer UPI cashback** to cut cash dependence.
5. **Launch loyalty or subscription passes**, since 91.6% of customers rode only once.
6. **Audit pricing** and auto-flag rides with a high fare per km.
7. **Add tagged ratings** (cleanliness, driving, punctuality) for actionable feedback.

---

<p align="center">
  Made by <b>Adarsh Tiwari</b> · Data Analyst Intern @ Labmentrix
</p>
