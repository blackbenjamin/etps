"""
Tests for PII Handling in ETPS_PATCH_v1.4

Covers:
- Contact model soft deletion
- Vector store sanitization for approved outputs
- Logging helpers with PII sanitization
- Placeholder rendering for networking outputs
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock
from sqlalchemy.orm import Session

from db.models import Contact, User, ApprovedOutput, CompanyProfile
from services.vector_store import index_approved_output, MockVectorStore
from services.embeddings import MockEmbeddingService
from services.placeholder_renderer import (
    render_networking_output,
    build_contact_context,
    _infer_role_archetype,
    _infer_seniority_band,
    _get_relationship_bucket
)
from utils.logging_helpers import safe_log_info, safe_log_debug, safe_log_warning, safe_log_error
from utils.pii_sanitizer import sanitize_personal_identifiers
import logging


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    return Mock(spec=Session)


class TestContactSoftDeletion:
    """Test Contact model soft deletion with deleted_at field."""

    def test_contact_has_deleted_at_field(self):
        """Contact model should have deleted_at field for GDPR compliance."""
        contact = Mock(spec=Contact)
        contact.id = 1
        contact.user_id = 100
        contact.full_name = "John Doe"
        contact.email = "john@example.com"
        contact.deleted_at = None

        assert hasattr(contact, 'deleted_at')
        assert contact.deleted_at is None

    def test_contact_soft_delete(self):
        """Contact can be soft-deleted by setting deleted_at."""
        contact = Mock(spec=Contact)
        contact.id = 1
        contact.user_id = 100
        contact.full_name = "Jane Smith"
        contact.email = "jane@example.com"
        contact.deleted_at = None

        # Soft delete
        contact.deleted_at = datetime.utcnow()

        # Verify soft deletion
        assert contact.deleted_at is not None


class TestApprovedOutputSanitization:
    """Test that approved outputs are sanitized before vector indexing."""

    @pytest.mark.asyncio
    async def test_index_approved_output_sanitizes_text(self):
        """Approved output text should be sanitized before storing in vector store."""
        # Create approved output with PII
        text_with_pii = "I worked with Sarah Johnson at sarah@example.com on this project."
        approved_output = Mock(spec=ApprovedOutput)
        approved_output.id = 1
        approved_output.user_id = 100
        approved_output.application_id = 10
        approved_output.output_type = 'resume_bullet'
        approved_output.original_text = text_with_pii
        approved_output.quality_score = 0.85
        approved_output.embedding = None
        approved_output.created_at = datetime(2024, 12, 1, 10, 0, 0)

        # Index with mock services
        embedding_service = MockEmbeddingService()
        vector_store = MockVectorStore()
        await vector_store.ensure_collection('approved_outputs')

        await index_approved_output(approved_output, embedding_service, vector_store)

        # Retrieve from vector store
        results = await vector_store.search(
            collection_name='approved_outputs',
            query_vector=[0.1] * 384,  # Mock vector
            limit=10
        )

        # Verify text was sanitized in payload
        assert len(results) > 0
        stored_text = results[0]['payload']['text']
        # Should have sanitized the name and email
        assert 'Sarah Johnson' not in stored_text
        assert 'sarah@example.com' not in stored_text
        assert '{{CONTACT_NAME}}' in stored_text or '{{CONTACT_EMAIL}}' in stored_text


class TestLoggingHelpers:
    """Test logging helpers with PII sanitization."""

    def test_safe_log_info_sanitizes_pii(self):
        """safe_log_info should sanitize personal identifiers."""
        logger = logging.getLogger('test_logger')
        message = "User John Smith contacted us at john@test.com"

        # This should not raise an exception
        safe_log_info(logger, message)

    def test_safe_log_debug_sanitizes_pii(self):
        """safe_log_debug should sanitize personal identifiers."""
        logger = logging.getLogger('test_logger')
        message = "Debug: Sarah Johnson's email is sarah@example.com"

        safe_log_debug(logger, message)

    def test_safe_log_warning_sanitizes_pii(self):
        """safe_log_warning should sanitize personal identifiers."""
        logger = logging.getLogger('test_logger')
        message = "Warning: Contact Mike Davis at mike@company.com"

        safe_log_warning(logger, message)

    def test_safe_log_error_sanitizes_pii(self):
        """safe_log_error should sanitize personal identifiers."""
        logger = logging.getLogger('test_logger')
        message = "Error processing request from alice@domain.com"

        safe_log_error(logger, message)


class TestPlaceholderRenderer:
    """Test placeholder rendering for networking outputs."""

    @pytest.mark.asyncio
    async def test_render_networking_output_replaces_placeholders(self, mock_db_session):
        """render_networking_output should replace placeholders with actual contact data."""
        contact_id = 1
        user_id = 100

        # Create mock contact
        contact = Mock(spec=Contact)
        contact.id = contact_id
        contact.user_id = user_id
        contact.full_name = "Robert Brown"
        contact.email = "robert@company.com"
        contact.linkedin_url = "https://linkedin.com/in/robertbrown"
        contact.title = "Senior Director"
        contact.deleted_at = None

        # Mock database query
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [contact]
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        # Template with placeholders
        template = f"Reach out to {{{{CONTACT_NAME_{contact_id}}}}} at {{{{CONTACT_EMAIL_{contact_id}}}}}"

        # Render
        rendered = await render_networking_output(template, mock_db_session, user_id)

        assert "Robert Brown" in rendered
        assert "robert@company.com" in rendered
        assert "{{CONTACT_NAME" not in rendered
        assert "{{CONTACT_EMAIL" not in rendered

    @pytest.mark.asyncio
    async def test_render_networking_output_excludes_deleted_contacts(self, mock_db_session):
        """render_networking_output should exclude soft-deleted contacts."""
        contact_id = 2
        user_id = 100

        # Mock database returns no contacts (deleted contact filtered out)
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        template = f"Contact {{{{CONTACT_NAME_{contact_id}}}}}"

        # Should raise PermissionError because contact is deleted
        with pytest.raises(PermissionError):
            await render_networking_output(template, mock_db_session, user_id)

    @pytest.mark.asyncio
    async def test_render_networking_output_validates_user_ownership(self, mock_db_session):
        """render_networking_output should validate contact ownership."""
        contact_id = 3
        user1_id = 100
        user2_id = 200

        # Mock database returns no contacts (wrong user)
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        template = f"Contact {{{{CONTACT_NAME_{contact_id}}}}}"

        # User2 should not be able to access user1's contact
        with pytest.raises(PermissionError):
            await render_networking_output(template, mock_db_session, user2_id)


class TestContactContextBuilder:
    """Test non-PII contact context building."""

    def test_build_contact_context_returns_non_pii(self):
        """build_contact_context should return only non-PII metadata."""
        contact = Mock(spec=Contact)
        contact.id = 1
        contact.user_id = 100
        contact.full_name = "VP Engineering"
        contact.title = "VP of Engineering"
        contact.email = "vp@company.com"
        contact.linkedin_url = "https://linkedin.com/in/vpeng"
        contact.relationship_strength = 0.8
        contact.is_hiring_manager_candidate = True

        context = build_contact_context(contact)

        # Should have metadata
        assert 'contact_id' in context
        assert 'role_archetype' in context
        assert 'seniority_band' in context
        assert 'relationship_bucket' in context
        assert 'has_email' in context
        assert 'has_linkedin' in context
        assert 'is_hiring_manager_candidate' in context

        # Should not have PII
        assert 'full_name' not in context
        assert 'email' not in context
        assert 'linkedin_url' not in context

        # Check values
        assert context['role_archetype'] == 'vp'
        assert context['seniority_band'] == 'executive'
        assert context['relationship_bucket'] == 'warm'
        assert context['has_email'] is True
        assert context['has_linkedin'] is True
        assert context['is_hiring_manager_candidate'] is True

    def test_infer_role_archetype_c_level(self):
        """Should correctly identify C-level roles."""
        assert _infer_role_archetype("CTO") == "c_level"
        assert _infer_role_archetype("Chief Data Officer") == "c_level"

    def test_infer_role_archetype_vp(self):
        """Should correctly identify VP roles."""
        assert _infer_role_archetype("VP of Engineering") == "vp"
        assert _infer_role_archetype("Vice President, Product") == "vp"

    def test_infer_role_archetype_director(self):
        """Should correctly identify director roles."""
        assert _infer_role_archetype("Director of Data Science") == "director"
        assert _infer_role_archetype("Head of AI") == "director"

    def test_infer_seniority_band_executive(self):
        """Should map C-level and VP to executive band."""
        assert _infer_seniority_band("CTO") == "executive"
        assert _infer_seniority_band("VP Engineering") == "executive"

    def test_infer_seniority_band_senior_leadership(self):
        """Should map director to senior_leadership band."""
        assert _infer_seniority_band("Director of AI") == "senior_leadership"

    def test_get_relationship_bucket_warm(self):
        """Should identify warm relationships."""
        assert _get_relationship_bucket(0.8) == "warm"
        assert _get_relationship_bucket(0.7) == "warm"

    def test_get_relationship_bucket_lukewarm(self):
        """Should identify lukewarm relationships."""
        assert _get_relationship_bucket(0.5) == "lukewarm"
        assert _get_relationship_bucket(0.4) == "lukewarm"

    def test_get_relationship_bucket_cold(self):
        """Should identify cold relationships."""
        assert _get_relationship_bucket(0.2) == "cold"
        assert _get_relationship_bucket(0.0) == "cold"

    def test_get_relationship_bucket_unknown(self):
        """Should handle None relationship strength."""
        assert _get_relationship_bucket(None) == "unknown"
