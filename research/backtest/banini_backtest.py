"""
Banini 反指標回測分析
資料來源: cablate/banini-tracker 公開資料庫 (banini-public.db)

分析：她的 345 筆預測，在 1/3/5/10 日後的實際價格走勢
檢驗假設：反向操作她的觀點是否真的能獲利
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from tabulate import tabulate

DB = Path(__file__).parent / "data" / "banini-public.db"
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)


def load_data():
    conn = sqlite3.connect(DB)
    preds = pd.read_sql("SELECT * FROM predictions", conn)
    snaps = pd.read_sql("SELECT * FROM price_snapshots", conn)
    conn.close()

    preds["created_at"] = pd.to_datetime(preds["created_at"])
    snaps["date"] = pd.to_datetime(snaps["date"])
    return preds, snaps


def score_trade(reverse_view: str, change_pct: float) -> str:
    """
    反指標評分邏輯：
    - reverse_view = '多' (反向觀點看多): 期望價格上漲 -> 漲=win
    - reverse_view = '空' (反向觀點看空): 期望價格下跌 -> 跌=win
    - 0% 視為平盤
    """
    if pd.isna(change_pct) or change_pct is None:
        return "na"
    if abs(change_pct) < 0.01:
        return "flat"
    if reverse_view == "多":
        return "win" if change_pct > 0 else "loss"
    elif reverse_view == "空":
        return "win" if change_pct < 0 else "loss"
    return "na"


def analyze():
    preds, snaps = load_data()

    # 合併預測與價格快照
    df = snaps.merge(
        preds[["id", "symbol_name", "symbol_code", "symbol_type",
               "her_action", "reverse_view", "confidence", "created_at", "base_price"]],
        left_on="prediction_id", right_on="id", how="left"
    )

    # 僅保留有明確方向的 (多/空)
    df = df[df["reverse_view"].isin(["多", "空"])].copy()

    # 計算勝負
    df["result"] = df.apply(
        lambda r: score_trade(r["reverse_view"], r["change_pct_close"]),
        axis=1
    )

    # === 總覽統計 ===
    print("=" * 70)
    print("Banini 反指標回測結果")
    print("=" * 70)
    print(f"\n原始資料:")
    print(f"  預測總數: {len(preds)}")
    print(f"  有明確多/空觀點: {preds['reverse_view'].isin(['多','空']).sum()}")
    print(f"  價格快照總數: {len(snaps)}")
    print(f"  資料期間: {preds['created_at'].min()} ~ {preds['created_at'].max()}")

    # === 按天數分析勝率 ===
    print("\n" + "-" * 70)
    print("按持有天數分析")
    print("-" * 70)

    rows = []
    for day in sorted(df["day_number"].unique()):
        sub = df[df["day_number"] == day]
        wins = (sub["result"] == "win").sum()
        losses = (sub["result"] == "loss").sum()
        flats = (sub["result"] == "flat").sum()
        total = wins + losses  # 排除平盤
        winrate = wins / total * 100 if total > 0 else 0
        avg_ret = sub["change_pct_close"].mean()
        # 正確方向報酬: 反向觀點看多時, 實際漲跌; 看空時, -1 * 實際漲跌
        sub_copy = sub.copy()
        sub_copy["signed_return"] = np.where(
            sub_copy["reverse_view"] == "多",
            sub_copy["change_pct_close"],
            -sub_copy["change_pct_close"]
        )
        strategy_ret = sub_copy["signed_return"].mean()
        rows.append([
            f"{int(day)} 日",
            int(total + flats),
            wins,
            losses,
            flats,
            f"{winrate:.1f}%",
            f"{avg_ret:+.2f}%",
            f"{strategy_ret:+.2f}%",
        ])

    print(tabulate(
        rows,
        headers=["持有期", "樣本", "勝", "負", "平", "勝率", "均漲跌", "策略均報酬"],
        tablefmt="github"
    ))

    # === 按信心度分析 ===
    print("\n" + "-" * 70)
    print("按她的信心度分析 (5 日持有)")
    print("-" * 70)
    sub = df[df["day_number"] == 5].copy()
    rows = []
    for conf in ["high", "medium", "low", ""]:
        cs = sub[sub["confidence"].fillna("") == conf]
        if len(cs) == 0:
            continue
        wins = (cs["result"] == "win").sum()
        losses = (cs["result"] == "loss").sum()
        total = wins + losses
        winrate = wins / total * 100 if total > 0 else 0
        cs_copy = cs.copy()
        cs_copy["signed_return"] = np.where(
            cs_copy["reverse_view"] == "多",
            cs_copy["change_pct_close"], -cs_copy["change_pct_close"]
        )
        strategy_ret = cs_copy["signed_return"].mean()
        rows.append([
            conf or "(無)",
            len(cs),
            f"{winrate:.1f}%",
            f"{strategy_ret:+.2f}%",
        ])
    print(tabulate(rows, headers=["信心度", "樣本", "勝率", "策略均報酬"], tablefmt="github"))

    # === 按方向分析 ===
    print("\n" + "-" * 70)
    print("按反向觀點方向分析 (5 日持有)")
    print("-" * 70)
    rows = []
    for direction in ["多", "空"]:
        cs = sub[sub["reverse_view"] == direction]
        wins = (cs["result"] == "win").sum()
        losses = (cs["result"] == "loss").sum()
        total = wins + losses
        winrate = wins / total * 100 if total > 0 else 0
        avg_move = cs["change_pct_close"].mean()
        rows.append([
            f"反向看{direction}",
            len(cs),
            wins,
            losses,
            f"{winrate:.1f}%",
            f"{avg_move:+.2f}%",
        ])
    print(tabulate(rows, headers=["方向", "樣本", "勝", "負", "勝率", "均漲跌"], tablefmt="github"))

    # === 按她的動作分類 ===
    print("\n" + "-" * 70)
    print("Top 15 最常見的「她的動作」及其反向勝率 (5 日)")
    print("-" * 70)
    sub_actions = sub.copy()
    sub_actions["signed_return"] = np.where(
        sub_actions["reverse_view"] == "多",
        sub_actions["change_pct_close"], -sub_actions["change_pct_close"]
    )
    action_stats = sub_actions.groupby("her_action").agg(
        n=("result", "size"),
        wins=("result", lambda x: (x == "win").sum()),
        losses=("result", lambda x: (x == "loss").sum()),
        strategy_ret=("signed_return", "mean"),
    ).reset_index()
    action_stats["winrate"] = action_stats["wins"] / (action_stats["wins"] + action_stats["losses"]) * 100
    action_stats = action_stats[action_stats["n"] >= 3].sort_values("n", ascending=False).head(15)
    rows = [
        [r["her_action"], int(r["n"]), int(r["wins"]), int(r["losses"]),
         f"{r['winrate']:.1f}%" if not pd.isna(r['winrate']) else "-",
         f"{r['strategy_ret']:+.2f}%"]
        for _, r in action_stats.iterrows()
    ]
    print(tabulate(rows, headers=["她的動作", "樣本", "勝", "負", "反向勝率", "策略均報酬"], tablefmt="github"))

    # === 統計顯著性檢定 ===
    print("\n" + "-" * 70)
    print("統計顯著性檢定 (二項檢定 vs. 50% 隨機)")
    print("-" * 70)
    from scipy import stats as sps_stats
    rows = []
    for day in sorted(df["day_number"].unique()):
        sub_d = df[df["day_number"] == day]
        wins = (sub_d["result"] == "win").sum()
        losses = (sub_d["result"] == "loss").sum()
        total = wins + losses
        if total < 10:
            continue
        # Binomial test H0: p = 0.5
        result = sps_stats.binomtest(wins, total, 0.5, alternative="two-sided")
        p_value = result.pvalue
        winrate = wins / total * 100
        signif = "***" if p_value < 0.01 else ("**" if p_value < 0.05 else ("*" if p_value < 0.1 else "ns"))
        rows.append([
            f"{int(day)} 日",
            f"{wins}/{total}",
            f"{winrate:.1f}%",
            f"{p_value:.4f}",
            signif,
        ])
    print(tabulate(rows, headers=["期間", "勝/總", "勝率", "p-value", "顯著性"], tablefmt="github"))
    print("\n顯著性: *** p<0.01, ** p<0.05, * p<0.1, ns=無顯著差異")

    # === 儲存詳細結果 ===
    detail_file = OUT / "banini_backtest_detail.csv"
    df[["prediction_id", "created_at", "symbol_name", "symbol_code",
        "her_action", "reverse_view", "confidence",
        "day_number", "date", "close_price", "change_pct_close", "result"]].to_csv(
        detail_file, index=False, encoding="utf-8-sig"
    )
    print(f"\n詳細資料儲存: {detail_file}")

    return df


if __name__ == "__main__":
    # scipy for binomial test
    try:
        import scipy
    except ImportError:
        import subprocess
        subprocess.run(["pip3", "install", "-q", "scipy"], check=True)
    analyze()
