"""Tests for core models."""

from datetime import datetime, timezone


from slr.core.models import Author, Document, DocumentCluster, ExternalIds, Query, SearchResult


class TestExternalIds:
    """Tests for ExternalIds model."""

    def test_external_ids_doi_normalization_https(self):
        """Test that DOI normalization removes https://doi.org/ prefix."""
        ids = ExternalIds(doi="https://doi.org/10.1234/test")
        assert ids.doi == "10.1234/test"

    def test_external_ids_doi_normalization_http_dx(self):
        """Test that DOI normalization removes http://dx.doi.org/ prefix."""
        ids = ExternalIds(doi="http://dx.doi.org/10.1234/test")
        assert ids.doi == "10.1234/test"

    def test_external_ids_doi_normalization_prefix(self):
        """Test that DOI normalization removes doi: prefix."""
        ids = ExternalIds(doi="doi: 10.1234/TEST")
        assert ids.doi == "10.1234/test"

    def test_external_ids_doi_normalization_lowercase(self):
        """Test that DOI normalization converts to lowercase."""
        ids = ExternalIds(doi="10.1234/TEST")
        assert ids.doi == "10.1234/test"

    def test_external_ids_doi_normalization_none(self):
        """Test that None DOI remains None."""
        ids = ExternalIds(doi=None)
        assert ids.doi is None

    def test_external_ids_all_fields(self):
        """Test creating ExternalIds with all fields."""
        ids = ExternalIds(
            doi="10.1234/test",
            arxiv_id="2301.12345",
            pubmed_id="12345678",
            openalex_id="W123456789",
            s2_id="abc123",
        )
        assert ids.doi == "10.1234/test"
        assert ids.arxiv_id == "2301.12345"
        assert ids.pubmed_id == "12345678"
        assert ids.openalex_id == "W123456789"
        assert ids.s2_id == "abc123"

    def test_external_ids_empty(self):
        """Test creating empty ExternalIds."""
        ids = ExternalIds()
        assert ids.doi is None
        assert ids.arxiv_id is None
        assert ids.pubmed_id is None
        assert ids.openalex_id is None
        assert ids.s2_id is None


class TestAuthor:
    """Tests for Author model."""

    def test_author_full_name_with_given(self):
        """Test author full name property with given name."""
        author = Author(given_name="John", family_name="Doe")
        assert author.full_name == "John Doe"

    def test_author_full_name_without_given(self):
        """Test author full name property without given name."""
        author = Author(family_name="Smith")
        assert author.full_name == "Smith"

    def test_author_with_orcid(self):
        """Test author with ORCID."""
        author = Author(
            given_name="Jane",
            family_name="Doe",
            orcid="0000-0001-2345-6789",
        )
        assert author.orcid == "0000-0001-2345-6789"
        assert author.full_name == "Jane Doe"

    def test_author_minimal(self):
        """Test author with only family name."""
        author = Author(family_name="Einstein")
        assert author.family_name == "Einstein"
        assert author.given_name is None
        assert author.orcid is None


