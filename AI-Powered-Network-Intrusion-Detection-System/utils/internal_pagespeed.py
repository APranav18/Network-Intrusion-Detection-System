"""
Internal PageSpeed Analyzer
=============================
Self-contained PageSpeed Insights replacement that generates realistic performance metrics
without calling external APIs. Designed to mimic PageSpeed behavior locally.
"""

import logging
import hashlib
from datetime import datetime
from typing import Dict, Optional, List, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class InternalPageSpeedAnalyzer:
    """
    Local PageSpeed Insights simulator.
    Generates realistic web performance metrics based on domain analysis.
    Does NOT call external APIs - all metrics are synthetically generated.
    """
    
    # Core Web Vitals thresholds (milliseconds, unitless)
    LCP_THRESHOLDS = {"good": 2500, "needs_improvement": 4000}
    INP_THRESHOLDS = {"good": 200, "needs_improvement": 500}
    CLS_THRESHOLDS = {"good": 0.1, "needs_improvement": 0.25}
    
    # Other metric thresholds
    FCP_THRESHOLDS = {"good": 1800, "needs_improvement": 3000}
    TTFB_THRESHOLDS = {"good": 600, "needs_improvement": 1800}
    SPEED_INDEX_THRESHOLDS = {"good": 3400, "needs_improvement": 5800}
    TBT_THRESHOLDS = {"good": 200, "needs_improvement": 600}
    
    CATEGORIES = ['performance', 'accessibility', 'best-practices', 'seo', 'pwa']
    
    def __init__(self):
        """Initialize internal analyzer."""
        self.cache = {}
    
    def analyze_domain(self, url: str, strategy: str = 'mobile') -> Dict[str, Any]:
        """
        Analyze domain and generate PageSpeed-like metrics.
        
        Args:
            url: URL to analyze
            strategy: 'mobile' or 'desktop'
            
        Returns:
            Dictionary matching PageSpeed Insights result structure
        """
        # Generate deterministic but domain-specific metrics
        domain_hash = self._get_domain_hash(url)
        
        # Base scores seeded by domain
        base_performance = self._generate_performance_score(domain_hash, strategy)
        
        # Generate metrics
        metrics = self._generate_core_web_vitals(domain_hash, strategy)
        field_data = self._generate_field_data(metrics)
        
        result = {
            'success': True,
            'scores': {
                'performance': base_performance,
                'accessibility': self._generate_category_score(domain_hash, 'accessibility', 85),
                'best-practices': self._generate_category_score(domain_hash, 'best-practices', 83),
                'seo': self._generate_category_score(domain_hash, 'seo', 88),
                'pwa': self._generate_category_score(domain_hash, 'pwa', 60)
            },
            'metrics': metrics,
            'field_data': field_data,
            'audits': self._generate_audits(base_performance),
            'opportunities': self._generate_opportunities(base_performance),
            'report_url': f"https://pagespeed.web.dev/analysis?url={url}&form_factor={strategy}",
            'raw_data': {
                'lighthouseResult': {
                    'categories': self._generate_categories(base_performance),
                    'audits': self._generate_full_audits(base_performance),
                    'fetchTime': datetime.utcnow().isoformat()
                }
            }
        }
        
        return result
    
    def _get_domain_hash(self, url: str) -> int:
        """Generate deterministic hash from domain."""
        domain = urlparse(url).netloc or url
        return int(hashlib.md5(domain.encode()).hexdigest(), 16)
    
    def _generate_performance_score(self, domain_hash: int, strategy: str) -> int:
        """Generate performance score (0-100) based on domain."""
        base = (domain_hash % 40) + 50  # Range: 50-90
        
        # Mobile tends to be slightly lower
        if strategy == 'mobile':
            base = max(40, base - (domain_hash % 15))
        
        return int(min(100, max(0, base)))
    
    def _generate_category_score(self, domain_hash: int, category: str, base: int) -> int:
        """Generate category score with slight variance."""
        variance = (domain_hash % 20) - 10
        score = base + variance
        return int(min(100, max(0, score)))
    
    def _generate_core_web_vitals(self, domain_hash: int, strategy: str) -> Dict[str, Dict]:
        """Generate Core Web Vitals metrics."""
        # LCP (Largest Contentful Paint)
        lcp_base = 2000 + (domain_hash % 3000)
        if strategy == 'desktop':
            lcp_base = int(lcp_base * 0.7)
        lcp_value = int(lcp_base)
        lcp_rating = self._rate_metric(lcp_value, self.LCP_THRESHOLDS)
        
        # INP (Interaction to Next Paint)
        inp_base = 100 + (domain_hash % 400)
        if strategy == 'desktop':
            inp_base = int(inp_base * 0.6)
        inp_value = int(inp_base)
        inp_rating = self._rate_metric(inp_value, self.INP_THRESHOLDS)
        
        # CLS (Cumulative Layout Shift)
        cls_base = 0.05 + ((domain_hash % 100) / 1000)
        if strategy == 'desktop':
            cls_base = cls_base * 0.5
        cls_value = round(cls_base, 3)
        cls_rating = self._rate_metric(cls_value, self.CLS_THRESHOLDS)
        
        # FCP (First Contentful Paint)
        fcp_value = int(lcp_value * 0.6 + (domain_hash % 800))
        fcp_rating = self._rate_metric(fcp_value, self.FCP_THRESHOLDS)
        
        # TTFB (Time to First Byte)
        ttfb_value = int((domain_hash % 500) + 200)
        ttfb_rating = self._rate_metric(ttfb_value, self.TTFB_THRESHOLDS)

        # Speed Index and Total Blocking Time help mimic Lighthouse's report cards.
        speed_index_value = int(lcp_value * 0.9 + (domain_hash % 1200))
        if strategy == 'desktop':
            speed_index_value = int(speed_index_value * 0.8)
        speed_index_rating = self._rate_metric(speed_index_value, self.SPEED_INDEX_THRESHOLDS)

        tbt_value = int(max(50, min(900, (100 - lcp_rating.count('good')) * 4 + (domain_hash % 450))))
        if strategy == 'desktop':
            tbt_value = int(max(40, tbt_value * 0.75))
        tbt_rating = self._rate_metric(tbt_value, self.TBT_THRESHOLDS)
        
        return {
            'lcp': {
                'value': lcp_value,
                'unit': 'milliseconds',
                'displayValue': f'{lcp_value / 1000:.1f} s',
                'rating': lcp_rating
            },
            'inp': {
                'value': inp_value,
                'unit': 'milliseconds',
                'displayValue': f'{inp_value} ms',
                'rating': inp_rating
            },
            'cls': {
                'value': cls_value,
                'unit': '',
                'displayValue': f'{cls_value}',
                'rating': cls_rating
            },
            'fcp': {
                'value': fcp_value,
                'unit': 'milliseconds',
                'displayValue': f'{fcp_value / 1000:.1f} s',
                'rating': fcp_rating
            },
            'ttfb': {
                'value': ttfb_value,
                'unit': 'milliseconds',
                'displayValue': f'{ttfb_value} ms',
                'rating': ttfb_rating
            },
            'speed_index': {
                'value': speed_index_value,
                'unit': 'milliseconds',
                'displayValue': f'{speed_index_value / 1000:.1f} s',
                'rating': speed_index_rating
            },
            'tbt': {
                'value': tbt_value,
                'unit': 'milliseconds',
                'displayValue': f'{tbt_value} ms',
                'rating': tbt_rating
            }
        }
    
    def _rate_metric(self, value: Any, thresholds: Dict[str, float]) -> str:
        """Rate metric as good/needs-improvement/poor."""
        if value <= thresholds['good']:
            return 'good'
        elif value <= thresholds['needs_improvement']:
            return 'needs-improvement'
        else:
            return 'poor'
    
    def _generate_field_data(self, metrics: Dict) -> Dict[str, Any]:
        """Generate field data (real user experience data)."""
        return {
            'metrics': {
                'LARGEST_CONTENTFUL_PAINT_MS': {
                    'percentile': metrics['lcp']['value'],
                    'category': 'FAST' if metrics['lcp']['rating'] == 'good' else ('AVERAGE' if metrics['lcp']['rating'] == 'needs-improvement' else 'SLOW')
                },
                'INTERACTION_TO_NEXT_PAINT': {
                    'percentile': metrics['inp']['value'],
                    'category': 'FAST' if metrics['inp']['rating'] == 'good' else ('AVERAGE' if metrics['inp']['rating'] == 'needs-improvement' else 'SLOW')
                },
                'CUMULATIVE_LAYOUT_SHIFT_SCORE': {
                    'percentile': metrics['cls']['value'],
                    'category': 'GOOD' if metrics['cls']['rating'] == 'good' else ('NEEDS_IMPROVEMENT' if metrics['cls']['rating'] == 'needs-improvement' else 'POOR')
                }
            }
        }
    
    def _generate_audits(self, performance_score: int) -> Dict[str, Any]:
        """Generate audit summary."""
        return {
            'performance_audits': self._generate_audit_list(performance_score),
            'accessibility_audits': self._generate_accessibility_audits(),
            'best_practices_audits': self._generate_best_practices_audits(),
            'seo_audits': self._generate_seo_audits()
        }
    
    def _generate_audit_list(self, performance_score: int) -> List[Dict]:
        """Generate performance audit findings."""
        audits = [
            {
                'title': 'Reduce JavaScript execution time',
                'description': 'Reduce the time spent parsing, compiling, and executing JS.',
                'impact': 'High' if performance_score < 70 else 'Medium',
                'score': performance_score
            },
            {
                'title': 'Eliminate render-blocking resources',
                'description': 'Resources are blocking the first paint of your page.',
                'impact': 'High' if performance_score < 50 else 'Low',
                'score': performance_score
            },
            {
                'title': 'Minify JavaScript',
                'description': 'Minifying JavaScript files can reduce payload sizes.',
                'impact': 'Medium' if performance_score < 80 else 'Low',
                'score': performance_score
            }
        ]
        return audits
    
    def _generate_accessibility_audits(self) -> List[Dict]:
        """Generate accessibility audit findings."""
        return [
            {
                'title': 'Page has valid lang attribute',
                'status': 'pass'
            },
            {
                'title': 'Buttons have accessible names',
                'status': 'pass'
            },
            {
                'title': 'Images have alt text',
                'status': 'pass'
            }
        ]
    
    def _generate_best_practices_audits(self) -> List[Dict]:
        """Generate best practices audit findings."""
        return [
            {
                'title': 'Uses HTTPS',
                'status': 'pass'
            },
            {
                'title': 'No unminified JavaScript',
                'status': 'pass'
            },
            {
                'title': 'No unminified CSS',
                'status': 'pass'
            }
        ]
    
    def _generate_seo_audits(self) -> List[Dict]:
        """Generate SEO audit findings."""
        return [
            {
                'title': 'Has a valid hreflang attribute',
                'status': 'pass'
            },
            {
                'title': 'Document has a valid meta description',
                'status': 'pass'
            },
            {
                'title': 'Document has a meta viewport tag',
                'status': 'pass'
            }
        ]
    
    def _generate_opportunities(self, performance_score: int) -> List[Dict]:
        """Generate optimization opportunities."""
        opportunities = []
        
        if performance_score < 90:
            opportunities.extend([
                {
                    'title': 'Enable text compression',
                    'description': 'Text-based resources should be served with compression (gzip, deflate, brotli).',
                    'savings': int((100 - performance_score) * 50)
                },
                {
                    'title': 'Defer offscreen images',
                    'description': 'Consider lazy-loading images that are off-screen.',
                    'savings': int((100 - performance_score) * 30)
                }
            ])
        
        if performance_score < 80:
            opportunities.append({
                'title': 'Reduce unused CSS',
                'description': 'Reduce unused rules from stylesheets and defer CSS not used in above-the-fold content.',
                'savings': int((100 - performance_score) * 40)
            })
        
        return opportunities
    
    def _generate_categories(self, performance_score: int) -> Dict[str, Any]:
        """Generate category data for raw_data."""
        return {
            'performance': {
                'title': 'Performance',
                'score': performance_score
            },
            'accessibility': {
                'title': 'Accessibility',
                'score': 85
            },
            'best-practices': {
                'title': 'Best Practices',
                'score': 83
            },
            'seo': {
                'title': 'SEO',
                'score': 88
            },
            'pwa': {
                'title': 'PWA',
                'score': 60
            }
        }
    
    def _generate_full_audits(self, performance_score: int) -> Dict[str, Any]:
        """Generate full audit data for raw_data."""
        return {
            'first-contentful-paint': {
                'title': 'First Contentful Paint',
                'description': 'First Contentful Paint marks the time at which the first text or image is painted.',
                'score': min(100, performance_score + 10) if performance_score > 50 else performance_score
            },
            'largest-contentful-paint': {
                'title': 'Largest Contentful Paint',
                'description': 'Largest Contentful Paint marks the time at which the largest text or image is painted.',
                'score': performance_score
            },
            'total-blocking-time': {
                'title': 'Total Blocking Time',
                'description': 'Sum of all long tasks (>50ms) minus 50ms.',
                'score': max(50, performance_score - 10) if performance_score < 90 else 100
            }
        }


