# anchor-shield-v2

**Autonomous AI security agent that detects, exploits, and certifies vulnerabilities in Solana Anchor programs — end-to-end, on-chain.**

---

## 1. Agent Autonomy

anchor-shield-v2 runs a fully autonomous pipeline with zero human intervention:

- **99 commits** of agent-driven development — from static analysis to on-chain attestation
- **29 Anchor programs** analyzed across staking, escrow, multisig, lending, and DEX categories
- The agent autonomously: parses Rust source → identifies logic bugs via LLM semantic analysis → generates TypeScript exploit code → executes exploits in solana-bankrun (local SBF runtime) → publishes attestation transactions on Solana devnet
- No manual curation: the pipeline decides what to scan, how to exploit, and when to certify

## 2. Originality

No existing tool combines **detect → exploit → certify** in a single autonomous loop:

- **Semantic analysis** using Claude to find logic bugs that regex/pattern matchers miss (4 bugs found where static analysis found 0)
- **solana-bankrun exploits**: compiled `.so` binaries run in a local Solana VM — real instruction-level exploits, not simulations
- **False-positive reduction**: iterative validation reduced FP rate from **18% to 9%** over 4 refinement cycles
- **On-chain attestation**: audit results are published as verifiable Solana memo transactions, creating a tamper-proof record

## 3. Real-world Impact

This is not a toy — it found real vulnerabilities in production Anchor code:

- **PR [#4229](https://github.com/solana-foundation/anchor/pull/4229)** submitted to `solana-foundation/anchor` with **3 confirmed vulnerabilities** (High + Medium severity)
- Findings include missing signer checks, constraint logic errors, and state validation gaps in widely-used example programs
- The agent generated reproducible exploit PoCs for each finding, making triage straightforward for maintainers

## 4. Meaningful Solana Use

anchor-shield-v2 is deeply integrated with the Solana runtime:

- **9 bankrun exploits confirmed** — real compiled SBF programs executed against the Solana VM via solana-bankrun
- **4 on-chain attestations** published on Solana devnet with verifiable memo transactions
- Programs analyzed include real-world Solana projects: Orca Whirlpool, anchor-escrow, anchor-multisig, skinflip-staking, anchor-tictactoe, and a vulnerable lending protocol
- Attestation memos follow a structured format: `ANCHOR-SHIELD-AUDIT|program_id|report_hash|timestamp|score|status|severity_breakdown|version`

## 5. Fully Reproducible

Every claim is verifiable:

- **53 tests** passing in CI (unit + integration + bankrun exploits)
- **GitHub Actions CI** runs the full pipeline on every push
- **React dashboard** at the project's GitHub Pages site visualizes all findings, exploits, and attestation status
- All exploit scripts, compiled `.so` binaries, and attestation logs are committed to the repository

---

## Links

| Resource | URL |
|----------|-----|
| Repository | [github.com/mbarreiroaraujo-cloud/anchor-shield-v2](https://github.com/mbarreiroaraujo-cloud/anchor-shield-v2) |
| Dashboard | [mbarreiroaraujo-cloud.github.io/anchor-shield-v2](https://mbarreiroaraujo-cloud.github.io/anchor-shield-v2) |
| Anchor PR #4229 | [solana-foundation/anchor/pull/4229](https://github.com/solana-foundation/anchor/pull/4229) |
| CI Actions | [Actions](https://github.com/mbarreiroaraujo-cloud/anchor-shield-v2/actions) |
| Attestation: NFT-Staking | [Explorer](https://explorer.solana.com/tx/57ym3odtHi7U4d3NipJD9QgxEhwqgfCPttwg6AotA9w4eitDKMXTmmDUENd8BTsbDsyCit3UqU5uBRZ9qngSaFth?cluster=devnet) |
| Attestation: Orca | [Explorer](https://explorer.solana.com/tx/jRpD8vBoEXXkcEhYyhHKHWAY3XnqhZnqdTFkiSnEeJQtGoJNcC6zyyaVotVPL5p6osJwuDkmyfDWbJ1Wm7x6bN4?cluster=devnet) |
| Attestation: Escrow | [Explorer](https://explorer.solana.com/tx/BMecNLVQL5bDyoj51Wru41P6pUK85nD6zN7XK9x4jNbQTEQdS5UcUrUa1cjmCW9eDC33kyv57EPtd5S6JqyCe9E?cluster=devnet) |
| Attestation: Lending | [Explorer](https://explorer.solana.com/tx/44zvdFEr2khyzo3ztv5SiRoXteerknJ34hdWqqc4eYsf8khZ4LDdE1xavpKQD2kxTBbwHp8Jh9eLwdDENnHxXbe3?cluster=devnet) |
