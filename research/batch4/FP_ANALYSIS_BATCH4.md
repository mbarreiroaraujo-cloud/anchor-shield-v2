# False Positive Analysis — Batch 4

## Semantic FP Analysis

**Batch 4 produced 0 semantic false positives.**

This is the first batch with zero semantic FPs. The reasons are:

### Why Zero FPs

1. **Production code (Orca)**: Dispatcher-only analysis limits what can be
   flagged. The semantic analyzer correctly recognizes that handler delegation
   means vulnerability claims have low confidence. It produces only informational
   findings about analysis limitations.

2. **Well-written community code (NFT Staking)**: The v0.5.0 prompt improvements
   prevent the FP patterns seen in earlier batches:
   - Rule #1 (usize/u64 cast): Not applicable — no such casts in this code
   - Rule #5 (boolean array): Not applicable
   - Rule #7 (zero-lamport GC): Not applicable
   - Rule #8 (permissionless cranker): Not applicable (no cranker pattern)
   - Rule #9 (PDA seed validation): Applicable — PDA seeds correctly understood
   - Rule #10 (UncheckedAccount CPI): Applicable — PDA authority accounts correctly
     not flagged despite being UncheckedAccount

3. **Calibration code (Sealevel-10)**: Clear ground truth eliminates ambiguity.

### FP Prevention by v0.5.0 Rules

| v0.5.0 Rule | Triggered in Batch 4? | Prevented FP? |
|-------------|----------------------|---------------|
| #1: usize/u64 safe cast | No | N/A |
| #2: No race conditions | No | N/A |
| #3: No reentrancy | No | N/A |
| #4: Positive timestamps | No | N/A |
| #5: Boolean idempotency | No | N/A |
| #6: Anchor discriminator | Yes (Orca uses Account<T>) | Yes |
| #7: Zero-lamport GC | No | N/A |
| #8: Permissionless cranker | No | N/A |
| #9: PDA seed validation | Yes (NFT Staking PDAs) | Yes |
| #10: UncheckedAccount CPI | Yes (NFT Staking authority accounts) | Yes |

Rules #6, #9, and #10 actively prevented FPs in this batch.

## Static Scanner FP Analysis

### 11 Static FPs in NFT Staking

| Finding | Pattern | Field | Why FP |
|---------|---------|-------|--------|
| 1 | ANCHOR-001 | InitStaking.stake_token_vault | ATA with proper mint+authority constraints |
| 2 | ANCHOR-001 | Stake.nft_custody | ATA with proper mint+authority constraints |
| 3 | ANCHOR-001 | WithdrawReward.reward_receive_account | ATA with proper mint+authority constraints |
| 4 | ANCHOR-001 | Unstake.reward_receive_account | ATA with proper mint+authority constraints |
| 5 | ANCHOR-001 | Unstake.nft_receive_account | ATA with proper mint+authority constraints |
| 6 | ANCHOR-002 | InitStaking.stake_token_vault | Same as above — init_if_needed co-location |
| 7 | ANCHOR-002 | Stake.nft_custody | Same — coexisting fields are unrelated |
| 8 | ANCHOR-002 | WithdrawReward.reward_receive_account | Same |
| 9 | ANCHOR-002 | Unstake.reward_receive_account | Same |
| 10 | ANCHOR-002 | Unstake.nft_receive_account | Same |
| 11 | ANCHOR-005 | Unstake.nft_custody | close = staker is correct Anchor pattern |

### Error Category Distribution (Static)

| Category | Count | % |
|----------|-------|---|
| init_if_needed on constrained ATAs | 10 | 91% |
| close attribute on token account | 1 | 9% |
| Total | 11 | 100% |

### Proposed Static Scanner Fix

**ATA init_if_needed skip**: When a field has BOTH `init_if_needed` and
`associated_token::mint` + `associated_token::authority` constraints, the
account is deterministically derived and cannot be substituted. These fields
should be excluded from ANCHOR-001 and ANCHOR-002 pattern matching.

This single improvement would eliminate 10 of 11 static FPs in Batch 4.

## Comparison with Previous Batch FPs

| Batch | Semantic FPs | Top FP Category | Static FPs |
|-------|-------------|-----------------|------------|
| 1 | 3 (anchor-multisig) | Integer cast, boolean idempotency | 68 |
| 2 | 0 (re-test) | N/A (improved) | 32 |
| 3 | 3 (anchor-auction-house) | Permissionless cranker, GC, PDA seeds | — |
| 4 | 0 | None | 11 |

The semantic FP patterns observed in Batches 1 and 3 do not recur in Batch 4,
confirming that the prompt improvements in v0.4.0 and v0.5.0 are effective
across diverse program types.
