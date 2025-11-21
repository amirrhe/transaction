# transactions/models.py
from djongo import models  # you already have djongo installed


class Transaction(models.Model):
    """
    Read-only mapping to existing Mongo collection `transaction` in `transaction_db`.
    We DON'T manage this collection with Django migrations.
    We also DON'T try to override the Mongo `_id`.
    """

    merchant_id = models.CharField(
        max_length=64,
        db_column="merchantId",
    )
    amount = models.BigIntegerField()
    created_at = models.DateTimeField(db_column="createdAt")

    class Meta:
        db_table = "transaction"
        managed = False

    def __str__(self) -> str:
        return f"{self.created_at} – {self.amount}"


class SummaryTransaction(models.Model):
    """
    Our own collection where we store precomputed daily/weekly/monthly summaries.
    This one IS managed by Django (migrations).
    """

    class Granularity(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    granularity = models.CharField(
        max_length=10,
        choices=Granularity.choices,
    )

    date = models.DateField()

    year = models.IntegerField()
    week = models.IntegerField(null=True, blank=True) 
    month = models.IntegerField(null=True, blank=True) 

    total_amount = models.BigIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "summary_transaction"

    def __str__(self) -> str:
        return f"{self.granularity} – {self.date} – {self.total_amount}"
