# Iterative Improvement Log

## Detector Versions

| Version | Changes | Static FP Count | Semantic FP Rate | Programs Tested |
|---------|---------|----------------|-----------------|-----------------|
| v0.3.0 | Baseline (initial prompt + 6 regex patterns) | 68 (community+anchor) | 18% (3/17) | 4 real + demo |
| v0.4.0 | Enhanced prompt (11 new rules), scanner FP reduction (PDA/seeds/address) | 32 (community+anchor) | 9.7% (3/31)* | 10 real + 11 calibration |

*Semantic FP rate uses accumulated findings. With API access and the improved prompt, expected FP rate is lower since the 3 FPs (anchor-multisig) would be addressed by strengthened usize/u64 and boolean idempotency rules.

| v0.5.0 | Enhanced prompt (+4 FP rules from batch 3), scanner: has_one/close/constraint skip + UncheckedAccount severity downgrade | 144 total (20 High/Med) | 10.3% (6/58)* | 15 real + 11 calibration |

*v0.5.0 metrics include batch 3 (5 new programs). Total static findings dropped -16% and actionable (High/Medium) findings dropped -88% vs v0.4.0.

## Improvement Cycle 1: Batch 1 → Error Analysis → v0.4.0

### Input
- 5 new programs analyzed (sol-vault, solana-staking, nft-staking-shuk, anchor-escrow, anchor-lockup)
- 11 sealevel-attacks programs calibrated
- Existing 5 programs from prior report

### Error Analysis Findings
1. **All 3 FPs concentrated in one program** (anchor-multisig) — suggests the LLM had a bad run rather than systematic issues
2. **Integer cast (usize→u64) accounts for 67% of FPs** — needs stronger prompt language
3. **Boolean idempotency accounts for 33% of FPs** — already in prompt but needs emphasis
4. **Static scanner produces 47 FPs on anchor-lockup alone** — PDA signer false positives dominate

### Changes Applied
- Semantic prompt: +11 new rules/patterns, ~2x longer prompt
- Static scanner: +3 skip conditions (seeds, address, signer field names)

### Measured Improvement
- Static scanner FPs: 57 → 32 (-44%) on community+anchor targets
- anchor-lockup specifically: 47 → 22 (-53%)
- Zero true detections lost
- All 53 tests pass

## Key Learnings

### 1. PDA signer accounts are the #1 static scanner noise source
Programs using `*_signer: AccountInfo<'info>` with `seeds = [...]` constraints are validated by PDA derivation. The scanner was flagging these as "missing owner validation" when the PDA address IS the validation.

### 2. The sealevel-attacks "secure" vs "recommended" distinction is critical
The "secure" variants fix vulnerabilities with MANUAL code checks but still use raw AccountInfo. The "recommended" variants use Anchor typed accounts. Our static scanner correctly identifies "recommended" as clean but cannot distinguish "secure" from "insecure" — this is a fundamental limitation of regex-based analysis.

### 3. Multi-file programs need concatenation
nft-staking-shuk was completely unanalyzable because its lib.rs only contains entrypoint stubs. The actual logic lives in `instructions/` modules. Future versions should concatenate all .rs files in a program crate.

### 4. Unaudited community programs yield the best true positives
Both new TPs (solana-staking) came from a community prototype. Audited production protocols (marinade, raydium) produce only informational findings. This validates the tool's best use case: catching bugs in early-stage or unaudited code.

### 5. The semantic prompt's Solana-specific rules are effective
This batch produced 0 new semantic FPs, compared to 3 FPs in the previous batch. The Solana atomicity, usize/u64, and boolean idempotency rules are working, though they could still be stronger.

## Improvement Cycle 2: Batch 3 → Error Analysis → v0.5.0

### Input
- 5 new Anchor framework programs (tictactoe, cashiers-check, ido-pool, cfo, auction-house)
- 3808 lines total, ranging from 180 to 1745 lines
- 27 semantic findings with 3 new FPs (all from anchor-auction-house)

### Error Analysis Findings
1. **UncheckedAccount dominates static scanner noise**: 124 of 132 flagged fields use UncheckedAccount, which is a deliberate Anchor choice. Should differentiate from accidental AccountInfo.
2. **New FP category: intentional permissionless design**: Cranker/relayer patterns where non-signer execution is by design (auction-house execute_sale).
3. **New FP category: Solana runtime behavior**: Zero-lamport garbage collection makes explicit data zeroing unnecessary.
4. **New FP category: PDA seed enforcement**: When same instruction arg is used in multiple PDA seeds, the constraint validates matching.
5. **has_one/close/constraint attributes skip opportunity**: Fields with these Anchor attributes have developer-explicit validation, reducing static scanner noise.

### Changes Applied
- **Semantic prompt (v0.5.0)**: +4 explicit FP rules:
  - #7: Zero-lamport account garbage collection
  - #8: Permissionless cranker/relayer pattern
  - #9: PDA seed parameter validation
  - #10: UncheckedAccount for CPI passthrough
- **Static scanner (v0.5.0)**: 3 improvements:
  - Skip fields with `has_one` or `close` constraints
  - Skip fields with any `constraint` expression
  - Downgrade UncheckedAccount findings from High/Medium to Low severity

### Measured Improvement
- Total static findings: 171 → 144 (-16%)
- **High/Medium actionable findings: 171 → 20 (-88%)**
- anchor-multisig: 3 → 0 (has_one constraint skip)
- anchor-lockup: 22 → 4 (-82%, constraint skip)
- solana-staking: 10 → 6 (-40%, constraint skip)
- Zero true detections lost
- All 53 tests pass

### Key Insight
The biggest improvement comes from **severity downgrading** rather than finding removal. By treating UncheckedAccount as Low severity, the scanner still reports these fields but the High/Medium list is focused on genuinely suspicious AccountInfo fields. This dramatically improves signal-to-noise: from 171 "High" alerts to 20.

## Key Learnings (continued)

### 6. UncheckedAccount ≠ AccountInfo for security severity
In modern Anchor, `UncheckedAccount` is a deliberate developer choice that requires `/// CHECK:` documentation. Treating it the same as `AccountInfo` (which might be accidental) generates massive false positive noise. Severity differentiation is the right approach.

### 7. Large programs have lower TP rate but more informational findings
anchor-auction-house (1745 lines) produced 1 TP out of 15 findings (6.7%), while smaller programs like anchor-tictactoe (213 lines) produced 1 TP out of 3 findings (33%). The signal-to-noise ratio decreases with program complexity.

### 8. DeFi design pattern awareness reduces FPs
Permissionless execution patterns (cranker/relayer) are common in DeFi but look like missing authorization to a naive analyzer. The prompt needs awareness of these design patterns to avoid false positives.
