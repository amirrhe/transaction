from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction

from transactions.models import SummaryTransaction
from transactions.summary_service import SummaryService


class Command(BaseCommand):
    help = "Rebuild summary_transaction table with amount + count + per-merchant breakdown."

    def add_arguments(self, parser):
        parser.add_argument("--truncate", action="store_true")

    def handle(self, *args, **opts):
        if opts["truncate"]:
            SummaryTransaction.objects.all().delete()
            self.stdout.write("Existing summary records removed.")

        objects = SummaryService.rebuild_all_summaries()

        self.stdout.write(f"Creating {len(objects)} summary documents...")

        with db_transaction.atomic():
            SummaryTransaction.objects.bulk_create(objects, batch_size=1000)

        self.stdout.write(self.style.SUCCESS("Summary rebuild complete."))
