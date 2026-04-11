# 交易策略研究筆記：8zz 反指標系列

**研究日期**: 2026-04-11  
**研究對象**:
- [8zz-Contrarian-Indicator-TradingView](https://github.com/hansai-art/8zz-Contrarian-Indicator-TradingView)
- [8zz-banini-tracker](https://github.com/hansai-art/8zz-banini-tracker)

---

## 1. 概述

兩個專案皆基於同一核心假設：追蹤台灣網路人物 "Banini"（巴逆逆 / 8zz，又稱「反指標女神」、「股海冥燈」）的公開社群媒體貼文，反轉她的操作方向作為交易信號。

| 維度 | Contrarian Indicator | Banini Tracker |
|------|---------------------|----------------|
| **類型** | 靜態 Pine Script 查表指標 | 自動化 TypeScript 即時管道 |
| **語言** | Pine Script v6 | TypeScript + Pine Script v5 |
| **資料來源** | 手動策整 63 事件 | Apify 爬蟲即時抓取 Threads/Facebook |
| **分析方式** | 純事件對照（無模型） | LLM 語意分析（MiniMax-M2.5） |
| **信號推播** | 無 | Telegram / Discord / LINE |
| **可擴展性** | 需手動更新事件 | 自動持續運行（cron 每 5 分鐘） |
| **可重現性** | 確定性輸出 | LLM 非確定性（temperature=0.3） |

---

## 2. Repo 1: 8zz-Contrarian-Indicator-TradingView

### 2.1 核心機制

事件驅動查表系統，63 個手動策整事件存於平行陣列中：

- `evt_time`: Unix 時間戳（毫秒）
- `evt_dir`: 方向（+1 看多、-1 看空）
- `evt_str`: 強度（1-3 星）
- `evt_tips`: 原始 Facebook 貼文摘錄

**反轉邏輯**:
- 她買進 / 加碼 / 被套 → 看空信號
- 她停損 / 賣出 / 認賠 → 看多信號

**倉位管理**: 每次同方向信號加 20%，最高 100%（5/5）

**信號強度分級**:
- 強（3 星）: 全押、停損、畢業（爆倉）、大額虧損
- 中（2 星）: 買賣操作
- 弱（1 星）: 觀望、持有、看法表達

### 2.2 回測模式

兩種模式：
- **Mode A（固定 N-bar）**: 翻轉後 N 根 K 棒（預設 8）後檢查勝負
- **Mode B（翻轉到翻轉）**: 上一次翻轉入場價到當前收盤價的損益

### 2.3 資安評估：低風險

- Pine Script 在 TradingView 沙箱內執行，無網路請求能力
- 無 `request.security()` 外部資料調用
- 程式碼完全可讀，無混淆
- 引用之 Facebook 貼文為公開資料

### 2.4 回測問題

| 問題 | 嚴重度 | 說明 |
|------|--------|------|
| 樣本量不足 | 高 | 63 事件 → 約 15-20 翻轉信號，不具統計顯著性 |
| 無交易成本 | 中 | 不計手續費、證交稅、滑價 |
| 時間精度差 | 中 | 事件時間為 FB 發文時間，非實際交易時間 |
| 標的不匹配 | 中 | 指標測 ETF 0050，本人交易個股 |
| 二元勝負 | 中 | 不考慮獲利/虧損幅度 |
| 無前瞻性 | 高 | 事件截至 2026/4/10，之後無新信號 |

### 2.5 結論

**定位**: 娛樂/參考工具  
**聲稱勝率**: ~60%（1 小時 K 線，ETF 0050）  
**統計可信度**: 低（樣本不足）

---

## 3. Repo 2: 8zz-banini-tracker

### 3.1 系統架構

```
Apify 爬蟲 → 貼文統一格式 → 去重 → LLM 語意分析 → 反轉信號 → 多平台推播
                                                         ↓
                                              回測引擎 / 靜態網站 / TradingView 指標
```

**五大子系統**:

1. **資料擷取** (`threads.ts`, `facebook.ts`): Apify 雲端爬蟲，Facebook 含 OCR 圖片文字
2. **LLM 分析** (`analyze.ts`): OpenAI 相容 API，結構化 JSON 輸出
3. **多平台推播** (`telegram.ts`, `discord.ts`, `line.ts`): 平行發送
4. **回測引擎** (`backtest-core.ts`): TWSE/TPEX 真實日線數據
5. **TradingView 指標** (`banini-reverse-indicator.pine`): 手動 5 槽位信號標記

### 3.2 LLM 分析輸出結構

```json
{
  "mentionedTargets": [{
    "name": "股票名稱",
    "type": "stock/etf/commodity",
    "herAction": "她的操作",
    "reverseView": "反向觀點",
    "confidence": "high/medium/low",
    "reasoning": "推理依據"
  }],
  "chainAnalysis": "連鎖效應分析",
  "moodScore": 1-10,
  "actionableSuggestion": "可操作建議"
}
```

### 3.3 回測核心邏輯

**入場**: 貼文次一交易日收盤價（避免前瞻偏差）  
**出場**: 入場後 1/3/5 個交易日收盤價  

**信號方向推導**:
```typescript
function inferSignalDirection(reverseView: string): SignalDirection | null {
  if (/(上漲|反彈|續漲|走高|偏多|看多|做多|噴|漲)/.test(reverseView)) return 'long';
  if (/(下跌|續跌|走低|偏空|看空|做空|回檔|跌)/.test(reverseView)) return 'short';
  return null;
}
```

**報酬率**: `((exitClose - entryClose) / entryClose) * 100`  
**勝率**: `wins / (wins + losses) * 100`（平盤排除）

### 3.4 資安評估：中等風險

| 風險 | 嚴重度 | 說明 |
|------|--------|------|
| API 金鑰管理 | 中 | `.env` 存放，無加密/vault |
| LLM 輸出無 runtime 驗證 | 中 | `JSON.parse()` 直接解析，無 Zod 等 schema 驗證 |
| Webhook 洩漏 | 中 | Discord/Telegram token 洩漏可被濫用 |
| 無成本上限 | 低 | 回測 300 篇 × LLM 呼叫，無預算防護 |
| TWSE/TPEX API 無限速 | 低 | 大量請求可能被封鎖 IP |
| `any` 型別斷言 | 低 | Apify 格式變更時靜默產生垃圾資料 |
| 靜態網站無驗證 | 低 | 全部分析歷史公開（設計如此） |

**正面**:
- AbortSignal 超時控制（120s/180s/60s）
- `seen.json` 限制 500 筆
- `.gitignore` 排除 `.env`

### 3.5 回測優缺點

**優點**:
- ✅ 次一交易日入場，避免前瞻偏差
- ✅ 多視窗（1/3/5 日）前瞻報酬
- ✅ 平盤排除，不灌水勝率
- ✅ 真實 TWSE/TPEX 日線數據
- ✅ ROC 日期正確轉換

**缺點**:
- ❌ LLM 非確定性（temperature=0.3），回測不可重現
- ❌ 無交易成本（台灣證交稅 0.3%、手續費 0.1425%）
- ❌ 存活者偏差（下市股票被跳過）
- ❌ 無基準比較（隨機基線/大盤報酬）
- ❌ 無倉位管理/組合分析
- ❌ 僅測個股/ETF，忽略商品/指數信號

---

## 4. 對投資開發案之應用評估

### 4.1 可借鑑之處

1. **社群情緒反指標框架**  
   爬取 → LLM 分析 → 信號生成 → 通知 的管道架構可泛化，追蹤多個散戶意見領袖

2. **LLM 語意分析管道**  
   從非結構化社群貼文提取結構化交易信號，但需改良可重現性

3. **連鎖效應分析 (Chain Analysis)**  
   推導產業連動關係（油價跌 → 製造業受益 → 電子股漲），適用於多資產策略

4. **Pine Script 複合評分**  
   多信號加權聚合成單一分數的設計值得參考

### 4.2 不建議直接採用

1. **單一人物依賴**: 統計顯著性不足，需擴展至多帳號
2. **無風控機制**: 無最大回撤、部位限制、停損
3. **回測方法論不足**: 缺交易成本、Walk-forward、蒙地卡羅模擬

### 4.3 改良方向

若整合至正式交易系統，建議：

| 層次 | 改良項目 | 說明 |
|------|----------|------|
| 資料層 | 多源聚合 | 追蹤 N 個反指標帳號，加權聚合信號 |
| 分析層 | 確定性管道 | temperature=0 + 結果快取 + Zod schema 驗證 |
| 風控層 | 倉位管理 | Kelly 公式 / 固定比例風險 |
| 風控層 | 回撤控制 | 最大回撤限制 + 動態停損 |
| 回測層 | 成本模型 | 台灣證交稅 0.3% + 手續費 0.1425% × 2 + 滑價 |
| 回測層 | 統計驗證 | Walk-forward + 蒙地卡羅 + 基準對比 |
| 資安層 | 金鑰管理 | 加密儲存 / vault 整合 |
| 資安層 | LLM 沙箱 | runtime schema 驗證 + 輸出清理 |

---

## 5. 總結

| 評估面向 | Contrarian Indicator | Banini Tracker |
|----------|---------------------|----------------|
| 創新性 | ★★★☆☆ | ★★★★☆ |
| 技術實現 | ★★☆☆☆ | ★★★★☆ |
| 回測可靠度 | ★☆☆☆☆ | ★★★☆☆ |
| 資安安全性 | ★★★★★ | ★★★☆☆ |
| 實戰可用性 | ★☆☆☆☆ | ★★☆☆☆ |
| 可擴展性 | ★☆☆☆☆ | ★★★★☆ |

**結論**: Banini Tracker 的架構設計值得借鑑，尤其是 LLM 語意分析管道和連鎖效應分析。但兩者作為獨立交易系統的實戰可靠度都不足，需要大幅改良回測方法論和風控機制後才能考慮整合到正式投資開發案中。

---

*此文件為研究筆記，僅供內部參考，不構成投資建議。*
