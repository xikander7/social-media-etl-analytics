"""
Twitter API Client for Social Media ETL
"""

import tweepy
import pandas as pd
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
import json

from ..utils.config import Config

logger = logging.getLogger(__name__)

class TwitterClient:
    """Twitter API client for extracting social media data"""
    
    def __init__(self):
        """Initialize Twitter API client"""
        self.api_key = Config.TWITTER_API_KEY
        self.api_secret = Config.TWITTER_API_SECRET
        self.access_token = Config.TWITTER_ACCESS_TOKEN
        self.access_token_secret = Config.TWITTER_ACCESS_TOKEN_SECRET
        self.bearer_token = Config.TWITTER_BEARER_TOKEN
        
        self.client = None
        self.api = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Twitter API"""
        try:
            # Initialize Twitter API v2 client
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            
            # Initialize Twitter API v1.1 for additional features
            auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
            auth.set_access_token(self.access_token, self.access_token_secret)
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            logger.info("Twitter API authentication successful")
        except Exception as e:
            logger.error(f"Twitter API authentication failed: {str(e)}")
            raise
    
    def search_tweets(self, query: str, max_results: int = 100, 
                     days_back: int = 7) -> pd.DataFrame:
        """
        Search for tweets based on query
        
        Args:
            query: Search query string
            max_results: Maximum number of tweets to retrieve
            days_back: Number of days to look back
            
        Returns:
            DataFrame with tweet data
        """
        try:
            # Calculate start time
            start_time = datetime.now() - timedelta(days=days_back)
            
            # Tweet fields to include
            tweet_fields = [
                'id', 'text', 'author_id', 'created_at', 'public_metrics',
                'context_annotations', 'entities', 'geo', 'lang', 'source'
            ]
            
            user_fields = ['id', 'username', 'name', 'verified', 'public_metrics']
            
            tweets_data = []
            
            # Search tweets using API v2
            tweets = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                tweet_fields=tweet_fields,
                user_fields=user_fields,
                expansions='author_id',
                start_time=start_time,
                max_results=min(max_results, 100)  # API limit per request
            ).flatten(limit=max_results)
            
            for tweet in tweets:
                tweet_data = {
                    'tweet_id': tweet.id,
                    'text': tweet.text,
                    'author_id': tweet.author_id,
                    'created_at': tweet.created_at,
                    'retweet_count': tweet.public_metrics.get('retweet_count', 0),
                    'like_count': tweet.public_metrics.get('like_count', 0),
                    'reply_count': tweet.public_metrics.get('reply_count', 0),
                    'quote_count': tweet.public_metrics.get('quote_count', 0),
                    'language': tweet.lang,
                    'source': tweet.source,
                    'extracted_at': datetime.now()
                }
                tweets_data.append(tweet_data)
            
            df = pd.DataFrame(tweets_data)
            logger.info(f"Extracted {len(df)} tweets for query: {query}")
            return df
            
        except Exception as e:
            logger.error(f"Error searching tweets: {str(e)}")
            raise
    
    def get_user_tweets(self, username: str, max_results: int = 100) -> pd.DataFrame:
        """
        Get tweets from a specific user
        
        Args:
            username: Twitter username (without @)
            max_results: Maximum number of tweets to retrieve
            
        Returns:
            DataFrame with user's tweets
        """
        try:
            # Get user by username
            user = self.client.get_user(username=username)
            if not user.data:
                raise ValueError(f"User {username} not found")
            
            user_id = user.data.id
            
            # Get user's tweets
            tweets = tweepy.Paginator(
                self.client.get_users_tweets,
                id=user_id,
                tweet_fields=['created_at', 'public_metrics', 'lang'],
                max_results=100
            ).flatten(limit=max_results)
            
            tweets_data = []
            for tweet in tweets:
                tweet_data = {
                    'tweet_id': tweet.id,
                    'user_id': user_id,
                    'username': username,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'retweet_count': tweet.public_metrics.get('retweet_count', 0),
                    'like_count': tweet.public_metrics.get('like_count', 0),
                    'reply_count': tweet.public_metrics.get('reply_count', 0),
                    'quote_count': tweet.public_metrics.get('quote_count', 0),
                    'language': tweet.lang,
                    'extracted_at': datetime.now()
                }
                tweets_data.append(tweet_data)
            
            df = pd.DataFrame(tweets_data)
            logger.info(f"Extracted {len(df)} tweets for user: {username}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting user tweets: {str(e)}")
            raise
    
    def get_trending_topics(self, location_id: int = 1) -> List[Dict]:
        """
        Get trending topics for a location
        
        Args:
            location_id: WOEID for location (1 = worldwide)
            
        Returns:
            List of trending topics
        """
        try:
            trends = self.api.get_place_trends(location_id)
            trending_topics = []
            
            for trend in trends[0]['trends']:
                trending_topics.append({
                    'name': trend['name'],
                    'url': trend['url'],
                    'promoted_content': trend['promoted_content'],
                    'query': trend['query'],
                    'tweet_volume': trend['tweet_volume'],
                    'extracted_at': datetime.now(),
                    'location_id': location_id
                })
            
            logger.info(f"Extracted {len(trending_topics)} trending topics")
            return trending_topics
            
        except Exception as e:
            logger.error(f"Error getting trending topics: {str(e)}")
            raise
    
    def save_to_json(self, data: pd.DataFrame, filename: str) -> str:
        """Save data to JSON file"""
        filepath = Config.RAW_DATA_DIR / f"twitter_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        data.to_json(filepath, orient='records', date_format='iso')
        logger.info(f"Data saved to {filepath}")
        return str(filepath)