from collections import defaultdict
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction

from transactions.models import Transaction, SummaryTransaction


class Command(BaseCommand):
    help = (
        "Rebuild daily, weekly, and monthly summaries in summary_transaction "
        "from the raw transaction collection."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Delete all existing SummaryTransaction records before rebuilding.",
        )

    def handle(self, *args, **options):
        truncate = options["truncate"]

        if truncate:
            self.stdout.write(self.style.WARNING("Deleting existing summaries..."))
            SummaryTransaction.objects.all().delete()

        daily_totals = defaultdict(int)
        weekly_totals = defaultdict(int)
        monthly_totals = defaultdict(int)

        qs = Transaction.objects.all().only("amount", "created_at")

        count = 0
        for tx in qs.iterator():
            if not tx.created_at:
                continue

            dt = tx.created_at.date()
            amount = int(tx.amount or 0)

            daily_totals[dt] += amount

            iso_year, iso_week, _ = dt.isocalendar()
            weekly_totals[(iso_year, iso_week)] += amount

            monthly_totals[(dt.year, dt.month)] += amount

            count += 1
            if count % 10_000 == 0:
                self.stdout.write(f"Processed {count} transactions...")

        self.stdout.write(self.style.SUCCESS(f"Finished reading {count} transactions."))

        summaries_to_create = []

        for day, total in daily_totals.items():
            summaries_to_create.append(
                SummaryTransaction(
                    granularity=SummaryTransaction.Granularity.DAILY,
                    date=day,
                    year=day.year,
                    week=None,
                    month=day.month,
                    total_amount=total,
                )
            )

        for (year, week), total in weekly_totals.items():
            ref_date = date.fromisocalendar(year, week, 1)
            summaries_to_create.append(
                SummaryTransaction(
                    granularity=SummaryTransaction.Granularity.WEEKLY,
                    date=ref_date,
                    year=year,
                    week=week,
                    month=None,
                    total_amount=total,
                )
            )

        for (year, month), total in monthly_totals.items():
            ref_date = date(year=year, month=month, day=1)
            summaries_to_create.append(
                SummaryTransaction(
                    granularity=SummaryTransaction.Granularity.MONTHLY,
                    date=ref_date,
                    year=year,
                    week=None,
                    month=month,
                    total_amount=total,
                )
            )

        self.stdout.write(f"Creating {len(summaries_to_create)} summary documents")

        with db_transaction.atomic():
            SummaryTransaction.objects.bulk_create(
                summaries_to_create,
                batch_size=1000,
            )

        self.stdout.write(self.style.SUCCESS("SummaryTransaction rebuild complete"))
