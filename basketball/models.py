"""
Modelos del módulo Basketball - ORM Django

Las personas se referencian al módulo externo de usuarios mediante `persona_external`.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class TipoInscripcion(models.TextChoices):
    """Enum para tipos de inscripción según edad del atleta"""

    MENOR_EDAD = "MENOR_EDAD", "Menor de edad (con representante)"
    MAYOR_EDAD = "MAYOR_EDAD", "Mayor de edad"


class TipoPrueba(models.TextChoices):
    """Enum para tipos de prueba física"""

    FUERZA = "FUERZA", "Fuerza"
    VELOCIDAD = "VELOCIDAD", "Velocidad"
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
    eliminado = models.BooleanField(default=False, verbose_name="Eliminado")

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

    persona_external = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        verbose_name="External ID Persona",
        help_text="UUID externo de la persona en el módulo de usuarios",
    )

    # Datos Personales Redundantes (backup local si el microservicio falla)
    nombres = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Nombres"
    )
    apellidos = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Apellidos"
    )
    cedula = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Cédula/Identificación"
    )
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    direccion = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Dirección"
    )
    genero = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Género"
    )

    # Datos Personales
    fecha_nacimiento = models.DateField(null=True, verbose_name="Fecha de nacimiento")
    edad = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Edad",
    )
    sexo = models.CharField(max_length=20, verbose_name="Sexo")
    telefono = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Teléfono"
    )

    # Información de Salud
    tipo_sangre = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="Tipo de sangre (RH)"
    )
    alergias = models.TextField(blank=True, null=True, verbose_name="Alergias")
    enfermedades = models.TextField(blank=True, null=True, verbose_name="Enfermedades")
    medicamentos = models.TextField(blank=True, null=True, verbose_name="Medicamentos")
    lesiones = models.TextField(blank=True, null=True, verbose_name="Lesiones")

    # Datos del Representante
    nombre_representante = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Nombre representante"
    )
    cedula_representante = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Cédula representante"
    )
    parentesco_representante = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Parentesco representante"
    )
    telefono_representante = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono representante",
    )
    correo_representante = models.EmailField(
        blank=True, null=True, verbose_name="Correo representante"
    )
    direccion_representante = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Dirección representante"
    )
    ocupacion_representante = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Ocupación representante"
    )

    # Relación con GrupoAtleta (pertenece) - Cardinalidad ManyToMany (1..* a 1..*)
    grupos = models.ManyToManyField(
        GrupoAtleta, related_name="atletas", verbose_name="Grupos"
    )

    class Meta:
        db_table = "atleta"
        verbose_name = "Atleta"
        verbose_name_plural = "Atletas"
        ordering = ["persona_external"]

    def __str__(self):
        return f"Atleta: {self.persona_external}"


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

    # ================================
    # Relación con Atleta
    # ================================
    atleta = models.ForeignKey(
        Atleta,
        on_delete=models.CASCADE,
        related_name="pruebas_antropometricas",
        verbose_name="Atleta",
    )

    # ================================
    # Registrador (Entrenador o Estudiante)
    # ================================
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Tipo de registrador",
    )
    object_id = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="ID del registrador"
    )
    registrado_por = GenericForeignKey("content_type", "object_id")

    rol_registrador = models.CharField(
        max_length=30,
        choices=[
            ("ENTRENADOR", "Entrenador"),
            ("ESTUDIANTE_VINCULACION", "Estudiante de Vinculación"),
        ],
        default="ENTRENADOR",
        verbose_name="Rol del registrador",
    )

    # ================================
    # Datos antropométricos
    # ================================
    fecha_registro = models.DateField(
        default=timezone.now, verbose_name="Fecha de registro"
    )

    peso = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Peso (kg)",
    )

    estatura = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Estatura (m)",
    )

    altura_sentado = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Altura sentado (m)",
    )

    envergadura = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Envergadura (m)",
    )

    # ================================
    # Índices calculados
    # ================================
    indice_masa_corporal = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
        verbose_name="Índice de Masa Corporal",
    )

    indice_cormico = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
        verbose_name="Índice Córmico",
    )

    # ================================
    # Control
    # ================================
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
    )

    estado = models.BooleanField(
        default=True,
        verbose_name="Estado",
    )

    class Meta:
        db_table = "prueba_antropometrica"
        verbose_name = "Prueba Antropométrica"
        verbose_name_plural = "Pruebas Antropométricas"
        ordering = ["-fecha_registro"]

    # ================================
    # Validaciones de dominio
    # ================================
    def clean(self):
        if self.altura_sentado > self.estatura:
            raise ValidationError(
                {
                    "altura_sentado": "La altura sentado no puede ser mayor que la estatura total."
                }
            )

        if self.envergadura < (self.estatura - Decimal("0.05")):
            raise ValidationError(
                {"envergadura": "La envergadura es incoherente respecto a la estatura."}
            )

    # ================================
    # Cálculos automáticos
    # ================================
    def calcular_imc(self):
        return Decimal(self.peso) / (Decimal(self.estatura) ** 2)

    def calcular_indice_cormico(self):
        if self.estatura == 0:
            return Decimal("0")
        return (Decimal(self.altura_sentado) / Decimal(self.estatura)) * Decimal("100")

    def save(self, *args, **kwargs):
        self.indice_masa_corporal = Decimal(self.calcular_imc()).quantize(
            Decimal("0.01")
        )
        self.indice_cormico = Decimal(self.calcular_indice_cormico()).quantize(
            Decimal("0.01")
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Prueba Antropométrica #{self.id} - {self.atleta}"


# =============================================================================
# Modelo PruebaFisica
# =============================================================================
class PruebaFisica(models.Model):
    """Modelo para Pruebas Físicas"""

    # Mapeo de tipo de prueba a unidad de medida (basado en pruebas de baloncesto)
    UNIDADES_POR_TIPO = {
        TipoPrueba.FUERZA: "Centímetros (cm)",  # Salto horizontal
        TipoPrueba.VELOCIDAD: "Segundos (seg)",  # 30 metros
        TipoPrueba.AGILIDAD: "Segundos (seg)",  # Zigzag
    }

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
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Resultado",
    )
    unidad_medida = models.CharField(max_length=20, verbose_name="Unidad de medida")
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    estado = models.BooleanField(default=True, verbose_name="Estado")

    @staticmethod
    def get_unidad_por_tipo(tipo_prueba: str) -> str:
        """Retorna la unidad de medida según el tipo de prueba."""
        return PruebaFisica.UNIDADES_POR_TIPO.get(tipo_prueba, "N/A")

    class Meta:
        db_table = "prueba_fisica"
        verbose_name = "Prueba Física"
        verbose_name_plural = "Pruebas Físicas"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"Prueba Física {self.id} - {self.atleta}"
