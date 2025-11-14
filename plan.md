## Revised Architecture Plan: General-Purpose SLR Framework

### Phase 1: Core Modularization (Week 1-2)

#### 1.1 Package Structure

Create a proper Python package structure that separates concerns:

```
simple_slr/
├── slr/                          # Main package
│   ├── __init__.py
│   ├── core/                     # Core abstractions (UI-agnostic)
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract base classes
│   │   ├── document.py          # Document model (pydantic)
│   │   ├── query.py             # Query model
│   │   └── result.py            # SearchResult container
│   ├── providers/               # Provider implementations
│   │   ├── __init__.py
│   │   ├── base.py              # BaseProvider abstract class
│   │   ├── openalex.py
│   │   ├── crossref.py
│   │   ├── arxiv.py
│   │   ├── semantic_scholar.py
│   │   └── registry.py          # Provider registry/factory
│   ├── translators/             # Query translation per provider
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── openalex.py
│   │   ├── crossref.py
│   │   ├── arxiv.py
│   │   └── semantic_scholar.py
│   ├── dedup/                   # Deduplication engine
│   │   ├── __init__.py
│   │   ├── base.py              # Deduplicator interface
│   │   ├── matching.py          # Matching strategies
│   │   ├── clustering.py        # DSU + clustering logic
│   │   ├── embeddings.py        # Semantic dedup (NEW)
│   │   └── strategies/          # Different dedup strategies
│   │       ├── conservative.py  # Current approach
│   │       ├── semantic.py      # Embedding-based
│   │       └── hybrid.py        # Combined approach
│   ├── classification/          # Paper classification (NEW)
│   │   ├── __init__.py
│   │   ├── base.py              # Classifier interface
│   │   ├── heuristic.py         # Rule-based classification
│   │   ├── ml_classifier.py     # ML-based (sklearn/transformers)
│   │   └── types.py             # PaperType enum
│   ├── normalization/           # Text/data normalization
│   │   ├── __init__.py
│   │   ├── text.py              # Title, abstract cleaning
│   │   ├── identifiers.py       # DOI, arXiv, ORCID
│   │   └── authors.py           # Author name parsing
│   ├── export/                  # Export formats
│   │   ├── __init__.py
│   │   ├── base.py              # Exporter interface
│   │   ├── bibtex.py
│   │   ├── ris.py
│   │   ├── csv.py
│   │   ├── jsonl.py
│   │   └── prisma.py            # PRISMA flowchart data
│   ├── screening/               # Screening workflow (UI-agnostic)
│   │   ├── __init__.py
│   │   ├── base.py              # ScreeningSession interface
│   │   ├── criteria.py          # Inclusion/exclusion criteria
│   │   └── session.py           # Session state management
│   ├── analysis/                # Analysis utilities
│   │   ├── __init__.py
│   │   ├── stats.py             # Descriptive statistics
│   │   ├── coverage.py          # Provider coverage analysis
│   │   └── trends.py            # Publication trends
│   └── utils/                   # Utilities
│       ├── __init__.py
│       ├── rate_limit.py
│       ├── config.py            # Configuration management
│       ├── logging.py           # Logging setup
│       └── exceptions.py        # Custom exceptions
├── interfaces/                   # UI implementations (separate)
│   ├── cli/                     # CLI interface
│   │   ├── __init__.py
│   │   ├── main.py              # Click-based CLI
│   │   ├── search.py
│   │   ├── dedup.py
│   │   └── screen.py
│   ├── tui/                     # TUI interface (textual/rich)
│   │   └── __init__.py
│   ├── api/                     # REST API (FastAPI)
│   │   └── __init__.py
│   └── web/                     # Web UI (future)
│       └── __init__.py
├── tests/
│   ├── unit/
│   │   ├── test_providers/
│   │   ├── test_dedup/
│   │   ├── test_classification/
│   │   └── test_normalization/
│   └── integration/
│       └── test_workflow.py
├── examples/                     # Example scripts
│   ├── basic_search.py
│   ├── custom_provider.py
│   ├── embedding_dedup.py
│   └── ml_classification.py
├── docs/
│   ├── architecture.md
│   ├── providers.md             # How to add providers
│   ├── deduplication.md         # Dedup strategies
│   └── api/                     # API documentation
├── pyproject.toml               # Modern Python packaging
├── setup.py
└── README.md
```


#### 1.2 Core Abstractions (UI-Agnostic Design)

**Document Model** (using Pydantic):

