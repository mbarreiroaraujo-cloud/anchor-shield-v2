#!/usr/bin/env python3
"""
Scan a verified Solana program by its on-chain address.

Usage:
    python scripts/scan_program.py <PROGRAM_ID> [--output-dir DIR] [--format FORMAT]

Examples:
    python scripts/scan_program.py whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc
    python scripts/scan_program.py MarBmsSgKXdrN1egZf5sqe1TMai9K1rChYNDJgjq7aD --format json
"""

import argparse
import json
import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from scanner.registry import (
    validate_program_id,
    check_verification,
    scan_program,
    ProgramScanResult,
)
from scanner.report import format_terminal_report, format_json_report

console = Console()

BANNER = """[bold purple]
   __ _ _ __   ___| |__   ___  _ __      ___| |__ (_) ___| | __| |
  / _` | '_ \\ / __| '_ \\ / _ \\| '__|____/ __| '_ \\| / _ \\ |/ _` |
 | (_| | | | | (__| | | | (_) | | |_____\\__ \\ | | | |  __/ | (_| |
  \\__,_|_| |_|\\___|_| |_|\\___/|_|       |___/_| |_|_|\\___|_|\\__,_|
[/bold purple]
[bold]Registry Scanner[/bold] — Scan verified Solana programs by address
[dim]Powered by OtterSec Verified Programs API (verify.osec.io)[/dim]
"""


def display_verification_info(result: ProgramScanResult):
    """Display verification status in a rich table."""
    v = result.verification

    table = Table(
        title="Program Verification Status",
        box=box.ROUNDED,
        title_style="bold purple",
    )
    table.add_column("Property", style="bold")
    table.add_column("Value")

    table.add_row("Program ID", result.program_id)

    if v.is_verified:
        table.add_row("Verified", "[bold green]Yes[/bold green]")
        table.add_row("Message", v.message)
        if v.repo_url:
            table.add_row("Repository", v.repo_url)
        if v.commit:
            table.add_row("Commit", v.commit[:12] + "...")
        if v.on_chain_hash:
            table.add_row("On-Chain Hash", v.on_chain_hash[:16] + "...")
        if v.last_verified_at:
            table.add_row("Last Verified", v.last_verified_at)
    else:
        table.add_row("Verified", "[bold red]No[/bold red]")
        table.add_row("Message", v.message)

    console.print(table)
    console.print()


def display_scan_results(result: ProgramScanResult, output_format: str):
    """Display scan results for all discovered Anchor programs."""
    if not result.scan_reports:
        return

    console.print(
        f"[bold green]Found {len(result.anchor_programs_found)} "
        f"Anchor program(s):[/bold green]"
    )
    for name in result.anchor_programs_found:
        console.print(f"  [dim]>[/dim] {name}")
    console.print()

    for report in result.scan_reports:
        console.print(f"[bold purple]--- Scan: {report.target} ---[/bold purple]")

        if output_format == "json":
            console.print(format_json_report(report))
        else:
            print(format_terminal_report(report))


def save_report(result: ProgramScanResult, output_dir: str):
    """Save scan results as JSON to the output directory."""
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "SECURITY_REPORT.json")

    report_data = {
        "program_id": result.program_id,
        "verification": result.verification.to_dict(),
        "anchor_programs_found": result.anchor_programs_found,
        "scan_results": [r.to_dict() for r in result.scan_reports],
        "summary": {
            "total_programs_scanned": len(result.scan_reports),
            "total_files_scanned": sum(r.files_scanned for r in result.scan_reports),
            "total_findings": sum(len(r.findings) for r in result.scan_reports),
        },
    }

    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)

    return report_path


def main():
    parser = argparse.ArgumentParser(
        description="Scan a verified Solana program by its on-chain address.",
        epilog="Uses the OtterSec Verified Programs API (verify.osec.io).",
    )
    parser.add_argument(
        "program_id",
        help="Solana program address (base58 encoded)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for saving the report (default: reports/<program_id>)",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["terminal", "json"],
        default="terminal",
        help="Output format (default: terminal)",
    )

    args = parser.parse_args()

    console.print(BANNER)

    # Validate program ID format
    if not validate_program_id(args.program_id):
        console.print(
            "[bold red]Error:[/bold red] Invalid Solana program ID format.\n"
            "[dim]A valid program ID is a base58-encoded string of 32-44 characters.\n"
            "Example: whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc[/dim]"
        )
        sys.exit(1)

    # Run the full scan pipeline
    with console.status(
        "[bold purple]Checking program verification on OtterSec...[/bold purple]"
    ):
        result = scan_program(args.program_id)

    # Display verification info
    display_verification_info(result)

    # Handle errors
    if result.error:
        console.print(f"[bold yellow]Note:[/bold yellow] {result.error}")
        console.print()

    # Handle unverified program
    if not result.verification.is_verified:
        console.print(
            Panel(
                "[bold]This program does not have verified source code.[/bold]\n\n"
                "To scan a program, it must have a verified build on "
                "[link=https://verify.osec.io]verify.osec.io[/link].\n\n"
                "[dim]Verified builds ensure the on-chain bytecode matches "
                "the published source code.\n"
                "You can verify your own programs at "
                "https://github.com/otter-sec/solana-verified-programs-api[/dim]",
                title="Unverified Program",
                border_style="yellow",
            )
        )
        sys.exit(0)

    # Display scan results
    if result.scan_reports:
        display_scan_results(result, args.output_format)

        # Save report
        output_dir = args.output_dir or os.path.join(
            "reports", args.program_id
        )
        report_path = save_report(result, output_dir)
        console.print(f"[bold green]Report saved to:[/bold green] {report_path}")

        # Summary
        total_findings = sum(len(r.findings) for r in result.scan_reports)
        total_files = sum(r.files_scanned for r in result.scan_reports)
        console.print()
        console.print(
            Panel(
                f"[bold]Programs scanned:[/bold] {len(result.scan_reports)}\n"
                f"[bold]Files analyzed:[/bold]   {total_files}\n"
                f"[bold]Findings:[/bold]          {total_findings}\n"
                f"[bold]Report:[/bold]            {report_path}",
                title="Scan Complete",
                border_style="green",
            )
        )
    elif not result.error:
        console.print("[dim]No scan results to display.[/dim]")


if __name__ == "__main__":
    main()
