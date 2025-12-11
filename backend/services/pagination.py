"""
Pagination Service for ETPS Resume Generation

Provides space-aware pagination logic for 2-page resume layout.
Manages line budget estimation and bullet prioritization based on
physical space constraints.

PRD Reference: Section 2.11 - Pagination-Aware Layout
"""

import math
import os
import re
from typing import List, Optional, Dict, Tuple, Any
from dataclasses import dataclass

import yaml


# Pre-compiled compression patterns (avoids ReDoS by compiling once)
_COMPRESSION_PATTERNS = [
    # Remove filler phrases
    (re.compile(r'\bin order to\b', re.IGNORECASE), 'to'),
    (re.compile(r'\bwith the goal of\b', re.IGNORECASE), 'to'),
    (re.compile(r'\bfor the purpose of\b', re.IGNORECASE), 'to'),
    (re.compile(r'\bas a result of\b', re.IGNORECASE), 'due to'),
    (re.compile(r'\bin addition to\b', re.IGNORECASE), 'besides'),
    (re.compile(r'\bat the same time\b', re.IGNORECASE), 'simultaneously'),
    (re.compile(r'\bon a daily basis\b', re.IGNORECASE), 'daily'),
    (re.compile(r'\bon a regular basis\b', re.IGNORECASE), 'regularly'),
    (re.compile(r'\bin a timely manner\b', re.IGNORECASE), 'promptly'),
    (re.compile(r'\bdue to the fact that\b', re.IGNORECASE), 'because'),
    (re.compile(r'\bin the event that\b', re.IGNORECASE), 'if'),
    (re.compile(r'\bfor the duration of\b', re.IGNORECASE), 'during'),
    (re.compile(r'\bwith respect to\b', re.IGNORECASE), 'regarding'),
    (re.compile(r'\bin regard to\b', re.IGNORECASE), 'regarding'),
    (re.compile(r'\bin terms of\b', re.IGNORECASE), 'for'),
    (re.compile(r'\ba total of\b', re.IGNORECASE), ''),
    (re.compile(r'\bthe ability to\b', re.IGNORECASE), 'ability to'),
    (re.compile(r'\bthat were\b', re.IGNORECASE), 'that'),
    (re.compile(r'\bwhich were\b', re.IGNORECASE), 'which'),
    (re.compile(r'\bthat was\b', re.IGNORECASE), 'that'),
    (re.compile(r'\bwhich was\b', re.IGNORECASE), 'which'),
    # Remove redundant modifiers
    (re.compile(r'\bvery\s+', re.IGNORECASE), ''),
    (re.compile(r'\breally\s+', re.IGNORECASE), ''),
    (re.compile(r'\bactually\s+', re.IGNORECASE), ''),
    (re.compile(r'\bbasically\s+', re.IGNORECASE), ''),
    (re.compile(r'\bessentially\s+', re.IGNORECASE), ''),
    (re.compile(r'\bjust\s+', re.IGNORECASE), ''),
    (re.compile(r'\bsimply\s+', re.IGNORECASE), ''),
    # Tighten common phrases
    (re.compile(r'\bhelped to\b', re.IGNORECASE), 'helped'),
    (re.compile(r'\bable to be\b', re.IGNORECASE), 'able to'),
    (re.compile(r'\bserved as\b', re.IGNORECASE), 'was'),
    (re.compile(r'\bacted as\b', re.IGNORECASE), 'was'),
    # Remove trailing "successfully" redundancy (action implies success)
    (re.compile(r'\bsuccessfully\s+(completed|delivered|implemented|executed|launched)\b', re.IGNORECASE), r'\1'),
]

# Compiled patterns for cleanup
_WHITESPACE_PATTERN = re.compile(r'\s+')

# Maximum bullet length for compression (prevents ReDoS on adversarial input)
_MAX_COMPRESSION_INPUT_LENGTH = 500


@dataclass
class RoleLayout:
    """Layout information for a single role."""
    experience_id: int
    job_header_lines: int
    bullet_count: int
    bullet_lines: int  # Total lines for all bullets
    total_lines: int  # header + bullets


