# 🚕 Ola Ride Insights

End-to-end analysis of **103,024 OLA ride bookings** (Bengaluru, July 2024): data cleaning → EDA → SQL → Power BI dashboard → Streamlit app.

**Domain:** Ride-sharing & mobility analytics  
**Stack:** Python (pandas, NumPy, Matplotlib, Seaborn), SQL (MySQL / SQLite), Power BI, Streamlit, Plotly

---

## 📁 Project structure

```
ola-ride-insights/
├── data/
│   ├── raw/OLA_DataSet.xlsx              # original file (sheet "July")
│   └── processed/
│       ├── ola_rides_clean.csv           # cleaned fact table (32 cols)
│       └── vehicle_types.csv             # vehicle dimension + icon URLs
├── notebooks/Ola_Ride_Insights_EDA.ipynb # EDA in the submission template (15 charts)
├── src/clean.py                          # cleaning pipeline → CSV + SQLite DB
├── sql/
│   ├── 01_schema_mysql.sql               # MySQL table + LOAD DATA (optional)
│   └── 02_ola_queries.sql                # 10 brief questions + 10 insight queries
├── powerbi/OlaRideInsights.pbip          # Power BI project (5 pages)
├── app/app.py                            # Streamlit app
├── .streamlit/                           # theme + secrets example
└── requirements.txt
```

## ⚙️ Setup

```bash
pip install -r requirements.txt
python src/clean.py                 # builds data/processed/* (CSV + ola.db)
streamlit run app/app.py            # opens http://localhost:8501
```
The notebook runs top-to-bottom with no errors (`Kernel → Restart & Run All`).

---

## 1️⃣ Data cleaning & preprocessing

| Step | What was done |
|---|---|
| Source | Only the `July` sheet (Sheet1/Sheet2 are scratch pivots) |
| Duplicates | None (rows or Booking_ID). Dedup kept as a safeguard |
| Date/time | `Date` already has the full timestamp → `Booking_Datetime`, `Booking_Date`, `Booking_Time`. `Time` dropped |
| Missing values | **Structural**: non-successful bookings have no TAT/payment/ratings. Text → `"Not Applicable"`, numeric left **NULL** so averages aren't dragged to 0 |
| Derived features | `Day`, `Day_Name`, `Weekday_Num`, `Is_Weekend`, `Hour`, `Time_Slot`, `Ride_Outcome`, `Is_Success`, `Is_Canceled`, `Revenue` (fare for successful rides only), `Distance_Band`, `Fare_per_km` |

## 2️⃣ SQL (`sql/02_ola_queries.sql`)

Runs unchanged on **MySQL 8** and **SQLite**. Results on the full dataset:

| # | Question | Result |
|---|---|---|
| Q1 | All successful bookings | 63,967 rows |
| Q2 | Avg ride distance per vehicle | ~15.5 km all bookings (Auto 6.2); **~25 km successful rides (Auto 10.0)** |
| Q3 | Rides cancelled by customers | **10,499** |
| Q4 | Top 5 customers by rides | CID954071 (5), then 4-ride ties |
| Q5 | Driver cancellations: personal & car issues | **6,542** |
| Q6 | Max / min driver rating, Prime Sedan | **5.0 / 3.0** |
| Q7 | Rides paid by UPI | 25,881 rows |
| Q8 | Avg customer rating per vehicle | 3.99 – 4.01 (all ≈ 4.0) |
| Q9 | Total booking value of successful rides | **₹3,50,80,467** |
| Q10 | Incomplete rides with reason | 3,926 rows (Customer Demand 1,601 · Vehicle Breakdown 1,591 · Other 734) |

Extra queries X1–X10 cover status share, peak hours, revenue by payment, top customers by value, vehicle scorecard, cancellation reasons, high-cancel pickup zones, fare-per-km anomalies and daily trend.

**MySQL (optional):** run `01_schema_mysql.sql` (edit the CSV path), then `02_ola_queries.sql`.

## 3️⃣ Power BI dashboard (`powerbi/`)

