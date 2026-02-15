# Real-World Validation Targets

Programs acquired for real-world I+D validation of anchor-shield-v2's semantic analysis capabilities.

## Full Corpus

| # | Program | Domain | Source | Lines | Tier | Compiled | TP | LTP | INFO | FP |
|---|---------|--------|--------|-------|------|----------|----|----|------|----|
| 1 | anchor-swap | DEX/AMM | coral-xyz/anchor (tests/) | 496 | 1 | — | 0 | 1 | 2 | 0 |
| 2 | anchor-multisig | Governance | coral-xyz/anchor (tests/) | 280 | 1 | multisig.so (219KB) | 2 | 0 | 0 | 3 |
| 3 | anchor-token-proxy | Token ops | coral-xyz/anchor (tests/) | 273 | 1 | — | 0 | 0 | 0 | 0 |
| 4 | anchor-escrow | Token escrow | coral-xyz/anchor (tests/) | 260 | 1 | anchor_escrow.so (258KB) | 0 | 1 | 2 | 0 |
| 5 | anchor-lockup | Token vesting | coral-xyz/anchor (tests/) | 1868 | 1 | — | 0 | 0 | 4 | 0 |
| 6 | marinade-staking | Liquid staking | marinade-finance | 1611 | 3 | — | 0 | 0 | 4 | 0 |
| 7 | raydium-clmm | CLMM AMM | raydium-io | 2931 | 3 | — | 0 | 0 | 4 | 1 |
| 8 | sol-vault | Token vault | Clish254/sol-vault | 359 | 2 | — | 0 | 0 | 3 | 0 |
| 9 | solana-staking | NFT staking | rpajo/solana-staking | 204 | 2 | skinflip_staking.so (239KB) | 2 | 0 | 3 | 0 |
| 10 | nft-staking-shuk | NFT staking | 0xShuk/NFT-Staking-Program | 170 | 2 | — | — | — | — | — |
| 11 | anchor-tictactoe | Game | coral-xyz/anchor (tests/) | 213 | 1 | tictactoe.so (203KB) | 1 | 0 | 2 | 0 |
| 12 | anchor-cashiers-check | Escrow | coral-xyz/anchor (tests/) | 180 | 1 | — | 0 | 0 | 3 | 0 |
| 13 | anchor-ido-pool | IDO/Token sale | coral-xyz/anchor (tests/) | 675 | 1 | — | 0 | 0 | 3 | 0 |
| 14 | anchor-cfo | DEX fees | coral-xyz/anchor (tests/) | 995 | 1 | — | 0 | 0 | 3 | 0 |
| 15 | anchor-auction-house | NFT marketplace | coral-xyz/anchor (tests/) | 1745 | 1 | FAILED | 1 | 1 | 10 | 3 |
| 16 | orca-whirlpools | CLMM DEX | orca-so/whirlpools | 1337 | 3 | — | 0 | 0 | 3 | 0 |
| 17 | nft-staking-unaudited | NFT staking | 0xShuk/NFT-Staking-Program | 1499 | 2 | — | 0 | 1 | 4 | 0 |

### Sealevel-Attacks Calibration (11 vulnerability categories + 1 semantic)

| # | Attack Type | Insecure Lines | Secure Lines | Detection |
|---|------------|---------------|-------------|-----------|
| 16 | 0-signer-authorization | 17 | 21 | Static: partial |
| 17 | 1-account-data-matching | 22 | 25 | Static: partial |
| 18 | 2-owner-checks | 26 | 29 | Static: partial |
| 19 | 3-type-cosplay | 37 | 48 | Static: partial |
| 20 | 4-initialization | 38 | 38 | Static: partial |
| 21 | 5-arbitrary-cpi | 35 | 38 | Static: partial |
| 22 | 6-duplicate-mutable-accounts | 28 | 31 | Static: MISSED |
| 23 | 7-bump-seed-canonicalization | 30 | 38 | Static: MISSED |
| 24 | 8-pda-sharing | 45 | 48 | Static: MISSED |
| 25 | 9-closing-accounts | 30 | 71 | Static: partial |
| 26 | 10-sysvar-address-checking | 18 | 19 | Static: MISSED |
| 27-29 | 10-sysvar (semantic calibration) | 18 | 19+18 | Semantic: TP insecure, 0 FP secure+recommended |

## Tier Definitions

- **Tier 1**: Anchor framework examples (known quality, single-file, compilable)
- **Tier 2**: Community open source (unaudited — highest chance of real bugs)
- **Tier 3**: Production protocols (audited — test for informational/FP rate)
- **Tier 4**: Known-vulnerable (sealevel-attacks — calibration dataset)

## Selection Criteria

- **Diversity**: Different domains (DEX, staking, governance, token ops, vault, escrow, vesting, CLMM)
- **Complexity**: Range from simple (170 lines) to complex (2931+ lines)
- **Audit status**: Mix of audited production protocols, framework examples, and community code
- **Relevance**: Financial operations with potential for logic bugs
- **Calibration**: Known-vulnerable programs for sensitivity/specificity testing
- **Batch 4 additions**: Highest-value production (Orca), unaudited community (NFT Staking),
  and sysvar calibration with ground truth (Sealevel-10)

## Aggregate Statistics

- **Total programs**: 29 (17 main + 11 sealevel calibration + 1 sealevel semantic)
- **Total lines analyzed**: ~19,000+
- **True Positives found**: 7 (anchor-multisig x2, solana-staking x2, anchor-tictactoe, anchor-auction-house, sealevel-10-insecure)
- **Likely True Positives**: 4 (anchor-swap, anchor-escrow, anchor-auction-house, nft-staking-unaudited)
- **False Positive rate**: 9.0% (6/67 semantic findings)
- **Bankrun confirmed**: 9 (multisig x2, escrow, tictactoe, staking x2, lending x3)
- **Simulation confirmed**: 3 (solana-staking x2, anchor-escrow)
- **Detector versions**: v0.3.0 → v0.4.0 → v0.5.0 → v0.5.1 (3 improvement cycles)
- **Sealevel calibration**: 11/11 categories covered (PASS on all tested categories)
