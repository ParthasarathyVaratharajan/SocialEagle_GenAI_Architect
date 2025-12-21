--Create the Top10Customers view.
CREATE VIEW [dbo].[Top10Customers]
AS
SELECT TOP(10)
    FS.[CustomerKey],
    DC.[Customer],
    SUM(FS.[TotalIncludingTax]) AS [TotalSalesAmount]
FROM
    [dbo].[dimention_customer] AS DC
    INNER JOIN [dbo].[fact_sale] AS FS
        ON DC.[CustomerKey] = FS.[CustomerKey]
GROUP BY
    FS.[CustomerKey],
    DC.[Customer]
ORDER BY
    [TotalSalesAmount] DESC;

 UPDATE [dbo].[fact_sale]
 SET [TotalIncludingTax] = 200000000
 WHERE [SaleKey] = 22632918; --For customer 'Tailspin Toys (Muir, MI)'
 GO

 --Retrieve the current (UTC) timestamp.
 SELECT CURRENT_TIMESTAMP;