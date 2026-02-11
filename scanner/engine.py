"""Core scanning engine for anchor-shield."""

import os
import re
import json
import time
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from scanner.patterns import ALL_PATTERNS
from scanner.patterns.base import Finding


@dataclass
class ScanReport:
    """Aggregated scan results."""

    target: str
    scan_time: float = 0.0
    files_scanned: int = 0
    patterns_checked: int = 0
    findings: list = field(default_factory=list)
    anchor_version: Optional[str] = None
    security_score: str = "A"
    summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "scan_time_seconds": round(self.scan_time, 2),
            "files_scanned": self.files_scanned,
            "patterns_checked": self.patterns_checked,
            "anchor_version": self.anchor_version,
            "security_score": self.security_score,
            "summary": self.summary,
            "findings": [f.to_dict() for f in self.findings],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class AnchorShieldEngine:
    """Main scanning engine that runs vulnerability patterns against Anchor code."""

    def __init__(self):
        self.patterns = [PatternClass() for PatternClass in ALL_PATTERNS]

    def scan_directory(self, path: str) -> ScanReport:
        """Scan all .rs files in a directory for vulnerability patterns."""
        start = time.time()
        path = os.path.abspath(path)

        if not os.path.isdir(path):
            if os.path.isfile(path):
                return self.scan_file(path)
            raise FileNotFoundError(f"Path not found: {path}")

        # Find all .rs files
        rs_files = []
        for root, _, files in os.walk(path):
            # Skip target/ and node_modules/
            if "target" in root.split(os.sep) or "node_modules" in root.split(os.sep):
                continue
            for f in files:
                if f.endswith(".rs"):
                    rs_files.append(os.path.join(root, f))

        # Detect Anchor version
        anchor_version = self._detect_anchor_version(path)

        # Scan each file
        all_findings = []
        for rs_file in rs_files:
            try:
                with open(rs_file, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
            except (OSError, IOError):
                continue

            # Make path relative for display
            rel_path = os.path.relpath(rs_file, path)

            for pattern in self.patterns:
                try:
                    findings = pattern.scan(rel_path, content)
                    all_findings.extend(findings)
                except Exception:
                    pass

        elapsed = time.time() - start

        report = ScanReport(
            target=path,
            scan_time=elapsed,
            files_scanned=len(rs_files),
            patterns_checked=len(self.patterns),
            findings=all_findings,
            anchor_version=anchor_version,
        )

        report.security_score = self._compute_security_score(all_findings)
        report.summary = self._compute_summary(all_findings)

        return report

    def scan_file(self, file_path: str) -> ScanReport:
        """Scan a single .rs file."""
        start = time.time()
        file_path = os.path.abspath(file_path)

        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()

        all_findings = []
        for pattern in self.patterns:
            try:
                findings = pattern.scan(os.path.basename(file_path), content)
                all_findings.extend(findings)
            except Exception:
                pass

        elapsed = time.time() - start

        report = ScanReport(
            target=file_path,
            scan_time=elapsed,
            files_scanned=1,
            patterns_checked=len(self.patterns),
            findings=all_findings,
        )

        report.security_score = self._compute_security_score(all_findings)
        report.summary = self._compute_summary(all_findings)

        return report

    def scan_content(self, content: str, filename: str = "<input>") -> ScanReport:
        """Scan raw content string."""
        start = time.time()
        all_findings = []

        for pattern in self.patterns:
            try:
                findings = pattern.scan(filename, content)
                all_findings.extend(findings)
            except Exception:
                pass

        elapsed = time.time() - start

        report = ScanReport(
            target=filename,
            scan_time=elapsed,
            files_scanned=1,
            patterns_checked=len(self.patterns),
            findings=all_findings,
        )

        report.security_score = self._compute_security_score(all_findings)
        report.summary = self._compute_summary(all_findings)

        return report

    def _detect_anchor_version(self, path: str) -> Optional[str]:
        """Detect Anchor version from Cargo.toml files."""
        for root, _, files in os.walk(path):
            if "target" in root.split(os.sep):
                continue
            for f in files:
                if f == "Cargo.toml":
                    try:
                        with open(os.path.join(root, f), "r") as fh:
                            content = fh.read()
                        m = re.search(
                            r'anchor-lang\s*=\s*["\']?([0-9]+\.[0-9]+\.[0-9]+)',
                            content,
                        )
                        if m:
                            return m.group(1)
                        m = re.search(
                            r'anchor-lang\s*=\s*\{[^}]*version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"',
                            content,
                        )
                        if m:
                            return m.group(1)
                    except (OSError, IOError):
                        continue
        return None

    @staticmethod
    def _compute_security_score(findings: list[Finding]) -> str:
        """Compute an overall security score based on findings."""
        if not findings:
            return "A"

        severity_weights = {"Critical": 10, "High": 5, "Medium": 2, "Low": 1}
        total = sum(
            severity_weights.get(f.severity, 0) for f in findings
        )

        if total >= 20:
            return "F"
        elif total >= 15:
            return "D"
        elif total >= 10:
            return "C"
        elif total >= 5:
            return "B"
        else:
            return "B+"

    @staticmethod
    def _compute_summary(findings: list[Finding]) -> dict:
        """Compute summary statistics."""
        by_severity = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        by_pattern = {}

        for f in findings:
            by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
            by_pattern[f.id] = by_pattern.get(f.id, 0) + 1

        return {
            "total": len(findings),
            "by_severity": by_severity,
            "by_pattern": by_pattern,
        }
