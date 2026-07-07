import asyncio
import os
import pandas as pd

from open_proxy_mcp.dart.client import get_dart_client


async def main():
    if not os.getenv("OPENDART_API_KEY"):
        raise RuntimeError("OPENDART_API_KEY 환경변수가 없습니다.")

    client = get_dart_client()

    corp = await client.lookup_corp_code("삼성전자")
    print("corp:", corp)

    data = await client.get_fnltt_singl_acnt_all(
        corp_code=corp["corp_code"],
        bsns_year="2024",
        reprt_code="11011",
        fs_div="CFS",
    )

    rows = data.get("list", [])
    print("rows:", len(rows))

    df = pd.DataFrame(rows)
    print(df.head())

    out = "samsung_2024_fnlttSinglAcntAll.xlsx"
    df.to_excel(out, index=False)
    print("saved:", out)


if __name__ == "__main__":
    asyncio.run(main())
