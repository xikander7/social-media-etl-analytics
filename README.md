# Social Media ETL Analytics

A comprehensive data engineering project that extracts, transforms, and analyzes social media data from multiple platforms including Twitter, Facebook, and Instagram. The pipeline implements modern ETL practices with cloud integration, data warehousing, and interactive analytics dashboards.

## Project Overview

This project builds a scalable ETL pipeline to:
- Extract social media data from APIs (Twitter, Facebook, Instagram)
- Clean, transform, and normalize data into analytics-ready format
- Load data into AWS Redshift data warehouse using star schema design
- Generate interactive dashboards and business insights
- Provide automated monitoring and notification capabilities

## Architecture

### Data Flow
1. **Extraction**: Social media APIs → Raw JSON files → AWS S3 staging
2. **Transformation**: Data cleaning, sentiment analysis, feature engineering
3. **Loading**: Dimensional modeling → AWS Redshift data warehouse
4. **Analytics**: Interactive dashboards and summary reports

### Technology Stack
- **Language**: Python 3.8+
- **APIs**: Twitter API v2, Facebook Graph API, Instagram Basic Display API
- **Cloud Storage**: AWS S3 for data staging
- **Data Warehouse**: AWS Redshift with star schema design
- **Orchestration**: Custom Python pipeline with logging and monitoring
- **Visualization**: Plotly, Matplotlib, Seaborn for interactive dashboards
- **Environment**: Docker support, virtual environment management

## Repository Structure

```
social-media-etl-analytics/
├── src/
│   ├── api_clients/           # API integration modules
│   │   ├── twitter_client.py  # Twitter API client
│   │   ├── facebook_client.py # Facebook API client
│   │   └── instagram_client.py# Instagram API client
│   ├── etl/                   # ETL pipeline components
│   │   ├── extract.py         # Data extraction logic
│   │   ├── transform.py       # Data transformation and cleaning
│   │   └── load.py            # Data loading to warehouse
│   ├── database/              # Database connectivity
│   │   └── redshift_client.py # AWS Redshift operations
│   ├── visualization/         # Dashboard generation
│   │   └── dashboard.py       # Interactive dashboard creation
│   └── utils/                 # Utility functions
│       ├── config.py          # Configuration management
│       └── notification.py    # Pipeline notifications
├── data/
│   ├── raw/                   # Raw extracted data
│   ├── processed/             # Transformed data
│   └── staging/               # Intermediate processing files
├── config/                    # Configuration files
├── tests/                     # Unit and integration tests
├── scripts/                   # Utility scripts
├── reports/                   # Generated reports and dashboards
│   └── figures/               # Dashboard visualizations
├── docs/                      # Project documentation
├── notebooks/                 # Jupyter analysis notebooks
├── main.py                    # Main pipeline orchestrator
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Quick Start

### Prerequisites
- Python 3.8 or higher
- AWS account with S3 and Redshift access
- Social media API credentials (Twitter, Facebook, Instagram)
- pip package manager

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/xikander7/social-media-etl-analytics.git
   cd social-media-etl-analytics
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials and AWS settings
   ```

### Configuration

Edit the `.env` file with your credentials:

```bash
# Twitter API
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# Facebook API
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_access_token

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your-s3-bucket
AWS_DEFAULT_REGION=us-east-1

# Redshift Database
REDSHIFT_HOST=your-cluster.redshift.amazonaws.com
REDSHIFT_DATABASE=social_media_db
REDSHIFT_USER=your_username
REDSHIFT_PASSWORD=your_password
```

### Usage

#### Run Complete Pipeline
```bash
python main.py
```

#### Run Specific Components
```bash
# Extract data only
python main.py --phase extract

# Run with custom configuration
python main.py --config config/custom_extraction.yml

# Set logging level
python main.py --log-level DEBUG
```

#### Quick Start Script
```bash
python scripts/run_pipeline.py
```

## Data Model

The pipeline implements a star schema design optimized for analytics:

### Dimension Tables
- **dim_user**: User profiles across platforms (user_id, username, platform, verified, followers_count, bio, location)
- **dim_post**: Social media posts (post_id, user_id, platform, content, created_at, post_type, language, sentiment)
- **dim_date**: Date dimension for time-based analysis (date_key, year, quarter, month, week, is_weekend)

### Fact Tables  
- **fact_engagement**: Engagement metrics (post_id, user_id, date_key, platform, likes_count, shares_count, comments_count, engagement_rate)

### Key Relationships
- Users (1:M) Posts: Each user can have multiple posts
- Posts (1:M) Engagement: Each post has engagement metrics over time
- Date (1:M) Engagement: Time-based analysis of engagement patterns

## Features

### Data Extraction
- **Multi-platform support**: Twitter, Facebook, Instagram APIs
- **Parallel processing**: Concurrent extraction from multiple sources
- **Rate limiting**: Built-in API rate limit handling and retry logic
- **Data validation**: Schema validation and quality checks
- **Incremental loading**: Support for incremental data updates

### Data Transformation
- **Text processing**: Content cleaning, hashtag/mention extraction
- **Sentiment analysis**: Automated sentiment scoring using TextBlob
- **Feature engineering**: Engagement metrics, temporal features
- **Data normalization**: Consistent schema across platforms
- **Quality monitoring**: Data quality validation and alerts

