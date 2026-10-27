SELECT
    ProductName,
    SUM(Quantity) AS TotalUnitsSold,
    ROUND(SUM(NetSales), 2) AS TotalRevenue,
    ROUND(SUM(Profit), 2) AS TotalProfit
FROM retail_sales
GROUP BY ProductName
ORDER BY TotalProfit ASC
LIMIT 10;