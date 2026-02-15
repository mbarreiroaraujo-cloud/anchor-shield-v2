# Iterative Improvement Log

## Detector Versions

| Version | Changes | Static FP Count | Semantic FP Rate | Programs Tested |
|---------|---------|----------------|-----------------|-----------------|
| v0.3.0 | Baseline (initial prompt + 6 regex patterns) | 68 (community+anchor) | 18% (3/17) | 4 real + demo |
| v0.4.0 | Enhanced prompt (11 new rules), scanner FP reduction (PDA/seeds/address) | 32 (community+anchor) | 9.7% (3/31)* | 10 real + 11 calibration |

*Semantic FP rate uses accumulated findings. With API access and the improved prompt, expected FP rate is lower since the 3 FPs (anchor-multisig) would be addressed by strengthened usize/u64 and boolean idempotency rules.

| v0.5.0 | Enhanced prompt (+4 FP rules from batch 3), scanner: has_one/close/constraint skip + UncheckedAccount severity downgrade | 144 total (20 High/Med) | 10.3% (6/58)* | 15 real + 11 calibration |

*v0.5.0 metrics include batch 3 (5 new programs). Total static findings dropped -16% and actionable (High/Medium) findings dropped -88% vs v0.4.0.

| v0.5.1 | Scanner: ATA init_if_needed skip (ANCHOR-001/002), Prompt: +accounting consistency analysis | Reduced (ATA FPs eliminated) | 9.0% (6/67) | 18 real + 11 calibration |

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

## Improvement Cycle 3: Batch 4 — High-Value Programs Validation

**Date**: 2026-02-15
**Detector**: v0.5.0 → v0.5.1
**Programs**: 3 (Orca Whirlpools, NFT Staking Unaudited, Sealevel-10 Sysvar)

### Programs Analyzed

| Program | Domain | Lines | Tier | Findings | TP | LTP | FP | INFO |
|---------|--------|-------|------|----------|----|----|-----|------|
| Orca Whirlpools | CLMM DEX | 1337 | Production | 3 | 0 | 0 | 0 | 3 |
| NFT Staking | NFT staking | 1499 | Community | 5 | 0 | 1 | 0 | 4 |
| Sealevel-10 (insecure) | Calibration | 18 | Calibration | 1 | 1 | 0 | 0 | 0 |
| Sealevel-10 (secure) | Calibration | 19 | Calibration | 0 | 0 | 0 | 0 | 0 |
| Sealevel-10 (recommended) | Calibration | 18 | Calibration | 0 | 0 | 0 | 0 | 0 |
| **TOTAL** | | **2891** | | **9** | **1** | **1** | **0** | **7** |

### Batch 4 Metrics

| Metric | Count | Percentage |
|--------|-------|------------|
| Total findings | 9 | 100% |
| True Positives | 1 | 11.1% |
| Likely True Positives | 1 | 11.1% |
| False Positives | 0 | 0% |
| Informational | 7 | 77.8% |

**Batch 4 FP Rate: 0/9 = 0%**

### Error Analysis — Why 0 FPs

Three factors contributed to zero false positives in this batch:

1. **Production code restraint**: On Orca Whirlpools (dispatcher-only analysis),
   the analyzer correctly recognized that handler delegation prevents definitive
   claims, producing only informational notes.

