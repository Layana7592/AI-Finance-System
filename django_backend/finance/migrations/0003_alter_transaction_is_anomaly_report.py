from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0002_transaction_is_anomaly_alert_journalentry"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="is_anomaly",
            field=models.SmallIntegerField(default=0),
        ),
    ]