# Installation Guide

## Requirements

- **Python:** 3.10 or higher
- **Operating System:** Windows, macOS, or Linux
- **Memory:** 2GB RAM minimum (4GB+ recommended for large reviews)
- **Disk Space:** 500MB for installation, more for results storage

## Installation Methods

### Method 1: Install from PyPI (Recommended)

```bash
pip install simple-slr
```

Verify installation:
```bash
slr --version
```

### Method 2: Install from Source

For development or latest features:

```bash
# Clone repository
git clone https://github.com/yourusername/simple-slr.git
cd simple-slr

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"
```

### Method 3: Install with Optional Dependencies

**For semantic deduplication (requires ~2GB model download):**
```bash
pip install simple-slr[semantic]
```

**For all features:**
```bash
pip install simple-slr[all]
```

## Dependency Groups

- **Base:** Core functionality (always installed)
- **dev:** Development tools (testing, linting, etc.)
- **semantic:** Semantic deduplication with embeddings
- **viz:** Visualization tools
- **all:** Everything

## Virtual Environment Setup

### Using venv (Standard)

```bash
# Create environment
python -m venv slr-env

# Activate
# Windows:
slr-env\Scripts\activate
# macOS/Linux:
source slr-env/bin/activate

# Install
pip install simple-slr
```

### Using conda

```bash
# Create environment
conda create -n slr-env python=3.11

# Activate
conda activate slr-env

# Install
pip install simple-slr
```

### Using poetry

```bash
# Initialize project
poetry init

# Add dependency
poetry add simple-slr

# Activate environment
poetry shell
```

## Verifying Installation

### Quick Test

```bash
# Check version
slr --version

# View help
slr --help

# Run built-in tests (if installed from source)
pytest
```

### Python Import Test

```python
from slr.core import SLRConfig, load_config
from slr.utils import setup_logging, TokenBucket

print("✓ Import successful")
```

## Configuration

After installation, create a configuration file:

```bash
# Copy example configuration
cp config.example.yml config.yml

# Edit with your settings
nano config.yml  # or your preferred editor
```

See [Configuration Guide](configuration.md) for details.

## Troubleshooting

### Common Installation Issues

**Issue:** `pip: command not found`
**Solution:** Ensure Python is in your PATH or use `python -m pip`

**Issue:** Permission denied on macOS/Linux
**Solution:** Use `pip install --user simple-slr` or virtual environment

**Issue:** SSL certificate errors
**Solution:** Update pip: `pip install --upgrade pip certifi`

**Issue:** Build failures on Windows
**Solution:** Install Visual C++ Build Tools from Microsoft

**Issue:** `ModuleNotFoundError` after installation
**Solution:** Ensure virtual environment is activated

### Platform-Specific Notes

**Windows:**
- Use PowerShell or Git Bash for best experience
- If using conda, install from conda-forge: `conda install -c conda-forge simple-slr`

**macOS:**
- Install via Homebrew Python recommended: `brew install python@3.11`
- Apple Silicon (M1/M2): All dependencies are compatible

**Linux:**
- Ubuntu/Debian: `sudo apt install python3-pip python3-venv`
- Fedora/RHEL: `sudo dnf install python3-pip python3-virtualenv`

## Next Steps

1. **Configure Simple SLR:** [Configuration Guide](configuration.md)
2. **Try Quick Start:** [Quick Start Tutorial](../quickstart.md)
3. **Learn about Providers:** [Provider Guide](../user-guide/providers.md)

## Upgrading

### From PyPI

```bash
pip install --upgrade simple-slr
```

### From Source

```bash
git pull origin main
pip install -e ".[dev]"
```

### Version-Specific Upgrades

```bash
# Upgrade to specific version
pip install simple-slr==1.0.0

# Upgrade within major version
pip install "simple-slr>=1.0,<2.0"
```

## Uninstalling

```bash
pip uninstall simple-slr
```

To completely remove including configuration:
```bash
# Remove package
pip uninstall simple-slr

# Remove configuration (optional)
rm -rf ~/.config/simple-slr  # Unix/macOS
# or
rmdir /s %APPDATA%\simple-slr  # Windows
```

## Docker Installation (Alternative)

Coming in future release:

```bash
docker pull simple-slr/simple-slr:latest
docker run -v $(pwd)/outputs:/outputs simple-slr search --config /config.yml
```

## Support

- **Installation Issues:** [GitHub Issues](https://github.com/yourusername/simple-slr/issues)
- **General Questions:** [GitHub Discussions](https://github.com/yourusername/simple-slr/discussions)
- **Documentation:** [Main Documentation](../README.md)

