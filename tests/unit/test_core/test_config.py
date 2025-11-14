"""
Tests for configuration management.

This module tests the configuration models and utilities defined in slr.core.config.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from slr.core.config import (
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


class TestProviderConfig:
    """Test the ProviderConfig model."""

    def test_default_values(self):
        """Test default provider configuration."""
        config = ProviderConfig()
        assert config.enabled is True
        assert config.rate_limit == 1.0
        assert config.timeout == 30
        assert config.api_key is None
        assert config.mailto is None

    def test_custom_values(self):
        """Test custom provider configuration."""
        config = ProviderConfig(
            enabled=False,
            rate_limit=5.0,
            timeout=60,
            api_key="test_key",
            mailto="test@example.com"
        )
        assert config.enabled is False
        assert config.rate_limit == 5.0
        assert config.timeout == 60
        assert config.api_key == "test_key"
        assert config.mailto == "test@example.com"

    def test_rate_limit_validation(self):
        """Test rate limit validation."""
        # Should fail with zero
        with pytest.raises(ValueError, match="rate_limit must be positive"):
            ProviderConfig(rate_limit=0)

        # Should fail with negative
        with pytest.raises(ValueError, match="rate_limit must be positive"):
            ProviderConfig(rate_limit=-1)

        # Should fail with excessive rate
        with pytest.raises(ValueError, match="should not exceed 100"):
            ProviderConfig(rate_limit=150)

    def test_timeout_validation(self):
        """Test timeout validation."""
        # Should fail with zero
        with pytest.raises(ValueError, match="timeout must be positive"):
            ProviderConfig(timeout=0)

        # Should fail with negative
        with pytest.raises(ValueError, match="timeout must be positive"):
            ProviderConfig(timeout=-1)

        # Should fail with excessive timeout
        with pytest.raises(ValueError, match="should not exceed 300"):
            ProviderConfig(timeout=400)

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed."""
        config = ProviderConfig(custom_field="value")
        assert config.model_extra["custom_field"] == "value"


class TestProvidersConfig:
    """Test the ProvidersConfig model."""

    def test_default_providers(self):
        """Test default provider configurations."""
        config = ProvidersConfig()
        assert config.openalex.enabled is True
        assert config.crossref.enabled is True
        assert config.arxiv.enabled is True
        assert config.semantic_scholar.enabled is False

    def test_default_rate_limits(self):
        """Test default rate limits."""
        config = ProvidersConfig()
        assert config.openalex.rate_limit == 5.0
        assert config.crossref.rate_limit == 1.0
        assert config.arxiv.rate_limit == 0.5
        assert config.semantic_scholar.rate_limit == 1.0

    def test_get_enabled_providers(self):
        """Test getting list of enabled providers."""
        config = ProvidersConfig()
        enabled = config.get_enabled_providers()
        assert "openalex" in enabled
        assert "crossref" in enabled
        assert "arxiv" in enabled
        assert "semantic_scholar" not in enabled

    def test_get_provider(self):
        """Test getting specific provider configuration."""
        config = ProvidersConfig()
        openalex = config.get_provider("openalex")
        assert openalex is not None
        assert openalex.enabled is True
        assert openalex.rate_limit == 5.0

    def test_s2_alias(self):
        """Test that 's2' alias works for semantic_scholar."""
        config = ProvidersConfig(**{"s2": {"enabled": True, "rate_limit": 2.0}})
        assert config.semantic_scholar.enabled is True
        assert config.semantic_scholar.rate_limit == 2.0


