from pathlib import Path
from datetime import datetime
import re

import pandas as pd


OUTPUT_DIR = Path("output")


def norm_text(x):
    if x is None or pd.isna(x):
        return ""
    return re.sub(r"\s+", "", str(x).strip())


def to_int(x):
    if x is None or pd.isna(x):
        return None
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return int(x)
    s = str(x).strip().replace(",", "").replace(" ", "")
    if not s or s in {"-", "—", "–", "nan", "None"}:
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    try:
        v = int(float(s))
        return -v if neg else v
    except Exception:
        return None


def contains_any_norm(text, keywords):
    t = norm_text(text)
    return any(norm_text(k) in t for k in keywords)


def find_match(g, *, sj_divs=None, id_equals=None, id_contains=None, name_exact=None, name_contains=None):
    sj_divs = set(sj_divs or [])
    id_equals = set(id_equals or [])
    id_contains = tuple(id_contains or [])
    name_exact_norm = {norm_text(x) for x in (name_exact or [])}
    name_contains = tuple(name_contains or [])

    rows = g.copy()
    if sj_divs:
        rows = rows[rows["sj_div"].astype(str).isin(sj_divs)]

    # 1. account_id exact
    if id_equals:
        for _, r in rows.iterrows():
            aid = str(r.get("account_id") or "")
            if aid in id_equals:
                return r

    # 2. account_id contains
    if id_contains:
        for _, r in rows.iterrows():
            aid = str(r.get("account_id") or "")
            if any(frag in aid for frag in id_contains):
                return r

    # 3. account_nm exact after whitespace removal
    if name_exact_norm:
        for _, r in rows.iterrows():
            anm = norm_text(r.get("account_nm"))
            if anm in name_exact_norm:
                return r

    # 4. account_nm contains after whitespace removal
    if name_contains:
        for _, r in rows.iterrows():
            anm = r.get("account_nm")
            if contains_any_norm(anm, name_contains):
                return r

    return None


def amount_from_row(row):
    if row is None:
        return None
    return to_int(row.get("thstrm_amount"))


def row_meta(row):
    if row is None:
        return {
            "matched": False,
            "sj_div": "",
            "account_id": "",
            "account_nm": "",
            "amount": None,
        }
    return {
        "matched": True,
        "sj_div": row.get("sj_div", ""),
        "account_id": row.get("account_id", ""),
        "account_nm": row.get("account_nm", ""),
        "amount": amount_from_row(row),
    }


SPECS = {
    "revenue": {
        "sj_divs": ["IS", "CIS"],
        "id_contains": ["Revenue"],
        "name_contains": ["매출액", "수익(매출액)", "영업수익"],
    },
    "operating_profit": {
        "sj_divs": ["IS", "CIS"],
        "id_contains": ["OperatingIncomeLoss"],
        "name_contains": ["영업이익", "영업이익(손실)"],
    },
    "net_income_parent": {
        "sj_divs": ["IS", "CIS"],
        "id_contains": ["ProfitLossAttributableToOwnersOfParent"],
        "name_contains": ["지배기업소유주지분", "지배주주지분순이익"],
    },
    "net_income_total": {
        "sj_divs": ["IS", "CIS"],
        "id_equals": ["ifrs-full_ProfitLoss"],
        "name_contains": ["당기순이익", "당기순이익(손실)", "분기순이익", "반기순이익"],
    },
    "total_assets": {
        "sj_divs": ["BS"],
        "id_equals": ["ifrs-full_Assets"],
        "name_exact": ["자산총계"],
    },
    "total_liabilities": {
        "sj_divs": ["BS"],
        "id_equals": ["ifrs-full_Liabilities"],
        "name_exact": ["부채총계"],
    },
    "total_equity": {
        "sj_divs": ["BS"],
        "id_equals": ["ifrs-full_Equity"],
        "name_exact": ["자본총계"],
    },
    "cash_and_equivalents": {
        "sj_divs": ["BS"],
        "id_equals": [
            "ifrs-full_CashAndCashEquivalents",
            "dart_CashAndDuefromBanks",
        ],
        "name_contains": [
            "현금및현금성자산",
            "현금 및 현금성자산",
            "현금 및 예치금",
            "현금 및 상각후원가측정예치금",
        ],
    },
    "cfo": {
        "sj_divs": ["CF"],
        "id_contains": ["CashFlowsFromUsedInOperatingActivities"],
        "name_contains": ["영업활동현금흐름", "영업활동으로인한현금흐름", "영업활동으로부터의현금흐름"],
    },
    "cfi": {
        "sj_divs": ["CF"],
        "id_contains": ["CashFlowsFromUsedInInvestingActivities"],
        "name_contains": ["투자활동현금흐름", "투자활동으로인한현금흐름", "투자활동으로부터의현금흐름"],
    },
    "cff": {
        "sj_divs": ["CF"],
        "id_contains": ["CashFlowsFromUsedInFinancingActivities"],
        "name_contains": ["재무활동현금흐름", "재무활동으로인한현금흐름", "재무활동으로부터의현금흐름"],
    },
    "capex": {
        "sj_divs": ["CF"],
        "name_contains": ["유형자산의취득", "유형자산취득", "유형자산의 취득"],
    },
    "dividends_paid": {
        "sj_divs": ["CF"],
        "id_contains": [
            "DividendsPaidClassifiedAsFinancingActivities",
        ],
        "name_contains": [
            "배당금의지급",
            "배당금지급",
            "배당금 지급",
            "현금배당",
        ],
    },
    "fx_effect": {
        "sj_divs": ["CF"],
        "id_equals": [
            "ifrs-full_EffectOfExchangeRateChangesOnCashAndCashEquivalents",
        ],
        "name_contains": [
            "환율변동효과",
            "환율 변동 효과",
            "환율변동으로 인한 현금흐름",
            "외화환산으로 인한 현금의 변동",
            "외화표시 현금 및 현금성자산에 대한 환율변동효과",
            "외화표시 현금및현금성자산에 대한 환율변동효과",
        ],
    },
}


