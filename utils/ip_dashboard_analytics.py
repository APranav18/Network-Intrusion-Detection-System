"""
IP Analytics for Dashboard
===========================
IP detection analysis and visualization for dashboard widgets.
"""

from typing import Dict, List, Any, Tuple
from datetime import datetime
from utils.ip_detector import IPValidator, analyze_ip
import logging

logger = logging.getLogger(__name__)


class IPDashboardAnalytics:
    """Analyze IPs for dashboard display."""
    
    def __init__(self):
        self.analyzed_ips = {}
        self.ip_history = []
    
    def analyze_and_store(self, ip: str) -> Dict[str, Any]:
        """
        Analyze IP and store for dashboard display.
        
        Args:
            ip: IP address to analyze
            
        Returns:
            Analysis result
        """
        result = analyze_ip(ip, use_cache=True)
        
        if result.get('success'):
            self.analyzed_ips[ip] = result
            self.ip_history.append({
                'ip': ip,
                'timestamp': datetime.utcnow().isoformat(),
                'result': result
            })
        
        return result
    
    def get_ip_statistics(self) -> Dict[str, Any]:
        """
        Get overall IP statistics for dashboard.
        
        Returns:
            Statistics dictionary
        """
        if not self.analyzed_ips:
            return {
                'total_ips': 0,
                'public_ips': 0,
                'private_ips': 0,
                'reserved_ips': 0,
                'countries': [],
                'top_isps': [],
                'type_distribution': {}
            }
        
        stats = {
            'total_ips': len(self.analyzed_ips),
            'public_ips': 0,
            'private_ips': 0,
            'reserved_ips': 0,
            'countries': {},
            'isps': {},
            'type_distribution': {'Public': 0, 'Private': 0, 'Reserved': 0}
        }
        
        for ip, data in self.analyzed_ips.items():
            validation = data.get('validation', {})
            classification = data.get('classification', {})
            geo = data.get('geolocation', {})
            
            # Count IP types
            if validation.get('is_private'):
                stats['private_ips'] += 1
                stats['type_distribution']['Private'] += 1
            elif validation.get('is_reserved'):
                stats['reserved_ips'] += 1
                stats['type_distribution']['Reserved'] += 1
            else:
                stats['public_ips'] += 1
                stats['type_distribution']['Public'] += 1
            
            # Collect countries
            if geo.get('country'):
                country = geo['country']
                stats['countries'][country] = stats['countries'].get(country, 0) + 1
            
            # Collect ISPs
            if geo.get('isp'):
                isp = geo['isp']
                stats['isps'][isp] = stats['isps'].get(isp, 0) + 1
        
        # Get top countries
        top_countries = sorted(
            stats['countries'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Get top ISPs
        top_isps = sorted(
            stats['isps'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_ips': stats['total_ips'],
            'public_ips': stats['public_ips'],
            'private_ips': stats['private_ips'],
            'reserved_ips': stats['reserved_ips'],
            'countries': dict(top_countries),
            'top_isps': dict(top_isps),
            'type_distribution': stats['type_distribution']
        }
    
    def get_geolocation_map_data(self) -> List[Dict[str, Any]]:
        """
        Get geolocation data for map visualization.
        
        Returns:
            List of coordinates and data for map
        """
        map_data = []
        
        for ip, data in self.analyzed_ips.items():
            geo = data.get('geolocation', {})
            
            if geo.get('latitude') and geo.get('longitude'):
                map_data.append({
                    'ip': ip,
                    'lat': geo['latitude'],
                    'lng': geo['longitude'],
                    'country': geo.get('country', 'Unknown'),
                    'city': geo.get('city', 'Unknown'),
                    'isp': geo.get('isp', 'Unknown'),
                    'type': 'public' if not data.get('validation', {}).get('is_private') else 'private'
                })
        
        return map_data
    
    def get_risk_distribution(self) -> Dict[str, int]:
        """
        Get risk distribution across analyzed IPs.
        
        Returns:
            Risk level distribution
        """
        risk_dist = {
            'low': 0,
            'medium': 0,
            'high': 0,
            'unknown': 0
        }
        
        for ip, data in self.analyzed_ips.items():
            classification = data.get('classification', {})
            risk_level = classification.get('risk_level', 'unknown')
            risk_dist[risk_level] = risk_dist.get(risk_level, 0) + 1
        
        return risk_dist
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recently analyzed IPs.
        
        Args:
            limit: Number of recent items to return
            
        Returns:
            List of recent IP analyses
        """
        return self.ip_history[-limit:]
    
    def get_ip_comparison_chart_data(self) -> Dict[str, Any]:
        """
        Get data for IP type comparison chart.
        
        Returns:
            Chart-ready data
        """
        stats = self.get_ip_statistics()
        type_dist = stats['type_distribution']
        
        return {
            'labels': list(type_dist.keys()),
            'datasets': [{
                'label': 'IP Count by Type',
                'data': list(type_dist.values()),
                'backgroundColor': [
                    '#28a745',  # Public - Green
                    '#ffc107',  # Private - Yellow
                    '#dc3545'   # Reserved - Red
                ],
                'borderColor': ['#1e7e34', '#e0a800', '#bb2d3b'],
                'borderWidth': 2
            }]
        }
    
    def get_country_distribution_chart(self) -> Dict[str, Any]:
        """
        Get data for country distribution chart.
        
        Returns:
            Chart-ready data
        """
        stats = self.get_ip_statistics()
        countries = stats['countries']
        
        return {
            'labels': list(countries.keys()),
            'datasets': [{
                'label': 'IPs by Country',
                'data': list(countries.values()),
                'backgroundColor': [
                    '#3b82f6',
                    '#8b5cf6',
                    '#ec4899',
                    '#f97316',
                    '#eab308'
                ],
                'borderColor': '#fff',
                'borderWidth': 1
            }]
        }


# Global analytics instance
_ip_analytics = IPDashboardAnalytics()


def get_ip_dashboard_data() -> Dict[str, Any]:
    """Get all IP analytics for dashboard."""
    return {
        'statistics': _ip_analytics.get_ip_statistics(),
        'type_chart': _ip_analytics.get_ip_comparison_chart_data(),
        'country_chart': _ip_analytics.get_country_distribution_chart(),
        'risk_distribution': _ip_analytics.get_risk_distribution(),
        'map_data': _ip_analytics.get_geolocation_map_data(),
        'recent_analyses': _ip_analytics.get_recent_analyses(5)
    }


def analyze_and_store_ip(ip: str) -> Dict[str, Any]:
    """Analyze IP and store for dashboard display."""
    return _ip_analytics.analyze_and_store(ip)


def get_analytics_instance() -> IPDashboardAnalytics:
    """Get the global analytics instance."""
    return _ip_analytics
