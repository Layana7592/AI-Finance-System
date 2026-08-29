from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0003_alter_transaction_is_anomaly_report"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(
                    model_name="user",
                    name="password_hash",
                ),
                migrations.AddField(
                    model_name="user",
                    name="password",
                    field=models.CharField(
                        db_column="password_hash",
                        max_length=128,
                    ),
                ),
            ],
        ),
    ]