### Data Loading
- **Star schema**: Optimized dimensional model for analytics
- **Upsert operations**: Merge new data with existing records
- **Batch processing**: Efficient bulk loading to Redshift
- **Error handling**: Comprehensive error logging and recovery
- **Performance optimization**: Query optimization and indexing

### Analytics & Visualization
- **Interactive dashboards**: Plotly-based web dashboards
- **Platform comparison**: Cross-platform analytics and benchmarking
- **Sentiment analysis**: Sentiment trends and distribution analysis  
- **Engagement insights**: Performance metrics and trending content
- **Automated reporting**: Scheduled report generation

### Monitoring & Operations
- **Pipeline logging**: Comprehensive logging with configurable levels
- **Performance monitoring**: Execution time and resource usage tracking
- **Error notifications**: Email alerts for pipeline failures
- **Data quality alerts**: Automated data quality issue detection
- **Health checks**: System status monitoring and diagnostics

## Generated Outputs

### Data Files
- **Raw data**: JSON files in `data/raw/` with timestamp-based naming
- **Processed data**: Parquet files in `data/processed/` for each dimension/fact table
- **Archive data**: Historical data retention with configurable policies

### Dashboards
- **Engagement Analytics**: Platform performance and trending content analysis
- **Sentiment Analysis**: Content sentiment distribution and trends over time
- **Platform Comparison**: Cross-platform metrics and benchmarking analysis
- **Summary Reports**: Executive-level KPI dashboards and insights

### Reports
- **Pipeline Summary**: Execution statistics and data processing metrics
- **Data Quality Report**: Data validation results and quality indicators
- **Performance Analytics**: System performance and optimization recommendations

## API Credentials Setup

### Twitter API (Required)
1. Create Twitter Developer Account at https://developer.twitter.com
2. Create new app and generate API keys
3. Add credentials to `.env` file

### Facebook API (Optional)
1. Create Facebook Developer Account at https://developers.facebook.com
2. Create new app and configure permissions
3. Generate access tokens with appropriate scopes
4. Add credentials to `.env` file

### Instagram API (Optional)  
1. Use Facebook Developer Console (Instagram Basic Display)
2. Configure Instagram Basic Display product
3. Generate access tokens and add to `.env`

## AWS Setup

### S3 Configuration
1. Create S3 bucket for data staging
2. Configure IAM role with S3 read/write permissions
3. Update bucket name in `.env` file

### Redshift Configuration  
1. Create Redshift cluster (recommended: dc2.large for development)
2. Configure security groups and network access
3. Create database and user account
4. Update connection details in `.env` file

## Performance Considerations

### Scalability
- **Horizontal scaling**: Multi-processing support for large datasets
- **Cloud integration**: AWS S3/Redshift for enterprise-scale storage
- **Memory optimization**: Streaming data processing for large files
- **Batch sizing**: Configurable batch sizes for optimal performance

### Cost Optimization
- **API usage**: Efficient API calls with caching and rate limiting
- **Storage costs**: Data lifecycle policies and archival strategies  
- **Compute costs**: Right-sizing recommendations for AWS resources
- **Monitoring**: Usage tracking and cost alerts

## Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests  
```bash
pytest tests/integration/
```

### End-to-End Tests
```bash
pytest tests/e2e/
```

### Data Quality Tests
```bash
python -m pytest tests/data_quality/
```

## Troubleshooting

### Common Issues

**API Authentication Errors**
- Verify API credentials in `.env` file
- Check token expiration dates
- Validate API permissions and scopes

**Database Connection Issues**
- Verify Redshift cluster status and connectivity
- Check security group configurations
- Validate database credentials and permissions

**Memory/Performance Issues**  
- Adjust batch sizes in configuration
- Monitor system resource usage
- Consider upgrading hardware specifications

**Data Quality Issues**
- Review data validation rules
- Check API response format changes
- Validate transformation logic

### Logging and Debugging
- Pipeline logs available in `logs/` directory
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Error notifications via email/console output
- Performance metrics tracking

## Development

### Adding New Platforms
1. Create new API client in `src/api_clients/`
2. Implement extraction logic in `src/etl/extract.py`
3. Add transformation rules in `src/etl/transform.py`
4. Update configuration and documentation

### Extending Analytics
1. Add new dashboard types in `src/visualization/dashboard.py`
2. Create custom analysis notebooks in `notebooks/`
3. Implement new metrics in transformation logic
4. Update reporting templates

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

**Syed Shah**  
Data Engineer  
Email: syedxanshah@gmail.com

For questions, issues, or collaboration opportunities, please reach out via email or create an issue in the repository.

## Development Tools

This project was developed using professional development tools and methodologies:

**Development Environment:**
- **Primary Language**: Python 3.8+ with modern data engineering libraries
- **IDE**: Visual Studio Code with Python extensions and linting
- **Version Control**: Git with conventional commit messages and branch management
- **Package Management**: pip with pinned dependencies for reproducibility
- **Documentation**: Comprehensive inline documentation and README files

**Quality Assurance:**
- **Code Structure**: Modular design with separation of concerns
- **Error Handling**: Comprehensive exception handling and logging
- **Testing Framework**: pytest for unit, integration, and end-to-end testing
- **Data Validation**: Automated data quality checks and monitoring
- **Performance Monitoring**: Execution metrics and resource usage tracking

The implementation follows industry best practices for data engineering pipelines, ensuring maintainability, scalability, and reliability in production environments.