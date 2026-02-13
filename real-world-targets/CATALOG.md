# Real-World Validation Targets

Programs acquired for real-world I+D validation of anchor-shield-v2's semantic analysis capabilities.

## Full Corpus

| # | Program | Domain | Source | Lines | Audited? | Tier | TP | LTP | INFO | FP |
|---|---------|--------|--------|-------|----------|------|----|----|------|----|
| 1 | anchor-swap | DEX/AMM | coral-xyz/anchor (tests/) | 496 | Framework test | 1 | 0 | 1 | 2 | 0 |
| 2 | anchor-multisig | Governance | coral-xyz/anchor (tests/) | 280 | Framework test | 1 | 2 | 0 | 0 | 3 |
| 3 | anchor-token-proxy | Token ops | coral-xyz/anchor (tests/) | 273 | Framework test | 1 | 0 | 0 | 0 | 0 |
| 4 | anchor-escrow | Token escrow | coral-xyz/anchor (tests/) | 260 | Framework test | 1 | 0 | 1 | 2 | 0 |
| 5 | anchor-lockup | Token vesting | coral-xyz/anchor (tests/) | 1868 | Framework test | 1 | 0 | 0 | 4 | 0 |
| 6 | marinade-staking | Liquid staking | marinade-finance | 1611 | Yes (audited) | 3 | 0 | 0 | 4 | 0 |
| 7 | raydium-clmm | CLMM AMM | raydium-io | 2931 | Yes (audited) | 3 | 0 | 0 | 4 | 1 |
| 8 | sol-vault | Token vault | Clish254/sol-vault | 359 | No | 2 | 0 | 0 | 3 | 0 |
| 9 | solana-staking | NFT staking | rpajo/solana-staking | 204 | No (prototype) | 2 | 2 | 0 | 3 | 0 |
| 10 | nft-staking-shuk | NFT staking | 0xShuk/NFT-Staking-Program | 170 | No | 2 | — | — | — | — |
| 11 | anchor-tictactoe | Game | coral-xyz/anchor (tests/) | 213 | Framework test | 1 | 1 | 0 | 2 | 0 |
| 12 | anchor-cashiers-check | Escrow | coral-xyz/anchor (tests/) | 180 | Framework test | 1 | 0 | 0 | 3 | 0 |
| 13 | anchor-ido-pool | IDO/Token sale | coral-xyz/anchor (tests/) | 675 | Framework test | 1 | 0 | 0 | 3 | 0 |
| 14 | anchor-cfo | DEX fees | coral-xyz/anchor (tests/) | 995 | Framework test | 1 | 0 | 0 | 3 | 0 |
| 15 | anchor-auction-house | NFT marketplace | coral-xyz/anchor (tests/) | 1745 | Framework test | 1 | 1 | 1 | 10 | 3 |

### Sealevel-Attacks Calibration (11 vulnerability categories)

| # | Attack Type | Insecure Lines | Secure Lines | Detection |
|---|------------|---------------|-------------|-----------|
| 11 | 0-signer-authorization | 17 | 21 | Static: partial |
| 12 | 1-account-data-matching | 22 | 25 | Static: partial |
| 13 | 2-owner-checks | 26 | 29 | Static: partial |
| 14 | 3-type-cosplay | 37 | 48 | Static: partial |
| 15 | 4-initialization | 38 | 38 | Static: partial |
| 16 | 5-arbitrary-cpi | 35 | 38 | Static: partial |
| 17 | 6-duplicate-mutable-accounts | 28 | 31 | Static: MISSED |
| 18 | 7-bump-seed-canonicalization | 30 | 38 | Static: MISSED |
| 19 | 8-pda-sharing | 45 | 48 | Static: MISSED |
| 20 | 9-closing-accounts | 30 | 71 | Static: partial |
| 21 | 10-sysvar-address-checking | 18 | 19 | Static: MISSED |

## Tier Definitions

- **Tier 1**: Anchor framework examples (known quality, single-file, compilable)
- **Tier 2**: Community open source (unaudited — highest chance of real bugs)
- **Tier 3**: Production protocols (audited — test for informational/FP rate)
- **Tier 4**: Known-vulnerable (sealevel-attacks — calibration dataset)

## Selection Criteria

- **Diversity**: Different domains (DEX, staking, governance, token ops, vault, escrow, vesting)
- **Complexity**: Range from simple (170 lines) to complex (2931 lines)
- **Audit status**: Mix of audited production protocols, framework examples, and community code
- **Relevance**: Financial operations with potential for logic bugs
- **Calibration**: Known-vulnerable programs for sensitivity/specificity testing

## Aggregate Statistics

- **Total programs**: 26 (15 main + 11 sealevel calibration)
- **Total lines analyzed**: ~16,000+
- **True Positives found**: 6 (anchor-multisig x2, solana-staking x2, anchor-tictactoe, anchor-auction-house)
- **Likely True Positives**: 3 (anchor-swap, anchor-escrow, anchor-auction-house)
- **False Positive rate**: 10.3% (6/58 semantic findings)
- **Bankrun confirmed**: 2 (anchor-multisig zero-threshold, empty-owners)
- **Simulation confirmed**: 3 (solana-staking x2, anchor-escrow)
- **Detector versions**: v0.3.0 → v0.4.0 → v0.5.0 (2 improvement cycles)
