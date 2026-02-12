"""Exploit synthesizer that generates proof-of-concept attack code.

Takes a SemanticFinding and the vulnerable source code, then generates
a self-contained Python simulation that demonstrates the exploit
step by step with concrete state transitions and assertions.
"""

import json
import os
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, asdict
from typing import List, Optional

from semantic.analyzer import SemanticFinding
from semantic.prompts import EXPLOIT_GENERATOR_SYSTEM_PROMPT


@dataclass
class ExploitCode:
    """A generated exploit proof-of-concept."""

    finding_id: str
    title: str
    language: str
    code: str
    setup_instructions: str
    expected_result: str
    status: str  # GENERATED, CONFIRMED, FAILED, SIMULATED

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# Pre-built exploit simulations for demo mode.
# Each simulates the vulnerable lending pool logic in Python and
# demonstrates the exploit with concrete state transitions.

_EXPLOIT_COLLATERAL_BYPASS = '''"""Exploit PoC: Collateral check ignores existing debt (SEM-001).

Demonstrates that the borrow function allows unlimited borrowing
because it only checks deposited >= amount without considering
cumulative debt.
"""
from dataclasses import dataclass


@dataclass
class Pool:
    """Simulates the on-chain Pool account."""
    total_deposits: int = 0
    total_borrows: int = 0
    interest_rate: int = 500  # basis points


@dataclass
class UserAccount:
    """Simulates the on-chain UserAccount."""
    deposited: int = 0
    borrowed: int = 0


def deposit(pool: Pool, user: UserAccount, amount: int) -> None:
    """Simulates the deposit instruction."""
    user.deposited += amount
    pool.total_deposits += amount
    print(f"  deposit({amount}) -> deposited={user.deposited}, pool_deposits={pool.total_deposits}")


def borrow_vulnerable(pool: Pool, user: UserAccount, amount: int) -> bool:
    """Simulates the VULNERABLE borrow instruction.

    BUG: Only checks deposited >= amount, ignores existing borrows.
    """
    # This is the vulnerable check — should include user.borrowed
    if user.deposited >= amount:
        user.borrowed += amount
        pool.total_borrows += amount
        print(f"  borrow({amount}) -> APPROVED (deposited {user.deposited} >= {amount})")
        print(f"    cumulative debt: {user.borrowed}, pool_borrows: {pool.total_borrows}")
        return True
    else:
        print(f"  borrow({amount}) -> REJECTED")
        return False


def borrow_fixed(pool: Pool, user: UserAccount, amount: int) -> bool:
    """What the CORRECT borrow check should look like."""
    if user.deposited * 75 // 100 >= user.borrowed + amount:
        user.borrowed += amount
        pool.total_borrows += amount
        return True
    return False


def main():
    print("=" * 60)
    print("EXPLOIT: Collateral Check Ignores Existing Debt")
    print("=" * 60)

    pool = Pool()
    attacker = UserAccount()
    vault_balance = 1000  # Other users deposited 1000 SOL

    # Step 1: Attacker deposits 100 SOL
    print("\\nStep 1: Attacker deposits 100 SOL")
    deposit(pool, attacker, 100)

    # Step 2: Borrow 100 SOL — should this pass?
    print("\\nStep 2: First borrow of 100 SOL")
    assert borrow_vulnerable(pool, attacker, 100), "First borrow should pass"
    vault_balance -= 100

    # Step 3: Borrow 100 SOL AGAIN — this should fail but doesn't
    print("\\nStep 3: Second borrow of 100 SOL (BUG: passes despite existing debt)")
    assert borrow_vulnerable(pool, attacker, 100), "Second borrow passes due to bug"
    vault_balance -= 100

    # Step 4: Borrow a third time
    print("\\nStep 4: Third borrow of 100 SOL (BUG: still passes)")
    assert borrow_vulnerable(pool, attacker, 100), "Third borrow passes due to bug"
    vault_balance -= 100

    # Verify exploit succeeded
    print("\\n" + "=" * 60)
    print("EXPLOIT RESULT:")
    print(f"  Attacker deposited:  100 SOL")
    print(f"  Attacker borrowed:   {attacker.borrowed} SOL")
    print(f"  Vault drained:       {300} SOL")
    print(f"  Debt ratio:          {attacker.borrowed / attacker.deposited:.0%} (should be <= 75%)")

    assert attacker.borrowed > attacker.deposited, (
        f"Exploit confirmed: borrowed {attacker.borrowed} > deposited {attacker.deposited}"
    )
    print("\\n  >>> EXPLOIT CONFIRMED: Unlimited borrowing with fixed collateral <<<")
    print("=" * 60)


if __name__ == "__main__":
    main()
'''

