# Real-World Validation Targets

Programs analyzed for validation of anchor-shield-v2's semantic analysis capabilities.

## Compiled Programs with Bankrun-Confirmed TPs

| # | Program | Domain | Source | Lines | Compiled | Binary Size | TPs | Notes |
|---|---------|--------|--------|-------|----------|-------------|-----|-------|
| 1 | anchor-multisig | Governance | coral-xyz/anchor | 280 | YES | multisig.so (219KB) | 2 | Zero threshold + empty owners |
| 2 | anchor-tictactoe | Gaming | coral-xyz/anchor | 213 | YES | tictactoe.so (203KB) | 1 | Inverted constraint deadlock |
| 3 | anchor-escrow | DeFi/Escrow | coral-xyz/anchor | 260 | YES | anchor_escrow.so (258KB) | 1 | Cancel without signer |
| 4 | solana-staking | NFT Staking | rpajo/solana-staking | 204 | YES | skinflip_staking.so (239KB) | 2 | Incomplete unstake + missing signer |
| 5 | anchor-auction-house | NFT Marketplace | coral-xyz/anchor | 1,745 | FAILED | — | 0 | Requires Metaplex IDL |
| 6 | vuln-lending | Lending (demo) | Internal | ~200 | YES | vuln_lending.so (204KB) | 3 | Collateral bypass + overflow |

**Compilation Rate**: 5/6 (83%) — all single-file programs <500 lines compiled successfully.

## Full Research Corpus

**26 programs analyzed** across 3 batches for comprehensive validation.

**Aggregate Metrics**:
- Total semantic findings: 58
- True Positives: 6 (10.3%)
- Likely True Positives: 3 (5.2%)
- Informational: 43 (74.1%)
- False Positives: 6 (10.3%)

**Iterative Improvement**:
- **Batch 1** (10 programs): 31 findings, 9.7% FP rate
- **Detector v0.4.0** applied: +11 prompt rules, PDA filtering
- **Batch 3** (5 programs): 27 findings, 11.1% FP rate
- **Detector v0.5.0** applied: address batch 3 FP patterns
- **Final FP rate**: 10.3%

**By Program Category**:
- Unaudited community programs: 0% FP rate (2 TPs found)
- Anchor framework tests: 14% FP rate (4 TPs found)
- Audited production protocols: 0% FP rate (0 TPs, informational only)

See [RESEARCH_REPORT.md](../RESEARCH_REPORT.md) for complete analysis.
