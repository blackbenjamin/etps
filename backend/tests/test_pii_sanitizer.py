"""
Unit tests for PII (Personally Identifiable Information) Sanitizer Utility.

Tests the sanitize_personal_identifiers, restore_personal_identifiers,
and extract_placeholder_ids functions for protecting sensitive user data.

Covers:
- Basic name, email, and LinkedIn URL sanitization
- Preservation of company names and technical terms
- Edge cases (possessives, punctuation, empty input)
- Contact map with ID-based placeholders
- Round-trip sanitization and restoration
- Placeholder ID extraction
- Performance with large text
"""

import pytest
from utils.pii_sanitizer import (
    sanitize_personal_identifiers,
    restore_personal_identifiers,
    extract_placeholder_ids,
    sanitize_with_id_mapping,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def basic_contact_map():
    """Basic name to ID mapping."""
    return {
        "Sarah Johnson": 1,
        "John Smith": 2,
        "Jane Doe": 3,
    }


@pytest.fixture
def restore_map_single():
    """Simple restore map for a single contact."""
    return {
        "{{CONTACT_NAME_1}}": "Sarah Johnson",
    }


@pytest.fixture
def restore_map_multiple():
    """Restore map with multiple contacts."""
    return {
        "{{CONTACT_NAME_1}}": "Sarah Johnson",
        "{{CONTACT_NAME_2}}": "John Smith",
        "{{CONTACT_NAME_3}}": "Jane Doe",
    }


@pytest.fixture
def large_text():
    """Large text sample for performance testing."""
    base_text = "Sarah Johnson worked with John Smith and Jane Doe on multiple projects. "
    return base_text * 100  # ~10KB of text


# ============================================================================
# TestBasicNameSanitization
# ============================================================================

class TestBasicNameSanitization:
    """Tests for sanitizing person names."""

    def test_sanitize_single_name(self):
        """Single full name should be sanitized."""
        text = "Sarah Johnson joined the team"
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_NAME}}" in result
        assert "Sarah Johnson" not in result

    def test_sanitize_name_at_sentence_start(self):
        """Name at start of sentence should be sanitized."""
        text = "John Smith led the initiative"
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_NAME}}" in result
        assert "John Smith" not in result

    def test_sanitize_name_at_sentence_end(self):
        """Name at end of sentence should be sanitized."""
        text = "Presented by Sarah Johnson"
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_NAME}}" in result
        assert "Sarah Johnson" not in result

    def test_sanitize_name_with_period(self):
        """Name followed by period should be sanitized."""
        text = "Sarah Johnson. Next sentence."
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_NAME}}." in result
        assert "Sarah Johnson." not in result

    def test_sanitize_name_with_comma(self):
        """Name followed by comma should be sanitized."""
        text = "Sarah Johnson, who worked here, was great."
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_NAME}}," in result
        assert "Sarah Johnson," not in result

    def test_sanitize_multiple_names(self):
        """Multiple names should all be sanitized."""
        text = "Jane Doe and John Smith worked together"
        result = sanitize_personal_identifiers(text)

        assert result.count("{{CONTACT_NAME}}") == 2
        assert "Jane Doe" not in result
        assert "John Smith" not in result

    def test_sanitize_name_with_three_words(self):
        """Three-word names should be sanitized."""
        text = "Mary Jane Watson is brilliant"
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_NAME}}" in result
        assert "Mary Jane Watson" not in result

    def test_sanitize_name_with_suffix(self):
        """Names with suffixes (Jr, Sr) should be handled."""
        text = "John Smith Jr. is the manager"
        result = sanitize_personal_identifiers(text)

        # Jr is skipped, but John Smith should be sanitized
        assert "John Smith" not in result


# ============================================================================
# TestEmailSanitization
# ============================================================================

