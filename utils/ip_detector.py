"""
IP Address Detection & Analysis Module
======================================
Detect, validate, and analyze IP addresses with geolocation and threat intelligence.
"""

import re
import os
import pickle
import socket
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
import json
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sqlalchemy import func

logger = logging.getLogger(__name__)


class IPValidator:
    """Validate IP addresses (IPv4 and IPv6)."""
    
    IPV4_PATTERN = re.compile(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    )
    
    IPV6_PATTERN = re.compile(
        r'^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|'
        r'([0-9a-fA-F]{1,4}:){1,7}:|'
        r'([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|'
        r'([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|'
        r'([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|'
        r'([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|'
        r'([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|'
        r'[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|'
        r':((:[0-9a-fA-F]{1,4}){1,7}|:)|'
        r'fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|'
        r'::(ffff(:0{1,4}){0,1}:){0,1}'
        r'((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}'
        r'(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|'
        r'([0-9a-fA-F]{1,4}:){1,4}:'
        r'((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}'
        r'(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$'
    )
    
    @staticmethod
    def is_valid_ipv4(ip: str) -> bool:
        """Check if string is valid IPv4 address."""
        return bool(IPValidator.IPV4_PATTERN.match(ip))
    
    @staticmethod
    def is_valid_ipv6(ip: str) -> bool:
        """Check if string is valid IPv6 address."""
        return bool(IPValidator.IPV6_PATTERN.match(ip))
    
    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Check if string is valid IPv4 or IPv6 address."""
        return IPValidator.is_valid_ipv4(ip) or IPValidator.is_valid_ipv6(ip)
    
    @staticmethod
    def ip_version(ip: str) -> Optional[str]:
        """Return 'IPv4', 'IPv6', or None."""
        if IPValidator.is_valid_ipv4(ip):
            return 'IPv4'
        elif IPValidator.is_valid_ipv6(ip):
            return 'IPv6'
        return None
    
    @staticmethod
    def is_private_ip(ip: str) -> bool:
        """Check if IP is private (RFC 1918, RFC 4193, etc.)."""
        try:
            addr = socket.inet_aton(ip)
            first_octet = ord(addr[0:1])
            second_octet = ord(addr[1:2])
            
            # 10.0.0.0/8
            if first_octet == 10:
                return True
            # 172.16.0.0/12
            if first_octet == 172 and 16 <= second_octet <= 31:
                return True
            # 192.168.0.0/16
            if first_octet == 192 and second_octet == 168:
                return True
            # 127.0.0.0/8 (Loopback)
            if first_octet == 127:
                return True
            
            return False
        except:
            return False
    
    @staticmethod
    def is_reserved_ip(ip: str) -> bool:
        """Check if IP is reserved (multicast, broadcast, etc.)."""
        try:
            addr = socket.inet_aton(ip)
            first_octet = ord(addr[0:1])
            
            # 224.0.0.0/4 (Multicast)
            if 224 <= first_octet <= 239:
                return True
            # 240.0.0.0/4 (Reserved)
            if first_octet >= 240:
                return True
            # 0.0.0.0/8
            if first_octet == 0:
                return True
            
            return False
        except:
            return False


class ThreatIntelligenceLookup:
    """Enhanced threat intelligence from multiple sources."""
    
    # Reputation APIs
    REPUTATION_APIS = {
        'abuseipdb-free': 'https://api.abuseipdb.com/api/v2/check',  # Requires API key
        'otx': 'https://otx.alienvault.com/api/v1/pulses/subscribed',  # Requires API key
        'ip-quality-score': 'https://ipqualityscore.com/api/json/ip',  # Free tier available
    }
    
    # Known malicious IPs and patterns (local database for demo/testing)
    KNOWN_MALICIOUS = {
        '185.220.101.42': {'name': 'Tor Exit Node', 'threat_level': 'high', 'reasons': ['Tor Exit', 'Proxy']},
        '45.33.32.156': {'name': 'Linode Abuse Source', 'threat_level': 'medium', 'reasons': ['Historical abuse', 'Port scanning']},
        '89.248.165.12': {'name': 'VPN/Proxy Provider', 'threat_level': 'medium', 'reasons': ['Proxy service', 'Anonymization']},
        '192.241.238.16': {'name': 'Botnet C&C', 'threat_level': 'critical', 'reasons': ['Known botnet', 'Malware C&C']},
        '104.21.45.76': {'name': 'DDoS Source', 'threat_level': 'high', 'reasons': ['DDoS attacks', 'Amplification']},
        '1.1.1.1': {'name': 'Cloudflare DNS', 'threat_level': 'none', 'reasons': ['Trusted service']},
        '8.8.8.8': {'name': 'Google DNS', 'threat_level': 'none', 'reasons': ['Trusted service']},
        '1.0.0.1': {'name': 'Cloudflare DNS', 'threat_level': 'none', 'reasons': ['Trusted service']},
    }
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
    
    def check_reputation(self, ip: str) -> Dict[str, Any]:
        """Check IP reputation from known database."""
        if ip in self.KNOWN_MALICIOUS:
            info = self.KNOWN_MALICIOUS[ip]
            return {
                'found': True,
                'name': info['name'],
                'threat_level': info['threat_level'],
                'reasons': info['reasons'],
                'source': 'local_database'
            }
        
        # Try free IP quality score API
        try:
            return self._check_ip_quality_score(ip)
        except Exception:
            pass
        
        return {'found': False, 'source': 'none'}
    
    def _check_ip_quality_score(self, ip: str) -> Dict[str, Any]:
        """Free tier check from IP Quality Score."""
        try:
            url = f'https://ipqualityscore.com/api/json/ip/{ip}'
            params = {'strictness': 1}
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get('fraud_score', 0) >= 75:
                threat_level = 'critical'
            elif data.get('fraud_score', 0) >= 50:
                threat_level = 'high'
            elif data.get('fraud_score', 0) >= 25:
                threat_level = 'medium'
            else:
                threat_level = 'low'
            
            reasons = []
            if data.get('is_bot'):
                reasons.append('Bot detected')
            if data.get('is_vpn'):
                reasons.append('VPN/Proxy')
            if data.get('is_proxy'):
                reasons.append('Proxy detected')
            if data.get('recent_abuse'):
                reasons.append('Recent abuse')
            
            return {
                'found': True,
                'name': f"IP Quality Score Analysis",
                'threat_level': threat_level,
                'fraud_score': data.get('fraud_score', 0),
                'reasons': reasons or ['See reputation analysis'],
                'source': 'ipqualityscore'
            }
        except Exception as e:
            logger.debug(f"IP Quality Score lookup failed: {e}")
            return {'found': False, 'source': 'ipqualityscore', 'error': str(e)}


class IPGeolocation:
    """Geolocation lookup for IP addresses."""
    
    # Free GeoIP APIs
    APIS = {
        'ip-api': 'http://ip-api.com/json/{ip}',
        'ipinfo': 'https://ipinfo.io/{ip}/json',
        'geoip-db': 'https://geolite.maxmind.com/geoip/v2.1/city/{ip}',
    }
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
    
    def lookup(self, ip: str) -> Dict[str, Any]:
        """
        Lookup geolocation for IP address.
        
        Args:
            ip: IP address to lookup
            
        Returns:
            Dictionary with geolocation data
        """
        if not IPValidator.is_valid_ipv4(ip):
            return {'error': 'Invalid IPv4 address'}
        
        # Try ip-api.com first (most reliable free service)
        result = self._lookup_ip_api(ip)
        if result and 'error' not in result:
            return result
        
        # Fallback to ipinfo.io
        result = self._lookup_ipinfo(ip)
        if result and 'error' not in result:
            return result
        
        return {'error': 'Could not lookup geolocation'}
    
    def _lookup_ip_api(self, ip: str) -> Dict[str, Any]:
        """Lookup using ip-api.com API."""
        try:
            url = f'http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,region,regionName,lat,lon,org,as,isp,mobile,proxy,hosting,query'
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'success':
                return {
                    'ip': data.get('query'),
                    'country': data.get('country'),
                    'country_code': data.get('countryCode'),
                    'city': data.get('city'),
                    'region': data.get('regionName'),
                    'latitude': data.get('lat'),
                    'longitude': data.get('lon'),
                    'organization': data.get('org'),
                    'asn': data.get('as'),
                    'isp': data.get('isp'),
                    'mobile': data.get('mobile', False),
                    'proxy': data.get('proxy', False),
                    'hosting': data.get('hosting', False),
                    'source': 'ip-api.com'
                }
            else:
                return {'error': data.get('message', 'Lookup failed')}
        except Exception as e:
            logger.error(f"ip-api.com lookup failed: {e}")
            return {'error': str(e)}
    
    def _lookup_ipinfo(self, ip: str) -> Dict[str, Any]:
        """Lookup using ipinfo.io API."""
        try:
            url = f'https://ipinfo.io/{ip}/json'
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            loc = data.get('loc', '').split(',')
            
            return {
                'ip': data.get('ip'),
                'country': data.get('country'),
                'city': data.get('city'),
                'region': data.get('region'),
                'latitude': float(loc[0]) if loc[0] else None,
                'longitude': float(loc[1]) if len(loc) > 1 else None,
                'organization': data.get('org'),
                'timezone': data.get('timezone'),
                'source': 'ipinfo.io'
            }
        except Exception as e:
            logger.error(f"ipinfo.io lookup failed: {e}")
            return {'error': str(e)}


class RealtimeIPRiskModel:
    """Lightweight real-time IP reputation model."""

    MODEL_PATH = Path('models') / 'ip_realtime_model.pkl'

    BENIGN_REFERENCE_IPS = [
        '8.8.8.8',
        '1.1.1.1',
        '9.9.9.9',
        '20.77.81.72',
        '13.107.21.200',
        '151.101.1.69',
        '104.16.132.229',
        '52.95.110.1',
    ]

    MALICIOUS_REFERENCE_IPS = [
        '185.220.101.42',
        '45.33.32.156',
        '89.248.165.12',
    ]

    def __init__(self):
        self.model = None
        self.feature_names = [
            'is_private',
            'is_reserved',
            'is_ipv4',
            'geolocation_available',
            'proxy_flag',
            'hosting_flag',
            'mobile_flag',
            'reverse_dns_success',
            'source_alert_count',
            'destination_alert_count',
            'total_alert_count',
            'blocked_threat',
            'threat_confidence',
            'watchlist_flag',
            'hostname_present',
        ]
        self.model_ready = False
        self._load_model()

    def _load_model(self) -> bool:
        try:
            if not self.MODEL_PATH.exists():
                return False

            with self.MODEL_PATH.open('rb') as handle:
                payload = pickle.load(handle)

            if isinstance(payload, dict):
                self.model = payload.get('model')
                self.feature_names = payload.get('feature_names', self.feature_names)
            else:
                self.model = payload

            self.model_ready = self.model is not None
            return self.model_ready
        except Exception as e:
            logger.warning(f"Unable to load realtime IP model: {e}")
            self.model = None
            self.model_ready = False
            return False

    def ensure_trained(self, force: bool = False) -> bool:
        if self.model_ready and not force:
            return True

        if self._load_model() and not force:
            return True

        return self.train()

    def train(self) -> bool:
        try:
            from app.models.database import Alert, ThreatIntelligence
        except Exception as e:
            logger.warning(f"Realtime IP model training fallback only: {e}")
            Alert = None
            ThreatIntelligence = None

        samples: List[np.ndarray] = []
        labels: List[int] = []

        for ip in self.BENIGN_REFERENCE_IPS:
            context = self._build_context(ip, include_database=False)
            samples.append(self._feature_vector(ip, context))
            labels.append(0)

        for ip in self.MALICIOUS_REFERENCE_IPS:
            context = self._build_context(ip, include_database=False)
            context['blocked_threat'] = 1.0
            context['source_alert_count'] = max(context.get('source_alert_count', 0.0), 1.0)
            context['destination_alert_count'] = max(context.get('destination_alert_count', 0.0), 1.0)
            samples.append(self._feature_vector(ip, context))
            labels.append(1)

        if Alert is not None and ThreatIntelligence is not None:
            try:
                unique_ips = set()
                for alert in Alert.query.with_entities(Alert.source_ip, Alert.destination_ip).all():
                    if alert.source_ip:
                        unique_ips.add(alert.source_ip)
                    if alert.destination_ip:
                        unique_ips.add(alert.destination_ip)

                for threat in ThreatIntelligence.query.all():
                    if threat.ip_address:
                        unique_ips.add(threat.ip_address)

                for ip in unique_ips:
                    context = self._build_context(ip)
                    label = 1 if (
                        context.get('blocked_threat', 0.0) > 0.5 or
                        context.get('destination_alert_count', 0.0) > 0.0 or
                        context.get('total_alert_count', 0.0) > 0.0 or
                        context.get('threat_confidence', 0.0) >= 0.85
                    ) else 0
                    samples.append(self._feature_vector(ip, context))
                    labels.append(label)
            except Exception as e:
                logger.warning(f"Realtime IP model database training skipped: {e}")

        if len(samples) < 4 or len(set(labels)) < 2:
            logger.warning("Realtime IP model training skipped due to insufficient data")
            self.model = None
            self.model_ready = False
            return False

        classifier = RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            class_weight='balanced',
        )
        classifier.fit(np.asarray(samples, dtype=float), np.asarray(labels, dtype=int))
        self.model = classifier
        self.model_ready = True

        self.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with self.MODEL_PATH.open('wb') as handle:
            pickle.dump({
                'model': self.model,
                'feature_names': self.feature_names,
                'trained_at': datetime.utcnow().isoformat(),
            }, handle)

        logger.info(f"Trained realtime IP model with {len(samples)} samples")
        return True

    def _build_context(self, ip: str, include_database: bool = True) -> Dict[str, Any]:
        context = {
            'geolocation': {},
            'reverse_lookup': {'success': False, 'hostname': None},
            'source_alert_count': 0.0,
            'destination_alert_count': 0.0,
            'total_alert_count': 0.0,
            'blocked_threat': 0.0,
            'threat_confidence': 0.0,
            'watchlist_flag': 0.0,
        }

        if not include_database:
            return context

        try:
            from app.models.database import Alert, ThreatIntelligence

            context['source_alert_count'] = float(Alert.query.filter(Alert.source_ip == ip).count())
            context['destination_alert_count'] = float(Alert.query.filter(Alert.destination_ip == ip).count())
            context['total_alert_count'] = float(Alert.query.filter(
                (Alert.source_ip == ip) | (Alert.destination_ip == ip)
            ).count())

            threat_record = ThreatIntelligence.query.filter_by(ip_address=ip).first()
            if threat_record:
                context['watchlist_flag'] = 1.0
                context['threat_confidence'] = float(threat_record.confidence or 0.0)
                context['blocked_threat'] = 1.0 if threat_record.is_blocked else 0.0
        except Exception:
            pass

        return context

    def _feature_vector(self, ip: str, context: Optional[Dict[str, Any]] = None) -> np.ndarray:
        context = context or {}
        geolocation = context.get('geolocation') or {}
        reverse_lookup = context.get('reverse_lookup') or {}

        return np.asarray([
            float(IPValidator.is_private_ip(ip)),
            float(IPValidator.is_reserved_ip(ip)),
            float(IPValidator.is_valid_ipv4(ip)),
            float(not bool(geolocation.get('error')) and bool(geolocation)),
            float(bool(geolocation.get('proxy'))),
            float(bool(geolocation.get('hosting'))),
            float(bool(geolocation.get('mobile'))),
            float(reverse_lookup.get('success', False)),
            float(np.log1p(context.get('source_alert_count', 0.0))),
            float(np.log1p(context.get('destination_alert_count', 0.0))),
            float(np.log1p(context.get('total_alert_count', 0.0))),
            float(context.get('blocked_threat', 0.0)),
            float(context.get('threat_confidence', 0.0)),
            float(context.get('watchlist_flag', 0.0)),
            float(bool(reverse_lookup.get('hostname'))),
        ], dtype=float)

    def score(self, ip: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.ensure_trained()

        context = dict(context or {})
        if 'geolocation' not in context:
            context['geolocation'] = {}
        if 'reverse_lookup' not in context:
            context['reverse_lookup'] = {'success': False, 'hostname': None}

        features = self._feature_vector(ip, context).reshape(1, -1)

        if self.model is not None and hasattr(self.model, 'predict_proba'):
            probability = float(self.model.predict_proba(features)[0][1])
        else:
            probability = self._heuristic_probability(ip, context)

        if probability >= 0.80:
            status = 'attacked'
            status_label = 'AI-detected attack'
        elif probability >= 0.55:
            status = 'suspicious'
            status_label = 'AI-detected suspicious activity'
        else:
            status = 'no_known_attack'
            status_label = 'No known attack'

        evidence = []
        geolocation = context.get('geolocation') or {}
        reverse_lookup = context.get('reverse_lookup') or {}

        if IPValidator.is_private_ip(ip):
            evidence.append('private_ip')
        if IPValidator.is_reserved_ip(ip):
            evidence.append('reserved_ip')
        if geolocation.get('proxy'):
            evidence.append('proxy_flag')
        if geolocation.get('hosting'):
            evidence.append('hosting_flag')
        if not reverse_lookup.get('success'):
            evidence.append('reverse_dns_missing')
        if context.get('blocked_threat', 0.0) > 0.5:
            evidence.append('blocked_threat_intelligence')
        if context.get('total_alert_count', 0.0) > 0:
            evidence.append('historical_alerts')

        return {
            'available': True,
            'source': 'realtime_ai_model',
            'trained': self.model is not None,
            'status': status,
            'status_label': status_label,
            'attacked': status == 'attacked',
            'suspicious': status == 'suspicious',
            'probability': probability,
            'confidence': probability,
            'evidence': evidence,
        }

    def _heuristic_probability(self, ip: str, context: Dict[str, Any]) -> float:
        score = 0.12
        geolocation = context.get('geolocation') or {}
        reverse_lookup = context.get('reverse_lookup') or {}

        if IPValidator.is_private_ip(ip):
            score += 0.05
        if IPValidator.is_reserved_ip(ip):
            score += 0.05
        if geolocation.get('proxy'):
            score += 0.22
        if geolocation.get('hosting'):
            score += 0.18
        if geolocation.get('mobile'):
            score += 0.08
        if not reverse_lookup.get('success'):
            score += 0.12
        score += min(0.25, float(context.get('total_alert_count', 0.0)) * 0.08)
        if context.get('blocked_threat', 0.0) > 0.5:
            score += 0.35
        score += min(0.10, float(context.get('threat_confidence', 0.0)) * 0.10)
        return max(0.0, min(1.0, score))


class IPAnalyzer:
    """Comprehensive IP address analysis."""
    
    def __init__(self):
        self.validator = IPValidator()
        self.geolocation = IPGeolocation()
        self.realtime_model = RealtimeIPRiskModel()
        self.threat_intel = ThreatIntelligenceLookup()
    
    def analyze(self, ip: str) -> Dict[str, Any]:
        """
        Analyze IP address comprehensively.
        
        Args:
            ip: IP address to analyze
            
        Returns:
            Complete analysis dictionary
        """
        if not self.validator.is_valid_ip(ip):
            return {
                'success': False,
                'error': f'Invalid IP address: {ip}'
            }
        
        analysis = {
            'success': True,
            'ip': ip,
            'timestamp': datetime.utcnow().isoformat(),
            'validation': self._validate_ip(ip),
            'geolocation': self.geolocation.lookup(ip) if self.validator.is_valid_ipv4(ip) else {},
            'classification': self._classify_ip(ip),
            'reverse_lookup': self._reverse_lookup(ip),
            'threat_intelligence': self.threat_intel.check_reputation(ip),  # NEW: Threat intel lookup
        }

        analysis['attack_assessment'] = self._assess_attack_history(
            ip,
            geolocation=analysis['geolocation'],
            reverse_lookup=analysis['reverse_lookup'],
            threat_intel=analysis['threat_intelligence']  # Pass threat intel data
        )
        
        # NEW: Add a comprehensive threat score
        analysis['overall_threat_score'] = self._calculate_threat_score(analysis)
        
        return analysis
    
    def _calculate_threat_score(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall threat score from all available data."""
        score = 0.0
        factors = []
        
        # Factor 1: Threat intelligence
        threat_intel = analysis.get('threat_intelligence', {})
        if threat_intel.get('found'):
            threat_level = threat_intel.get('threat_level', 'none')
            level_scores = {
                'critical': 0.9,
                'high': 0.75,
                'medium': 0.5,
                'low': 0.2,
                'none': 0.0
            }
            intel_score = level_scores.get(threat_level, 0.0)
            score += intel_score * 0.3  # 30% weight
            factors.append(f"Threat Intelligence: {threat_level} ({int(intel_score*100)}%)")
        
        # Factor 2: Attack assessment
        attack = analysis.get('attack_assessment', {})
        if attack.get('available'):
            total_alerts = attack.get('total_alert_count', 0)
            if total_alerts > 0:
                attack_score = min(0.9, 0.1 + (total_alerts * 0.05))
                score += attack_score * 0.35  # 35% weight
                factors.append(f"Attack History: {total_alerts} alerts ({int(attack_score*100)}%)")
        
        # Factor 3: Geolocation characteristics
        geoloc = analysis.get('geolocation', {})
        if not geoloc.get('error'):
            geo_score = 0.0
            if geoloc.get('proxy'):
                geo_score += 0.2
                factors.append("Proxy/VPN detected")
            if geoloc.get('hosting'):
                geo_score += 0.15
                factors.append("Hosting provider")
            if geoloc.get('mobile'):
                geo_score += 0.05
                factors.append("Mobile IP")
            score += min(0.3, geo_score) * 0.2  # 20% weight
        
        # Factor 4: Classification
        classif = analysis.get('classification', {})
        if classif.get('risk_level') == 'medium':
            score += 0.15 * 0.15  # 15% weight
        
        # Normalize to 0-100 scale
        final_score = min(100, max(0, score * 100))
        
        # Determine risk level
        if final_score >= 80:
            risk_level = 'critical'
            recommendation = 'BLOCK - Critical threat detected'
        elif final_score >= 60:
            risk_level = 'high'
            recommendation = 'ALERT - High risk IP'
        elif final_score >= 40:
            risk_level = 'medium'
            recommendation = 'MONITOR - Medium risk IP'
        elif final_score >= 20:
            risk_level = 'low'
            recommendation = 'ALLOW - Low risk IP'
        else:
            risk_level = 'safe'
            recommendation = 'TRUSTED - Safe IP'
        
        return {
            'score': round(final_score, 2),
            'risk_level': risk_level,
            'recommendation': recommendation,
            'factors': factors,
        }

    def _assess_attack_history(
        self,
        ip: str,
        geolocation: Optional[Dict[str, Any]] = None,
        reverse_lookup: Optional[Dict[str, Any]] = None,
        threat_intel: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Look up whether the IP has been involved in recorded attacks."""
        try:
            from app.models.database import Alert, ThreatIntelligence
        except Exception as e:
            logger.error(f"Attack history lookup unavailable: {e}")
            return {
                'available': False,
                'status': 'unknown',
                'attacked': None,
                'error': 'Attack history lookup is unavailable'
            }

        try:
            geolocation = geolocation or {}
            reverse_lookup = reverse_lookup or {'success': False, 'hostname': None}

            ip_alerts = Alert.query.filter(
                (Alert.source_ip == ip) | (Alert.destination_ip == ip)
            )

            source_alert_count = Alert.query.filter(Alert.source_ip == ip).count()
            destination_alert_count = Alert.query.filter(Alert.destination_ip == ip).count()
            total_alert_count = ip_alerts.count()

            severity_rows = Alert.query.with_entities(
                Alert.severity,
                func.count().label('count')
            ).filter(
                (Alert.source_ip == ip) | (Alert.destination_ip == ip)
            ).group_by(Alert.severity).all()

            attack_type_rows = Alert.query.with_entities(
                Alert.attack_type,
                func.count().label('count')
            ).filter(
                (Alert.source_ip == ip) | (Alert.destination_ip == ip)
            ).group_by(Alert.attack_type).order_by(func.count().desc()).all()

            recent_alerts = ip_alerts.order_by(Alert.timestamp.desc()).limit(5).all()
            first_seen_alert = ip_alerts.order_by(Alert.timestamp.asc()).first()
            last_seen_alert = recent_alerts[0] if recent_alerts else None

            threat_record = ThreatIntelligence.query.filter_by(ip_address=ip).first()

            attacked = destination_alert_count > 0 or bool(
                threat_record and threat_record.is_blocked
            )
            suspicious = not attacked and source_alert_count > 0

            if attacked:
                status = 'attacked'
                status_label = 'Attacked'
            elif suspicious:
                status = 'suspicious'
                status_label = 'Suspicious activity'
            elif threat_record:
                status = 'watchlist'
                status_label = 'On threat watchlist'
            else:
                status = 'no_known_attack'
                status_label = 'No known attack'

            severity_breakdown = {
                severity: count
                for severity, count in severity_rows
                if severity
            }

            attack_types = [
                {'attack_type': attack_type, 'count': count}
                for attack_type, count in attack_type_rows
                if attack_type
            ]

            recent_alert_data = []
            for alert in recent_alerts:
                recent_alert_data.append({
                    'id': alert.id,
                    'timestamp': alert.timestamp.isoformat() if alert.timestamp else None,
                    'attack_type': alert.attack_type,
                    'severity': alert.severity,
                    'source_ip': alert.source_ip,
                    'destination_ip': alert.destination_ip,
                    'description': alert.description,
                    'resolved': alert.resolved,
                    'acknowledged': alert.acknowledged,
                })

            threat_intelligence = None
            if threat_record:
                threat_intelligence = {
                    'threat_type': threat_record.threat_type,
                    'confidence': threat_record.confidence,
                    'source': threat_record.source,
                    'is_blocked': threat_record.is_blocked,
                    'first_seen': threat_record.first_seen.isoformat() if threat_record.first_seen else None,
                    'last_seen': threat_record.last_seen.isoformat() if threat_record.last_seen else None,
                }

            realtime_context = {
                'geolocation': geolocation,
                'reverse_lookup': reverse_lookup,
                'source_alert_count': source_alert_count,
                'destination_alert_count': destination_alert_count,
                'total_alert_count': total_alert_count,
                'blocked_threat': 1.0 if threat_record and threat_record.is_blocked else 0.0,
                'threat_confidence': float(threat_record.confidence or 0.0) if threat_record else 0.0,
                'watchlist_flag': 1.0 if threat_record else 0.0,
            }
            realtime_assessment = self.realtime_model.score(ip, realtime_context)

            final_status = status
            final_status_label = status_label
            final_attacked = attacked
            final_suspicious = suspicious

            status_rank = {
                'no_known_attack': 0,
                'watchlist': 1,
                'suspicious': 2,
                'attacked': 3,
            }
            if status_rank.get(realtime_assessment.get('status', 'no_known_attack'), 0) > status_rank.get(status, 0):
                final_status = realtime_assessment.get('status', final_status)
                final_status_label = realtime_assessment.get('status_label', final_status_label)
                final_attacked = realtime_assessment.get('attacked', final_attacked)
                final_suspicious = realtime_assessment.get('suspicious', final_suspicious)

            detection_mode = 'hybrid'
            if final_status == 'no_known_attack':
                detection_mode = 'realtime_ai'

            return {
                'available': True,
                'status': final_status,
                'status_label': final_status_label,
                'attacked': final_attacked,
                'suspicious': final_suspicious,
                'source_alert_count': source_alert_count,
                'destination_alert_count': destination_alert_count,
                'total_alert_count': total_alert_count,
                'severity_breakdown': severity_breakdown,
                'attack_types': attack_types,
                'first_seen': first_seen_alert.timestamp.isoformat() if first_seen_alert and first_seen_alert.timestamp else None,
                'last_seen': last_seen_alert.timestamp.isoformat() if last_seen_alert and last_seen_alert.timestamp else None,
                'recent_alerts': recent_alert_data,
                'threat_intelligence': threat_intelligence,
                'realtime_ai_assessment': realtime_assessment,
                'detection_mode': detection_mode,
            }
        except Exception as e:
            logger.error(f"Attack history lookup failed for {ip}: {e}")
            return {
                'available': False,
                'status': 'unknown',
                'attacked': None,
                'error': str(e)
            }
    
    def _validate_ip(self, ip: str) -> Dict[str, Any]:
        """Validate and characterize IP address."""
        return {
            'is_valid': True,
            'version': self.validator.ip_version(ip),
            'is_private': self.validator.is_private_ip(ip),
            'is_reserved': self.validator.is_reserved_ip(ip),
            'is_ipv4': self.validator.is_valid_ipv4(ip),
            'is_ipv6': self.validator.is_valid_ipv6(ip),
        }
    
    def _classify_ip(self, ip: str) -> Dict[str, Any]:
        """Classify IP address type."""
        classification = {
            'type': [],
            'risk_level': 'low',
            'description': ''
        }
        
        if self.validator.is_private_ip(ip):
            classification['type'].append('Private')
            classification['description'] = 'RFC 1918 Private Address Range'
        
        if self.validator.is_reserved_ip(ip):
            classification['type'].append('Reserved')
            classification['description'] = 'Reserved for special use'
        
        if not classification['type']:
            classification['type'].append('Public')
            classification['description'] = 'Public Internet Address'
        
        # Basic risk assessment
        if 'Private' in classification['type']:
            classification['risk_level'] = 'low'
        elif 'Reserved' in classification['type']:
            classification['risk_level'] = 'medium'
        else:
            classification['risk_level'] = 'unknown'  # Would need threat intelligence
        
        return classification
    
    def _reverse_lookup(self, ip: str) -> Dict[str, Any]:
        """Perform reverse DNS lookup."""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return {
                'hostname': hostname,
                'success': True
            }
        except socket.herror:
            return {'hostname': None, 'success': False}
        except Exception as e:
            logger.error(f"Reverse lookup failed for {ip}: {e}")
            return {'error': str(e), 'success': False}
    
    def analyze_multiple(self, ips: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple IP addresses.
        
        Args:
            ips: List of IP addresses
            
        Returns:
            List of analysis results
        """
        return [self.analyze(ip) for ip in ips]
    
    def extract_ips_from_text(self, text: str) -> List[str]:
        """
        Extract IP addresses from text.
        
        Args:
            text: Text to search for IP addresses
            
        Returns:
            List of unique IP addresses found
        """
        ipv4_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        ips = re.findall(ipv4_pattern, text)
        return list(set(ips))  # Return unique IPs


class IPDatabase:
    """In-memory IP database for caching analysis results."""
    
    def __init__(self, max_entries: int = 1000):
        self.db: Dict[str, Dict] = {}
        self.max_entries = max_entries
    
    def get(self, ip: str) -> Optional[Dict]:
        """Get cached analysis for IP."""
        return self.db.get(ip)
    
    def put(self, ip: str, data: Dict) -> None:
        """Cache analysis for IP."""
        if len(self.db) >= self.max_entries:
            # Remove oldest entry (simple FIFO)
            self.db.pop(next(iter(self.db)))
        self.db[ip] = data
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self.db.clear()
    
    def size(self) -> int:
        """Get number of cached entries."""
        return len(self.db)


# Global analyzer and cache
_ip_analyzer = IPAnalyzer()
_ip_database = IPDatabase()


def analyze_ip(ip: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    Analyze IP address with optional caching.
    
    Args:
        ip: IP address to analyze
        use_cache: Whether to use cached results
        
    Returns:
        Analysis results
    """
    if use_cache:
        cached = _ip_database.get(ip)
        if cached:
            logger.info(f"Using cached IP analysis for {ip}")
            return cached
    
    result = _ip_analyzer.analyze(ip)
    
    if result.get('success'):
        _ip_database.put(ip, result)
    
    return result


def validate_ip(ip: str) -> bool:
    """Quick validation check."""
    return IPValidator.is_valid_ip(ip)


def extract_ips(text: str) -> List[str]:
    """Extract all IPs from text."""
    return _ip_analyzer.extract_ips_from_text(text)
