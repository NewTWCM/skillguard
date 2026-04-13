"""
深度分析: 持有天數 × 報酬率 熱力圖
核心問題:
  1. 不同進場條件下, 最佳持有天數是多少?
  2. 做多 vs 做空的報酬結構是否對稱?
  3. 極端值 vs 中度值的報酬衰減曲線為何?

跨市場比較:
  - BTC (加密幣)
  - SPY (美股)
  - Banini 停損信號 (台股個股)
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # 非互動式後端
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from scipy import stats as sps_stats
from tabulate import tabulate

DATA_DIR = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

# 配色: 紅 (虧損) - 白 (零) - 綠 (獲利)
CMAP = LinearSegmentedColormap.from_list("RdWhGn", ["#b22222", "#ffffff", "#006400"], N=256)


def load_btc_data() -> pd.DataFrame:
    """載入 BTC 與加密幣 FNG"""
    btc = pd.read_csv(DATA_DIR / "yahoo_BTC-USD.csv", parse_dates=["date"])
    fng = pd.read_csv(DATA_DIR / "crypto_fng.csv", parse_dates=["date"])
    # Yahoo 日期可能帶時區, 僅取日期部分
    btc["date"] = pd.to_datetime(btc["date"]).dt.tz_localize(None).dt.normalize()
    fng["date"] = pd.to_datetime(fng["date"]).dt.tz_localize(None).dt.normalize()
    df = btc[["date", "close"]].merge(fng[["date", "fng"]], on="date", how="inner")
    return df.sort_values("date").reset_index(drop=True)


def load_spy_data() -> pd.DataFrame:
    spy = pd.read_csv(DATA_DIR / "yahoo_SPY.csv", parse_dates=["date"])
    fng = pd.read_csv(DATA_DIR / "crypto_fng.csv", parse_dates=["date"])
    spy["date"] = pd.to_datetime(spy["date"]).dt.tz_localize(None).dt.normalize()
    fng["date"] = pd.to_datetime(fng["date"]).dt.tz_localize(None).dt.normalize()
    df = spy[["date", "close"]].merge(fng[["date", "fng"]], on="date", how="inner")
    return df.sort_values("date").reset_index(drop=True)


def build_holding_matrix(df: pd.DataFrame, fng_col: str = "fng",
                          fng_bins=None, hold_days=None,
                          direction: str = "both") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    建立 [FNG 區間 × 持有天數] 的報酬 & 勝率矩陣
    direction:
      'long'  = 假設進場做多, 計算原始報酬
      'short' = 假設進場做空, 計算 -報酬
      'both'  = 正向持有報酬 (用於觀察)
    回傳: (mean_return, winrate, n_samples) 三個矩陣
    """
    if fng_bins is None:
        fng_bins = [(0, 10), (10, 20), (20, 30), (30, 40),
                    (40, 60), (60, 70), (70, 80), (80, 90), (90, 100)]
    if hold_days is None:
        hold_days = [1, 2, 3, 5, 7, 10, 14, 21, 30, 45, 60, 90]

    mean_ret = pd.DataFrame(index=[f"{lo}-{hi}" for lo, hi in fng_bins],
                             columns=hold_days, dtype=float)
    winrate = mean_ret.copy()
    n_samples = mean_ret.copy()

    for hold in hold_days:
        d = df.copy()
        d["entry"] = d["close"].shift(-1)
        d["exit"] = d["close"].shift(-1 - hold)
        d["raw_ret"] = (d["exit"] - d["entry"]) / d["entry"] * 100
        if direction == "long":
            d["ret"] = d["raw_ret"]
        elif direction == "short":
            d["ret"] = -d["raw_ret"]
        else:
            d["ret"] = d["raw_ret"]

        for lo, hi in fng_bins:
            mask = (d[fng_col] >= lo) & (d[fng_col] < hi)
            sub = d[mask].dropna(subset=["ret"])
            if len(sub) < 5:
                mean_ret.loc[f"{lo}-{hi}", hold] = np.nan
                winrate.loc[f"{lo}-{hi}", hold] = np.nan
                n_samples.loc[f"{lo}-{hi}", hold] = len(sub)
                continue
            mean_ret.loc[f"{lo}-{hi}", hold] = sub["ret"].mean()
            wr = (sub["ret"] > 0).sum() / len(sub) * 100
            winrate.loc[f"{lo}-{hi}", hold] = wr
            n_samples.loc[f"{lo}-{hi}", hold] = len(sub)

    return mean_ret, winrate, n_samples


