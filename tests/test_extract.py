"""
Test cases for data extraction module
"""

import unittest
import pandas as pd
from unittest.mock import Mock, patch
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from src.etl.extract import DataExtractor
from src.utils.config import Config

class TestDataExtractor(unittest.TestCase):
    """Test cases for DataExtractor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = DataExtractor()
    
    def test_init_without_credentials(self):
        """Test extractor initialization without API credentials"""
        extractor = DataExtractor()
        self.assertIsNone(extractor.twitter_client)
        self.assertIsNone(extractor.facebook_client)
    
    @patch('src.etl.extract.TwitterClient')
    def test_extract_twitter_data_empty_config(self, mock_twitter_client):
        """Test Twitter extraction with empty configuration"""
        mock_client = Mock()
        mock_twitter_client.return_value = mock_client
        self.extractor.twitter_client = mock_client
        
        config = {}
        result = self.extractor.extract_twitter_data(config)
        
        self.assertEqual(result, {})
    
    @patch('src.etl.extract.TwitterClient')
    def test_extract_twitter_data_with_search_queries(self, mock_twitter_client):
        """Test Twitter extraction with search queries"""
        mock_client = Mock()
        mock_client.search_tweets.return_value = pd.DataFrame({
            'tweet_id': ['123', '456'],
            'text': ['Sample tweet 1', 'Sample tweet 2'],
            'created_at': ['2024-01-01', '2024-01-02']
        })
        mock_twitter_client.return_value = mock_client
        self.extractor.twitter_client = mock_client
        
        config = {
            'search_queries': ['test query'],
            'max_results': 10
        }
        
        result = self.extractor.extract_twitter_data(config)
        
        self.assertIn('twitter_tweets', result)
        self.assertEqual(len(result['twitter_tweets']), 2)
        mock_client.search_tweets.assert_called_once()
    
    def test_save_raw_data(self):
        """Test saving raw data to files"""
        # Create sample data
        sample_data = {
            'test_dataset': pd.DataFrame({
                'id': [1, 2, 3],
                'text': ['sample 1', 'sample 2', 'sample 3']
            })
        }
        
        # Mock the raw data directory
        with patch.object(Config, 'RAW_DATA_DIR') as mock_dir:
            mock_dir.mkdir = Mock()
            mock_path = Mock()
            mock_dir.__truediv__ = Mock(return_value=mock_path)
            
            # Mock pandas to_json method
            with patch.object(pd.DataFrame, 'to_json') as mock_to_json:
                result = self.extractor.save_raw_data(sample_data, 'json')
                
                self.assertIn('test_dataset', result)
                mock_to_json.assert_called_once()
    
    def test_get_extraction_summary(self):
        """Test extraction summary generation"""
        sample_data = {
            'twitter_tweets': pd.DataFrame({
                'id': [1, 2], 
                'text': ['tweet 1', 'tweet 2']
            }),
            'facebook_posts': pd.DataFrame({
                'id': [1], 
                'message': ['post 1']
            })
        }
        
        summary = self.extractor.get_extraction_summary(sample_data)
        
        self.assertEqual(len(summary), 2)
        self.assertIn('dataset_name', summary.columns)
        self.assertIn('platform', summary.columns)
        self.assertIn('records_count', summary.columns)

if __name__ == '__main__':
    unittest.main()