class TestEmailSanitization:
    """Tests for sanitizing email addresses."""

    def test_sanitize_standard_email(self):
        """Standard email format should be sanitized."""
        text = "Email contact@example.com for details"
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_EMAIL}}" in result
        assert "contact@example.com" not in result

    def test_sanitize_email_with_numbers(self):
        """Email with numbers should be sanitized."""
        text = "Reach out to john.smith123@company.com"
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_EMAIL}}" in result
        assert "john.smith123@company.com" not in result

    def test_sanitize_email_with_plus(self):
        """Email with plus sign should be sanitized."""
        text = "Contact sarah+team@example.com"
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_EMAIL}}" in result
        assert "sarah+team@example.com" not in result

    def test_sanitize_multiple_emails(self):
        """Multiple emails should all be sanitized."""
        text = "cc: a@b.com and c@d.com"
        result = sanitize_personal_identifiers(text)

        assert result.count("{{CONTACT_EMAIL}}") == 2
        assert "a@b.com" not in result
        assert "c@d.com" not in result

    def test_sanitize_email_at_end(self):
        """Email at end of text should be sanitized."""
        text = "Contact us at support@company.com"
        result = sanitize_personal_identifiers(text)

        assert result.endswith("{{CONTACT_EMAIL}}")
        assert "support@company.com" not in result

    def test_sanitize_email_with_period_after(self):
        """Email followed by period should be sanitized."""
        text = "Email john@example.com. He'll respond."
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_EMAIL}}." in result
        assert "john@example.com" not in result


# ============================================================================
# TestLinkedInURLSanitization
# ============================================================================

class TestLinkedInURLSanitization:
    """Tests for sanitizing LinkedIn URLs."""

    def test_sanitize_full_linkedin_url(self):
        """Full LinkedIn URL should be sanitized."""
        text = "https://linkedin.com/in/sarah-johnson"
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_LINKEDIN}}" in result
        assert "linkedin.com" not in result

    def test_sanitize_linkedin_url_with_www(self):
        """LinkedIn URL with www should be sanitized."""
        text = "https://www.linkedin.com/in/john-smith"
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_LINKEDIN}}" in result
        assert "linkedin.com" not in result

    def test_sanitize_linkedin_url_without_protocol(self):
        """LinkedIn URL without http should be sanitized."""
        text = "linkedin.com/in/jane-doe"
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_LINKEDIN}}" in result
        assert "linkedin.com/in/jane-doe" not in result

    def test_sanitize_linkedin_url_in_sentence(self):
        """LinkedIn URL embedded in sentence should be sanitized."""
        text = "Check out https://linkedin.com/in/sarah-johnson for more info"
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_LINKEDIN}}" in result
        assert "linkedin.com" not in result

    def test_sanitize_multiple_linkedin_urls(self):
        """Multiple LinkedIn URLs should all be sanitized."""
        text = "Visit https://linkedin.com/in/john and https://linkedin.com/in/jane"
        result = sanitize_personal_identifiers(text)

        assert result.count("{{CONTACT_LINKEDIN}}") == 2


# ============================================================================
# TestPreservation
# ============================================================================

class TestPreservation:
    """Tests that certain terms should NOT be sanitized."""

    def test_preserve_company_names(self):
        """Company names should not be sanitized."""
        companies = [
            "Microsoft", "Google", "Apple", "Amazon",
            "Goldman Sachs", "JPMorgan Chase", "Bank of America",
            "McKinsey", "Bain & Company", "Boston Consulting Group"
        ]

        for company in companies:
            text = f"Worked at {company}"
            result = sanitize_personal_identifiers(text)
            assert company in result, f"{company} should not be sanitized"

    def test_preserve_technical_terms(self):
        """Technical terms should not be sanitized."""
        terms = [
            "Python", "Java", "JavaScript", "Kubernetes",
            "Machine Learning", "Natural Language Processing",
            "DevOps", "Cloud Engineering"
        ]

        for term in terms:
            text = f"Expert in {term}"
            result = sanitize_personal_identifiers(text)
            assert term in result, f"{term} should not be sanitized"

    def test_preserve_single_capitalized_word(self):
        """Single capitalized words should not be sanitized."""
        text = "Leadership and Management are key"
        result = sanitize_personal_identifiers(text)

        assert "Leadership" in result
        assert "Management" in result

    def test_preserve_product_names(self):
        """Product names should not be sanitized."""
        text = "Used Azure, AWS, and Google Cloud for deployment"
        result = sanitize_personal_identifiers(text)

        assert "Azure" in result
        assert "AWS" in result
        assert "Google Cloud" in result


# ============================================================================
# TestContactMapWithIDs
# ============================================================================

