---
description: >
  Governs all implementation work on the CDSCO Medical Device Submission Dossier Builder.
  Apply these rules to every coding session without exception.
---

# CDSCO Implementation Workflow Rules

## Core Discipline

You implement **one atomic sub-task at a time**, stop, report, and wait for user approval before continuing. You do not chain multiple sub-tasks in a single response.

---

## Before Writing Any Code

1. Read `docs/project-status.md` to understand the current engineering state and identify the **single next sub-task**.
2. Read the relevant technical specification document(s) for that sub-task **before writing code** (never guess field names or contracts):
   - **System Architecture & Data Flows:** `docs/technical_reference/03_SYSTEM_ARCHITECTURE_AND_DATA_FLOW.md`
   - **Database Schemas, DDL, JSON Contracts & REST API Endpoints:** `docs/technical_reference/04_ENGINEERING_AND_DATA_MODEL_SPEC.md`
   - **Engine 1 (Jinja2/docxtpl) & Engine 2 (PyMuPDF/pikepdf):** `docs/technical_reference/05_DOCUMENT_ENGINES_AND_FULFILLMENT_LOGIC.md`
   - **Team Distribution, Phase WBS & Hand-Off Gates:** `docs/technical_reference/06_TEAM_DISTRIBUTION_AND_SEQUENTIAL_WORKFLOW.md`
   - **Requirements Traceability Matrix (RTM) & Test Specifications:** `docs/technical_reference/07_SYSTEM_VERIFICATION_AND_TEST_TRACEABILITY.md`
   - **Regulatory Forms & Fourth Schedule Hierarchy:** `docs/05_REGULATORY_FORMS_AND_DOSSIER_MATRIX.md`
   - **Primary Official Checklists:** `md/` (General MD) and `ivd/` (IVD) directories
3. Cross-check existing code before adding anything — never duplicate or contradict existing implementations.

---

## Sub-Task Execution Rules

- Implement exactly **one sub-task** at a time — the smallest meaningful unit of work (e.g. one SQLAlchemy model, one Alembic migration, one REST endpoint, one Jinja2 template, one React component, one test file).
- Do not implement the next sub-task "while you're at it".
- Do not refactor unrelated code.
- Do not introduce dependencies not listed in the engineering specifications without explicitly flagging them first.

---

## After Every Sub-Task

1. **Update `docs/project-status.md`:**
   - Mark the completed sub-task `[x]`
   - Update the "Last completed" line with timestamp and git commit/diff summary
   - Mark the next sub-task `[ ]` as active
2. **Report to the user** (short, in chat — no fluff, zero emojis):
   - **What was implemented:** 2 to 3 concise bullet points
   - **Files created or modified:** List of file paths only
   - **How to validate it works:** 1 to 3 direct commands or verification checks (no lengthy essays)
3. **Stop. Wait for approval before proceeding.**

---

## Validation Principle

After each sub-task, provide the user with the **minimum verification steps** needed to confirm correctness:
- Run a specific pytest command: `pytest tests/unit/test_<name>.py -v`
- Run a curl or API test: `curl -X POST http://localhost:8000/api/v1/...`
- Inspect a generated file or database record
Do not write essays. Keep commands copy-pasteable.

---

## Regulatory and Engineering Integrity Rules (Always)

- **Strict Schema Adherence:** Never invent field names, slot keys (e.g. `1.0`, `10.1`, `10.11`), validation rule codes, or API paths. Adhere strictly to [04_ENGINEERING_AND_DATA_MODEL_SPEC.md](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/04_ENGINEERING_AND_DATA_MODEL_SPEC.md).
- **Statutory Completion:** Never mark a regulatory slot or feature as done unless its technical specification is fully implemented and passes its corresponding test case in [07_SYSTEM_VERIFICATION_AND_TEST_TRACEABILITY.md](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/07_SYSTEM_VERIFICATION_AND_TEST_TRACEABILITY.md).
- **10.0 MB Portal Ceiling:** Engine 2 must strictly enforce the $10,485,760$ bytes limit on all compiled dossiers and uploads.
- **Continuous Bates Numbering:** Stamped running headers and footers must conform exactly to `{bates_prefix}-{page_num:04d} | Page {page_num} of {total_pages}`.
- **Dual Fulfillment Integrity:** For generatable slots, always preserve both Option A (Upload Existing PDF) and Option B (Guided Form Generation).

---

## File Modification Rules

- Understand existing code and tests before modifying any file.
- Do not modify files outside the current sub-task's scope.
- Maintain documentation integrity: preserve all existing comments and docstrings unless directly related to the modification.

---

## Sub-Task Size Guide

### Good sub-tasks (Right size):
- "1.1.1: Initialize Python 3.11+ FastAPI project with async SQLAlchemy 2.0 and Alembic"
- "1.1.2: Execute PostgreSQL DDL migration for `application_definitions` and `profiles` tables"
- "1.2.1: Author declarative JSON schema blueprint fixture for Form MD-14 (36 discrete upload slots)"
- "1.3.1: Define `StorageProvider` abstract base interface"
- "1.3.2: Implement `LocalStorageProvider` writing to `./storage/submissions/{id}/`"
- "1.4.1: Build `POST /api/v1/submissions/{id}/evidence/upload` endpoint"
- "2.1.1: Author `covering_letter.html` Jinja2 template and print CSS"
- "2.3.2: Implement PyMuPDF two-pass Table of Contents offset calculator"

### Too large (Must be split):
- "Scaffold backend and write all database migrations"
- "Implement Engine 1 and all templates"
- "Build the entire frontend workspace"
- "Write all unit and integration tests"
