"""
Data Transformation Module for Social Media ETL Pipeline
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re
import json
from textblob import TextBlob
import hashlib

from ..utils.config import Config

logger = logging.getLogger(__name__)

class DataTransformer:
    """Main class for transforming social media data"""
    
    def __init__(self):
        """Initialize data transformer"""
        self.transformation_config = self._load_transformation_config()
    
    def _load_transformation_config(self) -> Dict:
        """Load transformation configuration"""
        return {
            'text_cleaning': {
                'remove_urls': True,
                'remove_mentions': False,
                'remove_hashtags': False,
                'remove_special_chars': True,
                'normalize_whitespace': True
            },
            'sentiment_analysis': {
                'enabled': True,
                'include_subjectivity': True
            },
            'feature_engineering': {
                'extract_hashtags': True,
                'extract_mentions': True,
                'extract_urls': True,
                'calculate_engagement_rate': True
            }
        }
    
    def transform_twitter_data(self, raw_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Transform Twitter raw data into analytics-ready format
        
        Args:
            raw_data: Dictionary of raw Twitter DataFrames
            
        Returns:
            Dictionary of transformed DataFrames
        """
        transformed_data = {}
        
        # Transform tweets data
        if 'twitter_tweets' in raw_data:
            tweets_df = raw_data['twitter_tweets'].copy()
            transformed_data['dim_twitter_users'], transformed_data['dim_twitter_posts'], transformed_data['fact_twitter_engagement'] = self._transform_twitter_tweets(tweets_df)
        
        # Transform user tweets data
        if 'twitter_user_tweets' in raw_data:
            user_tweets_df = raw_data['twitter_user_tweets'].copy()
            user_dim, posts_dim, engagement_fact = self._transform_twitter_tweets(user_tweets_df, is_user_timeline=True)
            
            # Combine with existing data or create new
            if 'dim_twitter_users' in transformed_data:
                transformed_data['dim_twitter_users'] = pd.concat([transformed_data['dim_twitter_users'], user_dim]).drop_duplicates('user_id')
                transformed_data['dim_twitter_posts'] = pd.concat([transformed_data['dim_twitter_posts'], posts_dim])
                transformed_data['fact_twitter_engagement'] = pd.concat([transformed_data['fact_twitter_engagement'], engagement_fact])
            else:
                transformed_data['dim_twitter_users'] = user_dim
                transformed_data['dim_twitter_posts'] = posts_dim
                transformed_data['fact_twitter_engagement'] = engagement_fact
        
        # Transform trends data
        if 'twitter_trends' in raw_data:
            transformed_data['dim_twitter_trends'] = self._transform_twitter_trends(raw_data['twitter_trends'])
        
        logger.info(f"Twitter transformation completed. Output tables: {list(transformed_data.keys())}")
        return transformed_data
    
    def transform_facebook_data(self, raw_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Transform Facebook raw data into analytics-ready format
        
        Args:
            raw_data: Dictionary of raw Facebook DataFrames
            
        Returns:
            Dictionary of transformed DataFrames
        """
        transformed_data = {}
        
        # Transform posts data
        if 'facebook_posts' in raw_data:
            posts_df = raw_data['facebook_posts'].copy()
            transformed_data['dim_facebook_pages'], transformed_data['dim_facebook_posts'], transformed_data['fact_facebook_engagement'] = self._transform_facebook_posts(posts_df)
        
        # Transform insights data
        if 'facebook_insights' in raw_data:
            transformed_data['fact_facebook_insights'] = self._transform_facebook_insights(raw_data['facebook_insights'])
        
        # Transform pages data
        if 'facebook_pages' in raw_data:
            pages_df = self._transform_facebook_pages_search(raw_data['facebook_pages'])
            
            # Combine with existing pages or create new
            if 'dim_facebook_pages' in transformed_data:
                transformed_data['dim_facebook_pages'] = pd.concat([transformed_data['dim_facebook_pages'], pages_df]).drop_duplicates('page_id')
            else:
                transformed_data['dim_facebook_pages'] = pages_df
        
        logger.info(f"Facebook transformation completed. Output tables: {list(transformed_data.keys())}")
        return transformed_data
    
    def _transform_twitter_tweets(self, tweets_df: pd.DataFrame, is_user_timeline: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Transform Twitter tweets into dimension and fact tables"""
        
        if tweets_df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Clean and enhance text
        tweets_df['cleaned_text'] = tweets_df['text'].apply(self._clean_text)
        tweets_df['text_length'] = tweets_df['text'].str.len()
        tweets_df['word_count'] = tweets_df['cleaned_text'].str.split().str.len()
        
        # Extract features
        tweets_df['hashtags'] = tweets_df['text'].apply(self._extract_hashtags)
        tweets_df['mentions'] = tweets_df['text'].apply(self._extract_mentions)
        tweets_df['urls'] = tweets_df['text'].apply(self._extract_urls)
        tweets_df['hashtag_count'] = tweets_df['hashtags'].str.len()
        tweets_df['mention_count'] = tweets_df['mentions'].str.len()
        tweets_df['url_count'] = tweets_df['urls'].str.len()
        
        # Sentiment analysis
        sentiment_scores = tweets_df['cleaned_text'].apply(self._get_sentiment)
        tweets_df['sentiment_score'] = sentiment_scores.apply(lambda x: x[0])
        tweets_df['sentiment_label'] = sentiment_scores.apply(lambda x: x[1])
        tweets_df['subjectivity_score'] = sentiment_scores.apply(lambda x: x[2])
        
        # Create user dimension
        user_columns = ['author_id'] if not is_user_timeline else ['user_id', 'username']
        if is_user_timeline:
            dim_users = tweets_df[['user_id', 'username']].drop_duplicates().copy()
            dim_users.rename(columns={'user_id': 'author_id'}, inplace=True)
        else:
            dim_users = tweets_df[['author_id']].drop_duplicates().copy()
            dim_users['username'] = None
        
        dim_users['platform'] = 'twitter'
        dim_users['display_name'] = None
        dim_users['verified'] = False
        dim_users['followers_count'] = 0
        dim_users['following_count'] = 0
        dim_users['posts_count'] = 0
        dim_users['bio'] = None
        dim_users['location'] = None
        dim_users['website'] = None
        dim_users['user_created_at'] = None
        dim_users['last_updated'] = datetime.now()
        dim_users['is_active'] = True
        dim_users.rename(columns={'author_id': 'user_id'}, inplace=True)
        
        # Create post dimension
        dim_posts = tweets_df[[
            'tweet_id', 'author_id', 'text', 'cleaned_text', 'created_at', 
            'language', 'source', 'text_length', 'word_count',
            'hashtags', 'mentions', 'urls', 'hashtag_count', 'mention_count', 'url_count',
            'sentiment_score', 'sentiment_label', 'subjectivity_score'
        ]].copy()
        
        dim_posts['platform'] = 'twitter'
        dim_posts['post_type'] = 'tweet'
        dim_posts['url'] = None  # Could be extracted from tweet entities
        dim_posts['last_updated'] = datetime.now()
        dim_posts['is_deleted'] = False
        dim_posts.rename(columns={
            'tweet_id': 'post_id',
            'author_id': 'user_id',
            'text': 'content',
            'created_at': 'post_created_at'
        }, inplace=True)
        
        # Create engagement fact table
        fact_engagement = tweets_df[[
            'tweet_id', 'author_id', 'created_at',
            'retweet_count', 'like_count', 'reply_count', 'quote_count'
        ]].copy()
        
        fact_engagement['platform'] = 'twitter'
        fact_engagement['shares_count'] = fact_engagement['retweet_count'] + fact_engagement['quote_count']
        fact_engagement['comments_count'] = fact_engagement['reply_count']
        fact_engagement['likes_count'] = fact_engagement['like_count']
        fact_engagement['views_count'] = 0  # Not available in basic API
        fact_engagement['impressions_count'] = 0
        fact_engagement['reach_count'] = 0
        
        # Calculate engagement rate
        fact_engagement['total_engagement'] = (
            fact_engagement['likes_count'] + 
            fact_engagement['shares_count'] + 
            fact_engagement['comments_count']
        )
        fact_engagement['engagement_rate'] = fact_engagement['total_engagement'] / (fact_engagement['total_engagement'].max() + 1)
        
        # Add date key
        fact_engagement['date_key'] = fact_engagement['created_at'].dt.strftime('%Y%m%d').astype(int)
        fact_engagement['extracted_at'] = datetime.now()
        fact_engagement['updated_at'] = datetime.now()
        
        fact_engagement.rename(columns={
            'tweet_id': 'post_id',
            'author_id': 'user_id'
        }, inplace=True)
        
        # Select final columns
        fact_engagement = fact_engagement[[
            'post_id', 'user_id', 'date_key', 'platform',
            'likes_count', 'shares_count', 'comments_count', 'views_count',
            'impressions_count', 'reach_count', 'engagement_rate',
            'extracted_at', 'updated_at'
        ]]
        
        return dim_users, dim_posts, fact_engagement
    
    def _transform_facebook_posts(self, posts_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Transform Facebook posts into dimension and fact tables"""
        
        if posts_df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Clean and enhance message text
        posts_df['cleaned_message'] = posts_df['message'].fillna('').apply(self._clean_text)
        posts_df['text_length'] = posts_df['message'].str.len()
        posts_df['word_count'] = posts_df['cleaned_message'].str.split().str.len()
        
        # Extract features
        posts_df['hashtags'] = posts_df['message'].fillna('').apply(self._extract_hashtags)
        posts_df['mentions'] = posts_df['message'].fillna('').apply(self._extract_mentions)
        posts_df['urls'] = posts_df['message'].fillna('').apply(self._extract_urls)
        
        # Sentiment analysis
        sentiment_scores = posts_df['cleaned_message'].apply(self._get_sentiment)
        posts_df['sentiment_score'] = sentiment_scores.apply(lambda x: x[0])
        posts_df['sentiment_label'] = sentiment_scores.apply(lambda x: x[1])
        posts_df['subjectivity_score'] = sentiment_scores.apply(lambda x: x[2])
        
        # Create page dimension (users in our model)
        dim_pages = posts_df[['page_id']].drop_duplicates().copy()
        dim_pages['platform'] = 'facebook'
        dim_pages['username'] = None
        dim_pages['display_name'] = None
        dim_pages['verified'] = False
        dim_pages['followers_count'] = 0
        dim_pages['following_count'] = 0
        dim_pages['posts_count'] = 0
        dim_pages['bio'] = None
        dim_pages['location'] = None
        dim_pages['website'] = None
        dim_pages['user_created_at'] = None
        dim_pages['last_updated'] = datetime.now()
        dim_pages['is_active'] = True
        dim_pages.rename(columns={'page_id': 'user_id'}, inplace=True)
        
        # Create post dimension
        dim_posts = posts_df[[
            'post_id', 'page_id', 'message', 'cleaned_message', 'created_time',
            'post_type', 'link', 'name', 'description', 'text_length', 'word_count',
            'hashtags', 'mentions', 'urls', 'sentiment_score', 'sentiment_label', 'subjectivity_score'
        ]].copy()
        
        dim_posts['platform'] = 'facebook'
        dim_posts['language'] = 'en'  # Default, could be detected
        dim_posts['last_updated'] = datetime.now()
        dim_posts['is_deleted'] = False
        dim_posts.rename(columns={
            'page_id': 'user_id',
            'message': 'content',
            'created_time': 'post_created_at',
            'link': 'url'
        }, inplace=True)
        
        # Create engagement fact table
        fact_engagement = posts_df[[
            'post_id', 'page_id', 'created_time',
            'shares_count', 'reactions_count', 'comments_count'
        ]].copy()
        
        fact_engagement['platform'] = 'facebook'
        fact_engagement['likes_count'] = fact_engagement['reactions_count']  # Reactions include likes
        fact_engagement['views_count'] = 0
        fact_engagement['impressions_count'] = 0
        fact_engagement['reach_count'] = 0
        
        # Calculate engagement rate
        fact_engagement['total_engagement'] = (
            fact_engagement['likes_count'] + 
            fact_engagement['shares_count'] + 
            fact_engagement['comments_count']
        )
        fact_engagement['engagement_rate'] = fact_engagement['total_engagement'] / (fact_engagement['total_engagement'].max() + 1)
        
        # Add date key
        fact_engagement['created_time'] = pd.to_datetime(fact_engagement['created_time'])
        fact_engagement['date_key'] = fact_engagement['created_time'].dt.strftime('%Y%m%d').astype(int)
        fact_engagement['extracted_at'] = datetime.now()
        fact_engagement['updated_at'] = datetime.now()
        
        fact_engagement.rename(columns={
            'page_id': 'user_id'
        }, inplace=True)
        
        # Select final columns
        fact_engagement = fact_engagement[[
            'post_id', 'user_id', 'date_key', 'platform',
            'likes_count', 'shares_count', 'comments_count', 'views_count',
            'impressions_count', 'reach_count', 'engagement_rate',
            'extracted_at', 'updated_at'
        ]]
        
        return dim_pages, dim_posts, fact_engagement
    
    def _clean_text(self, text: str) -> str:
        """Clean text content"""
        if pd.isna(text) or text == '':
            return ''
        
        cleaned = str(text)
        
        # Remove URLs if configured
        if self.transformation_config['text_cleaning']['remove_urls']:
            cleaned = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', cleaned)
        
        # Remove special characters if configured
        if self.transformation_config['text_cleaning']['remove_special_chars']:
            cleaned = re.sub(r'[^\w\s#@]', '', cleaned)
        
        # Normalize whitespace if configured
        if self.transformation_config['text_cleaning']['normalize_whitespace']:
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        if pd.isna(text):
            return []
        return re.findall(r'#\w+', str(text))
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from text"""
        if pd.isna(text):
            return []
        return re.findall(r'@\w+', str(text))
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        if pd.isna(text):
            return []
        return re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(text))
    
    def _get_sentiment(self, text: str) -> Tuple[float, str, float]:
        """Get sentiment analysis for text"""
        if pd.isna(text) or text == '':
            return 0.0, 'neutral', 0.0
        
        try:
            blob = TextBlob(str(text))
            sentiment_score = blob.sentiment.polarity
            subjectivity_score = blob.sentiment.subjectivity
            
            if sentiment_score > 0.1:
                sentiment_label = 'positive'
            elif sentiment_score < -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            return sentiment_score, sentiment_label, subjectivity_score
        except:
            return 0.0, 'neutral', 0.0
    
    def generate_date_dimension(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Generate date dimension table
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with date dimension
        """
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        dim_date = pd.DataFrame({
            'full_date': date_range,
            'date_key': date_range.strftime('%Y%m%d').astype(int),
            'year': date_range.year,
            'quarter': date_range.quarter,
            'month': date_range.month,
            'month_name': date_range.strftime('%B'),
            'day': date_range.day,
            'day_of_week': date_range.dayofweek + 1,  # 1=Monday, 7=Sunday
            'day_name': date_range.strftime('%A'),
            'week_of_year': date_range.isocalendar().week,
            'is_weekend': date_range.dayofweek >= 5
        })
        
        # Add holiday indicator (basic implementation)
        dim_date['is_holiday'] = False
        
        return dim_date
    
    def save_transformed_data(self, transformed_data: Dict[str, pd.DataFrame], 
                            file_format: str = 'parquet') -> Dict[str, str]:
        """
        Save transformed data to processed directory
        
        Args:
            transformed_data: Dictionary of transformed DataFrames
            file_format: File format (parquet, csv, json)
            
        Returns:
            Dictionary mapping table names to file paths
        """
        file_paths = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Ensure processed data directory exists
        Config.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        for table_name, df in transformed_data.items():
            if df.empty:
                logger.warning(f"Table {table_name} is empty, skipping save")
                continue
            
            filename = f"{table_name}_{timestamp}.{file_format}"
            filepath = Config.PROCESSED_DATA_DIR / filename
            
            try:
                if file_format.lower() == 'parquet':
                    df.to_parquet(filepath, index=False)
                elif file_format.lower() == 'csv':
                    df.to_csv(filepath, index=False)
                elif file_format.lower() == 'json':
                    df.to_json(filepath, orient='records', date_format='iso')
                else:
                    raise ValueError(f"Unsupported file format: {file_format}")
                
                file_paths[table_name] = str(filepath)
                logger.info(f"Saved {len(df)} records to {filepath}")
                
            except Exception as e:
                logger.error(f"Error saving {table_name}: {str(e)}")
        
        return file_paths