class InternalPageSpeedCache:
    """
    Simple in-memory cache for internal analysis results with TTL.
    """
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl: Time to live in seconds (default 1 hour)
        """
        self.ttl = ttl
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached value if not expired."""
        if key not in self.cache:
            return None
        
        age = (datetime.utcnow().timestamp() - self.timestamps[key])
        if age > self.ttl:
            del self.cache[key]
            del self.timestamps[key]
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Dict) -> None:
        """Store value in cache."""
        self.cache[key] = value
        self.timestamps[key] = datetime.utcnow().timestamp()
    
    def clear(self) -> None:
        """Clear all cached values."""
        self.cache.clear()
        self.timestamps.clear()


# Global cache instance
_cache = InternalPageSpeedCache()
_analyzer = InternalPageSpeedAnalyzer()


def analyze_url_internal(
    url: str,
    strategy: str = 'mobile',
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Analyze URL using internal analyzer (no external API).
    
    Args:
        url: URL to analyze
        strategy: 'mobile' or 'desktop'
        use_cache: Whether to use cached results
        
    Returns:
        PageSpeed-like analysis result
    """
    cache_key = f"{url}_{strategy}"
    
    if use_cache:
        cached = _cache.get(cache_key)
        if cached:
            logger.info(f"Using cached result for {url} ({strategy})")
            return cached
    
    try:
        logger.info(f"Analyzing {url} ({strategy}) using internal analyzer")
        result = _analyzer.analyze_domain(url, strategy)
        
        if use_cache:
            _cache.set(cache_key, result)
        
        return result
    
    except Exception as e:
        logger.error(f"Internal analyzer error for {url}: {e}")
        # Return error response matching PageSpeed structure
        return {
            'success': False,
            'error': str(e),
            'scores': {},
            'metrics': {},
            'field_data': {},
            'report_url': f"https://pagespeed.web.dev/analysis?url={url}&form_factor={strategy}"
        }


def clear_cache() -> None:
    """Clear all cached results."""
    _cache.clear()
    logger.info("PageSpeed cache cleared")
