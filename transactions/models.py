from djongo import models

class Transaction(models.Model):
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
