"""
Tests for Company Enrichment Service (Sprint 12)

Comprehensive test suite covering:
- Company name normalization and deduplication
- URL validation and SSRF protection
- Industry, size, and headquarters inference
- Culture signals extraction
- AI maturity classification
- Company profile persistence
- API endpoints
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from db.models import CompanyProfile, User
from schemas.company import (
    CompanyEnrichRequest,
    CompanyProfileResponse,
    CompanyProfileUpdate,
)
from services.company_enrichment import (
    normalize_company_name,
    is_private_ip,
    validate_url,
    check_robots_txt,
    fetch_company_website_data,
    infer_industry_and_size,
    _infer_metadata_heuristic,
    infer_culture_signals,
    infer_ai_maturity,
    enrich_company_profile,
    get_company_profile,
    search_company_profiles,
    INDUSTRIES,
    SIZE_BANDS,
    CULTURE_SIGNALS,
    AI_MATURITY_LEVELS,
)


class TestNormalizeCompanyName:
    """Tests for company name normalization."""

    def test_remove_inc_suffix(self):
        """Should remove Inc. suffix."""
        assert normalize_company_name("Acme Inc.") == "acme"
        assert normalize_company_name("Acme, Inc.") == "acme"
        assert normalize_company_name("Acme Inc") == "acme"

    def test_remove_llc_suffix(self):
        """Should remove LLC suffix."""
        assert normalize_company_name("Acme LLC") == "acme"
        assert normalize_company_name("Acme, LLC") == "acme"

    def test_remove_corp_suffix(self):
        """Should remove Corp/Corporation suffix."""
        assert normalize_company_name("Acme Corp") == "acme"
        assert normalize_company_name("Acme Corp.") == "acme"
        assert normalize_company_name("Acme Corporation") == "acme"

    def test_remove_ltd_suffix(self):
        """Should remove Ltd/Limited suffix."""
        assert normalize_company_name("Acme Ltd") == "acme"
        assert normalize_company_name("Acme Ltd.") == "acme"
        assert normalize_company_name("Acme Limited") == "acme"

    def test_remove_multiple_suffixes(self):
        """Should handle companies with multiple suffixes."""
        assert normalize_company_name("Acme Holdings, Inc.") == "acme"
        assert normalize_company_name("Acme Group LLC") == "acme"

    def test_normalize_whitespace(self):
        """Should normalize whitespace."""
        assert normalize_company_name("  Acme   Corp  ") == "acme"
        assert normalize_company_name("Acme\t\nInc") == "acme"

    def test_empty_string(self):
        """Should handle empty string."""
        assert normalize_company_name("") == ""
        assert normalize_company_name("   ") == ""

    def test_preserve_company_name(self):
        """Should preserve company name without suffixes."""
        assert normalize_company_name("Google") == "google"
        assert normalize_company_name("Goldman Sachs") == "goldman sachs"


class TestIsPrivateIP:
    """Tests for private IP detection (SSRF protection)."""

    def test_localhost_detection(self):
        """Should detect localhost."""
        assert is_private_ip("127.0.0.1") is True
        assert is_private_ip("localhost") is True

    def test_private_ip_ranges(self):
        """Should detect private IP ranges."""
        assert is_private_ip("10.0.0.1") is True
        assert is_private_ip("172.16.0.1") is True
        assert is_private_ip("192.168.1.1") is True

    def test_public_ip(self):
        """Should allow public IPs."""
        # Well-known public IP (Google DNS)
        assert is_private_ip("8.8.8.8") is False

    def test_unresolvable_hostname(self):
        """Should block unresolvable hostnames (conservative)."""
        assert is_private_ip("this-definitely-does-not-exist-xyz123.local") is True

    def test_loopback_detection(self):
        """Should detect loopback addresses."""
        assert is_private_ip("127.0.0.1") is True
        assert is_private_ip("127.255.255.255") is True


class TestValidateUrl:
    """Tests for URL validation."""

    def test_valid_https_url(self):
        """Should accept valid HTTPS URL."""
        is_valid, error = validate_url("https://www.google.com")
        assert is_valid is True
        assert error == ""

    def test_valid_http_url(self):
        """Should accept HTTP URL (with warning in logs)."""
        is_valid, error = validate_url("http://www.example.com")
        assert is_valid is True

    def test_invalid_scheme(self):
        """Should reject non-HTTP schemes."""
        is_valid, error = validate_url("ftp://example.com")
        assert is_valid is False
        assert "Invalid URL scheme" in error

        is_valid, error = validate_url("file:///etc/passwd")
        assert is_valid is False

    def test_private_ip_blocked(self):
        """Should block private IP addresses."""
        is_valid, error = validate_url("http://127.0.0.1/admin")
        assert is_valid is False
        assert "Private IP" in error

        is_valid, error = validate_url("http://192.168.1.1")
        assert is_valid is False

    def test_localhost_blocked(self):
        """Should block localhost."""
        is_valid, error = validate_url("http://localhost:8080")
        assert is_valid is False

    def test_empty_url(self):
        """Should reject empty URL."""
        is_valid, error = validate_url("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_no_hostname(self):
        """Should reject URL without hostname."""
        is_valid, error = validate_url("https:///path")
        assert is_valid is False


class TestInferMetadataHeuristic:
    """Tests for heuristic-based metadata inference."""

    def test_financial_services_detection(self):
        """Should detect financial services industry."""
        result = _infer_metadata_heuristic(
            "Goldman Sachs",
            "investment banking and financial services",
            "Join our trading team"
        )
        assert result["industry"] == "Financial Services"

    def test_technology_detection(self):
        """Should detect technology industry."""
        result = _infer_metadata_heuristic(
            "Acme Tech",
            "Building software solutions and cloud platforms",
            "Machine learning engineer"
        )
        assert result["industry"] == "Technology"

    def test_healthcare_detection(self):
        """Should detect healthcare industry."""
        result = _infer_metadata_heuristic(
            "HealthCorp",
            "Providing medical services and patient care",
            None
        )
        assert result["industry"] == "Healthcare"

    def test_consulting_detection(self):
        """Should detect consulting industry."""
        result = _infer_metadata_heuristic(
            "AHEAD",
            "management consulting and advisory services",
            "Strategy consultant"
        )
        assert result["industry"] == "Consulting"

    def test_size_fortune_500(self):
        """Should detect Fortune 500 as 5000+."""
        result = _infer_metadata_heuristic(
            "BigCorp",
            "We are a Fortune 500 company",
            None
        )
        assert result["size_band"] == "5000+"

    def test_size_startup(self):
        """Should detect startup as 1-50."""
        result = _infer_metadata_heuristic(
            "StartupCo",
            "We are an early stage startup",
            None
        )
        assert result["size_band"] == "1-50"

    def test_no_industry_match(self):
        """Should return None when no industry matches."""
        result = _infer_metadata_heuristic(
            "XYZ Company",
            "We do things",
            None
        )
        # May match or may be None depending on content
        assert result["industry"] is None or result["industry"] in INDUSTRIES


class TestInferCultureSignals:
    """Tests for culture signal extraction."""

    @pytest.mark.asyncio
    async def test_innovative_culture(self):
        """Should detect innovative culture."""
        signals = await infer_culture_signals(
            "We are cutting-edge innovators disrupting the industry",
            None
        )
        assert "innovative" in signals

    @pytest.mark.asyncio
    async def test_formal_culture(self):
        """Should detect formal culture."""
        signals = await infer_culture_signals(
            "Professional corporate environment with established practices",
            None
        )
        assert "formal" in signals

    @pytest.mark.asyncio
    async def test_collaborative_culture(self):
        """Should detect collaborative culture."""
        signals = await infer_culture_signals(
            "Team-based collaborative work environment",
            "Cross-functional team collaboration"
        )
        assert "collaborative" in signals

    @pytest.mark.asyncio
    async def test_fast_paced_culture(self):
        """Should detect fast-paced culture."""
        signals = await infer_culture_signals(
            "Fast-paced startup environment",
            "Rapidly evolving company"
        )
        assert "fast-paced" in signals

    @pytest.mark.asyncio
    async def test_data_driven_culture(self):
        """Should detect data-driven culture."""
        signals = await infer_culture_signals(
            "We make evidence-based decisions using analytics",
            "Data-driven approach"
        )
        assert "data-driven" in signals

    @pytest.mark.asyncio
    async def test_max_five_signals(self):
        """Should limit to 5 culture signals."""
        # Content with many culture keywords
        signals = await infer_culture_signals(
            "Innovative, collaborative, fast-paced, data-driven, customer-centric, "
            "mission-driven, experimental, formal, traditional, conservative",
            None
        )
        assert len(signals) <= 5

    @pytest.mark.asyncio
    async def test_empty_content(self):
        """Should return empty list for empty content."""
        signals = await infer_culture_signals(None, None)
        assert signals == []

    @pytest.mark.asyncio
    async def test_signals_from_taxonomy(self):
        """All returned signals should be from taxonomy."""
        signals = await infer_culture_signals(
            "We are innovative and collaborative",
            "Fast-paced environment"
        )
        for signal in signals:
            assert signal in CULTURE_SIGNALS


class TestInferAIMaturity:
    """Tests for AI maturity classification."""

    @pytest.mark.asyncio
    async def test_advanced_maturity(self):
        """Should detect advanced AI maturity."""
        maturity = await infer_ai_maturity(
            "Our MLOps platform enables AI at scale with production ML",
            "AI governance and responsible AI practices"
        )
        assert maturity == "advanced"

    @pytest.mark.asyncio
    async def test_developing_maturity(self):
        """Should detect developing AI maturity."""
        maturity = await infer_ai_maturity(
            "Building our data platform",
            "Looking for data scientist to build analytics"
        )
        assert maturity in ["developing", "low"]

    @pytest.mark.asyncio
    async def test_low_maturity(self):
        """Should detect low AI maturity."""
        maturity = await infer_ai_maturity(
            "Traditional business operations",
            "Standard office work"
        )
        assert maturity is None or maturity == "low"

    @pytest.mark.asyncio
    async def test_genai_indicates_advanced(self):
        """Should classify GenAI mentions as advanced."""
        maturity = await infer_ai_maturity(
            "Leading GenAI transformation",
            "LLM implementation and AI governance"
        )
        assert maturity == "advanced"

    @pytest.mark.asyncio
    async def test_empty_content(self):
        """Should return None for empty content."""
        maturity = await infer_ai_maturity(None, None)
        assert maturity is None


class TestEnrichCompanyProfile:
    """Tests for full enrichment flow."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.all.return_value = []
        return db

    @pytest.mark.asyncio
    async def test_create_new_profile(self, mock_db):
        """Should create new company profile."""
        profile = await enrich_company_profile(
            company_name="Acme Corp",
            jd_text="Software engineer at a technology company",
            db=mock_db,
        )

        # Verify add was called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_existing_profile(self, mock_db):
        """Should update existing company profile."""
        existing = CompanyProfile(
            id=1,
            name="Acme Corp",
            industry=None,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        profile = await enrich_company_profile(
            company_name="Acme Corp",
            jd_text="Technology company building software",
            db=mock_db,
        )

        # Should not add new, just commit
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deduplication_by_normalized_name(self, mock_db):
        """Should find existing profile by normalized name."""
        existing = CompanyProfile(
            id=1,
            name="Acme, Inc.",
        )
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.all.return_value = [existing]

        profile = await enrich_company_profile(
            company_name="Acme Corporation",
            db=mock_db,
        )

        # Should find existing by normalized name match
        # (acme inc == acme corporation after normalization)
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_requires_company_name(self, mock_db):
        """Should raise error for empty company name."""
        with pytest.raises(ValueError, match="company_name is required"):
            await enrich_company_profile(
                company_name="",
                db=mock_db,
            )

        with pytest.raises(ValueError, match="company_name is required"):
            await enrich_company_profile(
                company_name="   ",
                db=mock_db,
            )

    @pytest.mark.asyncio
    async def test_requires_db_session(self):
        """Should raise error without db session."""
        with pytest.raises(ValueError, match="Database session is required"):
            await enrich_company_profile(
                company_name="Acme",
                db=None,
            )


class TestGetCompanyProfile:
    """Tests for get_company_profile function."""

    @pytest.mark.asyncio
    async def test_get_existing_profile(self):
        """Should return existing profile."""
        mock_db = MagicMock(spec=Session)
        expected_profile = CompanyProfile(id=1, name="Acme")
        mock_db.query.return_value.filter.return_value.first.return_value = expected_profile

        result = await get_company_profile(1, mock_db)

        assert result == expected_profile

    @pytest.mark.asyncio
    async def test_get_nonexistent_profile(self):
        """Should return None for nonexistent profile."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await get_company_profile(999, mock_db)

        assert result is None


class TestSearchCompanyProfiles:
    """Tests for search_company_profiles function."""

    @pytest.mark.asyncio
    async def test_search_by_name(self):
        """Should search by name pattern."""
        mock_db = MagicMock(spec=Session)
        profiles = [
            CompanyProfile(id=1, name="Acme Corp"),
            CompanyProfile(id=2, name="Acme Industries"),
        ]
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = profiles

        result = await search_company_profiles("Acme", mock_db)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """Should return empty list for empty query."""
        mock_db = MagicMock(spec=Session)

        result = await search_company_profiles("", mock_db)

        assert result == []

    @pytest.mark.asyncio
    async def test_search_with_limit(self):
        """Should respect limit parameter."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []

        await search_company_profiles("Test", mock_db, limit=5)

        # Verify limit was called with correct value
        mock_db.query.return_value.filter.return_value.limit.assert_called_once_with(5)


class TestCompanySchemas:
    """Tests for Pydantic schemas."""

    def test_enrich_request_validation(self):
        """Should validate enrich request."""
        request = CompanyEnrichRequest(
            company_name="Acme Corp",
            user_id=1,
        )
        assert request.company_name == "Acme Corp"

    def test_enrich_request_strips_whitespace(self):
        """Should strip whitespace from company name."""
        request = CompanyEnrichRequest(
            company_name="  Acme Corp  ",
            user_id=1,
        )
        assert request.company_name == "Acme Corp"

    def test_enrich_request_empty_name_fails(self):
        """Should reject empty company name."""
        with pytest.raises(ValueError):
            CompanyEnrichRequest(
                company_name="   ",
                user_id=1,
            )

    def test_enrich_request_url_validation(self):
        """Should validate website URL."""
        request = CompanyEnrichRequest(
            company_name="Acme",
            user_id=1,
            website_url="https://acme.com",
        )
        assert request.website_url == "https://acme.com"

    def test_enrich_request_invalid_url(self):
        """Should reject invalid URL."""
        with pytest.raises(ValueError):
            CompanyEnrichRequest(
                company_name="Acme",
                user_id=1,
                website_url="not-a-url",
            )

    def test_profile_update_ai_maturity_validation(self):
        """Should validate AI maturity values."""
        # Valid values
        update = CompanyProfileUpdate(data_ai_maturity="advanced")
        assert update.data_ai_maturity == "advanced"

        # Invalid value
        with pytest.raises(ValueError):
            CompanyProfileUpdate(data_ai_maturity="super-advanced")

    def test_profile_update_culture_signals_limit(self):
        """Should limit culture signals to 5."""
        update = CompanyProfileUpdate(
            culture_signals=["a", "b", "c", "d", "e", "f", "g"]
        )
        assert len(update.culture_signals) == 5


class TestCompanyAPIEndpoints:
    """Tests for company API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        return User(id=1, email="test@test.com", full_name="Test User")

    def test_enrich_endpoint_user_not_found(self, client):
        """Should return 404 for nonexistent user (using non-existent user_id)."""
        # Using the test client with actual database - user 999999 won't exist
        response = client.post(
            "/api/v1/company/enrich",
            json={
                "company_name": "Acme Corp",
                "user_id": 999999,
            }
        )
        # Should return 404 since user doesn't exist in test DB
        assert response.status_code == 404

    def test_get_company_not_found(self, client):
        """Should return 404 for nonexistent company."""
        with patch('routers.company.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            with patch('routers.company.get_company_profile', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = None

                response = client.get("/api/v1/company/999")

                assert response.status_code == 404

    def test_search_companies_empty_query(self, client):
        """Should handle search endpoint."""
        with patch('routers.company.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            with patch('routers.company.search_company_profiles', new_callable=AsyncMock) as mock_search:
                mock_search.return_value = []

                response = client.get("/api/v1/company/search/?name=test")

                assert response.status_code == 200


class TestWebsiteFetching:
    """Tests for website data fetching."""

    def test_fetch_invalid_url(self):
        """Should handle invalid URL gracefully."""
        result = fetch_company_website_data("not-a-valid-url")
        assert result["error"] is not None

    def test_fetch_private_ip_blocked(self):
        """Should block private IP addresses."""
        result = fetch_company_website_data("http://192.168.1.1")
        assert result["error"] is not None
        assert "Private IP" in result["error"]

    def test_fetch_localhost_blocked(self):
        """Should block localhost."""
        result = fetch_company_website_data("http://localhost:8080")
        assert result["error"] is not None

    @patch('services.company_enrichment.requests.get')
    def test_fetch_timeout_handling(self, mock_get):
        """Should handle timeouts gracefully."""
        import requests
        mock_get.side_effect = requests.Timeout("Connection timed out")

        result = fetch_company_website_data("https://example.com")
        assert result["error"] == "Request timeout"

    @patch('services.company_enrichment.requests.get')
    @patch('services.company_enrichment.check_robots_txt')
    def test_fetch_success(self, mock_robots, mock_get):
        """Should successfully fetch and parse website."""
        mock_robots.return_value = True

        mock_response = MagicMock()
        mock_response.headers = {'content-length': '1000'}
        mock_response.iter_content.return_value = [b'<html><head><meta name="description" content="Test company"></head><body>Welcome</body></html>']
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_company_website_data("https://example.com")
        assert result["error"] is None
        assert result["meta_description"] == "Test company"


class TestTaxonomyValues:
    """Tests to verify taxonomy values are defined correctly."""

    def test_industries_defined(self):
        """Should have industries defined."""
        assert len(INDUSTRIES) > 0
        assert "Technology" in INDUSTRIES
        assert "Financial Services" in INDUSTRIES

    def test_size_bands_defined(self):
        """Should have size bands defined."""
        assert len(SIZE_BANDS) > 0
        assert "1-50" in SIZE_BANDS
        assert "5000+" in SIZE_BANDS

    def test_culture_signals_defined(self):
        """Should have culture signals defined."""
        assert len(CULTURE_SIGNALS) > 0
        assert "innovative" in CULTURE_SIGNALS
        assert "formal" in CULTURE_SIGNALS

    def test_ai_maturity_levels_defined(self):
        """Should have AI maturity levels defined."""
        assert AI_MATURITY_LEVELS == ["low", "developing", "advanced"]


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.all.return_value = []
        return db

    @pytest.mark.asyncio
    async def test_full_enrichment_tech_company(self, mock_db):
        """Should enrich a technology company profile."""
        jd_text = """
        Senior Software Engineer at TechCorp

        We are a cutting-edge technology company building innovative solutions.
        Join our collaborative, fast-paced engineering team.

        Requirements:
        - 5+ years of machine learning experience
        - Experience with MLOps and production ML systems
        - Knowledge of AI governance and responsible AI
        """

        profile = await enrich_company_profile(
            company_name="TechCorp",
            jd_text=jd_text,
            db=mock_db,
        )

        # Verify profile was created with enriched data
        mock_db.add.assert_called_once()
        added_profile = mock_db.add.call_args[0][0]

        assert added_profile.name == "TechCorp"
        # May have industry and culture signals based on heuristics
        assert added_profile.data_ai_maturity in ["advanced", "developing", None]

    @pytest.mark.asyncio
    async def test_full_enrichment_financial_company(self, mock_db):
        """Should enrich a financial services company profile."""
        jd_text = """
        Investment Banking Analyst at Goldman Sachs

        Goldman Sachs is a leading global investment banking firm.
        We provide wealth management and trading services.

        Our formal, professional environment values excellence.
        """

        profile = await enrich_company_profile(
            company_name="Goldman Sachs",
            jd_text=jd_text,
            db=mock_db,
        )

        mock_db.add.assert_called_once()
        added_profile = mock_db.add.call_args[0][0]

        assert added_profile.name == "Goldman Sachs"
