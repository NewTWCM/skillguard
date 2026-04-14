"""
交易成本與滑價模組 — 可配置 + 預設值

用途: 套用到任何回測, 將 gross return 轉為 net-of-cost return
用法:
    from costs import CostProfile, apply_costs

    # 使用預設 (台股 / 美股 / 加密一般值)
    p = CostProfile.default("tw_stock")
    net_ret = apply_costs(gross_ret_pct=2.5, profile=p)

    # 或互動式輸入
    p = CostProfile.from_user_input("us_stock")

設計原則:
    - 所有成本以「round-trip 百分比」表示 (進場 + 出場加總)
    - 滑價獨立於手續費以便分別調整
    - CLI / import 雙模式
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path(__file__).parent / "data" / "cost_profiles.json"


# ============================================================
# 預設成本值 (來源: 各交易所官方費率表, 2026 標準)
# ============================================================

DEFAULTS = {
    "tw_stock": {
        "commission_bps": 14.25,    # 券商手續費 0.1425%
        "commission_discount": 0.28,  # 常見網路下單 2.8 折
        "tax_bps": 30,              # 證交稅 0.3% (賣方)
        "slippage_bps_per_leg": 2,  # 2 bps 滑價/單邊
        "rounds": "buy_sell",        # 手續費兩邊都收
        "tax_side": "sell_only",     # 稅只收賣方
        "notes": "台股現股 2.8 折網路下單 + 證交稅 0.3%; 當沖證交稅減半 0.15%",
    },
    "tw_stock_day_trade": {
        "commission_bps": 14.25,
        "commission_discount": 0.28,
        "tax_bps": 15,               # 當沖稅減半
        "slippage_bps_per_leg": 2,
        "rounds": "buy_sell",
        "tax_side": "sell_only",
        "notes": "台股當沖 (證交稅半稅 0.15%)",
    },
    "tw_futures": {
        "commission_bps": 0,         # 不用 bps, 固定 NT$ 每口
        "commission_fixed_ntd": 60,  # 約 NT$60/口 (網路價)
        "tax_bps": 0.2,              # 期交稅 0.002% × 合約價值
        "slippage_bps_per_leg": 3,
        "rounds": "buy_sell",
        "tax_side": "both",
        "notes": "台指期每口手續費約 NT$40-80 + 期交稅 0.002%",
    },
    "us_stock": {
        "commission_bps": 0,
        "commission_fixed_usd": 0,   # Robinhood / IBKR Lite 免手續費
        "tax_bps": 0,
        "slippage_bps_per_leg": 1,   # 大型股流動性佳
        "rounds": "buy_sell",
        "tax_side": "none",
        "notes": "IBKR Lite / Robinhood 免佣; IBKR Pro $0.005/share",
    },
    "us_stock_ibkr_pro": {
        "commission_bps": 0,
        "commission_per_share_usd": 0.005,
        "commission_min_usd": 1.0,
        "commission_max_bps": 100,   # capped 1% of trade value
        "tax_bps": 0,
        "slippage_bps_per_leg": 1,
        "rounds": "buy_sell",
        "tax_side": "none",
        "notes": "IBKR Pro 分級費率 (美股)",
    },
    "us_option": {
        "commission_bps": 0,
        "commission_per_contract_usd": 0.65,  # IBKR / TD Ameritrade
        "tax_bps": 0,
        "slippage_bps_per_leg": 50,  # 期權 bid-ask 較大
        "rounds": "buy_sell",
        "tax_side": "none",
        "notes": "美股期權 $0.65/contract + 較大滑價 (價差)",
    },
    "crypto_spot": {
        "commission_bps": 10,        # Binance spot 0.1%
        "tax_bps": 0,
        "slippage_bps_per_leg": 5,
        "rounds": "buy_sell",
        "tax_side": "none",
        "notes": "Binance 現貨 taker 0.1% (VIP 0 / 有 BNB 折扣)",
    },
    "crypto_perp": {
        "commission_bps": 5,         # Binance perp taker 0.05%
        "funding_bps_per_day": 3,    # 平均 0.03% 每 8 小時 × 3 = 0.09%/日
        "tax_bps": 0,
        "slippage_bps_per_leg": 5,
        "rounds": "buy_sell",
        "tax_side": "none",
        "notes": "Binance 永續 taker 0.05% + 資金費率 (避長期持有)",
    },
}


# ============================================================
# 核心結構
# ============================================================

@dataclass
class CostProfile:
    """成本設定檔"""
    market: str                          # 標識符 (tw_stock / us_stock / crypto_spot...)
    commission_bps: float = 0            # 手續費 (基點 1 bp = 0.01%)
    commission_discount: float = 1.0     # 折扣 (0.28 = 2.8 折)
    commission_fixed_ntd: float = 0      # 固定手續費 NTD/交易
    commission_fixed_usd: float = 0      # 固定手續費 USD/交易
    commission_per_share_usd: float = 0  # 每股手續費
    commission_per_contract_usd: float = 0  # 期權每口手續費
    commission_min_usd: float = 0        # 最低手續費
    commission_max_bps: float = 0        # 手續費上限 (bps, 0=無限)
    tax_bps: float = 0                   # 交易稅 (基點)
    slippage_bps_per_leg: float = 0      # 滑價/單邊 (基點)
    funding_bps_per_day: float = 0       # 資金費率 (加密永續)
    rounds: str = "buy_sell"
    tax_side: str = "none"               # none / sell_only / both
    notes: str = ""

    @classmethod
    def default(cls, market: str) -> "CostProfile":
        if market not in DEFAULTS:
            raise ValueError(f"未知市場: {market}. 可選: {list(DEFAULTS.keys())}")
        d = DEFAULTS[market].copy()
        d["market"] = market
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def round_trip_bps(self, trade_notional_usd: float = 10000,
                       hold_days: float = 0) -> float:
        """
        計算單筆完整交易 (買+賣) 的總成本 (bps)
        trade_notional_usd: 交易名目價值 (用於固定費換算)
        hold_days: 持有天數 (用於資金費率)
        """
        total_bps = 0.0

        # 1. 手續費 (兩邊)
        if self.commission_bps > 0:
            total_bps += self.commission_bps * self.commission_discount * 2

        # 2. 固定手續費 → 換算成 bps
        fixed_per_leg_usd = 0
        if self.commission_fixed_usd > 0:
            fixed_per_leg_usd += self.commission_fixed_usd
        if self.commission_per_share_usd > 0 and trade_notional_usd > 0:
            # 假設平均股價 $100
            shares = trade_notional_usd / 100
            fee = max(shares * self.commission_per_share_usd,
                      self.commission_min_usd)
            if self.commission_max_bps > 0:
                fee = min(fee, trade_notional_usd * self.commission_max_bps / 10000)
            fixed_per_leg_usd += fee
        if self.commission_per_contract_usd > 0:
            # 假設 1 contract = $5000 名目
            contracts = trade_notional_usd / 5000
            fixed_per_leg_usd += contracts * self.commission_per_contract_usd

        if trade_notional_usd > 0:
            total_bps += (fixed_per_leg_usd / trade_notional_usd * 10000) * 2

        # 3. 交易稅
        if self.tax_side == "sell_only":
            total_bps += self.tax_bps
        elif self.tax_side == "both":
            total_bps += self.tax_bps * 2

        # 4. 滑價 (兩邊)
        total_bps += self.slippage_bps_per_leg * 2

        # 5. 資金費率 (加密永續, 僅 long 會付多頭溢價)
        if hold_days > 0:
            total_bps += self.funding_bps_per_day * hold_days

        return total_bps

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_user_input(cls, market: str, interactive: bool = True) -> "CostProfile":
        """互動式讓用戶輸入或確認每個值"""
        defaults = cls.default(market)
        if not interactive or not sys.stdin.isatty():
            return defaults

        print(f"\n=== 設定 {market} 成本檔 ===")
        print(f"預設: {defaults.notes}")
        print("直接按 Enter 保留預設值, 或輸入新值:")

        def ask(field_name: str, cur_value):
            if cur_value == 0 and field_name in ("commission_fixed_ntd", "commission_fixed_usd",
                                                  "commission_per_share_usd",
                                                  "commission_per_contract_usd",
                                                  "funding_bps_per_day"):
                return cur_value  # 跳過不相關欄位
            try:
                raw = input(f"  {field_name} [{cur_value}]: ").strip()
                if not raw:
                    return cur_value
                return float(raw)
            except (EOFError, KeyboardInterrupt):
                return cur_value

        defaults.commission_bps = ask("commission_bps (手續費基點)", defaults.commission_bps)
        defaults.commission_discount = ask("commission_discount (折扣)", defaults.commission_discount)
        defaults.tax_bps = ask("tax_bps (交易稅基點)", defaults.tax_bps)
        defaults.slippage_bps_per_leg = ask("slippage_bps_per_leg (滑價/邊)", defaults.slippage_bps_per_leg)
        if defaults.funding_bps_per_day > 0:
            defaults.funding_bps_per_day = ask("funding_bps_per_day", defaults.funding_bps_per_day)

        return defaults


# ============================================================
# 外掛到回測報酬率
# ============================================================

def apply_costs(gross_ret_pct: float, profile: CostProfile,
                hold_days: float = 0,
                trade_notional_usd: float = 10000) -> float:
    """
    將毛報酬率 (%) 轉為淨報酬率 (%)
    gross_ret_pct: 回測算出的 gross 報酬 (%, 例如 2.5 表示 2.5%)
    """
    cost_bps = profile.round_trip_bps(trade_notional_usd, hold_days)
    cost_pct = cost_bps / 100  # bps → %
    return gross_ret_pct - cost_pct


def apply_costs_to_trades(trade_returns_pct: list[float],
                          profile: CostProfile,
                          hold_days: float = 0,
                          trade_notional_usd: float = 10000) -> list[float]:
    """批次套用到交易列表"""
    return [apply_costs(r, profile, hold_days, trade_notional_usd)
            for r in trade_returns_pct]


def winrate_delta(trade_returns_pct: list[float],
                  profile: CostProfile,
                  hold_days: float = 0) -> dict:
    """計算扣除成本前後的勝率變化"""
    gross = [r for r in trade_returns_pct if r != 0]
    net = apply_costs_to_trades(gross, profile, hold_days)

    gross_wr = sum(1 for r in gross if r > 0) / len(gross) * 100 if gross else 0
    net_wr = sum(1 for r in net if r > 0) / len(net) * 100 if net else 0
    cost_bps = profile.round_trip_bps(10000, hold_days)

    return {
        "n": len(gross),
        "gross_winrate": gross_wr,
        "net_winrate": net_wr,
        "winrate_drop_pp": gross_wr - net_wr,
        "gross_avg": sum(gross) / len(gross) if gross else 0,
        "net_avg": sum(net) / len(net) if net else 0,
        "cost_bps_round_trip": cost_bps,
        "cost_pct_round_trip": cost_bps / 100,
    }


# ============================================================
# Persistence — 存取設定檔
# ============================================================

def load_profiles() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}


def save_profile(profile: CostProfile):
    CONFIG_PATH.parent.mkdir(exist_ok=True)
    existing = load_profiles()
    existing[profile.market] = profile.to_dict()
    CONFIG_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    print(f"已儲存 {profile.market} 至 {CONFIG_PATH}")


# ============================================================
# CLI
# ============================================================

def cmd_show():
    """列出所有預設市場的 round-trip 成本"""
    print("\n=== 預設市場 Round-Trip 成本對照表 ===\n")
    print(f"{'市場':<25} {'bps':>10} {'% round-trip':>15}")
    print("-" * 55)
    for m in DEFAULTS.keys():
        p = CostProfile.default(m)
        bps = p.round_trip_bps(10000, 0)
        print(f"{m:<25} {bps:>10.1f} {bps/100:>14.3f}%")
    print()

    # 顯示 30 日加密永續 funding 影響
    p = CostProfile.default("crypto_perp")
    bps_30d = p.round_trip_bps(10000, 30)
    print(f"注意: crypto_perp 持有 30 日含資金費率 = {bps_30d:.1f} bps ({bps_30d/100:.2f}%)\n")


def cmd_configure(market: str):
    """互動設定並存檔"""
    p = CostProfile.from_user_input(market)
    save_profile(p)
    print(f"\n最終設定: round-trip = {p.round_trip_bps():.1f} bps ({p.round_trip_bps()/100:.3f}%)")


def cmd_apply(market: str, gross_pct: float, hold_days: float):
    """計算單筆交易套用成本後的淨報酬"""
    profiles = load_profiles()
    if market in profiles:
        p = CostProfile(**profiles[market])
    else:
        p = CostProfile.default(market)

    net = apply_costs(gross_pct, p, hold_days)
    print(f"市場: {market}")
    print(f"  Gross:     {gross_pct:+.3f}%")
    print(f"  成本:      {p.round_trip_bps(10000, hold_days)/100:.3f}%")
    print(f"  Net:       {net:+.3f}%")


def main():
    ap = argparse.ArgumentParser(description="交易成本 + 滑價模組")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("show", help="顯示所有預設成本")

    cfg = sub.add_parser("configure", help="互動設定單一市場")
    cfg.add_argument("market", choices=list(DEFAULTS.keys()))

    app = sub.add_parser("apply", help="對單筆 gross 報酬套用成本")
    app.add_argument("market", choices=list(DEFAULTS.keys()))
    app.add_argument("gross_pct", type=float, help="Gross 報酬 (%, 例如 2.5)")
    app.add_argument("--hold-days", type=float, default=0, help="持有天數 (用於 funding)")

    args = ap.parse_args()

    if args.cmd == "show":
        cmd_show()
    elif args.cmd == "configure":
        cmd_configure(args.market)
    elif args.cmd == "apply":
        cmd_apply(args.market, args.gross_pct, args.hold_days)


if __name__ == "__main__":
    main()
