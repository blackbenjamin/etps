"""
Capability Ontology (Sprint 11)

Curated ontology of 25+ capability clusters for senior/strategic roles.
Each cluster contains:
- Description
- Component skills (Tier 2)
- Evidence keywords (Tier 3) that map to existing SKILL_TAXONOMY
- Typical importance levels
"""

from typing import Dict, List, Any


# Capability Ontology: 25 clusters covering AI, Data, Consulting, Technical, and Leadership roles
CAPABILITY_ONTOLOGY: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # AI & DATA STRATEGY CLUSTERS
    # =========================================================================
    "AI & Data Strategy": {
        "description": "Strategic leadership in AI/ML initiatives and data-driven transformation, including roadmap creation, stakeholder alignment, and business case development",
        "component_skills": [
            "AI roadmap creation",
            "Data strategy development",
            "Stakeholder alignment",
            "Business case development",
            "AI governance framework design",
            "Value articulation to executives",
            "Digital transformation leadership"
        ],
        "evidence_keywords": [
            "AI", "Machine Learning", "Data Science", "Strategy", "Roadmap",
            "Digital Transformation", "AI Governance", "Data Strategy"
        ],
        "typical_importance": "critical",
        "role_indicators": ["strategy", "director", "head of", "lead", "principal", "vp"]
    },

    "Solution Architecture": {
        "description": "Design and implementation of enterprise-scale technical solutions, including system design, cloud integration, and end-to-end architecture",
        "component_skills": [
            "System design",
            "Cloud architecture",
            "API design",
            "Data architecture",
            "Integration patterns",
            "Performance optimization",
            "Security architecture",
            "Scalability design"
        ],
        "evidence_keywords": [
            "AWS", "Azure", "GCP", "Architecture", "Microservices", "API",
            "System Design", "Cloud", "Infrastructure", "Kubernetes", "Docker"
        ],
        "typical_importance": "critical",
        "role_indicators": ["architect", "principal", "staff", "senior"]
    },

    "Machine Learning Engineering": {
        "description": "Building and deploying production ML systems, including model development, MLOps, and inference optimization",
        "component_skills": [
            "Model development",
            "Feature engineering",
            "Model training & tuning",
            "MLOps & deployment",
            "Inference optimization",
            "Model monitoring",
            "A/B testing for ML"
        ],
        "evidence_keywords": [
            "TensorFlow", "PyTorch", "Scikit-learn", "MLOps", "ML",
            "Deep Learning", "NLP", "Computer Vision", "Model Training"
        ],
        "typical_importance": "critical",
        "role_indicators": ["ml engineer", "machine learning", "ai engineer"]
    },

    "Data Engineering": {
        "description": "Building and maintaining data infrastructure, pipelines, and platforms for analytics and ML workloads",
        "component_skills": [
            "Data pipeline development",
            "ETL/ELT design",
            "Data warehouse architecture",
            "Real-time streaming",
            "Data quality management",
            "Data cataloging",
            "Performance tuning"
        ],
        "evidence_keywords": [
            "Spark", "Kafka", "Airflow", "dbt", "Databricks", "Snowflake",
            "ETL", "Data Pipeline", "Data Warehouse", "Hadoop"
        ],
        "typical_importance": "critical",
        "role_indicators": ["data engineer", "platform", "infrastructure"]
    },

    "Data Governance & Compliance": {
        "description": "Establishing data governance frameworks, ensuring regulatory compliance, and managing data quality and lineage",
        "component_skills": [
            "Governance framework design",
            "Data quality management",
            "Metadata management",
            "Data lineage tracking",
            "Regulatory compliance",
            "Privacy engineering",
            "Access control design"
        ],
        "evidence_keywords": [
            "Data Governance", "GDPR", "CCPA", "HIPAA", "SOC 2", "Data Catalog",
            "Collibra", "Alation", "Metadata", "Compliance"
        ],
        "typical_importance": "important",
        "role_indicators": ["governance", "compliance", "privacy", "steward"]
    },

    # =========================================================================
    # ADVISORY & CONSULTING CLUSTERS
    # =========================================================================
    "Client Advisory & Consulting": {
        "description": "Serving as trusted advisor to clients, facilitating workshops, and translating technical concepts for business stakeholders",
        "component_skills": [
            "Executive advisory",
            "Workshop facilitation",
            "Requirements discovery",
            "Stakeholder management",
            "Technical communication",
            "Proposal development",
            "Client relationship management"
        ],
        "evidence_keywords": [
            "Consulting", "Advisory", "Strategy", "Stakeholder",
            "Client", "Workshop", "Discovery", "Requirements"
        ],
        "typical_importance": "critical",
        "role_indicators": ["consultant", "advisor", "partner", "director"]
    },

    "Business Development & Growth": {
        "description": "Driving business growth through pipeline development, go-to-market strategies, and thought leadership",
        "component_skills": [
            "Pipeline development",
            "Go-to-market strategy",
            "Proposal writing",
            "Thought leadership",
            "Conference speaking",
            "White paper authoring",
            "Industry networking"
        ],
        "evidence_keywords": [
            "Business Development", "Sales", "GTM", "Proposal",
            "Revenue", "Growth", "Partnership", "Market"
        ],
        "typical_importance": "important",
        "role_indicators": ["business development", "growth", "sales", "partner"]
    },

    "Product Management": {
        "description": "Defining product vision, managing roadmaps, and driving product development from conception to launch",
        "component_skills": [
            "Product vision",
            "Roadmap management",
            "User research",
            "Feature prioritization",
            "Stakeholder alignment",
            "Go-to-market planning",
            "Metrics definition"
        ],
        "evidence_keywords": [
            "Product", "Roadmap", "User Research", "Feature",
            "Agile", "Scrum", "Sprint", "Backlog"
        ],
        "typical_importance": "critical",
        "role_indicators": ["product manager", "product owner", "pm"]
    },

    # =========================================================================
    # TECHNICAL DEPTH CLUSTERS
    # =========================================================================
    "Full-Stack Development": {
        "description": "End-to-end application development across frontend, backend, and infrastructure layers",
        "component_skills": [
            "Frontend development",
            "Backend development",
            "API development",
            "Database design",
            "DevOps practices",
            "Testing & QA",
            "Performance optimization"
        ],
        "evidence_keywords": [
            "React", "Angular", "Vue", "Node.js", "Python", "Java",
            "JavaScript", "TypeScript", "FastAPI", "Django", "Express"
        ],
        "typical_importance": "critical",
        "role_indicators": ["full-stack", "software engineer", "developer"]
    },

    "Cloud & Infrastructure": {
        "description": "Managing cloud infrastructure, DevOps practices, and platform reliability",
        "component_skills": [
            "Cloud platform management",
            "Infrastructure as Code",
            "CI/CD pipelines",
            "Container orchestration",
            "Monitoring & observability",
            "Cost optimization",
            "Disaster recovery"
        ],
        "evidence_keywords": [
            "AWS", "Azure", "GCP", "Terraform", "Kubernetes", "Docker",
            "CI/CD", "Jenkins", "GitHub Actions", "Prometheus", "Grafana"
        ],
        "typical_importance": "critical",
        "role_indicators": ["devops", "sre", "platform", "infrastructure"]
    },

    "Security & Cybersecurity": {
        "description": "Implementing security practices, managing vulnerabilities, and ensuring secure system design",
        "component_skills": [
            "Security architecture",
            "Vulnerability management",
            "Identity & access management",
            "Encryption & key management",
            "Security monitoring",
            "Incident response",
            "Compliance enforcement"
        ],
        "evidence_keywords": [
            "Security", "OAuth", "JWT", "Encryption", "SAML",
            "Zero Trust", "Cybersecurity", "Penetration Testing"
        ],
        "typical_importance": "important",
        "role_indicators": ["security", "infosec", "cybersecurity"]
    },

    "Analytics & Business Intelligence": {
        "description": "Building analytics solutions, dashboards, and insights platforms for data-driven decision making",
        "component_skills": [
            "Dashboard development",
            "Report design",
            "Data visualization",
            "Metrics definition",
            "Self-service analytics",
            "Data storytelling",
            "KPI tracking"
        ],
        "evidence_keywords": [
            "Tableau", "Power BI", "Looker", "Analytics", "Dashboard",
            "SQL", "Visualization", "Reporting", "Metrics"
        ],
        "typical_importance": "important",
        "role_indicators": ["analytics", "bi", "data analyst"]
    },

    # =========================================================================
    # EMERGING TECHNOLOGY CLUSTERS
    # =========================================================================
    "Emerging Technologies": {
        "description": "Staying current with and implementing emerging technologies including IoT, edge computing, and digital twins",
        "component_skills": [
            "Technology scouting",
            "Proof of concept development",
            "Pilot deployment",
            "Innovation programs",
            "Technology evaluation",
            "Trend analysis"
        ],
        "evidence_keywords": [
            "IoT", "Edge Computing", "Digital Twin", "Blockchain",
            "AR/VR", "5G", "Quantum", "Innovation"
        ],
        "typical_importance": "nice-to-have",
        "role_indicators": ["emerging", "innovation", "r&d", "labs"]
    },

    "IoT & Edge Computing": {
        "description": "Designing and implementing IoT ecosystems, edge computing solutions, and sensor networks",
        "component_skills": [
            "IoT architecture",
            "Edge deployment",
            "Sensor integration",
            "Real-time processing",
            "Device management",
            "Connectivity protocols"
        ],
        "evidence_keywords": [
            "IoT", "Edge", "Sensor", "MQTT", "Embedded",
            "Real-time", "Device", "Connectivity"
        ],
        "typical_importance": "important",
        "role_indicators": ["iot", "edge", "embedded", "smart"]
    },

    "Digital Twins & Simulation": {
        "description": "Creating digital twin models for simulation, optimization, and predictive analytics",
        "component_skills": [
            "Digital twin modeling",
            "Simulation design",
            "Optimization algorithms",
            "Predictive modeling",
            "3D visualization",
            "Sensor data integration"
        ],
        "evidence_keywords": [
            "Digital Twin", "Simulation", "Modeling", "Optimization",
            "Predictive", "3D", "CAD", "BIM"
        ],
        "typical_importance": "nice-to-have",
        "role_indicators": ["digital twin", "simulation", "modeling"]
    },

    "Generative AI & LLMs": {
        "description": "Implementing generative AI solutions, LLM applications, and prompt engineering",
        "component_skills": [
            "LLM integration",
            "Prompt engineering",
            "RAG implementation",
            "Fine-tuning",
            "AI safety & guardrails",
            "Cost optimization"
        ],
        "evidence_keywords": [
            "LLM", "GPT", "Claude", "LangChain", "RAG",
            "Generative AI", "Prompt Engineering", "OpenAI"
        ],
        "typical_importance": "critical",
        "role_indicators": ["generative ai", "llm", "ai engineer"]
    },

    # =========================================================================
    # DOMAIN EXPERTISE CLUSTERS
    # =========================================================================
    "Financial Services Domain": {
        "description": "Deep expertise in financial services including banking, investment management, and fintech",
        "component_skills": [
            "Banking systems",
            "Investment management",
            "Risk modeling",
            "Regulatory compliance",
            "Payment systems",
            "Trading platforms"
        ],
        "evidence_keywords": [
            "Banking", "Investment", "Fintech", "Trading",
            "Risk", "Compliance", "Payment", "Finance"
        ],
        "typical_importance": "important",
        "role_indicators": ["financial", "banking", "fintech", "investment"]
    },

    "Healthcare & Life Sciences Domain": {
        "description": "Deep expertise in healthcare, pharmaceuticals, and life sciences",
        "component_skills": [
            "Healthcare systems",
            "Clinical data management",
            "Regulatory compliance (HIPAA/FDA)",
            "Drug discovery support",
            "Patient data privacy",
            "EHR integration"
        ],
        "evidence_keywords": [
            "Healthcare", "HIPAA", "Clinical", "Pharma",
            "EHR", "FDA", "Life Sciences", "Medical"
        ],
        "typical_importance": "important",
        "role_indicators": ["healthcare", "pharma", "clinical", "medical"]
    },

    "Transportation & Mobility Domain": {
        "description": "Deep expertise in transportation, mobility, and smart city infrastructure",
        "component_skills": [
            "Transportation systems",
            "Mobility analytics",
            "Traffic optimization",
            "Fleet management",
            "Smart city integration",
            "Infrastructure resilience"
        ],
        "evidence_keywords": [
            "Transportation", "Mobility", "Smart City", "Traffic",
            "Fleet", "Infrastructure", "Logistics", "Autonomous"
        ],
        "typical_importance": "important",
        "role_indicators": ["transportation", "mobility", "smart city", "infrastructure"]
    },

    "Critical Infrastructure Domain": {
        "description": "Expertise in critical infrastructure including utilities, energy, and public services",
        "component_skills": [
            "Infrastructure resilience",
            "Utility systems",
            "Energy management",
            "Public safety systems",
            "Disaster recovery",
            "Asset management"
        ],
        "evidence_keywords": [
            "Infrastructure", "Utility", "Energy", "Public Safety",
            "Resilience", "Asset", "Grid", "Power"
        ],
        "typical_importance": "important",
        "role_indicators": ["infrastructure", "utility", "energy", "critical"]
    },

    # =========================================================================
    # LEADERSHIP & MANAGEMENT CLUSTERS
    # =========================================================================
    "Technical Leadership": {
        "description": "Leading technical teams, mentoring engineers, and driving technical excellence",
        "component_skills": [
            "Team leadership",
            "Technical mentorship",
            "Code review culture",
            "Architecture decisions",
            "Technical hiring",
            "Career development",
            "Knowledge sharing"
        ],
        "evidence_keywords": [
            "Lead", "Principal", "Staff", "Mentor",
            "Team", "Architecture Review", "Technical Leadership"
        ],
        "typical_importance": "critical",
        "role_indicators": ["lead", "principal", "staff", "manager"]
    },

    "Program & Project Management": {
        "description": "Managing complex programs and projects with multiple workstreams and stakeholders",
        "component_skills": [
            "Program planning",
            "Stakeholder management",
            "Risk management",
            "Budget management",
            "Timeline management",
            "Resource allocation",
            "Vendor management"
        ],
        "evidence_keywords": [
            "PMP", "Program", "Project", "Agile", "Scrum",
            "Timeline", "Budget", "Risk", "Stakeholder"
        ],
        "typical_importance": "important",
        "role_indicators": ["program manager", "project manager", "pmo"]
    },

    "Cross-Functional Collaboration": {
        "description": "Working effectively across teams, departments, and organizational boundaries",
        "component_skills": [
            "Cross-team coordination",
            "Stakeholder alignment",
            "Conflict resolution",
            "Influence without authority",
            "Virtual collaboration",
            "Communication"
        ],
        "evidence_keywords": [
            "Cross-functional", "Collaboration", "Stakeholder",
            "Communication", "Team", "Partnership"
        ],
        "typical_importance": "important",
        "role_indicators": ["collaboration", "cross-functional", "partner"]
    },

    "Enterprise Architecture": {
        "description": "Defining enterprise-wide technology standards, patterns, and governance",
        "component_skills": [
            "Enterprise standards",
            "Technology governance",
            "Reference architecture",
            "Vendor evaluation",
            "Technology strategy",
            "Integration patterns"
        ],
        "evidence_keywords": [
            "TOGAF", "Enterprise Architecture", "Standards",
            "Governance", "Reference Architecture", "EA"
        ],
        "typical_importance": "important",
        "role_indicators": ["enterprise architect", "ea", "chief architect"]
    },

    "AI Ethics & Responsible AI": {
        "description": "Ensuring AI systems are developed and deployed responsibly with appropriate governance",
        "component_skills": [
            "AI ethics frameworks",
            "Bias detection & mitigation",
            "Explainability",
            "Model governance",
            "Risk assessment",
            "Regulatory compliance"
        ],
        "evidence_keywords": [
            "AI Ethics", "Responsible AI", "Bias", "Fairness",
            "Explainability", "Model Risk", "AI Governance"
        ],
        "typical_importance": "important",
        "role_indicators": ["ethics", "responsible ai", "governance"]
    },

    # =========================================================================
    # BUSINESS ANALYSIS & REQUIREMENTS CLUSTERS (Added v1.4)
    # =========================================================================
    "Requirements Engineering": {
        "description": "Gathering, documenting, and managing business and technical requirements throughout the project lifecycle",
        "component_skills": [
            "Requirements elicitation",
            "User story creation",
            "Acceptance criteria definition",
            "Requirements traceability",
            "Prototyping",
            "Stakeholder interviews",
            "Gap analysis"
        ],
        "evidence_keywords": [
            "Requirements", "User Stories", "Use Cases", "BRD",
            "FRD", "Prototyping", "Wireframes", "Specifications",
            "Traceability", "Acceptance Criteria"
        ],
        "typical_importance": "important",
        "role_indicators": ["business analyst", "requirements", "ba", "analyst"]
    },

    "Business Analysis": {
        "description": "Analyzing business processes, identifying improvements, and driving operational efficiency",
        "component_skills": [
            "Process mapping",
            "Gap analysis",
            "Business case development",
            "ROI analysis",
            "Workflow optimization",
            "Data analysis",
            "Root cause analysis"
        ],
        "evidence_keywords": [
            "Business Analysis", "Process Improvement", "ROI",
            "Business Case", "Workflow", "Process Mapping", "BPMN",
            "Gap Analysis", "Process Optimization"
        ],
        "typical_importance": "important",
        "role_indicators": ["business analyst", "process improvement", "ba", "operations"]
    },

    "Change Management": {
        "description": "Managing organizational change initiatives, stakeholder adoption, and transformation programs",
        "component_skills": [
            "Change strategy development",
            "Stakeholder engagement",
            "Training & enablement",
            "Communication planning",
            "Resistance management",
            "Adoption metrics",
            "Change impact assessment"
        ],
        "evidence_keywords": [
            "Change Management", "Organizational Change", "Adoption",
            "Training", "Communication", "Transformation", "ADKAR",
            "Stakeholder Management", "OCM"
        ],
        "typical_importance": "important",
        "role_indicators": ["change management", "transformation", "adoption", "ocm"]
    },

    "Vendor Management": {
        "description": "Managing vendor relationships, contracts, and third-party service delivery",
        "component_skills": [
            "Vendor evaluation",
            "Contract negotiation",
            "SLA management",
            "Vendor performance monitoring",
            "Risk assessment",
            "Procurement coordination"
        ],
        "evidence_keywords": [
            "Vendor Management", "Contract", "SLA", "Procurement",
            "Third-party", "RFP", "Vendor Selection", "Sourcing"
        ],
        "typical_importance": "important",
        "role_indicators": ["vendor", "procurement", "sourcing", "contract"]
    },

    "Stakeholder Communication": {
        "description": "Effective communication with diverse stakeholders including executives, technical teams, and business users",
        "component_skills": [
            "Executive presentations",
            "Technical writing",
            "Status reporting",
            "Meeting facilitation",
            "Conflict resolution",
            "Active listening"
        ],
        "evidence_keywords": [
            "Communication", "Presentation", "Stakeholder",
            "Reporting", "Executive", "Facilitation", "Briefing"
        ],
        "typical_importance": "important",
        "role_indicators": ["communication", "liaison", "coordinator"]
    }
}


