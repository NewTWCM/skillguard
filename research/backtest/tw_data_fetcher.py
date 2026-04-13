"""
台灣市場資料抓取模組
資料來源:
  - TWSE (台灣證券交易所) - 加權指數、融資融券
  - TAIFEX (台灣期貨交易所) - 散戶多空比
  - 個股/ETF 日線
"""

import json
import time
import os
import datetime
import requests
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


def _cache_path(name: str) -> Path:
    return DATA_DIR / f"{name}.csv"


def _rate_limit(seconds=3.0):
    time.sleep(seconds)


# ============================================================
# 1. TWSE 加權指數日線 (含 0050 ETF)
# ============================================================

def fetch_twse_daily(stock_id: str, year: int, month: int) -> list[dict]:
    """從 TWSE 抓取單月日線資料"""
    date_str = f"{year}{month:02d}01"
    url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date_str}&stockNo={stock_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        data = resp.json()
        if data.get("stat") != "OK" or "data" not in data:
            return []
    except Exception as e:
        print(f"  [WARN] fetch {stock_id} {year}/{month}: {e}")
        return []

    rows = []
    for row in data["data"]:
        # 欄位: 日期, 成交股數, 成交金額, 開盤價, 最高價, 最低價, 收盤價, 漲跌價差, 成交筆數
        try:
            # ROC 日期轉換 (e.g., "114/01/02" -> "2025-01-02")
            parts = row[0].strip().split("/")
            ad_year = int(parts[0]) + 1911
            date_str = f"{ad_year}-{parts[1]}-{parts[2]}"

            close = float(row[6].replace(",", ""))
            open_ = float(row[3].replace(",", ""))
            high = float(row[4].replace(",", ""))
            low = float(row[5].replace(",", ""))
            volume = int(row[1].replace(",", ""))

            rows.append({
                "date": date_str,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            })
        except (ValueError, IndexError):
            continue
    return rows


def get_stock_history(stock_id: str, start_year: int = 2021, end_year: int = 2026) -> pd.DataFrame:
    """取得股票/ETF 歷史日線，含快取"""
    cache = _cache_path(f"stock_{stock_id}")
    if cache.exists():
        df = pd.read_csv(cache, parse_dates=["date"])
        # 檢查資料是否需要更新
        if len(df) > 0:
            last = df["date"].max()
            if last >= pd.Timestamp.now() - pd.Timedelta(days=7):
                return df

    print(f"  [INFO] 抓取 {stock_id} 歷史資料 {start_year}-{end_year}...")
    all_rows = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            if year == end_year and month > datetime.datetime.now().month:
                break
            rows = fetch_twse_daily(stock_id, year, month)
            all_rows.extend(rows)
            if rows:
                print(f"    {year}/{month:02d}: {len(rows)} 筆")
            _rate_limit(3.0)

    if not all_rows:
        print(f"  [WARN] {stock_id} 無資料")
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df


# ============================================================
# 2. TWSE 加權指數
# ============================================================

def fetch_taiex_monthly(year: int, month: int) -> list[dict]:
    """從 TWSE 抓取加權指數月資料"""
    date_str = f"{year}{month:02d}01"
    url = f"https://www.twse.com.tw/indicesReport/MI_5MINS_HIST?response=json&date={date_str}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        data = resp.json()
        if data.get("stat") != "OK" or "data" not in data:
            return []
    except Exception as e:
        print(f"  [WARN] TAIEX {year}/{month}: {e}")
        return []

    rows = []
    for row in data["data"]:
        try:
            parts = row[0].strip().split("/")
            ad_year = int(parts[0]) + 1911
            date_str = f"{ad_year}-{parts[1]}-{parts[2]}"
            close = float(row[4].replace(",", ""))
            open_ = float(row[1].replace(",", ""))
            high = float(row[2].replace(",", ""))
            low = float(row[3].replace(",", ""))
            rows.append({
                "date": date_str,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
            })
        except (ValueError, IndexError):
            continue
    return rows


def get_taiex_history(start_year: int = 2021, end_year: int = 2026) -> pd.DataFrame:
    """取得加權指數歷史"""
    cache = _cache_path("taiex_index")
    if cache.exists():
        df = pd.read_csv(cache, parse_dates=["date"])
        if len(df) > 0:
            last = df["date"].max()
            if last >= pd.Timestamp.now() - pd.Timedelta(days=7):
                return df

    print("  [INFO] 抓取加權指數歷史...")
    all_rows = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            if year == end_year and month > datetime.datetime.now().month:
                break
            rows = fetch_taiex_monthly(year, month)
            all_rows.extend(rows)
            if rows:
                print(f"    {year}/{month:02d}: {len(rows)} 筆")
            _rate_limit(3.0)

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df


# ============================================================
# 3. TWSE 融資融券 (信用交易)
# ============================================================

def fetch_margin_monthly(year: int, month: int) -> list[dict]:
    """從 TWSE 抓取融資融券月彙總"""
    date_str = f"{year}{month:02d}01"
    url = f"https://www.twse.com.tw/exchangeReport/MI_MARGN?response=json&date={date_str}&selectType=MS"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        data = resp.json()
        if data.get("stat") != "OK" or "creditList" not in data:
            return []
    except Exception as e:
        print(f"  [WARN] margin {year}/{month}: {e}")
        return []

    rows = []
    for row in data["creditList"]:
        try:
            parts = row[0].strip().split("/")
            ad_year = int(parts[0]) + 1911
            date_str = f"{ad_year}-{parts[1]}-{parts[2]}"

            # 融資餘額(張), 融券餘額(張)
            margin_buy_bal = int(row[6].replace(",", ""))
            short_sell_bal = int(row[12].replace(",", ""))

            rows.append({
                "date": date_str,
                "margin_balance": margin_buy_bal,     # 融資餘額
                "short_balance": short_sell_bal,       # 融券餘額
            })
        except (ValueError, IndexError):
            continue
    return rows


def get_margin_history(start_year: int = 2021, end_year: int = 2026) -> pd.DataFrame:
    """取得融資融券歷史"""
    cache = _cache_path("margin_trading")
    if cache.exists():
        df = pd.read_csv(cache, parse_dates=["date"])
        if len(df) > 0:
            last = df["date"].max()
            if last >= pd.Timestamp.now() - pd.Timedelta(days=7):
                return df

    print("  [INFO] 抓取融資融券歷史...")
    all_rows = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            if year == end_year and month > datetime.datetime.now().month:
                break
            rows = fetch_margin_monthly(year, month)
            all_rows.extend(rows)
            if rows:
                print(f"    {year}/{month:02d}: {len(rows)} 筆")
            _rate_limit(3.0)

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df


# ============================================================
# 4. TAIFEX 三大法人期貨部位 (含散戶多空比推算)
# ============================================================

def fetch_taifex_oi(date_str: str) -> dict | None:
    """
    抓取 TAIFEX 某日三大法人期貨未平倉 (小台指)
    date_str format: "2025/01/02"
    """
    url = "https://www.taifex.com.tw/cht/3/futContractsDateDown"
    params = {
        "queryType": 1,
        "commodity_id": "MTX",  # 小型台指
        "queryDate": date_str,
    }
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        # TAIFEX 回傳 CSV
        lines = resp.text.strip().split("\n")
        if len(lines) < 3:
            return None

        # 解析法人多空部位
        # 格式依欄位不同，嘗試解析
        total_long = 0
        total_short = 0
        inst_long = 0
        inst_short = 0

        for line in lines[1:]:  # skip header
            cols = line.split(",")
            if len(cols) < 12:
                continue
            # 嘗試找到小台指的資料列
            if "小型臺指" in cols[0] or "MTX" in cols[0]:
                try:
                    # 多方未平倉, 空方未平倉
                    inst_long += int(cols[3].replace(",", "").strip())
                    inst_short += int(cols[5].replace(",", "").strip())
                except (ValueError, IndexError):
                    pass

        return {
            "institutional_long": inst_long,
            "institutional_short": inst_short,
        }
    except Exception as e:
        return None


def fetch_taifex_retail_ratio_page(date_str: str) -> dict | None:
    """
    從 TAIFEX 大額交易人未沖銷部位結構取得資料
    用於推算散戶多空比
    date_str: "2025/01/02"
    """
    url = "https://www.taifex.com.tw/cht/3/largeTraderFutDown"
    params = {
        "queryDate": date_str,
        "commodity_id": "TXF",  # 台指期
    }
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if resp.status_code != 200:
            return None
        return {"raw": resp.text[:500]}
    except Exception:
        return None


# ============================================================
# 5. 簡易散戶多空比計算 (用三大法人買賣超推算)
# ============================================================

def fetch_institutional_daily(year: int, month: int) -> list[dict]:
    """
    TWSE 三大法人買賣超日報
    用於推算散戶淨買賣方向
    """
    date_str = f"{year}{month:02d}01"
    url = f"https://www.twse.com.tw/fund/BFI82U?response=json&dayDate={date_str}&type=day"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        data = resp.json()
        if data.get("stat") != "OK" or "data" not in data:
            return []
    except Exception as e:
        print(f"  [WARN] institutional {year}/{month}: {e}")
        return []

    rows = []
    for row in data["data"]:
        try:
            # 欄位: 日期, 外資買, 外資賣, 外資淨, 投信買, 投信賣, 投信淨, 自營買, 自營賣, 自營淨, 合計淨
            parts = row[0].strip().split("/")
            ad_year = int(parts[0]) + 1911
            date = f"{ad_year}-{parts[1]}-{parts[2]}"

            # 三大法人合計買賣超 (億元)
            net_total = float(row[len(row)-1].replace(",", ""))

            rows.append({
                "date": date,
                "institutional_net": net_total,  # 正=法人買超, 負=法人賣超
                # 散戶方向 = 法人的反面
                "retail_direction": -1 if net_total > 0 else 1,
            })
        except (ValueError, IndexError):
            continue
    return rows


def get_institutional_history(start_year: int = 2021, end_year: int = 2026) -> pd.DataFrame:
    """取得三大法人買賣超歷史"""
    cache = _cache_path("institutional_flow")
    if cache.exists():
        df = pd.read_csv(cache, parse_dates=["date"])
        if len(df) > 0:
            last = df["date"].max()
            if last >= pd.Timestamp.now() - pd.Timedelta(days=7):
                return df

    print("  [INFO] 抓取三大法人買賣超歷史...")
    all_rows = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            if year == end_year and month > datetime.datetime.now().month:
                break
            rows = fetch_institutional_daily(year, month)
            all_rows.extend(rows)
            if rows:
                print(f"    {year}/{month:02d}: {len(rows)} 筆")
            _rate_limit(3.0)

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df


if __name__ == "__main__":
    print("=" * 60)
    print("台灣市場資料抓取測試")
    print("=" * 60)

    # 測試抓取 0050 最近一個月
    print("\n--- 0050 ETF ---")
    now = datetime.datetime.now()
    rows = fetch_twse_daily("0050", now.year, now.month)
    print(f"本月資料: {len(rows)} 筆")
    if rows:
        print(f"最新: {rows[-1]}")

    # 測試加權指數
    print("\n--- 加權指數 ---")
    rows = fetch_taiex_monthly(now.year, now.month)
    print(f"本月資料: {len(rows)} 筆")
    if rows:
        print(f"最新: {rows[-1]}")