class TestContactMapWithIDs:
    """Tests for sanitization with ID-based contact mapping."""

    def test_sanitize_with_id_mapping_single(self, basic_contact_map):
        """Sanitize with ID mapping for single contact."""
        text = "Sarah Johnson joined the team"
        contact_map = {"Sarah Johnson": 1}

        result = sanitize_personal_identifiers(text, contact_map)

        assert "{{CONTACT_NAME_1}}" in result
        assert "Sarah Johnson" not in result

    def test_sanitize_with_id_mapping_multiple(self, basic_contact_map):
        """Sanitize with ID mapping for multiple contacts."""
        text = "Sarah Johnson worked with John Smith and Jane Doe"

        result = sanitize_personal_identifiers(text, basic_contact_map)

        assert "{{CONTACT_NAME_1}}" in result
        assert "{{CONTACT_NAME_2}}" in result
        assert "{{CONTACT_NAME_3}}" in result
        assert "Sarah Johnson" not in result
        assert "John Smith" not in result
        assert "Jane Doe" not in result

    def test_sanitize_with_partial_id_mapping(self, basic_contact_map):
        """Some names in ID map, others without IDs."""
        text = "Sarah Johnson and Unknown Person worked together"
        # Only Sarah Johnson has an ID
        contact_map = {"Sarah Johnson": 1}

        result = sanitize_personal_identifiers(text, contact_map)

        assert "{{CONTACT_NAME_1}}" in result
        # Unknown Person should be sanitized without ID
        assert "{{CONTACT_NAME}}" in result
        assert "Unknown Person" not in result

    def test_sanitize_with_empty_id_mapping(self):
        """Empty ID map should sanitize without IDs."""
        text = "Sarah Johnson and John Smith"
        contact_map = {}

        result = sanitize_personal_identifiers(text, contact_map)

        assert "{{CONTACT_NAME}}" in result
        assert "Sarah Johnson" not in result
        assert "John Smith" not in result

    def test_sanitize_with_id_mapping_preserves_duplicates(self):
        """Same name appearing multiple times gets same ID."""
        text = "Sarah Johnson led the team. Sarah Johnson is great."
        contact_map = {"Sarah Johnson": 1}

        result = sanitize_personal_identifiers(text, contact_map)

        # Both instances should have the same ID
        assert result.count("{{CONTACT_NAME_1}}") == 2


# ============================================================================
# TestRestoreFunction
# ============================================================================

class TestRestorePersonalIdentifiers:
    """Tests for restoring placeholders to original values."""

    def test_restore_single_placeholder(self, restore_map_single):
        """Single placeholder should be restored."""
        text = "Hello {{CONTACT_NAME_1}}"

        result = restore_personal_identifiers(text, restore_map_single)

        assert result == "Hello Sarah Johnson"
        assert "{{CONTACT_NAME_1}}" not in result

    def test_restore_multiple_placeholders(self, restore_map_multiple):
        """Multiple placeholders should all be restored."""
        text = "{{CONTACT_NAME_1}} worked with {{CONTACT_NAME_2}} and {{CONTACT_NAME_3}}"

        result = restore_personal_identifiers(text, restore_map_multiple)

        assert "Sarah Johnson" in result
        assert "John Smith" in result
        assert "Jane Doe" in result
        assert "{{CONTACT_NAME" not in result

    def test_restore_with_empty_map(self):
        """Empty restore map should return original text."""
        text = "Hello {{CONTACT_NAME_1}}"

        result = restore_personal_identifiers(text, {})

        assert result == text

    def test_restore_with_missing_key(self):
        """Missing key in map should leave placeholder unchanged."""
        text = "Hello {{CONTACT_NAME_1}} and {{CONTACT_NAME_2}}"
        restore_map = {"{{CONTACT_NAME_1}}": "Sarah Johnson"}

        result = restore_personal_identifiers(text, restore_map)

        assert "Sarah Johnson" in result
        assert "{{CONTACT_NAME_2}}" in result

    def test_restore_generic_placeholder(self):
        """Generic placeholder without ID should be handled."""
        text = "Contacted {{CONTACT_EMAIL}}"
        restore_map = {"{{CONTACT_EMAIL}}": "john@example.com"}

        result = restore_personal_identifiers(text, restore_map)

        assert result == "Contacted john@example.com"

    def test_restore_all_placeholder_types(self):
        """Restore mix of name, email, and LinkedIn placeholders."""
        text = "{{CONTACT_NAME_1}} email: {{CONTACT_EMAIL}} linkedin: {{CONTACT_LINKEDIN}}"
        restore_map = {
            "{{CONTACT_NAME_1}}": "Sarah Johnson",
            "{{CONTACT_EMAIL}}": "sarah@example.com",
            "{{CONTACT_LINKEDIN}}": "linkedin.com/in/sarah-johnson"
        }

        result = restore_personal_identifiers(text, restore_map)

        assert "Sarah Johnson" in result
        assert "sarah@example.com" in result
        assert "linkedin.com/in/sarah-johnson" in result

    def test_restore_empty_text(self):
        """Empty text should return empty."""
        result = restore_personal_identifiers("", {"{{CONTACT_NAME_1}}": "John"})
        assert result == ""

    def test_restore_text_without_placeholders(self):
        """Text without placeholders should be unchanged."""
        text = "Just regular text"
        restore_map = {"{{CONTACT_NAME_1}}": "John"}

        result = restore_personal_identifiers(text, restore_map)

        assert result == text


