from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0001_initial"),
    ]

    operations = [

        # ============================================================
        # TRANSACTION - IS ANOMALY
        # ============================================================

        # 0 = normal transaction
        # 1 = anomalous transaction
        migrations.AddField(
            model_name="transaction",
            name="is_anomaly",
            field=models.SmallIntegerField(default=0),
        ),

        # ============================================================
        # ALERTS
        # ============================================================

        migrations.CreateModel(
            name="Alert",
            fields=[
                (
                    "alert_id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "alert_type",
                    models.CharField(
                        max_length=100,
                    ),
                ),
                (
                    "severity",
                    models.CharField(
                        max_length=50,
                    ),
                ),
                (
                    "message",
                    models.TextField(),
                ),
                (
                    "is_resolved",
                    models.BooleanField(
                        default=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        db_column="transaction_id",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="finance.transaction",
                    ),
                ),
            ],
            options={
                "db_table": "alerts",
            },
        ),

        # ============================================================
        # JOURNAL ENTRIES
        # ============================================================

        migrations.CreateModel(
            name="JournalEntry",
            fields=[
                (
                    "journal_entry_id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "entry_date",
                    models.DateTimeField(),
                ),
                (
                    "description",
                    models.TextField(),
                ),
                (
                    "debit",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=15,
                    ),
                ),
                (
                    "credit",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=15,
                    ),
                ),
                (
                    "account",
                    models.ForeignKey(
                        db_column="account_id",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="finance.account",
                    ),
                ),
            ],
            options={
                "db_table": "journal_entries",
            },
        ),
    ]