from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

from transactions.models import SummaryTransaction
from transactions.serializers import SummaryPointSerializer
from transactions.utils import (
    format_daily_key,
    format_weekly_key,
    format_monthly_key,
)


class TransactionSummaryView(APIView):
    """
    GET /api/transactions/summary/?mode=daily&type=amount&merchant_id=...

    Query params:
      - mode: 'daily' | 'weekly' | 'monthly'  (required)
      - type: 'amount' | 'count'             (required)
      - merchant_id: optional (if omitted → all merchants)

    Response: [{ "key": <label string>, "value": <number> }, ...]
    """

    def get(self, request, *args, **kwargs):
        mode = request.query_params.get("mode")
        value_type = request.query_params.get("type")
        merchant_id = request.query_params.get("merchant_id")

        if mode not in {"daily", "weekly", "monthly"}:
            raise ValidationError({"mode": "mode must be one of: daily, weekly, monthly"})

        if value_type not in {"amount", "count"}:
            raise ValidationError({"type": "type must be one of: amount, count"})

        data = self._from_summary_transaction(mode=mode, value_type=value_type, merchant_id=merchant_id)

        serializer = SummaryPointSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _from_summary_transaction(self, mode: str, value_type: str, merchant_id: str | None) -> list[dict]:
        """
        Read EVERYTHING from SummaryTransaction:
        - filter by granularity
        - filter by merchant_id if provided, otherwise use aggregated 'all merchants' rows
        - use total_amount or total_count depending on type
        """

        granularity_map = {
            "daily": SummaryTransaction.Granularity.DAILY,
            "weekly": SummaryTransaction.Granularity.WEEKLY,
            "monthly": SummaryTransaction.Granularity.MONTHLY,
        }

        qs = SummaryTransaction.objects.filter(
            granularity=granularity_map[mode]
        )

        if merchant_id:
            qs = qs.filter(merchant_id=merchant_id)
        else:
            qs = qs.filter(merchant_id__isnull=True) | qs.filter(merchant_id="")

        qs = qs.order_by("date")

        results: list[dict] = []

        field_name = "total_amount" if value_type == "amount" else "total_count"

        for s in qs.only("date", "week", "month", field_name):
            if mode == "daily":
                key = format_daily_key(s.date)
            elif mode == "weekly":
                key = format_weekly_key(s.date, s.week)
            else:
                key = format_monthly_key(s.date)

            value = getattr(s, field_name, 0) or 0

            results.append(
                {
                    "key": key,
                    "value": int(value),
                }
            )

        return results
