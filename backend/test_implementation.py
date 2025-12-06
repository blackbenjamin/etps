"""
Quick test script for the ETPS job parser and skill-gap analysis implementation.

This script demonstrates the usage of all newly created modules:
- Text processing utilities
- Mock LLM
- Pydantic schemas
"""

import asyncio
from datetime import datetime
from utils.text_processing import clean_text, extract_bullets
from services.llm import MockLLM
from schemas import (
    JobParseRequest,
    SkillMatch,
    SkillGap,
    WeakSignal,
    UserSkillProfile,
)


async def test_text_processing():
    """Test text processing utilities."""
    print("=" * 60)
    print("TEXT PROCESSING UTILITIES")
    print("=" * 60)

    # Test clean_text
    messy = "Multiple    spaces\n\n\n\nToo many newlines"
    cleaned = clean_text(messy)
    print(f"\nCleaned text: {repr(cleaned)}")

    # Test extract_bullets
    bullets_text = """
    - First bullet point
    * Second bullet point
    • Third bullet point
    1. Fourth bullet point
    """
    bullets = extract_bullets(bullets_text)
    print(f"\nExtracted {len(bullets)} bullets:")
    for bullet in bullets:
        print(f"  • {bullet}")


async def test_mock_llm():
    """Test Mock LLM functionality."""
    print("\n" + "=" * 60)
    print("MOCK LLM")
    print("=" * 60)

    llm = MockLLM()

    # Sample job description
    jd = """
    Senior AI Governance Lead

    We're seeking a mission-driven leader to establish our AI governance
    framework. You'll work with cross-functional teams to develop policies,
    conduct risk assessments, and ensure ethical AI practices across our
    organization.

    Requirements:
    - Deep expertise in AI/ML technologies
    - Experience with policy development and compliance
    - Strong consulting and stakeholder management skills
    - Passion for ethical AI and social impact
    """

    # Test priority generation
    priorities = await llm.generate_core_priorities(jd, {})
    print("\nCore Priorities:")
    for i, priority in enumerate(priorities, 1):
        print(f"  {i}. {priority}")

    # Test tone inference
    tone = await llm.infer_tone(jd)
    print(f"\nDetected Tone: {tone}")


async def test_schemas():
    """Test Pydantic schemas."""
    print("\n" + "=" * 60)
    print("PYDANTIC SCHEMAS")
    print("=" * 60)

    # Test JobParseRequest
    print("\nJobParseRequest:")
    req = JobParseRequest(
        jd_text="Sample job description",
        user_id=1
    )
    print(f"  ✓ Created request for user {req.user_id}")

    # Test UserSkillProfile
    print("\nUserSkillProfile:")
    profile = UserSkillProfile(
        skills=["Python", "Machine Learning", "AI Governance"],
        capabilities=["Strategic Planning", "Stakeholder Management"],
        bullet_tags=["ai_governance", "consulting"],
        seniority_levels=["senior", "director"],
        relevance_scores={"ai_governance": 0.9, "ml": 0.8}
    )
    print(f"  ✓ Created profile with {len(profile.skills)} skills")

    # Test SkillMatch
    print("\nSkillMatch:")
    match = SkillMatch(
        skill="Python",
        match_strength=0.92,
        evidence=["5 years experience", "Led ML projects"]
    )
    print(f"  ✓ Skill: {match.skill} (strength: {match.match_strength})")

    # Test SkillGap
    print("\nSkillGap:")
    gap = SkillGap(
        skill="Kubernetes",
        importance="important",
        positioning_strategy="Highlight Docker experience and cloud architecture knowledge"
    )
    print(f"  ✓ Gap: {gap.skill} ({gap.importance})")

    # Test WeakSignal
    print("\nWeakSignal:")
    weak = WeakSignal(
        skill="Product Management",
        current_evidence=["Led cross-functional initiatives"],
        strengthening_strategy="Emphasize product thinking in technical leadership roles"
    )
    print(f"  ✓ Weak signal: {weak.skill}")

    # Test validation
    print("\nValidation Tests:")
    try:
        invalid_req = JobParseRequest(user_id=1)
    except ValueError:
        print("  ✓ Correctly rejected request without jd_text or jd_url")

    try:
        invalid_gap = SkillGap(
            skill="Test",
            importance="invalid",
            positioning_strategy="strategy"
        )
    except ValueError:
        print("  ✓ Correctly rejected invalid importance level")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ETPS IMPLEMENTATION TEST SUITE")
    print("=" * 60)

    await test_text_processing()
    await test_mock_llm()
    await test_schemas()

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
