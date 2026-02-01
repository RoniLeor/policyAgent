"""Database schema initialization for rule repository."""

from __future__ import annotations


INIT_SCHEMA = """
-- Main rules table
CREATE TABLE IF NOT EXISTS rules (
    id TEXT PRIMARY KEY,
    vendor TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    classification TEXT NOT NULL,
    source_text TEXT,
    sql_query TEXT,
    sql_formatted TEXT,
    confidence REAL DEFAULT 50.0,
    validation_notes TEXT,
    sources TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CPT codes junction table
CREATE TABLE IF NOT EXISTS rule_cpt_codes (
    rule_id TEXT NOT NULL,
    cpt_code TEXT NOT NULL,
    PRIMARY KEY (rule_id, cpt_code),
    FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE
);

-- ICD-10 codes junction table
CREATE TABLE IF NOT EXISTS rule_icd10_codes (
    rule_id TEXT NOT NULL,
    icd10_code TEXT NOT NULL,
    PRIMARY KEY (rule_id, icd10_code),
    FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE
);

-- Modifiers junction table
CREATE TABLE IF NOT EXISTS rule_modifiers (
    rule_id TEXT NOT NULL,
    modifier TEXT NOT NULL,
    PRIMARY KEY (rule_id, modifier),
    FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_rules_vendor ON rules(vendor);
CREATE INDEX IF NOT EXISTS idx_rules_classification ON rules(classification);
CREATE INDEX IF NOT EXISTS idx_rules_confidence ON rules(confidence);
CREATE INDEX IF NOT EXISTS idx_cpt_codes ON rule_cpt_codes(cpt_code);
CREATE INDEX IF NOT EXISTS idx_icd10_codes ON rule_icd10_codes(icd10_code);
CREATE INDEX IF NOT EXISTS idx_modifiers ON rule_modifiers(modifier);

-- Full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS rules_fts USING fts5(
    id, name, description, source_text,
    content='rules', content_rowid='rowid'
);

-- FTS triggers
CREATE TRIGGER IF NOT EXISTS rules_ai AFTER INSERT ON rules BEGIN
    INSERT INTO rules_fts(rowid, id, name, description, source_text)
    VALUES (NEW.rowid, NEW.id, NEW.name, NEW.description, NEW.source_text);
END;

CREATE TRIGGER IF NOT EXISTS rules_ad AFTER DELETE ON rules BEGIN
    INSERT INTO rules_fts(rules_fts, rowid, id, name, description, source_text)
    VALUES ('delete', OLD.rowid, OLD.id, OLD.name, OLD.description, OLD.source_text);
END;

CREATE TRIGGER IF NOT EXISTS rules_au AFTER UPDATE ON rules BEGIN
    INSERT INTO rules_fts(rules_fts, rowid, id, name, description, source_text)
    VALUES ('delete', OLD.rowid, OLD.id, OLD.name, OLD.description, OLD.source_text);
    INSERT INTO rules_fts(rowid, id, name, description, source_text)
    VALUES (NEW.rowid, NEW.id, NEW.name, NEW.description, NEW.source_text);
END;
"""
