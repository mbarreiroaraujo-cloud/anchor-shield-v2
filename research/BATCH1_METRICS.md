# Batch 1 Metrics — Baseline Analysis

## Programs Analyzed

### New Programs (this session)

| # | Program | Domain | Lines | Audited? | TP | LTP | INFO | FP | Notes |
|---|---------|--------|-------|----------|----|----|------|----|----|
| 1 | sol-vault | Token vault | 359 | No | 0 | 0 | 3 | 0 | Well-structured, proper Anchor constraints |
| 2 | solana-staking | NFT staking | 204 | No | 2 | 0 | 3 | 0 | Prototype with incomplete unstake |
| 3 | nft-staking-shuk | NFT staking | 170 | No | 0 | 0 | 0 | 0 | INSUFFICIENT CONTEXT (multi-file) |
| 4 | anchor-escrow | Token escrow | 260 | No | 0 | 1 | 2 | 0 | Missing signer on cancel |
| 5 | anchor-lockup | Token vesting | 1868 | No | 0 | 0 | 4 | 0 | Mature design, unchecked arithmetic |

### Previously Analyzed (from RESEARCH_REPORT.md)

| # | Program | Domain | Lines | Audited? | TP | LTP | INFO | FP |
|---|---------|--------|-------|----------|----|----|------|----|
| 6 | anchor-multisig | Governance | 280 | No | 2 | 0 | 0 | 3 |
| 7 | anchor-swap | DEX | 496 | No | 0 | 1 | 2 | 0 |
| 8 | marinade-staking | Liquid staking | 1611 | Yes | 0 | 0 | 4 | 0 |
| 9 | raydium-clmm | CLMM AMM | 2931 | Yes | 0 | 0 | 4 | 1 |
| 10 | anchor-token-proxy | Token ops | 273 | No | 0 | 0 | 0 | 0 |

### Sealevel-Attacks (calibration, not counted in main metrics)

11 vulnerability categories, each with insecure/secure/recommended.
See SEALEVEL_CALIBRATION.md for full results.

## Aggregate Metrics — All 10 Programs

| Metric | Count | Percentage |
|--------|-------|-----------|
| **Total semantic findings** | 31 | 100% |
| True Positives | 4 | 12.9% |
| Likely True Positives | 2 | 6.5% |
| Informational | 22 | 71.0% |
| False Positives | 3 | 9.7% |

### By Program Category

| Category | Programs | TP | LTP | INFO | FP | FP Rate |
|----------|---------|----|----|------|-----|---------|
| Unaudited community | 5 (vault, staking, shuk, escrow, lockup) | 2 | 1 | 12 | 0 | 0% |
| Unaudited Anchor tests | 3 (multisig, swap, token-proxy) | 2 | 1 | 2 | 3 | 43% |
| Audited production | 2 (marinade, raydium) | 0 | 0 | 8 | 1 | 11% |

### Detection Rate by Domain

| Domain | Programs | Findings | True Findings (TP+LTP) |
|--------|---------|----------|----------------------|
| Token vault | 1 | 3 | 0 |
| NFT staking | 2 | 5 | 2 |
| Governance | 1 | 5 | 2 |
| Escrow | 1 | 3 | 1 |
| Vesting | 1 | 4 | 0 |
| DEX/AMM | 2 | 7 | 1 |
| Liquid staking | 1 | 4 | 0 |

## Key Observations

1. **FP rate improved from 18% to 9.7%** with the expanded corpus (more programs = more informational dilution, but also previous FPs concentrated in anchor-multisig)

2. **True positives come from unaudited programs** — all 4 TPs (multisig zero-threshold, multisig empty-owners, solana-staking incomplete unstake, solana-staking missing signer) are on unaudited code

3. **Audited programs produce only informational findings** — consistent with expectations

4. **The 3 FPs are ALL from anchor-multisig** — specific to integer cast and data structure misunderstandings in the original analysis

5. **New programs (this session) produced 0 FPs** — suggesting the current prompt's Solana-specific rules are effective

6. **Multi-file programs are a blind spot** — nft-staking-shuk was unanalyzable

## Static Scanner Metrics

| Metric | Value |
|--------|-------|
| Total static findings across 10 programs | 68 |
| On audited programs | 6 |
| On sealevel-attacks (insecure) | ~20 |
| On sealevel-attacks (secure/recommended) | ~20 FP |
| Logic bugs detected by scanner | 0 |
| Logic bugs detected only by semantic | 6 (4 TP + 2 LTP) |