class TestDeduplicationConfig:
    """Test the DeduplicationConfig model."""

    def test_default_values(self):
        """Test default deduplication configuration."""
        config = DeduplicationConfig()
        assert config.strategy == DeduplicationStrategy.CONSERVATIVE
        assert config.fuzzy_threshold == 97
        assert config.max_year_gap == 1
        assert config.semantic_threshold == 0.92
        assert config.use_embeddings is False

    def test_fuzzy_threshold_validation(self):
        """Test fuzzy threshold validation."""
        # Valid values
        config = DeduplicationConfig(fuzzy_threshold=50)
        assert config.fuzzy_threshold == 50

        config = DeduplicationConfig(fuzzy_threshold=100)
        assert config.fuzzy_threshold == 100

        # Invalid values
        with pytest.raises(ValueError):
            DeduplicationConfig(fuzzy_threshold=-1)

        with pytest.raises(ValueError):
            DeduplicationConfig(fuzzy_threshold=101)

    def test_strategy_enum(self):
        """Test deduplication strategy enum."""
        config = DeduplicationConfig(strategy="semantic")
        assert config.strategy == DeduplicationStrategy.SEMANTIC

        config = DeduplicationConfig(strategy=DeduplicationStrategy.HYBRID)
        assert config.strategy == DeduplicationStrategy.HYBRID

    def test_extra_fields_forbidden(self):
        """Test that extra fields are not allowed."""
        with pytest.raises(ValueError):
            DeduplicationConfig(unknown_field="value")


class TestClassificationConfig:
    """Test the ClassificationConfig model."""

    def test_default_values(self):
        """Test default classification configuration."""
        config = ClassificationConfig()
        assert config.enabled is False
        assert config.method == ClassificationMethod.HEURISTIC
        assert config.confidence_threshold == 0.6

    def test_confidence_threshold_validation(self):
        """Test confidence threshold validation."""
        # Valid values
        config = ClassificationConfig(confidence_threshold=0.0)
        assert config.confidence_threshold == 0.0

        config = ClassificationConfig(confidence_threshold=1.0)
        assert config.confidence_threshold == 1.0

        # Invalid values
        with pytest.raises(ValueError):
            ClassificationConfig(confidence_threshold=-0.1)

        with pytest.raises(ValueError):
            ClassificationConfig(confidence_threshold=1.1)

    def test_method_enum(self):
        """Test classification method enum."""
        config = ClassificationConfig(method="ml")
        assert config.method == ClassificationMethod.ML

        config = ClassificationConfig(method=ClassificationMethod.ENSEMBLE)
        assert config.method == ClassificationMethod.ENSEMBLE


class TestOutputConfig:
    """Test the OutputConfig model."""

    def test_default_values(self):
        """Test default output configuration."""
        config = OutputConfig()
        assert config.directory == Path("outputs")
        assert config.format == "csv"
        assert config.include_raw is False

    def test_directory_conversion(self):
        """Test directory path conversion."""
        config = OutputConfig(directory="results")
        assert isinstance(config.directory, Path)
        assert config.directory == Path("results")

    def test_format_validation(self):
        """Test output format validation."""
        # Valid formats
        for fmt in ["csv", "jsonl", "both", "json"]:
            config = OutputConfig(format=fmt)
            assert config.format == fmt.lower()

        # Invalid format
        with pytest.raises(ValueError, match="format must be one of"):
            OutputConfig(format="xml")


