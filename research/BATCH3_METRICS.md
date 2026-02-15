# Batch 3 Metrics: 5 Additional Anchor Framework Programs

## Programs Analyzed

| Program | Lines | Domain | Static | Semantic | TP | LTP | INFO | FP |
|---------|-------|--------|--------|----------|----|----|------|-----|
| anchor-tictactoe | 213 | Game | 0 | 3 | 1 | 0 | 2 | 0 |
| anchor-cashiers-check | 180 | Escrow | 5 | 3 | 0 | 0 | 3 | 0 |
| anchor-ido-pool | 675 | IDO/Token sale | 4 | 3 | 0 | 0 | 3 | 0 |
| anchor-cfo | 995 | DEX fees | 36 | 3 | 0 | 0 | 3 | 0 |
| anchor-auction-house | 1745 | NFT marketplace | 89 | 15 | 1 | 1 | 10 | 3 |
| **Total** | **3808** | — | **134** | **27** | **2** | **1** | **21** | **3** |

## Batch 3 Aggregate

| Metric | Count | Percentage |
|--------|-------|-----------|
| Total semantic findings | 27 | 100% |
| True Positives | 2 | 7.4% |
| Likely True Positives | 1 | 3.7% |
| Informational | 21 | 77.8% |
| False Positives | 3 | 11.1% |

## New True Findings

| # | Program | Bug | Severity | Classification |
|---|---------|-----|----------|---------------|
| 1 | anchor-tictactoe | Inverted game_state constraint blocks player_o from joining | Critical | TRUE POSITIVE |
| 2 | anchor-auction-house | CreateAuctionHouse: authority not Signer (front-run griefing) | High | TRUE POSITIVE |
| 3 | anchor-auction-house | Authority can withdraw any user's escrow without user signature | High | LIKELY TRUE POSITIVE |

## False Positive Analysis

All 3 FPs came from anchor-auction-house:
1. **SEM-004**: buyer/seller not Signers in execute_sale → intentional permissionless cranker pattern
2. **SEM-005**: buyer_price matching → enforced by PDA seed derivation
3. **SEM-007**: account data not zeroed → Solana runtime handles zero-lamport cleanup

### FP Pattern: Intentional permissionless design
The auction-house follows a cranker/relayer model where both parties consent via separate instructions (buy/sell) and then anyone can execute the match. This is a well-known pattern in DeFi but can confuse analysis that expects signer requirements on all participants.

### FP Pattern: Solana runtime behavior
The runtime's automatic garbage collection of zero-lamport accounts is not always known to security analyzers.

## Static Scanner Performance

| Program | Static | Notes |
|---------|--------|-------|
| anchor-tictactoe | 0 | Clean modern Anchor code |
| anchor-cashiers-check | 5 | Older Anchor patterns (AccountInfo for CPI) |
| anchor-ido-pool | 4 | Intentional AccountInfo design (with comments) |
| anchor-cfo | 36 | UncheckedAccount for DEX CPI passthrough |
| anchor-auction-house | 89 | UncheckedAccount for stack size + CPI |
| **Total** | **134** | Dominated by CPI passthrough patterns |

The v0.4.0 scanner improvement (PDA/seeds skip) helped reduce false positives but the UncheckedAccount pattern (used deliberately for CPI passthrough or stack size reasons) generates the most noise on larger programs.

## Comparison Across Batches

| Metric | Batch 1 (10 programs) | Batch 3 (5 programs) | Combined (15 programs) |
|--------|----------------------|---------------------|----------------------|
| Semantic findings | 31 | 27 | 58 |
| True Positives | 4 | 2 | 6 |
| Likely True Positives | 2 | 1 | 3 |
| Informational | 22 | 21 | 43 |
| False Positives | 3 | 3 | 6 |
| FP Rate | 9.7% | 11.1% | 10.3% |
| TP+LTP Rate | 19.4% | 11.1% | 15.5% |
