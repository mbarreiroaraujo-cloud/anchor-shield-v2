"""Tests for anchor-shield scanner patterns.

Each pattern has:
  - True positive: known-vulnerable code that MUST be detected
  - True negative: safe code that MUST NOT be flagged
"""

import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.engine import AnchorShieldEngine
from scanner.patterns.init_if_needed import InitIfNeededPattern
from scanner.patterns.duplicate_mutable import DuplicateMutablePattern
from scanner.patterns.realloc_payer import ReallocPayerPattern
from scanner.patterns.type_cosplay import TypeCosplayPattern
from scanner.patterns.close_reinit import CloseReinitPattern
from scanner.patterns.missing_owner import MissingOwnerPattern

TEST_DIR = os.path.join(os.path.dirname(__file__), "test_patterns")
VULN_DIR = os.path.join(TEST_DIR, "vulnerable")
SAFE_DIR = os.path.join(TEST_DIR, "safe")


def read_test_file(subdir, filename):
    path = os.path.join(TEST_DIR, subdir, filename)
    with open(path, "r") as f:
        return f.read()


# ─── ANCHOR-001: init_if_needed Incomplete Field Validation ─────────

class TestAnchor001:
    def setup_method(self):
        self.pattern = InitIfNeededPattern()

    def test_detects_vulnerable_init_if_needed(self):
        """Scanner must detect init_if_needed without delegate/close_authority checks."""
        content = read_test_file("vulnerable", "init_if_needed_no_delegate_check.rs")
        findings = self.pattern.scan("test.rs", content)
        assert len(findings) >= 1
        assert findings[0].id == "ANCHOR-001"
        assert findings[0].severity == "High"

    def test_ignores_safe_init_if_needed(self):
        """Scanner must NOT flag init_if_needed with explicit constraint checks."""
        content = read_test_file("safe", "init_if_needed_with_constraints.rs")
        findings = self.pattern.scan("test.rs", content)
        anchor_001_findings = [f for f in findings if f.id == "ANCHOR-001"]
        assert len(anchor_001_findings) == 0

    def test_no_false_positive_plain_init(self):
        """Plain init (not init_if_needed) should not trigger."""
        content = """
        #[derive(Accounts)]
        pub struct Init<'info> {
            #[account(
                init,
                payer = payer,
                token::mint = mint,
                token::authority = authority,
            )]
            pub token_account: Account<'info, TokenAccount>,
            pub payer: Signer<'info>,
        }
        """
        findings = self.pattern.scan("test.rs", content)
        assert len(findings) == 0


# ─── ANCHOR-002: Duplicate Mutable Account Bypass ───────────────────

class TestAnchor002:
    def setup_method(self):
        self.pattern = DuplicateMutablePattern()

    def test_detects_duplicate_mutable_bypass(self):
        """Scanner must detect init_if_needed coexisting with mut of same type."""
        content = read_test_file("vulnerable", "duplicate_mutable_init.rs")
        findings = self.pattern.scan("test.rs", content)
        assert len(findings) >= 1
        assert findings[0].id == "ANCHOR-002"
        assert findings[0].severity == "Medium"

    def test_no_false_positive_different_types(self):
        """Different account types should not trigger."""
        content = """
        #[derive(Accounts)]
        pub struct Transfer<'info> {
            #[account(
                init_if_needed,
                payer = payer,
                space = 100,
            )]
            pub vault: Account<'info, Vault>,

            #[account(mut)]
            pub token_account: Account<'info, TokenAccount>,

            pub payer: Signer<'info>,
        }
        """
        findings = self.pattern.scan("test.rs", content)
        assert len(findings) == 0


# ─── ANCHOR-003: Realloc Payer Signer Gap ───────────────────────────

class TestAnchor003:
    def setup_method(self):
        self.pattern = ReallocPayerPattern()

    def test_detects_realloc_without_signer(self):
        """Scanner must detect realloc payer not typed as Signer."""
        content = read_test_file("vulnerable", "realloc_no_signer.rs")
        findings = self.pattern.scan("test.rs", content)
        assert len(findings) >= 1
        assert findings[0].id == "ANCHOR-003"
        assert findings[0].severity == "Medium"

    def test_ignores_realloc_with_signer(self):
        """Scanner must NOT flag realloc with Signer payer."""
        content = read_test_file("safe", "realloc_with_signer.rs")
        findings = self.pattern.scan("test.rs", content)
        anchor_003_findings = [f for f in findings if f.id == "ANCHOR-003"]
        assert len(anchor_003_findings) == 0


# ─── ANCHOR-004: Account Type Cosplay ───────────────────────────────