@dataclass
class PageLayout:
    """Layout information for a single page."""
    lines_used: int
    lines_available: int
    roles: List[RoleLayout]
    violations: List[str]


@dataclass
class ResumeLayout:
    """Complete resume layout simulation result."""
    page1: PageLayout
    page2: PageLayout
    total_lines: int
    fits_in_budget: bool
    violations: List[str]


def _load_pagination_config() -> dict:
    """Load pagination section from config.yaml with defaults.

    Returns:
        dict: Pagination configuration with fallback defaults
    """
    config_path = os.path.join(
        os.path.dirname(__file__), '..', 'config', 'config.yaml'
    )
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config.get('pagination', {})
    except FileNotFoundError:
        # Return sensible defaults if config not found
        return {
            'page1_line_budget': 50,
            'page2_line_budget': 55,
            'chars_per_line_estimate': 75,
            'min_bullets_per_role': 2,
            'max_bullets_per_role': 6,
            'section_header_lines': 1,
            'job_header_lines': 2,
            'bullet_chrome_lines': 1,
            'max_summary_lines': 4,
            'max_skills_lines': 3,
            'min_bullets_after_job_header': 2,
            'compression_enabled': True,
            'compression_target_reduction': 0.20,
            'condense_older_roles': True
        }


class PaginationService:
    """Service for managing resume pagination and line budget calculations.

    Provides methods to estimate line consumption for various resume elements
    and compute space-aware prioritization metrics.
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize pagination service with configuration.

        Args:
            config: Optional configuration dictionary override.
                   If None, loads from config.yaml.
        """
        if config is None:
            config = _load_pagination_config()

        self._config = config

        # Cache commonly used values
        self._page1_budget = config.get('page1_line_budget', 50)
        self._page2_budget = config.get('page2_line_budget', 55)
        self._chars_per_line = config.get('chars_per_line_estimate', 75)
        # Validate chars_per_line to prevent division by zero
        if self._chars_per_line <= 0:
            self._chars_per_line = 75  # Safe default
        self._section_header_lines = config.get('section_header_lines', 1)
        self._job_header_lines = config.get('job_header_lines', 2)
        self._bullet_chrome_lines = config.get('bullet_chrome_lines', 1)
        self._max_summary_lines = config.get('max_summary_lines', 4)
        self._max_skills_lines = config.get('max_skills_lines', 3)

    def estimate_bullet_lines(self, bullet_text: str) -> int:
        """Estimate line consumption for a bullet point.

        Formula: bullet_chrome_lines + ceil(text_length / chars_per_line)

        Args:
            bullet_text: The bullet point text content

        Returns:
            int: Estimated number of lines this bullet will consume
        """
        if not bullet_text:
            return self._bullet_chrome_lines

        text_length = len(bullet_text.strip())
        text_lines = math.ceil(text_length / self._chars_per_line)

        return self._bullet_chrome_lines + text_lines

    def estimate_summary_lines(self, summary_text: str) -> int:
        """Estimate line consumption for professional summary.

        Args:
            summary_text: The professional summary text

        Returns:
            int: Estimated number of lines, capped at max_summary_lines
        """
        if not summary_text:
            return 0

        text_length = len(summary_text.strip())
        estimated_lines = math.ceil(text_length / self._chars_per_line)

        # Cap at configured maximum
        return min(estimated_lines, self._max_summary_lines)

    def estimate_skills_lines(self, skills: List[str]) -> int:
        """Estimate line consumption for skills section.

        Assumes comma-separated format: "Python, Java, SQL, ..."

        Args:
            skills: List of skill strings

        Returns:
            int: Estimated number of lines, capped at max_skills_lines
        """
        if not skills:
            return 0

        # Format as comma-separated string
        skills_text = ", ".join(skill.strip() for skill in skills if skill.strip())

        if not skills_text:
            return 0

        text_length = len(skills_text)
        estimated_lines = math.ceil(text_length / self._chars_per_line)

        # Cap at configured maximum
        return min(estimated_lines, self._max_skills_lines)

    def get_job_header_lines(self) -> int:
        """Get configured line cost for job header.

        Job header includes: company, title, location, dates

        Returns:
            int: Number of lines consumed by job header
        """
        return self._job_header_lines

    def get_section_header_lines(self) -> int:
        """Get configured line cost for section header.

        Section headers: "EXPERIENCE", "SKILLS", "EDUCATION", etc.

        Returns:
            int: Number of lines consumed by section header
        """
        return self._section_header_lines

    def get_total_budget(self) -> int:
        """Get total line budget across both pages.

        Returns:
            int: page1_line_budget + page2_line_budget
        """
        return self._page1_budget + self._page2_budget

    def get_page1_budget(self) -> int:
        """Get line budget for page 1.

        Page 1 typically has less space due to header and contact info.

        Returns:
            int: Number of available lines on page 1
        """
        return self._page1_budget

    def get_page2_budget(self) -> int:
        """Get line budget for page 2.

        Page 2 typically has slightly more usable space.

        Returns:
            int: Number of available lines on page 2
        """
        return self._page2_budget

    def compute_bullet_value_per_line(
        self,
        bullet_text: str,
        relevance_score: float
    ) -> float:
        """Compute space-aware prioritization metric for a bullet.

        Formula: relevance_score / estimated_lines

        This enables prioritizing bullets that pack high relevance into
        minimal space, which is critical for 2-page layout constraints.

        Args:
            bullet_text: The bullet point text content
            relevance_score: Relevance score (typically 0.0 to 1.0)

        Returns:
            float: Value-per-line metric for prioritization.
                  Higher values indicate more efficient use of space.

        Example:
            - Bullet A: 0.9 relevance, 3 lines -> 0.30 value/line
            - Bullet B: 0.7 relevance, 2 lines -> 0.35 value/line
            Bullet B would be prioritized despite lower relevance.
        """
        estimated_lines = self.estimate_bullet_lines(bullet_text)

        # Guard against division by zero (shouldn't happen with bullet_chrome_lines)
        if estimated_lines == 0:
            return 0.0

        return relevance_score / estimated_lines

    def allocate_bullets_under_budget(
        self,
        scored_bullets: List[Tuple[Any, float, str, int]],  # (bullet, score, reason, line_cost)
        available_lines: int,
        min_bullets: int = 2,
        max_bullets: int = 6
    ) -> List[Tuple[Any, float, str, int]]:
        """
        Select bullets that fit within line budget while maximizing value.

        Strategy:
        1. Compute value_per_line for each
        2. Sort by value_per_line descending
        3. Greedily select until budget exhausted
        4. Ensure min_bullets if possible
        5. Never exceed max_bullets

        Args:
            scored_bullets: List of (bullet, score, reason, line_cost) tuples
            available_lines: Maximum lines available for bullets
            min_bullets: Minimum number of bullets to include if possible
            max_bullets: Maximum number of bullets to include

        Returns:
            List of selected (bullet, score, reason, line_cost) tuples that fit budget
        """
        if not scored_bullets:
            return []

        # Compute value per line for each bullet
        bullets_with_efficiency = []
        for bullet, score, reason, line_cost in scored_bullets:
            # Skip invalid line costs entirely
            if line_cost <= 0:
                continue
            value_per_line = score / line_cost
            bullets_with_efficiency.append((bullet, score, reason, line_cost, value_per_line))

        # Sort by value_per_line descending (highest efficiency first)
        bullets_with_efficiency.sort(key=lambda x: x[4], reverse=True)

        # Greedy selection: try to fit highest value/line bullets first
        selected = []
        total_lines_used = 0

        for bullet, score, reason, line_cost, value_per_line in bullets_with_efficiency:
            # Stop if we've hit max_bullets
            if len(selected) >= max_bullets:
                break

            # Try to add this bullet if it fits
            if total_lines_used + line_cost <= available_lines:
                selected.append((bullet, score, reason, line_cost))
                total_lines_used += line_cost

        # If we didn't get min_bullets, try to ensure we have at least that many
        # by selecting the smallest bullets from what's left
        if len(selected) < min_bullets:
            # Reset and try a different strategy: select smallest bullets first up to min
            remaining_bullets = [
                (bullet, score, reason, line_cost)
                for bullet, score, reason, line_cost, _ in bullets_with_efficiency
            ]
            # Sort by line_cost ascending (smallest first)
            remaining_bullets.sort(key=lambda x: x[3])

            selected = []
            total_lines_used = 0

            for bullet, score, reason, line_cost in remaining_bullets:
                if len(selected) >= min_bullets:
                    break
                if total_lines_used + line_cost <= available_lines:
                    selected.append((bullet, score, reason, line_cost))
                    total_lines_used += line_cost

        return selected


