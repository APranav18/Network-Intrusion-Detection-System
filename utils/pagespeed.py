"""
PageSpeed Insights Integration
===============================
Google PageSpeed Insights API wrapper for performance monitoring.
Analyzes web pages and tracks performance metrics over time.
"""

import requests
import logging
import json
from urllib.parse import quote_plus
from typing import Dict, Optional, List, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class PageSpeedAnalyzer:
    """
    Google PageSpeed Insights API wrapper.
    Monitors web page performance and stores metrics.
    """
    
    # Official Google PageSpeed Insights API endpoint
    API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize PageSpeed analyzer.
        
        Args:
            api_key: Google API key (optional). If not provided, limited requests allowed.
                    Get API key from: https://developers.google.com/speed/docs/insights/v5/get-started
        """
        self.api_key = api_key or os.environ.get('GOOGLE_PAGESPEED_API_KEY')
        self.session = requests.Session()
        self.timeout = 60
        
    def analyze_page(
        self,
        url: str,
        strategy: str = 'mobile',
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a web page using PageSpeed Insights API.
        
        Args:
            url: URL to analyze
            strategy: 'mobile' or 'desktop'
            categories: List of categories to analyze (e.g., ['performance', 'accessibility'])
            
        Returns:
            Dictionary with PageSpeed results
        """
        if not categories:
            categories = [
                'performance',
                'accessibility',
                'best-practices',
                'seo',
                'pwa'
            ]
        
        params = {
            'url': url,
            'strategy': strategy,
            'category': categories
        }
        
        if self.api_key:
            params['key'] = self.api_key
        
        try:
            logger.info(f"Analyzing {url} with strategy={strategy}")
            
            response = self.session.get(
                self.API_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract results
            result = self._parse_results(data, url, strategy)
            logger.info(f"Analysis complete for {url}: {result['scores']}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"PageSpeed API error for {url}: {e}")
            report_url = f"https://pagespeed.web.dev/analysis?url={quote_plus(url)}&form_factor={strategy}"
            message = str(e)
            if '429' in message:
                message = (
                    'PageSpeed API rate limit reached (429). Set GOOGLE_PAGESPEED_API_KEY '
                    'to increase quota and retry.'
                )
            return {
                'url': url,
                'strategy': strategy,
                'error': message,
                'report_url': report_url,
                'success': False
            }
    
    def _parse_results(self, data: Dict, url: str, strategy: str) -> Dict[str, Any]:
        """
        Parse PageSpeed API response and extract key metrics.
        
        Args:
            data: Raw API response
            url: Analyzed URL
            strategy: 'mobile' or 'desktop'
            
        Returns:
            Parsed results dictionary
        """
        try:
            # Lighthouse results
            lighthouse = data.get('lighthouseResult', {})
            
            # Extract scores
            scores = {}
            score_details = []
            for category, details in lighthouse.get('categories', {}).items():
                scores[category] = details.get('score', 0) * 100  # Convert to 0-100
                score_details.append({
                    'id': category,
                    'title': details.get('title', category.replace('-', ' ').title()),
                    'score': details.get('score', 0) * 100,
                })
            
            # Extract metrics
            metrics = {}
            audit_results = lighthouse.get('audits', {})
            
            # Core Web Vitals
            core_vitals = {
                'lcp': audit_results.get('largest-contentful-paint', {}),
                'fid': audit_results.get('first-input-delay', {}),
                'cls': audit_results.get('cumulative-layout-shift', {})
            }
            
            for vital_name, vital_data in core_vitals.items():
                if 'numericValue' in vital_data:
                    metrics[vital_name] = {
                        'value': vital_data['numericValue'],
                        'unit': vital_data.get('numericUnit', ''),
                        'displayValue': vital_data.get('displayValue', ''),
                        'rating': vital_data.get('rating', 'unknown')
                    }
            
            # Performance metrics
            perf_metrics = {
                'first-contentful-paint': audit_results.get('first-contentful-paint', {}),
                'speed-index': audit_results.get('speed-index', {}),
                'total-blocking-time': audit_results.get('total-blocking-time', {}),
                'cumulative-layout-shift': audit_results.get('cumulative-layout-shift', {})
            }
            
            for metric_name, metric_data in perf_metrics.items():
                if 'numericValue' in metric_data:
                    metrics[metric_name] = {
                        'value': metric_data['numericValue'],
                        'unit': metric_data.get('numericUnit', ''),
                        'displayValue': metric_data.get('displayValue', '')
                    }
            
            # Opportunities (optimization recommendations)
            opportunities = []
            for audit_name, audit_data in audit_results.items():
                if audit_data.get('details', {}).get('type') == 'opportunity':
                    opportunities.append({
                        'id': audit_name,
                        'title': audit_data.get('title', ''),
                        'description': audit_data.get('description', ''),
                        'savings': audit_data.get('details', {}).get('overallSavingsMs', 0),
                        'savings_bytes': audit_data.get('details', {}).get('overallSavingsBytes', 0)
                    })

            # Real-user field data (CrUX)
            field_data = self._parse_field_data(data.get('loadingExperience', {}))
            origin_field_data = self._parse_field_data(data.get('originLoadingExperience', {}))

            report_url = f"https://pagespeed.web.dev/analysis?url={quote_plus(url)}&form_factor={strategy}"
            
            # User experience signals
            page_experience = lighthouse.get('categories', {}).get('performance', {})
            
            return {
                'url': url,
                'strategy': strategy,
                'timestamp': datetime.utcnow().isoformat(),
                'success': True,
                'scores': scores,
                'score_details': score_details,
                'metrics': metrics,
                'opportunities': opportunities[:5],  # Top 5 opportunities
                'field_data': field_data,
                'origin_field_data': origin_field_data,
                'report_url': report_url,
                'page_experience': {
                    'score': page_experience.get('score', 0) * 100,
                    'description': page_experience.get('description', '')
                },
                'raw_data': data  # Keep raw data for advanced analysis
            }
            
        except Exception as e:
            logger.error(f"Error parsing PageSpeed results: {e}")
            return {
                'url': url,
                'strategy': strategy,
                'error': str(e),
                'success': False
            }

    def _parse_field_data(self, field_source: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CrUX real-user field data from PageSpeed response."""
        metrics = {}
        source_metrics = field_source.get('metrics', {}) if field_source else {}

        for metric_id, metric_value in source_metrics.items():
            metrics[metric_id] = {
                'percentile': metric_value.get('percentile'),
                'category': metric_value.get('category', 'N/A'),
                'distributions': metric_value.get('distributions', []),
            }

        return {
            'overall_category': field_source.get('overall_category', 'N/A') if field_source else 'N/A',
            'initial_url': field_source.get('initial_url', ''),
            'metrics': metrics,
        }
    
    def analyze_domain(self, domain: str, strategies: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze both mobile and desktop versions of a domain.
        
        Args:
            domain: Domain to analyze
            strategies: List of strategies ('mobile', 'desktop')
            
        Returns:
            Results for both strategies
        """
        if not strategies:
            strategies = ['mobile', 'desktop']
        
        results = {
            'domain': domain,
            'timestamp': datetime.utcnow().isoformat(),
            'analyses': {}
        }
        
        url = f"https://{domain}" if not domain.startswith('http') else domain
        
        for strategy in strategies:
            results['analyses'][strategy] = self.analyze_page(url, strategy=strategy)
        
        return results
    
    def get_score_grade(self, score: float) -> str:
        """
        Convert numeric score (0-100) to letter grade.
        
        Args:
            score: Numeric score (0-100)
            
        Returns:
            Letter grade (A+, A, B, C, D, F)
        """
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'
    
    def get_score_color(self, score: float) -> str:
        """
        Get color code for score visualization.
        
        Args:
            score: Numeric score (0-100)
            
        Returns:
            Bootstrap color class
        """
        if score >= 90:
            return 'success'  # Green
        elif score >= 70:
            return 'warning'  # Orange
        else:
            return 'danger'  # Red
    
    @staticmethod
    def format_time(milliseconds: float) -> str:
        """
        Format milliseconds to readable time string.
        
        Args:
            milliseconds: Time in milliseconds
            
        Returns:
            Formatted time string
        """
        if milliseconds < 1000:
            return f"{milliseconds:.0f}ms"
        else:
            return f"{milliseconds / 1000:.2f}s"


class PageSpeedCache:
    """
    Simple in-memory cache for PageSpeed results with expiration.
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time to live for cached entries (default: 1 hour)
        """
        self.cache: Dict[str, Dict] = {}
        self.ttl = ttl_seconds
    
    def get(self, url: str) -> Optional[Dict]:
        """Get cached result for URL."""
        if url in self.cache:
            entry = self.cache[url]
            if datetime.utcnow().timestamp() - entry['timestamp'] < self.ttl:
                return entry['data']
            else:
                del self.cache[url]
        return None
    
    def set(self, url: str, data: Dict) -> None:
        """Cache result for URL."""
        self.cache[url] = {
            'data': data,
            'timestamp': datetime.utcnow().timestamp()
        }
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()


# Global cache instance
_pagespeed_cache = PageSpeedCache()


def analyze_url_cached(
    url: str,
    strategy: str = 'mobile',
    api_key: Optional[str] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Analyze URL with optional caching.
    
    Args:
        url: URL to analyze
        strategy: 'mobile' or 'desktop'
        api_key: Google API key
        use_cache: Whether to use cached results
        
    Returns:
        Analysis results
    """
    cache_key = f"{url}:{strategy}"
    
    if use_cache:
        cached = _pagespeed_cache.get(cache_key)
        if cached:
            logger.info(f"Using cached PageSpeed result for {url}")
            return cached
    
    analyzer = PageSpeedAnalyzer(api_key=api_key)
    result = analyzer.analyze_page(url, strategy=strategy)
    
    if result.get('success'):
        _pagespeed_cache.set(cache_key, result)
    
    return result