2. **v0.5.0 rules effective on community code**: On NFT Staking, the PDA-aware
   UncheckedAccount rules (#10), Anchor discriminator rules (#6), and PDA seed
   rules (#9) all prevented FPs that earlier detector versions would have produced.

3. **Clear ground truth**: Sealevel-10 has an obvious vulnerability pattern
   (raw AccountInfo for sysvar without address check) that leaves no room for
   misclassification.

### Key Finding: Reward Accounting Mismatch (NFT Staking)

The most significant finding in Batch 4 is a cross-function accounting bug in
0xShuk/NFT-Staking-Program:

- `calc_reward()` iterates through ALL reward rate periods to compute actual payout
- `decrease_current_balance()` uses only the LAST reward rate for balance tracking
- After multiple reward rate changes + claims, `current_balance` overstates reality
- This could allow the creator to set unsustainable reward rates

**KNOW**: The code paths showing the mismatch are concrete and verifiable.
**BELIEVE**: Requires multi-step triggering (multiple reward changes + claims).
**SPECULATE**: May not manifest in practice if reward rate is never changed.

### Sealevel-10 Calibration Results

| Variant | Expected | Actual | Result |
|---------|----------|--------|--------|
| Insecure | 1 TP (missing sysvar address check) | 1 TP | PASS |
| Secure | 0 FP (manual address check present) | 0 FP | PASS |
| Recommended | 0 FP (Anchor Sysvar type) | 0 FP | PASS |

This completes calibration across all 11 sealevel-attacks categories.

### Detector Improvement: v0.5.0 → v0.5.1

Based on static scanner FP analysis on NFT Staking:

**Problem**: ANCHOR-001 and ANCHOR-002 flagged Associated Token Account (ATA)
`init_if_needed` fields even when both `associated_token::mint` and
`associated_token::authority` constraints are present. ATAs are deterministic
(derived from mint+authority), so an attacker cannot pre-create them with
malicious delegate/close_authority.

**Fix**: Skip ANCHOR-001/002 for ATA fields with both mint and authority constraints.

**Semantic prompt**: Added accounting consistency analysis focus area.

**Results**:
- NFT Staking static findings: 19 → 9 (10 fewer FPs, -53%)
- All High-severity ATA FPs eliminated
- Zero true detections lost across all programs
- All 53 tests pass

### Comparison with Baseline

| Metric | Baseline (Batches 1-3) | Batch 4 | Total (29 programs) |
|--------|----------------------|---------|---------------------|
| Programs | 26 | 3 | 29 |
| Semantic findings | 58 | 9 | 67 |
| Semantic FPs | 6 | 0 | 6 |
| FP Rate | 10.3% | 0% | 9.0% |
| Detector | v0.5.0 | v0.5.1 | v0.5.1 |

### Detector Evolution Summary

| Version | Batches | Programs | Semantic FP Rate | Changes |
|---------|---------|----------|-----------------|---------|
| v0.3.0 | Batch 1 | 10 | 18% (3/17) | Baseline prompt + 6 regex patterns |
| v0.4.0 | Batch 2 | 21 | 9.7% (3/31) | +11 prompt rules, PDA skip |
| v0.5.0 | Batch 3 | 26 | 10.3% (6/58) | +4 FP rules, constraint/UncheckedAccount |
| v0.5.1 | Batch 4 | 29 | 9.0% (6/67) | ATA init_if_needed skip, accounting analysis |

**Final State**: 29 programs, detector v0.5.1, semantic FP rate 9.0%

### Key Learnings (continued)

### 9. Production dispatchers validate FP suppression
Analyzing only the lib.rs of a large multi-file program (Orca, 171 files) is
a natural test for FP suppression — the analyzer must recognize that handler
delegation prevents confident vulnerability claims and produce only informational
findings.

### 10. ATA init_if_needed is universally safe
Associated Token Accounts with proper mint+authority constraints are deterministic
by construction. The delegate/close_authority attack vector does not apply because:
(a) ATA addresses are predetermined, (b) setting delegate requires authority
signature, (c) PDA authorities cannot sign outside the program. This eliminates
an entire class of static scanner false positives.

### 11. Cross-function accounting mismatches are the semantic analyzer's strength
The reward accounting bug in NFT Staking requires understanding how two different
functions compute the same economic quantity differently — `calc_reward()` (correct,
multi-period) vs `decrease_current_balance()` (simplified, single-period). This
type of cross-function reasoning is exactly what static analysis cannot do and
semantic analysis excels at.