_EXPLOIT_WITHDRAW_DRAIN = '''"""Exploit PoC: Withdrawal allows full exit with outstanding borrows (SEM-002).

Demonstrates that a user can deposit collateral, borrow against it,
then withdraw ALL collateral — leaving the protocol with bad debt.
"""
from dataclasses import dataclass


@dataclass
class Pool:
    """Simulates the on-chain Pool account."""
    total_deposits: int = 0
    total_borrows: int = 0


@dataclass
class UserAccount:
    """Simulates the on-chain UserAccount."""
    deposited: int = 0
    borrowed: int = 0


def deposit(pool: Pool, user: UserAccount, amount: int) -> None:
    """Simulates the deposit instruction."""
    user.deposited += amount
    pool.total_deposits += amount
    print(f"  deposit({amount}) -> deposited={user.deposited}")


def borrow(pool: Pool, user: UserAccount, amount: int) -> bool:
    """Simulates the borrow instruction (with bug 1 present)."""
    if user.deposited >= amount:
        user.borrowed += amount
        pool.total_borrows += amount
        print(f"  borrow({amount}) -> APPROVED, total_debt={user.borrowed}")
        return True
    return False


def withdraw_vulnerable(pool: Pool, user: UserAccount, amount: int) -> bool:
    """Simulates the VULNERABLE withdraw instruction.

    BUG: Only checks deposited >= amount, does NOT verify remaining
    collateral covers outstanding borrows.
    """
    if user.deposited >= amount:
        user.deposited -= amount
        pool.total_deposits -= amount
        print(f"  withdraw({amount}) -> APPROVED (deposited was {user.deposited + amount} >= {amount})")
        print(f"    remaining deposits: {user.deposited}, outstanding debt: {user.borrowed}")
        return True
    else:
        print(f"  withdraw({amount}) -> REJECTED")
        return False


def main():
    print("=" * 60)
    print("EXPLOIT: Withdrawal With Outstanding Borrows")
    print("=" * 60)

    pool = Pool(total_deposits=1000)  # Pre-existing deposits
    attacker = UserAccount()
    attacker_wallet = 100  # Attacker starts with 100 SOL

    # Step 1: Deposit 100 SOL
    print("\\nStep 1: Attacker deposits 100 SOL as collateral")
    deposit(pool, attacker, 100)
    attacker_wallet -= 100
    print(f"  Wallet balance: {attacker_wallet} SOL")

    # Step 2: Borrow 90 SOL
    print("\\nStep 2: Borrow 90 SOL against collateral")
    assert borrow(pool, attacker, 90)
    attacker_wallet += 90
    print(f"  Wallet balance: {attacker_wallet} SOL")

    # Step 3: Withdraw ALL 100 SOL (this should fail but doesn't)
    print("\\nStep 3: Withdraw 100 SOL (BUG: ignores outstanding 90 SOL debt)")
    assert withdraw_vulnerable(pool, attacker, 100), "Withdraw should pass due to bug"
    attacker_wallet += 100
    print(f"  Wallet balance: {attacker_wallet} SOL")

    # Verify exploit succeeded
    print("\\n" + "=" * 60)
    print("EXPLOIT RESULT:")
    print(f"  Attacker started with:  100 SOL")
    print(f"  Attacker now has:       {attacker_wallet} SOL")
    print(f"  Attacker profit:        {attacker_wallet - 100} SOL (pure theft)")
    print(f"  Protocol bad debt:      {attacker.borrowed} SOL (unrecoverable)")
    print(f"  Attacker collateral:    {attacker.deposited} SOL (withdrawn everything)")

    assert attacker_wallet > 100, f"Attacker profited: {attacker_wallet} > 100"
    assert attacker.deposited == 0, "Attacker withdrew all collateral"
    assert attacker.borrowed == 90, "Debt still exists but is unrecoverable"
    print("\\n  >>> EXPLOIT CONFIRMED: Full exit with outstanding borrows <<<")
    print("=" * 60)


if __name__ == "__main__":
    main()
'''