```python
# slr/core/document.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

class PaperType(str, Enum):
    """Paper classification types"""
    DATASET = "dataset"
    BENCHMARK = "benchmark"
    METHOD = "method"
    REVIEW = "review"
    SURVEY = "survey"
    APPLICATION = "application"
    UNKNOWN = "unknown"

class Author(BaseModel):
    given_name: Optional[str] = None
    family_name: str
    orcid: Optional[str] = None
    affiliations: List[str] = Field(default_factory=list)

class ExternalIds(BaseModel):
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pubmed_id: Optional[str] = None
    openalex_id: Optional[str] = None
    s2_id: Optional[str] = None
    
class Document(BaseModel):
    """Unified document representation across all providers"""
    # Core fields
    title: str
    year: Optional[int] = None
    abstract: Optional[str] = None
    authors: List[Author] = Field(default_factory=list)
    
    # Identifiers
    external_ids: ExternalIds = Field(default_factory=ExternalIds)
    
    # Publication info
    venue: Optional[str] = None
    url: Optional[HttpUrl] = None
    
    # Metadata
    provider: str  # openalex, crossref, arxiv, s2
    provider_id: str  # original provider-specific ID
    language: Optional[str] = None
    
    # Citations & metrics
    cited_by_count: Optional[int] = None
    
    # Classification (computed)
    paper_type: Optional[PaperType] = None
    confidence: Optional[float] = None  # classification confidence
    
    # Deduplication
    cluster_id: Optional[int] = None
    is_representative: bool = False
    
    # Provenance
    query_id: Optional[str] = None
    query_text: Optional[str] = None
    retrieved_at: Optional[str] = None
    
    # Raw data (optional, for debugging)
    raw_data: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True
```

**Provider Base Class**:

```python
# slr/providers/base.py
from abc import ABC, abstractmethod
from typing import List, Iterator, Optional, Dict, Any
from ..core.document import Document
from ..core.query import Query

class RateLimitConfig(BaseModel):
    requests_per_second: float = 1.0
    burst_size: int = 5
    backoff_factor: float = 2.0
    max_retries: int = 3

class ProviderConfig(BaseModel):
    """Configuration for a provider"""
    name: str
    enabled: bool = True
    api_key: Optional[str] = None
    mailto: Optional[str] = None  # for polite crawling
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    year_min: Optional[int] = None
    language: str = "en"
    custom_params: Dict[str, Any] = Field(default_factory=dict)

class BaseProvider(ABC):
    """Abstract base class for all search providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._rate_limiter = self._init_rate_limiter()
    
    @abstractmethod
    def search(
        self, 
        query: Query, 
        max_results: Optional[int] = None
    ) -> Iterator[Document]:
        """
        Execute search and yield documents.
        
        Args:
            query: Query object with search parameters
            max_results: Maximum number of results to return
            
        Yields:
            Document objects matching the query
        """
        pass
    
    @abstractmethod
    def translate_query(self, query: Query) -> str:
        """Translate query to provider-specific syntax"""
        pass
    
    @abstractmethod
    def normalize_response(self, raw: Dict[str, Any]) -> Document:
        """Convert provider response to Document"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier"""
        pass
    
    def _init_rate_limiter(self):
        """Initialize rate limiting mechanism"""
        # Implementation using token bucket or similar
        pass
```


### Phase 2: Advanced Deduplication (Week 2-3)

#### 2.1 Multi-Strategy Deduplication

**Embedding-Based Semantic Matching**:

```python
# slr/dedup/embeddings.py
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple
from ..core.document import Document

class SemanticDeduplicator:
    """Embedding-based deduplication using SBERT"""
    
    def __init__(
        self, 
        model_name: str = "allenai/specter2",  # Scientific paper embeddings
        similarity_threshold: float = 0.92
    ):
        self.model = SentenceTransformer(model_name)
        self.threshold = similarity_threshold
    
    def embed_documents(self, docs: List[Document]) -> np.ndarray:
        """Generate embeddings for documents"""
        texts = []
        for doc in docs:
            # Combine title + abstract for better representation
            text = doc.title
            if doc.abstract:
                text += " [SEP] " + doc.abstract[:500]  # Limit abstract length
            texts.append(text)
        
        return self.model.encode(texts, show_progress_bar=True)
    
    def find_similar_pairs(
        self, 
        embeddings: np.ndarray
    ) -> List[Tuple[int, int, float]]:
        """Find pairs of similar documents above threshold"""
        from sklearn.metrics.pairwise import cosine_similarity
        
        similarities = cosine_similarity(embeddings)
        pairs = []
        
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = similarities[i, j]
                if sim >= self.threshold:
                    pairs.append((i, j, sim))
        
        return pairs
```

