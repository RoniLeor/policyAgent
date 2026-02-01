# policyAgent - Task Breakdown

## Task Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TASK DEPENDENCY GRAPH                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [T1] Core Layer ──────────────────────────────────────┐            │
│         │                                               │            │
│         ▼                                               │            │
│  [T2] Tools Layer ─────────────────────────────────────┤            │
│         │                                               │            │
│         ├──► [T2.1] PDF Tool                           │            │
│         ├──► [T2.2] OCR Tool                           │            │
│         ├──► [T2.3] SQL Tool                           │            │
│         ├──► [T2.4] WebSearch Tool                     │            │
│         └──► [T2.5] HTML Tool                          │            │
│                                                         │            │
│  [T3] Agents Layer ◄───────────────────────────────────┘            │
│         │                                                            │
│         ├──► [T3.1] Parser Agent                                    │
│         ├──► [T3.2] Analyzer Agent                                  │
│         ├──► [T3.3] SQLGen Agent                                    │
│         ├──► [T3.4] Scorer Agent                                    │
│         └──► [T3.5] Reporter Agent                                  │
│                                                                      │
│  [T4] Orchestrator ◄────────────────────────────────────────────────│
│                                                                      │
│  [T5] Testing ◄─────────────────────────────────────────────────────│
│                                                                      │
│  [T6] Documentation ◄───────────────────────────────────────────────│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation

### T1: Core Layer

**Priority:** P0 (Critical)
**Depends on:** None
**Estimated Files:** 6

#### T1.1: Base Types
- **File:** `src/policyagent/core/types.py`
- **Description:** Shared Pydantic models
- **Deliverables:**
  - `RuleClassification` enum
  - `ExtractedRule` model
  - `SQLResult` model
  - `ConfidenceScore` model
  - `PolicyDocument` model
  - `ReportData` model

#### T1.2: Message Types
- **File:** `src/policyagent/core/message.py`
- **Description:** LLM message structures
- **Deliverables:**
  - `Message` class
  - `ToolCall` class
  - `MessageRole` enum

#### T1.3: Response Types
- **File:** `src/policyagent/core/response.py`
- **Description:** Standardized responses
- **Deliverables:**
  - `AgentResponse` generic class
  - `ToolResponse` class

#### T1.4: Tool Base
- **File:** `src/policyagent/core/tool.py`
- **Description:** Abstract tool class
- **Deliverables:**
  - `Tool` ABC
  - `@tool` decorator

#### T1.5: Agent Base
- **File:** `src/policyagent/core/agent.py`
- **Description:** Abstract agent class
- **Deliverables:**
  - `Agent` ABC
  - `run()` method signature
  - Tool integration

#### T1.6: LLM Client
- **File:** `src/policyagent/core/llm.py`
- **Description:** LLM API wrapper
- **Deliverables:**
  - `LLMClient` class
  - Support OpenAI/Anthropic
  - Message formatting

---

## Phase 2: Tools

### T2: Tools Layer

**Priority:** P0 (Critical)
**Depends on:** T1
**Estimated Files:** 5

#### T2.1: PDF Tool
- **File:** `src/policyagent/tools/pdf.py`
- **Description:** PDF loading and page extraction
- **Dependencies:** `pymupdf`
- **Deliverables:**
  - `PDFTool` class
  - `load(path)` method
  - `iter_pages(path)` iterator
  - `to_images(path)` method
- **Input:** File path
- **Output:** List of page images

#### T2.2: OCR Tool
- **File:** `src/policyagent/tools/ocr.py`
- **Description:** PaddleOCR ONNX integration
- **Dependencies:** `rapidocr`, `onnxruntime`
- **Deliverables:**
  - `OCRTool` class
  - `__call__(image)` method
  - Model loading
  - Result parsing
- **Input:** Image (bytes/array)
- **Output:** Text + bounding boxes

#### T2.3: SQL Tool
- **File:** `src/policyagent/tools/sql.py`
- **Description:** SQL validation
- **Dependencies:** `sqlglot`
- **Deliverables:**
  - `SQLTool` class
  - `validate(query)` method
  - `format(query)` method
  - Error extraction
- **Input:** SQL query string
- **Output:** Validation result

#### T2.4: WebSearch Tool
- **File:** `src/policyagent/tools/websearch.py`
- **Description:** Web search for industry sources
- **Dependencies:** `duckduckgo-search`
- **Deliverables:**
  - `WebSearchTool` class
  - `search(query)` method
  - Result parsing
- **Input:** Search query
- **Output:** List of results with URLs

#### T2.5: HTML Tool
- **File:** `src/policyagent/tools/html.py`
- **Description:** HTML report generation
- **Dependencies:** `jinja2`
- **Deliverables:**
  - `HTMLTool` class
  - `render(template, data)` method
  - Template loading
- **Input:** Template name + data
- **Output:** HTML string

---

## Phase 3: Agents

### T3: Agents Layer

**Priority:** P0 (Critical)
**Depends on:** T1, T2
**Estimated Files:** 5

