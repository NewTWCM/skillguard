<p align="center">
  <img src="https://img.shields.io/badge/SkillGuard-v2.3-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/資安防護-終極加固版-red?style=for-the-badge" />
  <img src="https://img.shields.io/badge/驗證-紅藍攻防實測-f96?style=for-the-badge" />
</p>

# 🛡️ SkillGuard (中文版)

**AI 代理程式 (AI Agent) 插件環境的三層執行期防禦協議**

SkillGuard v2.3 (終極加固版) 是一套專為 Claude Code、Cursor、MCP 伺服器等 AI 代理程式設計的執行期安全驗證工具。旨在防止惡意插件（Skills）在背後竊取資料、劫持系統 Hook 或進行供應鏈污染攻擊。

> **背景故事**：起源於 2026 年初的 `gstack` 遙測背門事件——當時一個熱門插件被發現正秘密將使用者的商業機密上傳至外部伺服器。SkillGuard 便是為了終結此類「特權代理程式」漏洞而生。

---

## ⚡ 三層防禦架構 (Three-Layer Architecture)

```
┌─────────────────────────────────┐
│     第三層：環境與完整性校驗     │ ┐
│    路徑淨化 + 絕對路徑指令鎖定   │ │ 「管控執行環境的物理邊界」
└─────────────────────────────────┘ │
               │                    │
               ▼                    │
┌─────────────────────────────────┐ │
│     第二層：進階行為向量掃描     │ ┼─ 零信任執行環境 (Zero-Trust)
│   變數注入、定時炸彈、掛鉤劫持   │ │
└─────────────────────────────────┘ │
               │                    │
               ▼                    │
┌─────────────────────────────────┐ │
│      第一層：誘餌式蜜罐監測      │ ┘
│    在敏感位置部署不可變偵測檔    │
└─────────────────────────────────┘
```

---

## 🔬 威脅情報分析

### 案例 1：`gstack` 遙測背門
許多 AI 插件會利用開發者的信任，悄悄讀取並上傳 `.claude/eureka.jsonl` 等敏感檔案。SkillGuard 能透過第 1 層 (蜜罐) 與第 2 層 (流量掃描) 即時發現並中斷連線。

### 案例 2：工具與環境劫持 (v2.3 新增)
高級黑客會嘗試掉包系統的 `shasum` 或 `grep` 指令。SkillGuard v2.3 通過**絕對路徑鎖定 (Absolute Path Locking)** 確保安全工具本身未被篡改，並能偵測 `$PATH` 變數是否被注入了 `/tmp` 等可疑路徑。

---

## 🚀 快速開始

### 1. 安裝與封裝 (Install & Seal)
部署蜜罐並對加密腳本進行 SHA256 簽署，防止防禦者被反向劫持。
```bash
chmod +x skillguard.sh
./skillguard.sh install
```

### 2. 進階安全掃描
在使用任何新插件或 MCP 伺服器前，執行深度的 15 向量掃描。
```bash
./skillguard.sh scan /path/to/suspicious-skill
```

### 3. 定期完整性檢查
檢查環境變數、蜜罐檔案與腳本自我 Hash 是否完好。
```bash
./skillguard.sh check
```

---

## 🔬 學術與研究

本專案不僅是一個工具，更是對 **AI 代理程式治理 (Agent Governance)** 的深度研究。我們提出了一套優於單純 Prompt 控管的「確定性、連動式」執行期防禦協議。

如果您在學術論文中引用本專案，請使用：
```bibtex
@misc{skillguard2026,
  title={SkillGuard: Three-Layer Runtime Defense Against Malicious AI Agent Plugins},
  author={CM Fang (NewTWCM)},
  year={2026}
}
```

---

---

## ☕ 支持我的研究
如果 SkillGuard 幫助您提升了 AI 代理程式的安全性，歡迎考慮支持本專案的持續研發：
- [**GitHub Sponsors**](https://github.com/sponsors/NewTWCM) (推薦方式)
- [**贊助一杯咖啡**](https://www.buymeacoffee.com/NewTWCM) (若有設定)

---

## ⚖️ 授權與宣告
MIT License. 本工具針對 AI 開發環境的安全性進行提升，使用前請詳閱代碼邏輯。
