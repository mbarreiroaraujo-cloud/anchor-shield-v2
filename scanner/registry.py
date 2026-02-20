"""
Registry Scanner — Scan Solana programs by their on-chain address.

Uses the OtterSec Verified Programs API (verify.osec.io) to fetch verified
source code and runs anchor-shield-v2 static analysis against it.
"""

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests

from scanner.engine import AnchorShieldEngine, ScanReport

OSEC_API = "https://verify.osec.io"

# Base58 character set used by Solana addresses
BASE58_CHARS = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")

REQUEST_TIMEOUT = 15
CLONE_TIMEOUT = 120


@dataclass
class VerificationStatus:
    """Verification status from OtterSec API."""

    is_verified: bool
    message: str
    on_chain_hash: Optional[str] = None
    executable_hash: Optional[str] = None
    repo_url: Optional[str] = None
    commit: Optional[str] = None
    last_verified_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "is_verified": self.is_verified,
            "message": self.message,
            "on_chain_hash": self.on_chain_hash,
            "executable_hash": self.executable_hash,
            "repo_url": self.repo_url,
            "commit": self.commit,
            "last_verified_at": self.last_verified_at,
        }


@dataclass
class ProgramScanResult:
    """Combined verification + scan result for a program."""

    program_id: str
    verification: VerificationStatus
    scan_reports: list = field(default_factory=list)
    anchor_programs_found: list = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "program_id": self.program_id,
            "verification": self.verification.to_dict(),
            "anchor_programs_found": self.anchor_programs_found,
            "scan_reports": [r.to_dict() for r in self.scan_reports],
            "error": self.error,
        }


def validate_program_id(program_id: str) -> bool:
    """Validate that a string looks like a Solana program ID (base58, 32-44 chars)."""
    if not program_id or len(program_id) < 32 or len(program_id) > 44:
        return False
    return all(c in BASE58_CHARS for c in program_id)


def check_verification(program_id: str) -> VerificationStatus:
    """Check if a Solana program has verified source code via OtterSec API.

    Args:
        program_id: Solana program address (base58).

    Returns:
        VerificationStatus with API response data.

    Raises:
        requests.ConnectionError: If the API is unreachable.
        requests.Timeout: If the API doesn't respond in time.
    """
    url = f"{OSEC_API}/status/{program_id}"
    response = requests.get(url, timeout=REQUEST_TIMEOUT)

    if response.status_code == 404:
        return VerificationStatus(
            is_verified=False,
            message="Program not found in OtterSec registry",
        )

    response.raise_for_status()
    data = response.json()

    return VerificationStatus(
        is_verified=data.get("is_verified", False),
        message=data.get("message", ""),
        on_chain_hash=data.get("on_chain_hash"),
        executable_hash=data.get("executable_hash"),
        repo_url=data.get("repo_url"),
        commit=data.get("commit"),
        last_verified_at=data.get("last_verified_at"),
    )


def clone_verified_source(repo_url: str, commit: str, target_dir: str) -> str:
    """Shallow clone the verified repo and checkout the specific commit.

    Args:
        repo_url: Git repository URL (e.g. https://github.com/org/repo).
        commit: Git commit hash to checkout.
        target_dir: Directory to clone into.

    Returns:
        Path to the cloned repository.

    Raises:
        subprocess.TimeoutExpired: If clone takes too long.
        subprocess.CalledProcessError: If git commands fail.
    """
    # Clone with enough depth to reach the verified commit
    subprocess.run(
        ["git", "clone", "--depth", "50", repo_url, target_dir],
        check=True,
        capture_output=True,
        timeout=CLONE_TIMEOUT,
    )

    # Checkout the specific verified commit
    try:
        subprocess.run(
            ["git", "-C", target_dir, "checkout", commit],
            check=True,
            capture_output=True,
            timeout=30,
        )
    except subprocess.CalledProcessError:
        # If commit not in shallow history, fetch it specifically
        subprocess.run(
            ["git", "-C", target_dir, "fetch", "--depth", "1", "origin", commit],
            check=True,
            capture_output=True,
            timeout=CLONE_TIMEOUT,
        )
        subprocess.run(
            ["git", "-C", target_dir, "checkout", commit],
            check=True,
            capture_output=True,
            timeout=30,
        )

    return target_dir


