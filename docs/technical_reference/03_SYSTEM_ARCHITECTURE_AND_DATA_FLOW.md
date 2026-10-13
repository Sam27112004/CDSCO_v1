# System Architecture and Data Flow Specification

**Document Identifier:** SAD-CDSCO-001  
**Revision:** 2.0  
**Classification:** Technical Architecture and System Design Baseline  
**Governing Standard:** Medical Devices Rules, 2017 (MDR 2017)  
**Status:** Approved for Implementation  

---

## 1. Architectural Principles and System Overview

The system architecture is structured around a **declarative, domain-driven engine** designed to decouple volatile regulatory rules and statutory forms from backend application logic and frontend presentation components.

```mermaid
flowchart TD
    subgraph Layer1["1. Presentation Layer (Web Workspace)"]
        UI["Dashboard | Entity Workspace | DMF/PMF Tree | Document Library | Validation Center | SUGAM Guide"]
    end

    subgraph Layer2["2. API Gateway & Transport Layer (FastAPI / Node)"]
        API["REST Endpoints | Server-Sent Events (SSE) | Session Auth & RBAC | Schema Validation"]
    end

    subgraph Layer3["3. Core Domain Engines"]
        E1["Application Definition Engine"]
        E2["Applicability & Rules Engine"]
        E3["Entity & Dossier Workspace Engine"]
        E4["Document Library & Linking Engine"]
        E5["Continuous Validation Engine"]
        E6["Assembly & SUGAM Handoff Engine"]
    end

    subgraph Layer4["4. Persistence & Storage Layer"]
        DB["PostgreSQL / SQLite Database | Secure Object Storage | Document Cache"]
    end

    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer3 --> Layer4
```

---

## 2. Core Domain Engines Pipeline

```mermaid
flowchart TD
    AppDef["1. Application Definition Engine<br/>(Parses Declarative Form Schemas)"]
    Context["Regulatory Context & Parameters<br/>(Device Class, Sterility, IVD)"]
    RulesEng["2. Applicability & Rules Engine<br/>(Evaluates Statutory Constraints & Predicates)"]
    Workspace["3. Entity & Dossier Workspace Engine<br/>(8-Point Guidance, Dual Fulfillment & DMF/PMF Trees)"]
    DocEng["4. Document Library & Linking Engine<br/>(Multi-Requirement Document Linking)"]
    ValEng["5. Continuous Validation Engine<br/>(Completeness & Reference Checks)"]
    HandoffEng["6. Assembly & SUGAM Handoff Engine<br/>(Dossier Compilation, 10MB Check & SUGAM Guide)"]
    Output["Interactive SUGAM Guide & Optional ZIP Archive"]

    AppDef --> RulesEng
    Context --> RulesEng
    RulesEng --> Workspace
    Workspace --> DocEng
    DocEng --> ValEng
    Workspace --> ValEng
    ValEng --> HandoffEng
    HandoffEng --> Output
```

### Functional Allocation Across Core Engines

| Engine Designation | Architectural Responsibility | Primary Inputs | Generated Outputs |
| :--- | :--- | :--- | :--- |
| **Application Definition Engine** | Parses declarative form schemas. Provides blueprints for forms MD-14, MD-7, MD-3, etc. | Declarative JSON Schemas | Compiled In-Memory Application Blueprint |
| **Applicability & Rules Engine** | Evaluates statutory constraints against regulatory context parameters (Risk Class, IVD, Sterility) to calculate requirement applicability. | Regulatory Context Attributes | Active, Conditional, and Non-Applicable Entity Lists |
| **Entity & Dossier Workspace Engine** | Manages one-entity-at-a-time rendering, resolves the 8-point regulatory guidance model, supports Dual Fulfillment (Upload vs. Generate), and tracks DMF/PMF hierarchy states. | Active Entity Key & Submission State | Resolved Entity ViewModel with Guidance, Form Generation, and Actions |
| **Document Library & Linking Engine** | Manages external certificates and test reports; enforces many-to-many relationships between files and statutory requirements. | Document Uploads and Linking Requests | Central Document Registry with Expiration Tracking |
| **Continuous Validation Engine** | Evaluates submission state across completeness, data consistency, technical evidence coverage, and certificate validity. | Field Payloads, Document Links, and Rule Sets | Categorized Issue Logs and Readiness Metrics |
| **Assembly & SUGAM Handoff Engine** | Stitches dossier sections into continuous PDFs (under 10MB), powers the In-App Interactive SUGAM Guide, and generates optional offline ZIP archives. | Validated Dossier Structure and Binary Assets | Interactive SUGAM Co-Pilot, Compiled PDFs, and Numbered ZIP Archive |

---

## 3. End-to-End Operational Data Flows

### Flow 1: Submission Initialization and Dynamic Rule Resolution

```mermaid
sequenceDiagram
    autonumber
    actor User as Specialist
    participant UI as Web Workspace
    participant Core as Regulatory Engine
    participant DB as Persistence DB

    User->>UI: Select Pathway & Set Context (e.g. Form MD-14, Class C, Sterile)
    UI->>Core: Initialize Submission Request
    Core->>Core: Evaluate Pathway Constraints & Statutory Rules
    Core->>DB: Persist Submission & Active Requirement Nodes
    DB-->>UI: Return Resolved Workspace Blueprint
    UI-->>User: Render Interactive Checklist & Dossier Trees
```

#### Flow 1 Step-by-Step Technical Execution