def build_summary(raw):
    group_cols = ["company_input", "resolved_corp_name", "stock_code", "corp_code"]
    summaries = []
    match_logs = []

    for keys, g in raw.groupby(group_cols, dropna=False):
        company_input, resolved_name, stock_code, corp_code = keys

        matched = {}
        for key, spec in SPECS.items():
            r = find_match(g, **spec)
            meta = row_meta(r)
            matched[key] = meta["amount"]

            match_logs.append({
                "company_input": company_input,
                "resolved_corp_name": resolved_name,
                "stock_code": stock_code,
                "corp_code": corp_code,
                "metric": key,
                **meta,
            })

        net_income = matched.get("net_income_parent")
        if net_income is None:
            net_income = matched.get("net_income_total")

        capex_raw = matched.get("capex")
        capex_cash_out = abs(capex_raw) if capex_raw is not None else None

        dividends_raw = matched.get("dividends_paid")
        dividend_cash_out = abs(dividends_raw) if dividends_raw is not None else None

        cfo = matched.get("cfo")

        fcf_before_div = None
        if cfo is not None or capex_cash_out is not None:
            fcf_before_div = (cfo or 0) - (capex_cash_out or 0)

        fcf_after_div = None
        if fcf_before_div is not None or dividend_cash_out is not None:
            fcf_after_div = (fcf_before_div or 0) - (dividend_cash_out or 0)

        payout_ratio_pct = None
        if dividend_cash_out is not None and net_income is not None and net_income > 0:
            payout_ratio_pct = round(dividend_cash_out / net_income * 100, 2)

        summary = {
            "company_input": company_input,
            "resolved_corp_name": resolved_name,
            "stock_code": stock_code,
            "corp_code": corp_code,

            "revenue_krw": matched.get("revenue"),
            "operating_profit_krw": matched.get("operating_profit"),
            "net_income_krw": net_income,

            "total_assets_krw": matched.get("total_assets"),
            "total_liabilities_krw": matched.get("total_liabilities"),
            "total_equity_krw": matched.get("total_equity"),
            "cash_and_equivalents_krw": matched.get("cash_and_equivalents"),

            "cfo_krw": matched.get("cfo"),
            "cfi_krw": matched.get("cfi"),
            "cff_krw": matched.get("cff"),
            "fx_effect_krw": matched.get("fx_effect"),

            "capex_raw_krw": capex_raw,
            "capex_cash_out_krw": capex_cash_out,
            "dividends_paid_raw_krw": dividends_raw,
            "dividend_cash_out_krw": dividend_cash_out,

            "fcf_before_div_krw": fcf_before_div,
            "fcf_after_div_krw": fcf_after_div,
            "payout_ratio_pct": payout_ratio_pct,
        }
        summaries.append(summary)

    summary_df = pd.DataFrame(summaries)
    match_log_df = pd.DataFrame(match_logs)

    def metric_matched(company, metric):
        sub = match_log_df[
            (match_log_df["company_input"] == company)
            & (match_log_df["metric"] == metric)
        ]
        if sub.empty:
            return False
        return bool(sub["matched"].iloc[0])

    def make_quality_flags(row):
        flags = []
        company = row.get("company_input")
        company_text = f"{row.get('company_input', '')} {row.get('resolved_corp_name', '')}"

        financial_keywords = (
            "금융",
            "은행",
            "보험",
            "증권",
            "생명",
            "해상",
            "손해보험",
            "화재",
            "카드",
            "캐피탈",
            "신한지주",
            "하나금융",
            "우리금융",
            "KB금융",
            "메리츠금융",
            "기업은행",
            "카카오뱅크",
        )
        if any(k in company_text for k in financial_keywords):
            flags.append("CHECK_FINANCIAL_INDUSTRY")

        if pd.isna(row.get("revenue_krw")):
            flags.append("MISSING_REVENUE")

        if pd.isna(row.get("operating_profit_krw")):
            flags.append("MISSING_OPERATING_PROFIT")

        if (
            not metric_matched(company, "net_income_parent")
            and metric_matched(company, "net_income_total")
        ):
            flags.append("USED_TOTAL_NET_INCOME")

        if pd.isna(row.get("net_income_krw")):
            flags.append("MISSING_NET_INCOME")

        if pd.isna(row.get("cash_and_equivalents_krw")):
            flags.append("MISSING_CASH")

        if pd.isna(row.get("cfo_krw")):
            flags.append("MISSING_CFO")

        if pd.isna(row.get("cfi_krw")):
            flags.append("MISSING_CFI")

        if pd.isna(row.get("cff_krw")):
            flags.append("MISSING_CFF")

        if pd.isna(row.get("capex_cash_out_krw")):
            flags.append("MISSING_CAPEX")

        if pd.isna(row.get("dividend_cash_out_krw")):
            flags.append("DIVIDEND_NOT_FOUND")

        fcf = row.get("fcf_before_div_krw")
        if pd.notna(fcf) and fcf < 0:
            flags.append("NEGATIVE_FCF_BEFORE_DIV")

        payout = row.get("payout_ratio_pct")
        if pd.notna(payout) and payout >= 80:
            flags.append("HIGH_PAYOUT_RATIO")

        return "|".join(flags) if flags else "OK"

    summary_df["quality_flags"] = summary_df.apply(make_quality_flags, axis=1)
    summary_df["needs_review"] = summary_df["quality_flags"] != "OK"

    front_cols = [
        "company_input",
        "resolved_corp_name",
        "stock_code",
        "corp_code",
        "quality_flags",
        "needs_review",
    ]
    rest_cols = [c for c in summary_df.columns if c not in front_cols]
    summary_df = summary_df[front_cols + rest_cols]

    return summary_df, match_log_df