def find_anchor_programs(repo_dir: str) -> list[str]:
    """Identify Anchor program directories in a cloned repository.

    Searches for Cargo.toml files that declare anchor-lang as a dependency,
    then returns the directories containing those programs.

    Args:
        repo_dir: Path to the cloned repository root.

    Returns:
        List of directory paths containing Anchor programs.
    """
    anchor_dirs = []
    anchor_pattern = re.compile(r'anchor-lang')

    for root, dirs, files in os.walk(repo_dir):
        # Skip build artifacts and hidden directories
        dirs[:] = [
            d for d in dirs
            if d not in ("target", "node_modules", ".git", "dist", "build")
        ]

        if "Cargo.toml" in files:
            cargo_path = os.path.join(root, "Cargo.toml")
            try:
                with open(cargo_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if anchor_pattern.search(content):
                    anchor_dirs.append(root)
            except OSError:
                continue

    return anchor_dirs


def scan_program(program_id: str) -> ProgramScanResult:
    """Full pipeline: verify → clone → find → scan → report.

    Args:
        program_id: Solana program address (base58).

    Returns:
        ProgramScanResult with verification info and scan results.
    """
    # Step 1: Check verification
    try:
        verification = check_verification(program_id)
    except requests.ConnectionError:
        return ProgramScanResult(
            program_id=program_id,
            verification=VerificationStatus(
                is_verified=False,
                message="Could not connect to OtterSec API",
            ),
            error="Could not connect to verify.osec.io. Check your internet connection.",
        )
    except requests.Timeout:
        return ProgramScanResult(
            program_id=program_id,
            verification=VerificationStatus(
                is_verified=False,
                message="OtterSec API timed out",
            ),
            error="Request to verify.osec.io timed out. Try again later.",
        )
    except requests.HTTPError as e:
        return ProgramScanResult(
            program_id=program_id,
            verification=VerificationStatus(
                is_verified=False,
                message=f"OtterSec API error: {e.response.status_code}",
            ),
            error=f"OtterSec API returned HTTP {e.response.status_code}.",
        )

    if not verification.is_verified:
        return ProgramScanResult(
            program_id=program_id,
            verification=verification,
        )

    # Step 2: Clone verified source
    tmp_dir = tempfile.mkdtemp(prefix="anchor-shield-")
    try:
        clone_dir = os.path.join(tmp_dir, "repo")
        try:
            clone_verified_source(verification.repo_url, verification.commit, clone_dir)
        except subprocess.TimeoutExpired:
            return ProgramScanResult(
                program_id=program_id,
                verification=verification,
                error="Repository clone timed out. The repository may be too large.",
            )
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode("utf-8", errors="ignore") if e.stderr else ""
            return ProgramScanResult(
                program_id=program_id,
                verification=verification,
                error=f"Failed to clone repository: {stderr.strip()}",
            )

        # Step 3: Find Anchor programs
        anchor_dirs = find_anchor_programs(clone_dir)

        if not anchor_dirs:
            return ProgramScanResult(
                program_id=program_id,
                verification=verification,
                anchor_programs_found=[],
                error=(
                    "No Anchor programs found in repository. "
                    "This may be a native Solana program (not built with Anchor). "
                    "anchor-shield-v2 is optimized for Anchor framework programs."
                ),
            )

        # Step 4: Scan each Anchor program directory
        engine = AnchorShieldEngine()
        scan_reports = []
        program_names = []

        for program_dir in anchor_dirs:
            rel_path = os.path.relpath(program_dir, clone_dir)
            program_names.append(rel_path)
            report = engine.scan_directory(program_dir)
            # Override target to show relative path instead of temp dir
            report.target = rel_path
            scan_reports.append(report)

        return ProgramScanResult(
            program_id=program_id,
            verification=verification,
            scan_reports=scan_reports,
            anchor_programs_found=program_names,
        )

    finally:
        # Cleanup temp directory
        shutil.rmtree(tmp_dir, ignore_errors=True)
