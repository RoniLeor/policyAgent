# Healthcare Billing Reference Guide

A comprehensive guide to understanding US healthcare billing concepts used in this project.

---

## Table of Contents

1. [Claims Processing Flow](#claims-processing-flow)
2. [CPT Codes](#cpt-codes)
3. [Modifiers](#modifiers)
4. [Global Surgical Periods](#global-surgical-periods)
5. [Overbilling Detection](#overbilling-detection)
6. [Database Schema](#database-schema)
7. [Rule Classifications](#rule-classifications)

---

## Claims Processing Flow

Healthcare billing follows this workflow:

```
Patient Visit
     │
     ▼
┌─────────────────┐
│ 1. Eligibility  │  Verify insurance coverage
│    Check        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Clinical     │  Document the visit
│    Documentation│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Medical      │  Assign CPT, ICD-10, HCPCS codes
│    Coding       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Claim        │  Create 837P/837I electronic claim
│    Creation     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. Clearinghouse│  Validate and route to payer
│    Processing   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. Payer        │  Insurance reviews against rules
│    Adjudication │  ◄── THIS IS WHERE OUR RULES APPLY
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 7. Payment/     │  Payer pays, patient billed for remainder
│    Billing      │
└─────────────────┘
```

---

## CPT Codes

### What Are CPT Codes?
**Current Procedural Terminology (CPT)** codes are 5-digit codes that identify medical procedures and services for billing.

### Code Categories

| Category | Range | Description |
|----------|-------|-------------|
| **E/M** | 99201-99499 | Evaluation & Management (office visits, hospital care) |
| **Anesthesia** | 00100-01999 | Anesthesia services |
| **Surgery** | 10004-69990 | Surgical procedures |
| **Radiology** | 70010-79999 | X-rays, CT, MRI, etc. |
| **Pathology** | 80047-89398 | Lab tests |
| **Medicine** | 90281-99607 | Other medical services |

### Common E/M Code Families

```
Office/Outpatient (99201-99215)
├── 99201-99205: New Patient
│   ├── 99201: Straightforward
│   ├── 99202: Low complexity
│   ├── 99203: Moderate complexity
│   ├── 99204: Moderate-high complexity
│   └── 99205: High complexity
│
└── 99211-99215: Established Patient
    ├── 99211: Minimal (nurse visit)
    ├── 99212: Straightforward
    ├── 99213: Low complexity
    ├── 99214: Moderate complexity
    └── 99215: High complexity

Hospital Inpatient (99221-99223)
├── 99221: Low complexity
├── 99222: Moderate complexity
└── 99223: High complexity

Emergency Department (99281-99285)
├── 99281: Minor problem
├── 99282: Low urgency
├── 99283: Moderate severity
├── 99284: High severity
└── 99285: Immediate threat to life

Preventive Medicine (99381-99397)
├── 99381-99387: New patient by age
└── 99391-99397: Established patient by age
```

### Obstetrical Codes

```
Global Packages (include prenatal + delivery + postpartum):
├── 59400: Vaginal delivery
├── 59510: Cesarean delivery
├── 59610: VBAC
└── 59618: Cesarean after VBAC attempt

Delivery Only:
├── 59409: Vaginal delivery only
├── 59514: Cesarean delivery only
├── 59612: VBAC delivery only
└── 59620: Cesarean after VBAC, delivery only

Antepartum Only:
├── 59425: 4-6 visits
└── 59426: 7+ visits

Postpartum Only:
└── 59430: Postpartum care only
```

---

## Modifiers

Modifiers are 2-character codes appended to CPT codes to provide additional information.

### Critical Modifiers for Billing Rules

| Modifier | Name | When to Use | Example |
|----------|------|-------------|---------|
| **25** | Significant, Separately Identifiable E/M | E/M service distinct from same-day procedure | 99213-25 with 11721 |
| **50** | Bilateral Procedure | Procedure on both sides of body | 29806-50 |
| **24** | Unrelated E/M During Global | E/M in post-op period for unrelated condition | 99213-24 |
| **78** | Unplanned Return to OR | Return to operating room during global period | |
| **79** | Unrelated Procedure During Global | Different procedure during post-op period | |
| **59** | Distinct Procedural Service | Service is independent from other services | |
| **76** | Repeat Procedure, Same Physician | Same procedure repeated same day | |
| **77** | Repeat Procedure, Different Physician | Same procedure by different physician | |

### Modifier Usage Examples

**Modifier 50 (Bilateral):**
```
WRONG: Two lines
  Line 1: 29806 (right shoulder)
  Line 2: 29806 (left shoulder)
  → Pays 200%

CORRECT: One line with modifier
  Line 1: 29806-50
  → Pays 150%
```

**Modifier 25 (Separate E/M):**
```
Scenario: Patient comes for nail trimming, also has new rash

WRONG:
  Line 1: 11721 (nail trimming)
  Line 2: 99213 (office visit)
  → E/M may be denied

CORRECT:
  Line 1: 11721 (nail trimming)
  Line 2: 99213-25 (separate E/M with modifier)
  → Both may be paid
```

**Modifier 24 (Unrelated E/M in Global):**
```
Scenario: Patient had knee surgery (90-day global).
          30 days later, comes in for ear infection.

CORRECT:
  Line 1: 99213-24 (with ear infection diagnosis)
  → Pays because unrelated to surgery
```

---

## Global Surgical Periods

After surgery, the surgeon's fee includes follow-up care for a defined period.

### Global Period Types

| Period | Description | Examples |
|--------|-------------|----------|
| **0-day** | No post-op included | Minor procedures, biopsies |
| **10-day** | 10 days follow-up included | Minor surgeries |
| **90-day** | 90 days follow-up included | Major surgeries |

### What's Included in Global Period

```
Pre-operative (1 day before):
├── E/M visit the day before surgery
└── Decision for surgery

Intra-operative:
├── The surgery itself
├── Local/regional anesthesia by surgeon
└── Immediate post-op care

Post-operative:
├── Follow-up visits during global period
├── Post-op pain management
├── Supplies (except take-home items)
└── Complications requiring return to OR (same surgeon)
```

### What's NOT Included (Can Bill Separately)

```
With Modifier 24 (Unrelated E/M):
└── E/M for condition unrelated to surgery

With Modifier 78 (Return to OR):
└── Unplanned return to operating room for complication

With Modifier 79 (Unrelated Procedure):
└── Different, unrelated procedure

Without Modifier:
├── Services by different specialty
├── Diagnostic tests (labs, imaging)
├── Durable medical equipment
└── Immunizations
```

---

## Overbilling Detection

### Common Overbilling Patterns

| Pattern | Description | Detection |
|---------|-------------|-----------|
| **Unbundling** | Billing separate codes for what should be one code | Look for code pairs that should be bundled |
| **Upcoding** | Using higher-paying code than appropriate | Compare E/M level to documentation |
| **Duplicate Billing** | Same service billed twice | Same CPT, same DOS, same provider |
| **Bilateral Abuse** | Two lines instead of modifier 50 | Count bilateral-eligible codes per claim |
| **Global Period Abuse** | E/M during global without valid modifier | Track surgery dates + follow-up E/M |

### Detection SQL Patterns

**Unbundling Detection:**
```sql
-- NCCI edit pairs
SELECT * FROM claim_lines cl1
JOIN claim_lines cl2 ON cl1.claim_id = cl2.claim_id
JOIN ncci_edits ncci ON cl1.cpt_code = ncci.column_1
                     AND cl2.cpt_code = ncci.column_2
WHERE cl1.modifier1 NOT IN ('59', 'XE', 'XP', 'XS', 'XU');
```

**Duplicate Detection:**
```sql
SELECT claim_id, cpt_code, date_of_service, COUNT(*)
FROM claim_lines
GROUP BY claim_id, cpt_code, date_of_service
HAVING COUNT(*) > 1;
```

---

## Database Schema

The schema used for rule SQL implementations:

```sql
-- Patient demographics
CREATE TABLE patients (
    patient_id    VARCHAR(50) PRIMARY KEY,
    dob           DATE,
    gender        CHAR(1)  -- 'M', 'F'
);

-- Claim header
CREATE TABLE claims (
    claim_id        VARCHAR(50) PRIMARY KEY,
    claim_number    VARCHAR(50),
    patient_id      VARCHAR(50) REFERENCES patients(patient_id),
    provider_npi    VARCHAR(10),
    provider_tin    VARCHAR(15),
    submission_date DATE
);

-- Claim line items
CREATE TABLE claim_lines (
    line_id           VARCHAR(50) PRIMARY KEY,
    claim_id          VARCHAR(50) REFERENCES claims(claim_id),
    line_number       INT,
    cpt_code          VARCHAR(10),
    modifier1         VARCHAR(5),
    modifier2         VARCHAR(5),
    modifier3         VARCHAR(5),
    modifier4         VARCHAR(5),
    icd_code          VARCHAR(10),
    place_of_service  VARCHAR(2),
    date_of_service   DATE,
    units             INT,
    amount_billed     DECIMAL(10,2)
);
```

### Field Descriptions

| Field | Description |
|-------|-------------|
| `patient_id` | Unique patient/member identifier |
| `provider_npi` | National Provider Identifier (10 digits) |
| `provider_tin` | Tax Identification Number |
| `cpt_code` | Procedure code (CPT/HCPCS) |
| `modifier1-4` | Up to 4 modifiers per line |
| `icd_code` | Diagnosis code (ICD-10) |
| `place_of_service` | Location code (see POS codes) |
| `date_of_service` | When service was rendered |
| `units` | Number of units billed |

---

## Rule Classifications

The agent classifies rules into three types:

### 1. Mutual Exclusion
Services that cannot appear together on the same claim.

**Examples:**
- Bilateral procedure on two lines (should use modifier 50)
- E/M + preventive same day without modifier 25
- Global OB code + separate prenatal E/M

### 2. Overutilization
Limits on frequency or quantity of services.

**Examples:**
- X-ray views (only highest view count reimbursed)
- Maximum units per day
- Frequency limits (once per year, etc.)

### 3. Service Not Covered
Services that are not allowed under certain conditions.

**Examples:**
- Gender-specific services (OB for male patient)
- Place of service mismatch (ED code without POS 23)
- Procedure not covered by plan

---

## Quick Reference Cards

### Place of Service (POS) Codes
| Code | Location |
|------|----------|
| 11 | Office |
| 12 | Home |
| 21 | Inpatient Hospital |
| 22 | Outpatient Hospital |
| 23 | Emergency Room - Hospital |
| 24 | Ambulatory Surgical Center |
| 31 | Skilled Nursing Facility |
| 32 | Nursing Facility |

### ICD-10 Injury Codes
Injury diagnoses that may justify separate E/M during global:
- **S00-S99**: Injuries by body region
- **T07-T88**: Burns, poisoning, complications

### Common Bilateral-Eligible Procedures
| CPT | Description |
|-----|-------------|
| 27447 | Total knee replacement |
| 29806 | Shoulder arthroscopy |
| 69436 | Ear tube placement |
| 64721 | Carpal tunnel release |
