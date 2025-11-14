# Simple SLR Documentation

Welcome to the Simple SLR documentation! This guide will help you conduct systematic literature reviews efficiently.

## 📚 Documentation Structure

### Getting Started
- [Installation](getting-started/installation.md) - Install and setup
- [Quick Start](quickstart.md) - Get running in 5 minutes
- [Configuration](getting-started/configuration.md) - Configure Simple SLR

### User Guide
- [Providers](user-guide/providers.md) - Working with data providers
- [Search & Queries](user-guide/queries.md) - Writing effective queries
- [Deduplication](deduplication.md) - Remove duplicate papers
- [Export Formats](user-guide/export.md) - Export your results
- [Screening](screening_export.md) - Screen papers for inclusion

### Developer Guide
- [Architecture](architecture.md) - System architecture
- [Contributing](../CONTRIBUTING.md) - How to contribute
- [API Reference](api-reference/) - Code documentation
- [Testing](developer-guide/testing.md) - Writing tests

### Advanced Topics
- [Rate Limiting](developer-guide/rate-limiting.md) - API rate management
- [Performance](developer-guide/performance.md) - Optimization tips
- [Migration](migration/) - Upgrading from older versions

## 🚀 Quick Links

### Common Tasks

**Install Simple SLR:**
```bash
pip install simple-slr
```

**Run a search:**
```bash
slr search --config config.yml --queries queries.yml
```

**Deduplicate results:**
```bash
slr deduplicate --input outputs/ --output dedup/
```

**Export to BibTeX:**
```bash
slr export --input dedup/ --format bibtex --output references.bib
```

### Configuration Examples

**Minimal config.yml:**
```yaml
mailto: your.email@example.com

providers:
  openalex:
    enabled: true
    rate_limit: 5.0
```

**Complete config.yml:**
See [config.example.yml](../config.example.yml)

## 📖 Tutorials

### Tutorial 1: Your First Literature Review
1. [Install Simple SLR](getting-started/installation.md)
2. [Create a configuration file](getting-started/configuration.md)
3. [Write your search queries](user-guide/queries.md)
4. [Run the search](quickstart.md#running-searches)
5. [Deduplicate results](deduplication.md)
6. [Export for screening](screening_export.md)

### Tutorial 2: Advanced Search Strategies
- Boolean query construction
- Field-specific searches
- Date range filtering
- Multiple provider coordination

### Tutorial 3: Working with Large Result Sets
- Streaming results to disk
- Incremental deduplication
- Memory management
- Performance optimization

## 🔧 Troubleshooting

### Common Issues

**Import Error:**
```
ModuleNotFoundError: No module named 'slr'
```
**Solution:** Install in development mode: `pip install -e .`

**Rate Limit Errors:**
```
RateLimitError: Rate limit exceeded
```
**Solution:** Reduce `rate_limit` in config.yml or add delays.

**Configuration Validation:**
```
ValidationError: year_min cannot be greater than year_max
```
**Solution:** Check your configuration file for invalid values.

See [Troubleshooting Guide](user-guide/troubleshooting.md) for more.

## 📊 Examples

### Example Configurations
- [Basic Research Project](examples/basic-project/)
- [Multi-Provider Search](examples/multi-provider/)
- [Large Scale Review](examples/large-scale/)

### Example Queries
- [Computer Science](examples/queries-cs.yml)
- [Medical Research](examples/queries-medical.yml)
- [Social Sciences](examples/queries-social.yml)

## 🤝 Community

- **GitHub Issues:** Bug reports and feature requests
- **Discussions:** Questions and community support
- **Contributing:** See [CONTRIBUTING.md](../CONTRIBUTING.md)

## 📝 Changelog

See [CHANGELOG.md](../CHANGELOG.md) for version history.

## 📄 License

Simple SLR is licensed under the MIT License. See [LICENSE](../LICENSE) for details.

## 🙏 Acknowledgments

Simple SLR builds on the work of:
- **OpenAlex** - Open bibliographic data
- **Crossref** - DOI registration and metadata
- **arXiv** - Open access preprints
- **Semantic Scholar** - AI-powered paper search

---

**Need help?** Open an issue on [GitHub](https://github.com/yourusername/simple-slr/issues)

