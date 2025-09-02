"""
Facebook API Client for Social Media ETL
"""

import requests
import pandas as pd
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time

from ..utils.config import Config

logger = logging.getLogger(__name__)

class FacebookClient:
    """Facebook Graph API client for extracting social media data"""
    
    def __init__(self):
        """Initialize Facebook API client"""
        self.app_id = Config.FACEBOOK_APP_ID
        self.app_secret = Config.FACEBOOK_APP_SECRET
        self.access_token = Config.FACEBOOK_ACCESS_TOKEN
        self.base_url = "https://graph.facebook.com/v18.0"
        
        self._validate_credentials()
    
    def _validate_credentials(self):
        """Validate Facebook API credentials"""
        if not all([self.app_id, self.app_secret, self.access_token]):
            logger.warning("Facebook API credentials not fully configured")
            return False
        
        try:
            # Test API connection
            url = f"{self.base_url}/me"
            params = {'access_token': self.access_token}
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                logger.info("Facebook API authentication successful")
                return True
            else:
                logger.error(f"Facebook API authentication failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Facebook API validation error: {str(e)}")
            return False
    
    def get_page_posts(self, page_id: str, limit: int = 100, 
                      days_back: int = 7) -> pd.DataFrame:
        """
        Get posts from a Facebook page
        
        Args:
            page_id: Facebook page ID
            limit: Maximum number of posts to retrieve
            days_back: Number of days to look back
            
        Returns:
            DataFrame with page posts data
        """
        try:
            # Calculate since parameter
            since_date = datetime.now() - timedelta(days=days_back)
            since_timestamp = int(since_date.timestamp())
            
            url = f"{self.base_url}/{page_id}/posts"
            params = {
                'access_token': self.access_token,
                'limit': min(limit, 100),  # API limit per request
                'since': since_timestamp,
                'fields': 'id,message,created_time,type,link,name,description,shares,reactions.summary(true),comments.summary(true)'
            }
            
            posts_data = []
            
            while url and len(posts_data) < limit:
                response = requests.get(url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Facebook API error: {response.text}")
                    break
                
                data = response.json()
                
                for post in data.get('data', []):
                    post_data = {
                        'post_id': post['id'],
                        'page_id': page_id,
                        'message': post.get('message', ''),
                        'created_time': post['created_time'],
                        'post_type': post.get('type', ''),
                        'link': post.get('link', ''),
                        'name': post.get('name', ''),
                        'description': post.get('description', ''),
                        'shares_count': post.get('shares', {}).get('count', 0),
                        'reactions_count': post.get('reactions', {}).get('summary', {}).get('total_count', 0),
                        'comments_count': post.get('comments', {}).get('summary', {}).get('total_count', 0),
                        'extracted_at': datetime.now()
                    }
                    posts_data.append(post_data)
                
                # Get next page URL
                url = data.get('paging', {}).get('next')
                params = {}  # Clear params for next request as they're in the URL
            
            df = pd.DataFrame(posts_data)
            logger.info(f"Extracted {len(df)} Facebook posts for page: {page_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting Facebook page posts: {str(e)}")
            raise
    
    def get_page_insights(self, page_id: str, metrics: List[str] = None) -> pd.DataFrame:
        """
        Get insights/analytics for a Facebook page
        
        Args:
            page_id: Facebook page ID
            metrics: List of metrics to retrieve
            
        Returns:
            DataFrame with page insights
        """
        if metrics is None:
            metrics = [
                'page_fans',
                'page_impressions',
                'page_engagements',
                'page_posts_impressions',
                'page_video_views'
            ]
        
        try:
            url = f"{self.base_url}/{page_id}/insights"
            params = {
                'access_token': self.access_token,
                'metric': ','.join(metrics),
                'period': 'day',
                'since': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'until': datetime.now().strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"Facebook Insights API error: {response.text}")
                return pd.DataFrame()
            
            data = response.json()
            insights_data = []
            
            for metric_data in data.get('data', []):
                metric_name = metric_data['name']
                for value_data in metric_data.get('values', []):
                    insights_data.append({
                        'page_id': page_id,
                        'metric_name': metric_name,
                        'date': value_data['end_time'][:10],  # Extract date part
                        'value': value_data['value'],
                        'extracted_at': datetime.now()
                    })
            
            df = pd.DataFrame(insights_data)
            logger.info(f"Extracted {len(df)} Facebook insights for page: {page_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting Facebook page insights: {str(e)}")
            raise
    
    def search_pages(self, query: str, limit: int = 50) -> pd.DataFrame:
        """
        Search for Facebook pages
        
        Args:
            query: Search query
            limit: Maximum number of pages to return
            
        Returns:
            DataFrame with page information
        """
        try:
            url = f"{self.base_url}/search"
            params = {
                'access_token': self.access_token,
                'q': query,
                'type': 'page',
                'limit': limit,
                'fields': 'id,name,category,about,website,fan_count,talking_about_count'
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"Facebook Search API error: {response.text}")
                return pd.DataFrame()
            
            data = response.json()
            pages_data = []
            
            for page in data.get('data', []):
                page_data = {
                    'page_id': page['id'],
                    'name': page['name'],
                    'category': page.get('category', ''),
                    'about': page.get('about', ''),
                    'website': page.get('website', ''),
                    'fan_count': page.get('fan_count', 0),
                    'talking_about_count': page.get('talking_about_count', 0),
                    'extracted_at': datetime.now()
                }
                pages_data.append(page_data)
            
            df = pd.DataFrame(pages_data)
            logger.info(f"Found {len(df)} Facebook pages for query: {query}")
            return df
            
        except Exception as e:
            logger.error(f"Error searching Facebook pages: {str(e)}")
            raise
    
    def save_to_json(self, data: pd.DataFrame, filename: str) -> str:
        """Save data to JSON file"""
        filepath = Config.RAW_DATA_DIR / f"facebook_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        data.to_json(filepath, orient='records', date_format='iso')
        logger.info(f"Data saved to {filepath}")
        return str(filepath)