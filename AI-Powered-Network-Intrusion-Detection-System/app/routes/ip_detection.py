"""
IP Detection Routes
===================
Detect and analyze IP addresses with geolocation and threat intelligence.
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import logging

from app import db
from app.models.database import Alert, NetworkFlow, ThreatIntelligence
from utils.ip_detector import analyze_ip, validate_ip, IPValidator
from utils.internal_pagespeed import analyze_url_internal

logger = logging.getLogger(__name__)

ip_detection_bp = Blueprint('ip_detection', __name__, url_prefix='/ip-detection')


@ip_detection_bp.route('/')
@login_required
def ip_detection_dashboard():
    """IP detection and analysis dashboard."""
    # If an IP is provided as a query parameter, pass it to the template so
    # the page can auto-run a lookup client-side.
    initial_ip = (request.args.get('ip') or '').strip()
    return render_template('ip_detection.html', initial_ip=initial_ip)


@ip_detection_bp.route('/analyze', methods=['POST'])
@login_required
def analyze_ip_address():
    """
    Analyze a single IP address.
    
    Request JSON:
    {
        "ip": "8.8.8.8",
        "use_cache": true
    }
    """
    data = request.get_json() or {}
    ip = data.get('ip', '').strip()
    use_cache = data.get('use_cache', True)
    
    if not ip:
        return jsonify({'error': 'IP address is required'}), 400
    
    if not validate_ip(ip):
        return jsonify({
            'error': 'Invalid IP address',
            'code': 'INVALID_IP',
            'detail': ip
        }), 400
    
    try:
        result = analyze_ip(ip, use_cache=use_cache)
        return jsonify(result)
    except Exception as e:
        logger.error(f"IP analysis error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@ip_detection_bp.route('/analyze-public', methods=['POST'])
def analyze_ip_address_public():
    """
    Dev-only: Analyze a single IP address without authentication when app is running in debug mode.
    """
    if not current_app.debug:
        return jsonify({'error': 'Public analyze disabled', 'success': False}), 403

    data = request.get_json() or {}
    ip = data.get('ip', '').strip()
    use_cache = data.get('use_cache', True)

    if not ip:
        return jsonify({'error': 'IP address is required'}), 400

    if not validate_ip(ip):
        return jsonify({
            'error': 'Invalid IP address',
            'code': 'INVALID_IP',
            'detail': ip
        }), 400

    try:
        result = analyze_ip(ip, use_cache=use_cache)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Public IP analysis error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@ip_detection_bp.route('/seed-demo-data', methods=['POST'])
@login_required
def seed_demo_data():
    """Seed a small set of demo alerts and threat-intelligence records."""
    if getattr(current_user, 'role', None) != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    demo_alerts = [
        {
            'source_ip': '185.220.101.42',
            'destination_ip': '192.168.1.10',
            'attack_type': 'DDoS',
            'severity': 'critical',
            'confidence': 0.98,
            'risk_score': 0.97,
            'description': 'Demo DDoS traffic detected from known malicious source.',
            'protocol': 'TCP',
            'destination_port': 80,
        },
        {
            'source_ip': '45.33.32.156',
            'destination_ip': '192.168.1.25',
            'attack_type': 'Brute Force',
            'severity': 'high',
            'confidence': 0.94,
            'risk_score': 0.91,
            'description': 'Demo brute force attempts detected against SSH.',
            'protocol': 'TCP',
            'destination_port': 22,
        },
        {
            'source_ip': '89.248.165.12',
            'destination_ip': '192.168.1.50',
            'attack_type': 'Port Scan',
            'severity': 'medium',
            'confidence': 0.89,
            'risk_score': 0.84,
            'description': 'Demo port scan activity detected from external host.',
            'protocol': 'TCP',
            'destination_port': 21,
        },
    ]

    demo_threats = [
        {
            'ip_address': '185.220.101.42',
            'threat_type': 'malicious_host',
            'confidence': 0.97,
            'source': 'demo-seed',
            'is_blocked': True,
            'notes': 'Seeded demo entry for attack detection testing.',
        },
        {
            'ip_address': '45.33.32.156',
            'threat_type': 'brute_force_source',
            'confidence': 0.95,
            'source': 'demo-seed',
            'is_blocked': True,
            'notes': 'Seeded demo entry for attack detection testing.',
        },
        {
            'ip_address': '89.248.165.12',
            'threat_type': 'reconnaissance_source',
            'confidence': 0.90,
            'source': 'demo-seed',
            'is_blocked': False,
            'notes': 'Seeded demo entry for attack detection testing.',
        },
    ]

    demo_flows = [
        {
            'source_ip': '185.220.101.42',
            'destination_ip': '192.168.1.10',
            'source_port': 443,
            'destination_port': 80,
            'protocol': 'TCP',
            'duration': 0.2,
            'total_bytes': 120000,
            'packets_sent': 240,
            'packets_recv': 18,
            'bytes_sent': 118500,
            'bytes_recv': 1500,
            'label': 'DDoS',
            'predicted_label': 'DDoS',
            'is_anomaly': True,
        },
        {
            'source_ip': '45.33.32.156',
            'destination_ip': '192.168.1.25',
            'source_port': 51522,
            'destination_port': 22,
            'protocol': 'TCP',
            'duration': 6.8,
            'total_bytes': 4800,
            'packets_sent': 42,
            'packets_recv': 11,
            'bytes_sent': 3600,
            'bytes_recv': 1200,
            'label': 'Brute Force',
            'predicted_label': 'Brute Force',
            'is_anomaly': True,
        },
        {
            'source_ip': '89.248.165.12',
            'destination_ip': '192.168.1.50',
            'source_port': 33333,
            'destination_port': 21,
            'protocol': 'TCP',
            'duration': 1.4,
            'total_bytes': 2200,
            'packets_sent': 19,
            'packets_recv': 7,
            'bytes_sent': 1800,
            'bytes_recv': 400,
            'label': 'Port Scan',
            'predicted_label': 'Port Scan',
            'is_anomaly': True,
        },
    ]

    created = {'alerts': 0, 'threats': 0, 'flows': 0}

    try:
        now = datetime.utcnow()

        for index, item in enumerate(demo_alerts):
            exists = Alert.query.filter_by(
                source_ip=item['source_ip'],
                destination_ip=item['destination_ip'],
                attack_type=item['attack_type']
            ).first()
            if exists:
                continue

            alert = Alert(
                timestamp=now - timedelta(minutes=15 * (index + 1)),
                source_ip=item['source_ip'],
                destination_ip=item['destination_ip'],
                source_port=40000 + index,
                destination_port=item['destination_port'],
                protocol=item['protocol'],
                attack_type=item['attack_type'],
                severity=item['severity'],
                confidence=item['confidence'],
                risk_score=item['risk_score'],
                description=item['description'],
                model_used='demo-seed',
                acknowledged=True,
                acknowledged_by=current_user.id,
                acknowledged_at=now - timedelta(minutes=10 * (index + 1)),
                resolved=False,
                raw_data='{}'
            )
            db.session.add(alert)
            created['alerts'] += 1

        for item in demo_threats:
            exists = ThreatIntelligence.query.filter_by(ip_address=item['ip_address']).first()
            if exists:
                continue

            threat = ThreatIntelligence(
                ip_address=item['ip_address'],
                threat_type=item['threat_type'],
                confidence=item['confidence'],
                source=item['source'],
                first_seen=now - timedelta(days=7),
                last_seen=now,
                is_blocked=item['is_blocked'],
                notes=item['notes'],
                raw_data='{}'
            )
            db.session.add(threat)
            created['threats'] += 1

        for index, item in enumerate(demo_flows):
            exists = NetworkFlow.query.filter_by(
                source_ip=item['source_ip'],
                destination_ip=item['destination_ip'],
                source_port=item['source_port'],
                destination_port=item['destination_port']
            ).first()
            if exists:
                continue

            flow = NetworkFlow(
                timestamp=now - timedelta(minutes=5 * (index + 1)),
                source_ip=item['source_ip'],
                destination_ip=item['destination_ip'],
                source_port=item['source_port'],
                destination_port=item['destination_port'],
                protocol=item['protocol'],
                duration=item['duration'],
                total_bytes=item['total_bytes'],
                packets_sent=item['packets_sent'],
                packets_recv=item['packets_recv'],
                bytes_sent=item['bytes_sent'],
                bytes_recv=item['bytes_recv'],
                label=item['label'],
                predicted_label=item['predicted_label'],
                is_anomaly=item['is_anomaly'],
                raw_data='{}'
            )
            db.session.add(flow)
            created['flows'] += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Demo data seeded successfully.',
            'created': created,
            'sample_ips': ['185.220.101.42', '45.33.32.156', '89.248.165.12']
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Demo data seed failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ip_detection_bp.route('/validate', methods=['POST'])
@login_required
def validate_ip_address():
    """
    Validate if string is a valid IP address.
    
    Request JSON:
    {
        "ip": "8.8.8.8"
    }
    """
    data = request.get_json() or {}
    ip = data.get('ip', '').strip()
    
    if not ip:
        return jsonify({'error': 'ip is required'}), 400
    
    is_valid = validate_ip(ip)
    version = None
    
    if is_valid:
        if IPValidator.is_valid_ipv4(ip):
            version = 'IPv4'
        elif IPValidator.is_valid_ipv6(ip):
            version = 'IPv6'
    
    return jsonify({
        'ip': ip,
        'is_valid': is_valid,
        'version': version,
        'is_private': IPValidator.is_private_ip(ip) if is_valid else None,
        'is_reserved': IPValidator.is_reserved_ip(ip) if is_valid else None,
    })


@ip_detection_bp.route('/analyze-domain', methods=['POST'])
@login_required
def analyze_domain_detection():
    """
    Analyze domain using Google PageSpeed Insights (mobile + desktop).

    Request JSON:
    {
        "domain": "example.com",
        "api_key": "optional-google-pagespeed-api-key",
        "use_cache": true
    }
    """
    data = request.get_json() or {}
    domain = (data.get('domain') or '').strip()
    raw_api_key = (data.get('api_key') or '').strip()
    api_key = raw_api_key if raw_api_key and not raw_api_key.lower().startswith(('http://', 'https://')) and '/' not in raw_api_key else ''
    use_cache = data.get('use_cache', True)

    if not domain:
        return jsonify({'error': 'domain is required'}), 400

    url = domain if domain.startswith(('http://', 'https://')) else f'https://{domain}'

    try:
        # Use internal analyzer - no external API required
        mobile_result = analyze_url_internal(url, strategy='mobile', use_cache=use_cache)
        desktop_result = analyze_url_internal(url, strategy='desktop', use_cache=use_cache)

        valid_scores = []
        for result in (mobile_result, desktop_result):
            if result.get('success'):
                performance_score = result.get('scores', {}).get('performance')
                if performance_score is not None:
                    valid_scores.append(float(performance_score))

        aggregate_score = round(sum(valid_scores) / len(valid_scores)) if valid_scores else None
        score_spread = None
        if mobile_result.get('success') and desktop_result.get('success'):
            mobile_score = float(mobile_result.get('scores', {}).get('performance', 0))
            desktop_score = float(desktop_result.get('scores', {}).get('performance', 0))
            score_spread = round(abs(mobile_score - desktop_score), 1)

        return jsonify({
            'domain': domain,
            'url': url,
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'performance_score': aggregate_score,
                'score_spread': score_spread,
                'grade': _grade_pagespeed_score(aggregate_score) if aggregate_score is not None else 'N/A'
            },
            'mobile': mobile_result,
            'desktop': desktop_result
        })
    except Exception as e:
        logger.error(f"Domain PageSpeed analysis error: {e}")
        return jsonify({'error': str(e)}), 500


def _grade_pagespeed_score(score):
    if score is None:
        return 'N/A'
    if score >= 90:
        return 'A+'
    if score >= 80:
        return 'A'
    if score >= 70:
        return 'B'
    if score >= 60:
        return 'C'
    if score >= 50:
        return 'D'
    return 'F'


@ip_detection_bp.route('/info')
@login_required
def ip_info():
    """Get information about IP detection features."""
    return jsonify({
        'features': {
            'validation': 'Validate IPv4 and IPv6 addresses',
            'classification': 'Classify as public, private, or reserved',
            'reverse_lookup': 'Perform reverse DNS lookup',
            'attack_history': 'Check recorded alerts and threat intelligence for attack evidence',
            'batch_analysis': 'Analyze multiple IPs from text',
            'comparison': 'Compare multiple IPs side-by-side',
            'domain_detection': 'Analyze domain quality with Google PageSpeed (mobile + desktop)',
        },
        'supported_formats': [
            'Single IP: 8.8.8.8',
            'Multiple IPs space-separated: 8.8.8.8 1.1.1.1',
            'Multiple IPs newline-separated',
            'IPv4 and IPv6 mixed'
        ],
        'capabilities': {
            'ipv4': 'Full support',
            'ipv6': 'Full support',
            'private_ips': 'Detected (RFC 1918, RFC 4193)',
            'reserved_ips': 'Detected (multicast, broadcast)',
            'attack_history': 'Recorded alerts and threat intel lookup',
            'caching': '1000 entries max'
        }
    })
