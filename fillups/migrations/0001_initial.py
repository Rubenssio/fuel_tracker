from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("vehicles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FillUp",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("odometer_km", models.PositiveIntegerField()),
                ("station_name", models.CharField(max_length=100)),
                ("fuel_brand", models.CharField(blank=True, max_length=64)),
                ("fuel_grade", models.CharField(blank=True, max_length=64)),
                ("liters", models.DecimalField(decimal_places=2, max_digits=8)),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("notes", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "vehicle",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fillups",
                        to="vehicles.vehicle",
                    ),
                ),
            ],
            options={
                "ordering": ["date", "id"],
                "indexes": [
                    models.Index(fields=["vehicle", "-date"], name="fillups_vehic_8934cf_idx"),
                    models.Index(fields=["vehicle", "odometer_km"], name="fillups_vehic_b6a5b6_idx"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="fillup",
            constraint=models.CheckConstraint(
                check=models.Q(("liters__gt", 0)),
                name="chk_liters_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="fillup",
            constraint=models.CheckConstraint(
                check=models.Q(("total_amount__gt", 0)),
                name="chk_total_positive",
            ),
        ),
    ]
