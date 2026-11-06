"""
Ola Ride Insights - Streamlit app
Pages: Dashboard (5 views) | SQL Query Explorer | Power BI Report | Insights
Run from the project root:  streamlit run app/app.py
"""

import os
import re
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# ------------------------------------------------------------------ paths
ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "processed" / "ola_rides_clean.csv"
VEH_CSV = ROOT / "data" / "processed" / "vehicle_types.csv"
DB = ROOT / "data" / "processed" / "ola.db"
SQL_FILE = ROOT / "sql" / "02_ola_queries.sql"

GREEN, DARK, GREY, ORANGE, RED = "#8CC63F", "#1F2A2E", "#9AA5A9", "#F3A712", "#E4572E"
STATUS_COLORS = {"Success": GREEN, "Canceled by Driver": RED, "Canceled by Customer": ORANGE, "Driver Not Found": GREY}
VEH_ORDER = ["Prime Sedan", "Prime SUV", "Prime Plus", "Mini", "Auto", "Bike", "eBike"]

st.set_page_config(page_title="Ola Ride Insights", page_icon="🚕", layout="wide")

st.markdown(f"""
<style>
    [data-testid="stSidebar"] {{ background-color: {DARK}; }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{ color: #E8ECEC; }}
    [data-testid="stSidebar"] [data-baseweb="select"] p {{ color: {DARK}; }}
    div[data-testid="stMetric"] {{ background: #FFFFFF; border: 1px solid {GREEN}; border-radius: 10px; padding: 10px 14px; }}
    div[data-testid="stMetricValue"] {{ font-size: 1.6rem; }}
    .block-container {{ padding-top: 3.2rem; }}
    .ola-title {{ font-size: 2rem !important; font-weight: 800; color: {DARK}; margin-bottom: 0; line-height: 1.2; }}
    .ola-title span {{ color: {GREEN}; }}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data layer
@st.cache_resource(show_spinner="Preparing database...")
def ensure_db() -> Path:
    """Build the SQLite DB from the cleaned CSV if it is missing (e.g. on Streamlit Cloud)."""
    if DB.exists():
        return DB
    if not CSV.exists():
        st.error(f"Cleaned data not found at {CSV}. Run `python src/clean.py` first.")
        st.stop()
    df = pd.read_csv(CSV)
    with sqlite3.connect(DB) as con:
        df.to_sql("ola_rides", con, index=False, if_exists="replace")
        if VEH_CSV.exists():
            pd.read_csv(VEH_CSV).to_sql("vehicle_types", con, index=False, if_exists="replace")
        for col in ["Booking_Status", "Vehicle_Type", "Customer_ID", "Payment_Method", "Booking_Date"]:
            con.execute(f"CREATE INDEX IF NOT EXISTS idx_{col.lower()} ON ola_rides({col})")
    return DB


@st.cache_data(show_spinner="Loading rides...")
def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV, parse_dates=["Booking_Datetime"])
    df["Booking_Date"] = pd.to_datetime(df["Booking_Date"]).dt.date
    return df


@st.cache_data
def load_queries() -> list[dict]:
    """Parse the .sql file into [{id, title, sql}] using the `-- @Qn | title` markers."""
    text = SQL_FILE.read_text(encoding="utf-8")
    queries = []
    for block in re.split(r"^-- @", text, flags=re.M)[1:]:
        head, body = block.split("\n", 1)
        qid, title = [s.strip() for s in head.split("|", 1)]
        lines = body.strip().splitlines()
        comments = [l for l in lines if l.strip().startswith("--")]
        code_only = "\n".join(l for l in lines if not l.strip().startswith("--"))
        sql = code_only.split(";")[0].strip()          # comments may contain ';' so strip them first
        full = "\n".join(comments + [sql])             # shown in the UI: notes + query
        queries.append({"id": qid, "title": title, "sql": sql, "full": full.strip()})
    return queries


def run_sql(sql: str, where: str, params: list) -> pd.DataFrame:
    """Run a query against ola_rides. Sidebar filters are applied through a TEMP VIEW that shadows the table."""
    con = sqlite3.connect(f"file:{ensure_db()}?mode=ro", uri=True)
    try:
        if where:
            # Temp views can't use bound parameters, so values are inlined after quoting
            quoted = [("'" + str(p).replace("'", "''") + "'") for p in params]
            clause = where
            for q in quoted:
                clause = clause.replace("?", q, 1)
            con.execute(f"CREATE TEMP VIEW ola_rides AS SELECT * FROM main.ola_rides WHERE {clause}")
        return pd.read_sql_query(sql, con)
    finally:
        con.close()


def is_read_only(sql: str) -> bool:
    s = re.sub(r"--.*", "", sql).strip().lower()
    banned = ("insert", "update", "delete", "drop", "alter", "create", "attach", "pragma", "replace", "vacuum")
    return s.startswith(("select", "with")) and not any(re.search(rf"\b{b}\b", s) for b in banned) and ";" not in s.rstrip(";")


# ------------------------------------------------------------------ sidebar filters
df_all = load_data()
ensure_db()

with st.sidebar:
    st.markdown(f"<h2 style='color:{GREEN};margin-bottom:0'>🚕 OLA</h2><p style='margin-top:0'>Ride Insights · July 2024</p>",
                unsafe_allow_html=True)
    page = st.radio("Navigate", ["📊 Dashboard", "🧮 SQL Query Explorer", "📈 Power BI Report", "💡 Insights"],
                    label_visibility="collapsed")
    st.divider()
    st.subheader("Filters")
    dmin, dmax = df_all["Booking_Date"].min(), df_all["Booking_Date"].max()
    dr = st.date_input("Booking date", (dmin, dmax), min_value=dmin, max_value=dmax)
    d_from, d_to = (dr if isinstance(dr, (list, tuple)) and len(dr) == 2 else (dmin, dmax))
    vehicles = st.multiselect("Vehicle type", VEH_ORDER, placeholder="All vehicles")
    statuses = st.multiselect("Booking status", list(STATUS_COLORS), placeholder="All statuses")
    payments = st.multiselect("Payment method", ["Cash", "UPI", "Credit Card", "Debit Card"], placeholder="All methods")
    search = st.text_input("Search Booking / Customer ID", placeholder="e.g. CID954071").strip()
    st.caption("Filters apply to the dashboard **and** the SQL queries.")

# pandas mask + equivalent SQL where-clause
mask = (df_all["Booking_Date"] >= d_from) & (df_all["Booking_Date"] <= d_to)
where, params = ["Booking_Date BETWEEN ? AND ?"], [str(d_from), str(d_to)]
if vehicles:
    mask &= df_all["Vehicle_Type"].isin(vehicles)
    where.append(f"Vehicle_Type IN ({','.join('?' * len(vehicles))})"); params += vehicles
if statuses:
    mask &= df_all["Booking_Status"].isin(statuses)
    where.append(f"Booking_Status IN ({','.join('?' * len(statuses))})"); params += statuses
if payments:
    mask &= df_all["Payment_Method"].isin(payments)
    where.append(f"Payment_Method IN ({','.join('?' * len(payments))})"); params += payments
if search:
    s = search.upper()
    mask &= df_all["Booking_ID"].str.contains(s, regex=False) | df_all["Customer_ID"].str.contains(s, regex=False)
    where.append("(UPPER(Booking_ID) LIKE ? OR UPPER(Customer_ID) LIKE ?)"); params += [f"%{s}%", f"%{s}%"]
is_filtered = bool(vehicles or statuses or payments or search or (d_from, d_to) != (dmin, dmax))
WHERE_SQL = " AND ".join(where) if is_filtered else ""

df = df_all[mask]
succ = df[df["Booking_Status"] == "Success"]


def fmt_inr(v: float) -> str:
    if v >= 1e7:
        return f"₹{v/1e7:.2f} Cr"
    if v >= 1e5:
        return f"₹{v/1e5:.2f} L"
    return f"₹{v:,.0f}"


def style(fig, h=360, legend=True):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=50, b=10), plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(color=DARK), title_font=dict(size=15), showlegend=legend,
                      legend=dict(orientation="h", y=1.08, x=0, title=None))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#EDF0F0")
    return fig


def header(title, sub=""):
    st.markdown(f"<p class='ola-title'>{title} <span>·</span></p>", unsafe_allow_html=True)
    if sub:
        st.caption(sub)


# ================================================================== PAGES
if df.empty and page in ("📊 Dashboard",):
    header("Ola Ride Insights")
    st.warning("No rides match the current filters.")
    st.stop()

# ------------------------------------------------------------------ Dashboard
if page == "📊 Dashboard":
    header("Ola Ride Insights", f"{len(df):,} bookings · {d_from:%d %b} – {d_to:%d %b %Y}"
           + (" · filtered" if is_filtered else ""))
    view = st.segmented_control("View", ["Overall", "Vehicle Type", "Revenue", "Cancellation", "Ratings"],
                                default="Overall", label_visibility="collapsed") or "Overall"

    if view == "Overall":
        c = st.columns(5)
        c[0].metric("Total Bookings", f"{len(df):,}")
        c[1].metric("Successful Rides", f"{len(succ):,}")
        c[2].metric("Success Rate", f"{len(succ)/len(df):.1%}")
        c[3].metric("Revenue", fmt_inr(succ["Booking_Value"].sum()))
        c[4].metric("Unique Customers", f"{df['Customer_ID'].nunique():,}")

        daily = df.groupby("Booking_Date").agg(Bookings=("Booking_ID", "size"), Successful=("Is_Success", "sum")).reset_index()
        fig = px.line(daily, x="Booking_Date", y=["Bookings", "Successful"], markers=True, title="Ride Volume Over Time",
                      color_discrete_sequence=[DARK, GREEN], labels={"value": "Rides", "Booking_Date": "", "variable": ""})
        fig.update_yaxes(rangemode="tozero")
        st.plotly_chart(style(fig, 330), width="stretch")

        l, r = st.columns(2)
        stat = df["Booking_Status"].value_counts().reset_index()
        fig = px.pie(stat, names="Booking_Status", values="count", hole=0.55, title="Booking Status Breakdown",
                     color="Booking_Status", color_discrete_map=STATUS_COLORS)
        fig.update_traces(textinfo="percent", textfont_color="white")
        l.plotly_chart(style(fig, 360), width="stretch")
        hourly = df.groupby("Hour").agg(Bookings=("Booking_ID", "size"), Success_Rate=("Is_Success", "mean")).reset_index()
        fig = go.Figure()
        fig.add_bar(x=hourly["Hour"], y=hourly["Bookings"], name="Bookings", marker_color=GREEN)
        fig.add_scatter(x=hourly["Hour"], y=hourly["Success_Rate"] * 100, name="Success rate %", yaxis="y2",
                        mode="lines+markers", line=dict(color=DARK))
        fig.update_layout(title="Peak Demand Hours", yaxis2=dict(overlaying="y", side="right", range=[0, 100], showgrid=False,
                                                                  tickvals=[0, 25, 50, 75, 100], title="Success %"),
                          xaxis=dict(dtick=1, range=[-0.6, 23.6], title="Hour"))
        r.plotly_chart(style(fig, 360), width="stretch")

    elif view == "Vehicle Type":
        c = st.columns(4)
        c[0].metric("Total Booking Value", fmt_inr(df["Booking_Value"].sum()))
        c[1].metric("Success Booking Value", fmt_inr(succ["Booking_Value"].sum()))
        c[2].metric("Avg Distance (km)", f"{succ['Ride_Distance'].mean():.1f}" if len(succ) else "–")
        c[3].metric("Total Distance (km)", f"{succ['Ride_Distance'].sum():,}")

        veh = pd.read_csv(VEH_CSV) if VEH_CSV.exists() else pd.DataFrame({"Vehicle_Type": VEH_ORDER, "Vehicle_Images": None})
        tbl = (df.groupby("Vehicle_Type").agg(Total_Booking_Value=("Booking_Value", "sum"), Bookings=("Booking_ID", "size"))
               .join(succ.groupby("Vehicle_Type").agg(Success_Booking_Value=("Booking_Value", "sum"),
                                                      Avg_Distance=("Ride_Distance", "mean"),
                                                      Total_Distance=("Ride_Distance", "sum"),
                                                      Successful=("Booking_ID", "size")))
               .reset_index())
        tbl["Success_Rate"] = tbl["Successful"] / tbl["Bookings"] * 100
        tbl = veh[["Vehicle_Type", "Vehicle_Images"]].merge(tbl, on="Vehicle_Type", how="inner")
        st.dataframe(
            tbl[["Vehicle_Images", "Vehicle_Type", "Total_Booking_Value", "Success_Booking_Value", "Avg_Distance", "Total_Distance", "Success_Rate"]],
            hide_index=True, width="stretch",
            column_config={
                "Vehicle_Images": st.column_config.ImageColumn(" ", width="small"),
                "Vehicle_Type": "Vehicle Type",
                "Total_Booking_Value": st.column_config.NumberColumn("Total Booking Value (₹)", format="localized"),
                "Success_Booking_Value": st.column_config.NumberColumn("Success Booking Value (₹)", format="localized"),
                "Avg_Distance": st.column_config.NumberColumn("Avg. Distance (km)", format="%.2f"),
                "Total_Distance": st.column_config.NumberColumn("Total Distance (km)", format="localized"),
                "Success_Rate": st.column_config.ProgressColumn("Success Rate", format="%.1f%%", min_value=0, max_value=100),
            })
        l, r = st.columns(2)
        top5 = succ.groupby("Vehicle_Type")["Ride_Distance"].sum().nlargest(5).sort_values().reset_index()
        fig = px.bar(top5, x="Ride_Distance", y="Vehicle_Type", orientation="h", text_auto=",.0f",
                     title="Top 5 Vehicle Types by Ride Distance", color_discrete_sequence=[GREEN],
                     labels={"Ride_Distance": "Total km", "Vehicle_Type": ""})
        l.plotly_chart(style(fig, 340, False), width="stretch")
        avg = succ.groupby("Vehicle_Type")["Ride_Distance"].mean().reindex(VEH_ORDER).dropna().reset_index()
        fig = px.bar(avg, x="Vehicle_Type", y="Ride_Distance", text_auto=".1f", title="Average Ride Distance (km)",
                     color_discrete_sequence=[DARK], labels={"Ride_Distance": "Avg km", "Vehicle_Type": ""})
        r.plotly_chart(style(fig, 340, False), width="stretch")

    elif view == "Revenue":
        c = st.columns(4)
        lost = df.loc[df["Booking_Status"] != "Success", "Booking_Value"].sum()
        digital = succ["Payment_Method"].isin(["UPI", "Credit Card", "Debit Card"]).mean() if len(succ) else 0
        c[0].metric("Revenue", fmt_inr(succ["Booking_Value"].sum()))
        c[1].metric("Avg Booking Value", f"₹{succ['Booking_Value'].mean():,.0f}" if len(succ) else "–")
        c[2].metric("Lost Value (cancelled / not found)", fmt_inr(lost))
        c[3].metric("Digital Payment Share", f"{digital:.1%}")
        l, r = st.columns(2)
        pay = succ.groupby("Payment_Method")["Booking_Value"].sum().sort_values().reset_index()
        fig = px.bar(pay, x="Booking_Value", y="Payment_Method", orientation="h", text_auto=".3s",
                     title="Revenue by Payment Method", color_discrete_sequence=[GREEN],
                     labels={"Booking_Value": "Revenue (₹)", "Payment_Method": ""})
        l.plotly_chart(style(fig, 340, False), width="stretch")
        top = succ.groupby("Customer_ID")["Booking_Value"].sum().nlargest(5).sort_values().reset_index()
        fig = px.bar(top, x="Booking_Value", y="Customer_ID", orientation="h", text_auto=",",
                     title="Top 5 Customers by Total Booking Value", color_discrete_sequence=[DARK],
                     labels={"Booking_Value": "₹", "Customer_ID": ""})
        r.plotly_chart(style(fig, 340, False), width="stretch")
        dd = succ.groupby("Booking_Date")["Ride_Distance"].sum().reset_index()
        fig = px.bar(dd, x="Booking_Date", y="Ride_Distance", title="Ride Distance Distribution Per Day",
                     color_discrete_sequence=[GREEN], labels={"Ride_Distance": "Total km", "Booking_Date": ""})
        st.plotly_chart(style(fig, 320, False), width="stretch")

    elif view == "Cancellation":
        cust = df[df["Booking_Status"] == "Canceled by Customer"]
        drv = df[df["Booking_Status"] == "Canceled by Driver"]
        nf = (df["Booking_Status"] == "Driver Not Found").sum()
        c = st.columns(5)
        c[0].metric("Total Cancellations", f"{len(cust) + len(drv):,}")
        c[1].metric("Cancellation Rate", f"{(len(cust) + len(drv)) / len(df):.1%}")
        c[2].metric("By Customer", f"{len(cust):,}")
        c[3].metric("By Driver", f"{len(drv):,}")
        c[4].metric("Driver Not Found", f"{nf:,}")
        l, r = st.columns(2)
        for col, data, colname, title, colr in [
            (l, cust, "Canceled_Rides_by_Customer", "Cancelled Rides Reasons (Customer)", ORANGE),
            (r, drv, "Canceled_Rides_by_Driver", "Cancelled Rides Reasons (Drivers)", RED),
        ]:
            if data.empty:
                col.info(f"No rides for: {title}")
                continue
            rs = data[colname].value_counts().sort_values().reset_index()
            fig = px.bar(rs, x="count", y=colname, orientation="h", text_auto=",", title=title,
                         color_discrete_sequence=[colr], labels={"count": "Rides", colname: ""})
            col.plotly_chart(style(fig, 340, False), width="stretch")
        cv = (df[df["Booking_Status"] != "Success"].groupby(["Vehicle_Type", "Booking_Status"]).size()
              .reset_index(name="Rides"))
        fig = px.bar(cv, x="Vehicle_Type", y="Rides", color="Booking_Status", barmode="group",
                     category_orders={"Vehicle_Type": VEH_ORDER}, color_discrete_map=STATUS_COLORS,
                     title="Cancellations by Vehicle Type", labels={"Vehicle_Type": ""})
        st.plotly_chart(style(fig, 330), width="stretch")

    elif view == "Ratings":
        if succ.empty:
            st.info("Ratings exist only for successful rides - none in the current filter.")
            st.stop()
        c = st.columns(4)
        c[0].metric("Avg Driver Rating", f"{succ['Driver_Ratings'].mean():.2f} ★")
        c[1].metric("Avg Customer Rating", f"{succ['Customer_Rating'].mean():.2f} ★")
        c[2].metric("Avg Vehicle TAT", f"{succ['V_TAT'].mean():.0f}")
        c[3].metric("Avg Customer TAT", f"{succ['C_TAT'].mean():.0f}")
        l, r = st.columns(2)
        for col, cname, title, colr in [(l, "Driver_Ratings", "Driver Ratings Distribution", GREEN),
                                        (r, "Customer_Rating", "Customer Ratings Distribution", DARK)]:
            dist = succ[cname].value_counts().sort_index().reset_index()
            fig = px.bar(dist, x=cname, y="count", title=title, color_discrete_sequence=[colr],
                         labels={cname: "Rating", "count": "Rides"})
            col.plotly_chart(style(fig, 320, False), width="stretch")
        rv = succ.groupby("Vehicle_Type")[["Driver_Ratings", "Customer_Rating"]].mean().reindex(VEH_ORDER).dropna().reset_index()
        fig = px.bar(rv, x="Vehicle_Type", y=["Driver_Ratings", "Customer_Rating"], barmode="group", text_auto=".2f",
                     title="Customer vs. Driver Ratings by Vehicle Type", color_discrete_sequence=[GREEN, DARK],
                     labels={"value": "Avg rating", "Vehicle_Type": "", "variable": ""})
        fig.update_yaxes(range=[3, 4.3])
        st.plotly_chart(style(fig, 330), width="stretch")

    with st.expander("🔎 Browse filtered rides"):
        st.dataframe(df.drop(columns=["Booking_Datetime"]).head(1000), width="stretch", hide_index=True)
        st.caption(f"Showing first 1,000 of {len(df):,} rows.")
        st.download_button("Download filtered data (CSV)", df.to_csv(index=False).encode(), "ola_rides_filtered.csv", "text/csv")

# ------------------------------------------------------------------ SQL explorer
elif page == "🧮 SQL Query Explorer":
    header("SQL Query Explorer", "Queries run live on SQLite from sql/02_ola_queries.sql (same file works on MySQL).")
    queries = load_queries()
    labels = {q["id"]: f"{q['id']} · {q['title']}" for q in queries}
    apply_f = st.toggle("Apply sidebar filters to queries", value=is_filtered,
                        help="Wraps ola_rides in a filtered temporary view, so every query respects the sidebar filters.")
    tab_brief, tab_extra, tab_custom = st.tabs(["Brief questions (Q1–Q10)", "Extra insights (X1–X10)", "✍️ Custom SQL"])

    def show_query(q):
        st.markdown(f"#### {q['id']} · {q['title']}")
        st.code(q["full"], language="sql")
        try:
            res = run_sql(q["sql"], WHERE_SQL if apply_f else "", params if apply_f else [])
        except Exception as e:  # noqa: BLE001
            st.error(f"Query failed: {e}")
            return
        m1, m2 = st.columns([1, 4])
        m1.metric("Rows returned", f"{len(res):,}")
        if len(res) == 1 and res.shape[1] <= 3:
            for i, (k, v) in enumerate(res.iloc[0].items()):
                m2.metric(k.replace("_", " "), f"{v:,.2f}" if isinstance(v, float) else (f"{v:,}" if isinstance(v, int) else v))
        else:
            st.dataframe(res.head(5000), width="stretch", hide_index=True)
            if len(res) > 5000:
                st.caption("Showing first 5,000 rows - download for the full result.")
        st.download_button("Download result (CSV)", res.to_csv(index=False).encode(), f"{q['id']}.csv", "text/csv",
                           key=f"dl_{q['id']}")

    with tab_brief:
        brief = [q for q in queries if q["id"].startswith("Q")]
        pick = st.selectbox("Choose a question", [q["id"] for q in brief], format_func=labels.get, key="sel_q")
        show_query(next(q for q in brief if q["id"] == pick))
    with tab_extra:
        extra = [q for q in queries if q["id"].startswith("X")]
        pick = st.selectbox("Choose an insight query", [q["id"] for q in extra], format_func=labels.get, key="sel_x")
        show_query(next(q for q in extra if q["id"] == pick))
    with tab_custom:
        st.caption("Read-only: SELECT / WITH statements only. Table: `ola_rides`, `vehicle_types`.")
        with st.expander("Columns in ola_rides"):
            st.write(", ".join(f"`{c}`" for c in df_all.columns))
        sql = st.text_area("SQL", "SELECT Vehicle_Type, COUNT(*) AS Rides, ROUND(AVG(Booking_Value), 2) AS Avg_Fare\n"
                                  "FROM ola_rides\nWHERE Booking_Status = 'Success'\nGROUP BY Vehicle_Type\nORDER BY Rides DESC",
                           height=170)
        if st.button("▶ Run query", type="primary"):
            if not is_read_only(sql):
                st.error("Only a single SELECT/WITH statement is allowed.")
            else:
                try:
                    res = run_sql(sql.rstrip().rstrip(";"), WHERE_SQL if apply_f else "", params if apply_f else [])
                    st.success(f"{len(res):,} rows")
                    st.dataframe(res.head(5000), width="stretch", hide_index=True)
                except Exception as e:  # noqa: BLE001
                    st.error(f"Query failed: {e}")

# ------------------------------------------------------------------ Power BI
elif page == "📈 Power BI Report":
    header("Power BI Report", "Interactive 5-page report: Overall · Vehicle Type · Revenue · Cancellation · Ratings")
    embed_url = ""
    try:
        embed_url = st.secrets.get("POWERBI_EMBED_URL", "")
    except Exception:  # no secrets.toml
        embed_url = ""
    embed_url = embed_url or os.getenv("POWERBI_EMBED_URL", "")
    with st.expander("Embed settings", expanded=not embed_url):
        embed_url = st.text_input("Power BI 'Publish to web' URL", embed_url,
                                  placeholder="https://app.powerbi.com/view?r=...")
        st.markdown(
            "1. Open `powerbi/OlaRideInsights.pbip` in Power BI Desktop → **Publish** to your workspace.\n"
            "2. In the Power BI service: **File → Embed report → Publish to web (public)** → copy the link.\n"
            "3. Paste it above, or save it permanently in `.streamlit/secrets.toml` as `POWERBI_EMBED_URL = \"...\"`.")
    embed_url = embed_url.strip()
    if embed_url.startswith("https://app.powerbi.com/"):
        if hasattr(st, "iframe"):          # Streamlit >= 1.5x
            st.iframe(embed_url, height=760)
        else:                              # older Streamlit
            components.iframe(embed_url, height=760, scrolling=False)
    else:
        if embed_url:
            st.error("That doesn't look like a Power BI link. Use the 'Link you can send in email' "
                     "(https://app.powerbi.com/view?r=...), not the iframe HTML.")
        # Plan B: static screenshots of the report pages, if provided
        shots_dir = ROOT / "assets" / "powerbi_screens"
        shots = sorted(p for p in shots_dir.glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg")) if shots_dir.exists() else []
        if shots:
            st.caption("Power BI report pages (screenshots from Power BI Desktop).")
            names = [re.sub(r"^\d+[_\-\s]*", "", p.stem).replace("_", " ").title() for p in shots]
            for tab, shot in zip(st.tabs(names), shots):
                with tab:
                    st.image(str(shot), width="stretch")
        else:
            st.info("No embed URL yet. Publish the report and paste its 'Publish to web' link above, "
                    "or drop page screenshots (1_overall.png ... 5_ratings.png) into assets/powerbi_screens/. "
                    "Meanwhile, the 📊 Dashboard page shows the same five views.")

# ------------------------------------------------------------------ Insights
elif page == "💡 Insights":
    header("Key Insights & Recommendations", "Full month, all bookings (ignores sidebar filters)")
    a = df_all
    s_all = a[a["Booking_Status"] == "Success"]
    c = st.columns(4)
    c[0].metric("Success rate", f"{len(s_all)/len(a):.1%}")
    c[1].metric("Driver cancellations", f"{(a['Booking_Status']=='Canceled by Driver').mean():.1%}")
    c[2].metric("Revenue", fmt_inr(s_all["Booking_Value"].sum()))
    c[3].metric("Cash share of rides", f"{(s_all['Payment_Method']=='Cash').mean():.0%}")
    st.markdown("""
**What the data says**
- **Fulfilment is the core problem.** Only 62% of bookings become rides. Drivers cancel 17.9% (1.8× customers) and 9.8% find no driver, so ~₹2.15 Cr of quoted value is lost in a month.
- **55% of customer cancellations are driver-caused**: "driver not moving towards pickup" and "driver asked to cancel".
- **Demand is flat** by hour (~4.3k/hour), weekday (~3.3k/day) and across the month. Mon–Wed only *look* higher because July 2024 had five of each.
- **Cash dominates (55%)**, UPI 40%, cards under 5%.
- **Auto trips are short (10 km avg)**, while all other vehicles average ~25 km.
- **Ratings are uniform** (avg ~4.0, spread 3–5) for both drivers and customers across every vehicle type.
- **Fare doesn't follow distance** (r ≈ 0). The top 1% of rides cost more than ₹640/km against a ₹20/km median, so these are flagged for review.

**What to do**
1. Penalise driver-initiated cancellations and auto-reassign when the driver isn't moving. This is the single largest lever (~24k rides/month).
2. Rebalance supply into *Driver Not Found* pockets with acceptance bonuses.
3. Use a steady 24×7 supply plan with small boosts at 08–10, 12 and 15–17 instead of relying on surge pricing.
4. Offer UPI cashback to shift cash rides to digital payments.
5. Build loyalty: 91.6% of customers rode only once in July.
6. Audit pricing logic and auto-flag high fare-per-km rides.
7. Add rating tags (cleanliness, driving, punctuality) so feedback becomes actionable.
""")

st.sidebar.caption("Data: OLA bookings, Bengaluru, July 2024 · 103,024 rows")
