
from datetime import date

from django.test import TestCase

from transactions.models import SummaryTransaction
from transactions.summary_service import SummaryService


class SummaryServiceTests(TestCase):
    def setUp(self):
        self.dt1 = date(2025, 1, 1) 
        self.dt2 = date(2025, 1, 2)

        SummaryTransaction.objects.create(
            granularity=SummaryTransaction.Granularity.DAILY,
            merchant_id=None,
            date=self.dt1,
            year=self.dt1.year,
            month=self.dt1.month,
            week=self.dt1.isocalendar().week,
            total_amount=1000,
            total_count=2,
        )
        SummaryTransaction.objects.create(
            granularity=SummaryTransaction.Granularity.DAILY,
            merchant_id=None,
            date=self.dt2,
            year=self.dt2.year,
            month=self.dt2.month,
            week=self.dt2.isocalendar().week,
            total_amount=2000,
            total_count=4,
        )

        iso_year, iso_week, _ = self.dt1.isocalendar()
        SummaryTransaction.objects.create(
            granularity=SummaryTransaction.Granularity.WEEKLY,
            merchant_id="42",
            date=date.fromisocalendar(iso_year, iso_week, 1),
            year=iso_year,
            month=None,
            week=iso_week,
            total_amount=5000,
            total_count=10,
        )

        SummaryTransaction.objects.create(
            granularity=SummaryTransaction.Granularity.MONTHLY,
            merchant_id="42",
            date=date(self.dt1.year, self.dt1.month, 1),
            year=self.dt1.year,
            month=self.dt1.month,
            week=None,
            total_amount=9000,
            total_count=20,
        )

    def test_get_daily_summary_amount_all_merchants(self):
        result = SummaryService.get_summary(
            mode="daily",
            value_type="amount",
            merchant_id=None,
        )

        self.assertEqual(len(result), 2)

        self.assertEqual(result[0]["value"], 1000)
        self.assertEqual(result[1]["value"], 2000)

    def test_get_daily_summary_count_all_merchants(self):
        result = SummaryService.get_summary(
            mode="daily",
            value_type="count",
            merchant_id=None,
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["value"], 2)
        self.assertEqual(result[1]["value"], 4)

    def test_get_weekly_summary_for_specific_merchant(self):
        result = SummaryService.get_summary(
            mode="weekly",
            value_type="amount",
            merchant_id="42",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["value"], 5000)

    def test_get_weekly_summary_ignores_other_merchants(self):
        result = SummaryService.get_summary(
            mode="weekly",
            value_type="amount",
            merchant_id="999",
        )
        self.assertEqual(result, [])

    def test_get_monthly_summary_for_specific_merchant(self):
        result = SummaryService.get_summary(
            mode="monthly",
            value_type="count",
            merchant_id="42",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["value"], 20)
