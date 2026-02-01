# policyAgent - Product Requirements Document

## Overview

**Product Name:** policyAgent
**Version:** 0.1.0
**Date:** 2026-02-01

### Purpose

Build an AI Agent system that extracts reimbursement rules from healthcare policy PDF documents and generates SQL implementations for claim validation.

### Problem Statement

Healthcare insurance companies publish reimbursement policies as PDF documents. These policies contain rules that determine when claims should be paid, denied, or flagged for review. Currently, translating these policies into executable business logic requires manual effort by domain experts.

### Solution

An automated multi-agent pipeline that:
1. Parses PDF policy documents using OCR
2. Identifies and classifies billing rules
3. Generates SQL queries to enforce rules
4. Validates rules against industry standards
5. Produces human-readable HTML reports

---

## Input/Output Specification

### Input

| Type | Format | Example |
|------|--------|---------|
| Policy Document | PDF | `MRP-001.pdf`, `RP-039.pdf` |

### Output

| Type | Format | Contents |
|------|--------|----------|
| HTML Report | `.html` | Policy name, rules list with SQL |

### Output Structure (per task requirements)

```
Policy Name
└── Rules List
    └── For each rule:
        ├── Rule Name
        ├── Description
        ├── SQL Query (claims schema)
        ├── Logic Confidence (0-100%)
        ├── Classification Type
        └── Source Quote (bonus)
```

---

## Rule Classifications

| Type | Code | Description | Example |
|------|------|-------------|---------|
| Mutual Exclusion | `mutual_exclusion` | Services cannot appear together on same claim | Code 69990 requires primary procedure |
| Overutilization | `overutilization` | Units/frequency limited over time period | Max 1 chest x-ray per day |
| Service Not Covered | `service_not_covered` | Service excluded from plan | Robotic surgery S290 denied |

---

## Claims Database Schema

### Tables

```sql
-- Patient information
CREATE TABLE patient (
    patient_id VARCHAR PRIMARY KEY,
    dob DATE,
    gender CHAR(1)  -- M/F
);

-- Provider information
CREATE TABLE provider (
    npi VARCHAR PRIMARY KEY,
    tin VARCHAR
);

-- Claim header
CREATE TABLE claim (
    claim_id VARCHAR PRIMARY KEY,
    patient_id VARCHAR REFERENCES patient(patient_id),
    provider_npi VARCHAR REFERENCES provider(npi)
);

-- Claim line details
CREATE TABLE claim_line (
    line_id VARCHAR PRIMARY KEY,
    claim_id VARCHAR REFERENCES claim(claim_id),
    dos DATE,                    -- Date of Service
    pos VARCHAR,                 -- Place of Service
    icd10 VARCHAR[],            -- Diagnosis codes
    cpt_code VARCHAR,           -- Procedure code
    units INTEGER,
    amount DECIMAL,
    modifiers VARCHAR[]         -- e.g., ['25', '50']
);
```

---

## Functional Requirements

### FR-1: Document Parsing
- **FR-1.1:** Load PDF files from local filesystem
- **FR-1.2:** Extract text using PaddleOCR ONNX
- **FR-1.3:** Identify document structure (sections, tables)
- **FR-1.4:** Extract CPT code lists from tables
- **FR-1.5:** Preserve source location for quotes

### FR-2: Policy Analysis
- **FR-2.1:** Identify rule patterns (IF/THEN logic)
- **FR-2.2:** Classify rules into three categories
- **FR-2.3:** Extract entities (CPT codes, modifiers, conditions)
- **FR-2.4:** Generate rule descriptions

### FR-3: SQL Generation
- **FR-3.1:** Map rule entities to claims schema
- **FR-3.2:** Generate syntactically valid SQL
- **FR-3.3:** Validate SQL syntax before output
- **FR-3.4:** Self-correct invalid queries (max 3 retries)

### FR-4: Confidence Scoring
- **FR-4.1:** Search industry sources for similar rules
- **FR-4.2:** Calculate confidence based on source matches
- **FR-4.3:** Document reasoning for score

### FR-5: Report Generation
- **FR-5.1:** Generate HTML report per policy
- **FR-5.2:** Include all rule details
- **FR-5.3:** Display source quotes when available
- **FR-5.4:** Format SQL with syntax highlighting

---

## Non-Functional Requirements

### NFR-1: Performance
- Process single policy PDF in < 60 seconds
- Support PDFs up to 50 pages

### NFR-2: Accuracy
- SQL syntax validation: 100%
- Rule extraction recall: > 80%

### NFR-3: Code Quality
- Type hints on all functions
- Ruff linting with zero errors
- Pylance strict mode
- Test coverage > 80%

### NFR-4: Deployment
- Run on CPU (no GPU required)
- Python 3.11+
- Cross-platform (Linux, macOS, Windows)

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| OCR | PaddleOCR ONNX (via RapidOCR) |
| PDF | PyMuPDF |
| LLM | OpenAI / Anthropic / Local |
| SQL Validation | sqlglot |
| Web Search | DuckDuckGo |
| Templates | Jinja2 |
| Types | Pydantic v2 |
| Linting | Ruff |
| Type Checking | Pylance/Pyright |

---

## Success Criteria

1. Successfully parse MRP-001.pdf and RP-039.pdf samples
2. Extract at least 1 rule per document
3. Generate valid SQL for each rule
4. Produce readable HTML report
5. All tests passing
6. Zero linting errors

---

## Out of Scope (v0.1)

- Web UI
- Database storage
- Multiple vendor support
- Real-time processing
- API endpoints
- Authentication