def main():
    raw_files = sorted(OUTPUT_DIR.glob("financial_raw_batch_*.xlsx"))
    if not raw_files:
        raise FileNotFoundError("output/financial_raw_batch_*.xlsx 파일이 없습니다.")

    latest = raw_files[-1]
    print(f"input: {latest}")

    raw = pd.read_excel(
        latest,
        sheet_name="raw_fnlttSinglAcntAll",
        dtype={
            "stock_code": "string",
            "corp_code": "string",
            "company_input": "string",
            "resolved_corp_name": "string",
        },
    )

    raw["stock_code"] = (
        raw["stock_code"]
        .fillna("")
        .astype(str)
        .str.replace(r"\\.0$", "", regex=True)
        .str.zfill(6)
    )

    raw["corp_code"] = (
        raw["corp_code"]
        .fillna("")
        .astype(str)
        .str.replace(r"\\.0$", "", regex=True)
        .str.zfill(8)
    )
    summary, match_log = build_summary(raw)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUTPUT_DIR / f"financial_summary_{ts}.xlsx"

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="summary", index=False)
        match_log.to_excel(writer, sheet_name="match_log", index=False)
        raw.to_excel(writer, sheet_name="raw", index=False)

    print(f"saved: {out}")
    print(summary)


if __name__ == "__main__":
    main()