class TestSLRConfig:
    """Test the main SLRConfig model."""

    def test_default_configuration(self):
        """Test default SLR configuration."""
        config = SLRConfig()
        assert config.mailto is None
        assert config.year_min is None
        assert config.year_max is None
        assert config.language == "en"
        assert isinstance(config.providers, ProvidersConfig)
        assert isinstance(config.deduplication, DeduplicationConfig)
        assert isinstance(config.classification, ClassificationConfig)
        assert isinstance(config.output, OutputConfig)

    def test_custom_configuration(self):
        """Test custom SLR configuration."""
        config = SLRConfig(
            mailto="test@example.com",
            year_min=2020,
            year_max=2023,
            language="es"
        )
        assert config.mailto == "test@example.com"
        assert config.year_min == 2020
        assert config.year_max == 2023
        assert config.language == "es"

    def test_year_validation(self):
        """Test year validation."""
        # Valid years
        config = SLRConfig(year_min=2000, year_max=2020)
        assert config.year_min == 2000
        assert config.year_max == 2020

        # Invalid years (too old)
        with pytest.raises(ValueError, match="between 1900 and 2100"):
            SLRConfig(year_min=1800)

        # Invalid years (too future)
        with pytest.raises(ValueError, match="between 1900 and 2100"):
            SLRConfig(year_max=2200)

    def test_year_range_validation(self):
        """Test year range validation."""
        # Valid range
        config = SLRConfig(year_min=2020, year_max=2023)
        assert config.year_min == 2020
        assert config.year_max == 2023

        # Invalid range (min > max)
        with pytest.raises(ValueError, match="year_min cannot be greater than year_max"):
            SLRConfig(year_min=2023, year_max=2020)

    def test_mailto_propagation(self):
        """Test that mailto is propagated to providers."""
        config = SLRConfig(mailto="test@example.com")
        assert config.providers.openalex.mailto == "test@example.com"
        assert config.providers.crossref.mailto == "test@example.com"
        assert config.providers.arxiv.mailto == "test@example.com"

    def test_nested_configuration(self):
        """Test nested configuration objects."""
        config = SLRConfig(
            providers={
                "openalex": {"enabled": False, "rate_limit": 10.0}
            },
            deduplication={"fuzzy_threshold": 90},
            output={"directory": "results", "format": "jsonl"}
        )
        assert config.providers.openalex.enabled is False
        assert config.providers.openalex.rate_limit == 10.0
        assert config.deduplication.fuzzy_threshold == 90
        assert config.output.directory == Path("results")
        assert config.output.format == "jsonl"


class TestLoadConfig:
    """Test configuration loading functions."""

    def test_load_from_yaml(self):
        """Test loading configuration from YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
mailto: test@example.com
year_min: 2020
language: en

providers:
  openalex:
    enabled: true
    rate_limit: 10.0
  crossref:
    enabled: false

deduplication:
  fuzzy_threshold: 95

output:
  directory: results
  format: jsonl
""")
            temp_path = f.name

        try:
            config = load_config(Path(temp_path))
            assert config.mailto == "test@example.com"
            assert config.year_min == 2020
            assert config.providers.openalex.rate_limit == 10.0
            assert config.providers.crossref.enabled is False
            assert config.deduplication.fuzzy_threshold == 95
            assert config.output.format == "jsonl"
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("nonexistent.yml"))

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
year_min: -1000
""")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid configuration"):
                load_config(Path(temp_path))
        finally:
            os.unlink(temp_path)

    def test_load_from_dict(self):
        """Test loading configuration from dictionary."""
        config_dict = {
            "mailto": "test@example.com",
            "year_min": 2020,
            "providers": {
                "openalex": {"rate_limit": 10.0}
            }
        }
        config = load_config_from_dict(config_dict)
        assert config.mailto == "test@example.com"
        assert config.year_min == 2020
        assert config.providers.openalex.rate_limit == 10.0

    def test_environment_variable_expansion(self):
        """Test environment variable expansion in config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
mailto: ${TEST_EMAIL}
providers:
  semantic_scholar:
    api_key: ${S2_API_KEY:-default_key}
