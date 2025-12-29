from django.contrib import admin
from .models import Administrador


@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ("id", "persona_external", "cargo", "estado", "fecha_registro")
    search_fields = ("persona_external", "cargo")
    list_filter = ("estado",)