**Hybrid Deduplication Strategy**:

```python
# slr/dedup/strategies/hybrid.py
from typing import List, Dict, Any
from ..base import DeduplicationStrategy
from ..clustering import DSU
from ..embeddings import SemanticDeduplicator
from ...core.document import Document

class HybridDeduplicator(DeduplicationStrategy):
    """
    Multi-stage deduplication:
    1. Exact ID matches (DOI, arXiv)
    2. Fuzzy string matching (conservative)
    3. Semantic similarity (embeddings)
    """
    
    def __init__(
        self,
        fuzzy_threshold: int = 97,
        semantic_threshold: float = 0.92,
        max_year_gap: int = 1,
        use_embeddings: bool = True
    ):
        self.fuzzy_threshold = fuzzy_threshold
        self.semantic_threshold = semantic_threshold
        self.max_year_gap = max_year_gap
        self.use_embeddings = use_embeddings
        
        if use_embeddings:
            self.semantic = SemanticDeduplicator(
                similarity_threshold=semantic_threshold
            )
    
    def deduplicate(self, documents: List[Document]) -> List[DocumentCluster]:
        """Execute multi-stage deduplication"""
        n = len(documents)
        dsu = DSU(n)
        
        # Stage 1: Exact ID matching (DOI, arXiv)
        self._merge_by_identifiers(documents, dsu)
        
        # Stage 2: Fuzzy title matching with blocking
        self._merge_by_fuzzy_title(documents, dsu)
        
        # Stage 3: Semantic similarity (optional)
        if self.use_embeddings:
            self._merge_by_semantics(documents, dsu)
        
        # Build clusters
        return self._build_clusters(documents, dsu)
    
    def _merge_by_semantics(
        self, 
        documents: List[Document], 
        dsu: DSU
    ):
        """Merge using semantic embeddings"""
        # Only embed unmerged docs to save computation
        unmerged_groups = self._get_unmerged_groups(documents, dsu)
        
        for group_docs, group_indices in unmerged_groups:
            if len(group_docs) < 2:
                continue
            
            embeddings = self.semantic.embed_documents(group_docs)
            pairs = self.semantic.find_similar_pairs(embeddings)
            
            for i, j, sim in pairs:
                # Additional validation
                doc_i = group_docs[i]
                doc_j = group_docs[j]
                
                # Year check
                if doc_i.year and doc_j.year:
                    if abs(doc_i.year - doc_j.year) > self.max_year_gap:
                        continue
                
                # First author check
                if (doc_i.authors and doc_j.authors and 
                    doc_i.authors[0].family_name != doc_j.authors[0].family_name):
                    continue
                
                # Merge
                actual_i = group_indices[i]
                actual_j = group_indices[j]
                dsu.union(actual_i, actual_j)
```


### Phase 3: Paper Classification (Week 3-4)

#### 3.1 Multi-Level Classification System

**Rule-Based Classifier** (fast, interpretable):

