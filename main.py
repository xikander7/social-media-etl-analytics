#!/usr/bin/env python3
"""
Social Media ETL Analytics - Main Pipeline Orchestrator
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import yaml

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

from src.utils.config import Config, setup_logging
from src.etl.extract import DataExtractor
from src.etl.transform import DataTransformer
from src.database.redshift_client import RedshiftClient
from src.visualization.dashboard import DashboardGenerator
from src.utils.notification import NotificationManager

logger = logging.getLogger(__name__)

class SocialMediaETLPipeline:
    """Main ETL pipeline orchestrator for social media analytics"""
    
    def __init__(self):
        """Initialize pipeline components"""
        self.extractor = DataExtractor()
        self.transformer = DataTransformer()
        self.db_client = None
        self.dashboard_generator = DashboardGenerator()
        self.notification_manager = NotificationManager()
        
        # Initialize database client if configured
        try:
            Config.validate_required_configs()
            self.db_client = RedshiftClient()
        except Exception as e:
            logger.warning(f"Database client initialization failed: {str(e)}")
    
    def run_extraction(self, config_file: str = None) -> dict:
        """
        Run data extraction phase
        
        Args:
            config_file: Path to extraction configuration file
            
        Returns:
            Dictionary with extraction results
        """
        logger.info("Starting data extraction phase")
        
        # Load extraction configuration
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                extraction_config = yaml.safe_load(f)
        else:
            # Default configuration
            extraction_config = {
                'twitter': {
                    'search_queries': [
                        'social media analytics',
                        'data engineering',
                        'ETL pipeline'
                    ],
                    'users': [
                        'elonmusk',
                        'sundarpichai',
                        'satyanadella'
                    ],
                    'max_results': 100,
                    'user_max_results': 50,
                    'days_back': 7,
                    'extract_trends': True
                },
                'facebook': {
                    'page_ids': [
                        'facebook',
                        'microsoft',
                        'google'
                    ],
                    'posts_limit': 50,
                    'days_back': 7,
                    'search_queries': ['technology', 'AI', 'data science'],
                    'search_limit': 25
                }
            }
        
        # Extract data from all platforms
        extracted_data = self.extractor.extract_all_platforms(extraction_config)
        
        # Save raw data
        raw_file_paths = self.extractor.save_raw_data(extracted_data, file_format='json')
        
        # Generate extraction summary
        extraction_summary = self.extractor.get_extraction_summary(extracted_data)
        
        results = {
            'extracted_data': extracted_data,
            'file_paths': raw_file_paths,
            'summary': extraction_summary,
            'config': extraction_config
        }
        
        logger.info(f"Extraction completed. Total datasets: {len(extracted_data)}")
        return results
    
    def run_transformation(self, extracted_data: dict) -> dict:
        """
        Run data transformation phase
        
        Args:
            extracted_data: Dictionary with extracted data
            
        Returns:
            Dictionary with transformation results
        """
        logger.info("Starting data transformation phase")
        
        transformed_data = {}
        
        # Transform Twitter data
        twitter_data = {k: v for k, v in extracted_data.items() if k.startswith('twitter_')}
        if twitter_data:
            twitter_transformed = self.transformer.transform_twitter_data(twitter_data)
            transformed_data.update(twitter_transformed)
        
        # Transform Facebook data
        facebook_data = {k: v for k, v in extracted_data.items() if k.startswith('facebook_')}
        if facebook_data:
            facebook_transformed = self.transformer.transform_facebook_data(facebook_data)
            transformed_data.update(facebook_transformed)
        
        # Generate date dimension
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        transformed_data['dim_date'] = self.transformer.generate_date_dimension(start_date, end_date)
        
        # Save transformed data
        transformed_file_paths = self.transformer.save_transformed_data(transformed_data, file_format='parquet')
        
        results = {
            'transformed_data': transformed_data,
            'file_paths': transformed_file_paths
        }
        
        logger.info(f"Transformation completed. Total tables: {len(transformed_data)}")
        return results
    
    def run_loading(self, transformed_data: dict) -> dict:
        """
        Run data loading phase to Redshift
        
        Args:
            transformed_data: Dictionary with transformed data
            
        Returns:
            Dictionary with loading results
        """
        logger.info("Starting data loading phase")
        
        if not self.db_client:
            logger.warning("Database client not available, skipping loading phase")
            return {'status': 'skipped', 'reason': 'database_not_configured'}
        
        loading_results = {}
        
        try:
            # Create schema and tables
            self.db_client.create_schema_if_not_exists('social_media')
            self.db_client.execute_ddl("SET search_path TO social_media, public")
            
            # Create dimension and fact tables
            self.db_client.create_dimension_tables()
            self.db_client.create_fact_tables()
            
            # Load data into tables
            table_load_results = {}
            
            for table_name, df in transformed_data.items():
                if df.empty:
                    continue
                
                try:
                    # Determine primary key based on table type
                    if table_name.startswith('dim_'):
                        if 'user_id' in df.columns:
                            primary_key = 'user_id'
                        elif 'post_id' in df.columns:
                            primary_key = 'post_id'
                        elif 'date_key' in df.columns:
                            primary_key = 'date_key'
                        else:
                            primary_key = df.columns[0]
                    else:
                        primary_key = 'post_id' if 'post_id' in df.columns else df.columns[0]
                    
                    # Upsert data
                    self.db_client.upsert_dataframe(df, table_name, primary_key)
                    table_load_results[table_name] = {
                        'status': 'success',
                        'records_loaded': len(df)
                    }
                    
                except Exception as e:
                    logger.error(f"Error loading table {table_name}: {str(e)}")
                    table_load_results[table_name] = {
                        'status': 'failed',
                        'error': str(e)
                    }
            
            loading_results = {
                'status': 'completed',
                'tables': table_load_results
            }
            
        except Exception as e:
            logger.error(f"Error in loading phase: {str(e)}")
            loading_results = {
                'status': 'failed',
                'error': str(e)
            }
        
        logger.info("Loading phase completed")
        return loading_results
    
    def run_visualization(self, transformed_data: dict) -> dict:
        """
        Run data visualization phase
        
        Args:
            transformed_data: Dictionary with transformed data
            
        Returns:
            Dictionary with visualization results
        """
        logger.info("Starting visualization phase")
        
        try:
            # Generate dashboards
            dashboard_paths = self.dashboard_generator.generate_all_dashboards(transformed_data)
            
            # Generate summary report
            report_path = self.dashboard_generator.generate_summary_report(transformed_data)
            
            results = {
                'status': 'completed',
                'dashboard_paths': dashboard_paths,
                'report_path': report_path
            }
            
        except Exception as e:
            logger.error(f"Error in visualization phase: {str(e)}")
            results = {
                'status': 'failed',
                'error': str(e)
            }
        
        logger.info("Visualization phase completed")
        return results
    
    def run_full_pipeline(self, extraction_config_file: str = None) -> dict:
        """
        Run complete ETL pipeline
        
        Args:
            extraction_config_file: Path to extraction configuration file
            
        Returns:
            Dictionary with pipeline results
        """
        pipeline_start_time = datetime.now()
        logger.info("Starting complete ETL pipeline")
        
        try:
            # Phase 1: Extraction
            extraction_results = self.run_extraction(extraction_config_file)
            
            # Phase 2: Transformation
            transformation_results = self.run_transformation(extraction_results['extracted_data'])
            
            # Phase 3: Loading
            loading_results = self.run_loading(transformation_results['transformed_data'])
            
            # Phase 4: Visualization
            visualization_results = self.run_visualization(transformation_results['transformed_data'])
            
            # Send success notification
            pipeline_duration = datetime.now() - pipeline_start_time
            self.notification_manager.send_success_notification(
                pipeline_duration=pipeline_duration,
                extraction_summary=extraction_results['summary'],
                loading_results=loading_results
            )
            
            results = {
                'status': 'completed',
                'pipeline_duration': pipeline_duration,
                'extraction': extraction_results,
                'transformation': transformation_results,
                'loading': loading_results,
                'visualization': visualization_results
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            
            # Send failure notification
            self.notification_manager.send_failure_notification(str(e))
            
            results = {
                'status': 'failed',
                'error': str(e),
                'pipeline_duration': datetime.now() - pipeline_start_time
            }
        
        logger.info(f"Pipeline completed in {results['pipeline_duration']}")
        return results

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Social Media ETL Analytics Pipeline')
    parser.add_argument('--phase', choices=['extract', 'transform', 'load', 'visualize', 'full'], 
                       default='full', help='Pipeline phase to run')
    parser.add_argument('--config', type=str, help='Path to extraction configuration file')
    parser.add_argument('--output-dir', type=str, help='Override output directory')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    os.environ['LOG_LEVEL'] = args.log_level
    setup_logging()
    
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    # Initialize pipeline
    pipeline = SocialMediaETLPipeline()
    
    try:
        if args.phase == 'full':
            results = pipeline.run_full_pipeline(args.config)
        elif args.phase == 'extract':
            results = pipeline.run_extraction(args.config)
        elif args.phase == 'transform':
            # For standalone transform, need to load extracted data
            logger.error("Standalone transform phase requires previously extracted data")
            sys.exit(1)
        elif args.phase == 'load':
            # For standalone load, need to load transformed data
            logger.error("Standalone load phase requires previously transformed data")
            sys.exit(1)
        elif args.phase == 'visualize':
            # For standalone visualize, need to load transformed data
            logger.error("Standalone visualize phase requires previously transformed data")
            sys.exit(1)
        
        if results['status'] == 'completed':
            logger.info("Pipeline execution completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Pipeline execution failed: {results.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()