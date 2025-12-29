from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("basketball", "0002_administrador"),
    ]

    operations = [
        # Primero eliminar la FK de grupo_atleta hacia entrenador
        migrations.RemoveField(
            model_name="grupoatleta",
            name="entrenador",
        ),
        migrations.DeleteModel(
            name="EstudianteVinculacion",
        ),
        migrations.DeleteModel(
            name="Entrenador",
        ),
        migrations.DeleteModel(
            name="Usuario",
        ),
        migrations.CreateModel(
            name="Entrenador",
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
                    "especialidad",
                    models.CharField(max_length=100, verbose_name="Especialidad"),
                ),
                (
                    "club_asignado",
                    models.CharField(max_length=100, verbose_name="Club asignado"),
                ),
                (
                    "fecha_registro",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Fecha de registro"
                    ),
                ),
                (
                    "estado",
                    models.BooleanField(default=True, verbose_name="Estado"),
                ),
            ],
            options={
                "verbose_name": "Entrenador",
                "verbose_name_plural": "Entrenadores",
                "db_table": "entrenador",
                "ordering": ["-fecha_registro"],
            },
        ),
        migrations.CreateModel(
            name="Pasante",
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
                    "carrera",
                    models.CharField(max_length=100, verbose_name="Carrera"),
                ),
                (
                    "semestre",
                    models.CharField(max_length=20, verbose_name="Semestre"),
                ),
                (
                    "universidad",
                    models.CharField(
                        blank=True,
                        max_length=150,
                        null=True,
                        verbose_name="Universidad",
                    ),
                ),
                (
                    "fecha_inicio",
                    models.DateField(verbose_name="Fecha de inicio de vinculación"),
                ),
                (
                    "fecha_fin",
                    models.DateField(
                        blank=True,
                        null=True,
                        verbose_name="Fecha de fin de vinculación",
                    ),
                ),
                (
                    "fecha_registro",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Fecha de registro"
                    ),
                ),
                (
                    "estado",
                    models.BooleanField(default=True, verbose_name="Estado"),
                ),
            ],
            options={
                "verbose_name": "Pasante",
                "verbose_name_plural": "Pasantes",
                "db_table": "pasante",
                "ordering": ["-fecha_registro"],
            },
        ),
        # Volver a agregar la FK de grupo_atleta hacia el nuevo Entrenador
        migrations.AddField(
            model_name="grupoatleta",
            name="entrenador",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="grupos",
                to="basketball.entrenador",
                verbose_name="Entrenador",
            ),
            preserve_default=False,
        ),
    ]
