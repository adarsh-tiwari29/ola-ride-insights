-- =====================================================================
-- Ola Ride Insights - MySQL schema + load
-- Only needed if you want MySQL (e.g. to connect Power BI to MySQL).
-- The Streamlit app uses the bundled SQLite DB and does NOT need this.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS ola;
USE ola;

DROP TABLE IF EXISTS ola_rides;
CREATE TABLE ola_rides (
    Booking_ID                  VARCHAR(20)  PRIMARY KEY,
    Booking_Datetime            DATETIME     NOT NULL,
    Booking_Date                DATE         NOT NULL,
    Booking_Time                TIME         NOT NULL,
    Day                         TINYINT,
    Day_Name                    VARCHAR(10),
    Weekday_Num                 TINYINT,
    Is_Weekend                  VARCHAR(10),
    Hour                        TINYINT,
    Time_Slot                   VARCHAR(25),
    Booking_Status              VARCHAR(25)  NOT NULL,
    Ride_Outcome                VARCHAR(25),
    Is_Success                  TINYINT,
    Is_Canceled                 TINYINT,
    Customer_ID                 VARCHAR(15)  NOT NULL,
    Vehicle_Type                VARCHAR(15)  NOT NULL,
    Pickup_Location             VARCHAR(50),
    Drop_Location               VARCHAR(50),
    V_TAT                       DECIMAL(6,1) NULL,
    C_TAT                       DECIMAL(6,1) NULL,
    Canceled_Rides_by_Customer  VARCHAR(60),
    Canceled_Rides_by_Driver    VARCHAR(60),
    Incomplete_Rides            VARCHAR(20),
    Incomplete_Rides_Reason     VARCHAR(30),
    Booking_Value               INT,
    Revenue                     INT,
    Payment_Method              VARCHAR(20),
    Ride_Distance               INT,
    Distance_Band               VARCHAR(20),
    Fare_per_km                 DECIMAL(8,2) NULL,
    Driver_Ratings              DECIMAL(2,1) NULL,
    Customer_Rating             DECIMAL(2,1) NULL,
    INDEX idx_status   (Booking_Status),
    INDEX idx_vehicle  (Vehicle_Type),
    INDEX idx_customer (Customer_ID),
    INDEX idx_payment  (Payment_Method),
    INDEX idx_date     (Booking_Date)
);

-- Update the path below to where ola_rides_clean.csv sits on your machine.
-- If you get error 1290/3948, enable local_infile:  SET GLOBAL local_infile = 1;
-- and connect with --local-infile=1 (or in Workbench: Advanced > Others: OPT_LOCAL_INFILE=1).
LOAD DATA LOCAL INFILE 'C:/ola-ride-insights/data/processed/ola_rides_clean.csv'
INTO TABLE ola_rides
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(Booking_ID, Booking_Datetime, Booking_Date, Booking_Time, Day, Day_Name, Weekday_Num, Is_Weekend, Hour,
 Time_Slot, Booking_Status, Ride_Outcome, Is_Success, Is_Canceled, Customer_ID, Vehicle_Type,
 Pickup_Location, Drop_Location, @V_TAT, @C_TAT, Canceled_Rides_by_Customer, Canceled_Rides_by_Driver,
 Incomplete_Rides, Incomplete_Rides_Reason, Booking_Value, Revenue, Payment_Method, Ride_Distance,
 Distance_Band, @Fare_per_km, @Driver_Ratings, @Customer_Rating)
SET V_TAT           = NULLIF(@V_TAT, ''),
    C_TAT           = NULLIF(@C_TAT, ''),
    Fare_per_km     = NULLIF(@Fare_per_km, ''),
    Driver_Ratings  = NULLIF(@Driver_Ratings, ''),
    Customer_Rating = NULLIF(TRIM(TRAILING '\r' FROM @Customer_Rating), '');

SELECT COUNT(*) AS rows_loaded FROM ola_rides;   -- expect 103024
