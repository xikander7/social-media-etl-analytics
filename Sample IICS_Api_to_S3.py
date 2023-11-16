# Import Informatica libraries
from informatica import CloudIntegration, Connector

# Create source for Twitter API
twitter = CloudIntegration.Source('Twitter') 

# Configure Twitter API connection
twitter.connector = Connector.Twitter()
twitter.connector.endpoint = 'https://api.twitter.com'
twitter.connector.auth_type = 'OAuth'
twitter.connector.consumer_key = '$TWITTER_CONSUMER_KEY'
twitter.connector.consumer_secret = '$TWITTER_CONSUMER_SECRET' 
twitter.connector.access_token = '$TWITTER_ACCESS_TOKEN'
twitter.connector.access_token_secret = '$TWITTER_ACCESS_TOKEN_SECRET'

# Set up resource and parameters
twitter.resource = '/2/tweets/search/recent'
twitter.params['query'] = 'source=Informatica' 
twitter.params['max_results'] = 100

# Create S3 target 
s3 = CloudIntegration.Target('S3 Target')
s3.connector = Connector.S3() 
s3.connector.bucket = '$S3_BUCKET_NAME'
s3.connector.key = 'twitter_data'
s3.connector.format = 'json'

# Create mapping between source and target
mapping = CloudIntegration.Mapping(twitter, s3)

# Execute pipeline 
pipeline = CloudIntegration.Pipeline()
pipeline.deploy(mapping)
pipeline.run()
