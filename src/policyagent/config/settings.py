"""Application settings and configuration."""

from __future__ import annotations

import os
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderEnum(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMSettings(BaseModel):
    """LLM provider configuration."""

    provider: LLMProviderEnum = LLMProviderEnum.OPENAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"


class OCRSettings(BaseModel):
    """OCR configuration."""

    det_model: str = "PP-OCRv5_det.onnx"
    rec_model: str = "PP-OCRv5_rec.onnx"
    use_gpu: bool = False


class PDFSettings(BaseModel):
    """PDF processing configuration."""

    dpi: int = 300


class SQLSettings(BaseModel):
    """SQL generation configuration."""

    max_retries: int = 3


class WebSearchSettings(BaseModel):
    """Web search configuration."""

    max_results: int = 5


class Settings(BaseSettings):
    """Application configuration.

    Settings are loaded from environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    # LLM Configuration
    llm: LLMSettings = Field(default_factory=LLMSettings)

    # OCR Configuration
    ocr: OCRSettings = Field(default_factory=OCRSettings)

    # PDF Configuration
    pdf: PDFSettings = Field(default_factory=PDFSettings)

    # SQL Configuration
    sql: SQLSettings = Field(default_factory=SQLSettings)

    # Web Search Configuration
    websearch: WebSearchSettings = Field(default_factory=WebSearchSettings)

    # Logging
    log_level: str = "INFO"

    def __init__(self, **data: Any) -> None:
        """Initialize settings with environment variable overrides."""
        super().__init__(**data)
        self._load_env_overrides()

    def _load_env_overrides(self) -> None:
        """Load environment variable overrides for nested settings."""
        # LLM overrides
        if provider := os.getenv("LLM_PROVIDER"):
            self.llm.provider = LLMProviderEnum(provider)
        if key := os.getenv("OPENAI_API_KEY"):
            self.llm.openai_api_key = key
        if model := os.getenv("OPENAI_MODEL"):
            self.llm.openai_model = model
        if key := os.getenv("ANTHROPIC_API_KEY"):
            self.llm.anthropic_api_key = key
        if model := os.getenv("ANTHROPIC_MODEL"):
            self.llm.anthropic_model = model

        # OCR overrides
        if det := os.getenv("OCR_DET_MODEL"):
            self.ocr.det_model = det
        if rec := os.getenv("OCR_REC_MODEL"):
            self.ocr.rec_model = rec
        if gpu := os.getenv("OCR_USE_GPU"):
            self.ocr.use_gpu = gpu.lower() in ("true", "1", "yes")

        # PDF overrides
        if dpi := os.getenv("PDF_DPI"):
            self.pdf.dpi = int(dpi)

        # SQL overrides
        if retries := os.getenv("SQL_MAX_RETRIES"):
            self.sql.max_retries = int(retries)

        # WebSearch overrides
        if results := os.getenv("WEBSEARCH_MAX_RESULTS"):
            self.websearch.max_results = int(results)
