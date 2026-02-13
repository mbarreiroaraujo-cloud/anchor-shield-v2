"""
ANCHOR-005: Close + Reinit Lifecycle Attack

Detects when the same account type is used with both close and init_if_needed
constraints within a program. After close zeroes an account, init_if_needed
can "revive" it in the same or subsequent transaction, potentially with
attacker-prepared state.
"""

import re
from scanner.patterns.base import VulnerabilityPattern, Finding


class CloseReinitPattern(VulnerabilityPattern):
    id = "ANCHOR-005"
    name = "Close + Reinit Lifecycle Attack"
    severity = "Medium"
    description = (
        "Same account type is used with both close and init_if_needed constraints, "
        "enabling potential account revival after close with attacker-controlled state."
    )

    def scan(self, file_path: str, content: str) -> list[Finding]:
        findings = []

        close_types = {}
        init_if_needed_types = {}

        for struct_name, struct_body, struct_start in self._find_derive_accounts_structs(content):
            for field in self._parse_struct_fields(struct_body, struct_start):
                base_type = self._extract_account_type(field["type"])
                if not base_type:
                    continue

                if re.search(r"\bclose\s*=", field["attrs"]):
                    close_types[base_type] = (struct_name, field["name"], field["line"])

                if re.search(r"init_if_needed", field["attrs"]):
                    init_if_needed_types[base_type] = (struct_name, field["name"], field["line"])

        overlapping = set(close_types.keys()) & set(init_if_needed_types.keys())

        for acct_type in overlapping:
            close_struct, close_field, close_line = close_types[acct_type]
            init_struct, init_field, init_line = init_if_needed_types[acct_type]

            snippet = self._extract_snippet(content, init_line)

            findings.append(
                Finding(
                    id=self.id,
                    name=self.name,
                    severity=self.severity,
                    file=file_path,
                    line=init_line,
                    description=(
                        f"Account type '{acct_type}' is used with close "
                        f"(in {close_struct}.{close_field}, line {close_line}) and "
                        f"init_if_needed (in {init_struct}.{init_field}, line "
                        f"{init_line}). Attacker can close and revive the account."
                    ),
                    root_cause=self.get_root_cause(),
                    exploit_scenario=self.get_exploit_scenario(),
                    fix_recommendation=self.get_fix_recommendation(),
                    code_snippet=snippet,
                    before_after_state={
                        "before": "Account: initialized, authority=victim",
                        "after": "Account: re-initialized via init_if_needed, authority=attacker",
                        "damage": "Account hijack via close-then-reinit lifecycle attack.",
                    },
                    impact={
                        "attack_cost": "< 0.01 SOL",
                        "exploitability": "Medium — requires close + init_if_needed on same type",
                        "breach_cost_context": "Account revival: $50K-$2M per program.",
                    },
                    anchor_versions_affected="0.25.0 - 0.30.x",
                    ecosystem_recommendations=[
                        "Use plain init instead of init_if_needed",
                        "Add lifecycle state tracking to prevent re-initialization",
                    ],
                )
            )

        return findings

    @staticmethod
    def _extract_account_type(type_str: str) -> str:
        """Extract the inner account type from Account<'info, T>."""
        m = re.search(r"Account\s*<\s*'[^,]+,\s*(\w+)", type_str)
        if m:
            return m.group(1)
        m = re.search(r"InterfaceAccount\s*<\s*'[^,]+,\s*(\w+)", type_str)
        if m:
            return m.group(1)
        return ""

    def get_fix_recommendation(self) -> str:
        return (
            "Use plain init instead of init_if_needed, or add lifecycle state tracking:\n"
            "  constraint = !account.is_closed"
        )

    def get_root_cause(self) -> str:
        return (
            "After close zeroes an account, init_if_needed can re-initialize it "
            "because the account appears uninitialized (system-owned). An attacker "
            "who funds the account between close and init_if_needed controls the "
            "re-initialization."
        )

    def get_exploit_scenario(self) -> str:
        return (
            "1. Attacker calls instruction with close constraint\n"
            "2. Account zeroed, lamports transferred\n"
            "3. Attacker funds account with rent-exempt minimum\n"
            "4. Attacker calls init_if_needed — account re-initialized\n"
            "5. Attacker controls initialization parameters"
        )