```python
# slr/classification/heuristic.py
from typing import Dict, List, Tuple
from ..core.document import Document, PaperType
import re

class HeuristicClassifier:
    """Rule-based paper type classification"""
    
    # Keyword patterns for each type
    PATTERNS = {
        PaperType.DATASET: {
            "title": [
                r'\bdataset\b', r'\bbenchmark\b', r'\bcollection\b',
                r'\bcorpus\b', r'\brepository\b', r'\bdata\s*set\b'
            ],
            "abstract": [
                r'we\s+(introduce|present|release|provide)\s+a\s+(new\s+)?dataset',
                r'publicly\s+available\s+dataset',
                r'benchmark\s+dataset',
                r'\d+k?\s+(images|samples|instances)'
            ],
            "weight": 1.0
        },
        PaperType.REVIEW: {
            "title": [
                r'\bsurvey\b', r'\breview\b', r'\boverview\b',
                r'\bstate[\-\s]of[\-\s]the[\-\s]art\b'
            ],
            "abstract": [
                r'comprehensive\s+(survey|review|overview)',
                r'we\s+survey', r'recent\s+advances',
                r'this\s+(survey|review)\s+covers'
            ],
            "weight": 0.9
        },
        PaperType.METHOD: {
            "title": [
                r'\bnovel\b', r'\bproposed?\b', r'\bapproach\b',
                r'\bmethod\b', r'\bframework\b', r'\barchitecture\b'
            ],
            "abstract": [
                r'we\s+propose', r'novel\s+(method|approach|framework)',
                r'outperforms?\s+(state[\-\s]of[\-\s]the[\-\s]art|baseline)',
                r'experiments\s+show'
            ],
            "weight": 0.8
        },
        PaperType.APPLICATION: {
            "title": [
                r'\bapplication\b', r'\bcase\s+study\b',
                r'\bdeployment\b', r'\bin\s+practice\b'
            ],
            "abstract": [
                r'applied\s+to', r'real[\-\s]world\s+application',
                r'case\s+study', r'deployed\s+in'
            ],
            "weight": 0.7
        }
    }
    
    def classify(
        self, 
        doc: Document
    ) -> Tuple[PaperType, float]:
        """
        Classify document and return confidence score.
        
        Returns:
            (paper_type, confidence) tuple
        """
        scores = {pt: 0.0 for pt in PaperType}
        
        text = {
            "title": doc.title.lower(),
            "abstract": (doc.abstract or "").lower()[:1000]
        }
        
        for paper_type, config in self.PATTERNS.items():
            for field, patterns in config.items():
                if field == "weight":
                    continue
                
                field_text = text.get(field, "")
                if not field_text:
                    continue
                
                matches = sum(
                    1 for pattern in patterns 
                    if re.search(pattern, field_text, re.IGNORECASE)
                )
                
                scores[paper_type] += matches * config["weight"]
        
        # Normalize and select best
        if max(scores.values()) == 0:
            return PaperType.UNKNOWN, 0.0
        
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type] / sum(scores.values())
        
        return best_type, confidence
```

**ML-Based Classifier** (more accurate, requires training):

```python
# slr/classification/ml_classifier.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Tuple
from ..core.document import Document, PaperType

class TransformerClassifier:
    """
    Fine-tuned transformer model for paper classification.
    Can be trained on labeled data or use zero-shot classification.
    """
    
    def __init__(
        self,
        model_name: str = "allenai/scibert_scivocab_uncased",
        use_zero_shot: bool = True
    ):
        if use_zero_shot:
            from transformers import pipeline
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            self.labels = [pt.value for pt in PaperType if pt != PaperType.UNKNOWN]
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=len(PaperType) - 1  # excluding UNKNOWN
            )
    
    def classify(
        self, 
        doc: Document
    ) -> Tuple[PaperType, float]:
        """Classify using transformer model"""
        text = f"{doc.title} [SEP] {(doc.abstract or '')[:512]}"
        
        if hasattr(self, 'classifier'):
            # Zero-shot classification
            result = self.classifier(
                text,
                self.labels,
                hypothesis_template="This paper is about {}."
            )
            best_label = result['labels'][0]
            confidence = result['scores'][0]
            return PaperType(best_label), confidence
        else:
            # Fine-tuned model
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=1)
                confidence, predicted = torch.max(probs, dim=1)
            
            paper_type = list(PaperType)[predicted.item()]
            return paper_type, confidence.item()
```


### Phase 4: Configuration \& Documentation (Week 4)

#### 4.1 Flexible Configuration System

```python
# slr/utils/config.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml

class ProviderSettings(BaseModel):
    enabled: bool = True
    api_key: Optional[str] = None
    rate_limit: float = 1.0
    timeout: int = 30
    custom: Dict[str, Any] = Field(default_factory=dict)

class DeduplicationSettings(BaseModel):
    strategy: str = "hybrid"  # conservative, semantic, hybrid
    fuzzy_threshold: int = 97
    semantic_threshold: float = 0.92
    use_embeddings: bool = True
    embedding_model: str = "allenai/specter2"
    max_year_gap: int = 1

class ClassificationSettings(BaseModel):
    enabled: bool = True
    method: str = "heuristic"  # heuristic, ml, ensemble
    ml_model: Optional[str] = None
    confidence_threshold: float = 0.5

class SLRConfig(BaseModel):
    """Master configuration for SLR framework"""
    
    # General settings
    year_min: int = 2019
    language: str = "en"
    mailto: str
    
    # Provider configurations
    providers: Dict[str, ProviderSettings] = Field(default_factory=dict)
    
    # Deduplication
    deduplication: DeduplicationSettings = Field(
        default_factory=DeduplicationSettings
    )
    
    # Classification
    classification: ClassificationSettings = Field(
        default_factory=ClassificationSettings
    )
    
    # Output settings
    output_dir: Path = Path("./outputs")
    export_formats: List[str] = Field(default_factory=lambda: ["csv", "jsonl", "bibtex"])
    
    @classmethod
    def from_yaml(cls, path: Path) -> "SLRConfig":
        """Load configuration from YAML file"""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    def to_yaml(self, path: Path):
        """Save configuration to YAML file"""
        with open(path, "w") as f:
            yaml.dump(self.dict(), f, default_flow_style=False)
```