_EXPLOIT_OVERFLOW_LIQUIDATION = '''"""Exploit PoC: Integer overflow in liquidation interest calc (SEM-003).

Demonstrates that the multiplication borrowed * interest_rate * total_borrows
can overflow u64, wrapping to a small number and making unhealthy positions
appear healthy — preventing liquidation.
"""
from dataclasses import dataclass
import ctypes


@dataclass
class Pool:
    """Simulates the on-chain Pool account."""
    total_deposits: int = 0
    total_borrows: int = 0
    interest_rate: int = 500  # 5% in basis points


@dataclass
class UserAccount:
    """Simulates the on-chain UserAccount."""
    deposited: int = 0
    borrowed: int = 0


# Simulate Rust u64 overflow behavior
U64_MAX = (1 << 64) - 1


def u64_mul(a: int, b: int) -> int:
    """Simulates unchecked u64 multiplication (wrapping on overflow)."""
    return (a * b) & U64_MAX


def liquidate_vulnerable(pool: Pool, user: UserAccount) -> dict:
    """Simulates the VULNERABLE liquidate instruction.

    BUG: Unchecked multiplication can overflow, making interest ~0.
    """
    # This is the vulnerable calculation
    interest = u64_mul(u64_mul(user.borrowed, pool.interest_rate), pool.total_borrows)
    denominator = (user.borrowed + interest) & U64_MAX

    if denominator == 0:
        return {"error": "division by zero", "health": None}

    health = (user.deposited * 100) // denominator
    return {"interest": interest, "health": health, "can_liquidate": health < 75}


def liquidate_correct(pool: Pool, user: UserAccount) -> dict:
    """What the CORRECT liquidation check should look like."""
    # Using Python arbitrary precision (no overflow)
    interest = user.borrowed * pool.interest_rate * pool.total_borrows
    denominator = user.borrowed + interest
    if denominator == 0:
        return {"error": "division by zero", "health": None}
    health = (user.deposited * 100) // denominator
    return {"interest": interest, "health": health, "can_liquidate": health < 75}


def main():
    print("=" * 60)
    print("EXPLOIT: Integer Overflow Prevents Liquidation")
    print("=" * 60)

    # Set up a scenario where overflow occurs
    pool = Pool(
        total_borrows=10_000_000_000_000,  # 10 trillion lamports in total borrows
        interest_rate=500,
    )

    underwater_user = UserAccount(
        deposited=1_000_000,       # 0.001 SOL deposited
        borrowed=100_000_000_000,  # 100 SOL borrowed — clearly underwater
    )

    print("\\nScenario: User borrowed 100 SOL with only 0.001 SOL collateral")
    print(f"  deposited:     {underwater_user.deposited} lamports")
    print(f"  borrowed:      {underwater_user.borrowed} lamports")
    print(f"  pool borrows:  {pool.total_borrows} lamports")
    print(f"  interest rate: {pool.interest_rate} bps")

    # Step 1: Show what the correct calculation gives
    print("\\nStep 1: Correct calculation (no overflow)")
    correct = liquidate_correct(pool, underwater_user)
    print(f"  interest:      {correct['interest']}")
    print(f"  health factor: {correct['health']}")
    print(f"  can liquidate: {correct['can_liquidate']}")

    # Step 2: Show what the vulnerable calculation gives
    print("\\nStep 2: Vulnerable calculation (u64 overflow)")
    vuln = liquidate_vulnerable(pool, underwater_user)
    print(f"  interest:      {vuln['interest']} (overflowed!)")
    print(f"  health factor: {vuln['health']}")
    print(f"  can liquidate: {vuln['can_liquidate']}")

    # Step 3: Demonstrate the discrepancy
    print("\\n" + "=" * 60)
    print("EXPLOIT RESULT:")
    print(f"  Correct health factor:    {correct['health']} (should be liquidatable)")
    print(f"  Vulnerable health factor: {vuln['health']} (overflow prevents liquidation)")

    # The vulnerable calculation should show the position as healthy
    # when it's actually deeply underwater
    assert correct['can_liquidate'], "Correct calc says: CAN liquidate"
    assert not vuln['can_liquidate'], "Vulnerable calc says: CANNOT liquidate (overflow)"
    print("\\n  >>> EXPLOIT CONFIRMED: Overflow prevents liquidation of underwater position <<<")
    print("=" * 60)


if __name__ == "__main__":
    main()
'''