def get_cluster_names() -> List[str]:
    """Return list of all capability cluster names."""
    return list(CAPABILITY_ONTOLOGY.keys())


def get_cluster(name: str) -> Dict[str, Any]:
    """Get a specific capability cluster by name."""
    return CAPABILITY_ONTOLOGY.get(name, {})


def get_clusters_by_keywords(keywords: List[str]) -> List[str]:
    """
    Find clusters that match given keywords.
    Returns cluster names sorted by match strength.
    """
    keyword_set = {k.lower() for k in keywords}
    matches = []

    for cluster_name, cluster_data in CAPABILITY_ONTOLOGY.items():
        evidence_keywords = {k.lower() for k in cluster_data.get("evidence_keywords", [])}
        overlap = keyword_set & evidence_keywords
        if overlap:
            matches.append((cluster_name, len(overlap)))

    # Sort by match count descending
    matches.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in matches]


def get_clusters_by_role_indicators(job_title: str) -> List[str]:
    """
    Find clusters that are typically relevant for a job title.
    Returns cluster names that have matching role indicators.
    """
    job_title_lower = job_title.lower()
    matches = []

    for cluster_name, cluster_data in CAPABILITY_ONTOLOGY.items():
        indicators = cluster_data.get("role_indicators", [])
        for indicator in indicators:
            if indicator in job_title_lower:
                matches.append(cluster_name)
                break

    return matches


def get_all_evidence_keywords() -> List[str]:
    """Return all unique evidence keywords from the ontology."""
    keywords = set()
    for cluster_data in CAPABILITY_ONTOLOGY.values():
        keywords.update(cluster_data.get("evidence_keywords", []))
    return sorted(keywords)


def get_ontology_summary() -> str:
    """
    Get a text summary of the ontology for use in LLM prompts.
    """
    lines = ["Available Capability Clusters:"]
    for name, data in CAPABILITY_ONTOLOGY.items():
        component_count = len(data.get("component_skills", []))
        lines.append(f"- {name} ({component_count} components): {data['description'][:100]}...")
    return "\n".join(lines)


# Export for convenience
__all__ = [
    "CAPABILITY_ONTOLOGY",
    "get_cluster_names",
    "get_cluster",
    "get_clusters_by_keywords",
    "get_clusters_by_role_indicators",
    "get_all_evidence_keywords",
    "get_ontology_summary"
]
