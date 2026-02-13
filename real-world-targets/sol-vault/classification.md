# sol-vault — Finding Classification

**Program**: Token vault with interest payments (359 lines)
**Source**: Clish254/sol-vault (community, unaudited)
**Domain**: Token vault / DeFi
**Static scanner findings**: 0

## Manual Semantic Analysis

| ID | Severity | Title | Classification | Reasoning |
|----|----------|-------|---------------|-----------|
| SEM-001 | Medium | Floating-point arithmetic in interest calculation | INFORMATIONAL | `send_interest` uses `0.01 * amount as f64` with `trunc() as u64`. Floating-point precision loss for large token amounts is a defense-in-depth concern but not directly exploitable since the sender consents to the payment. |
| SEM-002 | Low | Accounting variables track cumulative history, not current balance | INFORMATIONAL | `deposited_amount` increases but never decreases on withdrawal. Actual balance check uses `vault_token_account.amount` (on-chain token balance), so this doesn't create a vulnerability. Misleading for off-chain accounting. |
| SEM-003 | Low | Interest compounds on previously sent interest | INFORMATIONAL | Interest is 1% of `vault_token_account.amount`, which includes past interest. Design decision by the protocol, not a bug. Sender explicitly signs each interest payment. |

## Summary

- **True Positives**: 0
- **Likely True Positives**: 0
- **Informational**: 3
- **False Positives**: 0

**Assessment**: Well-structured vault program with proper Anchor constraints, PDA seed derivation, and signer checks. Uses `checked_add` for arithmetic. The interest mechanism uses floating-point which is a code quality concern but not exploitable. The owner constraint `#[account(address = vault.owner)]` correctly ties operations to the vault creator.