**Example config.yml**:

```yaml
mailto: your.email@example.com
year_min: 2019
language: en

providers:
  openalex:
    enabled: true
    rate_limit: 5.0
  crossref:
    enabled: true
    rate_limit: 1.0
  arxiv:
    enabled: true
    rate_limit: 0.5
  semantic_scholar:
    enabled: true
    api_key: ${S2_API_KEY}  # From environment
    rate_limit: 1.0

deduplication:
  strategy: hybrid
  fuzzy_threshold: 97
  semantic_threshold: 0.92
  use_embeddings: true
  embedding_model: allenai/specter2
  max_year_gap: 1

classification:
  enabled: true
  method: heuristic
  confidence_threshold: 0.6

output_dir: ./outputs
export_formats:
  - csv
  - jsonl
  - bibtex
  - ris
```


### Phase 5: Testing \& Documentation

#### 5.1 Comprehensive Test Suite

```python
# tests/unit/test_dedup/test_hybrid.py
import pytest
from slr.dedup.strategies.hybrid import HybridDeduplicator
from slr.core.document import Document, ExternalIds

def test_exact_doi_matching():
    """Test that documents with same DOI are merged"""
    docs = [
        Document(
            title="Test Paper",
            year=2023,
            provider="openalex",
            provider_id="1",
            external_ids=ExternalIds(doi="10.1234/test")
        ),
        Document(
            title="Test Paper",
            year=2023,
            provider="crossref",
            provider_id="2",
            external_ids=ExternalIds(doi="10.1234/test")
        )
    ]
    
    deduplicator = HybridDeduplicator()
    clusters = deduplicator.deduplicate(docs)
    
    assert len(clusters) == 1
    assert len(clusters[0].members) == 2

def test_fuzzy_matching_with_year_gap():
    """Test fuzzy matching respects year gap threshold"""
    docs = [
        Document(
            title="Machine Learning for Plant Disease Detection",
            year=2020,
            provider="openalex",
            provider_id="1",
            external_ids=ExternalIds()
        ),
        Document(
            title="Machine Learning for Plant Disease Detection",
            year=2023,  # 3 year gap
            provider="arxiv",
            provider_id="2",
            external_ids=ExternalIds()
        )
    ]
    
    deduplicator = HybridDeduplicator(max_year_gap=1)
    clusters = deduplicator.deduplicate(docs)
    
    # Should NOT merge due to year gap
    assert len(clusters) == 2
```


#### 5.2 Documentation Structure

Create comprehensive documentation:

1. **Architecture Guide** - Explain design decisions, abstractions
2. **Provider Development Guide** - How to add new providers
3. **Deduplication Strategies** - Explain each strategy, when to use
4. **Classification Guide** - Training custom classifiers
5. **API Reference** - Auto-generated from docstrings
6. **Tutorials** - End-to-end examples for different use cases

### Implementation Priority

**Week 1-2: Foundation**

1. Set up package structure
2. Create core abstractions (Document, Query, BaseProvider)
3. Refactor existing OpenAlex provider to new structure
4. Add comprehensive type hints and docstrings

**Week 2-3: Deduplication**

1. Extract current dedup logic into `conservative.py` strategy
2. Implement semantic deduplication with SPECTER2
3. Create hybrid strategy
4. Add extensive unit tests

**Week 3-4: Classification**

1. Implement heuristic classifier
2. Add zero-shot transformer classifier
3. Create ensemble classifier
4. Test on sample papers

**Week 4: Polish**

1. Configuration system
2. Documentation
3. Example scripts
4. Integration tests

This approach makes your framework:

- **UI-agnostic**: Core logic separate from interfaces
- **Extensible**: Easy to add providers, strategies, classifiers
- **Well-tested**: Comprehensive test coverage
- **Well-documented**: Clear for contributors and users
- **General-purpose**: Not tied to agricultural ML domain