#### T3.1: Parser Agent
- **File:** `src/policyagent/agents/parser/agent.py`
- **Description:** Extract content from PDF
- **Uses Tools:** PDF, OCR
- **Deliverables:**
  - `ParserAgent` class
  - PDF → pages → OCR → text
  - Structure identification
  - Table extraction
- **Input:** PDF file path
- **Output:** `PolicyDocument`

#### T3.2: Analyzer Agent
- **File:** `src/policyagent/agents/analyzer/agent.py`
- **Description:** Identify and classify rules
- **Uses Tools:** LLM only
- **Deliverables:**
  - `AnalyzerAgent` class
  - Rule identification prompts
  - Classification logic
  - Entity extraction
- **Input:** `PolicyDocument`
- **Output:** `List[ExtractedRule]`

#### T3.3: SQLGen Agent
- **File:** `src/policyagent/agents/sqlgen/agent.py`
- **Description:** Generate SQL with self-correction
- **Uses Tools:** SQL, LLM
- **Deliverables:**
  - `SQLGenAgent` class
  - SQL generation prompts
  - Self-correction loop
  - Schema mapping
- **Input:** `List[ExtractedRule]`
- **Output:** `List[SQLResult]`

#### T3.4: Scorer Agent
- **File:** `src/policyagent/agents/scorer/agent.py`
- **Description:** Calculate confidence scores
- **Uses Tools:** WebSearch
- **Deliverables:**
  - `ScorerAgent` class
  - Search query generation
  - Score calculation
  - Source aggregation
- **Input:** `List[SQLResult]`
- **Output:** `List[ConfidenceScore]`

#### T3.5: Reporter Agent
- **File:** `src/policyagent/agents/reporter/agent.py`
- **Description:** Generate HTML report
- **Uses Tools:** HTML
- **Deliverables:**
  - `ReporterAgent` class
  - Data aggregation
  - Template rendering
- **Input:** All pipeline data
- **Output:** HTML string

---

## Phase 4: Integration

### T4: Orchestrator

**Priority:** P0 (Critical)
**Depends on:** T3
**Estimated Files:** 1

#### T4.1: Pipeline
- **File:** `src/policyagent/orchestrator/pipeline.py`
- **Description:** Coordinate agent execution
- **Deliverables:**
  - `Pipeline` class
  - Sequential execution
  - Error handling
  - Progress logging
- **Input:** PDF path, output path
- **Output:** HTML file

---

## Phase 5: Quality

### T5: Testing

**Priority:** P1 (High)
**Depends on:** T4
**Estimated Files:** 7

#### T5.1: Core Tests
- **File:** `tests/test_core.py`
- **Coverage:** types, message, response, tool, agent

#### T5.2: Tool Tests
- **Files:** `tests/test_tools/test_*.py`
- **Coverage:** Each tool individually

#### T5.3: Agent Tests
- **Files:** `tests/test_agents/test_*.py`
- **Coverage:** Each agent individually

#### T5.4: Integration Tests
- **File:** `tests/test_integration.py`
- **Coverage:** Full pipeline with sample PDFs

---

### T6: Documentation

**Priority:** P2 (Medium)
**Depends on:** T4
**Estimated Files:** 3

#### T6.1: README
- **File:** `README.md`
- **Contents:** Quick start, installation, usage

#### T6.2: API Documentation
- **File:** `docs/API.md`
- **Contents:** Class/method reference

#### T6.3: Examples
- **Files:** `examples/*.py`
- **Contents:** Usage examples

---

## Task Checklist

### Phase 1: Foundation
- [ ] T1.1: Base Types
- [ ] T1.2: Message Types
- [ ] T1.3: Response Types
- [ ] T1.4: Tool Base
- [ ] T1.5: Agent Base
- [ ] T1.6: LLM Client

### Phase 2: Tools
- [ ] T2.1: PDF Tool
- [ ] T2.2: OCR Tool
- [ ] T2.3: SQL Tool
- [ ] T2.4: WebSearch Tool
- [ ] T2.5: HTML Tool

### Phase 3: Agents
- [ ] T3.1: Parser Agent
- [ ] T3.2: Analyzer Agent
- [ ] T3.3: SQLGen Agent
- [ ] T3.4: Scorer Agent
- [ ] T3.5: Reporter Agent

### Phase 4: Integration
- [ ] T4.1: Pipeline

### Phase 5: Quality
- [ ] T5.1: Core Tests
- [ ] T5.2: Tool Tests
- [ ] T5.3: Agent Tests
- [ ] T5.4: Integration Tests

### Phase 6: Documentation
- [ ] T6.1: README
- [ ] T6.2: API Documentation
- [ ] T6.3: Examples

---

## Execution Order

```
Week 1: T1 (Core) → T2.1 (PDF) → T2.2 (OCR)
Week 2: T2.3 (SQL) → T2.4 (WebSearch) → T2.5 (HTML)
Week 3: T3.1 (Parser) → T3.2 (Analyzer) → T3.3 (SQLGen)
Week 4: T3.4 (Scorer) → T3.5 (Reporter) → T4.1 (Pipeline)
Week 5: T5 (Testing) → T6 (Documentation)
```
