--Copy data from the public Azure storage account to the dimension_city table.
 COPY INTO [dbo].[dimension_city]
 FROM 'https://fabrictutorialdata.blob.core.windows.net/sampledata/WideWorldImportersDW/tables/dimension_city.parquet'
 WITH (FILE_TYPE = 'PARQUET');

 --Copy data from the public Azure storage account to the fact_sale table.
 COPY INTO [dbo].[fact_sale]
 FROM 'https://fabrictutorialdata.blob.core.windows.net/sampledata/WideWorldImportersDW/tables/fact_sale.parquet'
 WITH (FILE_TYPE = 'PARQUET');