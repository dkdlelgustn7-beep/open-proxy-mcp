import asyncio
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from open_proxy_mcp.dart.client import get_dart_client, DartClientError


INPUT_FILE = Path("input/targets_panel_sample.csv")


async def fetch_one(client, row):
    company = str(row["company"]).strip()
    bsns_year = str(row["bsns_year"]).strip()
    reprt_code = str(row["reprt_code"]).strip()
    fs_div = str(row["fs_div"]).strip()

    try:
        corp = await client.lookup_corp_code(company)
        if not corp:
            return [], {
                "company_input": company,
                "bsns_year_input": bsns_year,
                "reprt_code_input": reprt_code,
                "fs_div_input": fs_div,
                "status": "corp_not_found",
                "message": "기업코드 조회 실패",
            }

        data = await client.get_fnltt_singl_acnt_all(
            corp_code=corp["corp_code"],
            bsns_year=bsns_year,
            reprt_code=reprt_code,
            fs_div=fs_div,
        )

        rows = data.get("list", []) or []

        for item in rows:
            item["company_input"] = company
            item["resolved_corp_name"] = corp.get("corp_name")
            item["stock_code"] = corp.get("stock_code")
            item["corp_code"] = corp.get("corp_code")
            item["bsns_year_input"] = bsns_year
            item["reprt_code_input"] = reprt_code
            item["fs_div_input"] = fs_div

        return rows, {
            "company_input": company,
            "resolved_corp_name": corp.get("corp_name"),
            "stock_code": corp.get("stock_code"),
            "corp_code": corp.get("corp_code"),
            "bsns_year_input": bsns_year,
            "reprt_code_input": reprt_code,
            "fs_div_input": fs_div,
            "status": "ok",
            "row_count": len(rows),
            "message": "",
        }

    except DartClientError as e:
        return [], {
            "company_input": company,
            "bsns_year_input": bsns_year,
            "reprt_code_input": reprt_code,
            "fs_div_input": fs_div,
            "status": f"dart_error_{e.status}",
            "message": str(e),
        }

    except Exception as e:
        return [], {
            "company_input": company,
            "bsns_year_input": bsns_year,
            "reprt_code_input": reprt_code,
            "fs_div_input": fs_div,
            "status": "error",
            "message": repr(e),
        }


async def main():
    if not os.getenv("OPENDART_API_KEY"):
        raise RuntimeError("OPENDART_API_KEY 환경변수가 없습니다.")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"{INPUT_FILE} 파일이 없습니다.")

    os.makedirs("output", exist_ok=True)

    targets_df = pd.read_csv(INPUT_FILE, dtype=str)
    required = ["company", "bsns_year", "reprt_code", "fs_div"]

    missing = [c for c in required if c not in targets_df.columns]
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")

    targets_df = targets_df[required].dropna()
    targets_df = targets_df[
        targets_df["company"].astype(str).str.strip() != ""
    ].reset_index(drop=True)

    print(f"targets: {len(targets_df)}")

    client = get_dart_client()

    all_rows = []
    logs = []

    for i, row in targets_df.iterrows():
        print(
            f"[{i + 1}/{len(targets_df)}] "
            f"{row['company']} {row['bsns_year']} {row['reprt_code']} {row['fs_div']}"
        )
        rows, log = await fetch_one(client, row)
        all_rows.extend(rows)
        logs.append(log)
        print(log)

    raw_df = pd.DataFrame(all_rows)
    log_df = pd.DataFrame(logs)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_xlsx = f"output/financial_raw_panel_{ts}.xlsx"

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        raw_df.to_excel(writer, sheet_name="raw_fnlttSinglAcntAll", index=False)
        log_df.to_excel(writer, sheet_name="fetch_log", index=False)
        targets_df.to_excel(writer, sheet_name="targets", index=False)

    print(f"saved: {out_xlsx}")
    print(f"raw rows: {len(raw_df)}")
    print(f"targets: {len(log_df)}")


if __name__ == "__main__":
    asyncio.run(main())