""")
            temp_path = f.name

        try:
            # Set environment variable
            os.environ["TEST_EMAIL"] = "env@example.com"
            # Don't set S2_API_KEY to test default
            if "S2_API_KEY" in os.environ:
                del os.environ["S2_API_KEY"]

            config = load_config(Path(temp_path))
            assert config.mailto == "env@example.com"
            assert config.providers.semantic_scholar.api_key == "default_key"
        finally:
            os.unlink(temp_path)
            if "TEST_EMAIL" in os.environ:
                del os.environ["TEST_EMAIL"]


class TestSaveConfig:
    """Test configuration saving functions."""

    def test_save_config(self):
        """Test saving configuration to YAML file."""
        config = SLRConfig(
            mailto="test@example.com",
            year_min=2020,
            providers={"openalex": {"rate_limit": 10.0}}
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "config.yml"
            save_config(config, output_path)

            assert output_path.exists()

            # Load and verify
            loaded = load_config(output_path)
            assert loaded.mailto == "test@example.com"
            assert loaded.year_min == 2020
            assert loaded.providers.openalex.rate_limit == 10.0

    def test_create_default_config(self):
        """Test creating default configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "config.yml"
            config = create_default_config(output_path)

            assert isinstance(config, SLRConfig)
            assert output_path.exists()

            # Verify defaults
            assert config.language == "en"
            assert config.providers.openalex.enabled is True

    def test_save_creates_directory(self):
        """Test that save_config creates parent directories."""
        config = SLRConfig()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "config.yml"
            save_config(config, output_path)

            assert output_path.exists()
            assert output_path.parent.exists()


class TestMergeConfigs:
    """Test configuration merging."""

    def test_simple_merge(self):
        """Test simple configuration merge."""
        base = SLRConfig(mailto="base@example.com", year_min=2020)
        override = {"year_min": 2021, "year_max": 2023}

        merged = merge_configs(base, override)
        assert merged.mailto == "base@example.com"  # From base
        assert merged.year_min == 2021  # Overridden
        assert merged.year_max == 2023  # New value

    def test_nested_merge(self):
        """Test nested configuration merge."""
        base = SLRConfig(
            providers={"openalex": {"enabled": True, "rate_limit": 5.0}}
        )
        override = {
            "providers": {
                "openalex": {"rate_limit": 10.0},  # Override only rate_limit
                "crossref": {"enabled": False}  # New provider config
            }
        }

        merged = merge_configs(base, override)
        assert merged.providers.openalex.enabled is True  # From base
        assert merged.providers.openalex.rate_limit == 10.0  # Overridden
        assert merged.providers.crossref.enabled is False  # New value

    def test_merge_preserves_base(self):
        """Test that merge doesn't modify base config."""
        base = SLRConfig(year_min=2020)
        original_year = base.year_min

        override = {"year_min": 2021}
        merged = merge_configs(base, override)

        assert base.year_min == original_year  # Base unchanged
        assert merged.year_min == 2021  # Merged has new value


class TestConfigIntegration:
    """Integration tests for configuration system."""

    def test_complete_workflow(self):
        """Test complete configuration workflow."""
        # Create config
        config = SLRConfig(
            mailto="test@example.com",
            year_min=2020,
            year_max=2023,
            providers={
                "openalex": {"enabled": True, "rate_limit": 10.0},
                "crossref": {"enabled": False}
            },
            deduplication={"fuzzy_threshold": 95},
            output={"directory": "results", "format": "jsonl"}
        )

        # Save to file
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yml"
            save_config(config, config_path)

            # Load from file
            loaded = load_config(config_path)

            # Verify all values
            assert loaded.mailto == config.mailto
            assert loaded.year_min == config.year_min
            assert loaded.year_max == config.year_max
            assert loaded.providers.openalex.rate_limit == 10.0
            assert loaded.providers.crossref.enabled is False
            assert loaded.deduplication.fuzzy_threshold == 95
            assert loaded.output.format == "jsonl"

    def test_partial_config_with_defaults(self):
        """Test partial config uses defaults for missing values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
mailto: test@example.com
""")
            temp_path = f.name

        try:
            config = load_config(Path(temp_path))
            # Should have defaults for everything except mailto
            assert config.mailto == "test@example.com"
            assert config.language == "en"  # Default
            assert config.providers.openalex.enabled is True  # Default
            assert config.deduplication.fuzzy_threshold == 97  # Default
        finally:
            os.unlink(temp_path)

