# Classification: anchor-auction-house

- **Source**: coral-xyz/anchor (tests/auction-house)
- **Domain**: NFT marketplace (Metaplex Auction House)
- **Lines**: 1745
- **Static findings**: 89 (mostly ANCHOR-004/006 on UncheckedAccount fields used for stack size limitations)
- **Semantic findings**: 15

## Findings

| ID | Severity | Title | Classification | Reasoning |
|----|----------|-------|---------------|-----------|
| SEM-001 | High | Withdraw: authority can withdraw any user's escrow without user signature | LIKELY TRUE POSITIVE | Authority can withdraw escrowed funds to user's receipt account without user signing. Funds go to user (not stolen), but authority has custodial power. Centralization risk. |
| SEM-002 | Low | requires_sign_off flag is dead code | INFORMATIONAL | Flag is stored and updated but no instruction ever reads it. Authority is always required as signer on every instruction. |
| SEM-003 | Low | sell allows token_size=0 (no-op listing) | INFORMATIONAL | Creates a no-op trade state PDA. Wastes rent but no value extraction. |
| SEM-004 | N/A | execute_sale: buyer/seller not Signers | FALSE POSITIVE | Intentional permissionless cranker/relayer pattern. Both parties consented via buy/sell trade states. |
| SEM-005 | N/A | execute_sale: buyer_price matching between trade states | FALSE POSITIVE | Enforced by PDA seed derivation — same buyer_price in both PDA seeds. |
| SEM-006 | Low | Extreme metadata royalties + fees can make NFT sales revert | INFORMATIONAL | checked_sub prevents fund loss but malicious metadata royalties could DoS sales for specific NFTs. |
| SEM-007 | N/A | cancel: account data not explicitly zeroed | FALSE POSITIVE | Solana runtime garbage-collects zero-lamport accounts at end of slot. |
| SEM-008 | Medium | Authority can reprice seller listings to arbitrary value | INFORMATIONAL | By design when can_change_sale_price=true. Seller trusts authority by opting into free listing. |
| SEM-009 | Low | No zero-amount validation on deposit/withdraw/buy | INFORMATIONAL | No value extraction; just wasted rent/gas. |
| SEM-010 | Low | All instructions require authority co-signature (centralization) | INFORMATIONAL | Architectural design; authority is gatekeeper for all operations. |
| SEM-011 | N/A | execute_sale token_account is UncheckedAccount | FALSE POSITIVE | Validated by assert_is_ata helper function and downstream SPL token CPI. UncheckedAccount used for stack size reasons. |
| SEM-012 | Low | No buyer==seller check allows wash trading | INFORMATIONAL | Self-punishing — user pays fees. No value extraction. |
| SEM-013 | High | CreateAuctionHouse: authority not required as Signer | TRUE POSITIVE | Attacker can front-run auction house creation for any authority, setting malicious fee/treasury destinations. Authority can fix via update_auction_house, but it creates a griefing vector. |
| SEM-014 | Medium | fee_withdrawal_destination not validated as authority-owned | INFORMATIONAL | Combined with SEM-013, enables griefing. Correctable via update_auction_house. |
| SEM-015 | Low | Deposit/Buy require both wallet AND authority signatures | INFORMATIONAL | Heavy centralization design — all operations gated by authority. |

## Assessment

1 true positive (front-run griefing on auction house creation), 1 likely true positive (custodial authority withdrawal), 10 informational (centralization properties, dead code, defense-in-depth), 3 false positives (intentional permissionless patterns, Solana runtime behavior, helper function validation).

### Key Insight

The Metaplex Auction House is **intentionally highly centralized**. The authority must co-sign every operation. This is a design choice, not a bug. The only real vulnerability is SEM-013 (CreateAuctionHouse doesn't require authority signature), which enables a front-running griefing attack.

### Context Limitation

Several findings depend on the `utils` module (`crate::utils::*`) which is not available in this single-file analysis. Functions like `assert_is_ata`, `pay_creator_fees`, `get_fee_payer`, etc. are assumed to function as named.
