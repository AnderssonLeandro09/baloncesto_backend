from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("basketball", "0004_adjust_person_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="estudiantevinculacion",
            name="eliminado",
            field=models.BooleanField(default=False, verbose_name="Eliminado"),
        ),
    ]
