# Batch 4 Metrics — High-Value Programs Validation

## Overview

**Date**: 2026-02-15
**Detector version**: v0.5.0
**Programs analyzed**: 3 (Orca Whirlpools, NFT Staking Unaudited, Sealevel-10)
**Methodology**: V5 batch analysis — analyze, classify ALL, aggregate FP patterns

## Programs Analyzed

| Program | Domain | Lines | Tier | Source | Multi-file |
|---------|--------|-------|------|--------|------------|
| Orca Whirlpools | CLMM DEX | 1337 (lib.rs) | Production | orca-so/whirlpools | Yes (171 files, ~30K lines) |
| NFT Staking Unaudited | NFT staking | 1499 (concat) | Community | 0xShuk/NFT-Staking-Program | Yes (17 files, concatenated) |
| Sealevel-10 Sysvar | Calibration | 55 (3 variants) | Calibration | coral-xyz/sealevel-attacks | No (single-file each) |

## Semantic Analysis Results

| Program | Total | TP | LTP | INFO | FP |
|---------|-------|----|-----|------|----|
| Orca Whirlpools | 3 | 0 | 0 | 3 | 0 |
| NFT Staking Unaudited | 5 | 0 | 1 | 4 | 0 |
| Sealevel-10 (insecure) | 1 | 1 | 0 | 0 | 0 |
| Sealevel-10 (secure) | 0 | 0 | 0 | 0 | 0 |
| Sealevel-10 (recommended) | 0 | 0 | 0 | 0 | 0 |
| **TOTAL** | **9** | **1** | **1** | **7** | **0** |

## Static Scanner Results

| Program | Total | High | Medium | Low | FP |
|---------|-------|------|--------|-----|----|
| Orca Whirlpools | 0 | 0 | 0 | 0 | 0 |
| NFT Staking Unaudited | 19 | 5 | 6 | 8 | 11 |
| Sealevel-10 (all variants) | 0 | 0 | 0 | 0 | 0 |
| **TOTAL** | **19** | **5** | **6** | **8** | **11** |

## Batch 4 Metrics

| Metric | Count | Percentage |
|--------|-------|------------|
| Total semantic findings | 9 | 100% |
| True Positives | 1 | 11.1% |
| Likely True Positives | 1 | 11.1% |
| Informational | 7 | 77.8% |
| False Positives | 0 | 0% |

**Batch 4 Semantic FP Rate: 0/9 = 0%**

## Comparison with Baseline (Batches 1-3)

| Metric | Baseline (1-3) | Batch 4 | Total (29 programs) |
|--------|---------------|---------|---------------------|
| Programs | 26 | 3 | 29 |
| Semantic findings | 58 | 9 | 67 |
| True Positives | 6 | 1 | 7 |
| Likely True Positives | 3 | 1 | 4 |
| False Positives | 6 | 0 | 6 |
| FP Rate | 10.3% | 0% | 9.0% |
| Detector | v0.5.0 | v0.5.0 | v0.5.0 |

**Combined FP Rate: 6/67 = 9.0%** (improved from 10.3% baseline)

Note: The FP rate improvement is primarily because Batch 4 programs are
(a) a production protocol producing only informational findings, (b) well-written
community code with proper Anchor patterns, and (c) a calibration program with
a clear ground truth. None of these program types tend to produce FPs with the
v0.5.0 prompt improvements.

## Key Findings

### 1. Orca Whirlpools — Production CLMM
- **Result**: 0 TP, 0 FP, 3 INFO
- **Insight**: The detector correctly produces ZERO false positives on the
  highest-complexity production Solana program. All findings are informational
  notes about multi-file analysis limitations.
- **KNOW**: The lib.rs dispatcher file cannot reveal logic bugs because all
  handler logic is in separate modules.
- **BELIEVE**: Full multi-file analysis would still produce 0 TPs because
  Orca has been audited by multiple professional firms.

### 2. NFT Staking Unaudited — Community Code
- **Result**: 0 TP, 1 LTP, 4 INFO, 0 FP
- **Key finding**: Reward accounting mismatch in `decrease_current_balance()` —
  uses only the last reward rate while `calc_reward()` iterates all periods.
  This can cause `current_balance` to overstate actual remaining vault balance
  after multiple reward rate changes.
- **KNOW**: The code paths showing the mismatch are concrete and verifiable.
- **BELIEVE**: The bug requires multi-step triggering (multiple reward changes +
  claims) and the impact is limited to allowing unsustainable reward rates.
- **SPECULATE**: This bug may not manifest in practice if the creator never
  changes the reward rate.

### 3. Sealevel-10 — Calibration
- **Result**: PASS (1 TP on insecure, 0 FP on secure + recommended)
- **Insight**: The detector correctly distinguishes:
  - Raw AccountInfo without validation → vulnerability detected
  - Raw AccountInfo with manual address check → no false positive
  - Anchor Sysvar typed account → no false positive
- **KNOW**: This completes the sealevel-attacks calibration suite (all 11 categories).

## Sealevel Calibration Summary (All Categories)

| # | Attack Type | Static | Semantic (insecure) | Semantic (secure) |
|---|------------|--------|--------------------|--------------------|
| 0 | Signer authorization | partial | TP expected | 0 FP |
| 1 | Account data matching | partial | TP expected | 0 FP |
| 2 | Owner checks | partial | TP expected | 0 FP |
| 3 | Type cosplay | partial | TP expected | 0 FP |
| 4 | Initialization | partial | TP expected | 0 FP |
| 5 | Arbitrary CPI | partial | TP expected | 0 FP |
| 6 | Duplicate mutable | MISSED | TP expected | 0 FP |
| 7 | Bump seed canonical. | MISSED | TP expected | 0 FP |
| 8 | PDA sharing | MISSED | TP expected | 0 FP |
| 9 | Closing accounts | partial | TP expected | 0 FP |
| 10 | Sysvar address | MISSED | **TP confirmed** | **0 FP confirmed** |

## Error Analysis

### Why 0 FPs in Batch 4

1. **Orca (production)**: Only informational findings because dispatcher-only
   analysis cannot produce false vulnerability reports. All logic is in handlers.

2. **NFT Staking (community)**: The v0.5.0 prompt improvements are effective:
   - UncheckedAccount PDA fields correctly not flagged as vulnerabilities
   - init_if_needed with proper ATA constraints correctly not flagged
   - Permissionless patterns correctly understood
   - The one real finding (accounting mismatch) requires cross-function reasoning,
     which is the semantic analyzer's strength

3. **Sealevel-10 (calibration)**: Clear-cut case — raw AccountInfo for sysvar
   is an obvious vulnerability, and the fixed variants are obviously safe.

### Static Scanner Noise

The static scanner produced 19 findings on NFT Staking, of which 11 are FPs.
The v0.5.0 improvements (UncheckedAccount severity downgrade, constraint skip)
correctly classify 8 of 19 as Low severity. The remaining 11 High/Medium are
init_if_needed FPs that the scanner could be improved to handle.

**Potential improvement**: Skip ANCHOR-001/ANCHOR-002 on ATAs that have both
`associated_token::mint` and `associated_token::authority` constraints, as
these are fully validated by Anchor's ATA derivation.
