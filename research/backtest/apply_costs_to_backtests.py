"""
將交易成本套用至既有回測結果 → 產出 net-of-cost 報告

涵蓋:
  1. BTC FNG 反指標 (crypto_spot)
  2. SPY FNG 反指標 (us_stock)
  3. Peter Kurz 反指標 (tw_stock)
  4. Banini 停損信號 (tw_stock)

用法:
  python3 apply_costs_to_backtests.py                    # 用預設值
  python3 apply_costs_to_backtests.py --interactive      # 互動輸入自訂成本
  python3 apply_costs_to_backtests.py --market us_stock_ibkr_pro  # 指定替代 profile
"""

import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np
from tabulate import tabulate
from scipy import stats as sps_stats

from costs import CostProfile, apply_costs_to_trades, winrate_delta

DATA_DIR = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "output"
FINMIND_PRICE = DATA_DIR / "finmind_TaiwanStockPrice_TAIEX_2021-01-01_2026-04-13.csv"


def btc_spy_fng_net(market_label: str, price_csv: str, profile: CostProfile,
                    hold_days: int = 30) -> list:
    """對 BTC/SPY + Crypto FNG 重跑回測, 扣除成本"""
    fng = pd.read_csv(DATA_DIR / "crypto_fng.csv", parse_dates=["date"])
    price = pd.read_csv(DATA_DIR / price_csv, parse_dates=["date"])
    price["date"] = price["date"].dt.tz_localize(None) if hasattr(price["date"].dt, "tz_localize") else price["date"]

    df = price[["date", "close"]].merge(fng[["date", "fng"]], on="date").sort_values("date").reset_index(drop=True)
    df["entry"] = df["close"].shift(-1)
    df["exit"] = df["close"].shift(-1 - hold_days)
    df["ret"] = (df["exit"] - df["entry"]) / df["entry"] * 100

    rows = []
    # 做多極度恐懼 / 做空極度貪婪 兩種
    for label, sig_fn in [
        ("LONG FNG<15", lambda d: d[d["fng"] < 15]),
        ("LONG FNG<10", lambda d: d[d["fng"] < 10]),
        ("SHORT FNG>85", lambda d: d[d["fng"] > 85]),
        ("SHORT FNG>90", lambda d: d[d["fng"] > 90]),
    ]:
        sub = sig_fn(df).dropna(subset=["ret"])
        if len(sub) < 10:
            continue
        # 做空把報酬反向
        raw = sub["ret"].values
        if "SHORT" in label:
            raw = -raw
        stats = winrate_delta(raw.tolist(), profile, hold_days)
        rows.append([
            market_label, label, stats["n"],
            f"{stats['gross_winrate']:.1f}%",
            f"{stats['net_winrate']:.1f}%",
            f"{stats['winrate_drop_pp']:+.1f} pp",
            f"{stats['gross_avg']:+.2f}%",
            f"{stats['net_avg']:+.2f}%",
            f"{stats['cost_pct_round_trip']:.3f}%",
        ])
    return rows


def peter_kurz_net(profile: CostProfile, hold_days: int = 63) -> list:
    """Peter Kurz 反向操作, 扣成本"""
    detail = pd.read_csv(OUT / "peter_kurz_backtest_detail.csv")
    col = f"reverse_{'3M' if hold_days == 63 else '1M' if hold_days == 21 else '6M'}"
    if col not in detail.columns:
        col = "reverse_3M"
    valid = detail.dropna(subset=[col])
    if len(valid) < 5:
        return []
    stats = winrate_delta(valid[col].tolist(), profile, hold_days)
    return [[
        "Peter Kurz", col, stats["n"],
        f"{stats['gross_winrate']:.1f}%",
        f"{stats['net_winrate']:.1f}%",
        f"{stats['winrate_drop_pp']:+.1f} pp",
        f"{stats['gross_avg']:+.2f}%",
        f"{stats['net_avg']:+.2f}%",
        f"{stats['cost_pct_round_trip']:.3f}%",
    ]]


