from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vehicles", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="vehicle",
            index=models.Index(
                fields=["user", "id"],
                name="ix_vehicle_user_id",
            ),
        ),
    ]
