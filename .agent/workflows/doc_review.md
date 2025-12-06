---
description: Review documentation for consistency, completeness, and logic.
---

# Documentation Review Workflow

This workflow guides the agent through a systematic review of the project documentation.

## 1. Discovery
1.  List files in the documentation directory (e.g., `docs/`, `etps/`).
2.  Identify key documents:
    *   Product Requirements Document (PRD)
    *   Implementation Plan
    *   Architecture Document
    *   Data Model
    *   Testing Plan

## 2. Analysis
For each document, analyze:
*   **Version & Date:** Is it current? Does it match other documents?
*   **Completeness:** Are there missing sections?
*   **Consistency:** Do terms and definitions match across documents? (e.g., "Job Profile" vs "Job Description")
*   **Logic:** Does the proposed flow make sense?

## 3. Cross-Referencing
*   Check if the **Implementation Plan** matches the **PRD** phases.
*   Check if the **Architecture** supports the **PRD** requirements.
*   Check if the **Data Model** supports the **Architecture** and **PRD**.
*   Check if the **Testing Plan** covers the features in the **Implementation Plan**.

## 4. Reporting
1.  Create a markdown report (e.g., `documentation_review_issues.md`).
2.  List findings by category:
    *   Consistency
    *   Completeness
    *   Logic
3.  Assign a severity level (Low, Medium, High) to each issue.
4.  Provide a recommendation for each issue.