class PageSplitSimulator:
    """Simulates page breaks and validates layout rules per PRD 2.11."""

    def __init__(self, pagination_service: 'PaginationService'):
        self.pg = pagination_service

    def simulate_page_layout(
        self,
        summary_lines: int,
        skills_lines: int,
        roles: List[Dict[str, Any]],  # [{experience_id, job_header_lines, bullets: [{text, lines}]}]
        page2_footer_lines: int = 0   # Lines reserved at bottom of page 2 (skills, education)
    ) -> ResumeLayout:
        """
        Simulate filling Page 1 and Page 2 with resume sections.

        Order: Summary -> Skills (if on page 1) -> Experience (each role with its bullets)

        Note: If skills/education are at the bottom of page 2 (not page 1),
        pass skills_lines=0 and use page2_footer_lines to reserve that space.

        Returns ResumeLayout with page allocations and any violations.

        Args:
            summary_lines: Lines consumed by professional summary
            skills_lines: Lines consumed by skills section ON PAGE 1
            roles: List of role dicts with experience_id, job_header_lines,
                   and bullets list [{text, lines}]
            page2_footer_lines: Lines reserved at bottom of page 2 (skills, education)

        Returns:
            ResumeLayout with page1, page2 layouts and violations
        """
        page1_budget = self.pg.get_page1_budget()
        page2_budget = self.pg.get_page2_budget()

        # Reserve space on page 2 for footer sections (skills, education)
        # This effectively reduces available space for experience on page 2
        effective_page2_budget = page2_budget - page2_footer_lines

        violations = []
        page1_roles = []
        page2_roles = []

        # Start with page 1
        current_page = 1
        lines_used_page1 = 0
        lines_used_page2 = 0

        # Add summary and skills to page 1
        section_header_lines = self.pg.get_section_header_lines()

        # Summary section (if present)
        if summary_lines > 0:
            lines_used_page1 += section_header_lines + summary_lines

        # Skills section (if present)
        if skills_lines > 0:
            lines_used_page1 += section_header_lines + skills_lines

        # Experience section header goes on page 1 if there are roles
        if roles:
            lines_used_page1 += section_header_lines

        # Now process each role
        for role_idx, role in enumerate(roles):
            experience_id = role.get('experience_id', role_idx)
            job_header_lines = role.get('job_header_lines', self.pg.get_job_header_lines())
            bullets = role.get('bullets', [])

            # Calculate total lines for this role
            bullet_count = len(bullets)
            bullet_lines = sum(b.get('lines', 1) for b in bullets)
            total_role_lines = job_header_lines + bullet_lines

            # Create role layout
            role_layout = RoleLayout(
                experience_id=experience_id,
                job_header_lines=job_header_lines,
                bullet_count=bullet_count,
                bullet_lines=bullet_lines,
                total_lines=total_role_lines
            )

            # Try to fit on current page
            if current_page == 1:
                remaining_page1 = page1_budget - lines_used_page1

                # Check for orphaned header
                min_bullets_after = self.pg._config.get('min_bullets_after_job_header', 2)
                min_bullets_lines = sum(
                    sorted([b.get('lines', 1) for b in bullets])[:min(min_bullets_after, len(bullets))]
                ) if bullets else 0

                if self.check_orphaned_header(remaining_page1, job_header_lines, min_bullets_after):
                    # Would create orphan - move entire role to page 2
                    violations.append(
                        f"Role {experience_id}: Orphaned header avoided - moved to page 2"
                    )
                    current_page = 2
                    page2_roles.append(role_layout)
                    lines_used_page2 += total_role_lines
                elif lines_used_page1 + total_role_lines <= page1_budget:
                    # Fits completely on page 1
                    page1_roles.append(role_layout)
                    lines_used_page1 += total_role_lines
                else:
                    # Doesn't fit on page 1, move to page 2
                    current_page = 2
                    page2_roles.append(role_layout)
                    lines_used_page2 += total_role_lines
            else:
                # Already on page 2
                page2_roles.append(role_layout)
                lines_used_page2 += total_role_lines

        # Check for budget violations
        if lines_used_page1 > page1_budget:
            violations.append(
                f"Page 1 overflow: {lines_used_page1} lines used, {page1_budget} available"
            )

        if lines_used_page2 > effective_page2_budget:
            violations.append(
                f"Page 2 overflow: {lines_used_page2} lines used, "
                f"{effective_page2_budget} available (reserved {page2_footer_lines} for footer)"
            )

        # Build page layouts
        page1 = PageLayout(
            lines_used=lines_used_page1,
            lines_available=page1_budget,
            roles=page1_roles,
            violations=[v for v in violations if 'Page 1' in v]
        )

        page2 = PageLayout(
            lines_used=lines_used_page2,
            lines_available=effective_page2_budget,  # Use effective budget
            roles=page2_roles,
            violations=[v for v in violations if 'Page 2' in v]
        )

        total_lines = lines_used_page1 + lines_used_page2
        total_budget = page1_budget + effective_page2_budget  # Use effective budget
        fits_in_budget = total_lines <= total_budget and len(violations) == 0

        return ResumeLayout(
            page1=page1,
            page2=page2,
            total_lines=total_lines,
            fits_in_budget=fits_in_budget,
            violations=violations
        )

    def check_orphaned_header(
        self,
        remaining_lines: int,
        job_header_lines: int,
        min_bullets_after: int = 2
    ) -> bool:
        """
        Check if adding job header would create orphan.
        Returns True if orphaned (not enough space for header + min bullets)

        Args:
            remaining_lines: Lines available on current page
            job_header_lines: Lines consumed by job header
            min_bullets_after: Minimum bullets required after header

        Returns:
            bool: True if adding header would create orphan
        """
        # Estimate minimum lines needed for min_bullets_after
        # Use bullet_chrome_lines as minimum estimate (1 line per bullet minimum)
        min_bullet_lines = min_bullets_after * self.pg._bullet_chrome_lines

        # Need space for header + minimum bullets
        min_required = job_header_lines + min_bullet_lines

        return remaining_lines < min_required

    def suggest_condensation(
        self,
        roles: List[Dict[str, Any]],
        target_reduction_lines: int,
        min_bullets_per_role: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Suggest which roles to condense to free space.

        Strategy: Start with oldest roles (last in list), reduce to min_bullets.

        Args:
            roles: List of role dicts with bullets: [{text, lines}]
            target_reduction_lines: How many lines to save
            min_bullets_per_role: Minimum bullets to keep per role

        Returns:
            List of {role_index, current_bullets, suggested_bullets, lines_saved}
        """
        suggestions = []
        total_lines_saved = 0

        # Process roles from oldest (last) to newest (first)
        for role_idx in range(len(roles) - 1, -1, -1):
            if total_lines_saved >= target_reduction_lines:
                break

            role = roles[role_idx]
            bullets = role.get('bullets', [])
            current_bullet_count = len(bullets)

            # Only condense if we have more than minimum
            if current_bullet_count <= min_bullets_per_role:
                continue

            # Sort bullets by lines (keep shortest)
            sorted_bullets = sorted(bullets, key=lambda b: b.get('lines', 1))

            # Keep the min_bullets_per_role shortest bullets
            kept_bullets = sorted_bullets[:min_bullets_per_role]
            removed_bullets = sorted_bullets[min_bullets_per_role:]

            # Calculate lines saved
            lines_saved = sum(b.get('lines', 1) for b in removed_bullets)

            if lines_saved > 0:
                suggestions.append({
                    'role_index': role_idx,
                    'experience_id': role.get('experience_id', role_idx),
                    'current_bullets': current_bullet_count,
                    'suggested_bullets': min_bullets_per_role,
                    'lines_saved': lines_saved
                })
                total_lines_saved += lines_saved

        return suggestions


def compress_bullet_text(
    bullet_text: str,
    target_reduction: float = 0.20
) -> str:
    """
    Compress bullet text by removing filler words and tightening phrasing.

    This is a heuristic compression that removes common filler patterns
    without altering factual content. More aggressive compression would
    require LLM rewriting.

    Args:
        bullet_text: Original bullet text
        target_reduction: Target character reduction (0.20 = 20%)

    Returns:
        Compressed bullet text (may not achieve full target reduction)
    """
    if not bullet_text:
        return bullet_text

    # Security: Limit input length to prevent ReDoS
    if len(bullet_text) > _MAX_COMPRESSION_INPUT_LENGTH:
        return bullet_text  # Skip compression for very long bullets

    original_length = len(bullet_text)
    text = bullet_text

    # Pattern-based compression using pre-compiled patterns (prevents ReDoS)
    for pattern, replacement in _COMPRESSION_PATTERNS:
        text = pattern.sub(replacement, text)

    # Clean up multiple spaces using pre-compiled pattern
    text = _WHITESPACE_PATTERN.sub(' ', text).strip()

    # Calculate actual reduction
    new_length = len(text)
    actual_reduction = (original_length - new_length) / original_length if original_length > 0 else 0

    return text


class BulletCompressor:
    """Service for compressing bullets to fit space constraints."""

    def __init__(self, pagination_service: 'PaginationService'):
        self.pg = pagination_service
        self._config = pagination_service._config

    def compress_bullets_to_fit(
        self,
        bullets: List[Dict[str, Any]],  # [{text, lines, ...}]
        target_lines_saved: int,
        preserve_first_n: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Compress bullets to save space, starting with longest bullets.

        Args:
            bullets: List of bullet dicts with 'text' and 'lines' keys
            target_lines_saved: How many lines to try to save
            preserve_first_n: Don't compress the first N bullets (highest priority)

        Returns:
            Tuple of (updated bullets list, actual lines saved)
        """
        if not bullets or target_lines_saved <= 0:
            return bullets, 0

        compression_enabled = self._config.get('compression_enabled', True)
        if not compression_enabled:
            return bullets, 0

        target_reduction = self._config.get('compression_target_reduction', 0.20)

        # Sort by line cost descending (compress longest first)
        indexed_bullets = [(i, b) for i, b in enumerate(bullets)]
        compressible = [(i, b) for i, b in indexed_bullets if i >= preserve_first_n]
        compressible.sort(key=lambda x: x[1].get('lines', 1), reverse=True)

        total_lines_saved = 0
        updated_bullets = list(bullets)

        for idx, bullet in compressible:
            if total_lines_saved >= target_lines_saved:
                break

            original_text = bullet.get('text', '')
            original_lines = bullet.get('lines', self.pg.estimate_bullet_lines(original_text))

            # Compress the text
            compressed_text = compress_bullet_text(original_text, target_reduction)
            new_lines = self.pg.estimate_bullet_lines(compressed_text)

            lines_saved = original_lines - new_lines

            if lines_saved > 0:
                # Update the bullet
                updated_bullets[idx] = {
                    **bullet,
                    'text': compressed_text,
                    'lines': new_lines,
                    'was_compressed': True,
                    'original_text': original_text
                }
                total_lines_saved += lines_saved

        return updated_bullets, total_lines_saved
