# Bankrun Execution Evidence

Every vulnerability finding classified as TRUE POSITIVE has been
executed against the actual Solana runtime via solana-bankrun.
Each execution log is saved verbatim in `exploits/*_execution.log`.

## Execution Summary

| Exploit | Binary | Status | Key Evidence |
|---------|--------|--------|-------------|
| bankrun_exploit_001_collateral_bypass | vuln_lending.so | CONFIRMED | Borrowed 500 SOL with 100 SOL collateral (500% debt ratio) |
| bankrun_exploit_002_withdraw_drain | vuln_lending.so | CONFIRMED | Withdrew all collateral with 90 SOL outstanding debt |
| bankrun_exploit_003_overflow_liquidation | vuln_lending.so | CONFIRMED | u64 overflow wraps; division by zero panics program |
| bankrun_exploit_escrow_001_cancel_without_signer | anchor_escrow.so | CONFIRMED | CancelEscrow accepted non-signing initializer AccountInfo |
| bankrun_exploit_multisig_001_zero_threshold | multisig.so | CONFIRMED | execute_transaction dispatched with 0 approvals (0 < 0 = false) |
| bankrun_exploit_multisig_002_empty_owners | multisig.so | CONFIRMED | create_transaction rejected — 50 SOL permanently locked |
| bankrun_exploit_staking_001_incomplete_unstake | skinflip_staking.so | CONFIRMED | unstake() returned Ok() but staked_nfts unchanged (NFT locked) |
| bankrun_exploit_staking_002_missing_signer | skinflip_staking.so | CONFIRMED | Attacker called unstake() without victim's signature |
| bankrun_exploit_tictactoe_001_inverted_constraint | tictactoe.so | CONFIRMED | ConstraintRaw (0x7d3) — player_join rejected, game deadlocked |

**Total: 9/9 exploits confirmed**

## How to Reproduce

```bash
cd exploits && npm install
npx ts-node bankrun_exploit_tictactoe_001_inverted_constraint.ts
# Repeat for any exploit file
```

## Environment

```
Node: v22.22.0
solana-bankrun: 0.4.0
ts-node: v10.9.2
Date: 2026-02-13
```

## Log Files

Each `*_execution.log` file contains the verbatim stdout/stderr from
`npx ts-node <exploit>.ts` run against the compiled SBF binary
loaded into solana-bankrun's in-process validator. Logs are unedited
raw output — they include Solana runtime debug messages, program logs,
CPI traces, and the exploit script's own analysis output.
