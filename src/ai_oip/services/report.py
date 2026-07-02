"""Markdown rendering for the skeleton report.

Deliberately minimal — the Executive Report milestone owns real
reporting. This exists so every discovery run has a human-readable
artifact from day one.
"""

from ai_oip.schemas import SkeletonReport


def render_markdown_report(report: SkeletonReport) -> str:
    """Render a SkeletonReport as a markdown document."""
    lines = [
        "# Problem Discovery Report",
        "",
        f"- **Query:** `{report.query}`",
        f"- **Source:** {report.source}",
        f"- **Items analyzed:** {report.items_collected}",
        f"- **Problems found:** {len(report.findings)}",
        f"- **Generated:** {report.generated_at.isoformat()}",
        "",
    ]
    if not report.findings:
        lines.append("_No concrete problems were extracted from the collected items._")
    for number, finding in enumerate(report.findings, start=1):
        lines.append(f"## {number}. {finding.description}")
        lines.append("")
        if finding.context:
            lines.append(f"**Context:** {finding.context}")
        if finding.evidence:
            lines.append(f"> {finding.evidence}")
        if finding.source_title or finding.source_url:
            title = finding.source_title or "source"
            suffix = f" ({finding.source_url})" if finding.source_url else ""
            lines.append(f"**Source:** {title}{suffix}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