def banini_net(profile: CostProfile, hold_days: int = 5) -> list:
    """Banini 停損信號, 扣成本 — 使用實際 CSV 欄位"""
    detail = pd.read_csv(OUT / "banini_backtest_detail.csv")
    # 實際欄位: her_action, reverse_view, day_number, change_pct_close, result
    rows = []
    stop_loss_signals = ["停損賣出", "認賠", "畢業", "停損"]

    # 只取 day_number == hold_days 的資料 (因 CSV 是展開的多天)
    sub = detail[
        detail["her_action"].isin(stop_loss_signals) &
        (detail["day_number"] == hold_days)
    ].dropna(subset=["change_pct_close"])

    if len(sub) < 5:
        return []

    # reverse_view 策略: 她停損 → 反向做多, 報酬 = change_pct_close
    # (她「停損賣出」即 reverse_view 是買入, 所以跟著 change_pct_close 方向)
    returns = sub["change_pct_close"].tolist()
    stats = winrate_delta(returns, profile, hold_days)
    rows.append([
        "Banini 停損→做多", f"day={hold_days}", stats["n"],
        f"{stats['gross_winrate']:.1f}%",
        f"{stats['net_winrate']:.1f}%",
        f"{stats['winrate_drop_pp']:+.1f} pp",
        f"{stats['gross_avg']:+.2f}%",
        f"{stats['net_avg']:+.2f}%",
        f"{stats['cost_pct_round_trip']:.3f}%",
    ])

    # 同時測試她看多 → 反向做空 (負報酬)
    sub_buy = detail[
        detail["her_action"].isin(["買入", "計畫買入", "看多"]) &
        (detail["day_number"] == hold_days)
    ].dropna(subset=["change_pct_close"])
    if len(sub_buy) >= 5:
        # 反向做空 → 報酬 = -change_pct_close
        returns_short = (-sub_buy["change_pct_close"]).tolist()
        stats = winrate_delta(returns_short, profile, hold_days)
        rows.append([
            "Banini 看多→做空", f"day={hold_days}", stats["n"],
            f"{stats['gross_winrate']:.1f}%",
            f"{stats['net_winrate']:.1f}%",
            f"{stats['winrate_drop_pp']:+.1f} pp",
            f"{stats['gross_avg']:+.2f}%",
            f"{stats['net_avg']:+.2f}%",
            f"{stats['cost_pct_round_trip']:.3f}%",
        ])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interactive", action="store_true", help="互動輸入成本")
    ap.add_argument("--crypto-profile", default="crypto_spot")
    ap.add_argument("--us-profile", default="us_stock")
    ap.add_argument("--tw-profile", default="tw_stock")
    args = ap.parse_args()

    # 讀取 profiles
    if args.interactive:
        print("--- 設定加密幣成本 ---")
        p_crypto = CostProfile.from_user_input(args.crypto_profile)
        print("--- 設定美股成本 ---")
        p_us = CostProfile.from_user_input(args.us_profile)
        print("--- 設定台股成本 ---")
        p_tw = CostProfile.from_user_input(args.tw_profile)
    else:
        p_crypto = CostProfile.default(args.crypto_profile)
        p_us = CostProfile.default(args.us_profile)
        p_tw = CostProfile.default(args.tw_profile)

    print(f"\n使用成本 profile:")
    print(f"  加密: {args.crypto_profile} round-trip = {p_crypto.round_trip_bps()/100:.3f}%")
    print(f"  美股: {args.us_profile} round-trip = {p_us.round_trip_bps()/100:.3f}%")
    print(f"  台股: {args.tw_profile} round-trip = {p_tw.round_trip_bps()/100:.3f}%")

    # 跑每個市場
    all_rows = []
    print("\n[1] BTC + FNG (hold=30d) ...")
    all_rows.extend(btc_spy_fng_net("BTC-USD", "yahoo_BTC-USD.csv", p_crypto, hold_days=30))

    print("[2] SPY + FNG (hold=30d) ...")
    all_rows.extend(btc_spy_fng_net("SPY", "yahoo_SPY.csv", p_us, hold_days=30))

    print("[3] Peter Kurz (hold=63d=3M) ...")
    all_rows.extend(peter_kurz_net(p_tw, hold_days=63))

    print("[4] Banini 停損 (hold=5d) ...")
    all_rows.extend(banini_net(p_tw, hold_days=5))

    # 輸出
    print("\n" + "=" * 100)
    print("Net-of-Cost 回測結果")
    print("=" * 100)
    print(tabulate(
        all_rows,
        headers=["市場", "策略", "n", "Gross 勝", "Net 勝", "勝率降", "Gross 均", "Net 均", "成本"],
        tablefmt="github",
    ))

    # 存 CSV
    out_df = pd.DataFrame(all_rows, columns=[
        "市場", "策略", "n", "Gross 勝率", "Net 勝率", "勝率降 pp",
        "Gross 均報酬", "Net 均報酬", "Round-Trip 成本",
    ])
    out_df.to_csv(OUT / "net_of_cost_results.csv", index=False)
    print(f"\n已儲存: {OUT / 'net_of_cost_results.csv'}")


if __name__ == "__main__":
    main()
