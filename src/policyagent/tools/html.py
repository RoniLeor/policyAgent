"""HTML report generation tool."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from policyagent.core.response import ToolResult
from policyagent.core.tool import Tool


logger = logging.getLogger(__name__)
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class HTMLTool(Tool):
    """Tool for generating HTML reports from rule data."""

    name = "html_report"
    description = "Generate HTML report from extracted rules and SQL queries."

    def __init__(self, templates_dir: Path | None = None) -> None:
        self._templates_dir = templates_dir or TEMPLATES_DIR
        self._env: Environment | None = None

    def _get_env(self) -> Environment:
        if self._env is None:
            self._env = Environment(
                loader=FileSystemLoader(self._templates_dir),
                autoescape=select_autoescape(["html", "xml"]),
            )
        return self._env

    @classmethod
    def get_parameters_schema(cls) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "report_data": {"type": "object", "description": "Report data including rules and metadata."},
                "output_path": {"type": "string", "description": "Path to save the HTML report."},
                "template": {"type": "string", "description": "Template name to use.", "default": "report.html"},
            },
            "required": ["report_data", "output_path"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        report_data, output_path = kwargs.get("report_data"), kwargs.get("output_path")
        template_name = kwargs.get("template", "report.html")
        if not report_data:
            return ToolResult(tool_name=self.name, success=False, error="Missing required parameter: report_data")
        if not output_path:
            return ToolResult(tool_name=self.name, success=False, error="Missing required parameter: output_path")
        try:
            html_content = self._render(report_data, template_name)
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(html_content, encoding="utf-8")
            return ToolResult(tool_name=self.name, success=True, output={"path": str(output.absolute()), "size": len(html_content)})
        except Exception as e:
            logger.exception("HTML generation failed")
            return ToolResult(tool_name=self.name, success=False, error=f"HTML generation failed: {e}")

    def _render(self, data: dict[str, Any], template_name: str) -> str:
        env = self._get_env()
        template = env.get_template(template_name)
        return template.render(**data)


def create_default_template() -> None:
    """Create the default report template."""
    from policyagent.templates.report_template import REPORT_TEMPLATE  # noqa: PLC0415
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    template_path = TEMPLATES_DIR / "report.html"
    template_path.write_text(REPORT_TEMPLATE, encoding="utf-8")
