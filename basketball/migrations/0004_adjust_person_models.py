from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("basketball", "0003_external_person_models"),
    ]

    operations = [
        # Limpieza de campos que ya no se usan en Entrenador
        migrations.RemoveField(
            model_name="entrenador",
            name="fecha_registro",
        ),
        migrations.RemoveField(
            model_name="entrenador",
            name="estado",
        ),
        # Limpieza y renombrado de Pasante -> EstudianteVinculacion
        migrations.RemoveField(
            model_name="pasante",
            name="universidad",
        ),
        migrations.RemoveField(
            model_name="pasante",
            name="fecha_inicio",
        ),
        migrations.RemoveField(
            model_name="pasante",
            name="fecha_fin",
        ),
        migrations.RemoveField(
            model_name="pasante",
            name="fecha_registro",
        ),
        migrations.RemoveField(
            model_name="pasante",
            name="estado",
        ),
        migrations.RenameModel(
            old_name="Pasante",
            new_name="EstudianteVinculacion",
        ),
        migrations.AlterModelOptions(
            name="estudiantevinculacion",
            options={
                "verbose_name": "Estudiante de Vinculación",
                "verbose_name_plural": "Estudiantes de Vinculación",
                "ordering": ["persona_external"],
            },
        ),
        migrations.AlterModelTable(
            name="estudiantevinculacion",
            table="estudiante_vinculacion",
        ),
    ]
