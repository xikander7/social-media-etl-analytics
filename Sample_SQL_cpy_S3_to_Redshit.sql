-- Create staging table in Redshift to load XML data 
CREATE TABLE stg_xml_data (
  id INT, 
  name VARCHAR(50),
  email VARCHAR(100),
  address VARCHAR(200)
);

-- Load data from S3 XML file into staging table
COPY stg_xml_data
FROM 's3://mybucket/data.xml' 
IAM_ROLE 'arn:aws:iam::123456789012:role/MyRedshiftRole'
FORMAT AS XML 's3://mybucket/xmlformat.cfg';

-- Check rows loaded
SELECT COUNT(*) FROM stg_xml_data;

-- Create production table 
CREATE TABLE prod_xml_data (
  id INT PRIMARY KEY, 
  name VARCHAR(50),
  email VARCHAR(100),
  address VARCHAR(200)
);

-- Insert data from staging table into production
INSERT INTO prod_xml_data 
SELECT * FROM stg_xml_data;

-- Check rows inserted
SELECT COUNT(*) FROM prod_xml_data;
