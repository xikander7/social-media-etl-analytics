"""
Notification Manager for Social Media ETL Pipeline
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd

from .config import Config

logger = logging.getLogger(__name__)

class NotificationManager:
    """Manage pipeline notifications and alerts"""
    
    def __init__(self):
        """Initialize notification manager"""
        self.notification_email = Config.NOTIFICATION_EMAIL
    
    def send_success_notification(self, pipeline_duration: timedelta, 
                                extraction_summary: pd.DataFrame,
                                loading_results: Dict[str, Any]):
        """
        Send success notification after pipeline completion
        
        Args:
            pipeline_duration: Total pipeline execution time
            extraction_summary: Summary of extracted data
            loading_results: Results from data loading phase
        """
        try:
            subject = f"Social Media ETL Pipeline - Success ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
            
            # Build message content
            message_parts = [
                "Social Media ETL Pipeline completed successfully",
                "",
                f"Execution Summary:",
                f"Duration: {pipeline_duration}",
                f"Completion Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "Data Extraction Summary:"
            ]
            
            if not extraction_summary.empty:
                for _, row in extraction_summary.iterrows():
                    message_parts.append(f"{row['dataset_name']}: {row['records_count']:,} records ({row['memory_usage_mb']:.1f} MB)")
            
            message_parts.extend([
                "",
                "Data Loading Results:"
            ])
            
            if loading_results.get('status') == 'completed':
                for table_name, result in loading_results.get('tables', {}).items():
                    if result['status'] == 'success':
                        message_parts.append(f"{table_name}: SUCCESS - {result['records_loaded']:,} records loaded")
                    else:
                        message_parts.append(f"{table_name}: FAILED - {result['error']}")
            
            message_parts.extend([
                "",
                "Generated Outputs:",
                "Raw data files saved to data/raw/",
                "Processed data files saved to data/processed/",
                "Interactive dashboards generated in reports/figures/",
                "Summary report available in reports/",
                "",
                "Next Steps:",
                "Review generated dashboards for insights",
                "Check data quality in processed files",
                "Schedule next pipeline run if needed",
                "",
                "---",
                f"Pipeline executed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ])
            
            message = "\\n".join(message_parts)
            self._send_notification(subject, message)
            
        except Exception as e:
            logger.error(f"Failed to send success notification: {str(e)}")
    
    def send_failure_notification(self, error_message: str):
        """
        Send failure notification when pipeline fails
        
        Args:
            error_message: Error message describing the failure
        """
        try:
            subject = f"Social Media ETL Pipeline - Failure ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
            
            message_parts = [
                "Social Media ETL Pipeline failed",
                "",
                f"Failure Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                f"Error Details:",
                f"{error_message}",
                "",
                "Troubleshooting Steps:",
                "1. Check the pipeline logs for detailed error information",
                "2. Verify API credentials and connection settings",
                "3. Ensure all required dependencies are installed",
                "4. Check database connectivity and permissions",
                "5. Validate input data format and availability",
                "",
                "Common Issues:",
                "API rate limits exceeded - wait and retry",
                "Database connection timeout - check network/credentials",
                "Missing environment variables - verify .env configuration",
                "Insufficient disk space - clear temporary files",
                "",
                "Support:",
                f"Contact: {self.notification_email}",
                "",
                "---",
                f"Pipeline failed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            message = "\\n".join(message_parts)
            self._send_notification(subject, message)
            
        except Exception as e:
            logger.error(f"Failed to send failure notification: {str(e)}")
    
    def send_data_quality_alert(self, quality_issues: Dict[str, Any]):
        """
        Send alert for data quality issues
        
        Args:
            quality_issues: Dictionary containing data quality problems
        """
        try:
            subject = f"Social Media ETL - Data Quality Alert ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
            
            message_parts = [
                "Data Quality Issues Detected",
                "",
                f"Issues Found:"
            ]
            
            for issue_type, details in quality_issues.items():
                message_parts.append(f"{issue_type}: {details}")
            
            message_parts.extend([
                "",
                "Recommended Actions:",
                "Review data extraction logic for accuracy",
                "Check API response formats for changes",
                "Validate transformation rules",
                "Consider implementing additional data validation",
                "",
                f"Detection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ])
            
            message = "\\n".join(message_parts)
            self._send_notification(subject, message)
            
        except Exception as e:
            logger.error(f"Failed to send data quality alert: {str(e)}")
    
    def _send_notification(self, subject: str, message: str):
        """
        Send notification via console log (email implementation would go here)
        
        Args:
            subject: Email subject
            message: Email message body
        """
        # For now, just log the notification
        # In production, implement actual email sending via SMTP
        
        logger.info("="*80)
        logger.info(f"NOTIFICATION: {subject}")
        logger.info("="*80)
        logger.info(message)
        logger.info("="*80)
        
        # TODO: Implement actual email sending
        # if self.notification_email:
        #     self._send_email(subject, message)
    
    def _send_email(self, subject: str, message: str):
        """
        Send email notification (placeholder implementation)
        
        Args:
            subject: Email subject
            message: Email message body
        """
        # Placeholder for actual email implementation
        # This would typically use SMTP configuration
        
        try:
            # Example SMTP implementation:
            # smtp_server = "smtp.gmail.com"
            # smtp_port = 587
            # sender_email = Config.SMTP_EMAIL
            # sender_password = Config.SMTP_PASSWORD
            # 
            # msg = MIMEMultipart()
            # msg['From'] = sender_email
            # msg['To'] = self.notification_email
            # msg['Subject'] = subject
            # 
            # msg.attach(MIMEText(message, 'plain'))
            # 
            # with smtplib.SMTP(smtp_server, smtp_port) as server:
            #     server.starttls()
            #     server.login(sender_email, sender_password)
            #     server.send_message(msg)
            
            logger.info(f"Email notification would be sent to: {self.notification_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
    
    def log_pipeline_metrics(self, metrics: Dict[str, Any]):
        """
        Log pipeline execution metrics
        
        Args:
            metrics: Dictionary containing pipeline metrics
        """
        logger.info("Pipeline Execution Metrics:")
        for metric_name, metric_value in metrics.items():
            logger.info(f"  {metric_name}: {metric_value}")