from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0002_profile_utc_offset_minutes"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="efficiency_unit",
            field=models.CharField(
                choices=[
                    ("l_per_100km", "L/100km"),
                    ("mpg", "MPG"),
                ],
                default="l_per_100km",
                max_length=16,
            ),
            preserve_default=False,
        ),
    ]
