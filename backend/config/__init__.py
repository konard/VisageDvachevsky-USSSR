"""
Configuration module for USSR Leaders Platform
"""
from .config import Config, DevelopmentConfig, ProductionConfig, TestingConfig, get_config

__all__ = ['Config', 'DevelopmentConfig', 'ProductionConfig', 'TestingConfig', 'get_config']
