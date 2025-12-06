"""
Populate December 2025 Resume Data

Populates the database with Benjamin Black's December 2025 resume content
using the v1.3.0 schema with engagements.

Usage:
    cd backend
    python -m db.migrations.populate_dec2025_resume
"""

import json
from datetime import date
from sqlalchemy.orm import Session

from db.database import SessionLocal, engine
from db.models import User, Experience, Engagement, Bullet


def get_or_create_user(db: Session) -> User:
    """Get existing user or create new one."""
    user = db.query(User).filter(User.username == "benjaminblack").first()

    if not user:
        user = User(
            username="benjaminblack",
            email="ben@benjaminblack.consulting",
            full_name="Benjamin Black",
        )
        db.add(user)
        db.flush()

    # Update with v1.3.0 fields
    user.email = "ben@benjaminblack.consulting"
    user.phone = "617-504-5529"
    user.linkedin_url = "linkedin.com/in/benjaminblack"
    user.portfolio_url = "benjaminblack.consulting/projects"
    user.location = "Boston, MA"

    # Candidate profile JSON (v1.3.0)
    user.candidate_profile = {
        "primary_identity": "AI & Data Leader",
        "specializations": [
            "AI Strategy",
            "AI Enablement",
            "Enterprise AI Systems Development",
            "Data Governance & Architecture",
            "Financial Services AI",
            "AI Risk & Evaluation"
        ],
        "seniority_level": "Senior / Principal",
        "ai_systems_builder": True,
        "target_roles": [
            "AI Strategist",
            "AI Enablement Lead",
            "Director of Data & AI",
            "AI Platform Lead",
            "Head of AI Governance & Enablement"
        ],
        "linkedin_meta": {
            "headline_recommended": "AI & Data Strategist | Building Enterprise AI Systems, Data Governance & Analytics Platforms | MIT Sloan MBA",
            "top_skills_selected": ["AI Strategy", "Data Governance", "Analytics Modernization"],
            "open_to_work_titles": ["Director of Data & AI", "AI Strategist", "Head of AI Enablement"]
        },
        "ai_portfolio": [
            {
                "project_name": "Enterprise Talent Positioning System (ETPS)",
                "project_type": "RAG System",
                "tech_stack": ["Python", "Claude", "Vector DB", "FastAPI"],
                "fs_relevance": True,
                "repeatable_asset": True
            },
            {
                "project_name": "AI Governance Dashboard",
                "project_type": "Analytics Platform",
                "tech_stack": ["Python", "Power BI", "SQL"],
                "fs_relevance": True,
                "repeatable_asset": True
            }
        ],
        "schema_version": "1.3.0"
    }

    return user


def clear_existing_data(db: Session, user_id: int):
    """Clear existing experiences, engagements, and bullets for the user."""
    # Get experience IDs for this user
    experience_ids = [e.id for e in db.query(Experience.id).filter(Experience.user_id == user_id).all()]

    if experience_ids:
        # Delete bullets first (they reference experiences/engagements)
        db.query(Bullet).filter(Bullet.experience_id.in_(experience_ids)).delete(synchronize_session=False)
        # Delete engagements (they reference experiences)
        db.query(Engagement).filter(Engagement.experience_id.in_(experience_ids)).delete(synchronize_session=False)
        # Delete experiences
        db.query(Experience).filter(Experience.id.in_(experience_ids)).delete(synchronize_session=False)

    db.flush()


