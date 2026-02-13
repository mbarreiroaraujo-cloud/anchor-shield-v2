# Classification: anchor-cfo

- **Source**: coral-xyz/anchor (tests/cfo)
- **Domain**: Serum DEX fee collection and distribution
- **Lines**: 995 (marked WIP)
- **Static findings**: 36 (all from UncheckedAccount for DEX CPI passthrough)
- **Semantic findings**: 3

## Findings

| ID | Severity | Title | Classification | Reasoning |
|----|----------|-------|---------------|-----------|
| SEM-001 | Low | Distribution rounding loss | INFORMATIONAL | `total_fees * percent / 100` for each category leaves dust in vault due to integer division. Dust stays in srm_vault, not extractable. |
| SEM-002 | Medium | UncheckedAccount for DEX market accounts | INFORMATIONAL | Source explicitly comments: "DexAccounts are safe because they are used for CPI only. They are not read or written and so are not validated." Standard CPI passthrough pattern — Serum DEX program does validation. |
| SEM-003 | Low | u8 overflow in distribution validation | INFORMATIONAL | `d.burn + d.stake + d.treasury != 100` uses wrapping u8 arithmetic. Inputs summing to 356 mod 256 = 100 pass validation, but actual distribution would exceed vault balance, failing at CPI level. Not exploitable. |

## Assessment

0 true positives, 3 informational. Complex program with good architecture: PDA-controlled vaults, authority-gated configuration, anti-sandwich protection (is_not_trading), and proper CPI delegation to Serum DEX. Static scanner's 36 findings are all from UncheckedAccount fields explicitly intended for CPI passthrough.

Notable: The is_not_trading() function checks that only one instruction exists in the transaction, preventing sandwich attacks on swap operations. Well-designed defense.
