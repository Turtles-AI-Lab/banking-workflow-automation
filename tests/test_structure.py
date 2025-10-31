"""
Tests for project structure and configuration
"""

import pytest
import os


def test_project_structure():
    """Test that required directories exist"""
    project_root = os.path.dirname(os.path.dirname(__file__))

    assert os.path.exists(os.path.join(project_root, 'backend'))
    assert os.path.exists(os.path.join(project_root, 'frontend'))
    assert os.path.exists(os.path.join(project_root, 'docs'))


def test_required_files_exist():
    """Test that required configuration files exist"""
    project_root = os.path.dirname(os.path.dirname(__file__))

    required_files = [
        'README.md',
        'requirements.txt',
        '.env.example',
        'LICENSE'
    ]

    for filename in required_files:
        filepath = os.path.join(project_root, filename)
        assert os.path.exists(filepath), f"Required file missing: {filename}"


def test_backend_files_exist():
    """Test that backend files exist"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    backend_path = os.path.join(project_root, 'backend')

    backend_files = [
        'app.py',
        'models.py',
        'rules_engine.py',
        'integrations.py',
        'ai_validator.py'
    ]

    for filename in backend_files:
        filepath = os.path.join(backend_path, filename)
        assert os.path.exists(filepath), f"Backend file missing: {filename}"


def test_requirements_file_not_empty():
    """Test that requirements.txt is not empty"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    requirements_path = os.path.join(project_root, 'requirements.txt')

    with open(requirements_path, 'r') as f:
        content = f.read().strip()
        assert len(content) > 0, "requirements.txt is empty"


def test_readme_not_empty():
    """Test that README.md is not empty"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    readme_path = os.path.join(project_root, 'README.md')

    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        assert len(content) > 100, "README.md is too short or empty"
