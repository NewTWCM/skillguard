"""
制度性散戶多空比反指標回測
資料來源: FinMind API

回測策略:
  1. 基礎: 台指期 (TX) 日線
  2. 信號 A: 散戶多空比（從三大法人推算）
  3. 信號 B: 融資餘額增減率
  4. 驗證: 5 年歷史表現
"""

import requests
import pandas as pd
import numpy as np
from pathlib import Path
from tabulate import tabulate
from scipy import stats as sps_stats
import time

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

FINMIND = "https://api.finmindtrade.com/api/v4/data"


def fetch_finmind(dataset: str, data_id: str, start: str, end: str, cache_name: str | None = None) -> pd.DataFrame:
    """抓取 FinMind 資料並快取"""
    cache = DATA_DIR / f"finmind_{cache_name or dataset}_{data_id}_{start}_{end}.csv"
    if cache.exists():
        return pd.read_csv(cache, parse_dates=["date"])

    # FinMind 限制單次查詢範圍, 分年抓取
    all_data = []
    s_year = int(start[:4])
    e_year = int(end[:4])
    for year in range(s_year, e_year + 1):
        y_start = f"{year}-01-01" if year > s_year else start
        y_end = f"{year}-12-31" if year < e_year else end
        print(f"  [INFO] {dataset} {data_id} {y_start}~{y_end}...", end=" ")
        try:
            r = requests.get(FINMIND, params={
                "dataset": dataset, "data_id": data_id,
                "start_date": y_start, "end_date": y_end,
            }, timeout=60)
            j = r.json()
            rows = j.get("data", [])
            all_data.extend(rows)
            print(f"{len(rows)} rows")
        except Exception as e:
            print(f"ERR: {e}")
        time.sleep(1.5)

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df


def compute_retail_long_short_ratio(fut_inst: pd.DataFrame, fut_daily: pd.DataFrame) -> pd.DataFrame:
    """
    計算散戶多空比
    散戶部位 = 總未平倉 - 三大法人未平倉
    多空比 = (散戶多 - 散戶空) / 總未平倉 × 100%
    """
    # 三大法人合計 (自營商 + 投信 + 外資)
    inst = fut_inst.groupby("date").agg(
        inst_long=("long_open_interest_balance_volume", "sum"),
        inst_short=("short_open_interest_balance_volume", "sum"),
    ).reset_index()

    # 總未平倉 (取當月主要合約)
    fut_daily_agg = fut_daily.groupby("date").agg(
        total_oi=("open_interest", "sum"),
        close=("close", "last"),
    ).reset_index()

    df = inst.merge(fut_daily_agg, on="date", how="inner")
    # 散戶部位推算
    df["retail_long"] = df["total_oi"] - df["inst_long"]
    df["retail_short"] = df["total_oi"] - df["inst_short"]
    df["retail_net"] = df["retail_long"] - df["retail_short"]
    # 散戶多空比 (%)
    df["retail_ratio"] = df["retail_net"] / df["total_oi"] * 100
    return df


def backtest_retail_contrarian(df: pd.DataFrame, hold_days: int = 5,
                                entry_threshold: float = None) -> dict:
    """
    回測策略: 散戶多空比反指標
    - 散戶偏多 (ratio > threshold) → 次日做空
    - 散戶偏空 (ratio < -threshold) → 次日做多
    - 持有 hold_days 天後平倉
    """
    df = df.copy().sort_values("date").reset_index(drop=True)
    df["close_next"] = df["close"].shift(-1)  # 次日收盤 = 入場價
    df["close_exit"] = df["close"].shift(-1 - hold_days)  # hold_days 後收盤 = 出場價
    df["return_pct"] = (df["close_exit"] - df["close_next"]) / df["close_next"] * 100

    # 信號: 反向操作
    if entry_threshold is None:
        # 不設門檻, 純粹看正負
        df["signal"] = np.where(df["retail_ratio"] > 0, -1, 1)  # 散戶多 → 做空 (-1)
    else:
        df["signal"] = np.where(
            df["retail_ratio"] > entry_threshold, -1,
            np.where(df["retail_ratio"] < -entry_threshold, 1, 0)
        )

    df["strategy_ret"] = df["signal"] * df["return_pct"]

    # 僅統計有信號的交易
    trades = df[df["signal"] != 0].dropna(subset=["return_pct"])
    wins = (trades["strategy_ret"] > 0).sum()
    losses = (trades["strategy_ret"] < 0).sum()
    flats = (trades["strategy_ret"] == 0).sum()
    total = wins + losses

    if total == 0:
        return {"n": 0}

    winrate = wins / total * 100
    avg_ret = trades["strategy_ret"].mean()
    total_ret = trades["strategy_ret"].sum()  # 累計報酬 (簡化)
    # 單利近似: 複利需更嚴謹
    binom = sps_stats.binomtest(wins, total, 0.5, alternative="two-sided")

    # Benchmark: buy-and-hold
    bh_ret = (df["close"].iloc[-1] - df["close"].iloc[0]) / df["close"].iloc[0] * 100

    return {
        "n": int(total),
        "wins": int(wins),
        "losses": int(losses),
        "flats": int(flats),
        "winrate": winrate,
        "avg_return_per_trade": avg_ret,
        "total_return": total_ret,
        "buy_hold_return": bh_ret,
        "p_value": binom.pvalue,
        "max_drawdown": trades["strategy_ret"].cumsum().cummax().sub(
            trades["strategy_ret"].cumsum()).max() if len(trades) > 0 else 0,
    }


