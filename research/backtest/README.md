# 反指標量化回測整合包

本目錄包含針對多個台灣、美股、加密幣反指標策略的量化回測程式與結果。

## 快速開始

```bash
# 安裝依賴
pip3 install pandas numpy scipy matplotlib tabulate requests

# 執行所有回測
python3 banini_backtest.py           # Banini 個人反指標 (用公開 DB)
python3 institutional_backtest_v2.py # 台指散戶多空比 5 年
python3 us_crypto_backtest.py        # BTC/SPY 恐懼貪婪指數
```

## 檔案結構

```
backtest/
├── README.md                        # 本檔
├── RESULTS.md                       # 完整回測結果報告
├── banini_backtest.py               # Banini 345 筆預測分析
├── institutional_backtest.py        # 散戶多空比回測 v1 (期貨版, 有合約滾動問題)
├── institutional_backtest_v2.py     # 散戶多空比回測 v2 (加權指數版, 推薦)
├── us_crypto_backtest.py            # BTC + SPY FNG 回測
├── tw_data_fetcher.py               # TWSE / TAIFEX 資料抓取模組
├── data/                            # 資料快取
│   ├── banini-public.db             # Banini 公開 SQLite 資料庫 (345 預測)
│   └── finmind_*.csv                # FinMind API 快取
└── output/                          # 回測輸出
    ├── banini_backtest_detail.csv   # Banini 每筆預測明細
    ├── retail_ratio_daily_v2.csv    # 每日散戶多空比
    └── retail_contrarian_best_trades.csv # 最佳策略交易明細
```

## 主要結論

查看 [RESULTS.md](RESULTS.md) 獲得完整報告，要點：

1. **「反指標」是非對稱現象**：極度恐懼做多有效，極度貪婪做空反而大虧
2. **Banini 整體反指標無效**（勝率 44-50%），僅「停損賣出」信號有 80% 反向勝率
3. **散戶多空比不是穩定反指標**（5 年回測 p>0.1 無顯著性）
4. **BTC/SPY FNG 極端值**：極度恐懼做多勝率 56-76%；極度貪婪做空勝率 5-18%（穩輸）

## 資料來源

- **FinMind API** (https://finmindtrade.com) — 台股/期貨/融資融券免費 API
- **Alternative.me** (https://alternative.me/crypto/fear-and-greed-index/) — 加密幣 FNG
- **Yahoo Finance** — 美股、加密幣日線
- **cablate/banini-tracker** (https://github.com/cablate/banini-tracker) — Banini 預測公開 DB
