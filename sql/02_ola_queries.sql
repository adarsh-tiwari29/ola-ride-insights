-- =====================================================================
-- Ola Ride Insights - SQL questions (brief Q1-Q10) + extra insight queries
-- Table : ola_rides  (one row per booking, July 2024, 103,024 rows)
-- Works on MySQL 8 and SQLite (the Streamlit app runs this exact file).
-- Each query starts with a "-- @Qn | title" line - the app uses it as the label.
-- =====================================================================


-- @Q1 | Retrieve all successful bookings
SELECT *
FROM ola_rides
WHERE Booking_Status = 'Success';


-- @Q2 | Average ride distance for each vehicle type
-- Cancelled / not-found bookings are stored with distance 0, so both views are shown:
-- all bookings (matches a plain AVG on the raw sheet) and successful rides only (actual trip length).
SELECT Vehicle_Type,
       ROUND(AVG(Ride_Distance), 2)                                             AS Avg_Distance_All_Bookings,
       ROUND(AVG(CASE WHEN Booking_Status = 'Success' THEN Ride_Distance END), 2) AS Avg_Distance_Successful_Rides
FROM ola_rides
GROUP BY Vehicle_Type
ORDER BY Avg_Distance_All_Bookings DESC;


-- @Q3 | Total number of rides cancelled by customers
SELECT COUNT(*) AS Total_Canceled_by_Customer
FROM ola_rides
WHERE Booking_Status = 'Canceled by Customer';


-- @Q4 | Top 5 customers who booked the highest number of rides
SELECT Customer_ID,
       COUNT(Booking_ID) AS Total_Rides
FROM ola_rides
GROUP BY Customer_ID
ORDER BY Total_Rides DESC, Customer_ID
LIMIT 5;


-- @Q5 | Rides cancelled by drivers due to personal and car-related issues
SELECT COUNT(*) AS Canceled_Personal_Car_Issue
FROM ola_rides
WHERE Booking_Status = 'Canceled by Driver'
  AND Canceled_Rides_by_Driver = 'Personal & Car related issue';


-- @Q6 | Maximum and minimum driver ratings for Prime Sedan bookings
SELECT MAX(Driver_Ratings) AS Max_Driver_Rating,
       MIN(Driver_Ratings) AS Min_Driver_Rating
FROM ola_rides
WHERE Vehicle_Type = 'Prime Sedan'
  AND Driver_Ratings IS NOT NULL;


-- @Q7 | All rides where payment was made using UPI
SELECT *
FROM ola_rides
WHERE Payment_Method = 'UPI';


-- @Q8 | Average customer rating per vehicle type
SELECT Vehicle_Type,
       ROUND(AVG(Customer_Rating), 2) AS Avg_Customer_Rating
FROM ola_rides
WHERE Customer_Rating IS NOT NULL
GROUP BY Vehicle_Type
ORDER BY Avg_Customer_Rating DESC;


-- @Q9 | Total booking value of rides completed successfully
SELECT SUM(Booking_Value) AS Total_Successful_Booking_Value
FROM ola_rides
WHERE Booking_Status = 'Success';


-- @Q10 | All incomplete rides along with the reason
SELECT Booking_ID, Booking_Datetime, Customer_ID, Vehicle_Type,
       Pickup_Location, Drop_Location, Incomplete_Rides_Reason
FROM ola_rides
WHERE Incomplete_Rides = 'Yes'
ORDER BY Booking_Datetime;


-- =====================================================================
-- Extra insight queries (business use cases)
-- =====================================================================

-- @X1 | Booking status breakdown with share of total
SELECT Booking_Status,
       COUNT(*)                                                      AS Rides,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM ola_rides), 2) AS Pct_of_Total
FROM ola_rides
GROUP BY Booking_Status
ORDER BY Rides DESC;


-- @X2 | Peak demand hours (all bookings vs successful)
SELECT Hour,
       COUNT(*)                                     AS Bookings,
       SUM(Is_Success)                              AS Successful,
       ROUND(100.0 * SUM(Is_Success) / COUNT(*), 2) AS Success_Rate_Pct
FROM ola_rides
GROUP BY Hour
ORDER BY Bookings DESC;


-- @X3 | Revenue by payment method (successful rides)
SELECT Payment_Method,
       COUNT(*)                   AS Rides,
       SUM(Booking_Value)         AS Revenue,
       ROUND(AVG(Booking_Value),2) AS Avg_Fare
FROM ola_rides
WHERE Booking_Status = 'Success'
GROUP BY Payment_Method
ORDER BY Revenue DESC;


-- @X4 | Top 5 customers by total booking value (successful rides)
SELECT Customer_ID,
       COUNT(*)           AS Rides,
       SUM(Booking_Value) AS Total_Booking_Value
FROM ola_rides
WHERE Booking_Status = 'Success'
GROUP BY Customer_ID
ORDER BY Total_Booking_Value DESC
LIMIT 5;


-- @X5 | Vehicle type scorecard (matches the Power BI Vehicle Type page)
SELECT Vehicle_Type,
       SUM(Booking_Value)                                                       AS Total_Booking_Value,
       SUM(CASE WHEN Booking_Status = 'Success' THEN Booking_Value ELSE 0 END)    AS Success_Booking_Value,
       ROUND(AVG(CASE WHEN Booking_Status = 'Success' THEN Ride_Distance END), 2) AS Avg_Distance_Travelled,
       SUM(CASE WHEN Booking_Status = 'Success' THEN Ride_Distance ELSE 0 END)    AS Total_Distance_Travelled
FROM ola_rides
GROUP BY Vehicle_Type
ORDER BY Total_Booking_Value DESC;


-- @X6 | Cancellation reasons - customer side
SELECT Canceled_Rides_by_Customer AS Reason,
       COUNT(*)                   AS Rides
FROM ola_rides
WHERE Booking_Status = 'Canceled by Customer'
GROUP BY Canceled_Rides_by_Customer
ORDER BY Rides DESC;


-- @X7 | Cancellation reasons - driver side
SELECT Canceled_Rides_by_Driver AS Reason,
       COUNT(*)                 AS Rides
FROM ola_rides
WHERE Booking_Status = 'Canceled by Driver'
GROUP BY Canceled_Rides_by_Driver
ORDER BY Rides DESC;


-- @X8 | Pickup locations with the highest cancellation rate (min 1,000 bookings)
SELECT Pickup_Location,
       COUNT(*)                                       AS Bookings,
       SUM(Is_Canceled)                               AS Canceled,
       ROUND(100.0 * SUM(Is_Canceled) / COUNT(*), 2)  AS Cancel_Rate_Pct
FROM ola_rides
GROUP BY Pickup_Location
HAVING COUNT(*) >= 1000
ORDER BY Cancel_Rate_Pct DESC
LIMIT 10;


-- @X9 | Anomaly check - successful rides with fare per km above Rs 640 (top 1%)
-- Median fare/km is ~Rs 20; these are short trips billed like long ones -> pricing/fraud review list.
SELECT Booking_ID, Vehicle_Type, Ride_Distance, Booking_Value, Fare_per_km
FROM ola_rides
WHERE Booking_Status = 'Success'
  AND Fare_per_km >= 640
ORDER BY Fare_per_km DESC
LIMIT 50;


-- @X10 | Daily ride volume and revenue
SELECT Booking_Date,
       COUNT(*)        AS Bookings,
       SUM(Is_Success) AS Successful_Rides,
       SUM(Revenue)    AS Revenue
FROM ola_rides
GROUP BY Booking_Date
ORDER BY Booking_Date;
