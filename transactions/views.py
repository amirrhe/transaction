from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from transactions.serializers import SummaryPointSerializer
from transactions.summary_service import SummaryService


class TransactionSummaryView(APIView):

    def get(self, request):
        mode = request.query_params.get("mode")
        value_type = request.query_params.get("type")
        merchant_id = request.query_params.get("merchant_id")

        if mode not in {"daily", "weekly", "monthly"}:
            raise ValidationError({"mode": "Invalid mode"})

        if value_type not in {"amount", "count"}:
            raise ValidationError({"type": "Invalid type"})

        data = SummaryService.get_summary(
            mode=mode,
            value_type=value_type,
            merchant_id=merchant_id
        )

        return Response(SummaryPointSerializer(data, many=True).data)
