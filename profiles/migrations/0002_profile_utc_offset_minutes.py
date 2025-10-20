"""Add UTC offset preference to profiles."""
from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="utc_offset_minutes",
            field=models.IntegerField(default=0),
        ),
    ]