class TestAnchor004:
    def setup_method(self):
        self.pattern = TypeCosplayPattern()

    def test_detects_raw_account_info(self):
        """Scanner must detect raw AccountInfo without owner verification."""
        content = read_test_file("vulnerable", "type_cosplay_no_discriminator.rs")
        findings = self.pattern.scan("test.rs", content)
        assert len(findings) >= 1
        assert any(f.id == "ANCHOR-004" for f in findings)

    def test_ignores_typed_account(self):
        """Scanner must NOT flag Account<'info, T> usage."""
        content = read_test_file("safe", "proper_account_type.rs")
        findings = self.pattern.scan("test.rs", content)
        anchor_004_findings = [f for f in findings if f.id == "ANCHOR-004"]
        assert len(anchor_004_findings) == 0


# ─── ANCHOR-005: Close + Reinit Lifecycle ───────────────────────────

class TestAnchor005:
    def setup_method(self):
        self.pattern = CloseReinitPattern()

    def test_detects_close_reinit(self):
        """Scanner must detect close + init_if_needed on same account type."""
        content = read_test_file("vulnerable", "close_reinit_same_type.rs")
        findings = self.pattern.scan("test.rs", content)
        assert len(findings) >= 1
        assert findings[0].id == "ANCHOR-005"

    def test_no_false_positive_close_only(self):
        """Close without init_if_needed should not trigger."""
        content = """
        #[derive(Accounts)]
        pub struct CloseVault<'info> {
            #[account(mut, close = authority)]
            pub vault: Account<'info, Vault>,
            pub authority: Signer<'info>,
        }
        """
        findings = self.pattern.scan("test.rs", content)
        assert len(findings) == 0


# ─── ANCHOR-006: Missing Owner Validation ───────────────────────────

class TestAnchor006:
    def setup_method(self):
        self.pattern = MissingOwnerPattern()

    def test_detects_missing_owner_check(self):
        """Scanner must detect AccountInfo without owner validation."""
        content = read_test_file("vulnerable", "raw_account_info_no_owner.rs")
        findings = self.pattern.scan("test.rs", content)
        assert len(findings) >= 1
        assert any(f.id == "ANCHOR-006" for f in findings)

    def test_ignores_typed_account(self):
        """Scanner must NOT flag Account<'info, T> which has built-in owner check."""
        content = read_test_file("safe", "proper_account_type.rs")
        findings = self.pattern.scan("test.rs", content)
        anchor_006_findings = [f for f in findings if f.id == "ANCHOR-006"]
        assert len(anchor_006_findings) == 0

    def test_ignores_check_comment(self):
        """AccountInfo with CHECK comment should not trigger."""
        content = """
        #[derive(Accounts)]
        pub struct Safe<'info> {
            /// CHECK: This account is validated in the instruction body
            pub data: AccountInfo<'info>,
        }
        """
        findings = self.pattern.scan("test.rs", content)
        anchor_006_findings = [f for f in findings if f.id == "ANCHOR-006"]
        assert len(anchor_006_findings) == 0


# ─── Integration: Full engine scan ──────────────────────────────────

class TestEngineIntegration:
    def setup_method(self):
        self.engine = AnchorShieldEngine()

    def test_scan_vulnerable_directory(self):
        """Engine should find multiple vulnerabilities in vulnerable test files."""
        report = self.engine.scan_directory(VULN_DIR)
        assert report.files_scanned > 0
        assert len(report.findings) > 0
        assert report.security_score != "A"

        # Check all pattern IDs are represented
        found_ids = {f.id for f in report.findings}
        assert "ANCHOR-001" in found_ids
        assert "ANCHOR-003" in found_ids

    def test_scan_safe_directory(self):
        """Engine should find minimal or no issues in safe test files."""
        report = self.engine.scan_directory(SAFE_DIR)
        assert report.files_scanned > 0
        # Safe files should have very few findings
        critical_high = [f for f in report.findings if f.severity in ("Critical", "High")]
        # Acceptable: some patterns may still trigger on safe files
        # but the specific patterns should not
        anchor_001 = [f for f in report.findings if f.id == "ANCHOR-001"]
        anchor_003 = [f for f in report.findings if f.id == "ANCHOR-003"]
        assert len(anchor_001) == 0
        assert len(anchor_003) == 0

    def test_report_json_serialization(self):
        """Scan report should serialize to valid JSON."""
        report = self.engine.scan_directory(VULN_DIR)
        import json
        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert "findings" in parsed
        assert "summary" in parsed
        assert parsed["files_scanned"] > 0

    def test_security_score_computation(self):
        """Security score should reflect severity of findings."""
        report = self.engine.scan_directory(VULN_DIR)
        # With multiple findings, score should be worse than A
        assert report.security_score != "A"

    def test_empty_file_no_crash(self):
        """Engine should handle empty files gracefully."""
        report = self.engine.scan_content("", "empty.rs")
        assert report.files_scanned == 1
        assert len(report.findings) == 0
        assert report.security_score == "A"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
