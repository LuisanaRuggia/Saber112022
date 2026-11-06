"""Render the pipeline results as an A4 PDF made of text and tables."""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

from saber11.models.report.report_models import PipelineResults
from saber11.renderers.report.pdf_sections_closing import conclusions_section, sources_section, spatial_section
from saber11.renderers.report.pdf_sections_inference import explanatory_section
from saber11.renderers.report.pdf_sections_intro import cover, methodology, summary
from saber11.renderers.report.pdf_sections_stats import assumptions_section, descriptive_section
from saber11.renderers.report.pdf_styles import draw_footer


def render_pdf(results: PipelineResults, path: Path) -> Path:
    """Write the report PDF to path and return it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=40, rightMargin=40, topMargin=44, bottomMargin=44,
                            title="Saber 11 Bogotá: rendimiento por jornada")
    story = []
    for build in (cover, summary, methodology, descriptive_section, assumptions_section,
                  explanatory_section, spatial_section, conclusions_section, sources_section):
        story += build(results)
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    return path
