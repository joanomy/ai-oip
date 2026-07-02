"""Markdown rendering for the skeleton report.

Deliberately minimal — the Executive Report milestone owns real
reporting. This exists so every discovery run has a human-readable
artifact from day one.
"""

from ai_oip.schemas import OpportunityReport, SkeletonReport, WorkflowReport

_DIMENSION_LABELS = {
    "pain_intensity": "Pain intensity",
    "automation_feasibility": "Automation feasibility",
    "frequency": "Frequency",
    "market_breadth": "Market breadth",
    "willingness_to_pay": "Willingness to pay",
}


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


def render_opportunity_report(report: OpportunityReport) -> str:
    """Render an OpportunityReport as a markdown ranking."""
    lines = [
        "# Opportunity Scoring Report",
        "",
        f"- **Workflows scored:** {report.workflows_scored}",
        "",
    ]
    if not report.opportunities:
        lines.append("_No workflows were available to score._")
    for rank, opportunity in enumerate(report.opportunities, start=1):
        lines.append(f"## {rank}. {opportunity.workflow_name} — {opportunity.total_score}/100")
        lines.append("")
        for dimension, label in _DIMENSION_LABELS.items():
            judged = getattr(opportunity.score, dimension)
            lines.append(f"- **{label}:** {judged.score}/10 — {judged.rationale}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_workflow_report(report: WorkflowReport) -> str:
    """Render a WorkflowReport as a markdown document."""
    lines = [
        "# Workflow Discovery Report",
        "",
        f"- **Problems analyzed:** {report.problems_analyzed}",
        f"- **Workflows discovered:** {len(report.workflows)}",
        "",
    ]
    if not report.workflows:
        lines.append("_No recurring workflows were identified from the stored problems._")
    for number, workflow in enumerate(report.workflows, start=1):
        lines.append(f"## {number}. {workflow.name}")
        lines.append("")
        lines.append(workflow.description)
        if workflow.steps:
            lines.append("")
            lines.append("**Steps:**")
            lines.extend(
                f"{step_number}. {step}" for step_number, step in enumerate(workflow.steps, start=1)
            )
        if workflow.actors:
            lines.append("")
            lines.append(f"**Actors:** {', '.join(workflow.actors)}")
        lines.append("")
        lines.append(f"_Linked problems: {workflow.problems_linked}_")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
