# anchor-shield-v2

Adversarial security agent for Solana programs. Finds logic vulnerabilities
invisible to regex scanners, then proves them on the Solana runtime.

## What it does

1. **Static scan** — 7 regex patterns for common Anchor mistakes
2. **Semantic analysis** — LLM reads the code and finds logic bugs
3. **Exploit generation** — Produces bankrun TypeScript exploits
4. **Runtime proof** — Executes exploits against compiled SBF binaries

## Results

| Metric | Value |
|--------|-------|
| Programs analyzed | 9 real-world + 1 demo |
| True Positives found | 9 (bankrun-confirmed) |
| Domains covered | Governance, Gaming, DeFi, NFT Staking, Lending |
| False Positive rate | 18% (3/17 semantic findings on real programs) |
| Compiled binaries | 5 programs (203–258 KB) |
| Execution logs | 9 verbatim bankrun logs |

## Quick start

```bash
# Run the scanner
pip install -r requirements.txt
python -m scanner.cli path/to/lib.rs

# Run a bankrun exploit
cd exploits && npm install
npx ts-node bankrun_exploit_tictactoe_001_inverted_constraint.ts
```

## Evidence

Every True Positive has a complete evidence chain:
- Source code in `real-world-targets/<program>/lib.rs`
- Compiled binary in `real-world-targets/<program>/<name>.so`
- Bankrun exploit in `exploits/bankrun_exploit_<program>_*.ts`
- Execution log in `exploits/*_execution.log`
- Summary in [EXECUTION_EVIDENCE.md](EXECUTION_EVIDENCE.md)

## Documentation

- [RESEARCH_REPORT.md](RESEARCH_REPORT.md) — Full methodology and results
- [EXECUTION_EVIDENCE.md](EXECUTION_EVIDENCE.md) — Bankrun execution proof
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design

## License

MIT
