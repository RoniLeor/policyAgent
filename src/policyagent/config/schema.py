"""Claims database schema definition.

This schema represents the structure of healthcare claims data
that SQL queries will be generated against.
"""

from __future__ import annotations


CLAIMS_SCHEMA = """
-- Patient information
CREATE TABLE patient (
    patient_id VARCHAR(50) PRIMARY KEY,
    dob DATE NOT NULL,
    gender CHAR(1) CHECK (gender IN ('M', 'F', 'U'))
);

-- Provider information
CREATE TABLE provider (
    npi VARCHAR(10) PRIMARY KEY,
    tin VARCHAR(20) NOT NULL
);

-- Claim header
CREATE TABLE claim (
    claim_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL REFERENCES patient(patient_id),
    provider_npi VARCHAR(10) NOT NULL REFERENCES provider(npi),
    claim_date DATE NOT NULL
);

-- Claim line details
CREATE TABLE claim_line (
    line_id VARCHAR(50) PRIMARY KEY,
    claim_id VARCHAR(50) NOT NULL REFERENCES claim(claim_id),
    dos DATE NOT NULL,                    -- Date of Service
    pos VARCHAR(10),                      -- Place of Service code
    icd10 VARCHAR(10)[],                  -- Diagnosis codes (array)
    cpt_code VARCHAR(10) NOT NULL,        -- Procedure/service code
    units INTEGER DEFAULT 1,
    amount DECIMAL(10, 2),
    modifiers VARCHAR(2)[]                -- Modifier codes (array)
);
"""
