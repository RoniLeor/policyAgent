# policyAgent

AI Agent system for extracting billing rules from healthcare policy PDFs and generating SQL implementations.

## Overview

policyAgent is a multi-agent pipeline that:

1. **Parses** PDF policy documents using PaddleOCR (ONNX)
2. **Analyzes** content to identify billing rules
3. **Generates** SQL queries to enforce rules
4. **Executes** queries against claims database to find violations
5. **Validates** rules against industry standards via web search
6. **Produces** HTML reports with violations and confidence scores

## Architecture

```
PDF → Parser → Analyzer → SQLGen → Scorer → QueryExecutor → Reporter → HTML
       │         │          │         │           │             │
       ▼         ▼          ▼         ▼           ▼             ▼
    PDF+OCR     LLM       SQL+LLM   WebSearch   ClaimsDB       HTML
```

## Installation

```bash
# Clone repository
git clone https://github.com/RoniLeor/policyAgent.git
cd policyAgent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install package with dev dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks (required for contributors)
pre-commit install
```

## Quick Start

### CLI Usage

```bash
# Initialize claims database with sample data
policyagent init-claims --db claims.db

# Process a policy PDF (mock mode - no API keys needed)
policyagent process policy.pdf report.html --mock

# Process with claims database to find violations
policyagent process policy.pdf report.html --claims-db claims.db --mock

# Search indexed rules
policyagent search --cpt 69990
policyagent search --type mutual_exclusion
policyagent search --text "microsurgery"

# View database statistics
policyagent stats
```

### Python API

```python
import asyncio
from policyagent.orchestrator.pipeline import Pipeline
from policyagent.storage.claims_db import ClaimsDatabase

# Setup claims database
claims_db = ClaimsDatabase("claims.db")
claims_db.load_sample_data()

# Create pipeline with claims database
pipeline = Pipeline(claims_db=claims_db)

# Process a policy document
report = asyncio.run(pipeline.run(
    pdf_path="policy.pdf",
    output_path="report.html"
))

print(f"Found {report.total_violations} violations")
```

## Configuration

Create a `.env` file:

```env
# LLM Provider (openai or anthropic)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Or use Anthropic
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...
# ANTHROPIC_MODEL=claude-sonnet-4-20250514

# OCR (optional, uses defaults)
OCR_USE_GPU=false
PDF_DPI=300
```

## Project Structure

```
policyAgent/
├── src/policyagent/
│   ├── config/          # Configuration and settings
│   ├── core/            # Base classes, models, LLM clients
│   ├── tools/           # PDF, OCR, SQL, WebSearch, HTML tools
│   ├── agents/          # Parser, Analyzer, SQLGen, Scorer, Reporter
│   ├── orchestrator/    # Pipeline coordination
│   ├── storage/         # SQLite repositories (rules, claims)
│   └── templates/       # Jinja2 HTML templates
├── tests/               # Test suite
└── models/              # ONNX models (auto-downloaded)
```

## Rule Classifications

| Type | Description | Example |
|------|-------------|---------|
| `mutual_exclusion` | Services cannot appear together | CPT 69990 requires specific primary procedures |
| `overutilization` | Units limited over time period | Max 4 units per day for CPT 97110 |
| `service_not_covered` | Service not covered in plan | Cosmetic procedures excluded |

## Claims Database Schema

```sql
patient(patient_id, dob, gender)
provider(npi, tin)
claim(claim_id, patient_id, provider_npi)
claim_line(claim_id, dos, pos, icd10, cpt_code, units, amount, modifiers)
```

## Development

### Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Pre-commit Hooks

The project uses pre-commit hooks for code quality:

- **Ruff** - Linting and formatting
- **detect-secrets** - Prevent committing secrets/API keys
- **Bandit** - Security vulnerability scanning
- **Pyright** - Type checking

```bash
# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run detect-secrets --all-files
```

### Code Quality Commands

```bash
# Linting
ruff check src/ tests/
ruff check src/ tests/ --fix  # Auto-fix

# Formatting
ruff format src/ tests/

# Type checking
pyright src/

# Security scan
bandit -r src/

# Run tests
pytest

# Run tests with coverage
pytest --cov=policyagent --cov-report=html

# Run all checks (recommended before commit)
ruff check src/ tests/ && ruff format --check src/ tests/ && pyright src/ && pytest
```

### Git Workflow

```bash
# Before committing - hooks run automatically
git add .
git commit -m "feat: add new feature"

# If hooks fail, fix issues and retry
ruff check src/ --fix
git add .
git commit -m "feat: add new feature"

# Push changes
git push origin main
```

## HTML Report Features

The generated HTML report includes:

- **Summary stats**: Total rules, violations found, pages processed
- **Rule details**: Name, description, classification, CPT codes
- **SQL implementation**: Formatted query with syntax highlighting
- **Confidence score**: Visual bar with percentage
- **Violations table**: Actual claims that violate each rule
- **Validation sources**: Links to CMS guidelines and references

## Testing

```bash
# Run with mock LLM (no API keys needed)
policyagent process tests/fixtures/test_policy.pdf report.html --mock

# Run with claims database
policyagent init-claims
policyagent process tests/fixtures/test_policy.pdf report.html --mock --claims-db claims.db
```

## License

MIT