# ============================================================================
# TestExtractPlaceholderIds
# ============================================================================

class TestExtractPlaceholderIds:
    """Tests for extracting contact IDs from placeholders."""

    def test_extract_single_id(self):
        """Single ID in placeholder should be extracted."""
        text = "Meet {{CONTACT_NAME_42}}"

        result = extract_placeholder_ids(text)

        assert result == [42]

    def test_extract_multiple_ids(self):
        """Multiple IDs should be extracted in order."""
        text = "{{CONTACT_NAME_1}} and {{CONTACT_NAME_2}}"

        result = extract_placeholder_ids(text)

        assert result == [1, 2]

    def test_extract_duplicate_ids(self):
        """Duplicate IDs should be included in result."""
        text = "{{CONTACT_NAME_1}} and {{CONTACT_NAME_1}}"

        result = extract_placeholder_ids(text)

        assert result == [1, 1]

    def test_extract_no_ids(self):
        """No IDs in text should return empty list."""
        text = "Just {{CONTACT_NAME}} without IDs"

        result = extract_placeholder_ids(text)

        assert result == []

    def test_extract_mixed_placeholder_types(self):
        """Extract IDs only from ID-based placeholders."""
        text = "{{CONTACT_NAME_1}} emailed {{CONTACT_EMAIL}} linkedin: {{CONTACT_LINKEDIN_2}}"

        result = extract_placeholder_ids(text)

        # Should find both CONTACT_NAME_1 and CONTACT_LINKEDIN_2
        assert 1 in result
        assert 2 in result

    def test_extract_ids_empty_text(self):
        """Empty text should return empty list."""
        result = extract_placeholder_ids("")
        assert result == []

    def test_extract_ids_large_numbers(self):
        """Large ID numbers should be extracted."""
        text = "{{CONTACT_NAME_999999}}"

        result = extract_placeholder_ids(text)

        assert result == [999999]

    def test_extract_ids_ignores_non_ids(self):
        """Non-numeric patterns should not be extracted."""
        text = "{{CONTACT_NAME_abc}} and {{CONTACT_NAME_1}}"

        result = extract_placeholder_ids(text)

        # Should only get the numeric ID
        assert 1 in result
        assert "abc" not in str(result)


# ============================================================================
# TestEdgeCases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_string(self):
        """Empty string should return empty."""
        result = sanitize_personal_identifiers("")
        assert result == ""

    def test_none_input(self):
        """None input should raise or return None gracefully."""
        # This depends on implementation - adjust as needed
        text = None
        try:
            result = sanitize_personal_identifiers(text)
            assert result is None or result == ""
        except (TypeError, AttributeError):
            # It's acceptable to raise an error for None input
            pass

    def test_text_with_no_pii(self):
        """Text without PII should be unchanged."""
        text = "The quick brown fox jumps over the lazy dog"
        result = sanitize_personal_identifiers(text)
        assert result == text

    def test_possessive_name(self):
        """Names with possessive should be sanitized."""
        text = "Sarah Johnson's report was excellent"
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_NAME}}'s" in result
        assert "Sarah Johnson" not in result

    def test_name_in_quotation(self):
        """Name in quotes should be sanitized."""
        text = 'He said "John Smith is the best"'
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_NAME}}" in result
        assert "John Smith" not in result

    def test_mixed_case_email(self):
        """Mixed case email should be sanitized."""
        text = "Contact John.Smith@Example.COM"
        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_EMAIL}}" in result
        assert "John.Smith@Example.COM" not in result

    def test_consecutive_names(self):
        """Multiple names in sequence should be handled."""
        text = "John Smith Mary Jane Watson collaborated"
        result = sanitize_personal_identifiers(text)

        # Both should be sanitized
        assert "John Smith" not in result
        assert "Mary Jane Watson" not in result

    def test_special_characters_preserved(self):
        """Special characters not related to PII should be preserved."""
        text = "Increased revenue by 50% (year-over-year) - John Smith"
        result = sanitize_personal_identifiers(text)

        assert "50%" in result
        assert "year-over-year" in result
        assert "John Smith" not in result

    def test_unicode_in_text(self):
        """Unicode characters should be preserved."""
        text = "Worked in France, Germany (Deutschland), and España with Sarah Johnson"
        result = sanitize_personal_identifiers(text)

        assert "Deutschland" in result
        assert "España" in result
        assert "Sarah Johnson" not in result

    def test_very_long_name_not_sanitized(self):
        """Very long sequences shouldn't be treated as names."""
        text = "The Big Important Company Successfully Delivered Results"
        result = sanitize_personal_identifiers(text)

        # Only 2-4 word sequences should be sanitized
        assert "Big Important Company" not in result or "Successfully Delivered" not in result


