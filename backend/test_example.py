"""
Example test file for CI/CD pipeline
Add your actual tests here
"""
import pytest


def test_example():
    """Example test - replace with actual tests"""
    assert True


def test_imports():
    """Test that key modules can be imported"""
    try:
        import streamlit
        import pandas
        import crewai
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import required module: {e}")
