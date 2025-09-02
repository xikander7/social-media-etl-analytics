#!/usr/bin/env python3
"""
Pipeline Runner Script - Simplified execution interface
"""

import sys
import os
from pathlib import Path
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from main import SocialMediaETLPipeline
from src.utils.config import setup_logging

def main():
    """Main execution function"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Create logs directory
    Path('../logs').mkdir(exist_ok=True)
    
    logger.info("Starting Social Media ETL Pipeline")
    
    try:
        # Initialize and run pipeline
        pipeline = SocialMediaETLPipeline()
        results = pipeline.run_full_pipeline()
        
        if results['status'] == 'completed':
            logger.info("Pipeline completed successfully")
            logger.info("Check reports/figures/ for generated dashboards")
            logger.info("Check data/processed/ for transformed data")
        else:
            logger.error(f"Pipeline failed: {results.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()