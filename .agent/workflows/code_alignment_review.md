---
description: Review codebase for alignment with PRD, Architecture, and Data Model.
---

# Codebase Alignment Review Workflow

This workflow guides the agent through verifying that the implemented code matches the design documents.

## 1. Structure Verification
1.  Compare the directory structure against the **Architecture** document.
2.  Verify that key components (Services, Routers, Database Models) exist where expected.

## 2. Data Model Verification
1.  Compare `models.py` (SQLAlchemy) against the **Data Model** document.
2.  Check for missing fields, incorrect data types, or mismatched relationships.
3.  Verify that Pydantic schemas (`schemas/`) align with the database models and API requirements.

## 3. Feature Verification
1.  Select a sample of features from the **Implementation Plan** (e.g., specific Sprints).
2.  Verify that the corresponding code exists in `services/` and `routers/`.
3.  Check for key logic described in the **PRD** (e.g., specific algorithms, validation rules).

## 4. Logic & Quality Check
1.  Sample key files (e.g., main orchestrators, complex algorithms).
2.  Check for code quality, comments, and adherence to patterns described in the Architecture.
3.  Verify that "TODOs" or "Not Implemented" sections are tracked or consistent with the plan.

## 5. Reporting
1.  Create a markdown report (e.g., `codebase_alignment_issues.md`).
2.  Document:
    *   Structural mismatches
    *   Data model discrepancies
    *   Missing features (that should be present according to the plan)
    *   Logic errors or deviations from PRD
3.  Provide recommendations for remediation.
