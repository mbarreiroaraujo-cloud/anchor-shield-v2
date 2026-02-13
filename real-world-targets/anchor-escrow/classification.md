# anchor-escrow — Finding Classification

**Program**: Token escrow (260 lines)
**Source**: coral-xyz/anchor test suite
**Domain**: Escrow / token swap
**Static scanner findings**: 0

## Manual Semantic Analysis

| ID | Severity | Title | Classification | Reasoning |
|----|----------|-------|---------------|-----------|
| SEM-001 | High | Missing Signer constraint on cancel_escrow initializer | LIKELY TRUE POSITIVE | In `CancelEscrow` struct (line 162-163), `initializer` is `AccountInfo<'info>` without a Signer constraint. The only validation is `escrow_account.initializer_key == *initializer.key`, which checks the key matches but doesn't require the initializer to sign. Since `initializer_key` is stored on-chain and public, any third party can call `cancel_escrow` to return tokens to the initializer and close the escrow account. This is a denial-of-service vector: an attacker can cancel any open escrow, preventing the taker from completing the exchange. No fund theft occurs (tokens return to initializer, rent refund goes to initializer). |
| SEM-002 | Low | Zero amounts allowed in initialize_escrow | INFORMATIONAL | `initializer_amount` and `taker_amount` can both be 0. If `taker_amount = 0`, anyone can take the escrowed tokens for free. However, the initializer explicitly chooses these terms, so this is by design rather than a bug. |
| SEM-003 | Low | Shared PDA seed for all escrows | INFORMATIONAL | All escrows use `ESCROW_PDA_SEED = b"escrow"` for PDA authority. This is fine because set_authority operates on individual token accounts, not the PDA itself. The PDA serves as a global escrow authority, each token account's ownership is individually managed. |

## Summary

- **True Positives**: 0
- **Likely True Positives**: 1 (missing signer on cancel — DoS vector)
- **Informational**: 2
- **False Positives**: 0

**Assessment**: Classic PaulX escrow pattern. Well-constrained exchange logic with proper account validation. The cancel_escrow missing signer is a real design flaw — it's unclear if it's intentional ("anyone can trigger refund") or a bug. Since it prevents legitimate exchanges from completing, it's classified as likely TP.
