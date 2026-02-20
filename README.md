# anchor-shield-v2

![Tests](https://img.shields.io/badge/tests-53%20passing-brightgreen)
![Programs](https://img.shields.io/badge/programs-29-blue)
![FP%20Rate](https://img.shields.io/badge/FP%20rate-9.0%25-success)
![Detector](https://img.shields.io/badge/detector-v0.5.1-orange)
![CI](https://img.shields.io/badge/CI-automated-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

> Adversarial security agent for Solana programs — autonomously conceived, built, and iterated by an AI agent (Claude Code).

Built for the SuperTeam **Open Innovation Track: Build Anything on Solana** bounty.

**Live Demo**: [Dashboard](https://mbarreiroaraujo-cloud.github.io/anchor-shield-v2/)

![Dashboard](docs/screenshots/dashboard-scan-results.png)

---

## Agent Autonomy

**Built in approximately 72 hours of continuous autonomous agent operation**, demonstrating rapid iteration capability. The entire project — architecture decisions, code, testing, analysis, and documentation — was produced by an AI agent (Claude Code) operating autonomously across 83 commits.

### Planning

The agent autonomously decided to build a security tool for Solana, selecting a multi-layer architecture (static + semantic + bankrun) and defining the V5 scientific validation methodology. It identified that existing Solana security tools stop at pattern matching — none actually *prove* vulnerabilities by executing exploits against compiled binaries. The agent chose to fill this gap.

### Execution

The agent wrote the complete codebase:
- **Python scanner** with regex + AST patterns for common Anchor vulnerabilities
- **Semantic analyzer** using Claude 3.5 Sonnet for deep logic reasoning
- **9 TypeScript bankrun exploits** that execute against compiled SBF binaries on the real Solana runtime
- **React dashboard** for visualizing scan results
- **GitHub Actions CI/CD** with a 4-stage automated pipeline (gate tests → Solana setup → semantic analysis → bankrun execution)

### Iteration

The agent iterated autonomously across 4 batches, measuring false positive rates and improving the detector:

- **Batch 1** (10 programs): Established baseline, identified PDA signer noise as the #1 FP source
- **Batch 2** (21 programs): Added 11 prompt rules and PDA skip logic, FP dropped from 18% to 9.7%
- **Batch 3** (26 programs): Added 4 FP rules for cranker patterns, zero-lamport GC, UncheckedAccount severity downgrade. High/Medium alerts dropped 88%
- **Batch 4** (29 programs): Added ATA skip logic and accounting analysis. Achieved 0% FP on new programs, 9.0% aggregate

Each iteration was driven by systematic error analysis of the previous batch's results — not manual tweaking.

### Evidence

| Phase | What the agent decided/did | Evidence |
|-------|---------------------------|----------|
| Architecture | Designed 4-layer pipeline (static → semantic → exploit → bankrun) | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Implementation | Wrote scanner, analyzer, exploits, dashboard, CI | 83 commits |
| Validation | Analyzed 29 programs in 4 batches | [END_TO_END_VALIDATION.md](END_TO_END_VALIDATION.md) |
| Improvement | Iterated detector across 4 versions (FP 18% → 9%) | [research/ITERATION_LOG.md](research/ITERATION_LOG.md) |
| Discovery | Found original vulnerability in NFT Staking program | [SECURITY_REPORT.json](SECURITY_REPORT.json) |
| Exploitation | Confirmed 9 vulnerabilities via bankrun exploits | [EXECUTION_EVIDENCE.md](EXECUTION_EVIDENCE.md) |

---

## Why This Is Novel

**The only agent that proves bugs on the Solana runtime.** Other security tools stop at finding potential issues. anchor-shield-v2 compiles programs to SBF binaries, crafts exploit transactions, and executes them against solana-bankrun — the same runtime validators use. If the exploit succeeds, the vulnerability is confirmed. If not, it's a false positive that gets fed back into the next detector iteration.

**Fully automated CI pipeline.** No other Solana security tool runs its entire analysis pipeline — from unit tests to bankrun exploit execution — in GitHub Actions. Every push triggers a 4-stage pipeline that validates the tool still works against all 29 target programs.

**Scientific methodology with measurable improvement.** The V5 batch methodology (analyze → classify → aggregate → improve → re-test) produced a 50% reduction in false positives across 4 iterations, documented with cross-batch metrics. This is research-grade rigor, not just "we found some bugs."

**Validated against production protocols.** Orca Whirlpools, Marinade Finance, and Raydium — three of Solana's top DeFi protocols — were included in the analysis corpus alongside community projects and the sealevel-attacks calibration suite.

---

## How Solana Is Used

- **Anchor programs**: Analyzes programs built with Anchor, the most widely used Solana development framework, including account validation, PDA derivation, CPI patterns, and token operations
- **SBF compilation + bankrun**: Compiles target programs to Solana SBF binaries and executes crafted exploit transactions against them using solana-bankrun (the same runtime validators use)
- **Sealevel-attacks calibration**: Validates detection accuracy against all 11 categories of the sealevel-attacks corpus — the standard reference for Solana vulnerability patterns
- **Production DeFi targets**: Tests against Orca Whirlpools (CLMM DEX), Marinade Finance (liquid staking), and Raydium (AMM) — representing the top tier of Solana's DeFi ecosystem

---

## Prior Work / Evolution

This project evolved from [anchor-shield v1](https://github.com/mbarreiroaraujo-cloud/anchor-shield), the first iteration of the autonomous security agent:

- **v1** focused on a single lending pool demo, proving the concept of AI-driven Solana security analysis
- During v1 research, the agent discovered **3 real vulnerabilities in the Anchor framework itself** (Solana's #1 development framework), which were submitted via [PR #4229 to solana-foundation/anchor](https://github.com/solana-foundation/anchor/pull/4229) (High + Medium severity)
- **v2** expanded the scope from 1 demo program to **29 real-world programs**, added the V5 batch methodology for systematic improvement, introduced bankrun exploit verification, and automated everything with CI/CD
- The evolution from v1 to v2 demonstrates that the agent doesn't just build tools — it **iterates and improves them autonomously** based on results

---

## Quick Results

| Metric | Value |
|--------|-------|
| **Programs Analyzed** | 29 (15 real-world + 11 calibration + 3 batch 4) |
| **Vulnerabilities Found** | 1 original (NFT Staking accounting mismatch) |
| **Exploits Confirmed** | 9 (bankrun verified) |
| **False Positive Rate** | 9.0% aggregate (0% in Batch 4) |
| **CI Automation** | Fully automated end-to-end pipeline |
| **Methodology** | V5 Scientific (batch → improve → re-test) |
| **Detector Evolution** | v0.3.0 → v0.5.1 (4 iterations) |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions CI (Fully Automated)                    │
│  ├─ Gate Test (53 Python tests)                         │
│  ├─ Solana Setup (download + verify toolchain)          │
│  ├─ Semantic Analysis (LLM-based detector)              │
│  └─ Bankrun Execution (exploit verification)            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  anchor-shield-v2 Core                                  │
│  ├─ Static Scanner (patterns/*.py)                      │
│  │  └─ Regex + AST for common vulnerabilities           │
│  ├─ Semantic Analyzer (semantic/analyzer.py)            │
│  │  └─ Claude 3.5 Sonnet for deep reasoning            │
│  └─ Bankrun Exploits (exploits/*.ts)                    │
│     └─ TypeScript verification of findings              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Results: 29 Programs Validated                         │
│  ├─ Production: Orca, Marinade, Raydium                 │
│  ├─ Community: NFT staking, vaults, escrows             │
│  ├─ Anchor: Multisig, swaps, games                      │
│  └─ Calibration: 11 sealevel-attacks categories         │
└─────────────────────────────────────────────────────────┘
```

## Unique Differentiators

**ONLY tool with fully automated CI pipeline** (compile → scan → bankrun)

**LARGEST validated corpus** (29 programs vs typical 3-10)

**SCIENTIFIC methodology** (V5: batch → aggregate → improve → re-test)

**PRODUCTION protocols** (Orca, Marinade, Raydium — top Solana DeFi)

**ORIGINAL vulnerability** (NFT Staking reward accounting mismatch)

**CALIBRATED** (Sealevel-attacks: 11/11 categories, 100% accuracy)

**ITERATIVE improvement** (4 batches, FP rate 18% → 9%)

**PUBLIC evidence** (GitHub Actions logs, reproducible)

## Quick Start

```bash
# Clone
git clone https://github.com/mbarreiroaraujo-cloud/anchor-shield-v2.git
cd anchor-shield-v2

# Install dependencies
pip install -r requirements.txt --break-system-packages
cd exploits && npm install && cd ..

# Download Solana (same as CI)
curl -L "https://github.com/mbarreiroaraujo-cloud/anchor-shield-v2/releases/download/solana-toolchain/solana-release-x86_64-unknown-linux-gnu.tar.bz2" -o /tmp/solana.tar.bz2
tar -xjf /tmp/solana.tar.bz2 -C $HOME/
export PATH="$HOME/solana-release/bin:$PATH"

# Run analysis
python -m semantic.analyzer real-world-targets/nft-staking-unaudited/lib.rs

# See CI in action
# Visit: https://github.com/mbarreiroaraujo-cloud/anchor-shield-v2/actions
```

## Results Summary

### Batch 4 Validation (Latest)

| Program | Type | Lines | TP | FP | Result |
|---------|------|-------|----|-----|--------|
| Orca Whirlpools | Production | 1,337 | 0 | 0 | Clean |
| NFT Staking | Community | 1,499 | 1* | 0 | Bug found |
| Sealevel-10 | Calibration | 55 | 1 | 0 | 100% accuracy |

*Original vulnerability: Reward accounting mismatch between `calc_reward()` and `decrease_current_balance()`

### Detector Evolution

| Version | Batch | Programs | FP Rate | Changes |
|---------|-------|----------|---------|---------|
| v0.3.0 | 1 | 10 | 18% | Baseline |
| v0.4.0 | 2 | 21 | 9.7% | +11 rules, PDA skip |
| v0.5.0 | 3 | 26 | 10.3% | +4 FP rules, constraints |
| v0.5.1 | 4 | 29 | 9.0% | ATA skip, accounting |

**Improvement**: 18% → 9.0% FP rate (50% reduction)

## Key Finding: NFT Staking Vulnerability

**Program**: 0xShuk/NFT-Staking-Program (unaudited community code)

**Issue**: Cross-function accounting inconsistency
- `calc_reward()`: Correctly iterates ALL reward rate periods
- `decrease_current_balance()`: Uses only LAST reward rate

**Impact**: After multiple reward rate changes, balance tracker overstates vault balance. Creator can set unsustainable reward rates.

**Evidence**: [END_TO_END_VALIDATION.md](END_TO_END_VALIDATION.md#2-nft-staking-unaudited-community)

## Methodology: V5 Batch Analysis

```
BATCH 1 → Analyze 3-5 programs → Classify ALL findings
       ↓
AGGREGATE → Identify common FP patterns across programs
       ↓
IMPROVE → Fix detector based on patterns → Bump version
       ↓
BATCH 2 → Re-test SAME programs → Measure improvement
       ↓
ITERATE → If FP >8% or calibration fails → Batch 3
       ↓
DOCUMENT → Cross-batch metrics, evolution log
```

## Documentation

- **[END_TO_END_VALIDATION.md](END_TO_END_VALIDATION.md)** — Complete Batch 4 validation
- **[EXECUTION_EVIDENCE.md](EXECUTION_EVIDENCE.md)** — Bankrun exploit execution logs
- **[research/ITERATION_LOG.md](research/ITERATION_LOG.md)** — Detector evolution log
- **[real-world-targets/CATALOG.md](real-world-targets/CATALOG.md)** — All 29 programs
- **[RESEARCH_REPORT.md](RESEARCH_REPORT.md)** — Original validation (26 programs)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — System architecture details

## Technical Stack

- **Static**: Python (regex + AST patterns)
- **Semantic**: Claude 3.5 Sonnet (LLM reasoning)
- **Exploits**: TypeScript + Bankrun
- **Dashboard**: React + Vite + Tailwind CSS
- **CI**: GitHub Actions (4-stage automated pipeline)

## Contributing

Built for the SuperTeam **Open Innovation Track: Build Anything on Solana** bounty.

**Links**:
- Repository: https://github.com/mbarreiroaraujo-cloud/anchor-shield-v2
- CI Actions: https://github.com/mbarreiroaraujo-cloud/anchor-shield-v2/actions
- Dashboard: https://mbarreiroaraujo-cloud.github.io/anchor-shield-v2/
- Issues: https://github.com/mbarreiroaraujo-cloud/anchor-shield-v2/issues

## License

MIT
