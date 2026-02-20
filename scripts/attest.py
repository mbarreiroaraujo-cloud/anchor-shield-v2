#!/usr/bin/env python3
"""
Publish a security audit attestation on Solana devnet via SPL Memo.

Creates an immutable, publicly verifiable on-chain record of an
anchor-shield-v2 security analysis.

Usage:
    python scripts/attest.py <REPORT_PATH> [--program-id ID] [--keypair PATH]

Examples:
    python scripts/attest.py SECURITY_REPORT.json
    python scripts/attest.py SECURITY_REPORT.json --program-id whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc
    python scripts/attest.py SECURITY_REPORT.json --keypair attestation/auditor-keypair.json
"""

import argparse
import base64
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from rich.console import Console
from rich.panel import Panel

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message
from solders.instruction import Instruction, AccountMeta
from solders.hash import Hash

console = Console()

# SPL Memo v2 Program ID (deployed on all Solana clusters)
MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")

DEVNET_URL = "https://api.devnet.solana.com"
LAMPORTS_PER_SOL = 1_000_000_000

BANNER = """[bold cyan]
   __ _ _ __   ___| |__   ___  _ __      ___| |__ (_) ___| | __| |
  / _` | '_ \\ / __| '_ \\ / _ \\| '__|____/ __| '_ \\| / _ \\ |/ _` |
 | (_| | | | | (__| | | | (_) | | |_____\\__ \\ | | | |  __/ | (_| |
  \\__,_|_| |_|\\___|_| |_|\\___/|_|       |___/_| |_|_|\\___|_|\\__,_|
[/bold cyan]
[bold]On-Chain Attestation[/bold] — Publish audit results to Solana devnet
[dim]Via SPL Memo program (MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr)[/dim]
"""


