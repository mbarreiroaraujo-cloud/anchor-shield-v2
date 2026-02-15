# Classification: anchor-cashiers-check

- **Source**: coral-xyz/anchor (tests/cashiers-check)
- **Domain**: Escrow / cashier's check
- **Lines**: 180
- **Static findings**: 5 (3x ANCHOR-006, 2x ANCHOR-004)
- **Semantic findings**: 3

## Findings

| ID | Severity | Title | Classification | Reasoning |
|----|----------|-------|---------------|-----------|
| SEM-001 | Medium | owner in CreateCheck is AccountInfo without Signer | INFORMATIONAL | CPI to token::transfer uses owner as authority, so SPL token program enforces signer check implicitly. Not exploitable. |
| SEM-002 | Medium | token_program is AccountInfo, not Program<Token> | INFORMATIONAL | A fake token_program can't modify SPL token accounts (Solana ownership model). CPI would fail or have no effect on real token accounts. Defense-in-depth concern. |
| SEM-003 | Low | vault in CashCheck/CancelCheck is AccountInfo | INFORMATIONAL | Validated by has_one = vault constraint on check account, plus PDA signer CPI. |

## Assessment

0 true positives, 3 informational. Well-designed escrow program. Static scanner's 5 findings are from older Anchor patterns (AccountInfo for CPI passthrough, program fields) which are implicitly validated by CPI constraints.
