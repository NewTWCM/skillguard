"""
谷月涵 (Peter Kurz) 反指標歷史呼叫量化回測
資料: 20 筆 2021-2026 公開市場呼叫 (data/peter_kurz_calls.json)
標的: TAIEX 加權指數
策略: 反向操作 (Kurz 看多 → 做空; Kurz 看空 → 做多)
多時間尺度: 1M / 3M / 6M / 12M forward return
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from tabulate import tabulate
from scipy import stats as sps_stats
import requests
import time

DATA_DIR = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)
FINMIND = "https://api.finmindtrade.com/api/v4/data"


def fetch_finmind_cached(dataset: str, data_id: str, start: str, end: str) -> pd.DataFrame:
    cache = DATA_DIR / f"finmind_{dataset}_{data_id}_{start}_{end}.csv"
    if cache.exists():
        return pd.read_csv(cache, parse_dates=["date"])
    all_data = []
    for year in range(int(start[:4]), int(end[:4]) + 1):
        y_start = f"{year}-01-01" if year > int(start[:4]) else start
        y_end = f"{year}-12-31" if year < int(end[:4]) else end
        try:
            r = requests.get(FINMIND, params={
                "dataset": dataset, "data_id": data_id,
                "start_date": y_start, "end_date": y_end,
            }, timeout=60)
            all_data.extend(r.json().get("data", []))
        except Exception:
            pass
        time.sleep(1.5)
    if not all_data:
        return pd.DataFrame()
    df = pd.DataFrame(all_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df


def score_call(call: dict, taiex: pd.DataFrame, days: int) -> dict:
    """
    對單筆呼叫計算前向報酬。
    direction = "bullish" → Kurz 看多，反向操作 = 做空
    direction = "bearish" → Kurz 看空，反向操作 = 做多
    reverse_ret = TAIEX 漲 x%:
        bullish 呼叫 → 反向 = 做空 → 反向報酬 = -x%
        bearish 呼叫 → 反向 = 做多 → 反向報酬 = +x%
    """
    call_date = pd.to_datetime(call["date"])
    direction = call["direction"]

    # 找到呼叫日之後第一個交易日
    future = taiex[taiex["date"] >= call_date].copy()
    if len(future) < 2:
        return {"reverse_ret": None, "taiex_ret": None}

    entry = future.iloc[0]["close"]

    # 前 N 個交易日 (約 21 交易日 = 1 個月)
    if len(future) <= days:
        return {"reverse_ret": None, "taiex_ret": None}

    exit_price = future.iloc[days]["close"]
    taiex_ret = (exit_price - entry) / entry * 100

    # 將方向轉成反向操作報酬
    if direction == "bullish":
        reverse_ret = -taiex_ret  # 反向做空
    elif direction == "bearish":
        reverse_ret = taiex_ret  # 反向做多
    else:  # mixed / conditional
        reverse_ret = None

    return {"reverse_ret": reverse_ret, "taiex_ret": taiex_ret}


def main():
    print("=" * 70)
    print("谷月涵 (Peter Kurz) 反指標量化回測 — 20 筆歷史呼叫")
    print("=" * 70)

    # 讀取呼叫資料
    with open(DATA_DIR / "peter_kurz_calls.json") as f:
        calls = json.load(f)
    print(f"\n呼叫數: {len(calls)}")
    bullish = sum(1 for c in calls if c["direction"] == "bullish")
    bearish = sum(1 for c in calls if c["direction"] == "bearish")
    print(f"  看多: {bullish} 筆")
    print(f"  看空: {bearish} 筆")
    print(f"  其他: {len(calls) - bullish - bearish} 筆")

    # 抓取 TAIEX
    print("\n[1] 抓取 TAIEX 2021-01 ~ 2026-04...")
    taiex = fetch_finmind_cached("TaiwanStockPrice", "TAIEX", "2021-01-01", "2026-04-13")
    if taiex.empty:
        print("  TAIEX 不可用, 改用 0050")
        taiex = fetch_finmind_cached("TaiwanStockPrice", "0050", "2021-01-01", "2026-04-13")
    print(f"  {len(taiex)} 筆交易日")

    # 對每筆呼叫算多時間尺度報酬
    print("\n[2] 計算多時間尺度反向報酬...")
    horizons = {"1M": 21, "3M": 63, "6M": 126, "12M": 252}

    rows = []
    for call in calls:
        row = {
            "id": call["id"],
            "date": call["date"],
            "direction": call["direction"],
            "prediction": call["prediction"][:40] + "...",
        }
        for label, days in horizons.items():
            r = score_call(call, taiex, days)
            row[f"taiex_{label}"] = r["taiex_ret"]
            row[f"reverse_{label}"] = r["reverse_ret"]
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "peter_kurz_backtest_detail.csv", index=False)

    # ========== 勝率統計 ==========
    print("\n" + "=" * 70)
    print("反向操作勝率統計 (以 Kurz 呼叫方向對作 TAIEX)")
    print("=" * 70)

    stat_rows = []
    for label, _ in horizons.items():
        col = f"reverse_{label}"
        valid = df.dropna(subset=[col])
        n = len(valid)
        if n == 0:
            continue
        wins = (valid[col] > 0).sum()
        losses = (valid[col] < 0).sum()
        winrate = wins / n * 100 if n else 0
        avg = valid[col].mean()
        median = valid[col].median()
        total = n
        p = sps_stats.binomtest(int(wins), total, 0.5,
                                 alternative="two-sided").pvalue if total > 0 else 1.0
        stat_rows.append([
            label, n, int(wins), int(losses),
            f"{winrate:.1f}%",
            f"{avg:+.2f}%",
            f"{median:+.2f}%",
            f"{p:.4f}",
            "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else "ns",
        ])

    print(tabulate(stat_rows,
                   headers=["時間尺度", "n", "勝", "負", "勝率", "均報酬", "中位數", "p", "顯著"],
                   tablefmt="github"))

    # ========== 方向分解 ==========
    print("\n" + "=" * 70)
    print("按呼叫方向分解 (3M)")
    print("=" * 70)

    dir_rows = []
    for direction in ["bullish", "bearish"]:
        sub = df[df["direction"] == direction].dropna(subset=["reverse_3M"])
        n = len(sub)
        if n == 0:
            continue
        wins = (sub["reverse_3M"] > 0).sum()
        winrate = wins / n * 100
        avg = sub["reverse_3M"].mean()
        dir_rows.append([
            direction, n, int(wins), f"{winrate:.1f}%", f"{avg:+.2f}%",
        ])
    print(tabulate(dir_rows, headers=["Kurz 方向", "n", "反向勝", "反向勝率", "反向均報酬"],
                   tablefmt="github"))

    # ========== 經典倖存者偏差案例 ==========
    print("\n" + "=" * 70)
    print("最受社群矚目的 5 筆 (按反向 3M 報酬排序)")
    print("=" * 70)

    top5 = df.dropna(subset=["reverse_3M"]).sort_values("reverse_3M", ascending=False).head(5)
    print(tabulate(
        [[r["date"], r["direction"], r["prediction"][:30], f"{r['reverse_3M']:+.2f}%"]
         for _, r in top5.iterrows()],
        headers=["日期", "方向", "呼叫", "反向 3M"], tablefmt="github"))

    print("\n同時, 反向失敗最慘的 3 筆 (Kurz 是正確的):")
    bot3 = df.dropna(subset=["reverse_3M"]).sort_values("reverse_3M").head(3)
    print(tabulate(
        [[r["date"], r["direction"], r["prediction"][:30], f"{r['reverse_3M']:+.2f}%"]
         for _, r in bot3.iterrows()],
        headers=["日期", "方向", "呼叫", "反向 3M"], tablefmt="github"))


if __name__ == "__main__":
    main()
