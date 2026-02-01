# policyAgent - System Design Document

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           policyAgent                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      ORCHESTRATOR                                │    │
│  │                    (Pipeline Controller)                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        AGENTS LAYER                              │    │
│  │                                                                   │    │
│  │  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌────────┐  ┌─────────┐ │    │
│  │  │ Parser  │─►│ Analyzer │─►│ SQLGen │─►│ Scorer │─►│Reporter │ │    │
│  │  └────┬────┘  └────┬─────┘  └───┬────┘  └───┬────┘  └────┬────┘ │    │
│  │       │            │            │           │            │       │    │
│  └───────┼────────────┼────────────┼───────────┼────────────┼───────┘    │
│          │            │            │           │            │            │
│  ┌───────┼────────────┼────────────┼───────────┼────────────┼───────┐    │
│  │       ▼            ▼            ▼           ▼            ▼       │    │
│  │                        TOOLS LAYER                               │    │
│  │                                                                   │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────────┐  ┌──────┐ │    │
│  │  │   PDF   │  │   OCR   │  │   SQL   │  │ WebSearch │  │ HTML │ │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └───────────┘  └──────┘ │    │
│  │                                                                   │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                        CORE LAYER                                  │  │
│  │                                                                     │  │
│  │  ┌────────┐  ┌────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │  │
│  │  │ Agent  │  │  Tool  │  │ Function │  │ Message  │  │ Response │ │  │
│  │  │ (base) │  │ (base) │  │ (wrapper)│  │  (types) │  │  (types) │ │  │
│  │  └────────┘  └────────┘  └──────────┘  └──────────┘  └──────────┘ │  │
│  │                                                                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Layer Descriptions

### Core Layer

Base classes and shared types that all components inherit from.

| Component | Purpose |
|-----------|---------|
| `Agent` | Abstract base for all agents |
| `Tool` | Abstract base for all tools |
| `Function` | Wrapper for callable tools |
| `Message` | LLM message structure |
| `Response` | Standardized agent response |

### Tools Layer

Concrete implementations of external capabilities.

| Tool | Input | Output | Dependencies |
|------|-------|--------|--------------|
| `PDF` | File path | Pages (images) | PyMuPDF |
| `OCR` | Image | Text + boxes | RapidOCR/ONNX |
| `SQL` | Query string | Validation result | sqlglot |
| `WebSearch` | Query | Search results | duckduckgo-search |
| `HTML` | Data + template | HTML string | Jinja2 |

### Agents Layer

Specialized agents that use tools and LLMs.

| Agent | Input | Output | Tools Used |
|-------|-------|--------|------------|
| `Parser` | PDF path | PolicyDocument | PDF, OCR |
| `Analyzer` | PolicyDocument | List[Rule] | LLM only |
| `SQLGen` | List[Rule] | List[SQLResult] | SQL, LLM |
| `Scorer` | List[SQLResult] | List[Confidence] | WebSearch |
| `Reporter` | All data | HTML file | HTML |

### Orchestrator Layer

Coordinates the pipeline execution.

```python
Pipeline:
  PDF → Parser → Analyzer → SQLGen → Scorer → Reporter → HTML
```

---

## Data Flow

```
┌──────────┐
│ PDF File │
└────┬─────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ PARSER AGENT                                                  │
│ ┌─────────┐    ┌─────────┐    ┌─────────────────────────────┐│
│ │PDF Tool │───►│OCR Tool │───►│ PolicyDocument              ││
│ │(pages)  │    │(text)   │    │ - name                      ││
│ └─────────┘    └─────────┘    │ - sections[]                ││
│                               │ - tables[]                  ││
│                               │ - raw_text                  ││
│                               └─────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ ANALYZER AGENT                                                │
│ ┌─────────┐    ┌─────────────────────────────────────────────┐│
│ │   LLM   │───►│ List[ExtractedRule]                        ││
│ │         │    │ - name                                      ││
│ └─────────┘    │ - description                               ││
│                │ - classification                            ││
│                │ - entities                                  ││
│                │ - source_quote                              ││
│                └─────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ SQLGEN AGENT                                                  │
│ ┌─────────┐    ┌─────────┐    ┌─────────────────────────────┐│
│ │   LLM   │───►│SQL Tool │───►│ List[SQLResult]             ││
│ │(generate)│   │(validate)│   │ - rule_name                 ││
│ └─────────┘    └─────────┘    │ - query                     ││
│      ▲              │         │ - is_valid                  ││
│      └──────────────┘         │ - error                     ││
│      (retry if invalid)       └─────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ SCORER AGENT                                                  │
│ ┌───────────┐    ┌──────────────────────────────────────────┐│
│ │WebSearch  │───►│ List[ConfidenceScore]                    ││
│ │Tool       │    │ - rule_name                              ││
│ └───────────┘    │ - score (0-100)                          ││
│                  │ - sources[]                              ││
│                  │ - reasoning                              ││
│                  └──────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│ REPORTER AGENT                                                │
│ ┌─────────┐    ┌──────────────────────────────────────────┐  │
│ │HTML Tool│───►│ report.html                              │  │
│ │(Jinja2) │    │                                          │  │
│ └─────────┘    └──────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## Core Classes Design

### Agent Base Class

```python
class Agent(ABC):
    """Abstract base agent."""

    name: str
    description: str
    tools: list[Tool]
    llm: LLMClient | None

    @abstractmethod
    def run(self, input: Any) -> AgentResponse:
        """Execute agent logic."""
        pass
