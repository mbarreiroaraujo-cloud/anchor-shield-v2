"""Report generation for scan results."""

import json
from typing import Optional
from scanner.engine import ScanReport


SEVERITY_COLORS = {
    "Critical": "\033[91m",  # Red
    "High": "\033[91m",      # Red
    "Medium": "\033[93m",    # Yellow
    "Low": "\033[92m",       # Green
}
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def format_terminal_report(report: ScanReport) -> str:
    """Format scan report for terminal output."""
    lines = []

    # Header
    lines.append("")
    lines.append(f"{BOLD}anchor-shield Scan Report{RESET}")
    lines.append("=" * 60)
    lines.append(f"Target:           {report.target}")
    lines.append(f"Files scanned:    {report.files_scanned}")
    lines.append(f"Patterns checked: {report.patterns_checked}")
    lines.append(f"Scan time:        {report.scan_time:.2f}s")

    if report.anchor_version:
        lines.append(f"Anchor version:   {report.anchor_version}")

    lines.append(f"Security score:   {_colorize_score(report.security_score)}")
    lines.append("")

    # Summary bar
    summary = report.summary
    if summary:
        sev = summary.get("by_severity", {})
        critical = sev.get("Critical", 0)
        high = sev.get("High", 0)
        medium = sev.get("Medium", 0)
        low = sev.get("Low", 0)

        lines.append(
            f"  \033[91mCritical: {critical}{RESET}  "
            f"\033[91mHigh: {high}{RESET}  "
            f"\033[93mMedium: {medium}{RESET}  "
            f"\033[92mLow: {low}{RESET}"
        )
        lines.append("")

    # Findings
    if not report.findings:
        lines.append(f"\033[92mNo vulnerabilities detected.{RESET}")
        lines.append("")
        lines.append(f"{DIM}Scanned {report.files_scanned} files against "
                     f"{report.patterns_checked} detection patterns.{RESET}")
    else:
        lines.append(f"{BOLD}Findings ({len(report.findings)}):{RESET}")
        lines.append("-" * 60)

        for i, finding in enumerate(report.findings, 1):
            color = SEVERITY_COLORS.get(finding.severity, "")
            lines.append("")
            lines.append(
                f"  {color}{BOLD}[{finding.severity.upper()}]{RESET} "
                f"{BOLD}{finding.id}{RESET} — {finding.name}"
            )
            lines.append(f"  File: {finding.file}:{finding.line}")
            lines.append(f"  {finding.description}")

            if finding.code_snippet:
                lines.append("")
                for snip_line in finding.code_snippet.split("\n"):
                    lines.append(f"    {snip_line}")

            lines.append("")
            lines.append(f"  {BOLD}Fix:{RESET} {finding.fix_recommendation.split(chr(10))[0]}")
            lines.append(f"  {DIM}Reference: {finding.reference}{RESET}")

            if i < len(report.findings):
                lines.append("  " + "-" * 56)

    lines.append("")
    lines.append("=" * 60)
    lines.append("")

    return "\n".join(lines)


def format_json_report(report: ScanReport, indent: int = 2) -> str:
    """Format scan report as JSON."""
    return report.to_json(indent=indent)