def create_experiences_and_engagements(db: Session, user: User):
    """Create all experiences with engagements and bullets."""

    # =========================================================================
    # 1. BBC (10/2025 – Present) - Independent AI Strategist & Builder
    # =========================================================================
    bbc_2025 = Experience(
        user_id=user.id,
        job_title="Independent AI Strategist & Builder",
        employer_name="Benjamin Black Consulting",
        location="Boston, MA",
        start_date=date(2025, 10, 1),
        end_date=None,
        employer_type="independent_consulting",
        role_summary="Designing and developing enterprise-grade AI systems, portfolio projects, and advisory assets.",
        ai_systems_built=["ETPS", "RAG systems", "AI governance dashboards"],
        governance_frameworks_created=["AI readiness model", "FinTech governance framework"],
        fs_domain_relevance=0.9,
        tools_and_technologies=["Claude", "Python", "Vector DBs", "FastAPI", "LLM orchestration"],
        order=1
    )
    db.add(bbc_2025)
    db.flush()

    # Bullets for BBC 2025 (direct, no engagements for this period)
    bbc_2025_bullets = [
        Bullet(
            user_id=user.id,
            experience_id=bbc_2025.id,
            text="Synthesized AI implementation patterns from 20+ financial institutions and delivered a proprietary framework and toolkit to accelerate client scaling from pilots to production.",
            tags=["AI Strategy", "Financial Services", "Framework Development"],
            importance="high",
            ai_first_choice=True,
            order=1
        ),
        Bullet(
            user_id=user.id,
            experience_id=bbc_2025.id,
            text="Produced production-grade RAG, governance dashboards, and financial-services analytics tools; LLM orchestration, vector search, data pipelines, evaluation frameworks.",
            tags=["RAG", "AI Systems", "Data Pipelines", "LLM"],
            importance="high",
            ai_first_choice=True,
            order=2
        ),
        Bullet(
            user_id=user.id,
            experience_id=bbc_2025.id,
            text="Developed enterprise-wide AI governance frameworks for a FinTech client, reducing compliance risk by 20% and accelerating production readiness for agentic and generative applications.",
            tags=["AI Governance", "Compliance", "FinTech"],
            importance="high",
            ai_first_choice=True,
            order=3
        ),
    ]
    db.add_all(bbc_2025_bullets)

    # =========================================================================
    # 2. KeyLogic Associates (9/2024 – 10/2025)
    # =========================================================================
    keylogic = Experience(
        user_id=user.id,
        job_title="Deputy Project Leader - Data Governance, Architecture & Modeling, CDO Office",
        employer_name="KeyLogic Associates (assigned to Kessel Run)",
        location="Bedford, MA",
        start_date=date(2024, 9, 1),
        end_date=date(2025, 10, 1),
        employer_type="contract",
        fs_domain_relevance=0.3,
        tools_and_technologies=["Data Governance", "Zero-Trust", "AI Research"],
        order=2
    )
    db.add(keylogic)
    db.flush()

    keylogic_bullets = [
        Bullet(
            user_id=user.id,
            experience_id=keylogic.id,
            text="Lead research on data governance frameworks, AI capabilities, and ZT (zero-trust) frameworks for CIO and CDO.",
            tags=["Data Governance", "AI Research", "Zero-Trust", "DoD"],
            importance="high",
            ai_first_choice=True,
            order=1
        ),
        Bullet(
            user_id=user.id,
            experience_id=keylogic.id,
            text="Coordinated workstreams and managed priorities across two ten-member teams to DoD stakeholders.",
            tags=["Leadership", "Program Management", "DoD"],
            importance="medium",
            order=2
        ),
    ]
    db.add_all(keylogic_bullets)

    # =========================================================================
    # 3. BBC (8/2022 – 9/2024) - Principal Consultant
    # =========================================================================
    bbc_2022 = Experience(
        user_id=user.id,
        job_title="Principal Consultant",
        employer_name="Benjamin Black Consulting",
        location="Boston, MA",
        start_date=date(2022, 8, 1),
        end_date=date(2024, 9, 1),
        employer_type="independent_consulting",
        role_summary="Focused on data strategy, governance, and analytics transformation across financial-services organizations.",
        fs_domain_relevance=0.95,
        tools_and_technologies=["Data Strategy", "Governance", "Analytics"],
        order=3
    )
    db.add(bbc_2022)
    db.flush()

    # Engagement: Edward Jones
    edward_jones = Engagement(
        experience_id=bbc_2022.id,
        client="Edward Jones",
        project_name="Enterprise Data Strategy & Governance",
        project_type="advisory",
        date_range_label="2/2023-11/2023",
        domain_tags=["Financial Services", "Broker-Dealer", "Data Governance"],
        tech_tags=["Data Strategy", "Governance Frameworks"],
        order=1
    )
    db.add(edward_jones)
    db.flush()

    edward_jones_bullets = [
        Bullet(
            user_id=user.id,
            experience_id=bbc_2022.id,
            engagement_id=edward_jones.id,
            text="Designed and operationalized a firm-wide strategy for data culture, literacy, and governance.",
            tags=["Data Strategy", "Data Governance", "Broker-Dealer"],
            importance="high",
            ai_first_choice=True,
            order=1
        ),
    ]
    db.add_all(edward_jones_bullets)

    # Engagement: Darling Consulting Group
    darling = Engagement(
        experience_id=bbc_2022.id,
        client="Darling Consulting Group",
        project_name="Data Strategy & Analytics Portal",
        project_type="implementation",
        date_range_label="9/2022-1/2023",
        domain_tags=["Financial Services", "Banking", "Analytics Modernization"],
        tech_tags=["Analytics Portal", "Data Strategy"],
        order=2
    )
    db.add(darling)
    db.flush()

    darling_bullets = [
        Bullet(
            user_id=user.id,
            experience_id=bbc_2022.id,
            engagement_id=darling.id,
            text="Assessed enterprise data practices and led development of a client-facing analytics portal.",
            tags=["Analytics", "Data Assessment", "Banking"],
            importance="high",
            ai_first_choice=True,
            order=1
        ),
    ]
    db.add_all(darling_bullets)

    # =========================================================================
    # 4. MANTL (2/2021 – 6/2022)
    # =========================================================================
    mantl = Experience(
        user_id=user.id,
        job_title="Principal Systems Analyst – Activations",
        employer_name="MANTL (Capital G-funded omnichannel account-opening platform)",
        location="Remote",
        start_date=date(2021, 2, 1),
        end_date=date(2022, 6, 1),
        employer_type="full_time",
        fs_domain_relevance=0.85,
        tools_and_technologies=["Core Banking", "APIs", "Postman", "GitHub", "VS Code"],
        order=4
    )
    db.add(mantl)
    db.flush()

    mantl_bullets = [
        Bullet(
            user_id=user.id,
            experience_id=mantl.id,
            text="Collaborated with client bank, core banking providers (Fiserv Premier SOA & Signature, Jack Henry) and MANTL engineers to connect omnichannel account-opening technology via APIs.",
            tags=["Core Banking", "APIs", "Fiserv", "Jack Henry", "FinTech"],
            importance="high",
            ai_first_choice=True,
            order=1
        ),
        Bullet(
            user_id=user.id,
            experience_id=mantl.id,
            text="Tested and refined XML transactions using Postman, GitHub, VS Code in an agile environment.",
            tags=["API Testing", "Agile", "Technical"],
            importance="medium",
            order=2
        ),
    ]
    db.add_all(mantl_bullets)

    # =========================================================================
    # 5. BBC (7/2016 – 1/2021) - Principal Consultant
    # =========================================================================
    bbc_2016 = Experience(
        user_id=user.id,
        job_title="Principal Consultant",
        employer_name="Benjamin Black Consulting",
        location="Boston, MA",
        start_date=date(2016, 7, 1),
        end_date=date(2021, 1, 1),
        employer_type="independent_consulting",
        role_summary="Focused on AI/ML commercialization, data governance, and analytics modernization for top financial institutions.",
        fs_domain_relevance=0.95,
        tools_and_technologies=["AI/ML", "Data Governance", "Analytics"],
        order=5
    )
    db.add(bbc_2016)
    db.flush()

    # Engagement: Squark
    squark = Engagement(
        experience_id=bbc_2016.id,
        client="Squark (AI/ML startup)",
        project_name="Go-to-Market & Product Strategy",
        project_type="advisory",
        date_range_label="5/2018-7/2020",
        domain_tags=["AI Strategy", "AI/ML"],
        tech_tags=["AI/ML", "Product Strategy"],
        order=1
    )
    db.add(squark)
    db.flush()

    squark_bullets = [
        Bullet(
            user_id=user.id,
            experience_id=bbc_2016.id,
            engagement_id=squark.id,
            text="Defined early AI/ML product offerings, value propositions, and GTM strategy targeting asset managers.",
            tags=["AI/ML", "Product Strategy", "GTM", "Asset Management"],
            importance="high",
            ai_first_choice=True,
            order=1
        ),
    ]
    db.add_all(squark_bullets)

    # Engagement: Vestmark
    vestmark = Engagement(
        experience_id=bbc_2016.id,
        client="Vestmark",
        project_name="WealthTech Platform & Client Delivery",
        project_type="implementation",
        date_range_label="7/2017-3/2018",
        domain_tags=["Financial Services", "WealthTech"],
        tech_tags=["Agile", "Integrations"],
        order=2
    )
    db.add(vestmark)
    db.flush()

    vestmark_bullets = [
        Bullet(
            user_id=user.id,
            experience_id=bbc_2016.id,
            engagement_id=vestmark.id,
            text="Directed agile delivery of integrations, customizations, and enhancements for top broker-dealer and wealth-management clients.",
            tags=["WealthTech", "Agile", "Broker-Dealer"],
            importance="high",
            ai_first_choice=True,
            order=1
        ),
    ]
    db.add_all(vestmark_bullets)

    # Engagement: John Hancock Investments (via Olmstead)
    jhi = Engagement(
        experience_id=bbc_2016.id,
        client="John Hancock Investments (via Olmstead Associates)",
        project_name="SEC Modernization Architecture",
        project_type="advisory",
        date_range_label="11/2016-1/2017",
        domain_tags=["Financial Services", "Asset Management", "Regulatory Compliance"],
        tech_tags=["Data Architecture", "Data Lineage"],
        order=3
    )
    db.add(jhi)
    db.flush()

    jhi_bullets = [
        Bullet(
            user_id=user.id,
            experience_id=bbc_2016.id,
            engagement_id=jhi.id,
            text="Designed the data architecture, governance model, and full data-lineage for SEC modernization compliance.",
            tags=["Data Architecture", "Governance", "SEC", "Compliance"],
            importance="high",
            ai_first_choice=True,
            order=1
        ),
        Bullet(
            user_id=user.id,
            experience_id=bbc_2016.id,
            engagement_id=jhi.id,
            text="Mapped systems, interfaces, and data sources across custodians, sub-advisers, pricing feeds, and IBOR.",
            tags=["Data Architecture", "Systems Integration", "Asset Management"],
            importance="medium",
            order=2
        ),
    ]
    db.add_all(jhi_bullets)

    # Engagement: Olmstead Associates
    olmstead = Engagement(
        experience_id=bbc_2016.id,
        client="Olmstead Associates",
        project_name="Data Management Frameworks",
        project_type="advisory",
        date_range_label="1/2017-5/2017",
        domain_tags=["Data Governance", "Data Architecture"],
        tech_tags=["Governance Frameworks", "Assessment"],
        order=4
    )
    db.add(olmstead)
    db.flush()

    olmstead_bullets = [
        Bullet(
            user_id=user.id,
            experience_id=bbc_2016.id,
            engagement_id=olmstead.id,
            text="Developed reusable client-assessment and governance frameworks deployed across asset-management clients for migration readiness and regulatory compliance.",
            tags=["Governance Frameworks", "Assessment", "Asset Management"],
            importance="high",
            ai_first_choice=True,
            order=1
        ),
    ]
    db.add_all(olmstead_bullets)

    # Engagement: Fidelity Investments
    fidelity_bbc = Engagement(
        experience_id=bbc_2016.id,
        client="Fidelity Investments",
        project_name="Finance IT Data Strategy",
        project_type="advisory",
        date_range_label="8/2016-11/2016",
        domain_tags=["Financial Services", "Asset Management", "Analytics Modernization"],
        tech_tags=["Data Strategy", "Architecture"],
        order=5
    )
    db.add(fidelity_bbc)
    db.flush()

    fidelity_bbc_bullets = [
        Bullet(
            user_id=user.id,
            experience_id=bbc_2016.id,
            engagement_id=fidelity_bbc.id,
            text="Created a data-strategy roadmap optimizing compute, storage, and analytics workflows for Finance IT.",
            tags=["Data Strategy", "Analytics", "Finance IT"],
            importance="high",
            ai_first_choice=True,
            order=1
        ),
        Bullet(
            user_id=user.id,
            experience_id=bbc_2016.id,
            engagement_id=fidelity_bbc.id,
            text="Evaluated architecture and governance practices against strategic objectives, surfaced risks and alignment gaps.",
            tags=["Architecture", "Governance", "Risk Assessment"],
            importance="medium",
            order=2
        ),
    ]
    db.add_all(fidelity_bbc_bullets)

    # =========================================================================
    # 6. Knowledgent Group (12/2014 – 6/2016)
    # =========================================================================
    knowledgent = Experience(
        user_id=user.id,
        job_title="Senior Consultant",
        employer_name="Knowledgent Group, Inc. (acquired by Accenture)",
        location="Boston, MA",
        start_date=date(2014, 12, 1),
        end_date=date(2016, 6, 1),
        employer_type="full_time",
        fs_domain_relevance=0.9,
        tools_and_technologies=["Azure", "Hadoop", "SQL", "Python", "R", "QlikView", "Tableau"],
        order=6
    )
    db.add(knowledgent)
    db.flush()

    # Engagement: John Hancock Financial Services
    jhfs = Engagement(
        experience_id=knowledgent.id,
        client="John Hancock Financial Services",
        project_name="Azure Big Data Platform & Enterprise Analytics",
        project_type="implementation",
        date_range_label="12/2014-6/2016",
        domain_tags=["Financial Services", "Asset Management", "Cloud Platforms"],
        tech_tags=["Azure", "Hadoop", "Big Data", "Analytics"],
        order=1
    )
    db.add(jhfs)
    db.flush()

    jhfs_bullets = [
        Bullet(
            user_id=user.id,
            experience_id=knowledgent.id,
            engagement_id=jhfs.id,
            text="Designed and launched a Microsoft Azure–based Hadoop data lake and shared big-data service supporting all investment and business units.",
            tags=["Azure", "Hadoop", "Data Lake", "Big Data"],
            importance="high",
            ai_first_choice=True,
            order=1
        ),
        Bullet(
            user_id=user.id,
            experience_id=knowledgent.id,
            engagement_id=jhfs.id,
            text="Defined analytics use cases, success metrics, and proof-of-value criteria to accelerate adoption of cloud analytics.",
            tags=["Analytics", "Cloud", "Use Cases"],
            importance="high",
            ai_first_choice=True,
            order=2
        ),
        Bullet(
            user_id=user.id,
            experience_id=knowledgent.id,
            engagement_id=jhfs.id,
            text="Built dynamic C-suite business intelligence dashboards (QlikView/Tableau).",
            tags=["BI", "Dashboards", "QlikView", "Tableau"],
            importance="medium",
            order=3
        ),
        Bullet(
            user_id=user.id,
            experience_id=knowledgent.id,
            engagement_id=jhfs.id,
            text="Developed and optimized data models, pipelines, and workflows across structured and unstructured sources.",
            tags=["Data Modeling", "Pipelines", "ETL"],
            importance="medium",
            order=4
        ),
        Bullet(
            user_id=user.id,
            experience_id=knowledgent.id,
            engagement_id=jhfs.id,
            text="Analyzed datasets in SQL, Python, R, and PowerShell to validate quality, ingestion logic, and analytic outputs.",
            tags=["SQL", "Python", "R", "Data Quality"],
            importance="medium",
            order=5
        ),
    ]
    db.add_all(jhfs_bullets)

    # =========================================================================
    # 7. Santander Bank (2/2010 – 12/2014)
    # =========================================================================
    santander = Experience(
        user_id=user.id,
        job_title="Platform Product Lead",
        employer_name="Santander Bank, N.A. (Sovereign Bank)",
        location="Boston, MA",
        start_date=date(2010, 2, 1),
        end_date=date(2014, 12, 1),
        employer_type="full_time",
        fs_domain_relevance=0.95,
        tools_and_technologies=["Product Management", "Change Management", "Governance"],
        order=7
    )
    db.add(santander)
    db.flush()

    santander_bullets = [
        Bullet(
            user_id=user.id,
            experience_id=santander.id,
            text="Product lead on bank's core enterprise transactional/content platform for 10,000+ users; a global strategic asset.",
            tags=["Product Management", "Banking", "Enterprise Platform"],
            importance="high",
            ai_first_choice=True,
            order=1
        ),
        Bullet(
            user_id=user.id,
            experience_id=santander.id,
            text="Led the U.S. rollout of a Spain-developed platform, building the team, governance model, controls framework, and operational processes, driving business process redesign and change management across multiple units.",
            tags=["Change Management", "Governance", "International"],
            importance="high",
            ai_first_choice=True,
            order=2
        ),
        Bullet(
            user_id=user.id,
            experience_id=santander.id,
            text="Directed requirements, process design, vendor management, and continuous improvement for a mission-critical internal system.",
            tags=["Requirements", "Vendor Management", "Process Design"],
            importance="medium",
            order=3
        ),
        Bullet(
            user_id=user.id,
            experience_id=santander.id,
            text="Delivered three CEO-priority software initiatives on schedule and budget.",
            tags=["Leadership", "Delivery", "Executive"],
            importance="high",
            ai_first_choice=True,
            order=4
        ),
    ]
    db.add_all(santander_bullets)

    # =========================================================================
    # 8. Fidelity Investments (6/2008 – 4/2009)
    # =========================================================================
    fidelity = Experience(
        user_id=user.id,
        job_title="Senior Analyst – Strategic Modeling & Analysis, Fidelity Technology Group",
        employer_name="Fidelity Investments",
        location="Boston, MA",
        start_date=date(2008, 6, 1),
        end_date=date(2009, 4, 1),
        employer_type="full_time",
        fs_domain_relevance=0.95,
        tools_and_technologies=["Analytics", "Systems Dynamics", "Business Case"],
        order=8
    )
    db.add(fidelity)
    db.flush()

    fidelity_bullets = [
        Bullet(
            user_id=user.id,
            experience_id=fidelity.id,
            text="Advised product managers on best practices for unified customer communication.",
            tags=["Product Management", "Customer Communication"],
            importance="medium",
            order=1
        ),
        Bullet(
            user_id=user.id,
            experience_id=fidelity.id,
            text="Subject matter expert on digital consumer analytics and shared insights in widely distributed internal reports.",
            tags=["Analytics", "Consumer Analytics", "Thought Leadership"],
            importance="medium",
            order=2
        ),
        Bullet(
            user_id=user.id,
            experience_id=fidelity.id,
            text="Assessed feasibility of $300M business case through a systems dynamics model of contact center operations.",
            tags=["Business Case", "Systems Dynamics", "Contact Center"],
            importance="high",
            ai_first_choice=True,
            order=3
        ),
    ]
    db.add_all(fidelity_bullets)


def run_population():
    """Execute the data population."""
    print("=" * 60)
    print("Populating December 2025 Resume Data")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Get or create user
        user = get_or_create_user(db)
        print(f"User: {user.full_name} (id={user.id})")

        # Clear existing data
        print("Clearing existing experiences, engagements, and bullets...")
        clear_existing_data(db, user.id)

        # Create new data
        print("Creating experiences with engagements and bullets...")
        create_experiences_and_engagements(db, user)

        # Commit
        db.commit()

        # Summary
        exp_count = db.query(Experience).filter(Experience.user_id == user.id).count()
        eng_count = db.query(Engagement).join(Experience).filter(Experience.user_id == user.id).count()
        bullet_count = db.query(Bullet).filter(Bullet.user_id == user.id).count()

        print(f"\nCreated:")
        print(f"  - {exp_count} experiences")
        print(f"  - {eng_count} engagements")
        print(f"  - {bullet_count} bullets")

        print("\n" + "=" * 60)
        print("Population completed successfully!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\nPopulation failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_population()
