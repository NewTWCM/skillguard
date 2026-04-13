"""
即時反指標監控儀表板

監控:
  1. Crypto Fear & Greed Index (alternative.me) → 極端值時觸發警報
  2. BTC 30 日均 + 當前價格 (Yahoo)
  3. SPY 當前價格

警報條件 (基於回測):
  - FNG < 15 → 極度恐懼 → 做多 BTC/SPY 訊號 (BTC 30 日勝率 76%)
  - FNG > 85 → 極度貪婪 → 降低曝險/止盈警示 (不建議做空)

使用:
  python3 monitoring_dashboard.py               # 單次檢查並印出
  python3 monitoring_dashboard.py --watch       # 每 4 小時輪詢
  python3 monitoring_dashboard.py --telegram    # 觸發時發 Telegram
  環境變數 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)
STATE_FILE = OUT / "dashboard_state.json"

# --- 警報門檻 (基於本專案回測) ---
FNG_EXTREME_FEAR = 15    # BTC 30d 勝率 76% (n=33)
FNG_EXTREME_GREED = 85   # 不做空 (勝率 13%), 僅警示
FNG_DEEP_FEAR = 10       # 更強信號
FNG_DEEP_GREED = 90      # 極度警示

# --- 資料源 ---
FNG_URL = "https://api.alternative.me/fng/?limit=1"
FNG_HIST_URL = "https://api.alternative.me/fng/?limit=30"
BTC_URL = "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD?interval=1d&range=1mo"
SPY_URL = "https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&range=1mo"


def fetch_fng() -> dict | None:
    try:
        r = requests.get(FNG_URL, timeout=15)
        d = r.json()["data"][0]
        return {
            "fng": int(d["value"]),
            "classification": d["value_classification"],
            "timestamp": int(d["timestamp"]),
        }
    except Exception as e:
        print(f"[fetch_fng] {e}", file=sys.stderr)
        return None


def fetch_fng_history() -> list:
    try:
        r = requests.get(FNG_HIST_URL, timeout=15)
        return [{"fng": int(d["value"]),
                 "class": d["value_classification"],
                 "ts": int(d["timestamp"])}
                for d in r.json()["data"]]
    except Exception:
        return []


def fetch_price(url: str) -> dict | None:
    try:
        r = requests.get(url, timeout=15,
                         headers={"User-Agent": "Mozilla/5.0"})
        j = r.json()["chart"]["result"][0]
        closes = [c for c in j["indicators"]["quote"][0]["close"] if c is not None]
        if not closes:
            return None
        return {
            "last": closes[-1],
            "prev_close": closes[-2] if len(closes) > 1 else closes[-1],
            "avg_30d": sum(closes) / len(closes),
            "n_days": len(closes),
        }
    except Exception as e:
        print(f"[fetch_price] {e}", file=sys.stderr)
        return None


def classify_signal(fng: int) -> dict:
    """根據 FNG 數值決定信號強度與方向。"""
    if fng <= FNG_DEEP_FEAR:
        return {"level": "DEEP_FEAR", "action": "STRONG_LONG",
                "strength": "極強", "note": "BTC 30 日極深恐懼勝率 > 75%",
                "alert": True, "priority": "HIGH"}
    if fng <= FNG_EXTREME_FEAR:
        return {"level": "EXTREME_FEAR", "action": "LONG",
                "strength": "強", "note": "BTC 30 日勝率 ~76%, SPY ~44%",
                "alert": True, "priority": "MEDIUM"}
    if fng >= FNG_DEEP_GREED:
        return {"level": "DEEP_GREED", "action": "REDUCE_EXPOSURE",
                "strength": "警告",
                "note": "不要做空! 僅部分止盈/買保護性 Put",
                "alert": True, "priority": "HIGH"}
    if fng >= FNG_EXTREME_GREED:
        return {"level": "EXTREME_GREED", "action": "CAUTION",
                "strength": "警示",
                "note": "做空勝率 < 15%, 考慮減少曝險而非放空",
                "alert": True, "priority": "MEDIUM"}
    return {"level": "NEUTRAL", "action": "HOLD",
            "strength": "觀望", "note": "FNG 在一般區間",
            "alert": False, "priority": "LOW"}


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def send_telegram(message: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        print("[telegram] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 未設定, 跳過推送")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat, "text": message, "parse_mode": "Markdown"},
            timeout=15,
        )
        return r.status_code == 200
    except Exception as e:
        print(f"[telegram] {e}", file=sys.stderr)
        return False


def build_report(fng_now: dict, fng_hist: list,
                 btc: dict | None, spy: dict | None,
                 signal: dict) -> str:
    ts = datetime.fromtimestamp(fng_now["timestamp"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "=" * 60,
        f"反指標監控儀表板 ({ts})",
        "=" * 60,
        "",
        f"  Crypto FNG:       {fng_now['fng']}/100 ({fng_now['classification']})",
    ]

    if fng_hist:
        vals = [h["fng"] for h in fng_hist]
        avg = sum(vals) / len(vals)
        lo = min(vals)
        hi = max(vals)
        lines.append(f"  FNG 30 日:        avg {avg:.1f}, min {lo}, max {hi}")

    if btc:
        ret = (btc["last"] / btc["prev_close"] - 1) * 100
        lines.append(f"  BTC-USD:          ${btc['last']:,.0f} "
                     f"({ret:+.2f}% 日) / 30 日均 ${btc['avg_30d']:,.0f}")

    if spy:
        ret = (spy["last"] / spy["prev_close"] - 1) * 100
        lines.append(f"  SPY:              ${spy['last']:.2f} "
                     f"({ret:+.2f}% 日) / 30 日均 ${spy['avg_30d']:.2f}")

    lines.extend([
        "",
        f"  [信號] {signal['level']} — 強度: {signal['strength']}",
        f"  [建議] {signal['action']}",
        f"  [備註] {signal['note']}",
        "",
    ])

    if signal["alert"]:
        if signal["action"] == "STRONG_LONG" or signal["action"] == "LONG":
            lines.append("  ✅ 建議: 分批逢低買入 BTC/SPY; 持有 14-30 日")
            lines.append("     基於回測: FNG < 15 時 BTC 30 日勝率 76%, 平均 +4.81%")
        else:
            lines.append("  ⚠️  建議: 部分止盈 / 買保護性 Put / 降低槓桿")
            lines.append("     基於回測: FNG > 85 時做空勝率僅 13%, 強行做空平均 -21%")

    lines.extend(["", "=" * 60])
    return "\n".join(lines)


def build_telegram_message(signal: dict, fng: int, btc_last, spy_last) -> str:
    emoji = "🟢" if signal["action"] in ("LONG", "STRONG_LONG") else "🔴"
    return (
        f"{emoji} *反指標信號觸發*\n\n"
        f"*FNG*: `{fng}/100` ({signal['level']})\n"
        f"*BTC*: `${btc_last:,.0f}`\n" if btc_last else ""
        f"*SPY*: `${spy_last:.2f}`\n" if spy_last else ""
        f"\n*建議*: {signal['action']}\n"
        f"*說明*: {signal['note']}\n\n"
        f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"_基於 7 年量化回測 (BTC + SPY + Crypto FNG)_"
    )


def check_once(use_telegram: bool = False, force_alert: bool = False):
    fng_now = fetch_fng()
    if not fng_now:
        print("無法取得 FNG, 跳過本次檢查")
        return

    fng_hist = fetch_fng_history()
    btc = fetch_price(BTC_URL)
    spy = fetch_price(SPY_URL)
    signal = classify_signal(fng_now["fng"])

    report = build_report(fng_now, fng_hist, btc, spy, signal)
    print(report)

    # 歷史記錄
    state = load_state()
    history = state.get("history", [])
    history.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "fng": fng_now["fng"],
        "level": signal["level"],
        "action": signal["action"],
        "btc_last": btc["last"] if btc else None,
        "spy_last": spy["last"] if spy else None,
    })
    state["history"] = history[-200:]  # 保留最近 200 次
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    last_alert_level = state.get("last_alert_level")

    # 判斷是否需要發送警報 (邊緣觸發: 從 NEUTRAL 進入極端, 或極端升級)
    should_alert = signal["alert"] and (
        force_alert or last_alert_level != signal["level"]
    )

    if should_alert and use_telegram:
        msg = build_telegram_message(
            signal, fng_now["fng"],
            btc["last"] if btc else None,
            spy["last"] if spy else None,
        )
        sent = send_telegram(msg)
        print(f"\n[Telegram] {'已推送' if sent else '發送失敗'}")
        state["last_alert_ts"] = datetime.now(timezone.utc).isoformat()

    state["last_alert_level"] = signal["level"]
    save_state(state)


def watch(interval_hours: int, use_telegram: bool):
    print(f"監控模式啟動, 每 {interval_hours} 小時輪詢一次. Ctrl+C 停止.")
    while True:
        try:
            check_once(use_telegram=use_telegram)
        except Exception as e:
            print(f"[watch] 錯誤: {e}", file=sys.stderr)
        time.sleep(interval_hours * 3600)


def main():
    ap = argparse.ArgumentParser(description="反指標監控儀表板")
    ap.add_argument("--watch", action="store_true", help="持續輪詢模式")
    ap.add_argument("--interval", type=int, default=4, help="輪詢間隔(小時)")
    ap.add_argument("--telegram", action="store_true", help="觸發時推送 Telegram")
    ap.add_argument("--force-alert", action="store_true", help="強制發送當前警報 (測試用)")
    args = ap.parse_args()

    if args.watch:
        watch(args.interval, args.telegram)
    else:
        check_once(use_telegram=args.telegram, force_alert=args.force_alert)


if __name__ == "__main__":
    main()
