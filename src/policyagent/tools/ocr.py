"""OCR tool using PaddleOCR via RapidOCR."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from policyagent.config.settings import Settings
from policyagent.core.response import ToolResult
from policyagent.core.tool import Tool


logger = logging.getLogger(__name__)


def download_models(models_dir: Path | None = None) -> None:
    """Download PaddleOCR ONNX models using huggingface_hub.

    Args:
        models_dir: Directory to save models. Defaults to project models/ dir.
    """
    from huggingface_hub import hf_hub_download

    if models_dir is None:
        models_dir = Path(__file__).parent.parent.parent.parent.parent / "models"

    models_dir.mkdir(parents=True, exist_ok=True)

    # Use monkt/paddleocr-onnx for PP-OCRv5 models
    models = [
        ("monkt/paddleocr-onnx", "detection/v5/det.onnx", "PP-OCRv5_det.onnx"),
        ("monkt/paddleocr-onnx", "languages/english/rec.onnx", "PP-OCRv5_rec.onnx"),
    ]

    for repo_id, filename, local_name in models:
        target = models_dir / local_name
        if target.exists():
            logger.info("Model already exists: %s", local_name)
            continue

        logger.info("Downloading %s from %s...", filename, repo_id)
        downloaded = hf_hub_download(repo_id=repo_id, filename=filename)
        # Copy to our models directory
        import shutil

        shutil.copy(downloaded, target)
        logger.info("Downloaded: %s", local_name)


class OCRTool(Tool):
    """Tool for extracting text from images using PaddleOCR (ONNX via RapidOCR)."""

    name = "ocr"
    description = "Extract text from images using PaddleOCR ONNX models."

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize OCR tool.

        Args:
            settings: Application settings. If None, loads from environment.
        """
        if settings is None:
            settings = Settings()

        self.use_gpu = settings.ocr.use_gpu
        self._ocr: Any = None

    def _get_ocr(self) -> Any:
        """Lazy initialization of RapidOCR engine."""
        if self._ocr is None:
            from rapidocr import RapidOCR

            # RapidOCR v3+ auto-downloads models, just use defaults
            self._ocr = RapidOCR()

        return self._ocr

    @classmethod
    def get_parameters_schema(cls) -> dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Image data (bytes or path) to extract text from.",
                },
            },
            "required": ["image"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Extract text from an image.

        Args:
            **kwargs: Must include 'image' (bytes or path).

        Returns:
            ToolResult with extracted text and bounding boxes.
        """
        image_data = kwargs.get("image")
        if image_data is None:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Missing required parameter: image",
            )

        try:
            text, boxes = self._extract_text(image_data)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "text": text,
                    "boxes": boxes,
                },
            )
        except Exception as e:
            logger.exception("OCR failed")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"OCR failed: {e}",
            )

    def _extract_text(self, image_data: bytes | str | Path) -> tuple[str, list[dict[str, Any]]]:
        """Extract text from image data.

        Args:
            image_data: Image as bytes, file path string, or Path object.

        Returns:
            Tuple of (full text, list of text boxes with coordinates).
        """
        # Load image
        if isinstance(image_data, bytes):
            img = Image.open(BytesIO(image_data))
        elif isinstance(image_data, str | Path):
            img = Image.open(image_data)
        else:
            msg = f"Invalid image data type: {type(image_data)}"
            raise TypeError(msg)

        # Run OCR
        ocr = self._get_ocr()
        result = ocr(img)

        # Extract results
        lines: list[str] = []
        boxes: list[dict[str, Any]] = []

        if result and result.boxes is not None:
            for i, (box, text, score) in enumerate(
                zip(result.boxes, result.txts, result.scores, strict=True)
            ):
                lines.append(text)
                boxes.append(
                    {
                        "id": i,
                        "text": text,
                        "confidence": float(score),
                        "box": box.tolist() if hasattr(box, "tolist") else list(box),
                    }
                )

        return "\n".join(lines), boxes

    async def process_pdf_images(self, images: list[bytes]) -> list[dict[str, Any]]:
        """Process multiple PDF page images.

        Args:
            images: List of PNG image bytes.

        Returns:
            List of OCR results per page.
        """
        results: list[dict[str, Any]] = []

        for i, image_bytes in enumerate(images):
            result = await self.execute(image=image_bytes)
            if result.success and isinstance(result.output, dict):
                results.append(
                    {
                        "page": i + 1,
                        "text": result.output.get("text", ""),
                        "boxes": result.output.get("boxes", []),
                    }
                )
            else:
                results.append(
                    {
                        "page": i + 1,
                        "text": "",
                        "boxes": [],
                        "error": result.error,
                    }
                )

        return results