5 pages built on the Ola slide template with working left-nav buttons, a synced **Booking Date** range slicer and **Vehicle Type** slicer on every page:

| Page | Visuals |
|---|---|
| **Overall** | KPIs · Ride Volume Over Time · Booking Status Breakdown · Peak Demand by Hour |
| **Vehicle Type** | KPIs · Vehicle scorecard table (icons, Total/Success Booking Value, Avg/Total Distance, Success %) · Top 5 Vehicle Types by Ride Distance · Avg distance |
| **Revenue** | KPIs · Revenue by Payment Method · Top 5 Customers by Total Booking Value · Ride Distance per Day |
| **Cancellation** | KPIs · Cancelled Rides Reasons (Customer) · Cancelled Rides Reasons (Drivers) · Cancellations by Vehicle |
| **Ratings** | KPIs · Driver Ratings distribution · Customer Ratings distribution · Customer vs Driver Ratings |

Model: `ola_rides` (fact, 21 DAX measures) ↔ `vehicle_types` (dim, image URLs, sort order).

**Open it**
1. Run `python src/clean.py` (creates the CSVs).
2. Open `powerbi/OlaRideInsights.pbip` in Power BI Desktop.
3. **Transform data → Edit parameters → `DataFolder`** = full path to `data\processed\` (ending with `\`) → **Refresh**.
4. `File → Save as → .pbix` if you need a single file to submit.

> If Desktop asks, enable *Options → Preview features → Power BI Project (.pbip) save option* and *Store reports using enhanced metadata format (PBIR)*.

**Embed in Streamlit:** Publish → in Power BI service `File → Embed report → Publish to web` → copy the link → put it in `.streamlit/secrets.toml` as `POWERBI_EMBED_URL` (see `.example`) or paste it in the app.

## 4️⃣ Streamlit app (`app/app.py`)

- **Dashboard:** the same 5 views with KPIs and Plotly charts, a filtered-data browser and CSV download.
- **SQL Query Explorer:** pick any query from the `.sql` file, see the SQL, run it live and download the result. A read-only **custom SQL** editor is included too.
- **Power BI Report:** embedded "Publish to web" report.
- **Insights:** findings and recommendations.
- **Sidebar filters** (date range, vehicle, status, payment, ID search) apply to the dashboard *and* the SQL queries (through a filtered temp view).

**Deploy (Streamlit Community Cloud):** push to GitHub → *New app* → main file `app/app.py` → add `POWERBI_EMBED_URL` under *Secrets*. `ola.db` is rebuilt automatically from the CSV on first run.

---

## 💡 Key insights

- **62.1% success rate.** Drivers cancel **17.9%** (1.8× customers at 10.2%) and **9.8%** find no driver. That is about **₹2.15 Cr** of quoted value lost in a month.
- **55% of customer cancellations are driver-caused** ("driver not moving", "driver asked to cancel").
- **Demand is flat**: ~3,300 bookings/day and ~4,300/hour. Mon–Wed only look higher because July 2024 had 5 of each.
- **Revenue ₹3.51 Cr**: Cash 55% · UPI 40% · Cards under 5%.
- **Auto trips average 10 km** against ~25 km for every other vehicle.
- **Ratings are uniform** (~4.0, range 3–5) across all vehicles.
- **Fare ≠ distance** (r ≈ 0). The top 1% of rides cost more than ₹640/km against a ₹20/km median, so they are flagged for audit.

## ✅ Recommendations

1. Penalise driver-initiated cancellations and auto-reassign stalled pickups (~24k rides/month at stake).
2. Rebalance supply into *Driver Not Found* zones with acceptance bonuses.
3. Use a steady 24×7 supply plan with light boosts at 08–10, 12 and 15–17.
4. Offer UPI cashback to cut cash dependence.
5. Launch loyalty or subscription passes (91.6% of customers rode only once).
6. Audit pricing and auto-flag high fare-per-km rides.
7. Add tagged ratings (cleanliness, driving, punctuality) for actionable feedback.
