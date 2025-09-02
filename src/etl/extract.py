"""
Data Extraction Module for Social Media ETL Pipeline
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import concurrent.futures
from pathlib import Path

from ..api_clients.twitter_client import TwitterClient
from ..api_clients.facebook_client import FacebookClient
from ..utils.config import Config

logger = logging.getLogger(__name__)

class DataExtractor:
    """Main class for extracting data from social media APIs"""
    
    def __init__(self):
        """Initialize data extractor with API clients"""
        self.twitter_client = None
        self.facebook_client = None
        
        # Initialize clients if credentials are available
        try:
            if Config.TWITTER_API_KEY:
                self.twitter_client = TwitterClient()
                logger.info("Twitter client initialized")
        except Exception as e:
            logger.warning(f"Twitter client initialization failed: {str(e)}")
        
        try:
            if Config.FACEBOOK_APP_ID:
                self.facebook_client = FacebookClient()
                logger.info("Facebook client initialized")
        except Exception as e:
            logger.warning(f"Facebook client initialization failed: {str(e)}")
    
    def extract_twitter_data(self, config: Dict) -> Dict[str, pd.DataFrame]:
        """
        Extract data from Twitter API
        
        Args:
            config: Extraction configuration
            
        Returns:
            Dictionary of DataFrames with extracted data
        """
        results = {}
        
        if not self.twitter_client:
            logger.warning("Twitter client not available, skipping Twitter extraction")
            return results
        
        try:
            # Extract tweets by search queries
            if 'search_queries' in config:
                all_tweets = []
                for query in config['search_queries']:
                    tweets_df = self.twitter_client.search_tweets(
                        query=query,
                        max_results=config.get('max_results', 100),
                        days_back=config.get('days_back', 7)
                    )
                    tweets_df['search_query'] = query
                    all_tweets.append(tweets_df)
                
                if all_tweets:
                    results['twitter_tweets'] = pd.concat(all_tweets, ignore_index=True)
            
            # Extract user tweets
            if 'users' in config:
                all_user_tweets = []
                for username in config['users']:
                    user_tweets_df = self.twitter_client.get_user_tweets(
                        username=username,
                        max_results=config.get('user_max_results', 50)
                    )
                    all_user_tweets.append(user_tweets_df)
                
                if all_user_tweets:
                    results['twitter_user_tweets'] = pd.concat(all_user_tweets, ignore_index=True)
            
            # Extract trending topics
            if config.get('extract_trends', False):
                trends = self.twitter_client.get_trending_topics()
                results['twitter_trends'] = pd.DataFrame(trends)
            
            logger.info(f"Twitter extraction completed. Datasets: {list(results.keys())}")
            
        except Exception as e:
            logger.error(f"Error in Twitter extraction: {str(e)}")
        
        return results
    
    def extract_facebook_data(self, config: Dict) -> Dict[str, pd.DataFrame]:
        """
        Extract data from Facebook API
        
        Args:
            config: Extraction configuration
            
        Returns:
            Dictionary of DataFrames with extracted data
        """
        results = {}
        
        if not self.facebook_client:
            logger.warning("Facebook client not available, skipping Facebook extraction")
            return results
        
        try:
            # Extract page posts
            if 'page_ids' in config:
                all_posts = []
                for page_id in config['page_ids']:
                    posts_df = self.facebook_client.get_page_posts(
                        page_id=page_id,
                        limit=config.get('posts_limit', 100),
                        days_back=config.get('days_back', 7)
                    )
                    all_posts.append(posts_df)
                
                if all_posts:
                    results['facebook_posts'] = pd.concat(all_posts, ignore_index=True)
            
            # Extract page insights
            if 'insights_page_ids' in config:
                all_insights = []
                for page_id in config['insights_page_ids']:
                    insights_df = self.facebook_client.get_page_insights(
                        page_id=page_id,
                        metrics=config.get('insights_metrics')
                    )
                    all_insights.append(insights_df)
                
                if all_insights:
                    results['facebook_insights'] = pd.concat(all_insights, ignore_index=True)
            
            # Search for pages
            if 'search_queries' in config:
                all_pages = []
                for query in config['search_queries']:
                    pages_df = self.facebook_client.search_pages(
                        query=query,
                        limit=config.get('search_limit', 50)
                    )
                    pages_df['search_query'] = query
                    all_pages.append(pages_df)
                
                if all_pages:
                    results['facebook_pages'] = pd.concat(all_pages, ignore_index=True)
            
            logger.info(f"Facebook extraction completed. Datasets: {list(results.keys())}")
            
        except Exception as e:
            logger.error(f"Error in Facebook extraction: {str(e)}")
        
        return results
    
    def extract_all_platforms(self, extraction_config: Dict) -> Dict[str, pd.DataFrame]:
        """
        Extract data from all configured platforms
        
        Args:
            extraction_config: Configuration for all platforms
            
        Returns:
            Combined dictionary of all extracted DataFrames
        """
        all_results = {}
        
        # Parallel extraction from different platforms
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            # Submit Twitter extraction
            if 'twitter' in extraction_config:
                futures['twitter'] = executor.submit(
                    self.extract_twitter_data, 
                    extraction_config['twitter']
                )
            
            # Submit Facebook extraction
            if 'facebook' in extraction_config:
                futures['facebook'] = executor.submit(
                    self.extract_facebook_data, 
                    extraction_config['facebook']
                )
            
            # Collect results
            for platform, future in futures.items():
                try:
                    platform_results = future.result(timeout=300)  # 5 minute timeout
                    all_results.update(platform_results)
                    logger.info(f"{platform.capitalize()} extraction completed successfully")
                except Exception as e:
                    logger.error(f"Error in {platform} extraction: {str(e)}")
        
        return all_results
    
    def save_raw_data(self, data_dict: Dict[str, pd.DataFrame], 
                     file_format: str = 'json') -> Dict[str, str]:
        """
        Save extracted data to raw data directory
        
        Args:
            data_dict: Dictionary of DataFrames to save
            file_format: File format (json, csv, parquet)
            
        Returns:
            Dictionary mapping dataset names to file paths
        """
        file_paths = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Ensure raw data directory exists
        Config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        for dataset_name, df in data_dict.items():
            if df.empty:
                logger.warning(f"Dataset {dataset_name} is empty, skipping save")
                continue
            
            filename = f"{dataset_name}_{timestamp}.{file_format}"
            filepath = Config.RAW_DATA_DIR / filename
            
            try:
                if file_format.lower() == 'json':
                    df.to_json(filepath, orient='records', date_format='iso')
                elif file_format.lower() == 'csv':
                    df.to_csv(filepath, index=False)
                elif file_format.lower() == 'parquet':
                    df.to_parquet(filepath, index=False)
                else:
                    raise ValueError(f"Unsupported file format: {file_format}")
                
                file_paths[dataset_name] = str(filepath)
                logger.info(f"Saved {len(df)} records to {filepath}")
                
            except Exception as e:
                logger.error(f"Error saving {dataset_name}: {str(e)}")
        
        return file_paths
    
    def get_extraction_summary(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Generate summary of extracted data
        
        Args:
            data_dict: Dictionary of extracted DataFrames
            
        Returns:
            DataFrame with extraction summary
        """
        summary_data = []
        
        for dataset_name, df in data_dict.items():
            platform = dataset_name.split('_')[0]
            data_type = '_'.join(dataset_name.split('_')[1:])
            
            summary_data.append({
                'dataset_name': dataset_name,
                'platform': platform,
                'data_type': data_type,
                'records_count': len(df),
                'columns_count': len(df.columns) if not df.empty else 0,
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
                'extraction_time': datetime.now(),
                'has_data': not df.empty
            })
        
        return pd.DataFrame(summary_data)