# PageSpeed Insights Integration Guide

## Overview

The AI-NIDS application now includes Google PageSpeed Insights integration for monitoring and analyzing web performance metrics. This feature allows you to:

- 🚀 Analyze web page performance (mobile & desktop)
- 📊 Track Core Web Vitals (LCP, FID, CLS)
- 💡 Get optimization recommendations
- 🔍 Monitor third-party website performance
- 💾 Cache results to reduce API calls

## Features

### Performance Analysis
- **Mobile & Desktop Analysis**: Analyze pages on both mobile and desktop strategies
- **Core Web Vitals**: Track Largest Contentful Paint (LCP), First Input Delay (FID), and Cumulative Layout Shift (CLS)
- **Performance Scoring**: Get scores for Performance, Accessibility, Best Practices, SEO, and PWA
- **Optimization Opportunities**: Get specific recommendations to improve performance

### Dashboard Integration
- New **Performance** page accessible from the main navigation
- Visual score cards with color-coded grades (A+ to F)
- Detailed metrics breakdown
- Optimization opportunities list
- Mobile/Desktop comparison

## Getting Started

### 1. Access the Performance Dashboard

Navigate to: **Performance** menu item in the sidebar, or directly at:
```
http://127.0.0.1:5000/performance/
```

### 2. Analyze a Website

