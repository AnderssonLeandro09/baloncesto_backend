"""
Modelos del módulo Basketball - ORM Django

Las personas se referencian al módulo externo de usuarios mediante `persona_external`.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class TipoInscripcion(models.TextChoices):
    """Enum para tipos de inscripción"""

    FEDERADO = "FEDERADO", "Federado"
    NO_FEDERADO = "NO_FEDERADO", "No Federado"
    INVITADO = "INVITADO", "Invitado"


class TipoPrueba(models.TextChoices):
    """Enum para tipos de prueba física"""

    VELOCIDAD = "VELOCIDAD", "Velocidad"
    RESISTENCIA = "RESISTENCIA", "Resistencia"
    FUERZA = "FUERZA", "Fuerza"
    FLEXIBILIDAD = "FLEXIBILIDAD", "Flexibilidad"
    COORDINACION = "COORDINACION", "Coordinación"
    AGILIDAD = "AGILIDAD", "Agilidad"


class Sexo(models.TextChoices):
    """Enum para sexo"""

    MASCULINO = "M", "Masculino"
    FEMENINO = "F", "Femenino"
    OTRO = "O", "Otro"


class Administrador(models.Model):
    """Administrador referenciado al módulo de usuarios mediante persona_external."""

    persona_external = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="External ID Persona",
        help_text="UUID externo de la persona en el módulo de usuarios",
    )
    cargo = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Cargo"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de registro"
    )
    estado = models.BooleanField(default=True, verbose_name="Estado")

    class Meta:
        db_table = "administrador"
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"Administrador: {self.persona_external}"


# =============================================================================
# Modelo GrupoAtleta
# =============================================================================
class GrupoAtleta(models.Model):
    """Modelo para grupos de atletas"""

    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    rango_edad_minima = models.IntegerField(
        validators=[MinValueValidator(0)], verbose_name="Rango edad mínima"
    )
    rango_edad_maxima = models.IntegerField(
        validators=[MinValueValidator(0)], verbose_name="Rango edad máxima"
    )
    categoria = models.CharField(max_length=50, verbose_name="Categoría")
    fecha_creacion = models.DateField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    estado = models.BooleanField(default=True, verbose_name="Estado")

    # Relación con Entrenador (implementa) - Cardinalidad 1 Entrenador tiene 1..* Grupos
    # La FK se define como string porque Entrenador se define después
    entrenador = models.ForeignKey(
        "Entrenador",
        on_delete=models.PROTECT,
        related_name="grupos",
        verbose_name="Entrenador",
    )

    class Meta:
        db_table = "grupo_atleta"
        verbose_name = "Grupo de Atleta"
        verbose_name_plural = "Grupos de Atletas"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} - {self.categoria}"


# =============================================================================
# Modelo Entrenador (referencia externa al módulo de usuarios)
# =============================================================================
class Entrenador(models.Model):
    """Modelo para Entrenadores usando persona_external del módulo de usuarios."""

    persona_external = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="External ID Persona",
        help_text="UUID externo de la persona en el módulo de usuarios",
    )
    especialidad = models.CharField(max_length=100, verbose_name="Especialidad")
    club_asignado = models.CharField(max_length=100, verbose_name="Club asignado")
    eliminado = models.BooleanField(default=False, verbose_name="Eliminado")

    class Meta:
        db_table = "entrenador"
        verbose_name = "Entrenador"
        verbose_name_plural = "Entrenadores"
        ordering = ["persona_external"]

    def __str__(self):
        return f"Entrenador: {self.persona_external} - {self.especialidad}"


# =============================================================================
# Modelo Estudiante de Vinculación referencia externa
# =============================================================================
class EstudianteVinculacion(models.Model):
    """Modelo para Estudiantes de Vinculación usando persona_external."""

    persona_external = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="External ID Persona",
        help_text="UUID externo de la persona en el módulo de usuarios",
    )
    carrera = models.CharField(max_length=100, verbose_name="Carrera")
    semestre = models.CharField(max_length=20, verbose_name="Semestre")
    eliminado = models.BooleanField(default=False, verbose_name="Eliminado")

    class Meta:
        db_table = "estudiante_vinculacion"
        verbose_name = "Estudiante de Vinculación"
        verbose_name_plural = "Estudiantes de Vinculación"
        ordering = ["persona_external"]

    def __str__(self):
        return f"Estudiante Vinculación: {self.persona_external} - {self.carrera}"


# =============================================================================
# Modelo Atleta
# =============================================================================
class Atleta(models.Model):
    """Modelo para Atletas"""

    nombre_atleta = models.CharField(max_length=100, verbose_name="Nombre")
    apellido_atleta = models.CharField(max_length=100, verbose_name="Apellido")
    dni = models.CharField(max_length=20, unique=True, verbose_name="DNI")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de nacimiento")
    edad = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Edad",
    )
    sexo = models.CharField(max_length=1, choices=Sexo.choices, verbose_name="Sexo")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    telefono = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Teléfono"
    )
    tipo_sangre = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="Tipo de sangre"
    )
    datos_representante = models.TextField(
        blank=True, null=True, verbose_name="Datos del representante"
    )
    telefono_representante = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono representante",
    )

    # Relación con GrupoAtleta (pertenece) - Cardinalidad ManyToMany (1..* a 1..*)
    grupos = models.ManyToManyField(
        GrupoAtleta, related_name="atletas", verbose_name="Grupos"
    )

    class Meta:
        db_table = "atleta"
        verbose_name = "Atleta"
        verbose_name_plural = "Atletas"
        ordering = ["apellido_atleta", "nombre_atleta"]

    def __str__(self):
        return f"{self.nombre_atleta} {self.apellido_atleta}"


# =============================================================================
# Modelo Inscripcion
# =============================================================================
class Inscripcion(models.Model):
    """Modelo para Inscripciones"""

    # Relación con Atleta (realiza) - Cardinalidad 1 a 1
    atleta = models.OneToOneField(
        Atleta,
        on_delete=models.CASCADE,
        related_name="inscripcion",
        verbose_name="Atleta",
    )
    fecha_inscripcion = models.DateField(verbose_name="Fecha de inscripción")
    tipo_inscripcion = models.CharField(
        max_length=20,
        choices=TipoInscripcion.choices,
        verbose_name="Tipo de inscripción",
    )
    fecha_creacion = models.DateField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    habilitada = models.BooleanField(default=True, verbose_name="Habilitada")

    class Meta:
        db_table = "inscripcion"
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"
        ordering = ["-fecha_inscripcion"]

    def __str__(self):
        return f"Inscripción {self.id} - {self.atleta}"


# =============================================================================
# Modelo PruebaAntropometrica
# =============================================================================
class PruebaAntropometrica(models.Model):
    """Modelo para Pruebas Antropométricas"""

    # Relación con Atleta (tiene)
    atleta = models.ForeignKey(
        Atleta,
        on_delete=models.CASCADE,
        related_name="pruebas_antropometricas",
        verbose_name="Atleta",
    )
    fecha_registro = models.DateField(verbose_name="Fecha de registro")
    indice_masa_corporal = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Índice de masa corporal",
    )
    estatura = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Estatura (cm)",
    )
    altura_sentado = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Altura sentado (cm)",
    )
    envergadura = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Envergadura (cm)",
    )
    indice_cornico = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Índice córnico",
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    estado = models.BooleanField(default=True, verbose_name="Estado")

    class Meta:
        db_table = "prueba_antropometrica"
        verbose_name = "Prueba Antropométrica"
        verbose_name_plural = "Pruebas Antropométricas"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"Prueba Antropométrica {self.id} - {self.atleta}"


# =============================================================================
# Modelo PruebaFisica
# =============================================================================
class PruebaFisica(models.Model):
    """Modelo para Pruebas Físicas"""

    # Relación con Atleta (tiene)
    atleta = models.ForeignKey(
        Atleta,
        on_delete=models.CASCADE,
        related_name="pruebas_fisicas",
        verbose_name="Atleta",
    )
    fecha_registro = models.DateField(verbose_name="Fecha de registro")
    tipo_prueba = models.CharField(
        max_length=20,
        choices=TipoPrueba.choices,
        verbose_name="Tipo de prueba",
    )
    resultado = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Resultado"
    )
    unidad_medida = models.CharField(max_length=20, verbose_name="Unidad de medida")
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    estado = models.BooleanField(default=True, verbose_name="Estado")

    class Meta:
        db_table = "prueba_fisica"
        verbose_name = "Prueba Física"
        verbose_name_plural = "Pruebas Físicas"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"Prueba Física {self.id} - {self.atleta}"
