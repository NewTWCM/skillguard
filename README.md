<p align="center">
  <img src="https://img.shields.io/badge/SkillGuard-v2.3-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Security-Extreme--Hardening-red?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Audit-Red--Team--Verified-f96?style=for-the-badge" />
</p>

# 🛡️ SkillGuard

[**繁體中文版說明 (README_zh.md)**](README_zh.md)

**Three-Layer Runtime Defense for AI Agent Plugin Ecosystems**

SkillGuard v2.3 (Extreme Hardening Edition) is a runtime verification protocol designed to protect AI Agent environments (Claude Code, Cursor, MCP) from malicious 3rd-party skills and toolsets.

> **Red-Team Verified**: This version includes advanced countermeasures against Tool Hijacking, Out-of-Band (OOB) Variable Injection, and Python Environment Hijacking, identified during our internal 4-Expert Security Workshop.

---

## ⚡ Multi-Link Defense Architecture

```
┌─────────────────────────────────┐
│       LAYER 3: ENV & INTEGRITY  │ ┐
│      PATH Sanitization + L3+    │ │ "Absolute Path Control"
└─────────────────────────────────┘ │
               │                    │
               ▼                    │
┌─────────────────────────────────┐ │
│      LAYER 2: ADVANCED SCAN     │ ┼─ Zero-Trust Runtime
│   OOB Inject, Time-Bombs, Hooks │ │
└─────────────────────────────────┘ │
               │                    │
               ▼                    │
┌─────────────────────────────────┐ │
│      LAYER 1: HONEYPOT DECOYS   │ ┘
│    Immutable files at targets   │
└─────────────────────────────────┘
```

---

## 🔬 Threat Intelligence: Why SkillGuard?

### Case Study #1: The `gstack` Telemetry Backdoor
In early 2026, a popular Claude Code skill named `gstack` was found exfiltrating user insights. **SkillGuard detected this bypass** using Layer 1 (Honeypot) and Layer 2 (Vector #2).

### Case Study #2: Tool & Environment Hijacking
Advanced hackers attempt to override system binaries (like `shasum`). **SkillGuard v2.3 utilizes Absolute Path Locking** and `$PATH` sanity checks to ensure the security tools themselves haven't been tampered with.

---

---

## ☕ Support My Research
If SkillGuard has helped secure your AI Agent environment, consider supporting further development:
- [**GitHub Sponsors**](https://github.com/sponsors/NewTWCM) (Recommended)
- [**Buy Me a Coffee**](https://www.buymeacoffee.com/NewTWCM) (If available)

### 1. Install & Seal
Deploys honeypots and computes the Layer 3 checksum to prevent tampering.
```bash
chmod +x skillguard.sh
./skillguard.sh install
```

### 2. Full Security Scan
Run this on any plugin or skill directory before use.
```bash
./skillguard.sh scan /path/to/suspicious-skill
```

### 3. Routine Check
Check honeypot integrity and self-integrity.
```bash
./skillguard.sh check
```

---

## 📂 Project Structure

- `skillguard.sh`: Core defense logic (Bash).
- `patterns.db`: Malware signature database.
- `_quarantine/`: Secure storage for detected malicious skills.

---

## 🔬 Publication & Research

SkillGuard is part of a broader research initiative into **AI Tool Governance**. See the [Abstract](abstract.md) for academic details.

If you find this useful, please cite:
```bibtex
@misc{skillguard2026,
  title={SkillGuard: Three-Layer Runtime Defense Against Malicious AI Agent Plugins},
  author={CM Fang},
  year={2026}
}
```

---

## ⚖️ License
MIT License. See [LICENSE](LICENSE) for details.
