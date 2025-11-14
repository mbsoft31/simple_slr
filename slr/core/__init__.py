"""
Core functionality for Simple SLR.

This package contains core models, configuration, and base classes
for the SLR framework.
"""

from .config import (
    SLRConfig,
    ProviderConfig,
    ProvidersConfig,
    DeduplicationConfig,
    ClassificationConfig,
    OutputConfig,
    DeduplicationStrategy,
    ClassificationMethod,
    load_config,
    load_config_from_dict,
    create_default_config,
    save_config,
    merge_configs,
)

__all__ = [
    # Configuration
    "SLRConfig",
    "ProviderConfig",
    "ProvidersConfig",
    "DeduplicationConfig",
    "ClassificationConfig",
    "OutputConfig",
    "DeduplicationStrategy",
    "ClassificationMethod",
    # Config utilities
    "load_config",
    "load_config_from_dict",
    "create_default_config",
    "save_config",
    "merge_configs",
]

