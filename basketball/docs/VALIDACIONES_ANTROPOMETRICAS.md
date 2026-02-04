# Validaciones de Datos Antropométricos

## 📋 Resumen

Este documento describe las validaciones implementadas para prevenir la entrada de datos basura en las pruebas antropométricas que puedan dañar las gráficas y estadísticas.

## 🎯 Problema Identificado

Los usuarios podían ingresar:
- Valores negativos o ceros
- Cantidades exorbitantes (peso 500kg, estatura 5m)
- Valores enteros sin punto decimal (IMC e índice córmico no se calculaban)
- Fechas futuras o muy antiguas
- Relaciones desproporcionadas entre medidas

## ✅ Validaciones Implementadas

### 1. Validación de Peso (kg)

| Regla | Valor | Mensaje de Error |
|-------|-------|------------------|
| Mínimo | 20.0 kg | "El peso es muy bajo (mínimo 20 kg)" |
| Máximo | 200.0 kg | "El peso es muy alto (máximo 200 kg)" |
| Negativo/Cero | No permitido | "El peso debe ser mayor a 0 kg" |

**Archivo:** `basketball/serializar/prueba_antropometrica.py` - método `validate_peso()`

### 2. Validación de Estatura (m)

| Regla | Valor | Mensaje de Error |
|-------|-------|------------------|
| Mínimo | 1.0 m | "La estatura es muy baja (mínimo 1.0 m)" |
| Máximo | 2.5 m | "La estatura es muy alta (máximo 2.5 m)" |
| Negativo/Cero | No permitido | "La estatura debe ser mayor a 0 m" |

**Archivo:** `basketball/serializar/prueba_antropometrica.py` - método `validate_estatura()`

### 3. Validación de Altura Sentado (m)

| Regla | Valor | Mensaje de Error |
|-------|-------|------------------|
| Mínimo | 0.5 m | "La altura sentado es muy baja (mínimo 0.5 m)" |
| Máximo | 1.5 m | "La altura sentado es muy alta (máximo 1.5 m)" |
| No mayor que estatura | altura_sentado ≤ estatura | "La altura sentado no puede ser mayor que la estatura" |
| Proporción mínima | ≥ 40% de estatura | "La altura sentado parece incorrecta (muy baja respecto a estatura)" |

**Archivos:** 
- `basketball/serializar/prueba_antropometrica.py` - método `validate_altura_sentado()`
- `basketball/serializar/prueba_antropometrica.py` - método `validate()` (validaciones cruzadas)

### 4. Validación de Envergadura (m)

| Regla | Valor | Mensaje de Error |
|-------|-------|------------------|
| Mínimo | 1.0 m | "La envergadura es muy baja (mínimo 1.0 m)" |
| Máximo | 3.0 m | "La envergadura es muy alta (máximo 3.0 m)" |
| Ratio con estatura | 0.9 - 1.4 | "La relación envergadura/estatura ({ratio:.2f}) es inusual. Verifica los datos." |

**Archivos:** 
- `basketball/serializar/prueba_antropometrica.py` - método `validate_envergadura()`
- `basketball/serializar/prueba_antropometrica.py` - método `validate()` (ratio)

### 5. Validación de Fecha de Registro

| Regla | Valor | Mensaje de Error |
|-------|-------|------------------|
| Fecha futura | No permitido | "La fecha no puede ser futura" |
| Fecha muy antigua | Máximo 10 años atrás | "La fecha no puede ser anterior a {fecha_minima}" |

**Archivo:** `basketball/serializar/prueba_antropometrica.py` - método `validate_fecha_registro()`

### 6. Conversión Automática de Tipos

**Problema:** Usuarios ingresaban valores enteros sin decimales (ej: `70` en lugar de `70.0`), causando que los índices IMC y córmico no se calcularan correctamente.

**Solución:** Conversión automática en el método `to_internal_value()` que:
- Convierte enteros a Decimales
- Convierte strings numéricos a Decimales
- Garantiza 2 decimales de precisión

**Archivo:** `basketball/serializar/prueba_antropometrica.py` - método `to_internal_value()`

## 🧪 Cobertura de Tests

Se implementaron **30 tests** que cubren:

### Tests de Peso (7)
- ✅ Peso negativo
- ✅ Peso en cero
- ✅ Peso muy bajo (< 20 kg)
- ✅ Peso exorbitante (> 200 kg)
- ✅ Peso límite inferior válido (20 kg)
- ✅ Peso límite superior válido (200 kg)
- ✅ Conversión de enteros

### Tests de Estatura (3)
- ✅ Estatura negativa
- ✅ Estatura muy baja (< 1.0 m)
- ✅ Estatura exorbitante (> 2.5 m)

### Tests de Altura Sentado (5)
- ✅ Altura sentado negativa
- ✅ Altura sentado muy baja (< 0.5 m)
- ✅ Altura sentado muy alta (> 1.5 m)
- ✅ Altura sentado mayor que estatura
- ✅ Altura sentado desproporcionada (< 40% estatura)

### Tests de Envergadura (5)
- ✅ Envergadura negativa
- ✅ Envergadura muy baja (< 1.0 m)
- ✅ Envergadura exorbitante (> 3.0 m)
- ✅ Ratio envergadura/estatura muy bajo (< 0.9)
- ✅ Ratio envergadura/estatura muy alto (> 1.4)

### Tests de Fecha (4)
- ✅ Fecha futura
- ✅ Fecha muy antigua (> 10 años)
- ✅ Fecha actual válida
- ✅ Fecha límite válida (10 años atrás)

