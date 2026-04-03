# SkillGuard: Three-Layer Runtime Defense Against Malicious AI Agent Plugins

**Abstract**

The rapid evolution of LLM-based agentic ecosystems (e.g., Claude Code, Cursor, MCP servers) has introduced a new, critical attack surface: third-party plugins (skills) that execute with elevated privileges. Recent incidents, such as the *gstack* telemetry scandal, demonstrate that malicious plugins can silently exfiltrate business insights, hijack development hooks, and compromise supply chain integrity without user awareness.

We present **SkillGuard**, a lightweight, three-layer runtime defense system designed to secure AI agent plugin environments. SkillGuard specifically addresses the vulnerabilities of **supply chain integrity** within the agent's package manager context, the persistent threat of **malicious telemetry**, and **behavioral anomalies** such as time-delayed exfiltration ("time-bombs"). Layer 1 utilizes proactive, immutable honeypot decoys at known malware write targets. Layer 2 implements a deterministic, multi-vector scan engine (v2.2) to identify environment hijacking (PYTHONPATH), credential exfiltration, and LLM-targeted prompt injection. Layer 3 introduces a novel multi-link self-integrity verification mechanism using SHA256 cryptographic sealing to prevent privileged attackers from disabling the defense.

Our evaluation against real-world malicious skill variants demonstrates high detection rates with minimal performance overhead (<1s total overhead). SkillGuard moves AI agent security from semantic prompting layers to deterministic, cryptographic runtime validation, providing a pragmatically secure framework for high-stakes AI-assisted development environments.

**Keywords**: AI Agent Security, LLM Plugins, MCP Servers, Runtime Defense, Honeypots, Supply Chain Security.