def rpc_call(method: str, params: list, retries: int = 3) -> dict:
    """Make a JSON-RPC call to Solana devnet with retries."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    last_error = None
    for attempt in range(retries):
        try:
            resp = requests.post(DEVNET_URL, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if "error" in data:
                    last_error = data["error"]
                    console.print(
                        f"[yellow]RPC error (attempt {attempt + 1}):[/yellow] "
                        f"{data['error'].get('message', data['error'])}"
                    )
                else:
                    return data.get("result", {})
            else:
                last_error = f"HTTP {resp.status_code}"
        except requests.exceptions.RequestException as e:
            last_error = str(e)

        if attempt < retries - 1:
            wait = 2 ** (attempt + 1)
            console.print(f"[dim]Retrying in {wait}s...[/dim]")
            time.sleep(wait)

    raise ConnectionError(f"RPC call {method} failed after {retries} attempts: {last_error}")


def load_or_create_keypair(keypair_path: str) -> Keypair:
    """Load an existing keypair or generate a new one."""
    path = Path(keypair_path)
    if path.exists():
        with open(path) as f:
            secret = json.load(f)
        kp = Keypair.from_bytes(bytes(secret))
        console.print(f"[dim]Loaded keypair from {keypair_path}[/dim]")
        return kp

    # Generate new keypair
    kp = Keypair()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(list(bytes(kp)), f)
    console.print(f"[green]Generated new keypair at {keypair_path}[/green]")
    console.print(f"[dim]Public key: {kp.pubkey()}[/dim]")
    return kp


def ensure_funded(pubkey: Pubkey) -> bool:
    """Check balance and request airdrop if needed. Returns True if funded."""
    try:
        result = rpc_call("getBalance", [str(pubkey), {"commitment": "confirmed"}])
        balance = result.get("value", 0)
        balance_sol = balance / LAMPORTS_PER_SOL
        console.print(f"[dim]Balance: {balance_sol:.4f} SOL[/dim]")

        if balance >= 10_000:  # 0.00001 SOL minimum for a memo tx
            return True

        console.print("[dim]Requesting airdrop of 1 SOL...[/dim]")
        airdrop_result = rpc_call("requestAirdrop", [
            str(pubkey),
            LAMPORTS_PER_SOL,
        ])
        airdrop_sig = airdrop_result

        # Wait for airdrop confirmation
        console.print(f"[dim]Airdrop tx: {airdrop_sig}[/dim]")
        for _ in range(30):
            time.sleep(1)
            status = rpc_call("getSignatureStatuses", [[airdrop_sig]])
            value = status.get("value", [None])[0]
            if value and value.get("confirmationStatus") in ("confirmed", "finalized"):
                console.print("[green]Airdrop confirmed.[/green]")
                return True
        console.print("[yellow]Airdrop confirmation timeout — proceeding anyway.[/yellow]")
        return True

    except ConnectionError as e:
        console.print(f"[yellow]Could not fund wallet: {e}[/yellow]")
        return False


def load_report(report_path: str) -> dict:
    """Load and parse the security report."""
    with open(report_path) as f:
        return json.load(f)


def compute_report_hash(report: dict) -> str:
    """Compute SHA256 hash of the report (deterministic)."""
    # Hash the original report without attestation field
    report_copy = {k: v for k, v in report.items() if k != "attestation"}
    canonical = json.dumps(report_copy, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def extract_findings(report: dict) -> dict:
    """Extract severity counts from the report."""
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}

    # Semantic analysis findings
    semantic = report.get("semantic_analysis", {})
    for finding in semantic.get("findings", []):
        sev = finding.get("severity", "")
        if sev in counts:
            counts[sev] += 1

    # Static analysis findings
    static = report.get("static_analysis", {})
    for finding in static.get("findings", []):
        sev = finding.get("severity", "")
        if sev in counts:
            counts[sev] += 1

    return counts


def compute_severity_score(counts: dict) -> int:
    """Compute a 0-100 severity score based on finding counts."""
    score = (
        counts["Critical"] * 25
        + counts["High"] * 10
        + counts["Medium"] * 3
        + counts["Low"] * 1
    )
    return min(100, score)


def determine_status(score: int) -> str:
    """Determine audit status from severity score."""
    if score == 0:
        return "PASS"
    elif score < 50:
        return "WARN"
    else:
        return "FAIL"


def extract_program_id(report: dict) -> str:
    """Try to extract a program ID from the report metadata."""
    target = report.get("meta", {}).get("target", "")
    # Use target directory name as a fallback identifier
    if target:
        return Path(target).name
    return "unknown"


def build_memo(
    program_id: str,
    report_hash: str,
    severity_score: int,
    status: str,
    counts: dict,
    version: str = "v0.5.1",
) -> str:
    """Build the memo string for on-chain attestation."""
    timestamp = int(time.time())
    findings_str = (
        f"{counts['Critical']}c"
        f"{counts['High']}h"
        f"{counts['Medium']}m"
        f"{counts['Low']}l"
    )
    return (
        f"ANCHOR-SHIELD-AUDIT|{program_id}|{report_hash[:16]}"
        f"|{timestamp}|{severity_score}/100|{status}"
        f"|{findings_str}|anchor-shield-v2-{version}"
    )


def send_memo_transaction(keypair: Keypair, memo: str) -> str:
    """Build, sign, and send a memo transaction to devnet. Returns tx signature."""
    # Get recent blockhash
    bh_result = rpc_call("getLatestBlockhash", [{"commitment": "confirmed"}])
    blockhash_str = bh_result["value"]["blockhash"]
    last_valid_height = bh_result["value"]["lastValidBlockHeight"]
    blockhash = Hash.from_string(blockhash_str)

    # Build memo instruction
    memo_ix = Instruction(
        MEMO_PROGRAM_ID,
        memo.encode("utf-8"),
        [AccountMeta(keypair.pubkey(), is_signer=True, is_writable=True)],
    )

    # Build and sign transaction
    msg = Message.new_with_blockhash([memo_ix], keypair.pubkey(), blockhash)
    tx = Transaction.new_unsigned(msg)
    tx.sign([keypair], blockhash)

    # Serialize and send
    tx_bytes = bytes(tx)
    tx_b64 = base64.b64encode(tx_bytes).decode("ascii")

    result = rpc_call("sendTransaction", [
        tx_b64,
        {"encoding": "base64", "skipPreflight": False, "preflightCommitment": "confirmed"},
    ])
    tx_signature = result
    console.print(f"[dim]Transaction sent: {tx_signature}[/dim]")

    # Confirm transaction
    console.print("[dim]Confirming transaction...[/dim]")
    for _ in range(60):
        time.sleep(0.5)
        status = rpc_call("getSignatureStatuses", [[tx_signature]])
        value = status.get("value", [None])[0]
        if value:
            if value.get("err"):
                raise RuntimeError(f"Transaction failed: {value['err']}")
            if value.get("confirmationStatus") in ("confirmed", "finalized"):
                console.print("[green]Transaction confirmed![/green]")
                return tx_signature
    raise TimeoutError(f"Transaction {tx_signature} not confirmed within 30 seconds")


def update_report(report_path: str, report: dict, attestation_data: dict):
    """Add attestation field to the report, preserving existing content."""
    report["attestation"] = attestation_data
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    console.print(f"[green]Report updated:[/green] {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Publish a security audit attestation on Solana devnet.",
        epilog="Creates a verifiable on-chain record via SPL Memo program.",
    )
    parser.add_argument(
        "report_path",
        help="Path to SECURITY_REPORT.json",
    )
    parser.add_argument(
        "--program-id",
        default=None,
        help="Solana program ID being audited (default: extracted from report)",
    )
    parser.add_argument(
        "--keypair",
        default="attestation/auditor-keypair.json",
        help="Path to auditor keypair JSON (default: attestation/auditor-keypair.json)",
    )

    args = parser.parse_args()
    console.print(BANNER)

    # 1. Load report
    if not os.path.exists(args.report_path):
        console.print(f"[bold red]Error:[/bold red] Report not found: {args.report_path}")
        sys.exit(1)

    report = load_report(args.report_path)
    console.print(f"[dim]Loaded report: {args.report_path}[/dim]")

    # 2. Extract data
    report_hash = compute_report_hash(report)
    counts = extract_findings(report)
    severity_score = compute_severity_score(counts)
    status = determine_status(severity_score)
    program_id = args.program_id or extract_program_id(report)
    version = report.get("meta", {}).get("version", "0.5.1")

    # 3. Build memo
    memo = build_memo(program_id, report_hash, severity_score, status, counts, f"v{version}")

    # Display summary
    console.print()
    console.print(Panel(
        f"[bold]Program audited:[/bold]  {program_id}\n"
        f"[bold]Report hash:[/bold]      {report_hash[:16]}\n"
        f"[bold]Severity score:[/bold]   {severity_score}/100\n"
        f"[bold]Findings:[/bold]         "
        f"{counts['Critical']} Critical, {counts['High']} High, "
        f"{counts['Medium']} Medium, {counts['Low']} Low\n"
        f"[bold]Status:[/bold]           {status}\n"
        f"[bold]Memo:[/bold]             {memo}",
        title="Attestation Summary",
        border_style="cyan",
    ))
    console.print()

    # 4. Load/create keypair
    keypair = load_or_create_keypair(args.keypair)
    console.print(f"[bold]Auditor pubkey:[/bold] {keypair.pubkey()}")
    console.print()

    # 5. Ensure wallet is funded
    console.print("[bold cyan]Publishing security attestation to Solana devnet...[/bold cyan]")
    console.print()

    funded = ensure_funded(keypair.pubkey())
    if not funded:
        console.print()
        console.print(Panel(
            "[bold yellow]Could not connect to Solana devnet.[/bold yellow]\n\n"
            "The attestation script is fully functional but requires\n"
            "network access to api.devnet.solana.com.\n\n"
            "[bold]To publish the attestation manually:[/bold]\n"
            f"  1. Run: solana airdrop 1 {keypair.pubkey()} --url devnet\n"
            f"  2. Run: python scripts/attest.py {args.report_path}"
            + (f" --program-id {program_id}" if args.program_id else "")
            + "\n\n"
            "[dim]The keypair has been saved for reuse.[/dim]",
            title="Network Unavailable",
            border_style="yellow",
        ))

        # Save attestation metadata without tx (for documentation)
        attestation_data = {
            "status": "pending",
            "cluster": "devnet",
            "memo": memo,
            "report_hash": report_hash,
            "severity_score": severity_score,
            "audit_status": status,
            "auditor_pubkey": str(keypair.pubkey()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "Attestation prepared but not yet published (network unavailable). "
                    "Run the script again with devnet access to publish.",
        }
        update_report(args.report_path, report, attestation_data)
        sys.exit(0)

    # 6. Send transaction
    try:
        tx_signature = send_memo_transaction(keypair, memo)
        explorer_url = f"https://explorer.solana.com/tx/{tx_signature}?cluster=devnet"

        console.print()
        console.print(Panel(
            f"[bold green]Attestation published![/bold green]\n\n"
            f"[bold]Transaction:[/bold]  {tx_signature}\n"
            f"[bold]Explorer:[/bold]     {explorer_url}\n"
            f"[bold]Memo:[/bold]         {memo}",
            title="Success",
            border_style="green",
        ))

        # 7. Update report with attestation data
        attestation_data = {
            "tx_signature": tx_signature,
            "explorer_url": explorer_url,
            "cluster": "devnet",
            "memo": memo,
            "report_hash": report_hash,
            "severity_score": severity_score,
            "audit_status": status,
            "auditor_pubkey": str(keypair.pubkey()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        update_report(args.report_path, report, attestation_data)

    except (ConnectionError, RuntimeError, TimeoutError) as e:
        console.print(f"\n[bold red]Transaction failed:[/bold red] {e}")
        console.print(
            "[dim]The memo was prepared but the transaction could not be confirmed.\n"
            "Try again later or check Solana devnet status.[/dim]"
        )

        # Save partial attestation
        attestation_data = {
            "status": "failed",
            "cluster": "devnet",
            "memo": memo,
            "report_hash": report_hash,
            "severity_score": severity_score,
            "audit_status": status,
            "auditor_pubkey": str(keypair.pubkey()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }
        update_report(args.report_path, report, attestation_data)
        sys.exit(1)


if __name__ == "__main__":
    main()
