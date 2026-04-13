"""
制度性散戶多空比反指標回測 v2 (修正版)
修正: 使用加權指數 TAIEX 作為標的 (連續指數, 無合約滾動問題)
信號: 從台指期三大法人未平倉推算散戶多空比
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

FINMIND = "https://api.finmindtrade.com/api/v4/data"


def fetch_finmind(dataset: str, data_id: str, start: str, end: str) -> pd.DataFrame:
    cache = DATA_DIR / f"finmind_{dataset}_{data_id}_{start}_{end}.csv"
    if cache.exists():
        return pd.read_csv(cache, parse_dates=["date"])

    all_data = []
    s_year = int(start[:4])
    e_year = int(end[:4])
    for year in range(s_year, e_year + 1):
        y_start = f"{year}-01-01" if year > s_year else start
        y_end = f"{year}-12-31" if year < e_year else end
        try:
            r = requests.get(FINMIND, params={
                "dataset": dataset, "data_id": data_id,
                "start_date": y_start, "end_date": y_end,
            }, timeout=60)
            j = r.json()
            rows = j.get("data", [])
            all_data.extend(rows)
        except Exception:
            pass
        time.sleep(1.5)

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df


def main():
    print("=" * 70)
    print("制度性散戶反指標 5 年回測 v2 (2021-01 ~ 2026-04)")
    print("=" * 70)

    # 1. 加權指數 (連續) 作為標的
    print("\n[1/3] 加權指數歷史...")
    taiex = fetch_finmind("TaiwanStockPrice", "TAIEX", "2021-01-01", "2026-04-13")
    if taiex.empty:
        # 嘗試抓 0050 ETF 作為替代
        print("  TAIEX 不可用, 改用 0050 ETF")
        taiex = fetch_finmind("TaiwanStockPrice", "0050", "2021-01-01", "2026-04-13")
    # 去重
    taiex = taiex.drop_duplicates(subset="date").sort_values("date").reset_index(drop=True)
    print(f"  共 {len(taiex)} 筆日線, 期間 {taiex['date'].min().date()} ~ {taiex['date'].max().date()}")

    # 2. 台指期法人未平倉 + 加總
    print("\n[2/3] 台指期法人未平倉 (三大法人合計)...")
    fut_inst = fetch_finmind("TaiwanFuturesInstitutionalInvestors", "TX",
                              "2021-01-01", "2026-04-13")

    # 加總三大法人 (自營商, 投信, 外資)
    inst = fut_inst.groupby("date").agg(
        inst_long=("long_open_interest_balance_volume", "sum"),
        inst_short=("short_open_interest_balance_volume", "sum"),
    ).reset_index()
    print(f"  共 {len(inst)} 筆日數據")

    # 3. 抓取總未平倉 (從期貨日資料, 僅取近月合約)
    print("\n[3/3] 台指期總未平倉 (近月合約)...")
    fut_d = fetch_finmind("TaiwanFuturesDaily", "TX", "2021-01-01", "2026-04-13")
    fut_d = fut_d[fut_d["trading_session"] == "position"]
    # 僅取當月 (近月) 合約: contract_date = YYYYMM 最近
    fut_d["date"] = pd.to_datetime(fut_d["date"])
    fut_d["contract_date_int"] = pd.to_numeric(fut_d["contract_date"], errors="coerce")
    fut_d = fut_d.dropna(subset=["contract_date_int"])

    # 對每個日期, 取 contract_date 最小 (最近月) 的合約
    fut_near = fut_d.sort_values(["date", "contract_date_int"]).groupby("date").first().reset_index()

    # 總未平倉 = 全部合約加總
    total_oi = fut_d.groupby("date")["open_interest"].sum().reset_index()
    total_oi.columns = ["date", "total_oi"]

    # 合併
    merged = total_oi.merge(inst, on="date", how="inner")
    merged["retail_long"] = merged["total_oi"] - merged["inst_long"]
    merged["retail_short"] = merged["total_oi"] - merged["inst_short"]
    merged["retail_net"] = merged["retail_long"] - merged["retail_short"]
    merged["retail_ratio"] = merged["retail_net"] / merged["total_oi"] * 100

    # 合併到 TAIEX 日線
    df = taiex[["date", "close"]].merge(merged[["date", "retail_ratio"]], on="date", how="inner")
    df = df.sort_values("date").reset_index(drop=True)
    print(f"\n  最終有效樣本: {len(df)} 交易日")
    print(f"  散戶多空比統計:")
    print(f"    平均: {df['retail_ratio'].mean():.2f}%")
    print(f"    標準差: {df['retail_ratio'].std():.2f}%")
    print(f"    25/50/75 分位: {df['retail_ratio'].quantile([0.25, 0.5, 0.75]).values}")

    df.to_csv(OUT / "retail_ratio_daily_v2.csv", index=False)

    # ========== 回測 ==========
    print("\n" + "=" * 70)
    print("回測策略: 散戶偏多則做空 TAIEX, 散戶偏空則做多")
    print("=" * 70)

    results = []
    for hold in [1, 3, 5, 10, 20]:
        for thresh in [0, 2, 5, 10, 15]:
            d = df.copy()
            d["entry_price"] = d["close"].shift(-1)
            d["exit_price"] = d["close"].shift(-1 - hold)
            d["return_pct"] = (d["exit_price"] - d["entry_price"]) / d["entry_price"] * 100

            d["signal"] = np.where(
                d["retail_ratio"] > thresh, -1,
                np.where(d["retail_ratio"] < -thresh, 1, 0)
            )
            d["strategy_ret"] = d["signal"] * d["return_pct"]

            trades = d[d["signal"] != 0].dropna(subset=["return_pct"])
            wins = (trades["strategy_ret"] > 0).sum()
            losses = (trades["strategy_ret"] < 0).sum()
            total = wins + losses
            if total < 20:
                continue

            winrate = wins / total * 100
            avg_ret = trades["strategy_ret"].mean()
            # 累計報酬: 假設每筆固定投入資金
            total_ret = trades["strategy_ret"].sum() / hold  # 正規化為日平均

            # Benchmark
            bh = (df["close"].iloc[-1] - df["close"].iloc[0]) / df["close"].iloc[0] * 100

            p = sps_stats.binomtest(int(wins), total, 0.5, alternative="two-sided").pvalue

            # Sharpe-like: avg / std
            sharpe = avg_ret / trades["strategy_ret"].std() if trades["strategy_ret"].std() > 0 else 0

            results.append({
                "hold": hold,
                "thresh": thresh,
                "n": total,
                "wins": wins,
                "losses": losses,
                "winrate": winrate,
                "avg_ret": avg_ret,
                "total_ret_norm": total_ret,
                "bh_ret": bh,
                "p": p,
                "sharpe": sharpe,
            })

    res_df = pd.DataFrame(results)
    res_df = res_df.sort_values(["hold", "thresh"])

    rows = [
        [r["hold"], r["thresh"] if r["thresh"] > 0 else "無", r["n"],
         r["wins"], r["losses"],
         f"{r['winrate']:.1f}%",
         f"{r['avg_ret']:+.3f}%",
         f"{r['total_ret_norm']:+.1f}%",
         f"{r['bh_ret']:+.1f}%",
         f"{r['sharpe']:.3f}",
         f"{r['p']:.4f}",
         "***" if r["p"] < 0.01 else "**" if r["p"] < 0.05 else "*" if r["p"] < 0.1 else "ns",
         ]
        for _, r in res_df.iterrows()
    ]

    print("\n" + tabulate(
        rows,
        headers=["持有", "門檻", "交易", "勝", "負", "勝率",
                 "均報酬", "累計(日化)", "Buy&Hold", "Sharpe", "p", "顯著性"],
        tablefmt="github",
    ))

    # 找出最佳策略
    best = res_df.loc[res_df["winrate"].idxmax()]
    print(f"\n[最高勝率] 持有 {best['hold']} 日, 門檻 {best['thresh']}%: "
          f"{best['winrate']:.1f}% (p={best['p']:.4f})")
    best_sig = res_df[res_df["p"] < 0.05].sort_values("sharpe", ascending=False).head(3)
    print(f"\n[顯著性 p<0.05 且 Sharpe 最高 Top 3]:")
    for _, r in best_sig.iterrows():
        print(f"  持有 {r['hold']} 日, 門檻 {r['thresh']}%: "
              f"勝率 {r['winrate']:.1f}%, 均報酬 {r['avg_ret']:+.3f}%, "
              f"Sharpe {r['sharpe']:.3f}, p={r['p']:.4f}")

    # ========== 年度分解 (用最佳策略) ==========
    if len(best_sig) > 0:
        b = best_sig.iloc[0]
        print(f"\n{'=' * 70}")
        print(f"年度分解: 持有 {int(b['hold'])} 日, 門檻 {int(b['thresh'])}%")
        print(f"{'=' * 70}")

        d = df.copy()
        d["entry_price"] = d["close"].shift(-1)
        d["exit_price"] = d["close"].shift(-1 - int(b['hold']))
        d["return_pct"] = (d["exit_price"] - d["entry_price"]) / d["entry_price"] * 100
        d["signal"] = np.where(
            d["retail_ratio"] > b['thresh'], -1,
            np.where(d["retail_ratio"] < -b['thresh'], 1, 0)
        )
        d["strategy_ret"] = d["signal"] * d["return_pct"]
        trades = d[d["signal"] != 0].dropna(subset=["return_pct"]).copy()
        trades["year"] = trades["date"].dt.year

        yearly = trades.groupby("year").agg(
            n=("strategy_ret", "size"),
            wins=("strategy_ret", lambda x: (x > 0).sum()),
            losses=("strategy_ret", lambda x: (x < 0).sum()),
            total=("strategy_ret", "sum"),
            avg=("strategy_ret", "mean"),
        ).reset_index()
        yearly["winrate"] = yearly["wins"] / (yearly["wins"] + yearly["losses"]) * 100

        # TAIEX 年度報酬作對照
        taiex_year = df.set_index("date")["close"].resample("YE").agg(["first", "last"])
        taiex_year["bh_ret"] = (taiex_year["last"] - taiex_year["first"]) / taiex_year["first"] * 100
        taiex_year.index = taiex_year.index.year

        year_rows = []
        for _, r in yearly.iterrows():
            bh_ret = taiex_year.loc[r["year"], "bh_ret"] if r["year"] in taiex_year.index else None
            year_rows.append([
                int(r["year"]), int(r["n"]),
                f"{r['winrate']:.1f}%",
                f"{r['avg']:+.3f}%",
                f"{r['total']:+.2f}%",
                f"{bh_ret:+.2f}%" if bh_ret is not None else "-",
            ])
        print(tabulate(
            year_rows,
            headers=["年度", "交易", "勝率", "均報酬/筆", "累計報酬", "TAIEX Buy&Hold"],
            tablefmt="github"
        ))
        trades.to_csv(OUT / "retail_contrarian_best_trades.csv", index=False)


if __name__ == "__main__":
    main()
