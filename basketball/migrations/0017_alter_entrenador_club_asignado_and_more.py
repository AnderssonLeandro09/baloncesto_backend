# Generated migration to add validators to Entrenador fields

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("basketball", "0016_merge_0013_add_email_direccion_genero_0015_merge_all"),
    ]

    operations = [
        migrations.AlterField(
            model_name="entrenador",
            name="especialidad",
            field=models.CharField(
                max_length=100,
                validators=[
                    django.core.validators.MinLengthValidator(3, "La especialidad debe tener al menos 3 caracteres")
                ],
                verbose_name="Especialidad",
            ),
        ),
        migrations.AlterField(
            model_name="entrenador",
            name="club_asignado",
            field=models.CharField(
                max_length=100,
                validators=[
                    django.core.validators.MinLengthValidator(3, "El club asignado debe tener al menos 3 caracteres")
                ],
                verbose_name="Club asignado",
            ),
        ),
    ]
