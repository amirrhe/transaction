from django.urls import path
from transactions.views import TransactionSummaryView

urlpatterns = [
    path(
        "transactions/summary/",
        TransactionSummaryView.as_view(),
        name="transaction-summary",
    ),
]
