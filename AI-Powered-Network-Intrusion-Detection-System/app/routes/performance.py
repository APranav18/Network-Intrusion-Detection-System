"""
Performance Monitoring Routes
=============================
Track web application performance using Google PageSpeed Insights.
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required
from datetime import datetime
import logging

from app import db
from utils.pagespeed import PageSpeedAnalyzer, analyze_url_cached

logger = logging.getLogger(__name__)

performance_bp = Blueprint('performance', __name__, url_prefix='/performance')


@performance_bp.route('/')
@login_required
def performance_dashboard():
    """Performance monitoring dashboard."""
    return render_template('performance.html')


@performance_bp.route('/analyze', methods=['POST'])
@login_required
def analyze_performance():
    """
    Analyze web page performance.
    
    Request JSON:
    {
        "url": "https://example.com",
        "strategy": "mobile",
        "use_cache": true
    }
    """
    data = request.get_json() or {}
    url = data.get('url')
    strategy = data.get('strategy', 'mobile')
    use_cache = data.get('use_cache', True)
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Ensure URL has scheme
    if not url.startswith('http'):
        url = f'https://{url}'
    
    try:
        # Get API key from config
        api_key = current_app.config.get('GOOGLE_PAGESPEED_API_KEY') or \
                  request.environ.get('GOOGLE_PAGESPEED_API_KEY')
        
        result = analyze_url_cached(
            url,
            strategy=strategy,
            api_key=api_key,
            use_cache=use_cache
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Performance analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/analyze-both', methods=['POST'])
@login_required
def analyze_both_strategies():
    """
    Analyze both mobile and desktop performance.
    
    Request JSON:
    {
        "url": "https://example.com",
        "use_cache": true
    }
    """
    data = request.get_json() or {}
    url = data.get('url')
    use_cache = data.get('use_cache', True)
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    if not url.startswith('http'):
        url = f'https://{url}'
    
    try:
        api_key = current_app.config.get('GOOGLE_PAGESPEED_API_KEY')
        
        results = {
            'url': url,
            'timestamp': datetime.utcnow().isoformat(),
            'mobile': analyze_url_cached(url, strategy='mobile', api_key=api_key, use_cache=use_cache),
            'desktop': analyze_url_cached(url, strategy='desktop', api_key=api_key, use_cache=use_cache)
        }
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Dual strategy analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/app-analysis')
@login_required
def app_performance():
    """
    Analyze this application's own performance.
    Analyzes http://127.0.0.1:5000/dashboard
    """
    try:
        # Note: This will only work if the app is accessible externally
        # For localhost development, use the manual URL input instead
        app_url = request.host_url.rstrip('/') + '/dashboard'
        
        api_key = current_app.config.get('GOOGLE_PAGESPEED_API_KEY')
        analyzer = PageSpeedAnalyzer(api_key=api_key)
        
        result = analyzer.analyze_page(app_url, strategy='mobile')
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"App self-analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/insights/<category>')
@login_required
def performance_insights(category):
    """
    Get performance optimization insights for a category.
    
    Categories: performance, accessibility, best-practices, seo, pwa
    """
    insights = {
        'performance': {
            'title': 'Performance Optimization',
            'tips': [
                'Minimize render-blocking resources',
                'Optimize images and videos',
                'Enable compression (gzip/brotli)',
                'Use CDN for static assets',
                'Implement caching strategies',
                'Minify CSS, JavaScript, and HTML',
                'Remove unused CSS and JavaScript',
                'Optimize fonts and reduce requests',
                'Defer non-critical JavaScript',
                'Optimize above-the-fold content'
            ]
        },
        'accessibility': {
            'title': 'Accessibility Best Practices',
            'tips': [
                'Use semantic HTML elements',
                'Ensure proper color contrast ratios',
                'Add alt text to all images',
                'Use proper heading hierarchy (h1-h6)',
                'Provide keyboard navigation',
                'Add ARIA labels where appropriate',
                'Test with screen readers',
                'Ensure form labels are associated',
                'Provide transcripts for videos',
                'Use descriptive link text'
            ]
        },
        'best-practices': {
            'title': 'Web Best Practices',
            'tips': [
                'Use HTTPS protocol',
                'Avoid deprecated APIs',
                'Use modern browser APIs',
                'Implement proper error handling',
                'Keep dependencies updated',
                'Use responsive images',
                'Set viewport meta tag',
                'Avoid console errors and warnings',
                'Use valid HTML markup',
                'Implement security headers'
            ]
        },
        'seo': {
            'title': 'SEO Optimization',
            'tips': [
                'Add descriptive meta tags',
                'Use descriptive page titles',
                'Optimize for mobile',
                'Implement structured data (JSON-LD)',
                'Use descriptive URLs',
                'Implement internal linking',
                'Add robots.txt file',
                'Create XML sitemap',
                'Use canonical URLs',
                'Monitor crawl errors'
            ]
        },
        'pwa': {
            'title': 'Progressive Web App',
            'tips': [
                'Add web app manifest',
                'Implement service worker',
                'Enable offline functionality',
                'Use HTTPS',
                'Design mobile-first',
                'Add app shortcuts',
                'Set display mode (standalone)',
                'Use theme color',
                'Implement app icons',
                'Handle installation prompts'
            ]
        }
    }
    
    if category not in insights:
        return jsonify({'error': 'Invalid category'}), 404
    
    return jsonify(insights[category])


@performance_bp.route('/metrics-guide')
@login_required
def metrics_guide():
    """Get explanation of key Web Vitals metrics."""
    return jsonify({
        'core_web_vitals': {
            'LCP': {
                'name': 'Largest Contentful Paint',
                'description': 'Measures loading performance. Good: < 2.5s',
                'importance': 'Indicates how quickly main content is visible'
            },
            'INP': {
                'name': 'Interaction to Next Paint',
                'description': 'Measures interactivity. Good: < 200ms',
                'importance': 'Indicates responsiveness to user interactions'
            },
            'CLS': {
                'name': 'Cumulative Layout Shift',
                'description': 'Measures visual stability. Good: < 0.1',
                'importance': 'Indicates how much layout shifts unexpectedly'
            }
        },
        'other_metrics': {
            'FCP': {
                'name': 'First Contentful Paint',
                'description': 'Time when first content appears',
                'good': '< 1.8s'
            },
            'Speed Index': {
                'name': 'Speed Index',
                'description': 'How quickly visible content is rendered',
                'good': '< 3.4s'
            },
            'TTI': {
                'name': 'Time to Interactive',
                'description': 'When page is fully interactive',
                'good': '< 3.8s'
            },
            'TBT': {
                'name': 'Total Blocking Time',
                'description': 'Total time when main thread is blocked',
                'good': '< 200ms'
            }
        }
    })
