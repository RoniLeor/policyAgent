"""Parser agent for extracting content from PDF documents."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from policyagent.core.agent import Agent
from policyagent.core.models import ParsedDocument, ParsedPage
from policyagent.core.response import AgentResponse, LLMResponse, ToolResult
from policyagent.core.types import AgentRole
from policyagent.tools.ocr import OCRTool
from policyagent.tools.pdf import PDFTool


if TYPE_CHECKING:
    from policyagent.core.llm import LLMClient


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a document parsing specialist.
Your task is to extract text content from PDF policy documents using OCR.

You have access to the following tools:
- pdf_loader: Load a PDF file and extract pages as images
- ocr: Extract text from images using PaddleOCR

Process:
1. Load the PDF file using pdf_loader
2. For each page image, extract text using OCR
3. Return the complete extracted text

Focus on accurate text extraction. Preserve the document structure as much as possible."""


class ParserAgent(Agent):
    """Agent for parsing PDF documents and extracting text content."""

    def __init__(self, llm: LLMClient) -> None:
        """Initialize the parser agent.

        Args:
            llm: LLM client for agent reasoning.
        """
        pdf_tool = PDFTool()
        ocr_tool = OCRTool()
        super().__init__(llm=llm, tools=[pdf_tool, ocr_tool], max_iterations=5)
        self._pdf_tool = pdf_tool
        self._ocr_tool = ocr_tool

    @property
    def role(self) -> AgentRole:
        """Get the agent's role."""
        return AgentRole.PARSER

    @property
    def system_prompt(self) -> str:
        """Get the agent's system prompt."""
        return SYSTEM_PROMPT

    def format_input(self, input_data: Any) -> str:
        """Format input data as a user message.

        Args:
            input_data: Path to PDF file.

        Returns:
            Formatted user message.
        """
        return f"Please extract all text content from the PDF document at: {input_data}"

    def process_output(
        self,
        response: LLMResponse,
        tool_results: list[ToolResult],
        total_tokens: int,
    ) -> AgentResponse:
        """Process the final LLM response into an AgentResponse.

        Args:
            response: Final LLM response.
            tool_results: Results from all tool executions.
            total_tokens: Total tokens used.

        Returns:
            AgentResponse with ParsedDocument output.
        """
        # This agent primarily uses direct tool execution
        # The response content is secondary
        return AgentResponse(
            success=True,
            output=response.content,
            tool_results=tool_results,
            total_tokens=total_tokens,
        )

    async def parse(self, pdf_path: str | Path) -> ParsedDocument:
        """Parse a PDF document directly without LLM reasoning.

        This is the primary method for parsing PDFs, using tools directly
        rather than going through the LLM reasoning loop.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            ParsedDocument with extracted text.
        """
        path = Path(pdf_path)
        logger.info("Parsing PDF: %s", path.name)

        # Load PDF
        pdf_result = await self._pdf_tool.execute(pdf_path=str(path))
        if not pdf_result.success or not isinstance(pdf_result.output, dict):
            msg = f"Failed to load PDF: {pdf_result.error}"
            raise ValueError(msg)

        output_dict = cast("dict[str, Any]", pdf_result.output)
        images: list[bytes] = output_dict.get("images", [])
        page_count: int = output_dict.get("page_count", 0)

        # OCR each page
        pages: list[ParsedPage] = []
        ocr_results = await self._ocr_tool.process_pdf_images(images)

        for result in ocr_results:
            pages.append(
                ParsedPage(
                    page_number=result["page"],
                    text=result.get("text", ""),
                    boxes=result.get("boxes", []),
                )
            )
            text_len = len(result.get("text", ""))
            logger.debug("Parsed page %d: %d characters", result["page"], text_len)

        document = ParsedDocument(
            path=str(path.absolute()),
            page_count=page_count,
            pages=pages,
        )

        logger.info("Parsed %d pages from %s", page_count, path.name)
        return document
