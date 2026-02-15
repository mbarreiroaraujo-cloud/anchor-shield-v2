# Classification: anchor-ido-pool

- **Source**: coral-xyz/anchor (tests/ido-pool)
- **Domain**: IDO (Initial DEX Offering) token sale
- **Lines**: 675
- **Static findings**: 4 (2x ANCHOR-004, 2x ANCHOR-006)
- **Semantic findings**: 3

## Findings

| ID | Severity | Title | Classification | Reasoning |
|----|----------|-------|---------------|-----------|
| SEM-001 | Medium | user_authority in ExchangeRedeemableForWatermelon/WithdrawFromEscrow is AccountInfo without Signer | INFORMATIONAL | Intentional design — comments explain "allows anyone to redeem on their behalf and prevents forgotten/leftover tokens." Tokens go to user's account (constraint validated), not attacker's. |
| SEM-002 | Low | ido_name length not validated | INFORMATIONAL | `name_data[..name_bytes.len()].copy_from_slice(name_bytes)` panics if name > 10 chars. Only ido_authority (Signer) can call initialize_pool, so self-inflicted DoS. Retry with shorter name. |
| SEM-003 | Low | u128 to u64 truncation in watermelon_amount | INFORMATIONAL | `(amount * pool_watermelon / supply) as u64` — intermediate u128 result divided back is bounded by pool size (u64). Cannot exceed u64::MAX in practice. |

## Assessment

0 true positives, 3 informational. Well-structured IDO program with proper PDA validation, access control phases, and intentional permissionless redemption design. Static scanner's 4 findings are all from the intentional AccountInfo design on user_authority (explicitly commented in source).
