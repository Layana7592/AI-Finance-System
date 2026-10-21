# Generated for the separate synthetic double-entry teaching ledger.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0006_merge_20260830_1630"),
    ]

    operations = [
        migrations.CreateModel(
            name="SyntheticLedgerAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True)),
                ("balance", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("is_system_clearing", models.BooleanField(default=False)),
                ("account", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="synthetic_wallet", to="finance.account")),
            ],
            options={"db_table": "synthetic_ledger_accounts"},
        ),
        migrations.CreateModel(
            name="SyntheticLedgerPosting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("idempotency_key", models.CharField(max_length=120, unique=True)),
                ("operation", models.CharField(max_length=24)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=15)),
                ("memo", models.CharField(blank=True, max_length=500)),
                ("request_fingerprint", models.CharField(max_length=64)),
                ("posted_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("source_account", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="synthetic_outgoing_postings", to="finance.account")),
                ("destination_account", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="synthetic_incoming_postings", to="finance.account")),
                ("reversal_of", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reversed_by", to="finance.syntheticledgerposting")),
            ],
            options={"db_table": "synthetic_ledger_postings"},
        ),
        migrations.CreateModel(
            name="SyntheticLedgerLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("side", models.CharField(choices=[("DR", "Debit"), ("CR", "Credit")], max_length=2)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=15)),
                ("ledger_account", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="posted_lines", to="finance.syntheticledgeraccount")),
                ("posting", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lines", to="finance.syntheticledgerposting")),
            ],
            options={"db_table": "synthetic_ledger_lines"},
        ),
        migrations.AddConstraint(
            model_name="syntheticledgerline",
            constraint=models.CheckConstraint(condition=models.Q(("amount__gt", 0)), name="ledger_line_gt_zero"),
        ),
    ]