def plot_heatmap(matrix: pd.DataFrame, title: str, fname: str,
                  cbar_label: str = "%", vmin=None, vmax=None,
                  fmt: str = ".2f", center: float = 0.0):
    """繪製熱力圖"""
    fig, ax = plt.subplots(figsize=(14, 7))
    values = matrix.astype(float).values

    if vmin is None:
        vmin = np.nanmin(values)
    if vmax is None:
        vmax = np.nanmax(values)
    if center is not None and vmin < center < vmax:
        norm = TwoSlopeNorm(vcenter=center, vmin=vmin, vmax=vmax)
    else:
        norm = None

    im = ax.imshow(values, cmap=CMAP, aspect="auto", norm=norm)

    ax.set_xticks(np.arange(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns)
    ax.set_yticks(np.arange(len(matrix.index)))
    ax.set_yticklabels(matrix.index)

    for i in range(len(matrix.index)):
        for j in range(len(matrix.columns)):
            v = values[i, j]
            if np.isnan(v):
                txt = "—"
            else:
                txt = f"{v:{fmt}}"
            ax.text(j, i, txt, ha="center", va="center",
                    color="black" if abs(v or 0) < (vmax - vmin) / 3 else "white",
                    fontsize=9)

    ax.set_xlabel("Holding Days")
    ax.set_ylabel("FNG Range")
    ax.set_title(title)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label(cbar_label)
    plt.tight_layout()
    plt.savefig(OUT / fname, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  [SAVED] {OUT / fname}")


def analyze_market(df: pd.DataFrame, label: str):
    """對單一市場做完整的持有期 × FNG 分析"""
    print(f"\n{'=' * 70}")
    print(f"深度分析: {label}")
    print(f"{'=' * 70}")
    print(f"樣本: {len(df)} 天, 期間 {df['date'].min().date()} ~ {df['date'].max().date()}")

    # 1. 做多報酬矩陣
    long_ret, long_wr, long_n = build_holding_matrix(df, direction="long")

    # 2. 做空報酬矩陣
    short_ret, short_wr, _ = build_holding_matrix(df, direction="short")

    # ===== 文字摘要 =====
    print(f"\n[做多平均報酬 %] — FNG 區間 × 持有天數")
    print(tabulate(
        long_ret.round(2).fillna("-"),
        headers=[f"{h}d" for h in long_ret.columns],
        tablefmt="github", showindex=True,
    ))

    print(f"\n[做多勝率 %]")
    print(tabulate(
        long_wr.round(1).fillna("-"),
        headers=[f"{h}d" for h in long_wr.columns],
        tablefmt="github", showindex=True,
    ))

    print(f"\n[樣本數]")
    print(tabulate(
        long_n.fillna(0).astype(int),
        headers=[f"{h}d" for h in long_n.columns],
        tablefmt="github", showindex=True,
    ))

    # ===== 畫圖 =====
    safe = label.replace(" ", "_").replace("/", "-")
    plot_heatmap(long_ret, f"{label} - Long Return % (FNG x Holding Days)",
                 f"heatmap_{safe}_long_return.png", cbar_label="%",
                 vmin=long_ret.min().min(), vmax=long_ret.max().max())
    plot_heatmap(long_wr, f"{label} - Long Win Rate % (FNG x Holding Days)",
                 f"heatmap_{safe}_long_winrate.png", cbar_label="%",
                 vmin=30, vmax=70, center=50, fmt=".0f")
    plot_heatmap(short_ret, f"{label} - Short Return % (FNG x Holding Days)",
                 f"heatmap_{safe}_short_return.png", cbar_label="%",
                 vmin=short_ret.min().min(), vmax=short_ret.max().max())
    plot_heatmap(short_wr, f"{label} - Short Win Rate % (FNG x Holding Days)",
                 f"heatmap_{safe}_short_winrate.png", cbar_label="%",
                 vmin=30, vmax=70, center=50, fmt=".0f")

    # ===== 存 CSV =====
    long_ret.to_csv(OUT / f"matrix_{safe}_long_return.csv")
    long_wr.to_csv(OUT / f"matrix_{safe}_long_winrate.csv")
    short_ret.to_csv(OUT / f"matrix_{safe}_short_return.csv")
    short_wr.to_csv(OUT / f"matrix_{safe}_short_winrate.csv")

    # ===== 最佳策略識別 =====
    print(f"\n[做多 TOP 5 最高平均報酬]")
    stacked = long_ret.stack().reset_index()
    stacked.columns = ["FNG Range", "Hold Days", "Mean Return"]
    stacked = stacked.dropna().sort_values("Mean Return", ascending=False).head(5)
    for _, r in stacked.iterrows():
        fng_range = r["FNG Range"]
        hold = r["Hold Days"]
        wr = long_wr.loc[fng_range, hold]
        n = long_n.loc[fng_range, hold]
        print(f"  FNG {fng_range} × {hold} 日: "
              f"均報酬 {r['Mean Return']:+.2f}%, 勝率 {wr:.1f}%, 樣本 {int(n)}")

    print(f"\n[做空 TOP 5 最高平均報酬]")
    stacked_s = short_ret.stack().reset_index()
    stacked_s.columns = ["FNG Range", "Hold Days", "Mean Return"]
    stacked_s = stacked_s.dropna().sort_values("Mean Return", ascending=False).head(5)
    for _, r in stacked_s.iterrows():
        fng_range = r["FNG Range"]
        hold = r["Hold Days"]
        wr = short_wr.loc[fng_range, hold]
        print(f"  FNG {fng_range} × {hold} 日: "
              f"均報酬 {r['Mean Return']:+.2f}%, 勝率 {wr:.1f}%")

    # ===== 不對稱性指數 =====
    print(f"\n[不對稱性分析]")
    # 極度恐懼 (0-20) 做多 vs 極度貪婪 (80-100) 做空
    for hold in [5, 10, 20, 30]:
        if hold not in long_ret.columns:
            continue
        fear_long = long_ret.loc[["0-10", "10-20"], hold].dropna()
        greed_short = short_ret.loc[["80-90", "90-100"], hold].dropna()
        if len(fear_long) > 0 and len(greed_short) > 0:
            fear_ret = fear_long.mean()
            greed_ret = greed_short.mean()
            print(f"  {hold} 日: 恐懼買入 {fear_ret:+.2f}%, 貪婪賣空 {greed_ret:+.2f}%, "
                  f"差距 {fear_ret - greed_ret:+.2f}pp")

    return long_ret, long_wr, short_ret, short_wr


def analyze_banini_holding():
    """Banini 停損信號的持有期分析"""
    print(f"\n{'=' * 70}")
    print("Banini 信號 × 持有期分析")
    print(f"{'=' * 70}")

    conn = sqlite3.connect(DATA_DIR / "banini-public.db")
    preds = pd.read_sql("SELECT * FROM predictions", conn)
    snaps = pd.read_sql("SELECT * FROM price_snapshots", conn)
    conn.close()

    df = snaps.merge(
        preds[["id", "her_action", "reverse_view", "base_price"]],
        left_on="prediction_id", right_on="id", how="left"
    )

    # 計算策略報酬 (反向觀點方向)
    def signed(row):
        if row["reverse_view"] == "多":
            return row["change_pct_close"]
        elif row["reverse_view"] == "空":
            return -row["change_pct_close"]
        return None

    df["strat_ret"] = df.apply(signed, axis=1)

    # 分組: 按動作 × 天數
    actions = ["停損賣出", "買入", "看多", "計畫買入", "持有", "被套", "賣出", "看空"]
    hold_days = sorted(df["day_number"].unique())

    ret_matrix = pd.DataFrame(index=actions, columns=hold_days, dtype=float)
    wr_matrix = pd.DataFrame(index=actions, columns=hold_days, dtype=float)
    n_matrix = pd.DataFrame(index=actions, columns=hold_days, dtype=int)

    for action in actions:
        for day in hold_days:
            sub = df[(df["her_action"] == action) & (df["day_number"] == day)].dropna(subset=["strat_ret"])
            if len(sub) < 2:
                ret_matrix.loc[action, day] = np.nan
                wr_matrix.loc[action, day] = np.nan
                n_matrix.loc[action, day] = len(sub)
                continue
            ret_matrix.loc[action, day] = sub["strat_ret"].mean()
            wr = (sub["strat_ret"] > 0).sum() / len(sub) * 100
            wr_matrix.loc[action, day] = wr
            n_matrix.loc[action, day] = len(sub)

    print("\n[反向策略平均報酬 %] — Banini 動作 × 持有天數")
    print(tabulate(ret_matrix.round(2).fillna("-"),
                   headers=[f"{int(h)}d" for h in ret_matrix.columns],
                   tablefmt="github", showindex=True))

    print("\n[反向策略勝率 %]")
    print(tabulate(wr_matrix.round(1).fillna("-"),
                   headers=[f"{int(h)}d" for h in wr_matrix.columns],
                   tablefmt="github", showindex=True))

    print("\n[樣本數]")
    print(tabulate(n_matrix.fillna(0).astype(int),
                   headers=[f"{int(h)}d" for h in n_matrix.columns],
                   tablefmt="github", showindex=True))

    plot_heatmap(ret_matrix, "Banini Reverse Strategy Return % (Action × Hold Days)",
                 "heatmap_Banini_action_return.png", cbar_label="%", fmt=".2f")
    plot_heatmap(wr_matrix, "Banini Reverse Strategy Win Rate % (Action × Hold Days)",
                 "heatmap_Banini_action_winrate.png",
                 cbar_label="%", vmin=20, vmax=80, center=50, fmt=".0f")

    ret_matrix.to_csv(OUT / "matrix_banini_action_return.csv")
    wr_matrix.to_csv(OUT / "matrix_banini_action_winrate.csv")


def main():
    print("=" * 70)
    print("反指標深度分析: 持有期 × 報酬率 熱力圖")
    print("=" * 70)

    # 1. BTC
    btc_df = load_btc_data()
    analyze_market(btc_df, "BTC-USD (Crypto FNG)")

    # 2. SPY
    spy_df = load_spy_data()
    analyze_market(spy_df, "SPY (Crypto FNG as proxy)")

    # 3. Banini
    analyze_banini_holding()

    print("\n" + "=" * 70)
    print("所有熱力圖與 CSV 已輸出至 output/")
    print("=" * 70)


if __name__ == "__main__":
    main()
