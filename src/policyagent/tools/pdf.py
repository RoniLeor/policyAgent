"""PDF loading and image extraction tool."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from policyagent.config.settings import Settings
from policyagent.core.response import ToolResult
from policyagent.core.tool import Tool


logger = logging.getLogger(__name__)


class PDFTool(Tool):
    """Tool for loading PDF files and extracting page images."""

    name = "pdf_loader"
    description = "Load a PDF file and extract pages as images for OCR processing."

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize PDF tool.

        Args:
            settings: Application settings. If None, loads from environment.
        """
        if settings is None:
            settings = Settings()
        self.dpi = settings.pdf.dpi

    @classmethod
    def get_parameters_schema(cls) -> dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "pdf_path": {
                    "type": "string",
                    "description": "Path to the PDF file to load.",
                },
            },
            "required": ["pdf_path"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Load PDF and extract page images.

        Args:
            **kwargs: Must include 'pdf_path'.

        Returns:
            ToolResult with list of PIL images for each page.
        """
        pdf_path = kwargs.get("pdf_path")
        if not pdf_path:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Missing required parameter: pdf_path",
            )

        path = Path(pdf_path)
        if not path.exists():
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"PDF file not found: {pdf_path}",
            )

        try:
            images = self._extract_images(path)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "path": str(path.absolute()),
                    "page_count": len(images),
                    "images": images,
                },
            )
        except Exception as e:
            logger.exception("Failed to load PDF: %s", pdf_path)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Failed to load PDF: {e}",
            )

    def _extract_images(self, pdf_path: Path) -> list[bytes]:
        """Extract page images from PDF.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            List of PNG image bytes for each page.
        """
        images: list[bytes] = []
        zoom = self.dpi / 72  # 72 is the default PDF DPI

        with fitz.open(pdf_path) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                images.append(pix.tobytes("png"))
                logger.debug("Extracted page %d from %s", page_num + 1, pdf_path.name)

        return images
