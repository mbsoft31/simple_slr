# Configuration Guide

Simple SLR uses YAML configuration files for flexible and readable configuration.

## Quick Start

Create a minimal configuration file:

```yaml
# config.yml
mailto: your.email@example.com

providers:
  openalex:
    enabled: true
```

## Complete Configuration

See `config.example.yml` for a complete example with all options.

## Configuration Structure

### General Settings

```yaml
# Your email (required for polite API crawling)
mailto: researcher@university.edu

# Year range filter (optional)
year_min: 2020
year_max: 2024

# Language filter
language: en
```

### Provider Configuration

Configure each provider independently:

```yaml
providers:
  # OpenAlex (open bibliographic database)
  openalex:
    enabled: true
    rate_limit: 5.0      # requests per second
    timeout: 30          # request timeout in seconds
    mailto: null         # override general mailto if needed
  
  # Crossref (DOI metadata)
  crossref:
    enabled: true
    rate_limit: 1.0
    timeout: 30
  
  # arXiv (preprint repository)
  arxiv:
    enabled: true
    rate_limit: 0.5      # arXiv prefers slower rates
    timeout: 30
  
  # Semantic Scholar (AI-powered search)
  semantic_scholar:
    enabled: false       # requires API key
    api_key: ${S2_API_KEY}  # from environment variable
    rate_limit: 1.0
    timeout: 30
```

### Deduplication Settings

```yaml
deduplication:
  # Strategy: conservative, semantic, or hybrid
  strategy: conservative
  
  # Conservative deduplication settings
  fuzzy_threshold: 97    # 0-100, higher = more strict
  max_year_gap: 1        # max year difference for duplicates
  
  # Semantic deduplication (requires semantic extras)
  semantic_threshold: 0.92
  embedding_model: "allenai/specter2"
  use_embeddings: false  # set true to enable (downloads ~2GB)
```

### Classification Settings

```yaml
classification:
  enabled: false         # not available in v1.0
  method: heuristic      # heuristic, ml, ensemble
  confidence_threshold: 0.6
```

### Output Settings

```yaml
output:
  directory: ./outputs
  format: csv            # csv, jsonl, both, json
  include_raw: false     # include raw API responses
```

## Environment Variables

Use environment variables for sensitive data:

```yaml
providers:
  semantic_scholar:
    api_key: ${S2_API_KEY}           # required
    mailto: ${USER_EMAIL}             # optional
    custom_setting: ${VAR:-default}   # with default value
```

Set environment variables:

```bash
# Linux/macOS
export S2_API_KEY="your-api-key-here"
export USER_EMAIL="user@example.com"

# Windows PowerShell
$env:S2_API_KEY="your-api-key-here"
$env:USER_EMAIL="user@example.com"

# Windows CMD
set S2_API_KEY=your-api-key-here
set USER_EMAIL=user@example.com
```

Or use a `.env` file (recommended):

```bash
# .env
S2_API_KEY=your-api-key-here
USER_EMAIL=user@example.com
```

## Loading Configuration

### From File

```python
from slr.core import load_config
from pathlib import Path

config = load_config(Path("config.yml"))
print(config.mailto)
print(config.providers.openalex.rate_limit)
```

### Programmatically

```python
from slr.core import SLRConfig

config = SLRConfig(
    mailto="user@example.com",
    year_min=2020,
    providers={
        "openalex": {"enabled": True, "rate_limit": 10.0}
    }
)
```

### From Dictionary

```python
from slr.core import load_config_from_dict

config_dict = {
    "mailto": "user@example.com",
    "year_min": 2020
}
config = load_config_from_dict(config_dict)
```

## Merging Configurations

Combine base and override configurations:

```python
from slr.core import load_config, merge_configs

base = load_config(Path("base-config.yml"))
override = {
    "year_min": 2021,
    "providers": {"openalex": {"rate_limit": 15.0}}
}

merged = merge_configs(base, override)
```

## Configuration Examples

### Minimal Setup

```yaml
mailto: researcher@university.edu

providers:
  openalex:
    enabled: true
```

### Multi-Provider Setup

