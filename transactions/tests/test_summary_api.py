from datetime import date

from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from transactions.models import SummaryTransaction


class TransactionSummaryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("transaction-summary")

        dt = date(2025, 1, 1)
        SummaryTransaction.objects.create(
            granularity=SummaryTransaction.Granularity.DAILY,
            merchant_id=None,
            date=dt,
            year=dt.year,
            month=dt.month,
            week=dt.isocalendar().week,
            total_amount=1234,
            total_count=7,
        )

    def test_missing_mode_param_returns_validation_error(self):
        response = self.client.get(self.url, {"type": "amount"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mode", response.data)

    def test_invalid_mode_returns_validation_error(self):
        response = self.client.get(self.url, {"mode": "yearly", "type": "amount"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mode", response.data)

    def test_invalid_type_returns_validation_error(self):
        response = self.client.get(self.url, {"mode": "daily", "type": "avg"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", response.data)

    def test_daily_amount_summary_success(self):
        response = self.client.get(
            self.url,
            {"mode": "daily", "type": "amount"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        point = response.data[0]
        self.assertIn("key", point)
        self.assertIn("value", point)
        self.assertEqual(point["value"], 1234)

    def test_daily_count_summary_success(self):
        response = self.client.get(
            self.url,
            {"mode": "daily", "type": "count"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        point = response.data[0]
        self.assertEqual(point["value"], 7)
