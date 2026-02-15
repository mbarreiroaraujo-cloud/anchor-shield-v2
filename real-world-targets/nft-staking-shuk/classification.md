# nft-staking-shuk — Finding Classification

**Program**: NFT staking with rewards (170 lines across 2 files)
**Source**: 0xShuk/NFT-Staking-Program (community)
**Domain**: NFT staking / rewards
**Static scanner findings**: 0

## Manual Semantic Analysis

| ID | Severity | Title | Classification | Reasoning |
|----|----------|-------|---------------|-----------|
| N/A | N/A | Insufficient context for analysis | INSUFFICIENT CONTEXT | Both `lib.rs` files (nft_stake_vault: 57 lines, nft_stake_auth: 38 lines) are thin wrappers that delegate to `instructions::*` modules via handler functions. The actual business logic (stake_handler, withdraw_reward_handler, unstake_handler, etc.) lives in separate files we don't have. Cannot perform meaningful vulnerability analysis on entrypoint stubs alone. |

## Summary

- **True Positives**: 0
- **Likely True Positives**: 0
- **Informational**: 0
- **False Positives**: 0
- **Analyzable**: NO (multi-file program, logic in separate modules)

**Assessment**: This program demonstrates a key limitation of single-file analysis. The lib.rs files only contain function signatures and error codes. All actual logic is in `instructions/` and `state/` modules. A production analyzer would need to concatenate all source files or analyze the full crate. The error codes suggest the program handles: staking periods, collection verification, reward eligibility, and balance validation — but we cannot verify the implementation.
