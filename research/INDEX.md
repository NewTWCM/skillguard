# 投資研究主索引 (Master Manifest)

**最後更新**: 2026-04-14
**維護原則**: 此檔為**版本控制的真相來源**，避免 context 壓縮後遺失資訊。
**當規則**: 任何新增檔案、資料源、路徑、版本變更，**必須同步更新此檔**並 commit。

---

## 📐 專案架構

```
skillguard/
├── research/
│   ├── INDEX.md                                  ← 本檔 (真相來源)
│   ├── trading-strategies/                       ← 研究文件 (Markdown)
│   └── backtest/                                 ← 回測程式與資料
│       ├── data/          ← 原始快取 (git 追蹤)
│       ├── output/        ← 產出 (git 追蹤; state.json 除外)
│       └── *.py           ← 可執行 Python 模組
└── .gitignore                                    ← 已排除 runtime state
```

**所有資料抓取與分析一律用 Python** (requirement from user 2026-04-14)。
**所有產出一律 git 追蹤** (含 CSV/PNG/JSON, 執行期 state 排除)。

---

## 📚 研究文件 (Markdown Reports)

| # | 檔名 | 日期 | 主題 | 狀態 |
|---|-----|-----|------|------|
| R1 | [research/trading-strategies/2026-04-11-8zz-contrarian-indicators.md](trading-strategies/2026-04-11-8zz-contrarian-indicators.md) | 2026-04-11 | 8zz Contrarian TradingView + banini-tracker 兩個 repo 資安/回測/適用性分析 | ✅ |
| R2 | [research/trading-strategies/2026-04-11-taiwan-contrarian-ecosystem.md](trading-strategies/2026-04-11-taiwan-contrarian-ecosystem.md) | 2026-04-11 | 台股反指標生態 (Banini/Peter Kurz/謝金河/河谷/嘉偉/郭哲榮) + 制度性指標 + AAII 學術證據 | ✅ |
| R3 | [research/trading-strategies/2026-04-13-asymmetric-contrarian-literature.md](trading-strategies/2026-04-13-asymmetric-contrarian-literature.md) | 2026-04-13 | 40 年學術文獻綜述 (Shleifer-Vishny / Stambaugh / Miller / Kahneman 等 15 篇) | ✅ |
| R4 | [research/backtest/README.md](backtest/README.md) | 2026-04-13 | 回測包快速上手 | ✅ |
| R5 | [research/backtest/RESULTS.md](backtest/RESULTS.md) | 2026-04-13 | 完整回測報告 (早期版) | ✅ |
| R6 | [research/backtest/FINAL_REPORT.md](backtest/FINAL_REPORT.md) | 2026-04-13 | **最終整合報告** (實證 + 文獻 + 監控) | ✅ |
| R7 | [research/backtest/NET_RESULTS.md](backtest/NET_RESULTS.md) | 2026-04-14 | **Net-of-cost 回測** (扣交易成本/滑價) | ✅ |

---

## 🐍 Python 模組 (Executable Scripts)

### 資料抓取

| 模組 | 路徑 | 功能 | 資料源 |
|------|-----|------|-------|
| `tw_data_fetcher` | [research/backtest/tw_data_fetcher.py](backtest/tw_data_fetcher.py) | TWSE + TAIFEX 月度資料抓取 | twse.com.tw / taifex.com.tw |

### 回測

| 模組 | 路徑 | 標的 | 樣本 | 主發現 |
|------|-----|-----|-----|-------|
| `banini_backtest` | [research/backtest/banini_backtest.py](backtest/banini_backtest.py) | Banini 345 預測 | 2 年 | 整體 50% 勝率, 停損信號 80% |
| `institutional_backtest_v2` | [research/backtest/institutional_backtest_v2.py](backtest/institutional_backtest_v2.py) | TAIEX + 散戶多空比 | 5 年 | 無穩定反指標效果 |
| `us_crypto_backtest` | [research/backtest/us_crypto_backtest.py](backtest/us_crypto_backtest.py) | BTC + SPY + FNG | 7 年 | **非對稱: 恐懼有效, 貪婪無效** |
| `deep_holding_analysis` | [research/backtest/deep_holding_analysis.py](backtest/deep_holding_analysis.py) | FNG × 持有天數熱圖 | 全部 | 30 日為甜蜜點 |
| `peter_kurz_backtest` | [research/backtest/peter_kurz_backtest.py](backtest/peter_kurz_backtest.py) | Peter Kurz 20 筆呼叫 | 5 年 | **看空反向 100% 勝率** |