1. Enter a URL (with or without https://)
2. Choose analysis strategy (mobile or desktop)
3. Optionally enable caching (1-hour TTL)
4. Click "Analyze Single" or "Analyze Both"

**Note**: Only public URLs can be analyzed. For local development:
- Use an external tunnel service like ngrok
- Or analyze a publicly deployed version of your app

### 3. Set Up Google API Key (Optional but Recommended)

Get increased rate limits by using a Google API key:

1. **Get Your API Key**:
   - Go to: https://developers.google.com/speed/docs/insights/v5/get-started
   - Create a Google Cloud project
   - Enable the "PageSpeed Insights API"
   - Create an API key

2. **Configure Your App**:

   **Option A - Environment Variable**:
   ```bash
   # Linux/Mac
   export GOOGLE_PAGESPEED_API_KEY="your-api-key-here"
   
   # Windows PowerShell
   $env:GOOGLE_PAGESPEED_API_KEY="your-api-key-here"
   
   # Windows CMD
   set GOOGLE_PAGESPEED_API_KEY=your-api-key-here
   ```

   **Option B - Configuration File**:
   Add to `config.py`:
   ```python
   class DevelopmentConfig(Config):
       GOOGLE_PAGESPEED_API_KEY = 'your-api-key-here'
   ```

   **Option C - .env File**:
   Create a `.env` file and use python-dotenv (already installed):
   ```
   GOOGLE_PAGESPEED_API_KEY=your-api-key-here
   ```

3. **Restart the Application**:
   ```bash
   python run.py
   ```

## API Endpoints

### Analyze Single URL

**Endpoint**: `POST /performance/analyze`

**Request Body**:
```json
{
    "url": "https://example.com",
    "strategy": "mobile",
    "use_cache": true
}
```

**Response**:
```json
{
    "url": "https://example.com",
    "strategy": "mobile",
    "timestamp": "2024-01-15T10:30:00",
    "success": true,
    "scores": {
        "performance": 85,
        "accessibility": 92,
        "best-practices": 88,
        "seo": 95,
        "pwa": 60
    },
    "metrics": {
        "lcp": {
            "value": 2100,
            "unit": "milliseconds",
            "displayValue": "2.1 s",
            "rating": "good"
        },
        ...
    },
    "opportunities": [
        {
            "id": "unused-css",
            "title": "Remove unused CSS",
            "description": "Remove unused rules from stylesheets",
            "savings": 50000
        },
        ...
    ]
}
```

### Analyze Both Strategies

**Endpoint**: `POST /performance/analyze-both`

**Request Body**:
```json
{
    "url": "https://example.com",
    "use_cache": true
}
```

**Response**: Combined results for both mobile and desktop

### Get Performance Insights

**Endpoint**: `GET /performance/insights/<category>`

**Categories**: `performance`, `accessibility`, `best-practices`, `seo`, `pwa`

**Response**: List of optimization tips for the category

### Get Metrics Guide

**Endpoint**: `GET /performance/metrics-guide`

**Response**: Explanation of all metrics and their targets

## Understanding the Results

### Performance Scores

| Grade | Score Range | Status |
|-------|-------------|--------|
| A+    | 90-100      | ✅ Excellent |
| A     | 80-89       | ✅ Good |
| B     | 70-79       | ⚠️ Fair |
| C     | 60-69       | ⚠️ Needs Improvement |
| D     | 50-59       | ❌ Poor |
| F     | 0-49        | ❌ Critical |

### Core Web Vitals

**Largest Contentful Paint (LCP)**
- Good: < 2.5s
- Measures: How fast the main content loads
- Impact: User perception of loading performance

**First Input Delay (FID)**
- Good: < 100ms
- Measures: Response time to user interaction
- Impact: Feel of interactivity

**Cumulative Layout Shift (CLS)**
- Good: < 0.1
- Measures: Visual stability
- Impact: User experience quality

### Optimization Opportunities

Each opportunity shows:
- **Title**: What to optimize
- **Description**: Explanation of the issue
- **Savings**: Estimated time savings in milliseconds

## Python Integration

### Using the PageSpeedAnalyzer Class

```python
from utils.pagespeed import PageSpeedAnalyzer, analyze_url_cached

# Create analyzer
analyzer = PageSpeedAnalyzer(api_key='your-api-key')

# Analyze a single URL
result = analyzer.analyze_page('https://example.com', strategy='mobile')

# Or use the cached convenience function
result = analyze_url_cached(
    'https://example.com',
    strategy='mobile',
    use_cache=True
)

# Access results
print(f"Performance Score: {result['scores']['performance']}")
print(f"Grade: {analyzer.get_score_grade(result['scores']['performance'])}")
print(f"LCP: {result['metrics']['lcp']['displayValue']}")

# Get optimization tips
for opportunity in result['opportunities']:
    print(f"{opportunity['title']}: {opportunity['savings']}ms savings")
```

### Analyzing Multiple Sites

```python
analyzer = PageSpeedAnalyzer()

sites = [
    'https://example1.com',
    'https://example2.com',
    'https://example3.com'
]

for site in sites:
    result = analyzer.analyze_domain(site, strategies=['mobile', 'desktop'])
    print(f"\n{site}:")
    for strategy, data in result['analyses'].items():
        print(f"  {strategy.title()}: {data['scores']['performance']}")
```

## Troubleshooting

### Common Issues

**Issue**: "Analysis failed" or "Error querying API"
- **Solution**: Ensure the URL is publicly accessible
- **Solution**: Check your internet connection
- **Solution**: If using API key, verify it's valid and enabled

**Issue**: "HTTP 403" with API key
- **Solution**: Ensure PageSpeed Insights API is enabled in Google Cloud Console
- **Solution**: Verify the API key has permissions for PageSpeed API

**Issue**: "URL not found" (404)
- **Solution**: Use complete URL with https://
- **Solution**: Ensure the domain is valid and accessible

**Issue**: Slow analysis times
- **Solution**: Results are cached for 1 hour by default
- **Solution**: Enable caching in the UI
- **Solution**: Use an API key for faster results

**Issue**: "Cannot analyze localhost"
- **Solution**: Use ngrok to tunnel localhost to public URL
  ```bash
  # Terminal 1: Start ngrok tunnel
  ngrok http 5000
  
  # Terminal 2: Analyze the ngrok URL
  # e.g., https://abc123.ngrok.io
  ```

## Rate Limits

**Without API Key**:
- 25 queries per day (per IP)

**With API Key**:
- 25,000 queries per day (most plans)
- Check your Google Cloud billing for exact limits

## Production Deployment

### Best Practices

1. **Always Use API Key**: Set GOOGLE_PAGESPEED_API_KEY environment variable
2. **Enable Caching**: Cache results to minimize API calls
3. **Monitor Usage**: Track API quota in Google Cloud Console
4. **Error Handling**: Implement fallback for API failures
5. **Rate Limiting**: Implement app-level rate limiting on the endpoint

### Environment Setup

```bash
# Production .env
FLASK_ENV=production
GOOGLE_PAGESPEED_API_KEY=your-production-api-key
```

## File Structure

```
app/
├── routes/
│   └── performance.py          # Performance monitoring routes
├── templates/
│   └── performance.html        # Dashboard UI
└── __init__.py                 # Updated to register performance blueprint

utils/
└── pagespeed.py               # PageSpeed Insights API wrapper
```

## API Reference

### PageSpeedAnalyzer Class

```python
class PageSpeedAnalyzer:
    def __init__(api_key: Optional[str] = None)
    def analyze_page(url: str, strategy: str = 'mobile', 
                    categories: Optional[List[str]] = None) -> Dict
    def analyze_domain(domain: str, strategies: Optional[List[str]] = None) -> Dict
    def get_score_grade(score: float) -> str
    def get_score_color(score: float) -> str
    @staticmethod
    def format_time(milliseconds: float) -> str
```

### PageSpeedCache Class

```python
class PageSpeedCache:
    def __init__(ttl_seconds: int = 3600)
    def get(url: str) -> Optional[Dict]
    def set(url: str, data: Dict) -> None
    def clear() -> None
```

## Resources

- [Google PageSpeed Insights API](https://developers.google.com/speed/docs/insights/v5/get-started)
- [Web Vitals Guide](https://web.dev/vitals/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [Web Performance Working Group](https://www.w3.org/webperf/)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the Google PageSpeed Insights documentation
3. Check browser console for JavaScript errors
4. Review Flask application logs

## Version History

### v1.0 (Current)
- Initial PageSpeed Insights integration
- Mobile & Desktop analysis
- Core Web Vitals tracking
- Optimization recommendations
- Result caching
- Dashboard UI
- API endpoints