| Step | Action | Sender | Receiver | Technical Payload & Operation |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Select Pathway | Specialist | Web Workspace | Chooses Form MD-14, sets device risk class (Class A/B/C/D), sterility, and category (MD/IVD). |
| **2** | Initialize Request | Web Workspace | API Gateway | `POST /api/v1/submissions` with pathway code and regulatory context JSON. |
| **3** | Rule Evaluation | Rules Engine | Rules Engine | Evaluates boolean conditions; activates mandatory requirements and marks non-applicable items. |
| **4** | State Persistence | Rules Engine | Persistence DB | Persists submission master record, active entity states, and Fourth Schedule DMF/PMF nodes. |
| **5** | Return Blueprint | Persistence DB | Web Workspace | Returns compiled hierarchy tree with 8-point guidance definitions and initial validation status. |
| **6** | Display Workspace | Web Workspace | Specialist | Displays interactive tree explorer and active requirement checklist. |

---

### Flow 2: Dual Fulfillment (Upload vs. Generate) and Evidence Linking

```mermaid
sequenceDiagram
    autonumber
    actor User as Specialist
    participant UI as Web Workspace
    participant Core as Regulatory Engine
    participant Store as Storage & DB

    alt Option A: User Uploads Existing File
        User->>UI: Select "Upload Existing" & Choose File
        UI->>Core: Upload Binary & Link to Entity
        Core->>Store: Store File & Record Metadata
    else Option B: User Selects In-App Form Generation
        User->>UI: Select "Generate Document" & Answer Questions
        UI->>Core: Submit Form Questionnaire Answers
        Core->>Core: Render Official Statutory Template to PDF/Word
        Core->>Store: Store Generated Document
    end

    Core->>Core: Run Pre-Submission Validation Check
    Core-->>UI: Push Real-Time Validation Status
    UI-->>User: Update Entity Badge to Satisfied
```

#### Flow 2 Step-by-Step Technical Execution

| Step | Action | Sender | Receiver | Technical Payload & Operation |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Select Fulfillment | Specialist | Web Workspace | Chooses between Option A (Upload Existing) or Option B (Generate via Guided Form). |
| **2A** | Upload Existing | Web Workspace | Regulatory Engine | `POST /api/v1/submissions/{id}/evidence/upload-and-link` with binary file and entity key. |
| **2B** | In-App Generate | Web Workspace | Regulatory Engine | `POST /api/v1/submissions/{id}/entities/{key}/generate` with questionnaire answers; renders template. |
| **3** | Store Payload | Regulatory Engine | Storage & DB | Saves document in secure storage, records metadata (issue date, expiry date, standards). |
| **4** | Validate & Update | Regulatory Engine | Regulatory Engine | Updates requirement state and runs pre-submission validation checks. |
| **5** | Push Status | Regulatory Engine | Web Workspace | Pushes updated readiness metrics and cleared blocker logs. |
| **6** | Update UI | Web Workspace | Specialist | Entity badge transitions to `SATISFIED`; readiness counter updates immediately. |

---

### Flow 3: Dossier Assembly & SUGAM Filing Handoff

```mermaid
sequenceDiagram
    autonumber
    actor User as Specialist
    participant UI as Web Workspace
    participant Assembly as Assembly Engine
    participant SUGAM as CDSCO SUGAM Portal

    User->>UI: Request Dossier Assembly (DMF / PMF)
    UI->>Assembly: Trigger Assembly Pipeline
    Assembly->>Assembly: Prepend Cover Page & TOC, Stitch Chapters, Stamp Page Numbers
    Assembly->>Assembly: Check File Size & Apply Image Optimization (<= 10MB)
    Assembly-->>UI: Deliver Ready-to-Upload Dossier PDF
    UI->>UI: Render Interactive SUGAM Filing Guide
    User->>SUGAM: Upload Verified File to Matching SUGAM Tab Slot
```

---

## 4. Lifecycle State Machines

### Regulatory Entity Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> NOT_APPLICABLE : Applicability rule evaluates FALSE
    [*] --> MISSING : Applicability rule evaluates TRUE
    
    NOT_APPLICABLE --> MISSING : Regulatory context variable changed
    MISSING --> IN_PROGRESS : Initial data saved or file uploaded
    IN_PROGRESS --> SATISFIED : Mandatory inputs complete & valid evidence linked
    
    SATISFIED --> INVALID : Discrepancy detected (e.g. certificate expired)
    INVALID --> SATISFIED : Discrepancy rectified
    
    SATISFIED --> NEEDS_REVIEW : Linked evidence file modified or unlinked
    NEEDS_REVIEW --> SATISFIED : Change confirmed by specialist
```

### Global Submission Dossier Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Record initialized
    DRAFT --> IN_PREPARATION : Regulatory context configured
    
    IN_PREPARATION --> VALIDATION_BLOCKED : Unresolved BLOCKER or ERROR issues exist
    VALIDATION_BLOCKED --> IN_PREPARATION : Remediation completed
    
    IN_PREPARATION --> SUBMISSION_READY : 100% Mandatory Entities Satisfied, Zero Blockers
    SUBMISSION_READY --> GUIDE_ACTIVE : In-App SUGAM Guide launched for live portal filing
    GUIDE_ACTIVE --> SUBMISSION_FILED : Formally lodged on CDSCO SUGAM portal
```

---

## 5. Security Architecture and Data Protection

1. **Access Controls (RBAC):** Role-Based Access Control enforcing least privilege:
   * `Regulatory Specialist`: Read, write, upload, generate documents, and execute validation.
   * `Quality Assurance Reviewer`: Read, audit verification, approval gating.
   * `System Administrator`: Schema management, application definition updates.
2. **Data Security Standards:**
   * Data at rest: Secure AES-256 encryption across database records and object storage.
   * Data in transit: Mandatory TLS 1.3 encryption across all client-server interactions.
   * Document integrity: Secure file storage and validation ensuring document authenticity.
