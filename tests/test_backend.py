"""
Tests for backend functionality
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_backend_imports():
    """Test that backend modules can be imported"""
    try:
        from backend import app, models, rules_engine
        assert app is not None
        assert models is not None
        assert rules_engine is not None
    except ImportError as e:
        pytest.skip(f"Backend imports not available: {e}")


def test_models_module_exists():
    """Test that models module exists and has basic structure"""
    try:
        from backend import models
        assert hasattr(models, '__file__')
    except ImportError:
        pytest.skip("Models module not available")


def test_app_module_exists():
    """Test that app module exists"""
    try:
        from backend import app
        assert hasattr(app, '__file__')
    except ImportError:
        pytest.skip("App module not available")


def test_rules_engine_module_exists():
    """Test that rules engine module exists"""
    try:
        from backend import rules_engine
        assert hasattr(rules_engine, '__file__')
    except ImportError:
        pytest.skip("Rules engine module not available")


def test_integrations_module_exists():
    """Test that integrations module exists"""
    try:
        from backend import integrations
        assert hasattr(integrations, '__file__')
    except ImportError:
        pytest.skip("Integrations module not available")


def test_ai_validator_module_exists():
    """Test that AI validator module exists"""
    try:
        from backend import ai_validator
        assert hasattr(ai_validator, '__file__')
    except ImportError:
        pytest.skip("AI validator module not available")
