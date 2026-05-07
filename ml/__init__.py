"""
AI-NIDS Machine Learning Package
Complete ML pipeline for network intrusion detection
"""

from importlib import import_module

__version__ = '1.0.0'

__all__ = [
    # Preprocessing
    'DataPreprocessor', 'FeatureEngineer', 'create_preprocessor',
    # Models
    'XGBoostClassifier', 'create_xgboost_classifier',
    'AnomalyAutoencoder', 'create_autoencoder',
    'LSTMDetector', 'create_lstm_detector',
    'EnsembleDetector', 'create_ensemble',
    # Explainability
    'SHAPExplainer', 'create_explainer'
]


_EXPORT_MAP = {
    # Preprocessing
    'DataPreprocessor': ('ml.preprocessing', 'DataPreprocessor'),
    'FeatureEngineer': ('ml.preprocessing', 'FeatureEngineer'),
    'create_preprocessor': ('ml.preprocessing', 'create_preprocessor'),
    # Models
    'XGBoostClassifier': ('ml.models', 'XGBoostClassifier'),
    'create_xgboost_classifier': ('ml.models', 'create_xgboost_classifier'),
    'AnomalyAutoencoder': ('ml.models', 'AnomalyAutoencoder'),
    'create_autoencoder': ('ml.models', 'create_autoencoder'),
    'LSTMDetector': ('ml.models', 'LSTMDetector'),
    'create_lstm_detector': ('ml.models', 'create_lstm_detector'),
    'EnsembleDetector': ('ml.models', 'EnsembleDetector'),
    'create_ensemble': ('ml.models', 'create_ensemble'),
    # Explainability
    'SHAPExplainer': ('ml.explainability', 'SHAPExplainer'),
    'create_explainer': ('ml.explainability', 'create_explainer'),
}


def __getattr__(name):
    """Lazy-load heavy ML symbols to avoid importing full training stack at app startup."""
    target = _EXPORT_MAP.get(name)
    if target is None:
        raise AttributeError(f"module 'ml' has no attribute '{name}'")

    module_name, attr_name = target
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