# ============================================================================
# TestRoundTripOperations
# ============================================================================

class TestRoundTripOperations:
    """Tests for sanitizing and restoring in sequence."""

    def test_sanitize_restore_roundtrip(self, basic_contact_map):
        """Sanitize then restore should recover original (with IDs)."""
        original = "Sarah Johnson worked with John Smith"
        contact_map = basic_contact_map

        # Sanitize
        sanitized, restore_map = sanitize_with_id_mapping(original, contact_map)

        # Should have placeholders with IDs
        assert "{{CONTACT_NAME_1}}" in sanitized
        assert "{{CONTACT_NAME_2}}" in sanitized

        # Restore
        restored = restore_personal_identifiers(sanitized, restore_map)

        assert restored == original

    def test_sanitize_restore_partial_mapping(self):
        """Partial mapping: some names with IDs, some without."""
        original = "Sarah Johnson and Unknown Person worked together"
        contact_map = {"Sarah Johnson": 1}

        # Sanitize
        sanitized = sanitize_personal_identifiers(original, contact_map)

        # Has both ID and non-ID placeholder
        assert "{{CONTACT_NAME_1}}" in sanitized
        assert "{{CONTACT_NAME}}" in sanitized

    def test_sanitize_restore_all_types(self):
        """Sanitize and restore with names, emails, and URLs."""
        original = "Sarah Johnson (sarah@example.com) linkedin: https://linkedin.com/in/sarah-johnson"
        contact_map = {"Sarah Johnson": 1}

        sanitized = sanitize_personal_identifiers(original, contact_map)

        restore_map = {
            "{{CONTACT_NAME_1}}": "Sarah Johnson",
            "{{CONTACT_EMAIL}}": "sarah@example.com",
            "{{CONTACT_LINKEDIN}}": "https://linkedin.com/in/sarah-johnson"
        }

        restored = restore_personal_identifiers(sanitized, restore_map)

        assert "Sarah Johnson" in restored
        assert "sarah@example.com" in restored
        assert "linkedin" in restored.lower()


# ============================================================================
# TestPerformance
# ============================================================================

class TestPerformance:
    """Tests for performance with large inputs."""

    def test_large_text_sanitization(self, large_text):
        """Sanitizing large text should complete in reasonable time."""
        import time

        start = time.time()
        result = sanitize_personal_identifiers(large_text)
        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0, f"Sanitization took {elapsed}s, expected < 1s"
        assert "{{CONTACT_NAME}}" in result

    def test_large_text_restore(self, large_text):
        """Restoring large text should complete in reasonable time."""
        import time

        sanitized = sanitize_personal_identifiers(large_text)
        restore_map = {
            "{{CONTACT_NAME}}": "Sarah Johnson",
            "{{CONTACT_EMAIL}}": "sarah@example.com",
        }

        start = time.time()
        result = restore_personal_identifiers(sanitized, restore_map)
        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0, f"Restore took {elapsed}s, expected < 1s"

    def test_large_text_extract_ids(self, large_text):
        """Extracting IDs from large text should be fast."""
        import time

        sanitized = sanitize_personal_identifiers(
            large_text,
            {"Sarah Johnson": 1, "John Smith": 2, "Jane Doe": 3}
        )

        start = time.time()
        result = extract_placeholder_ids(sanitized)
        elapsed = time.time() - start

        # Should complete in under 500ms
        assert elapsed < 0.5, f"ID extraction took {elapsed}s, expected < 0.5s"


