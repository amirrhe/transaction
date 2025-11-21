# transactions/management/commands/rebuild_summaries.py

from collections import defaultdict
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction

from transactions.models import Transaction, SummaryTransaction


class Command(BaseCommand):
    help = (
        "Rebuild daily, weekly, and monthly summaries with amount, count, "
        "and merchant breakdown, stored in SummaryTransaction."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Delete all existing SummaryTransaction records first.",
        )

    def handle(self, *args, **options):
        truncate = options["truncate"]

        if truncate:
            self.stdout.write(self.style.WARNING("Deleting old summaries..."))
            SummaryTransaction.objects.all().delete()

        summary = defaultdict(lambda: {"amount": 0, "count": 0})

        qs = Transaction.objects.all().only("created_at", "amount", "merchant_id")

        count = 0

        for tx in qs.iterator():
            if not tx.created_at:
                continue

            dt = tx.created_at.date()
            merchant = str(tx.merchant_id) if tx.merchant_id else None
            amount = int(tx.amount or 0)

            key_daily = ("daily", merchant, dt.year, dt.month, None, dt)
            summary[key_daily]["amount"] += amount
            summary[key_daily]["count"] += 1

            iso_year, iso_week, _ = dt.isocalendar()
            ref_week_date = date.fromisocalendar(iso_year, iso_week, 1)
            key_weekly = ("weekly", merchant, iso_year, None, iso_week, ref_week_date)
            summary[key_weekly]["amount"] += amount
            summary[key_weekly]["count"] += 1

            month_start = date(dt.year, dt.month, 1)
            key_monthly = ("monthly", merchant, dt.year, dt.month, None, month_start)
            summary[key_monthly]["amount"] += amount
            summary[key_monthly]["count"] += 1

            count += 1
            if count % 10000 == 0:
                self.stdout.write(f"Processed {count} transactions...")

        self.stdout.write(self.style.SUCCESS(f"Finished reading {count} transactions."))


        summaries_to_create = []

        for (granularity, merchant_id, year, month, week, ref_date), values in summary.items():
            summaries_to_create.append(
                SummaryTransaction(
                    granularity=granularity,
                    merchant_id=merchant_id,
                    date=ref_date,
                    year=year,
                    month=month,
                    week=week,
                    total_amount=values["amount"],
                    total_count=values["count"],
                )
            )

        self.stdout.write(f"Creating {len(summaries_to_create)} summary documents...")

        with db_transaction.atomic():
            SummaryTransaction.objects.bulk_create(summaries_to_create, batch_size=1000)

        self.stdout.write(self.style.SUCCESS("SummaryTransaction rebuild complete."))
