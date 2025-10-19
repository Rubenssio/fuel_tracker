from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def populate_fillup_users(apps, schema_editor):
    FillUp = apps.get_model("fillups", "FillUp")
    queryset = FillUp.objects.select_related("vehicle")
    for fillup in queryset.iterator():
        FillUp.objects.filter(pk=fillup.pk).update(user_id=fillup.vehicle.user_id)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("vehicles", "0001_initial"),
        ("fillups", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="fillup",
            name="user",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="fillups",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(populate_fillup_users, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="fillup",
            name="user",
            field=models.ForeignKey(
                editable=False,
                null=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="fillups",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RemoveIndex(
            model_name="fillup",
            name="fillups_vehic_8934cf_idx",
        ),
        migrations.RemoveIndex(
            model_name="fillup",
            name="fillups_vehic_b6a5b6_idx",
        ),
        migrations.AddIndex(
            model_name="fillup",
            index=models.Index(
                fields=["user", "vehicle", "-date"],
                name="ix_fill_user_veh_date",
            ),
        ),
        migrations.AddIndex(
            model_name="fillup",
            index=models.Index(
                fields=["user", "-date"],
                name="ix_fill_user_date",
            ),
        ),
        migrations.AddIndex(
            model_name="fillup",
            index=models.Index(
                fields=["user", "fuel_brand"],
                name="ix_fill_user_brand",
            ),
        ),
        migrations.AddIndex(
            model_name="fillup",
            index=models.Index(
                fields=["user", "fuel_grade"],
                name="ix_fill_user_grade",
            ),
        ),
        migrations.AddIndex(
            model_name="fillup",
            index=models.Index(
                fields=["user", "station_name"],
                name="ix_fill_user_station",
            ),
        ),
        migrations.AddIndex(
            model_name="fillup",
            index=models.Index(
                fields=["vehicle", "odometer_km"],
                name="ix_fill_vehicle_odo",
            ),
        ),
    ]
