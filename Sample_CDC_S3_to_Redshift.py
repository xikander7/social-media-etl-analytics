from informatica import CloudIntegration, Connector 

# Source from S3
s3_source = CloudIntegration.Source('S3 Source')
s3_source.connector = Connector.S3()
s3_source.connector.bucket = 'mybucket'
s3_source.connector.key = 'data.csv'

# Target for Redshift staging
rs_staging = CloudIntegration.Target('Redshift Staging')
rs_staging.connector = Connector.Redshift()
rs_staging.connector.username = 'username'
rs_staging.connector.password = 'password'
rs_staging.connector.database = 'dev'
rs_staging.connector.table = 'stg_table'

# Load from S3 into Redshift staging
load_to_staging = CloudIntegration.Mapping(s3_source, rs_staging)

# Target for Redshift base table 
rs_base = CloudIntegration.Target('Redshift Base')
rs_base.connector = Connector.Redshift()  
rs_base.connector.table = 'base_table'

# Incremental load from staging into base
cdc_to_base = CloudIntegration.Mapping(rs_staging, rs_base)
cdc_to_base.cdc_enabled = True
cdc_to_base.audit_fields = ['updated_at']

# Pipeline
pipe = CloudIntegration.Pipeline()
pipe.deploy(load_to_staging)
pipe.deploy(cdc_to_base)

pipe.run()