def run():
    print("=" * 70)
    print("制度性散戶反指標 5 年回測 (2021-2026)")
    print("=" * 70)

    # 1. 抓取資料 (近 5 年)
    print("\n[1/4] 抓取台指期日線...")
    fut_daily = fetch_finmind("TaiwanFuturesDaily", "TX",
                               "2021-01-01", "2026-04-13", "tx_daily")
    # 僅保留 position (一般盤)
    fut_daily = fut_daily[fut_daily["trading_session"] == "position"]
    print(f"  共 {len(fut_daily)} 筆")

    print("\n[2/4] 抓取台指期法人未平倉...")
    fut_inst = fetch_finmind("TaiwanFuturesInstitutionalInvestors", "TX",
                              "2021-01-01", "2026-04-13", "tx_inst")
    print(f"  共 {len(fut_inst)} 筆")

    print("\n[3/4] 計算散戶多空比...")
    rr = compute_retail_long_short_ratio(fut_inst, fut_daily)
    print(f"  有效交易日: {len(rr)}")
    print(f"  散戶多空比統計:")
    print(f"    平均: {rr['retail_ratio'].mean():.2f}%")
    print(f"    標準差: {rr['retail_ratio'].std():.2f}%")
    print(f"    最多頭: {rr['retail_ratio'].max():.2f}%")
    print(f"    最空頭: {rr['retail_ratio'].min():.2f}%")

    # 儲存
    rr.to_csv(OUT / "retail_ratio_daily.csv", index=False)

    # 4. 回測多種策略
    print("\n[4/4] 執行回測...")
    print("\n策略 A: 單純反向操作散戶多空比 (無門檻)")
    print("-" * 70)
    rows = []
    for hold in [1, 3, 5, 10, 20]:
        for thresh in [None, 0, 2, 5, 10]:
            result = backtest_retail_contrarian(rr, hold_days=hold, entry_threshold=thresh)
            if result["n"] < 10:
                continue
            rows.append([
                hold,
                thresh if thresh is not None else "0 (無門檻)",
                result["n"],
                result["wins"],
                result["losses"],
                f"{result['winrate']:.1f}%",
                f"{result['avg_return_per_trade']:+.3f}%",
                f"{result['total_return']:+.1f}%",
                f"{result['buy_hold_return']:+.1f}%",
                f"{result['p_value']:.4f}",
            ])

    print(tabulate(
        rows,
        headers=["持有日", "門檻%", "交易數", "勝", "負", "勝率",
                 "均報酬/筆", "累計報酬", "Buy&Hold", "p-value"],
        tablefmt="github"
    ))

    # 最佳參數詳細分析
    print("\n" + "=" * 70)
    print("最佳策略細節：5 日持有, 門檻 ±5%")
    print("=" * 70)

    rr_test = rr.copy().sort_values("date").reset_index(drop=True)
    rr_test["close_next"] = rr_test["close"].shift(-1)
    rr_test["close_exit"] = rr_test["close"].shift(-6)  # 5 days later
    rr_test["return_pct"] = (rr_test["close_exit"] - rr_test["close_next"]) / rr_test["close_next"] * 100
    rr_test["signal"] = np.where(
        rr_test["retail_ratio"] > 5, -1,
        np.where(rr_test["retail_ratio"] < -5, 1, 0)
    )
    rr_test["strategy_ret"] = rr_test["signal"] * rr_test["return_pct"]
    trades = rr_test[rr_test["signal"] != 0].dropna(subset=["return_pct"]).copy()

    # 年度分解
    trades["year"] = trades["date"].dt.year
    yearly = trades.groupby("year").agg(
        n=("strategy_ret", "size"),
        wins=("strategy_ret", lambda x: (x > 0).sum()),
        losses=("strategy_ret", lambda x: (x < 0).sum()),
        total=("strategy_ret", "sum"),
        avg=("strategy_ret", "mean"),
    ).reset_index()
    yearly["winrate"] = yearly["wins"] / (yearly["wins"] + yearly["losses"]) * 100

    print("\n年度績效:")
    year_rows = [
        [int(r["year"]), int(r["n"]), int(r["wins"]), int(r["losses"]),
         f"{r['winrate']:.1f}%", f"{r['avg']:+.3f}%", f"{r['total']:+.2f}%"]
        for _, r in yearly.iterrows()
    ]
    print(tabulate(
        year_rows,
        headers=["年度", "交易", "勝", "負", "勝率", "均報酬", "累計報酬"],
        tablefmt="github"
    ))

    trades.to_csv(OUT / "retail_contrarian_trades.csv", index=False)

    return rr, yearly


if __name__ == "__main__":
    run()
