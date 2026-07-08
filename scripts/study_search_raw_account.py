import argparse
from pathlib import Path

import pandas as pd


def latest_raw_file():
    files = sorted(Path("output").glob("financial_raw_batch_*.xlsx"))
    if not files:
        raise FileNotFoundError("output/financial_raw_batch_*.xlsx 파일이 없습니다.")
    return files[-1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", default="", help="회사명 일부. 예: 삼성전자, SK이노베이션")
    parser.add_argument("--keyword", required=True, help="검색어. 예: 재무활동, 차입금, 사채, 배당")
    parser.add_argument("--sj", default="", help="재무제표 구분. 예: BS, IS, CIS, CF, SCE")
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()

    raw_file = latest_raw_file()
    raw = pd.read_excel(raw_file, sheet_name="raw_fnlttSinglAcntAll", dtype=str)

    for col in ["company_input", "resolved_corp_name", "account_nm", "account_id", "sj_div"]:
        if col not in raw.columns:
            raw[col] = ""

    mask = (
        raw["account_nm"].fillna("").str.contains(args.keyword, case=False, regex=False)
        | raw["account_id"].fillna("").str.contains(args.keyword, case=False, regex=False)
    )

    if args.company:
        company_mask = (
            raw["company_input"].fillna("").str.contains(args.company, case=False, regex=False)
            | raw["resolved_corp_name"].fillna("").str.contains(args.company, case=False, regex=False)
        )
        mask = mask & company_mask

    if args.sj:
        mask = mask & (raw["sj_div"].fillna("") == args.sj)

    result = raw.loc[mask].copy()

    cols = [
        "company_input",
        "resolved_corp_name",
        "stock_code",
        "corp_code",
        "sj_div",
        "account_id",
        "account_nm",
        "thstrm_nm",
        "thstrm_amount",
        "frmtrm_nm",
        "frmtrm_amount",
        "ord",
    ]
    cols = [c for c in cols if c in result.columns]

    print(f"input: {raw_file}")
    print(f"matched rows: {len(result)}")

    if result.empty:
        return

    show = result[cols].head(args.limit)
    print(show.to_string(index=False))

    out_dir = Path("output")
    safe_company = args.company.replace("/", "_").replace("\\", "_") or "all"
    safe_keyword = args.keyword.replace("/", "_").replace("\\", "_")
    out = out_dir / f"raw_search_{safe_company}_{safe_keyword}.xlsx"
    result[cols].to_excel(out, index=False)
    print(f"\nsaved: {out}")


if __name__ == "__main__":
    main()
