from datetime import datetime, timedelta
from pprint import pprint

import pandas as pd

from src.iiko_sdk import IikoSDK

pd.options.display.width = 1000
pd.options.display.max_columns = 100


ISO_MS = "%Y-%m-%dT%H:%M:%S.%f"


def parse_dt(s: str) -> datetime:
    return datetime.strptime(s, ISO_MS)


def fmt_dt_ms(dt: datetime) -> str:
    # "2026-01-01T00:00:00.000"
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000")


def fmt_dt_no_ms(dt: datetime) -> str:
    # если твой SDK ожидает без .000 в dateFrom/dateTo
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def next_monday_00(dt: datetime) -> datetime:
    dt0 = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    monday_this = dt0 - timedelta(
        days=dt0.weekday()
    )  # понедельник текущей недели 00:00
    monday_next = monday_this + timedelta(days=7)
    return monday_next if dt0 >= monday_this else monday_this


def add_summary_arrays(a, b):
    """
    Складывает два массива summary/totals поэлементно (числа суммируем, None пропускаем).
    """
    if a is None:
        return b
    if b is None:
        return a

    n = max(len(a), len(b))
    out = [None] * n
    for i in range(n):
        av = a[i] if i < len(a) else None
        bv = b[i] if i < len(b) else None

        if av is None:
            out[i] = bv
        elif bv is None:
            out[i] = av
        elif isinstance(av, (int, float)) and isinstance(bv, (int, float)):
            out[i] = av + bv
        else:
            # если вдруг прилетело не число (строка и т.п.) — оставляем av
            out[i] = av
    return out


def main():
    overall_from = "2026-01-01T00:00:00.000"
    overall_to = "2026-02-02T00:00:00.000"

    aggs = [
        "DiscountSum",
        "DishDiscountSumInt",
        "discountWithoutVAT",
        "DishDiscountSumInt.withoutVAT",
        "sumAfterDiscountWithoutVAT",
        "IncreaseSum",
        "GuestNum",
        "Bonus.Sum",
    ]

    group_by = ["OpenDate.Typed", "Department", "WaiterName", "PayTypes"]

    dt_from = parse_dt(overall_from)
    dt_to = parse_dt(overall_to)

    merged_raw = {
        "data": [],
        # будем пытаться суммировать "summary" или "totals" (что вернёт API)
        "summary": None,
        "totals": None,
        # полезно хранить чанки (можешь удалить, если не нужно)
        "chunks": [],
        # чтобы потребитель знал, какая схема данных
        "schema": {
            "groupByRowFields": group_by,
            "aggregateFields": aggs,
            "columns": group_by + aggs,
        },
    }

    cur = dt_from

    with IikoSDK() as sdk:
        while cur < dt_to:
            week_end = min(next_monday_00(cur), dt_to)

            report = sdk.olap.build_report_v2(
                report_type="SALES",
                date_from=fmt_dt_no_ms(cur),
                date_to=fmt_dt_no_ms(week_end),
                summary=True,
                group_by_row_fields=group_by,
                aggregate_fields=aggs,
                filters={
                    "OpenDate.Typed": {
                        "filterType": "DateRange",
                        "periodType": "CUSTOM",
                        "includeLow": True,
                        "includeHigh": False,  # [from, to)
                        "from": fmt_dt_ms(cur),
                        "to": fmt_dt_ms(week_end),
                    }
                },
            )

            raw = report.raw or {}

            # 1) Склеиваем data
            merged_raw["data"].extend(raw.get("data", []))

            # 2) Склеиваем summary/totals если они есть
            #    (у iiko иногда ключ "summary", иногда "totals")
            if "summary" in raw:
                merged_raw["summary"] = add_summary_arrays(
                    merged_raw["summary"], raw.get("summary")
                )
            if "totals" in raw:
                merged_raw["totals"] = add_summary_arrays(
                    merged_raw["totals"], raw.get("totals")
                )

            # 3) Сохраняем чанк как есть (для контроля)
            merged_raw["chunks"].append(
                {
                    "from": fmt_dt_ms(cur),
                    "to": fmt_dt_ms(week_end),
                    "raw": raw,
                    "rows": len(raw.get("data", [])),
                }
            )

            print(
                f"Chunk: {fmt_dt_ms(cur)} -> {fmt_dt_ms(week_end)} | rows: {len(raw.get('data', []))}"
            )

            cur = week_end

    pprint(
        {
            "columns": merged_raw["schema"]["columns"],
            "row_count": len(merged_raw["data"]),
            "has_summary": merged_raw["summary"] is not None,
            "has_totals": merged_raw["totals"] is not None,
            "chunks": len(merged_raw["chunks"]),
        }
    )

    # итоговый "склеенный raw"
    report_data = pd.DataFrame(merged_raw.get("data"))
    print(report_data)


if __name__ == "__main__":
    main()