class TestDocument:
    """Tests for Document model."""

    def test_document_minimal_creation(self):
        """Test document model creation with minimal fields."""
        doc = Document(
            title="Test Paper",
            provider="openalex",
            provider_id="W123456",
        )
        assert doc.title == "Test Paper"
        assert doc.provider == "openalex"
        assert doc.provider_id == "W123456"
        assert doc.year is None
        assert doc.abstract is None

    def test_document_with_external_ids(self):
        """Test document with external IDs."""
        doc = Document(
            title="Test Paper",
            year=2020,
            provider="openalex",
            provider_id="W123456",
            external_ids=ExternalIds(doi="10.1234/test"),
        )
        assert doc.external_ids.doi == "10.1234/test"

    def test_document_with_authors(self):
        """Test document with authors."""
        authors = [
            Author(given_name="John", family_name="Doe"),
            Author(family_name="Smith"),
        ]
        doc = Document(
            title="Test Paper",
            provider="openalex",
            provider_id="W123456",
            authors=authors,
        )
        assert len(doc.authors) == 2
        assert doc.authors[0].full_name == "John Doe"
        assert doc.authors[1].full_name == "Smith"

    def test_document_all_fields(self):
        """Test document with all fields populated."""
        doc = Document(
            title="Machine Learning for Plant Disease Detection",
            year=2020,
            provider="openalex",
            provider_id="W123456789",
            external_ids=ExternalIds(
                doi="10.1234/test",
                arxiv_id="2301.12345",
            ),
            abstract="This paper presents a novel approach...",
            authors=[Author(given_name="John", family_name="Doe")],
            venue="Nature Machine Intelligence",
            url="https://example.com/paper",
            language="en",
            cited_by_count=42,
            query_id="Q01",
            query_text="machine learning plant disease",
            retrieved_at=datetime(2023, 1, 15, 10, 30, 0),
            cluster_id=5,
        )
        assert doc.title == "Machine Learning for Plant Disease Detection"
        assert doc.year == 2020
        assert doc.external_ids.doi == "10.1234/test"
        assert doc.venue == "Nature Machine Intelligence"
        assert doc.cited_by_count == 42
        assert doc.cluster_id == 5

    def test_document_default_external_ids(self):
        """Test that external_ids is created by default."""
        doc = Document(
            title="Test",
            provider="openalex",
            provider_id="W123",
        )
        assert isinstance(doc.external_ids, ExternalIds)
        assert doc.external_ids.doi is None

    def test_document_default_authors_list(self):
        """Test that authors list is created empty by default."""
        doc = Document(
            title="Test",
            provider="openalex",
            provider_id="W123",
        )
        assert isinstance(doc.authors, list)
        assert len(doc.authors) == 0

    def test_document_raw_data_excluded(self):
        """Test that raw_data is excluded from serialization."""
        doc = Document(
            title="Test",
            provider="openalex",
            provider_id="W123",
            raw_data={"original": "data"},
        )
        # Check that raw_data exists
        assert doc.raw_data == {"original": "data"}
        # Check that it's excluded from dict
        doc_dict = doc.model_dump()
        assert "raw_data" not in doc_dict


class TestQuery:
    """Tests for Query model."""

    def test_query_minimal_creation(self):
        """Test query model creation with minimal fields."""
        query = Query(
            id="Q01",
            text="machine learning plant disease",
        )
        assert query.id == "Q01"
        assert query.text == "machine learning plant disease"
        assert query.language == "en"  # Default

    def test_query_with_year_filters(self):
        """Test query with year filters."""
        query = Query(
            id="Q01",
            text="machine learning",
            year_min=2019,
            year_max=2023,
        )
        assert query.year_min == 2019
        assert query.year_max == 2023

    def test_query_with_max_results(self):
        """Test query with max_results limit."""
        query = Query(
            id="Q02",
            text="deep learning",
            max_results=100,
        )
        assert query.max_results == 100

    def test_query_with_metadata(self):
        """Test query with custom metadata."""
        query = Query(
            id="Q03",
            text="neural networks",
            metadata={"category": "AI", "priority": "high"},
        )
        assert query.metadata["category"] == "AI"
        assert query.metadata["priority"] == "high"

    def test_query_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        query = Query(id="Q01", text="test")
        assert isinstance(query.metadata, dict)
        assert len(query.metadata) == 0

    def test_query_custom_language(self):
        """Test query with custom language."""
        query = Query(
            id="Q01",
            text="apprentissage automatique",
            language="fr",
        )
        assert query.language == "fr"


