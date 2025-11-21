from collections import defaultdict
from datetime import date
from transactions.models import SummaryTransaction, Transaction
from transactions.utils import (
    format_daily_key,
    format_weekly_key,
    format_monthly_key,
)


class SummaryService:
    """
    Handles:
    - Reading pre-aggregated summary data for the API
    - Rebuilding summaries from Transaction collection (used by command)
    """

    GRANULARITY_MAP = {
        "daily": SummaryTransaction.Granularity.DAILY,
        "weekly": SummaryTransaction.Granularity.WEEKLY,
        "monthly": SummaryTransaction.Granularity.MONTHLY,
    }

    @staticmethod
    def get_summary(mode: str, value_type: str, merchant_id: str | None):
        """
        Pure function — perfect for testing.
        Reads ONLY from SummaryTransaction.
        """
        granularity = SummaryService.GRANULARITY_MAP[mode]

        qs = SummaryTransaction.objects.filter(granularity=granularity)
        if merchant_id:
            qs = qs.filter(merchant_id=merchant_id)

        qs = qs.order_by("date")

        results = []
        field = "total_amount" if value_type == "amount" else "total_count"

        for s in qs.only("date", "month", "week", field):
            if mode == "daily":
                key = format_daily_key(s.date)
            elif mode == "weekly":
                key = format_weekly_key(s.date, s.week)
            else:
                key = format_monthly_key(s.date)

            results.append({
                "key": key,
                "value": int(getattr(s, field, 0) or 0)
            })

        return results

    @staticmethod
    def rebuild_all_summaries():
        """
        Pure business logic for your management command.
        Read all transactions → compute → return SummaryTransaction objects.
        """
        summary = defaultdict(lambda: {"amount": 0, "count": 0})

        qs = Transaction.objects.all().only("created_at", "amount", "merchant_id")

        for tx in qs.iterator():
            if not tx.created_at:
                continue

            dt = tx.created_at.date()
            merchant = str(tx.merchant_id) if tx.merchant_id else None
            amount = int(tx.amount or 0)

            # DAILY
            key_daily = ("daily", merchant, dt.year, dt.month, None, dt)
            summary[key_daily]["amount"] += amount
            summary[key_daily]["count"] += 1

            # WEEKLY
            iso_year, iso_week, _ = dt.isocalendar()
            ref_week_date = date.fromisocalendar(iso_year, iso_week, 1)
            key_weekly = ("weekly", merchant, iso_year, None, iso_week, ref_week_date)
            summary[key_weekly]["amount"] += amount
            summary[key_weekly]["count"] += 1

            # MONTHLY
            month_start = date(dt.year, dt.month, 1)
            key_monthly = ("monthly", merchant, dt.year, dt.month, None, month_start)
            summary[key_monthly]["amount"] += amount
            summary[key_monthly]["count"] += 1

        results = []
        for (granularity, merchant_id, year, month, week, ref_date), vals in summary.items():
            results.append(
                SummaryTransaction(
                    granularity=granularity,
                    merchant_id=merchant_id,
                    date=ref_date,
                    year=year,
                    month=month,
                    week=week,
                    total_amount=vals["amount"],
                    total_count=vals["count"]
                )
            )
        return results