```

### Tool Base Class

```python
class Tool(ABC):
    """Abstract base tool."""

    name: str
    description: str

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute tool logic."""
        pass
```

### Message Types

```python
class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str | None = None
    tool_calls: list[ToolCall] | None = None

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]
```

### Response Types

```python
class AgentResponse(BaseModel):
    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = {}
```

---

## Agent Implementations

### Parser Agent

```python
class ParserAgent(Agent):
    """Extract text and structure from PDF."""

    tools = [PDFTool, OCRTool]

    def run(self, pdf_path: str) -> AgentResponse[PolicyDocument]:
        # 1. Load PDF pages
        pages = self.tools.pdf.load(pdf_path)

        # 2. OCR each page
        texts = []
        for page in pages:
            result = self.tools.ocr(page.image)
            texts.append(result.text)

        # 3. Structure extraction (LLM)
        document = self.llm.extract_structure(texts)

        return AgentResponse(success=True, data=document)
```

### Analyzer Agent

```python
class AnalyzerAgent(Agent):
    """Identify and classify rules."""

    tools = []  # LLM only

    def run(self, document: PolicyDocument) -> AgentResponse[list[ExtractedRule]]:
        # Prompt LLM to identify rules
        rules = self.llm.analyze_policy(document)

        return AgentResponse(success=True, data=rules)
```

### SQLGen Agent

```python
class SQLGenAgent(Agent):
    """Generate SQL with self-correction."""

    tools = [SQLTool]
    max_retries: int = 3

    def run(self, rules: list[ExtractedRule]) -> AgentResponse[list[SQLResult]]:
        results = []

        for rule in rules:
            query = None
            for attempt in range(self.max_retries):
                # Generate SQL
                query = self.llm.generate_sql(rule)

                # Validate
                validation = self.tools.sql.validate(query)

                if validation.is_valid:
                    break

                # Self-correct
                query = self.llm.correct_sql(query, validation.error)

            results.append(SQLResult(
                rule_name=rule.name,
                query=query,
                is_valid=validation.is_valid
            ))

        return AgentResponse(success=True, data=results)
```

### Scorer Agent

```python
class ScorerAgent(Agent):
    """Calculate confidence scores."""

    tools = [WebSearchTool]

    def run(self, results: list[SQLResult]) -> AgentResponse[list[ConfidenceScore]]:
        scores = []

        for result in results:
            # Search for similar rules
            search_results = self.tools.websearch.search(
                f"CMS {result.rule_name} billing policy"
            )

            # Calculate confidence
            score = self._calculate_score(search_results)

            scores.append(ConfidenceScore(
                rule_name=result.rule_name,
                score=score,
                sources=search_results
            ))

        return AgentResponse(success=True, data=scores)
```

### Reporter Agent

```python
class ReporterAgent(Agent):
    """Generate HTML report."""

    tools = [HTMLTool]

    def run(self, data: ReportData) -> AgentResponse[str]:
        html = self.tools.html.render(
            template="report.jinja2",
            data=data
        )

        return AgentResponse(success=True, data=html)
```

---

## Orchestrator Design

```python
class Pipeline:
    """Orchestrate agent execution."""

    def __init__(self):
        self.parser = ParserAgent()
        self.analyzer = AnalyzerAgent()
        self.sqlgen = SQLGenAgent()
        self.scorer = ScorerAgent()
        self.reporter = ReporterAgent()

    def run(self, pdf_path: str, output_path: str) -> None:
        # Step 1: Parse document
        doc_response = self.parser.run(pdf_path)
        if not doc_response.success:
            raise PipelineError(doc_response.error)

        # Step 2: Analyze policy
        rules_response = self.analyzer.run(doc_response.data)
        if not rules_response.success:
            raise PipelineError(rules_response.error)

        # Step 3: Generate SQL
        sql_response = self.sqlgen.run(rules_response.data)
        if not sql_response.success:
            raise PipelineError(sql_response.error)

        # Step 4: Score confidence
        score_response = self.scorer.run(sql_response.data)
        if not score_response.success:
            raise PipelineError(score_response.error)

        # Step 5: Generate report
        report_data = ReportData(
            document=doc_response.data,
            rules=rules_response.data,
            sql_results=sql_response.data,
            confidence_scores=score_response.data
        )
        report_response = self.reporter.run(report_data)

        # Save output
        Path(output_path).write_text(report_response.data)
```

---

## Error Handling Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                     ERROR HANDLING                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Tool Errors:                                                    │
│    - Catch at tool level                                        │
│    - Return error in response                                   │
│    - Agent decides retry/fail                                   │
│                                                                  │
│  Agent Errors:                                                   │
│    - Catch at agent level                                       │
│    - Return AgentResponse(success=False, error=...)             │
│    - Orchestrator handles                                       │
│                                                                  │
│  Pipeline Errors:                                                │
│    - Catch at pipeline level                                    │
│    - Log full context                                           │
│    - Raise PipelineError to caller                              │
│                                                                  │
│  Retry Strategy (SQLGen):                                        │
│    - Max 3 attempts                                             │
│    - Pass error to LLM for correction                           │
│    - Fail gracefully with partial results                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
policyAgent/
├── src/policyagent/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py      # Environment config
│   │   └── schema.py        # Claims DB schema
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py         # Agent ABC
│   │   ├── tool.py          # Tool ABC
│   │   ├── function.py      # Function wrapper
│   │   ├── message.py       # Message types
│   │   ├── response.py      # Response types
│   │   └── types.py         # Shared types
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── parser/
│   │   ├── analyzer/
│   │   ├── sqlgen/
│   │   ├── scorer/
│   │   └── reporter/
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── pdf.py
│   │   ├── ocr.py
│   │   ├── sql.py
│   │   ├── websearch.py
│   │   └── html.py
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   └── pipeline.py
│   └── templates/
│       └── report.jinja2
├── tests/
├── docs/
├── models/
└── examples/
```