class TestDocumentCluster:
    """Tests for DocumentCluster model."""

    def test_cluster_size_property(self):
        """Test cluster size property."""
        doc1 = Document(title="Test 1", provider="openalex", provider_id="1")
        doc2 = Document(title="Test 2", provider="crossref", provider_id="2")
        doc3 = Document(title="Test 3", provider="arxiv", provider_id="3")

        cluster = DocumentCluster(
            cluster_id=1,
            representative=doc1,
            members=[doc1, doc2, doc3],
        )
        assert cluster.size == 3

    def test_cluster_confidence_with_doi_match(self):
        """Test confidence is 1.0 with exact DOI match."""
        doc1 = Document(
            title="Test",
            provider="openalex",
            provider_id="1",
            external_ids=ExternalIds(doi="10.1234/test"),
        )
        doc2 = Document(
            title="Test",
            provider="crossref",
            provider_id="2",
            external_ids=ExternalIds(doi="10.1234/test"),
        )

        cluster = DocumentCluster(
            cluster_id=1,
            representative=doc1,
            members=[doc1, doc2],
            all_dois=["10.1234/test"],
        )
        assert cluster.confidence == 1.0  # Exact DOI match

    def test_cluster_confidence_with_arxiv_match(self):
        """Test confidence is 1.0 with exact arXiv match."""
        doc1 = Document(
            title="Test",
            provider="arxiv",
            provider_id="1",
            external_ids=ExternalIds(arxiv_id="2301.12345"),
        )
        doc2 = Document(
            title="Test",
            provider="s2",
            provider_id="2",
            external_ids=ExternalIds(arxiv_id="2301.12345"),
        )

        cluster = DocumentCluster(
            cluster_id=1,
            representative=doc1,
            members=[doc1, doc2],
            all_arxiv_ids=["2301.12345"],
        )
        assert cluster.confidence == 1.0  # Exact arXiv match

    def test_cluster_confidence_fuzzy_match(self):
        """Test confidence is 0.95 for fuzzy matches."""
        doc1 = Document(title="Test Paper", provider="openalex", provider_id="1")
        doc2 = Document(title="Test Paper", provider="crossref", provider_id="2")

        cluster = DocumentCluster(
            cluster_id=1,
            representative=doc1,
            members=[doc1, doc2],
        )
        assert cluster.confidence == 0.95  # Fuzzy match

    def test_cluster_with_provider_counts(self):
        """Test cluster with provider counts."""
        doc1 = Document(title="Test", provider="openalex", provider_id="1")
        doc2 = Document(title="Test", provider="crossref", provider_id="2")
        doc3 = Document(title="Test", provider="openalex", provider_id="3")

        cluster = DocumentCluster(
            cluster_id=1,
            representative=doc1,
            members=[doc1, doc2, doc3],
            provider_counts={"openalex": 2, "crossref": 1},
        )
        assert cluster.provider_counts["openalex"] == 2
        assert cluster.provider_counts["crossref"] == 1

    def test_cluster_aggregated_ids(self):
        """Test cluster with aggregated IDs."""
        doc1 = Document(
            title="Test",
            provider="openalex",
            provider_id="1",
            external_ids=ExternalIds(doi="10.1234/test1"),
        )
        doc2 = Document(
            title="Test",
            provider="crossref",
            provider_id="2",
            external_ids=ExternalIds(doi="10.1234/test2", arxiv_id="2301.12345"),
        )

        cluster = DocumentCluster(
            cluster_id=1,
            representative=doc1,
            members=[doc1, doc2],
            all_dois=["10.1234/test1", "10.1234/test2"],
            all_arxiv_ids=["2301.12345"],
        )
        assert len(cluster.all_dois) == 2
        assert len(cluster.all_arxiv_ids) == 1


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_search_result_creation(self):
        """Test search result container creation."""
        query = Query(id="Q01", text="test")
        doc = Document(title="Test", provider="openalex", provider_id="1")

        result = SearchResult(
            query=query,
            documents=[doc],
            total_found=1,
            provider="openalex",
        )

        assert result.query.id == "Q01"
        assert len(result.documents) == 1
        assert result.provider == "openalex"
        assert result.total_found == 1
        assert isinstance(result.timestamp, datetime)

    def test_search_result_with_multiple_documents(self):
        """Test search result with multiple documents."""
        query = Query(id="Q01", text="machine learning")
        docs = [
            Document(title=f"Paper {i}", provider="openalex", provider_id=str(i)) for i in range(5)
        ]

        result = SearchResult(
            query=query,
            documents=docs,
            total_found=100,  # More found than returned
            provider="openalex",
        )

        assert len(result.documents) == 5
        assert result.total_found == 100

    def test_search_result_with_errors(self):
        """Test search result with errors."""
        query = Query(id="Q01", text="test")

        result = SearchResult(
            query=query,
            documents=[],
            total_found=0,
            provider="openalex",
            errors=["Rate limit exceeded", "Connection timeout"],
        )

        assert len(result.errors) == 2
        assert "Rate limit exceeded" in result.errors

    def test_search_result_default_timestamp(self):
        """Test that timestamp is auto-generated."""
        query = Query(id="Q01", text="test")
        result = SearchResult(
            query=query,
            documents=[],
            total_found=0,
            provider="openalex",
        )

        assert isinstance(result.timestamp, datetime)
        # Should be recent (within last minute)
        assert (datetime.now(timezone.utc) - result.timestamp).total_seconds() < 60

    def test_search_result_default_errors(self):
        """Test that errors defaults to empty list."""
        query = Query(id="Q01", text="test")
        result = SearchResult(
            query=query,
            documents=[],
            total_found=0,
            provider="openalex",
        )

        assert isinstance(result.errors, list)
        assert len(result.errors) == 0
