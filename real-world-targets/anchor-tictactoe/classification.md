# Classification: anchor-tictactoe

- **Source**: coral-xyz/anchor (tests/tictactoe)
- **Domain**: On-chain game
- **Lines**: 213
- **Static findings**: 0
- **Semantic findings**: 3

## Findings

| ID | Severity | Title | Classification | Reasoning |
|----|----------|-------|---------------|-----------|
| SEM-001 | Critical | Inverted game_state constraint prevents player_o from joining | TRUE POSITIVE | `Playerjoin` has constraint `game.game_state != 0`, but after `initialize`, game_state is 0 (default). This means `game_state != 0` → false, so player_o can NEVER join. Games are permanently stuck in Waiting state. Should be `game_state == 0`. |
| SEM-002 | Medium | Array out-of-bounds on player_move ≥ 9 | INFORMATIONAL | `game.board[player_move as usize]` panics if player_move ≥ 9 (u8 allows 0-255, board is [u8; 9]). Transaction just fails — self-inflicted DoS, not exploitable. |
| SEM-003 | Low | Unchecked addition on game_count | INFORMATIONAL | `dashboard.game_count + 1` could overflow at u64::MAX. Astronomically unlikely. |

## Assessment

1 true positive (inverted constraint makes game completely unplayable), 2 informational.

The constraint `game.game_state != 0` on line 82 should be `game.game_state == 0` to allow joining only when the game is in Waiting state. As written, the entire game logic is broken — no game can progress past initialization.
