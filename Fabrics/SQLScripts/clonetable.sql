--Create a clone of the dbo.dimension_city table.
 CREATE TABLE [dbo].[dimension_city1] AS CLONE OF [dbo].[dimension_city];

 --Create a clone of the dbo.fact_sale table.
 CREATE TABLE [dbo].[fact_sale1] AS CLONE OF [dbo].[fact_sale];


 --Create a clone of the dbo.dimension_city table at a specific point in time.   
CREATE TABLE [dbo].[dimension_city2] AS CLONE OF [dbo].[dimension_city] AT '2025-01-01T10:00:00.000';

 --Create a clone of the dbo.fact_sale table at a specific point in time.
CREATE TABLE [dbo].[fact_sale2] AS CLONE OF [dbo].[fact_sale] AT '2025-01-01T10:00:00.000';