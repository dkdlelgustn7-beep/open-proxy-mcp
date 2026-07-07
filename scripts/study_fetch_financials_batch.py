import asyncio
import os
from datetime import datetime

import pandas as pd

from open_proxy_mcp.dart.client import get_dart_client, DartClientError


TARGETS = [
    "삼성전자",
    "SK하이닉스",
    "현대차",
    "기아",
    "LG전자",
]

BSNS_YEAR = "2024"
REPRT_CODE = "11011"   # 사업보고서
FS_DIV = "CFS"         # 연결


async def fetch_one(client, company):
    try:
        corp = await client.lookup_corp_code(company)
        if not corp:
            return [], {
                "company_input": company,
                "status": "corp_not_found",
                "message": "기업코드 조회 실패",
            }

        data = await client.get_fnltt_singl_acnt_all(
            corp_code=corp["corp_code"],
            bsns_year=BSNS_YEAR,
            reprt_code=REPRT_CODE,
            fs_div=FS_DIV,
        )

        rows = data.get("list", []) or []

        for row in rows:
            row["company_input"] = company
            row["resolved_corp_name"] = corp.get("corp_name")
            row["stock_code"] = corp.get("stock_code")

        return rows, {
            "company_input": company,
            "resolved_corp_name": corp.get("corp_name"),
            "stock_code": corp.get("stock_code"),
            "corp_code": corp.get("corp_code"),
            "status": "ok",
            "row_count": len(rows),
            "message": "",
        }

    except DartClientError as e:
        return [], {
            "company_input": company,
            "status": f"dart_error_{e.status}",
            "message": str(e),
        }

    except Exception as e:
        return [], {
            "company_input": company,
            "status": "error",
            "message": repr(e),
        }


async def main():
    if not os.getenv("OPENDART_API_KEY"):
        raise RuntimeError("OPENDART_API_KEY 환경변수가 없습니다.")

    os.makedirs("output", exist_ok=True)

    client = get_dart_client()

    all_rows = []
    logs = []

    for company in TARGETS:
        print(f"fetching: {company}")
        rows, log = await fetch_one(client, company)
        all_rows.extend(rows)
        logs.append(log)
        print(log)

    raw_df = pd.DataFrame(all_rows)
    log_df = pd.DataFrame(logs)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_xlsx = f"output/financial_raw_batch_{BSNS_YEAR}_{REPRT_CODE}_{ts}.xlsx"

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        raw_df.to_excel(writer, sheet_name="raw_fnlttSinglAcntAll", index=False)
        log_df.to_excel(writer, sheet_name="fetch_log", index=False)

    print(f"saved: {out_xlsx}")
    print(f"raw rows: {len(raw_df)}")
    print(f"companies: {len(log_df)}")


if __name__ == "__main__":
    asyncio.run(main())
