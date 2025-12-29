# Generated manually for Administrador model
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("basketball", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Administrador",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "persona_external",
                    models.CharField(
                        help_text="UUID externo de la persona en el módulo de usuarios",
                        max_length=100,
                        unique=True,
                        verbose_name="External ID Persona",
                    ),
                ),
                (
                    "cargo",
                    models.CharField(
                        blank=True, max_length=100, null=True, verbose_name="Cargo"
                    ),
                ),
                (
                    "fecha_registro",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Fecha de registro"
                    ),
                ),
                ("estado", models.BooleanField(default=True, verbose_name="Estado")),
            ],
            options={
                "db_table": "administrador",
                "ordering": ["-fecha_registro"],
                "verbose_name": "Administrador",
                "verbose_name_plural": "Administradores",
            },
        ),
    ]
