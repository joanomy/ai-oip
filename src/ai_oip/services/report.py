"""Markdown rendering for the skeleton report.

Deliberately minimal — the Executive Report milestone owns real
reporting. This exists so every discovery run has a human-readable
artifact from day one.
"""

from ai_oip.schemas import (
    CompetitionReport,
    OpportunityReport,
    RecommendationReport,
    SkeletonReport,
    WorkflowReport,
)

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


def render_competition_report(report: CompetitionReport) -> str:
    """Render a CompetitionReport as a markdown document."""
    lines = [
        "# Competition Research Report",
        "",
        f"- **Opportunities analyzed:** {report.targets_analyzed}",
        "",
        "_Assessments reflect model training knowledge and may lag the",
        "live market — verify before acting on them._",
        "",
    ]
    if not report.assessments:
        lines.append("_No scored opportunities were available to research._")
    for number, assessment in enumerate(report.assessments, start=1):
        lines.append(
            f"## {number}. {assessment.workflow_name} "
            f"({assessment.total_score}/100) — saturation: {assessment.saturation}"
        )
        lines.append("")
        if assessment.competitors:
            lines.append("**Known competitors:**")
            for competitor in assessment.competitors:
                suffix = f" — {competitor.positioning}" if competitor.positioning else ""
                lines.append(f"- **{competitor.name}**: {competitor.offering}{suffix}")
        else:
            lines.append("_No known competitors identified._")
        if assessment.market_gap:
            lines.append("")
            lines.append(f"**Gap:** {assessment.market_gap}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_recommendation_report(report: RecommendationReport) -> str:
    """Render a RecommendationReport as a markdown document."""
    lines = [
        "# Product Recommendation Report",
        "",
        f"- **Opportunities analyzed:** {report.targets_analyzed}",
        "",
    ]
    if not report.recommendations:
        lines.append("_No researched opportunities were available to recommend on._")
    for number, rec in enumerate(report.recommendations, start=1):
        lines.append(
            f"## {number}. {rec.workflow_name} ({rec.total_score}/100) — "
            f"{rec.recommendation.upper()}"
        )
        lines.append("")
        lines.append(rec.product_concept)
        lines.append("")
        if rec.mvp_scope:
            lines.append("**MVP scope:**")
            lines.extend(f"- {step}" for step in rec.mvp_scope)
            lines.append("")
        if rec.differentiation:
            lines.append(f"**Differentiation:** {rec.differentiation}")
            lines.append("")
        lines.append(f"_Saturation: {rec.saturation}_")
        lines.append("")
        lines.append(f"**Rationale:** {rec.rationale}")
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
