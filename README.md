# policyAgent

AI Agent system for extracting rules from healthcare policy PDFs and generating SQL implementations.

## Overview

policyAgent is a multi-agent pipeline that:

1. **Parses** PDF policy documents using PaddleOCR (ONNX)
2. **Analyzes** content to identify billing rules
3. **Generates** SQL queries to enforce rules
4. **Validates** rules against industry standards
5. **Produces** HTML reports

## Architecture

```
PDF → Parser → Analyzer → SQLGen → Scorer → Reporter → HTML
       │         │          │         │         │
       ▼         ▼          ▼         ▼         ▼
    PDF+OCR     LLM       SQL+LLM   WebSearch   HTML
```

## Installation

```bash
# Clone repository
git clone https://github.com/roni/policyAgent.git
cd policyAgent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install package
pip install -e ".[dev]"

# Download OCR models
python -c "from policyagent.tools.ocr import download_models; download_models()"
```

## Quick Start

```python
from policyagent.orchestrator.pipeline import Pipeline

# Create pipeline
pipeline = Pipeline()

# Process a policy document
pipeline.run(
    pdf_path="policies/MRP-001.pdf",
    output_path="reports/MRP-001.html"
)
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
│   ├── config/          # Configuration
│   ├── core/            # Base classes
│   ├── tools/           # PDF, OCR, SQL, WebSearch, HTML
│   ├── agents/          # Parser, Analyzer, SQLGen, Scorer, Reporter
│   ├── orchestrator/    # Pipeline coordination
│   └── templates/       # Jinja2 templates
├── tests/               # Test suite
├── docs/                # Documentation
├── models/              # ONNX models
└── examples/            # Usage examples
```

## Rule Classifications

| Type | Description |
|------|-------------|
| `mutual_exclusion` | Services cannot appear together |
| `overutilization` | Units limited over time period |
| `service_not_covered` | Service not in plan |

## Development

```bash
# Run linting
ruff check src/ tests/

# Run formatting
ruff format src/ tests/

# Run type checking
pyright src/

# Run tests
pytest

# Run all checks
ruff check src/ tests/ && pyright src/ && pytest
```

## Sample Output

```html
<h1>Policy: MRP-001 Microsurgery</h1>

<div class="rule">
  <h2>Rule: Microsurgery Add-on Restriction</h2>
  <p><b>Classification:</b> Mutual Exclusion</p>
  <p><b>Confidence:</b> 95%</p>
  <pre>
    SELECT cl.* FROM claim_line cl
    WHERE cl.cpt_code = '69990'
    AND NOT EXISTS (
      SELECT 1 FROM claim_line cl2
      WHERE cl2.claim_id = cl.claim_id
      AND cl2.cpt_code IN ('61304', '61305', ...)
    )
  </pre>
</div>
```

## License

MIT