### 即時工具

| 模組 | 路徑 | 功能 |
|------|-----|------|
| `monitoring_dashboard` | [research/backtest/monitoring_dashboard.py](backtest/monitoring_dashboard.py) | FNG + BTC + SPY 即時監控 + Telegram 推送 |

### 成本 / 淨報酬

| 模組 | 路徑 | 功能 |
|------|-----|------|
| `costs` | [research/backtest/costs.py](backtest/costs.py) | 可配置交易成本 + 滑價模組 (8 個預設 profile) |
| `apply_costs_to_backtests` | [research/backtest/apply_costs_to_backtests.py](backtest/apply_costs_to_backtests.py) | 將成本套用至所有回測產出 Net-of-cost 報表 |

---

## 💾 原始資料快取 (Git-Tracked)

| 檔名 | 資料內容 | 區間 | 源 API |
|------|---------|------|--------|
| `data/banini-public.db` | Banini 345 筆預測 (SQLite) | 2 年 | [cablate/banini-tracker](https://github.com/cablate/banini-tracker) |
| `data/crypto_fng.csv` | Crypto Fear & Greed Index (日) | 2018-2026 | [alternative.me API](https://api.alternative.me/fng/) |
| `data/yahoo_BTC-USD.csv` | BTC-USD 日 K | 7 年 | Yahoo Finance chart API |
| `data/yahoo_SPY.csv` | SPY 日 K | 6 年 | Yahoo Finance chart API |
| `data/finmind_TaiwanStockPrice_TAIEX_*.csv` | TAIEX 日線 | 2021-2026 | [FinMind API](https://finmindtrade.com) |
| `data/finmind_TaiwanFuturesInstitutionalInvestors_TX_*.csv` | 台指期三大法人未平倉 | 2021-2026 | FinMind |
| `data/finmind_TaiwanFuturesDaily_TX_*.csv` | 台指期日成交 | 2021-2026 | FinMind |
| `data/peter_kurz_calls.json` | Peter Kurz 20 筆公開呼叫 (手動整理) | 2021-2026 | 新聞媒體交叉驗證 |
| `data/cost_profiles.json` | 自訂成本 profile (自動產生) | — | `costs.py configure` 寫入 |

---

## 📊 產出檔案 (Output, Git-Tracked)

### Banini
- `output/banini_backtest_detail.csv` — 每筆預測明細
- `output/matrix_banini_action_{return,winrate}.csv` — 動作 × 天數矩陣
- `output/heatmap_Banini_action_{return,winrate}.png` — 熱圖

### 散戶多空比
- `output/retail_ratio_daily_v2.csv` — 每日散戶多空比
- `output/retail_contrarian_best_trades.csv` — 最佳策略交易明細

### 加密 / 美股 FNG
- `output/matrix_BTC-USD_(Crypto_FNG)_{long,short}_{return,winrate}.csv`
- `output/matrix_SPY_(Crypto_FNG_as_proxy)_{long,short}_{return,winrate}.csv`
- `output/heatmap_*.png` — 8 張 FNG × 持有天數熱圖

### Peter Kurz
- `output/peter_kurz_backtest_detail.csv` — 20 筆呼叫多時間尺度報酬

### Net-of-Cost
- `output/net_of_cost_results.csv` — 所有策略 Gross vs Net 對照表

### 忽略 (runtime)
- `output/dashboard_state.json` — 監控狀態 (gitignore)

---

## 🌐 原始資料源清單 (含未實作部分)

### ✅ 已整合

| 類別 | 資料源 | URL | 採集方式 |
|------|-------|-----|---------|
| 台股日線 | FinMind `TaiwanStockPrice` | https://finmindtrade.com | Python `requests` |
| 台股法人 | FinMind `TaiwanStockInstitutionalInvestorsBuySell` | 同上 | Python |
| 台指期法人 | FinMind `TaiwanFuturesInstitutionalInvestors` | 同上 | Python |
| 台指期日資料 | FinMind `TaiwanFuturesDaily` | 同上 | Python |
| 加密幣情緒 | Alternative.me FNG | https://api.alternative.me/fng/ | Python |
| 美股/加密日線 | Yahoo Finance Chart API | https://query1.finance.yahoo.com/v8/finance/chart/ | Python |
| 名人預測 DB | cablate/banini-tracker | https://github.com/cablate/banini-tracker | Git clone SQLite |
| 名人媒體呼叫 | 新聞爬蟲 (手動) | udn/cnyes/newtalk/technews/ettoday | 手動彙整 JSON |

### 🔲 待整合 (用戶 2026-04-14 提及的缺失領域)

| 類別 | 建議資料源 | URL / API | 實作優先度 | 備註 |
|------|-----------|-----------|----------|------|
| **台股融資融券** | FinMind `TaiwanStockMarginPurchaseShortSale` | https://finmindtrade.com | 🔴 高 | 融資維持率為關鍵 L2 信號 |
| **台股券資比** | FinMind 同上 + 計算 | 同上 | 🔴 高 | 配合多空比 |
| **台股籌碼** | FinMind `TaiwanStockShareholding` | 同上 | 🟡 中 | 千張大戶持股 |
| **台股融資使用率** | TWSE 融資融券餘額表 | https://www.twse.com.tw/exchangeReport/MI_MARGN | 🟡 中 | |
| **美股期權** | Yahoo Finance options chain | https://query1.finance.yahoo.com/v7/finance/options/{symbol} | 🔴 高 | Put/Call Ratio |
| **CBOE Put/Call Ratio** | CBOE 官方 | https://www.cboe.com/us/options/market_statistics/ | 🔴 高 | 已在文獻驗證有效 |
| **VIX** | Yahoo `^VIX` | Yahoo chart API | 🔴 高 | VIX>35 為強做多信號 |
| **美股國會議員交易** | QuiverQuant / Capitol Trades | https://www.capitoltrades.com/ <br> https://api.quiverquant.com/beta/live/congresstrading | 🟡 中 | Nancy Pelosi tracker 有效 |
| **美股暗池** | CheddarFlow / FlowAlgo / UnusualWhales | https://unusualwhales.com/ (API 付費) <br> FINRA Dark Pool TRF: https://otctransparency.finra.org/otctransparency | 🟡 中 | FINRA 免費但 delay |
| **期權 Unusual Activity** | Unusual Whales / BarChart | https://www.barchart.com/options/unusual-activity | 🟢 低 | |
| **加密永續資金費率** | Binance Funding Rate | https://fapi.binance.com/fapi/v1/fundingRate | 🟡 中 | 極端 funding 可作情緒 proxy |
| **加密巨鯨** | Whale Alert | https://api.whale-alert.io/ | 🟢 低 | 需付費 API |
| **AAII 情緒調查** | AAII 週報 | https://www.aaii.com/sentimentsurvey (CSV 下載) | 🟡 中 | 週頻, 已在文獻驗證 |
| **CNN Fear & Greed** | CNN 官方 | https://production.dataviz.cnn.io/index/fearandgreed/graphdata | 🟡 中 | vs Crypto FNG 不同來源 |
| **台灣選擇權 P/C Ratio** | TAIFEX 選擇權交易量 | https://www.taifex.com.tw/cht/3/pcRatio | 🔴 高 | 制度性情緒指標 |
| **台股暗盤 (興櫃)** | 證交所 | 有限公開資料 | 🟢 低 | |

### 名人反指標候選清單

| 人物 | 領域 | 資料來源 | 已實作 |
|------|-----|---------|-------|
| 巴逆逆 (Banini/8zz) | 台股 | cablate/banini-tracker SQLite | ✅ |
| 谷月涵 (Peter Kurz) | 台股宏觀 | 媒體新聞 | ✅ 20 筆 |
| 謝金河 | 台股 | 財訊 + YouTube | 🔲 待做 |
| 河谷指標 (PTT 合稱) | 台股 | PTT Stock 板 | 🔲 待做 |
| 嘉偉老師 | 台股當沖 | YouTube 直播 | 🔲 待做 |
| 郭哲榮 | 台股 | 媒體 | 🔲 待做 |
| 韭家家母 | 散戶 | 匿名 PTT 討論 | 🔲 統計不可行 |

---

## 🗂️ Commit 歷史 (反指標研究分支)

分支: `claude/trading-strategy-research-Pbn1F`

| SHA | 日期 | 範圍 |
|-----|------|------|
| `35c8e03` | 2026-04-11 | 8zz 兩 repo 初步資安/回測分析 |
| `b61480f` | 2026-04-11 | 台灣反指標生態文件 |
| `a58bed7` | 2026-04-11 | 擴充 Peter Kurz/謝金河等 |
| `905682d` | 2026-04-13 | 5 年綜合回測 (Banini/散戶多空/FNG) |
| `05e0904` | 2026-04-13 | 非對稱深度分析 + 監控儀表板 + 學術文獻 |
| `2556d43` | 2026-04-13 | gitignore 動態狀態檔 |
| `208876a` | 2026-04-14 | Master INDEX manifest (抗 context 壓縮) |
| `(next)` | 2026-04-14 | 交易成本框架 + NET_RESULTS |

---

## 🧭 工作流程約定 (Working Agreement)

1. **所有資料一律透過 Python 抓取** — 不用 shell curl/wget 在 README 上示範
2. **所有快取進 git** — CSV/JSON/SQLite 一律追蹤 (避免重複打 API)
3. **runtime state 進 gitignore** — `dashboard_state.json` 之類
4. **更新 INDEX 比寫程式更重要** — 每次新增檔案先 commit 到此索引
5. **交易成本必須納入** — 任何勝率數字標註「gross/net of fees」
6. **新增名人反指標需要樣本 ≥ 15 筆** — 否則統計力不足
7. **新增資料源先補本檔「原始資料源清單」** — 包含 URL + API 端點 + 實作優先度

---

## 🎯 當前市場狀態 (參考, 非交易建議)

**2026-04-13 截點**:
- Crypto FNG = 12 (極度恐懼)
- BTC = $70,910 (30 日均 $69,895)
- SPY = $679.46 (30 日均 $659.35)
- 監控儀表板信號: **EXTREME_FEAR → LONG**
- 回測歷史: FNG < 15 後 30 日 BTC 平均 +4.81%, 勝率 76% (n=33)

---

## 📋 下一步任務 (排序)

1. ✅ 建立 INDEX.md (本檔)
2. ✅ 建立可配置交易成本 + 滑價 Python 模組 (`costs.py`)
3. ✅ 重跑所有回測帶入成本 → 產出 `NET_RESULTS.md`
4. ⏳ 整合台股融資維持率 L2 信號 (FinMind 新 dataset)
5. ⏳ 整合 VIX 美股強化信號
6. ⏳ 整合 CBOE / TAIFEX Put/Call Ratio
7. ⏳ 擴充 Peter Kurz 樣本至 50+ 筆
8. ⏳ 加入國會議員交易追蹤 (QuiverQuant)
9. ⏳ 加入美股期權 Unusual Activity

---

*此 INDEX 為**抗壓縮 (compaction-resistant)** 文件: Claude 下次 session 被壓縮記憶後, 只要讀此檔就能恢復完整上下文。*