class ExploitSynthesizer:
    """Generates exploit proof-of-concept code for semantic findings.

    Takes a vulnerability finding and the source code, then produces
    a self-contained Python simulation that demonstrates the attack.
    Uses the Claude API when available, falls back to pre-built exploits.
    """

    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"
    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    # Map finding titles to pre-built exploits
    _PREBUILT_EXPLOITS = {
        "collateral": _EXPLOIT_COLLATERAL_BYPASS,
        "withdraw": _EXPLOIT_WITHDRAW_DRAIN,
        "overflow": _EXPLOIT_OVERFLOW_LIQUIDATION,
    }

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the exploit synthesizer.

        Args:
            api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
            model: Model to use. Defaults to claude-sonnet-4-20250514.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model or self.DEFAULT_MODEL
        self._demo_mode = False

    @property
    def is_demo_mode(self) -> bool:
        """Whether the last generation used pre-built exploits."""
        return self._demo_mode

    def generate_exploit(
        self, source_code: str, finding: SemanticFinding
    ) -> Optional[ExploitCode]:
        """Generate an exploit PoC for a finding.

        Args:
            source_code: The vulnerable program source code.
            finding: The semantic finding to exploit.

        Returns:
            ExploitCode with the generated proof-of-concept, or None on failure.
        """
        # Try live API generation
        if self.api_key:
            code = self._call_api(source_code, finding)
            if code:
                return ExploitCode(
                    finding_id=finding.id,
                    title=finding.title,
                    language="python",
                    code=code,
                    setup_instructions="python3 <exploit_file>.py",
                    expected_result=f"Demonstrates: {finding.title}",
                    status="GENERATED",
                )

        # Fall back to pre-built exploits
        return self._get_prebuilt_exploit(finding)

    def generate_all(
        self, source_code: str, findings: List[SemanticFinding]
    ) -> List[ExploitCode]:
        """Generate exploits for all Critical/High findings.

        Args:
            source_code: The vulnerable program source code.
            findings: List of semantic findings.

        Returns:
            List of ExploitCode objects for Critical and High severity findings.
        """
        exploits = []
        for finding in findings:
            if finding.severity not in ("Critical", "High"):
                continue
            exploit = self.generate_exploit(source_code, finding)
            if exploit:
                exploits.append(exploit)
        return exploits

    def _call_api(self, source_code: str, finding: SemanticFinding) -> Optional[str]:
        """Call the Claude API to generate exploit code."""
        user_message = (
            f"Generate a Python exploit simulation for this vulnerability:\n\n"
            f"Title: {finding.title}\n"
            f"Severity: {finding.severity}\n"
            f"Function: {finding.function}\n"
            f"Description: {finding.description}\n"
            f"Attack scenario: {finding.attack_scenario}\n\n"
            f"Vulnerable program source:\n```rust\n{source_code}\n```"
        )

        payload = json.dumps({
            "model": self.model,
            "max_tokens": 4096,
            "system": EXPLOIT_GENERATOR_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_message}],
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
        }

        delay = self.RETRY_DELAY
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                req = urllib.request.Request(
                    self.API_URL, data=payload, headers=headers, method="POST"
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    body = json.loads(resp.read().decode("utf-8"))

                text = ""
                for block in body.get("content", []):
                    if block.get("type") == "text":
                        text += block["text"]

                # Strip markdown fences
                code = text.strip()
                if code.startswith("```"):
                    first_nl = code.index("\n")
                    code = code[first_nl + 1:]
                if code.endswith("```"):
                    code = code[:-3]

                return code.strip()

            except (urllib.error.HTTPError, urllib.error.URLError,
                    TimeoutError, OSError) as e:
                print(f"    [attempt {attempt}/{self.MAX_RETRIES}] API error: {e}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(delay)
                    delay *= 2

        return None

    def _get_prebuilt_exploit(self, finding: SemanticFinding) -> Optional[ExploitCode]:
        """Match a finding to a pre-built exploit simulation."""
        self._demo_mode = True
        title_lower = finding.title.lower()

        for keyword, code in self._PREBUILT_EXPLOITS.items():
            if keyword in title_lower:
                return ExploitCode(
                    finding_id=finding.id,
                    title=finding.title,
                    language="python",
                    code=code,
                    setup_instructions="python3 <exploit_file>.py",
                    expected_result=f"Demonstrates: {finding.title}",
                    status="GENERATED",
                )

        return None
