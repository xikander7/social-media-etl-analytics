"""
AWS Redshift Database Client for Social Media ETL
"""

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import logging
from typing import Optional, List, Dict
from datetime import datetime
import boto3
from io import StringIO

from ..utils.config import Config

logger = logging.getLogger(__name__)

class RedshiftClient:
    """AWS Redshift database client for data warehouse operations"""
    
    def __init__(self):
        """Initialize Redshift client"""
        self.host = Config.REDSHIFT_HOST
        self.port = Config.REDSHIFT_PORT
        self.database = Config.REDSHIFT_DATABASE
        self.user = Config.REDSHIFT_USER
        self.password = Config.REDSHIFT_PASSWORD
        
        self.engine = None
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Redshift"""
        try:
            # Create SQLAlchemy engine
            connection_string = Config.get_redshift_connection_string()
            self.engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=300
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Redshift connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redshift: {str(e)}")
            raise
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            DataFrame with query results
        """
        try:
            with self.engine.connect() as conn:
                if params:
                    result = pd.read_sql(text(query), conn, params=params)
                else:
                    result = pd.read_sql(text(query), conn)
            
            logger.info(f"Query executed successfully, returned {len(result)} rows")
            return result
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
    
    def execute_ddl(self, ddl_statement: str):
        """
        Execute DDL statement (CREATE, ALTER, DROP)
        
        Args:
            ddl_statement: DDL SQL statement
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text(ddl_statement))
                conn.commit()
            
            logger.info("DDL statement executed successfully")
            
        except Exception as e:
            logger.error(f"Error executing DDL: {str(e)}")
            raise
    
    def create_schema_if_not_exists(self, schema_name: str):
        """Create schema if it doesn't exist"""
        ddl = f"CREATE SCHEMA IF NOT EXISTS {schema_name}"
        self.execute_ddl(ddl)
    
    def create_dimension_tables(self):
        """Create dimension tables for social media data"""
        
        # User dimension table
        dim_user_ddl = """
        CREATE TABLE IF NOT EXISTS dim_user (
            user_id VARCHAR(50) PRIMARY KEY,
            username VARCHAR(100),
            display_name VARCHAR(200),
            platform VARCHAR(20) NOT NULL,
            verified BOOLEAN DEFAULT FALSE,
            followers_count INTEGER DEFAULT 0,
            following_count INTEGER DEFAULT 0,
            posts_count INTEGER DEFAULT 0,
            bio TEXT,
            location VARCHAR(200),
            website VARCHAR(500),
            created_at TIMESTAMP,
            last_updated TIMESTAMP DEFAULT GETDATE(),
            is_active BOOLEAN DEFAULT TRUE
        )
        DISTSTYLE KEY
        DISTKEY (user_id)
        SORTKEY (platform, created_at);
        """
        
        # Post dimension table
        dim_post_ddl = """
        CREATE TABLE IF NOT EXISTS dim_post (
            post_id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            platform VARCHAR(20) NOT NULL,
            post_type VARCHAR(50),
            content TEXT,
            language VARCHAR(10),
            url VARCHAR(1000),
            created_at TIMESTAMP NOT NULL,
            last_updated TIMESTAMP DEFAULT GETDATE(),
            is_deleted BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES dim_user(user_id)
        )
        DISTSTYLE KEY
        DISTKEY (user_id)
        SORTKEY (platform, created_at);
        """
        
        # Date dimension table
        dim_date_ddl = """
        CREATE TABLE IF NOT EXISTS dim_date (
            date_key INTEGER PRIMARY KEY,
            full_date DATE NOT NULL,
            year INTEGER NOT NULL,
            quarter INTEGER NOT NULL,
            month INTEGER NOT NULL,
            month_name VARCHAR(20) NOT NULL,
            day INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL,
            day_name VARCHAR(20) NOT NULL,
            week_of_year INTEGER NOT NULL,
            is_weekend BOOLEAN NOT NULL,
            is_holiday BOOLEAN DEFAULT FALSE
        )
        DISTSTYLE ALL
        SORTKEY (date_key);
        """
        
        # Execute DDL statements
        tables = [
            ("dim_user", dim_user_ddl),
            ("dim_post", dim_post_ddl),
            ("dim_date", dim_date_ddl)
        ]
        
        for table_name, ddl in tables:
            try:
                self.execute_ddl(ddl)
                logger.info(f"Created table: {table_name}")
            except Exception as e:
                logger.error(f"Error creating table {table_name}: {str(e)}")
    
    def create_fact_tables(self):
        """Create fact tables for social media data"""
        
        # Engagement fact table
        fact_engagement_ddl = """
        CREATE TABLE IF NOT EXISTS fact_engagement (
            engagement_id BIGINT IDENTITY(1,1) PRIMARY KEY,
            post_id VARCHAR(50) NOT NULL,
            user_id VARCHAR(50) NOT NULL,
            date_key INTEGER NOT NULL,
            platform VARCHAR(20) NOT NULL,
            likes_count INTEGER DEFAULT 0,
            shares_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            views_count INTEGER DEFAULT 0,
            impressions_count INTEGER DEFAULT 0,
            reach_count INTEGER DEFAULT 0,
            engagement_rate DECIMAL(5,4) DEFAULT 0.0000,
            created_at TIMESTAMP DEFAULT GETDATE(),
            updated_at TIMESTAMP DEFAULT GETDATE(),
            FOREIGN KEY (post_id) REFERENCES dim_post(post_id),
            FOREIGN KEY (user_id) REFERENCES dim_user(user_id),
            FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
        )
        DISTSTYLE KEY
        DISTKEY (user_id)
        SORTKEY (platform, date_key, created_at);
        """
        
        try:
            self.execute_ddl(fact_engagement_ddl)
            logger.info("Created table: fact_engagement")
        except Exception as e:
            logger.error(f"Error creating fact_engagement table: {str(e)}")
    
    def load_data_from_s3(self, table_name: str, s3_path: str, 
                         iam_role: str, file_format: str = 'JSON') -> bool:
        """
        Load data from S3 into Redshift table using COPY command
        
        Args:
            table_name: Target table name
            s3_path: S3 path to data files
            iam_role: IAM role ARN for Redshift
            file_format: File format (JSON, CSV, PARQUET)
            
        Returns:
            Boolean indicating success
        """
        try:
            if file_format.upper() == 'JSON':
                copy_command = f"""
                COPY {table_name}
                FROM '{s3_path}'
                IAM_ROLE '{iam_role}'
                FORMAT AS JSON 'auto'
                TIMEFORMAT 'auto'
                TRUNCATECOLUMNS;
                """
            elif file_format.upper() == 'CSV':
                copy_command = f"""
                COPY {table_name}
                FROM '{s3_path}'
                IAM_ROLE '{iam_role}'
                FORMAT AS CSV
                DELIMITER ','
                IGNOREHEADER 1
                TRUNCATECOLUMNS;
                """
            elif file_format.upper() == 'PARQUET':
                copy_command = f"""
                COPY {table_name}
                FROM '{s3_path}'
                IAM_ROLE '{iam_role}'
                FORMAT AS PARQUET;
                """
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            self.execute_ddl(copy_command)
            logger.info(f"Successfully loaded data from {s3_path} to {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data from S3: {str(e)}")
            return False
    
    def upsert_dataframe(self, df: pd.DataFrame, table_name: str, 
                        primary_key: str, staging_table: Optional[str] = None):
        """
        Upsert DataFrame into Redshift table
        
        Args:
            df: DataFrame to upsert
            table_name: Target table name
            primary_key: Primary key column for upsert
            staging_table: Optional staging table name
        """
        if staging_table is None:
            staging_table = f"{table_name}_staging"
        
        try:
            # Create staging table
            create_staging_ddl = f"""
            CREATE TEMP TABLE {staging_table} 
            (LIKE {table_name} INCLUDING DEFAULTS);
            """
            self.execute_ddl(create_staging_ddl)
            
            # Load data into staging table
            df.to_sql(staging_table, self.engine, if_exists='append', index=False)
            
            # Upsert from staging to target
            upsert_sql = f"""
            BEGIN TRANSACTION;
            
            DELETE FROM {table_name}
            USING {staging_table}
            WHERE {table_name}.{primary_key} = {staging_table}.{primary_key};
            
            INSERT INTO {table_name}
            SELECT * FROM {staging_table};
            
            DROP TABLE {staging_table};
            
            END TRANSACTION;
            """
            
            self.execute_ddl(upsert_sql)
            logger.info(f"Successfully upserted {len(df)} records to {table_name}")
            
        except Exception as e:
            logger.error(f"Error upserting data: {str(e)}")
            raise
    
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """Get table column information"""
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = :table_name
        ORDER BY ordinal_position
        """
        return self.execute_query(query, {"table_name": table_name})
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
        logger.info("Redshift connection closed")