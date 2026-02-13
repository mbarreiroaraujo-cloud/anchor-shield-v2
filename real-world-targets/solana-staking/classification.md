# solana-staking — Finding Classification

**Program**: NFT staking prototype (204 lines)
**Source**: rpajo/solana-staking (community, prototype/tutorial)
**Domain**: NFT staking
**Static scanner findings**: 10 (5x ANCHOR-004, 5x ANCHOR-006 — all raw AccountInfo)

## Manual Semantic Analysis

| ID | Severity | Title | Classification | Reasoning |
|----|----------|-------|---------------|-----------|
| SEM-001 | Critical | Unstake function never returns the NFT | TRUE POSITIVE | The `unstake` function (lines 85-102) only calculates time_diff and logs it. It NEVER transfers the NFT back to the holder, and NEVER decrements `staking_machine.staked_nfts`. Any user who stakes permanently loses their NFT. |
| SEM-002 | High | Missing Signer constraint on nft_holder in unstake | TRUE POSITIVE | In `UnstakeInstructionStruct` (line 176-177), `nft_holder` is raw `AccountInfo` without a Signer constraint. Anyone can call unstake with any holder's public key. Combined with SEM-001 (no actual transfer), this is currently non-exploitable, but if the transfer were added, any attacker could trigger unstake for any user. |
| SEM-003 | Medium | Missing Signer constraint on nft_holder in stake | INFORMATIONAL | In `StakeInstructionStruct` (line 134), `nft_holder` is `AccountInfo` not `Signer`. However, the SPL token transfer at line 66-74 uses `nft_holder` as authority, and the token program enforces signature verification via CPI. So the signer check is implicitly enforced, though not explicitly declared. |
| SEM-004 | Low | Unchecked u16 addition on staked_nfts | INFORMATIONAL | Line 76: `staking_machine.staked_nfts + 1` uses unchecked addition on u16. Would overflow after 65535 stakes. Unlikely in practice but should use `checked_add()`. |
| SEM-005 | Medium | Raw AccountInfo for nft_token and nft_vault | INFORMATIONAL | `nft_token` (line 137-138) has no type validation. `nft_vault` is validated via `has_one = nft_vault` on staking_machine. The SPL token program provides runtime validation, but explicit type checking would be more robust. |

## Static Scanner Assessment

The 10 static scanner findings (ANCHOR-004/006) correctly identify the raw AccountInfo usage. However, they don't distinguish between accounts where CPI provides implicit validation (nft_token for token::transfer) and truly unvalidated accounts. All 10 findings are **INFORMATIONAL** — they flag a real code quality issue but the actual security impact varies.

## Summary

- **True Positives**: 2 (SEM-001: incomplete unstake, SEM-002: missing signer)
- **Likely True Positives**: 0
- **Informational**: 3
- **False Positives**: 0

**Assessment**: This is a prototype/tutorial program with significant issues. The critical bug (incomplete unstake) means staked NFTs are permanently locked. The missing signer check compounds the issue. The static scanner correctly flags raw AccountInfo usage but misses the logic bugs.
