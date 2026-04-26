"""
從 SurveyCake API 抓取板橋案預約資料，輸出為 data.json
用法：
  python fetch_data.py --api-key YOUR_KEY
  或設定環境變數 SURVEYCAKE_API_KEY
"""

import os
import json
import argparse
import requests
from datetime import datetime

FORM_HASH = "Rl3oz"
API_BASE = f"https://api.surveycake.com/v0/form/{FORM_HASH}/submit"

FIELD_MAP = {
    "貴賓姓名": "name",
    "請問您的年齡:": "age",
    "請問您居住的縣市": "city",
    "台北市哪一區?": "taipei_district",
    "新北市哪一區?": "newtaipei_district",
    "請問您的職業": "occupation",
    "聯繫電話": "phone",
    "LINE ID": "line_id",
    "預約賞屋建案": "project",
    "想要看的房型": "housing_type",
    "購屋的預算範圍": "budget",
    "是否為首次購屋": "first_buyer",
    "本次購屋的用途": "purpose",
}


def fetch_all(api_key: str) -> list[dict]:
    headers = {"X-API-KEY": api_key}
    records = []
    page = 1

    while True:
        resp = requests.get(API_BASE, headers=headers, params={"page": page}, timeout=30)
        resp.raise_for_status()
        body = resp.json()

        # SurveyCake returns: {"code":0,"result":{"data":[...],"total":N,"page":P,"per_page":100}}
        result = body.get("result", body)
        rows = result.get("data", result) if isinstance(result, dict) else result

        if not rows:
            break

        for row in rows:
            record = {"date": row.get("created_at", "")}
            answers = row.get("answers", [])
            for ans in answers:
                subject = ans.get("subject", "").strip()
                key = FIELD_MAP.get(subject)
                if key:
                    val = ans.get("answer", [])
                    record[key] = ", ".join(val) if isinstance(val, list) else str(val)
            records.append(record)

        # Check if there's another page
        if isinstance(result, dict):
            total = result.get("total", 0)
            per_page = result.get("per_page", 100)
            if page * per_page >= total:
                break
        else:
            break
        page += 1

    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", default=os.environ.get("SURVEYCAKE_API_KEY", ""))
    parser.add_argument("--out", default="data.json")
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("錯誤：請提供 --api-key 或設定 SURVEYCAKE_API_KEY 環境變數")

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 開始抓取...")
    records = fetch_all(args.api_key)
    print(f"共取得 {len(records)} 筆")

    out_path = os.path.join(os.path.dirname(__file__), args.out)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"已寫入 {out_path}")


if __name__ == "__main__":
    main()