### Tests de Conversión (2)
- ✅ Enteros sin punto decimal
- ✅ Strings numéricos

### Tests Generales (4)
- ✅ Creación exitosa
- ✅ Listado de pruebas
- ✅ Toggle de estado
- ✅ Permisos denegados

**Archivo de tests:** `basketball/tests/controllers/test_prueba_antropometrica.py`

## 🔧 Archivos Modificados

1. **`basketball/serializar/prueba_antropometrica.py`**
   - Agregado método `to_internal_value()` para conversión automática
   - Agregado método `validate_peso()`
   - Agregado método `validate_estatura()`
   - Agregado método `validate_altura_sentado()`
   - Agregado método `validate_envergadura()`
   - Agregado método `validate_fecha_registro()`
   - Mejorado método `validate()` con validaciones cruzadas

2. **`basketball/models.py`**
   - Actualizados validadores del modelo `PruebaAntropometrica`
   - Agregados `MinValueValidator` y `MaxValueValidator` con rangos específicos

3. **`basketball/tests/controllers/test_prueba_antropometrica.py`**
   - Agregados 24 tests nuevos de validación
   - Tests cubren casos límite y casos de error

## 📊 Impacto en los Datos

### Rangos Aceptables

```python
RANGOS_VALIDOS = {
    "peso": (20.0, 200.0),           # kg
    "estatura": (1.0, 2.5),          # metros
    "altura_sentado": (0.5, 1.5),    # metros
    "envergadura": (1.0, 3.0),       # metros
    "ratio_envergadura": (0.9, 1.4), # proporción
    "ratio_altura_sentado": 0.4,     # 40% mínimo de estatura
    "fecha_maxima_antiguedad": 10    # años
}
```

### Ejemplos de Valores Rechazados

❌ **Rechazados:**
- Peso: -10 kg, 0 kg, 15 kg, 250 kg
- Estatura: -1.75 m, 0.85 m, 3.0 m
- Altura sentado: -0.90 m, 0.30 m, 1.85 m (mayor que estatura)
- Envergadura: -1.80 m, 0.80 m, 3.50 m
- Fecha: 2026-02-01 (futura), 2010-01-01 (muy antigua)

✅ **Aceptados:**
- Peso: 20.0 kg, 70.5 kg, 200.0 kg
- Estatura: 1.0 m, 1.75 m, 2.5 m
- Altura sentado: 0.5 m, 0.90 m, 1.5 m
- Envergadura: 1.0 m, 1.80 m, 3.0 m
- Fecha: 2016-01-07 hasta 2026-01-06

## 🚀 Ejecución de Tests

```bash
# Ejecutar todos los tests de pruebas antropométricas
cd baloncesto_backend
python manage.py test basketball.tests.controllers.test_prueba_antropometrica

# Ejecutar con verbosidad
python manage.py test basketball.tests.controllers.test_prueba_antropometrica -v 2

# Ejecutar un test específico
python manage.py test basketball.tests.controllers.test_prueba_antropometrica.PruebaAntropometricaControllerTests.test_create_prueba_peso_negativo
```

## 💡 Recomendaciones Adicionales

### Para el Frontend

1. **Validaciones en Tiempo Real:**
   ```javascript
   const validaciones = {
     peso: { min: 20, max: 200, step: 0.1 },
     estatura: { min: 1.0, max: 2.5, step: 0.01 },
     altura_sentado: { min: 0.5, max: 1.5, step: 0.01 },
     envergadura: { min: 1.0, max: 3.0, step: 0.01 }
   }
   ```

2. **Input Type Number:**
   ```html
   <input type="number" min="20" max="200" step="0.1" />
   ```

3. **Mensajes de Ayuda:**
   - Mostrar rangos válidos en tooltips
   - Feedback visual cuando el valor está fuera de rango

### Para Datos Existentes

Si hay datos basura en la base de datos, puedes crear un comando de limpieza:

```python
# basketball/management/commands/limpiar_pruebas_antropometricas.py
from django.core.management.base import BaseCommand
from basketball.models import PruebaAntropometrica
from django.db.models import Q

class Command(BaseCommand):
    help = 'Marca como inválidas las pruebas con datos fuera de rango'

    def handle(self, *args, **options):
        pruebas_invalidas = PruebaAntropometrica.objects.filter(
            Q(peso__lt=20) | Q(peso__gt=200) |
            Q(estatura__lt=1.0) | Q(estatura__gt=2.5) |
            Q(altura_sentado__lt=0.5) | Q(altura_sentado__gt=1.5) |
            Q(envergadura__lt=1.0) | Q(envergadura__gt=3.0)
        )
        count = pruebas_invalidas.update(estado=False)
        self.stdout.write(
            self.style.SUCCESS(f'Se marcaron {count} pruebas como inválidas')
        )
```

## 📝 Notas de Implementación

- Las validaciones están en **dos capas**: serializer (API) y modelo (base de datos)
- La conversión automática de tipos garantiza compatibilidad con diferentes inputs del frontend
- Los tests usan mocks para no depender de la base de datos
- Las validaciones cruzadas previenen inconsistencias entre medidas relacionadas

## 🔗 Referencias

- Django Rest Framework Serializers: https://www.django-rest-framework.org/api-guide/serializers/
- Django Model Validators: https://docs.djangoproject.com/en/stable/ref/validators/
- Índice de Masa Corporal (IMC): Peso(kg) / Estatura²(m)
- Índice Córmico: (Altura Sentado / Estatura) × 100

---

**Fecha de Implementación:** 6 de enero de 2026  
**Autor:** Sistema de Validaciones Antropométricas  
**Versión:** 1.0
