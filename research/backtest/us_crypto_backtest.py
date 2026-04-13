"""
美股 / 加密幣反指標基準測試
使用 Fear & Greed Index (美股), Crypto Fear & Greed Index (加密幣)
這些是市場最公認的情緒指標，用於對照台灣市場測試

資料來源:
  - alternative.me/fng/ (加密幣恐懼貪婪指數, 免費 API)
  - Yahoo Finance (SPY, BTC-USD)
"""

import requests
import pandas as pd
import numpy as np
from pathlib import Path
from tabulate import tabulate
from scipy import stats as sps_stats
import time

DATA_DIR = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)


def fetch_crypto_fng() -> pd.DataFrame:
    """抓取加密幣恐懼貪婪指數 (alternative.me)"""
    cache = DATA_DIR / "crypto_fng.csv"
    if cache.exists():
        return pd.read_csv(cache, parse_dates=["date"])

    url = "https://api.alternative.me/fng/?limit=0"
    r = requests.get(url, timeout=30)
    j = r.json()
    rows = []
    for d in j.get("data", []):
        rows.append({
            "date": pd.to_datetime(int(d["timestamp"]), unit="s"),
            "fng": int(d["value"]),
            "classification": d["value_classification"],
        })
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df


def fetch_yahoo(symbol: str, period_years: int = 6) -> pd.DataFrame:
    """從 Yahoo Finance 取日線"""
    cache = DATA_DIR / f"yahoo_{symbol}.csv"
    if cache.exists():
        df = pd.read_csv(cache, parse_dates=["date"])
        if len(df) > 0 and df["date"].max() >= pd.Timestamp.now() - pd.Timedelta(days=7):
            return df

    now = int(pd.Timestamp.now().timestamp())
    start = int((pd.Timestamp.now() - pd.Timedelta(days=365 * period_years)).timestamp())
    url = f"https://query1.finance.yahoo.com/v7/finance/download/{symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, params={
            "period1": start, "period2": now, "interval": "1d",
            "events": "history", "includeAdjustedClose": "true",
        }, headers=headers, timeout=60)
        if r.status_code == 200 and not r.text.startswith("{"):
            from io import StringIO
            df = pd.read_csv(StringIO(r.text))
            df.columns = [c.lower() for c in df.columns]
            df["date"] = pd.to_datetime(df["date"])
            df.to_csv(cache, index=False)
            return df
    except Exception as e:
        print(f"  Yahoo {symbol} error: {e}")

    # Fallback: use chart API
    url2 = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    try:
        r = requests.get(url2, params={
            "period1": start, "period2": now, "interval": "1d",
        }, headers=headers, timeout=60)
        if r.status_code == 200:
            j = r.json()
            result = j["chart"]["result"][0]
            ts = result["timestamp"]
            q = result["indicators"]["quote"][0]
            df = pd.DataFrame({
                "date": pd.to_datetime(ts, unit="s").normalize(),
                "open": q["open"],
                "high": q["high"],
                "low": q["low"],
                "close": q["close"],
                "volume": q["volume"],
            })
            df = df.dropna(subset=["close"])
            df.to_csv(cache, index=False)
            return df
    except Exception as e:
        print(f"  Yahoo Chart {symbol} error: {e}")

    return pd.DataFrame()


def backtest_fng(price_df: pd.DataFrame, fng_df: pd.DataFrame, symbol: str):
    """恐懼貪婪指數反指標回測"""
    df = price_df[["date", "close"]].merge(
        fng_df[["date", "fng"]], on="date", how="inner"
    ).sort_values("date").reset_index(drop=True)

    print(f"\n{'=' * 70}")
    print(f"{symbol} 反指標回測 (恐懼貪婪指數)")
    print(f"{'=' * 70}")
    print(f"樣本: {len(df)} 天, 期間: {df['date'].min().date()} ~ {df['date'].max().date()}")
    print(f"FNG 統計: 平均 {df['fng'].mean():.1f}, 中位數 {df['fng'].median():.1f}")

    rows = []
    # 反指標邏輯: FNG 極度貪婪 → 做空; 極度恐懼 → 做多
    for hold in [1, 3, 5, 10, 20, 30]:
        for low_thr, high_thr in [(25, 75), (20, 80), (15, 85), (10, 90)]:
            d = df.copy()
            d["entry"] = d["close"].shift(-1)
            d["exit"] = d["close"].shift(-1 - hold)
            d["ret"] = (d["exit"] - d["entry"]) / d["entry"] * 100

            d["signal"] = np.where(
                d["fng"] > high_thr, -1,  # 極度貪婪 → 做空
                np.where(d["fng"] < low_thr, 1, 0)  # 極度恐懼 → 做多
            )
            d["strat_ret"] = d["signal"] * d["ret"]

            trades = d[d["signal"] != 0].dropna(subset=["ret"])
            wins = (trades["strat_ret"] > 0).sum()
            losses = (trades["strat_ret"] < 0).sum()
            total = wins + losses
            if total < 10:
                continue

            winrate = wins / total * 100
            avg = trades["strat_ret"].mean()
            p = sps_stats.binomtest(int(wins), total, 0.5, alternative="two-sided").pvalue
            bh = (df["close"].iloc[-1] - df["close"].iloc[0]) / df["close"].iloc[0] * 100

            # 分別看做多和做空的勝率
            longs = trades[trades["signal"] == 1]
            shorts = trades[trades["signal"] == -1]
            long_wr = (longs["strat_ret"] > 0).sum() / max(len(longs), 1) * 100
            short_wr = (shorts["strat_ret"] > 0).sum() / max(len(shorts), 1) * 100

            rows.append([
                hold,
                f"{low_thr}/{high_thr}",
                total,
                f"{winrate:.1f}%",
                f"{avg:+.2f}%",
                f"{long_wr:.1f}% ({len(longs)})",
                f"{short_wr:.1f}% ({len(shorts)})",
                f"{p:.4f}",
                "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else "ns",
            ])

    print("\n" + tabulate(
        rows,
        headers=["持有", "恐懼/貪婪", "交易", "總勝率", "均報酬",
                 "做多勝率(n)", "做空勝率(n)", "p", "顯著性"],
        tablefmt="github"
    ))
    return df


def main():
    print("=" * 70)
    print("美股 / 加密幣 恐懼貪婪反指標 基準測試")
    print("=" * 70)

    # 1. 加密幣 FNG
    print("\n[1] 抓取加密幣恐懼貪婪指數...")
    fng = fetch_crypto_fng()
    print(f"  {len(fng)} 筆, {fng['date'].min().date()} ~ {fng['date'].max().date()}")

    # 2. BTC 日線
    print("\n[2] 抓取 BTC-USD 日線...")
    btc = fetch_yahoo("BTC-USD", period_years=7)
    print(f"  BTC: {len(btc)} 筆")

    # 3. SPY 日線 (作對照)
    print("\n[3] 抓取 SPY (S&P 500 ETF)...")
    spy = fetch_yahoo("SPY", period_years=6)
    print(f"  SPY: {len(spy)} 筆")

    # 回測 1: BTC + Crypto FNG
    if len(btc) > 0:
        backtest_fng(btc, fng, "BTC-USD")

    # 回測 2: SPY + Crypto FNG (Crypto FNG 也常被用於 risk-on 指標)
    if len(spy) > 0:
        backtest_fng(spy, fng, "SPY (用加密幣 FNG 作情緒 proxy)")


if __name__ == "__main__":
    main()