```yaml
mailto: researcher@university.edu
year_min: 2020
year_max: 2024

providers:
  openalex:
    enabled: true
    rate_limit: 10.0
  
  crossref:
    enabled: true
    rate_limit: 2.0
  
  arxiv:
    enabled: true
    rate_limit: 1.0
```

### With Semantic Scholar

```yaml
mailto: researcher@university.edu

providers:
  openalex:
    enabled: true
  
  semantic_scholar:
    enabled: true
    api_key: ${S2_API_KEY}
    rate_limit: 2.0
```

### High-Throughput Setup

```yaml
mailto: researcher@university.edu

providers:
  openalex:
    enabled: true
    rate_limit: 10.0   # max recommended
    timeout: 60
  
  crossref:
    enabled: true
    rate_limit: 5.0    # with Crossref Plus
    timeout: 60
```

### Conservative Deduplication

```yaml
mailto: researcher@university.edu

deduplication:
  strategy: conservative
  fuzzy_threshold: 98    # very strict
  max_year_gap: 0        # must match exactly
```

### Relaxed Deduplication

```yaml
mailto: researcher@university.edu

deduplication:
  strategy: conservative
  fuzzy_threshold: 90    # more lenient
  max_year_gap: 2        # allow 2-year difference
```

## Validation

Configuration is validated when loaded. Common validation errors:

**Invalid rate limit:**
```
ValidationError: rate_limit must be positive and not exceed 100
```

**Invalid year range:**
```
ValidationError: year_min cannot be greater than year_max
```

**Invalid format:**
```
ValidationError: format must be one of {'csv', 'jsonl', 'both', 'json'}
```

## Best Practices

### 1. Use Version Control

Keep configuration in version control:

```bash
git add config.yml
git commit -m "feat: update search configuration"
```

But exclude sensitive data:

```bash
# .gitignore
.env
config.local.yml
*-secret.yml
```

### 2. Use Multiple Configurations

Different configs for different purposes:

```
config/
├── base.yml           # Shared settings
├── development.yml    # Development overrides
├── production.yml     # Production settings
└── testing.yml        # Test configuration
```

### 3. Document Your Configuration

Add comments:

```yaml
# Research project: Impact of AI on healthcare
# Last updated: 2024-01-15
# Contact: researcher@university.edu

mailto: researcher@university.edu
year_min: 2020  # Focus on recent research
year_max: 2024

providers:
  openalex:
    enabled: true
    rate_limit: 5.0  # Stay conservative to be polite
```

### 4. Test Configuration

Validate before running:

```python
from slr.core import load_config

try:
    config = load_config(Path("config.yml"))
    print("✓ Configuration valid")
except ValueError as e:
    print(f"✗ Configuration error: {e}")
```

### 5. Use Defaults Wisely

Only specify non-default values:

```yaml
# Good - only overrides needed
mailto: user@example.com
providers:
  openalex:
    rate_limit: 10.0  # override default 5.0

# Less good - unnecessary verbosity
mailto: user@example.com
year_min: null
year_max: null
language: en  # this is the default anyway
providers:
  openalex:
    enabled: true  # default
    rate_limit: 10.0
    timeout: 30    # default
```

## Troubleshooting

### Configuration Not Found

```python
FileNotFoundError: Configuration file not found: config.yml
```
**Solution:** Check file path and current directory

### Environment Variable Not Expanded

```yaml
api_key: ${MISSING_VAR}  # keeps literal ${MISSING_VAR}
```
**Solution:** Set the environment variable or provide default:
```yaml
api_key: ${MISSING_VAR:-default_value}
```

### Invalid YAML Syntax

```
yaml.scanner.ScannerError: while scanning...
```
**Solution:** Check YAML syntax, common issues:
- Incorrect indentation (must use spaces, not tabs)
- Missing colons
- Unquoted strings with special characters

### Type Validation Errors

```
ValidationError: value is not a valid integer
```
**Solution:** Check value types match expected types

## Next Steps

- [Quick Start](../quickstart.md) - Run your first search
- [Provider Guide](../user-guide/providers.md) - Learn about providers
- [Query Guide](../user-guide/queries.md) - Write effective queries

