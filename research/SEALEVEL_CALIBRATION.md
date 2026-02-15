# Sealevel-Attacks Calibration Report

Source: coral-xyz/sealevel-attacks — 11 known vulnerability categories with insecure/secure/recommended variants.

## Methodology

For each attack type:
1. **Static scanner** was run on insecure, secure, and recommended variants
2. **Manual semantic analysis** assessed what the LLM-based analyzer should detect
3. Results compared to ground truth (known vulnerability in each insecure variant)

## Calibration Matrix

### Static Scanner Results

| # | Attack Type | Insecure Detected? | Secure Detected? | Recommended Detected? | Notes |
|---|------------|-------------------|-----------------|----------------------|-------|
| 0 | Signer Authorization | PARTIAL (ANCHOR-006) | FP (ANCHOR-006) | CLEAN | Catches raw AccountInfo but equally flags secure version |
| 1 | Account Data Matching | PARTIAL (004+006) | FP (004+006) | CLEAN | Same issue: can't distinguish manual validation |
| 2 | Owner Checks | PARTIAL (004+006) | FP (004+006) | CLEAN | Same pattern |
| 3 | Type Cosplay | PARTIAL (004+006) | FP (004+006) | CLEAN | Same pattern |
| 4 | Initialization | PARTIAL (004+006) | FP (004+006) | CLEAN | Same pattern |
| 5 | Arbitrary CPI | PARTIAL (004+006 x5) | FP (004+006 x5) | CLEAN | Flags raw accounts, not the CPI issue |
| 6 | Duplicate Mutable | MISSED | MISSED | CLEAN | Uses typed Account, not raw AccountInfo |
| 7 | Bump Seed Canon. | MISSED | MISSED | CLEAN | Logic-level issue, no regex pattern |
| 8 | PDA Sharing | MISSED | MISSED | CLEAN | Logic-level issue, no regex pattern |
| 9 | Closing Accounts | PARTIAL (004+006) | FP (004+006 x6) | FP (004+006) | Scanner flags raw AccountInfo, not the actual close bug |
| 10 | Sysvar Address | MISSED | MISSED | CLEAN | No pattern for sysvar validation |

### Static Scanner Summary

- **True detections (catches the insecure variant)**: 7/11 (64%) — but only superficially (flags raw AccountInfo, not the actual vulnerability)
- **False positives on secure code**: 7/11 (64%) — equally flags the manually-secured versions
- **Clean detections (insecure YES, secure NO)**: 0/11 (0%) — scanner NEVER correctly distinguishes insecure from secure when both use raw AccountInfo
- **Total misses (logic-level bugs)**: 4/11 (36%) — duplicate mutable, bump seed, PDA sharing, sysvar

**Key insight**: The static scanner detects a CORRELATED pattern (raw AccountInfo) rather than the ACTUAL vulnerability. It catches programs that use older patterns but cannot tell if the vulnerability is manually mitigated in the instruction logic. The recommended Anchor patterns (typed accounts) correctly resolve all findings.

### Semantic Analysis Calibration (What LLM Should Detect)

| # | Attack Type | LLM Should Detect Insecure? | Key Pattern for LLM | Difficulty |
|---|------------|---------------------------|---------------------|------------|
| 0 | Signer Authorization | YES | `authority: AccountInfo` without `is_signer` check | Easy |
| 1 | Account Data Matching | YES | Token data read without `authority.key == token.owner` validation | Easy |
| 2 | Owner Checks | YES | Token data accessed without `token.owner == spl_token::ID` | Medium |
| 3 | Type Cosplay | YES | Manual deserialization without discriminator check — Metadata can be passed as User | Medium |
| 4 | Initialization | YES | No check if account already initialized — authority can be overwritten | Medium |
| 5 | Arbitrary CPI | YES | `token_program` is raw AccountInfo, attacker can pass malicious program | Easy |
| 6 | Duplicate Mutable | MAYBE | Same account passed as both user_a and user_b, data overwritten | Hard (subtle) |
| 7 | Bump Seed Canon. | UNLIKELY | Non-canonical bump allows multiple PDAs for same seeds | Hard (Solana-specific) |
| 8 | PDA Sharing | MAYBE | PDA seeds don't include withdraw_destination, pools share authority | Hard (architectural) |
| 9 | Closing Accounts | YES | Data not zeroed after closing, account can be resurrected | Medium |
| 10 | Sysvar Address | YES | `rent` is raw AccountInfo, attacker can pass fake rent account | Easy |

### Expected LLM Detection Rate

- **Should detect (Easy + Medium)**: 8/11 (73%)
- **Might detect (Hard)**: 2-3/11 (18-27%)
- **Unlikely to detect**: 1/11 (9%) — bump seed canonicalization

### Semantic Analysis Should NOT Flag Secure/Recommended Variants

For each secure variant, the LLM should recognize the mitigation:
- Secure versions that manually check (0-5, 9, 10): LLM should see the validation code
- Recommended versions using Anchor types: LLM should understand Anchor constraints
- Expected false positive rate on secure code: <10% (LLM should be better than regex at understanding manual mitigations)

## Key Findings

### 1. Static scanner detects correlation, not causation
The regex patterns catch programs using raw `AccountInfo` — a pattern CORRELATED with vulnerabilities but not the vulnerability itself. Many programs use raw AccountInfo with proper manual validation.

### 2. Four vulnerability classes are invisible to regex
Duplicate mutable accounts, bump seed canonicalization, PDA sharing, and sysvar address spoofing leave no syntactic signature that regex can match. These are pure logic bugs requiring semantic understanding.

### 3. Recommended Anchor patterns eliminate regex findings
Using `Account<'info, T>`, `Signer<'info>`, `Program<'info, T>`, and `Sysvar<'info, T>` resolves all scanner findings. This validates that Anchor's type system is the correct defense for patterns 0-5, 9, 10.

### 4. Logic bugs require LLM reasoning
Patterns 6 (duplicate mutable), 7 (bump seed), and 8 (PDA sharing) require understanding the MEANING of the code, not just its syntax. These are the highest-value targets for semantic analysis.

## Implications for Detector Improvement

1. **Reduce static scanner false positives**: Check for manual validation in the instruction body before flagging raw AccountInfo
2. **Add semantic prompt guidance**: Add specific rules for each sealevel-attack category
3. **Calibrate severity**: Raw AccountInfo usage should be Medium/Informational when the program contains manual checks
4. **Focus LLM on logic bugs**: The unique value of semantic analysis is patterns 6-8 — train the prompt to look for these specifically
