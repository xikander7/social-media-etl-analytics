"""
Dashboard Generation Module for Social Media Analytics
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from pathlib import Path

from ..utils.config import Config

logger = logging.getLogger(__name__)

class DashboardGenerator:
    """Generate interactive dashboards and visualizations for social media analytics"""
    
    def __init__(self):
        """Initialize dashboard generator"""
        self.reports_dir = Config.REPORTS_DIR
        self.figures_dir = self.reports_dir / "figures"
        
        # Create directories if they don't exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style preferences
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Color schemes for different platforms
        self.platform_colors = {
            'twitter': '#1DA1F2',
            'facebook': '#4267B2',
            'instagram': '#E4405F',
            'linkedin': '#0077B5'
        }
    
    def generate_engagement_dashboard(self, engagement_data: pd.DataFrame) -> str:
        """
        Generate engagement analytics dashboard
        
        Args:
            engagement_data: Combined engagement fact data
            
        Returns:
            Path to generated dashboard file
        """
        logger.info("Generating engagement analytics dashboard")
        
        if engagement_data.empty:
            logger.warning("No engagement data available for dashboard")
            return None
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Engagement by Platform',
                'Daily Engagement Trends',
                'Engagement Rate Distribution',
                'Top Performing Content'
            ],
            specs=[[{"type": "bar"}, {"type": "scatter"}],
                   [{"type": "histogram"}, {"type": "bar"}]]
        )
        
        # 1. Engagement by Platform
        platform_engagement = engagement_data.groupby('platform').agg({
            'likes_count': 'sum',
            'shares_count': 'sum',
            'comments_count': 'sum'
        }).reset_index()
        
        for i, metric in enumerate(['likes_count', 'shares_count', 'comments_count']):
            fig.add_trace(
                go.Bar(
                    x=platform_engagement['platform'],
                    y=platform_engagement[metric],
                    name=metric.replace('_count', '').title(),
                    marker_color=px.colors.qualitative.Set3[i]
                ),
                row=1, col=1
            )
        
        # 2. Daily Engagement Trends
        engagement_data['date'] = pd.to_datetime(engagement_data['date_key'], format='%Y%m%d')
        daily_engagement = engagement_data.groupby(['date', 'platform']).agg({
            'engagement_rate': 'mean'
        }).reset_index()
        
        for platform in daily_engagement['platform'].unique():
            platform_data = daily_engagement[daily_engagement['platform'] == platform]
            fig.add_trace(
                go.Scatter(
                    x=platform_data['date'],
                    y=platform_data['engagement_rate'],
                    mode='lines+markers',
                    name=f'{platform.title()} Engagement',
                    line=dict(color=self.platform_colors.get(platform, '#666666'))
                ),
                row=1, col=2
            )
        
        # 3. Engagement Rate Distribution
        fig.add_trace(
            go.Histogram(
                x=engagement_data['engagement_rate'],
                nbinsx=20,
                name='Engagement Rate',
                marker_color='lightblue'
            ),
            row=2, col=1
        )
        
        # 4. Top Performing Content
        top_posts = engagement_data.nlargest(10, 'engagement_rate')
        fig.add_trace(
            go.Bar(
                x=top_posts['engagement_rate'],
                y=[f'Post {i+1}' for i in range(len(top_posts))],
                orientation='h',
                name='Top Posts',
                marker_color='gold'
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text="Social Media Engagement Analytics Dashboard",
            showlegend=True
        )
        
        # Save dashboard
        dashboard_path = self.figures_dir / "engagement_analytics_dashboard.html"
        fig.write_html(dashboard_path)
        
        logger.info(f"Engagement dashboard saved to {dashboard_path}")
        return str(dashboard_path)
    
    def generate_sentiment_analysis_dashboard(self, posts_data: pd.DataFrame) -> str:
        """
        Generate sentiment analysis dashboard
        
        Args:
            posts_data: Combined posts dimension data
            
        Returns:
            Path to generated dashboard file
        """
        logger.info("Generating sentiment analysis dashboard")
        
        if posts_data.empty or 'sentiment_label' not in posts_data.columns:
            logger.warning("No sentiment data available for dashboard")
            return None
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Sentiment Distribution by Platform',
                'Sentiment Over Time',
                'Sentiment vs Engagement',
                'Word Cloud Data'
            ],
            specs=[[{"type": "bar"}, {"type": "scatter"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        # 1. Sentiment Distribution by Platform
        sentiment_platform = posts_data.groupby(['platform', 'sentiment_label']).size().unstack(fill_value=0)
        
        for sentiment in ['positive', 'neutral', 'negative']:
            if sentiment in sentiment_platform.columns:
                fig.add_trace(
                    go.Bar(
                        x=sentiment_platform.index,
                        y=sentiment_platform[sentiment],
                        name=sentiment.title(),
                        marker_color={'positive': 'green', 'neutral': 'gray', 'negative': 'red'}[sentiment]
                    ),
                    row=1, col=1
                )
        
        # 2. Sentiment Over Time
        posts_data['date'] = pd.to_datetime(posts_data['post_created_at']).dt.date
        daily_sentiment = posts_data.groupby(['date', 'sentiment_label']).size().unstack(fill_value=0).reset_index()
        
        for sentiment in ['positive', 'neutral', 'negative']:
            if sentiment in daily_sentiment.columns:
                fig.add_trace(
                    go.Scatter(
                        x=daily_sentiment['date'],
                        y=daily_sentiment[sentiment],
                        mode='lines',
                        name=f'{sentiment.title()} Trend',
                        line=dict(color={'positive': 'green', 'neutral': 'gray', 'negative': 'red'}[sentiment])
                    ),
                    row=1, col=2
                )
        
        # 3. Sentiment vs Text Length
        fig.add_trace(
            go.Scatter(
                x=posts_data['text_length'],
                y=posts_data['sentiment_score'],
                mode='markers',
                text=posts_data['sentiment_label'],
                name='Sentiment vs Length',
                marker=dict(
                    color=posts_data['sentiment_score'],
                    colorscale='RdYlGn',
                    showscale=True
                )
            ),
            row=2, col=1
        )
        
        # 4. Most Common Words by Sentiment
        if 'word_count' in posts_data.columns:
            sentiment_words = posts_data.groupby('sentiment_label')['word_count'].mean().reset_index()
            fig.add_trace(
                go.Bar(
                    x=sentiment_words['sentiment_label'],
                    y=sentiment_words['word_count'],
                    name='Avg Words by Sentiment',
                    marker_color='purple'
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            height=800,
            title_text="Social Media Sentiment Analysis Dashboard",
            showlegend=True
        )
        
        dashboard_path = self.figures_dir / "sentiment_analysis_dashboard.html"
        fig.write_html(dashboard_path)
        
        logger.info(f"Sentiment dashboard saved to {dashboard_path}")
        return str(dashboard_path)
    
    def generate_platform_comparison_dashboard(self, transformed_data: Dict[str, pd.DataFrame]) -> str:
        """
        Generate platform comparison dashboard
        
        Args:
            transformed_data: All transformed data tables
            
        Returns:
            Path to generated dashboard file
        """
        logger.info("Generating platform comparison dashboard")
        
        # Combine engagement data from all platforms
        engagement_tables = [k for k in transformed_data.keys() if k.startswith('fact_') and 'engagement' in k]
        if not engagement_tables:
            logger.warning("No engagement data available for platform comparison")
            return None
        
        combined_engagement = pd.concat([transformed_data[table] for table in engagement_tables], ignore_index=True)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Platform Metrics Comparison',
                'Platform Activity Timeline',
                'Engagement Rate by Platform',
                'Content Volume by Platform'
            ]
        )
        
        # 1. Platform Metrics Comparison (Radar Chart)
        platform_metrics = combined_engagement.groupby('platform').agg({
            'likes_count': 'mean',
            'shares_count': 'mean',
            'comments_count': 'mean',
            'engagement_rate': 'mean'
        }).reset_index()
        
        # Normalize metrics for radar chart
        for col in ['likes_count', 'shares_count', 'comments_count', 'engagement_rate']:
            platform_metrics[f'{col}_norm'] = platform_metrics[col] / platform_metrics[col].max()
        
        for platform in platform_metrics['platform'].unique():
            platform_data = platform_metrics[platform_metrics['platform'] == platform]
            fig.add_trace(
                go.Scatterpolar(
                    r=[platform_data[f'{col}_norm'].iloc[0] for col in ['likes_count', 'shares_count', 'comments_count', 'engagement_rate']],
                    theta=['Likes', 'Shares', 'Comments', 'Engagement'],
                    fill='toself',
                    name=platform.title(),
                    line_color=self.platform_colors.get(platform, '#666666')
                ),
                row=1, col=1
            )
        
        # 2. Platform Activity Timeline
        combined_engagement['date'] = pd.to_datetime(combined_engagement['date_key'], format='%Y%m%d')
        daily_activity = combined_engagement.groupby(['date', 'platform']).size().reset_index(name='post_count')
        
        for platform in daily_activity['platform'].unique():
            platform_data = daily_activity[daily_activity['platform'] == platform]
            fig.add_trace(
                go.Scatter(
                    x=platform_data['date'],
                    y=platform_data['post_count'],
                    mode='lines',
                    name=f'{platform.title()} Posts',
                    line=dict(color=self.platform_colors.get(platform, '#666666'))
                ),
                row=1, col=2
            )
        
        # 3. Engagement Rate Distribution by Platform
        fig.add_trace(
            go.Box(
                y=combined_engagement['engagement_rate'],
                x=combined_engagement['platform'],
                name='Engagement Rate',
                boxpoints='outliers'
            ),
            row=2, col=1
        )
        
        # 4. Content Volume by Platform
        platform_volume = combined_engagement['platform'].value_counts()
        fig.add_trace(
            go.Pie(
                labels=platform_volume.index,
                values=platform_volume.values,
                name="Content Volume"
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=800,
            title_text="Social Media Platform Comparison Dashboard",
            showlegend=True
        )
        
        dashboard_path = self.figures_dir / "platform_comparison_dashboard.html"
        fig.write_html(dashboard_path)
        
        logger.info(f"Platform comparison dashboard saved to {dashboard_path}")
        return str(dashboard_path)
    
    def generate_static_summary_charts(self, transformed_data: Dict[str, pd.DataFrame]) -> List[str]:
        """
        Generate static summary charts using matplotlib
        
        Args:
            transformed_data: All transformed data tables
            
        Returns:
            List of paths to generated chart files
        """
        logger.info("Generating static summary charts")
        
        chart_paths = []
        
        # Combine all engagement data
        engagement_tables = [k for k in transformed_data.keys() if 'engagement' in k]
        if engagement_tables:
            combined_engagement = pd.concat([transformed_data[table] for table in engagement_tables], ignore_index=True)
            
            # Chart 1: Platform Performance Summary
            plt.figure(figsize=(12, 8))
            
            # Create subplot grid
            gs = plt.GridSpec(2, 2, hspace=0.3, wspace=0.3)
            
            # Platform engagement comparison
            ax1 = plt.subplot(gs[0, 0])
            platform_totals = combined_engagement.groupby('platform')[['likes_count', 'shares_count', 'comments_count']].sum()
            platform_totals.plot(kind='bar', ax=ax1, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
            ax1.set_title('Total Engagement by Platform')
            ax1.set_ylabel('Count')
            ax1.tick_params(axis='x', rotation=45)
            
            # Engagement rate distribution
            ax2 = plt.subplot(gs[0, 1])
            combined_engagement.boxplot(column='engagement_rate', by='platform', ax=ax2)
            ax2.set_title('Engagement Rate Distribution')
            ax2.set_ylabel('Engagement Rate')
            
            # Daily post volume
            ax3 = plt.subplot(gs[1, :])
            combined_engagement['date'] = pd.to_datetime(combined_engagement['date_key'], format='%Y%m%d')
            daily_posts = combined_engagement.groupby(['date', 'platform']).size().unstack(fill_value=0)
            daily_posts.plot(ax=ax3, marker='o', linewidth=2)
            ax3.set_title('Daily Post Volume by Platform')
            ax3.set_ylabel('Number of Posts')
            ax3.legend(title='Platform')
            
            plt.suptitle('Social Media Analytics Summary', fontsize=16, y=0.98)
            
            chart_path = self.figures_dir / "analytics_summary.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            chart_paths.append(str(chart_path))
        
        return chart_paths
    
    def generate_summary_report(self, transformed_data: Dict[str, pd.DataFrame]) -> str:
        """
        Generate a comprehensive summary report
        
        Args:
            transformed_data: All transformed data tables
            
        Returns:
            Path to generated report file
        """
        logger.info("Generating comprehensive summary report")
        
        report_content = []
        report_content.append("# Social Media ETL Analytics Report")
        report_content.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_content.append("\\n")
        
        # Data Summary Section
        report_content.append("## Data Summary")
        total_records = sum(len(df) for df in transformed_data.values())
        report_content.append(f"- Total records processed: {total_records:,}")
        report_content.append(f"- Number of tables generated: {len(transformed_data)}")
        
        # Table breakdown
        report_content.append("\\n### Table Breakdown")
        for table_name, df in transformed_data.items():
            if not df.empty:
                report_content.append(f"- **{table_name}**: {len(df):,} records")
        
        # Platform Analysis
        engagement_tables = [k for k in transformed_data.keys() if 'engagement' in k]
        if engagement_tables:
            combined_engagement = pd.concat([transformed_data[table] for table in engagement_tables], ignore_index=True)
            
            report_content.append("\\n## Platform Analysis")
            
            platform_stats = combined_engagement.groupby('platform').agg({
                'likes_count': ['sum', 'mean'],
                'shares_count': ['sum', 'mean'],
                'comments_count': ['sum', 'mean'],
                'engagement_rate': ['mean', 'std']
            }).round(2)
            
            for platform in platform_stats.index:
                report_content.append(f"\\n### {platform.title()} Platform")
                report_content.append(f"- Total Likes: {platform_stats.loc[platform, ('likes_count', 'sum')]:,}")
                report_content.append(f"- Total Shares: {platform_stats.loc[platform, ('shares_count', 'sum')]:,}")
                report_content.append(f"- Total Comments: {platform_stats.loc[platform, ('comments_count', 'sum')]:,}")
                report_content.append(f"- Average Engagement Rate: {platform_stats.loc[platform, ('engagement_rate', 'mean')]:.4f}")
        
        # Sentiment Analysis
        posts_tables = [k for k in transformed_data.keys() if 'posts' in k]
        if posts_tables:
            combined_posts = pd.concat([transformed_data[table] for table in posts_tables if 'sentiment_label' in transformed_data[table].columns], ignore_index=True)
            
            if not combined_posts.empty and 'sentiment_label' in combined_posts.columns:
                report_content.append("\\n## Sentiment Analysis")
                sentiment_dist = combined_posts['sentiment_label'].value_counts()
                total_posts = len(combined_posts)
                
                for sentiment, count in sentiment_dist.items():
                    percentage = (count / total_posts) * 100
                    report_content.append(f"- {sentiment.title()}: {count:,} posts ({percentage:.1f}%)")
        
        # Key Insights
        report_content.append("\\n## Key Insights")
        report_content.append("- ETL pipeline successfully processed social media data from multiple platforms")
        report_content.append("- Data transformation included sentiment analysis and engagement metrics")
        report_content.append("- Dimensional modeling applied for analytics-ready data warehouse")
        
        # Write report to file
        report_path = self.reports_dir / "analytics_summary_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\\n".join(report_content))
        
        logger.info(f"Summary report saved to {report_path}")
        return str(report_path)
    
    def generate_all_dashboards(self, transformed_data: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """
        Generate all available dashboards
        
        Args:
            transformed_data: All transformed data tables
            
        Returns:
            Dictionary mapping dashboard names to file paths
        """
        logger.info("Generating all dashboards")
        
        dashboard_paths = {}
        
        try:
            # Combine engagement data
            engagement_tables = [k for k in transformed_data.keys() if 'engagement' in k]
            if engagement_tables:
                combined_engagement = pd.concat([transformed_data[table] for table in engagement_tables], ignore_index=True)
                
                # Generate engagement dashboard
                engagement_path = self.generate_engagement_dashboard(combined_engagement)
                if engagement_path:
                    dashboard_paths['engagement'] = engagement_path
            
            # Combine posts data for sentiment analysis
            posts_tables = [k for k in transformed_data.keys() if 'posts' in k]
            if posts_tables:
                combined_posts = pd.concat([transformed_data[table] for table in posts_tables], ignore_index=True)
                
                # Generate sentiment dashboard
                sentiment_path = self.generate_sentiment_analysis_dashboard(combined_posts)
                if sentiment_path:
                    dashboard_paths['sentiment'] = sentiment_path
            
            # Generate platform comparison dashboard
            comparison_path = self.generate_platform_comparison_dashboard(transformed_data)
            if comparison_path:
                dashboard_paths['platform_comparison'] = comparison_path
            
            # Generate static charts
            static_chart_paths = self.generate_static_summary_charts(transformed_data)
            if static_chart_paths:
                dashboard_paths['static_charts'] = static_chart_paths
            
        except Exception as e:
            logger.error(f"Error generating dashboards: {str(e)}")
        
        logger.info(f"Generated {len(dashboard_paths)} dashboards")
        return dashboard_paths