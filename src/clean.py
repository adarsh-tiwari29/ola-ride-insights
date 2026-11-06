"""
clean.py - Ola Ride Insights
Loads the raw OLA July-2024 booking export, cleans it and writes:
    data/processed/ola_rides_clean.csv   (fact table, used by Power BI + Streamlit)
    data/processed/vehicle_types.csv     (vehicle dimension with icon URLs)
    data/processed/ola.db                (SQLite database, table `ola_rides`)

Run from the project root:
    python src/clean.py
"""

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "OLA_DataSet.xlsx"
OUT = ROOT / "data" / "processed"

NA_LABEL = "Not Applicable"  # used for reasons that only exist for some statuses


def load_raw(path: Path = RAW) -> pd.DataFrame:
    """Read only the `July` sheet - Sheet1/Sheet2 are scratch pivots in the source file."""
    if not path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {path}")
    return pd.read_excel(path, sheet_name="July")


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Standardise column names (no spaces) and trim text columns
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    obj_cols = df.select_dtypes(include=["object", "string"]).columns
    for c in obj_cols:
        if c != "Time":
            df[c] = df[c].astype("string").str.strip()

    # 2. Drop exact duplicates / duplicate booking ids (none expected, kept as a safeguard)
    df = df.drop_duplicates().drop_duplicates(subset="Booking_ID", keep="first")

    # 3. Date & time: `Date` already holds the full timestamp, `Time` is a duplicate time-of-day
    df["Booking_Datetime"] = pd.to_datetime(df["Date"])
    df["Booking_Date"] = df["Booking_Datetime"].dt.date
    df["Booking_Time"] = df["Booking_Datetime"].dt.strftime("%H:%M:%S")
    df = df.drop(columns=["Date", "Time"])

    # 4. Missing values - they are structural, not random:
    #    every non-Success booking has no TAT, payment, ratings or Incomplete flag.
    #    Text columns -> explicit label; numeric columns stay NULL so averages are not distorted.
    df["Canceled_Rides_by_Customer"] = df["Canceled_Rides_by_Customer"].fillna(NA_LABEL)
    df["Canceled_Rides_by_Driver"] = df["Canceled_Rides_by_Driver"].fillna(NA_LABEL)
    df["Incomplete_Rides"] = df["Incomplete_Rides"].fillna(NA_LABEL)
    df["Incomplete_Rides_Reason"] = df["Incomplete_Rides_Reason"].fillna(NA_LABEL)
    df["Payment_Method"] = df["Payment_Method"].fillna(NA_LABEL)

    # 5. Types
    for c in ["V_TAT", "C_TAT", "Driver_Ratings", "Customer_Rating"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["Booking_Value"] = pd.to_numeric(df["Booking_Value"], errors="coerce").astype("Int64")
    df["Ride_Distance"] = pd.to_numeric(df["Ride_Distance"], errors="coerce").astype("Int64")

    # 6. Derived features
    dt = df["Booking_Datetime"]
    df["Day"] = dt.dt.day
    df["Day_Name"] = dt.dt.day_name()
    df["Weekday_Num"] = dt.dt.dayofweek + 1  # Monday = 1
    df["Is_Weekend"] = np.where(df["Weekday_Num"] >= 6, "Weekend", "Weekday")
    df["Hour"] = dt.dt.hour
    df["Time_Slot"] = pd.cut(
        df["Hour"],
        bins=[-1, 5, 11, 16, 20, 23],
        labels=["Night (0-5)", "Morning (6-11)", "Afternoon (12-16)", "Evening (17-20)", "Late Evening (21-23)"],
    ).astype("string")

    # Final ride outcome: splits Success into Completed vs Incomplete
    df["Ride_Outcome"] = np.select(
        [
            (df["Booking_Status"] == "Success") & (df["Incomplete_Rides"] == "Yes"),
            df["Booking_Status"] == "Success",
        ],
        ["Incomplete", "Completed"],
        default=df["Booking_Status"],
    )
    df["Is_Success"] = (df["Booking_Status"] == "Success").astype(int)
    df["Is_Canceled"] = df["Booking_Status"].isin(["Canceled by Customer", "Canceled by Driver"]).astype(int)

    # Revenue only counts for successful bookings (cancelled rows still carry a quoted fare)
    df["Revenue"] = np.where(df["Is_Success"] == 1, df["Booking_Value"], 0)

    df["Distance_Band"] = pd.cut(
        df["Ride_Distance"].astype(float),
        bins=[-1, 0, 10, 20, 30, 40, 50],
        labels=["0 km (no ride)", "1-10 km", "11-20 km", "21-30 km", "31-40 km", "41-50 km"],
    ).astype("string")

    # Value per km for successful rides (pricing pattern analysis)
    dist = df["Ride_Distance"].astype(float).replace(0, np.nan)
    df["Fare_per_km"] = np.where(df["Is_Success"] == 1, (df["Booking_Value"] / dist).round(2), np.nan)

    order = [
        "Booking_ID", "Booking_Datetime", "Booking_Date", "Booking_Time", "Day", "Day_Name", "Weekday_Num",
        "Is_Weekend", "Hour", "Time_Slot", "Booking_Status", "Ride_Outcome", "Is_Success", "Is_Canceled",
        "Customer_ID", "Vehicle_Type", "Pickup_Location", "Drop_Location", "V_TAT", "C_TAT",
        "Canceled_Rides_by_Customer", "Canceled_Rides_by_Driver", "Incomplete_Rides", "Incomplete_Rides_Reason",
        "Booking_Value", "Revenue", "Payment_Method", "Ride_Distance", "Distance_Band", "Fare_per_km",
        "Driver_Ratings", "Customer_Rating", "Vehicle_Images",
    ]
    return df[order].sort_values("Booking_Datetime").reset_index(drop=True)


def vehicle_dim(df: pd.DataFrame) -> pd.DataFrame:
    order = ["Prime Sedan", "Prime SUV", "Prime Plus", "Mini", "Auto", "Bike", "eBike"]
    v = df.groupby("Vehicle_Type", as_index=False)["Vehicle_Images"].first()
    v["Sort_Order"] = v["Vehicle_Type"].map({k: i + 1 for i, k in enumerate(order)})
    return v.sort_values("Sort_Order")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = load_raw()
    df = clean(raw)
    veh = vehicle_dim(df)
    fact = df.drop(columns=["Vehicle_Images"])

    fact.to_csv(OUT / "ola_rides_clean.csv", index=False)
    veh.to_csv(OUT / "vehicle_types.csv", index=False)

    db = OUT / "ola.db"
    db.unlink(missing_ok=True)
    with sqlite3.connect(db) as con:
        sql_df = fact.copy()
        sql_df["Booking_Datetime"] = sql_df["Booking_Datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
        sql_df["Booking_Date"] = sql_df["Booking_Date"].astype(str)
        sql_df.to_sql("ola_rides", con, index=False)
        veh.to_sql("vehicle_types", con, index=False)
        for col in ["Booking_Status", "Vehicle_Type", "Customer_ID", "Payment_Method", "Booking_Date"]:
            con.execute(f"CREATE INDEX idx_{col.lower()} ON ola_rides({col})")

    print(f"raw rows: {len(raw):,} -> clean rows: {len(fact):,}")
    print(f"written: {OUT}")


if __name__ == "__main__":
    main()
