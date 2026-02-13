# Real-World Validation Targets

Programs acquired for real-world I+D validation of anchor-shield-v2's semantic analysis capabilities.

| # | Program | Domain | Source | Lines | Compiled | TPs | Notes |
|---|---------|--------|--------|-------|----------|-----|-------|
| 1 | anchor-swap | DEX/AMM | coral-xyz/anchor (tests/) | 496 | — | 0 | Token swap with pool logic |
| 2 | anchor-multisig | Governance | coral-xyz/anchor (tests/) | 280 | multisig.so (219KB) | 2 | Zero threshold + empty owners |
| 3 | anchor-token-proxy | Token ops | coral-xyz/anchor (tests/) | 273 | — | 0 | SPL token proxy operations |
| 4 | marinade-staking | Liquid staking | marinade-finance/liquid-staking-program | 1611 | — | 0 | Audited production protocol |
| 5 | raydium-clmm | Concentrated liquidity | raydium-io/raydium-clmm | 2931 | — | 0 | Audited production protocol |
| 6 | anchor-tictactoe | Gaming | coral-xyz/anchor (tests/) | 213 | tictactoe.so (203KB) | 1 | Inverted constraint deadlock |
| 7 | anchor-escrow | DeFi/Escrow | coral-xyz/anchor (tests/) | 260 | anchor_escrow.so (258KB) | 1 | Cancel without signer |
| 8 | solana-staking | NFT Staking | rpajo/solana-staking | 204 | skinflip_staking.so (239KB) | 2 | Incomplete unstake + missing signer |
| 9 | anchor-auction-house | NFT Marketplace | coral-xyz/anchor (tests/) | 1745 | FAILED | 0 | Requires Metaplex IDL + multi-file |

## Selection Criteria

- **Diversity**: Different domains (DEX, staking, governance, token ops)
- **Complexity**: Range from simple (273 lines) to complex (2931 lines)
- **Audit status**: Mix of audited production protocols and framework examples
- **Relevance**: Financial operations with potential for logic bugs
