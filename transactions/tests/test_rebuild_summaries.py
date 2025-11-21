from datetime import datetime

from django.core.management import call_command
from django.test import TestCase

from transactions.models import Transaction, SummaryTransaction


class RebuildSummariesCommandTests(TestCase):
    def setUp(self):
        self.dt = datetime(2025, 1, 1, 10, 30)
        Transaction.objects.create(
            created_at=self.dt,
            amount=1000,
            merchant_id="42",
        )
        Transaction.objects.create(
            created_at=self.dt,
            amount=2000,
            merchant_id="42",
        )

    def test_rebuild_summaries_creates_expected_records(self):
        self.assertEqual(SummaryTransaction.objects.count(), 0)

        call_command("rebuild_summaries", "--truncate")

        all_summaries = SummaryTransaction.objects.all()
        self.assertEqual(all_summaries.count(), 3)

        total_amount = sum(s.total_amount for s in all_summaries)
        total_count = sum(s.total_count for s in all_summaries)

        self.assertEqual(total_amount, 3000 * 3)
        self.assertEqual(total_count, 2 * 3)

        granularities = {s.granularity for s in all_summaries}
        self.assertSetEqual(
            granularities,
            {"daily", "weekly", "monthly"},
        )

    def test_truncate_option_deletes_existing_summaries(self):
        call_command("rebuild_summaries", "--truncate")
        self.assertEqual(SummaryTransaction.objects.count(), 3)

        SummaryTransaction.objects.create(
            granularity="daily",
            merchant_id=None,
            date=self.dt.date(),
            year=self.dt.year,
            month=self.dt.month,
            week=self.dt.isocalendar().week,
            total_amount=999,
            total_count=1,
        )
        self.assertEqual(SummaryTransaction.objects.count(), 4)

        call_command("rebuild_summaries", "--truncate")
        self.assertEqual(SummaryTransaction.objects.count(), 3)
