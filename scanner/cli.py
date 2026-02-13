"""CLI entry point for anchor-shield-v2."""

import sys
import os
import json

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from scanner.engine import AnchorShieldEngine, ScanReport
from scanner.report import format_terminal_report, format_json_report, format_html_report

console = Console()

BANNER = """[bold purple]
   __ _ _ __   ___| |__   ___  _ __      ___| |__ (_) ___| | __| |
  / _` | '_ \\ / __| '_ \\ / _ \\| '__|____/ __| '_ \\| / _ \\ |/ _` |
 | (_| | | | | (__| | | | (_) | | |_____\\__ \\ | | | |  __/ | (_| |
  \\__,_|_| |_|\\___|_| |_|\\___/|_|       |___/_| |_|_|\\___|_|\\__,_|
[/bold purple]
[dim]Automated Security Scanner for Solana Anchor Programs[/dim]
"""


@click.group()
@click.version_option(version="0.1.0", prog_name="anchor-shield-v2")
def cli():
    """anchor-shield-v2: Automated security scanner for Solana Anchor programs."""
    pass


@cli.command()
@click.argument("target")
@click.option("--format", "output_format", type=click.Choice(["terminal", "json", "html"]),
              default="terminal", help="Output format")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def scan(target, output_format, output, verbose):
    """Scan an Anchor program for vulnerability patterns.

    TARGET can be a local directory path or a GitHub repository URL.
    """
    console.print(BANNER)

    engine = AnchorShieldEngine()

    # Determine if target is a URL or local path
    if target.startswith("https://github.com/") or target.startswith("github.com/"):
        console.print(f"[bold]Scanning GitHub repository:[/bold] {target}")
        console.print("[dim]Fetching source files...[/dim]")

        try:
            from scanner.github_client import GitHubClient
            client = GitHubClient()
            files = client.fetch_repo_files(target)

            if not files:
                console.print("[red]No Rust files found in repository.[/red]")
                sys.exit(1)

            console.print(f"[dim]Fetched {len(files)} Rust files[/dim]")

            # Scan each file
            report = ScanReport(
                target=target,
                files_scanned=len(files),
                patterns_checked=len(engine.patterns),
            )

            import time
            start = time.time()
            for filepath, content in files.items():
                for pattern in engine.patterns:
                    try:
                        findings = pattern.scan(filepath, content)
                        report.findings.extend(findings)
                    except Exception:
                        pass

            report.scan_time = time.time() - start
            report.security_score = engine._compute_security_score(report.findings)
            report.summary = engine._compute_summary(report.findings)

        except Exception as e:
            console.print(f"[red]Error fetching repository: {e}[/red]")
            sys.exit(1)
    else:
        # Local path
        target_path = os.path.abspath(target)
        if not os.path.exists(target_path):
            console.print(f"[red]Path not found: {target_path}[/red]")
            sys.exit(1)

        console.print(f"[bold]Scanning local path:[/bold] {target_path}")
        report = engine.scan_directory(target_path)

    # Output results
    _output_report(report, output_format, output)


@cli.command()
@click.argument("program_id")
@click.option("--network", "-n", type=click.Choice(["mainnet-beta", "devnet", "testnet"]),
              default="mainnet-beta", help="Solana network")
def check(program_id, network):
    """Check a deployed Solana program for risk indicators.

    PROGRAM_ID is the on-chain program address.
    """
    console.print(BANNER)
    console.print(f"[bold]Checking program:[/bold] {program_id}")
    console.print(f"[dim]Network: {network}[/dim]")
    console.print()

    try:
        from scanner.solana_client import SolanaChecker
        checker = SolanaChecker(network=network)

        with console.status("[bold purple]Querying Solana RPC...[/bold purple]"):
            assessment = checker.check_program_risk(program_id)

        # Display results
        risk_color = {
            "Minimal": "green",
            "Low": "green",
            "Medium": "yellow",
            "High": "red",
            "Unknown": "dim",
        }.get(assessment.risk_level, "white")

        table = Table(
            title="On-Chain Risk Assessment",
            box=box.ROUNDED,
            title_style="bold purple",
        )
        table.add_column("Property", style="bold")
        table.add_column("Value")

        table.add_row("Program ID", program_id)
        table.add_row("Network", network)
        table.add_row("Risk Level", f"[{risk_color}]{assessment.risk_level}[/{risk_color}]")
        table.add_row("IDL Found", "Yes" if assessment.idl_found else "No")

        if assessment.program_info:
            info = assessment.program_info
            table.add_row("Executable", "Yes" if info.executable else "No")
            table.add_row("Upgradeable", "Yes" if info.is_upgradeable else "No")
            if info.upgrade_authority:
                table.add_row("Upgrade Authority", info.upgrade_authority)
            if info.last_deploy_slot:
                table.add_row("Last Deploy Slot", str(info.last_deploy_slot))

        console.print(table)
        console.print()

        # Warnings
        if assessment.idl_warnings:
            console.print("[bold yellow]Warnings:[/bold yellow]")
            for w in assessment.idl_warnings:
                console.print(f"  [yellow]! {w}[/yellow]")
            console.print()

        # Recommendations
        if assessment.recommendations:
            console.print("[bold]Recommendations:[/bold]")
            for r in assessment.recommendations:
                console.print(f"  [dim]> {r}[/dim]")
            console.print()

        # JSON output
        console.print(Panel(
            json.dumps(assessment.to_dict(), indent=2),
            title="Raw Assessment Data",
            border_style="dim",
        ))

    except Exception as e:
        console.print(f"[red]Error checking program: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("target")
@click.option("--format", "output_format", type=click.Choice(["json", "html"]),
              default="json", help="Report format")
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file path")
def report(target, output_format, output):
    """Generate a scan report file.

    TARGET is a local directory path or GitHub repo URL.
    """
    console.print(BANNER)
    console.print(f"[bold]Generating {output_format.upper()} report for:[/bold] {target}")

    engine = AnchorShieldEngine()

    if target.startswith("https://github.com/"):
        from scanner.github_client import GitHubClient
        client = GitHubClient()
        files = client.fetch_repo_files(target)

        import time
        start = time.time()
        scan_report = ScanReport(
            target=target,
            files_scanned=len(files),
            patterns_checked=len(engine.patterns),
        )
        for filepath, content in files.items():
            for pattern in engine.patterns:
                try:
                    findings = pattern.scan(filepath, content)
                    scan_report.findings.extend(findings)
                except Exception:
                    pass
        scan_report.scan_time = time.time() - start
        scan_report.security_score = engine._compute_security_score(scan_report.findings)
        scan_report.summary = engine._compute_summary(scan_report.findings)
    else:
        scan_report = engine.scan_directory(os.path.abspath(target))

    if output_format == "json":
        content = format_json_report(scan_report)
    else:
        content = format_html_report(scan_report)

    with open(output, "w") as f:
        f.write(content)

    console.print(f"[green]Report saved to {output}[/green]")
    console.print(f"[dim]Found {len(scan_report.findings)} findings[/dim]")


def _output_report(report: ScanReport, output_format: str, output_path: str | None):
    """Output the scan report in the specified format."""
    if output_format == "json":
        result = format_json_report(report)
    elif output_format == "html":
        result = format_html_report(report)
    else:
        result = format_terminal_report(report)

    if output_path:
        with open(output_path, "w") as f:
            f.write(result)
        console.print(f"[green]Report saved to {output_path}[/green]")
    else:
        if output_format == "terminal":
            print(result)
        else:
            console.print(result)


def main():
    cli()


if __name__ == "__main__":
    main()