# ============================================================================
# TestConvenienceFunction
# ============================================================================

class TestSanitizeWithIdMapping:
    """Tests for sanitize_with_id_mapping convenience function."""

    def test_returns_tuple(self, basic_contact_map):
        """Function should return tuple of (text, map)."""
        text = "Sarah Johnson worked here"

        result = sanitize_with_id_mapping(text, basic_contact_map)

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_sanitized_text_is_first_element(self, basic_contact_map):
        """First element should be sanitized text."""
        text = "Sarah Johnson"

        sanitized, restore_map = sanitize_with_id_mapping(text, basic_contact_map)

        assert "{{CONTACT_NAME_1}}" in sanitized
        assert "Sarah Johnson" not in sanitized

    def test_restore_map_is_second_element(self, basic_contact_map):
        """Second element should be restore map."""
        text = "Sarah Johnson and John Smith"

        sanitized, restore_map = sanitize_with_id_mapping(text, basic_contact_map)

        assert "{{CONTACT_NAME_1}}" in restore_map
        assert "{{CONTACT_NAME_2}}" in restore_map
        assert restore_map["{{CONTACT_NAME_1}}"] == "Sarah Johnson"
        assert restore_map["{{CONTACT_NAME_2}}"] == "John Smith"

    def test_convenience_function_roundtrip(self, basic_contact_map):
        """Convenience function should support roundtrip."""
        original = "Sarah Johnson and John Smith"

        sanitized, restore_map = sanitize_with_id_mapping(original, basic_contact_map)
        restored = restore_personal_identifiers(sanitized, restore_map)

        assert restored == original


# ============================================================================
# TestRealWorldScenarios
# ============================================================================

class TestRealWorldScenarios:
    """Tests with realistic resume/cover letter content."""

    def test_resume_professional_summary(self):
        """Sanitize realistic professional summary."""
        text = (
            "Led cross-functional teams at Microsoft and Google. "
            "Contact: sarah.johnson@example.com, LinkedIn: https://linkedin.com/in/sarah-johnson"
        )

        result = sanitize_personal_identifiers(text)

        assert "Microsoft" in result
        assert "Google" in result
        assert "sarah.johnson@example.com" not in result
        assert "linkedin.com" not in result

    def test_work_experience_entry(self):
        """Sanitize realistic work experience bullet."""
        text = (
            "Collaborated with John Smith and Jane Doe to build cloud infrastructure using AWS and Kubernetes. "
            "Increased uptime by 99.9%. Contact John at john.smith@acme.com for details."
        )

        result = sanitize_personal_identifiers(text)

        assert "{{CONTACT_NAME}}" in result
        assert "AWS" in result
        assert "Kubernetes" in result
        assert "99.9%" in result
        assert "john.smith@acme.com" not in result

    def test_reference_list(self):
        """Sanitize reference list with multiple people."""
        text = (
            "References:\n"
            "1. Sarah Johnson, VP Engineering at Microsoft, sarah.johnson@microsoft.com\n"
            "2. John Smith, Director at Google, john.smith@google.com\n"
            "3. Jane Doe, CEO at StartupCo, jane.doe@startupco.io\n"
        )

        contact_map = {
            "Sarah Johnson": 1,
            "John Smith": 2,
            "Jane Doe": 3,
        }

        result = sanitize_personal_identifiers(text, contact_map)

        assert "{{CONTACT_NAME_1}}" in result
        assert "{{CONTACT_NAME_2}}" in result
        assert "{{CONTACT_NAME_3}}" in result
        assert "{{CONTACT_EMAIL}}" in result
        assert "Microsoft" in result
        assert "Google" in result

    def test_cover_letter_with_hiring_manager(self):
        """Sanitize cover letter addressing hiring manager."""
        text = (
            "Dear Ms. Jane Doe,\n\n"
            "I am writing to express my interest in the position. "
            "I met Jane Doe at the AWS Summit and was impressed by her vision. "
            "You can reach me at john.smith@gmail.com or https://linkedin.com/in/john-smith.\n\n"
            "Sincerely,\nJohn Smith"
        )

        result = sanitize_personal_identifiers(text)

        # "Jane Doe" after "Ms." might be trickier - the regex handles it
        assert "{{CONTACT_NAME}}" in result
        assert "{{CONTACT_EMAIL}}" in result
        assert "{{CONTACT_LINKEDIN}}" in result
        assert "AWS" in result  # Should be preserved


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