def format_html_report(report: ScanReport) -> str:
    """Format scan report as standalone HTML."""
    summary = report.summary or {}
    sev = summary.get("by_severity", {})

    findings_html = ""
    for finding in report.findings:
        sev_class = finding.severity.lower()
        findings_html += f"""
        <div class="finding {sev_class}">
            <div class="finding-header">
                <span class="severity-badge {sev_class}">{finding.severity.upper()}</span>
                <strong>{finding.id}</strong> — {finding.name}
            </div>
            <div class="finding-meta">
                <code>{finding.file}:{finding.line}</code>
            </div>
            <p>{finding.description}</p>
            <details>
                <summary>Details & Fix</summary>
                <div class="details-content">
                    <h4>Root Cause</h4>
                    <p>{finding.root_cause}</p>
                    <h4>Exploit Scenario</h4>
                    <pre>{finding.exploit_scenario}</pre>
                    <h4>Fix Recommendation</h4>
                    <pre>{finding.fix_recommendation}</pre>
                    {_render_code_snippet(finding.code_snippet)}
                </div>
            </details>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>anchor-shield Scan Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
               background: #0F1117; color: #E0E0E0; padding: 2rem; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #9945FF; font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #888; margin-bottom: 2rem; }}
        .summary-bar {{ display: flex; gap: 1.5rem; margin-bottom: 2rem;
                       padding: 1rem; background: #1A1D2E; border-radius: 8px; }}
        .summary-item {{ text-align: center; }}
        .summary-item .count {{ font-size: 1.5rem; font-weight: bold; }}
        .summary-item .label {{ font-size: 0.8rem; color: #888; }}
        .critical .count {{ color: #FF4444; }}
        .high .count {{ color: #FF4444; }}
        .medium .count {{ color: #FFA500; }}
        .low .count {{ color: #00C853; }}
        .meta {{ display: flex; gap: 2rem; margin-bottom: 2rem; color: #888;
                font-size: 0.9rem; }}
        .finding {{ background: #1A1D2E; border-radius: 8px; padding: 1.2rem;
                   margin-bottom: 1rem; border-left: 4px solid #555; }}
        .finding.high {{ border-left-color: #FF4444; }}
        .finding.critical {{ border-left-color: #FF4444; }}
        .finding.medium {{ border-left-color: #FFA500; }}
        .finding.low {{ border-left-color: #00C853; }}
        .finding-header {{ margin-bottom: 0.5rem; }}
        .severity-badge {{ padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;
                          font-weight: bold; }}
        .severity-badge.high, .severity-badge.critical {{ background: #FF444433; color: #FF4444; }}
        .severity-badge.medium {{ background: #FFA50033; color: #FFA500; }}
        .severity-badge.low {{ background: #00C85333; color: #00C853; }}
        .finding-meta {{ color: #888; font-size: 0.85rem; margin-bottom: 0.5rem; }}
        details {{ margin-top: 0.8rem; }}
        summary {{ cursor: pointer; color: #9945FF; font-size: 0.9rem; }}
        .details-content {{ margin-top: 1rem; padding: 1rem; background: #0F1117;
                          border-radius: 4px; }}
        .details-content h4 {{ color: #14F195; margin: 0.8rem 0 0.3rem; font-size: 0.9rem; }}
        pre {{ background: #0a0c12; padding: 0.8rem; border-radius: 4px;
              overflow-x: auto; font-size: 0.85rem; color: #ccc; white-space: pre-wrap; }}
        code {{ font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 0.85rem; }}
        .no-findings {{ text-align: center; padding: 2rem; color: #00C853; font-size: 1.1rem; }}
        .score {{ font-size: 1.2rem; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>anchor-shield Scan Report</h1>
        <p class="subtitle">Automated security scanner for Solana Anchor programs</p>

        <div class="meta">
            <span>Target: <strong>{report.target}</strong></span>
            <span>Files: <strong>{report.files_scanned}</strong></span>
            <span>Patterns: <strong>{report.patterns_checked}</strong></span>
            <span>Time: <strong>{report.scan_time:.2f}s</strong></span>
            <span>Score: <strong class="score">{report.security_score}</strong></span>
        </div>

        <div class="summary-bar">
            <div class="summary-item critical"><div class="count">{sev.get('Critical', 0)}</div><div class="label">Critical</div></div>
            <div class="summary-item high"><div class="count">{sev.get('High', 0)}</div><div class="label">High</div></div>
            <div class="summary-item medium"><div class="count">{sev.get('Medium', 0)}</div><div class="label">Medium</div></div>
            <div class="summary-item low"><div class="count">{sev.get('Low', 0)}</div><div class="label">Low</div></div>
        </div>

        {"<div class='no-findings'>No vulnerabilities detected. Scanned " + str(report.files_scanned) + " files against " + str(report.patterns_checked) + " patterns.</div>" if not report.findings else findings_html}
    </div>
</body>
</html>"""


def _colorize_score(score: str) -> str:
    """Add color to security score."""
    if score in ("A", "A+"):
        return f"\033[92m{score}{RESET}"
    elif score in ("B", "B+"):
        return f"\033[93m{score}{RESET}"
    else:
        return f"\033[91m{score}{RESET}"


def _render_code_snippet(snippet: str) -> str:
    """Render code snippet as HTML."""
    if not snippet:
        return ""
    import html
    return f"<h4>Code</h4><pre><code>{html.escape(snippet)}</code></pre>"
