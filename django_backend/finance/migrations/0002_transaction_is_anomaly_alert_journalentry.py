from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0001_initial"),
    ]

    operations = [

        # is_anomaly already exists in PostgreSQL.
        # This updates Django's migration state without
        # attempting to create the column again.
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="transaction",
                    name="is_anomaly",
                    field=models.BooleanField(default=False),
                ),
            ],
        ),

        # Create Alerts table
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
                    models.CharField(max_length=100),
                ),
                (
                    "severity",
                    models.CharField(max_length=50),
                ),
                (
                    "message",
                    models.TextField(),
                ),
                (
                    "is_resolved",
                    models.BooleanField(default=False),
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

        # Create Journal Entries table
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