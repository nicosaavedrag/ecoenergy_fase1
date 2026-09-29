from django.contrib import admin, messages
from django.utils import timezone
from .models import (
    Organizacion,
    CategoriaDispositivo,
    Zona,
    Dispositivo,
    PerfilUsuario,
    RegistroConsumo,
    AlertaConsumo,
)


def get_user_org(request):
    """
    Retorna la Organización asociada al usuario autenticado mediante su PerfilUsuario.
    Si el usuario es superusuario o no tiene perfil asignado, retorna None (acceso global).
    """
    if request.user.is_superuser:
        return None
    perfil = getattr(request.user, 'perfil', None)
    if perfil and perfil.organizacion:
        return perfil.organizacion
    return None


# ==============================================================================
# INLINES (Admin Pro)
# ==============================================================================

class DispositivoInline(admin.TabularInline):
    """
    Inline que permite visualizar y dar de alta dispositivos directamente
    dentro de la interfaz de edición de una Zona.
    """
    model = Dispositivo
    extra = 0
    fields = ('nombre', 'codigo_inventario', 'categoria', 'potencia_nominal_kw', 'estado')
    show_change_link = True


class RegistroConsumoInline(admin.TabularInline):
    """
    Inline que permite visualizar las últimas mediciones de consumo directamente
    en la ficha técnica de un Dispositivo.
    """
    model = RegistroConsumo
    extra = 0
    fields = ('fecha_hora', 'consumo_kwh', 'voltaje_promedio', 'observacion')
    readonly_fields = ('fecha_hora',)
    can_delete = False
    max_num = 5


# ==============================================================================
# MODELADMINS - TABLAS MAESTRAS
# ==============================================================================

@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    """
    Tabla Maestra 1: Gestión de Organizaciones.
    Aplica scoping: los usuarios limitados solo ven su propia organización.
    """
    list_display = ('nombre', 'rut', 'email_contacto', 'telefono', 'activa', 'fecha_registro')
    search_fields = ('nombre', 'rut', 'email_contacto')
    list_filter = ('activa', 'fecha_registro')
    ordering = ('nombre',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        org = get_user_org(request)
        if org:
            return qs.filter(id=org.id)
        return qs

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            org = get_user_org(request)
            if org and obj.id != org.id:
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(CategoriaDispositivo)
class CategoriaDispositivoAdmin(admin.ModelAdmin):
    """
    Tabla Maestra 2: Catálogo de Categorías de Dispositivos.
    """
    list_display = ('nombre', 'descripcion_corta', 'es_critica', 'total_dispositivos')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('es_critica',)
    ordering = ('nombre',)

    @admin.display(description="Descripción")
    def descripcion_corta(self, obj):
        return (obj.descripcion[:60] + '...') if len(obj.descripcion) > 60 else obj.descripcion

    @admin.display(description="Dispositivos Asociados")
    def total_dispositivos(self, obj):
        return obj.dispositivos.count()


@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    """
    Tabla Maestra 3: Zonas o Dependencias.
    Incluye Inline de Dispositivos, optimización de FK y scoping por organización.
    """
    list_display = ('nombre', 'organizacion', 'limite_kwh', 'responsable', 'activa', 'cantidad_dispositivos')
    search_fields = ('nombre', 'responsable', 'organizacion__nombre')
    list_filter = ('activa', 'organizacion')
    ordering = ('organizacion__nombre', 'nombre')
    list_select_related = ('organizacion',)
    inlines = [DispositivoInline]

    @admin.display(description="Cant. Dispositivos")
    def cantidad_dispositivos(self, obj):
        return obj.dispositivos.count()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        org = get_user_org(request)
        if org:
            return qs.filter(organizacion=org)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "organizacion":
            org = get_user_org(request)
            if org:
                kwargs["queryset"] = Organizacion.objects.filter(id=org.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        org = get_user_org(request)
        if org and not request.user.is_superuser:
            obj.organizacion = org
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            org = get_user_org(request)
            if org and obj.organizacion_id != org.id:
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            org = get_user_org(request)
            if org and obj.organizacion_id != org.id:
                return False
        return super().has_delete_permission(request, obj)


@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    """
    Tabla Maestra 4: Equipos de Consumo Eléctrico.
    Incluye Inline de Mediciones, acciones personalizadas, optimización de FK y scoping.
    """
    list_display = (
        'nombre',
        'codigo_inventario',
        'zona',
        'organizacion_zona',
        'categoria',
        'potencia_nominal_kw',
        'estado',
        'fecha_instalacion'
    )
    search_fields = ('nombre', 'codigo_inventario', 'zona__nombre', 'zona__organizacion__nombre')
    list_filter = ('estado', 'categoria', 'zona__organizacion')
    ordering = ('zona__organizacion__nombre', 'nombre')
    list_select_related = ('zona', 'categoria', 'zona__organizacion')
    inlines = [RegistroConsumoInline]
    actions = ['marcar_en_mantenimiento', 'marcar_como_activo', 'desactivar_dispositivos']

    @admin.display(description="Organización")
    def organizacion_zona(self, obj):
        return obj.zona.organizacion.nombre

    # --------------------------------------------------------------------------
    # ACCIONES PERSONALIZADAS (Admin Pro)
    # --------------------------------------------------------------------------
    @admin.action(description="Marcar dispositivos seleccionados: EN MANTENIMIENTO")
    def marcar_en_mantenimiento(self, request, queryset):
        actualizados = queryset.update(estado='MANTENIMIENTO')
        self.message_user(
            request,
            f"Se cambiaron {actualizados} dispositivo(s) a estado 'En Mantenimiento'.",
            messages.SUCCESS
        )

    @admin.action(description="Marcar dispositivos seleccionados: ACTIVO")
    def marcar_como_activo(self, request, queryset):
        actualizados = queryset.update(estado='ACTIVO')
        self.message_user(
            request,
            f"Se cambiaron {actualizados} dispositivo(s) a estado 'Activo'.",
            messages.SUCCESS
        )

    @admin.action(description="Marcar dispositivos seleccionados: INACTIVO")
    def desactivar_dispositivos(self, request, queryset):
        actualizados = queryset.update(estado='INACTIVO')
        self.message_user(
            request,
            f"Se desactivaron {actualizados} dispositivo(s).",
            messages.WARNING
        )

    # --------------------------------------------------------------------------
    # SEGURIDAD Y SCOPING POR ORGANIZACIÓN
    # --------------------------------------------------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        org = get_user_org(request)
        if org:
            return qs.filter(zona__organizacion=org)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        org = get_user_org(request)
        if org:
            if db_field.name == "zona":
                kwargs["queryset"] = Zona.objects.filter(organizacion=org)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            org = get_user_org(request)
            if org and obj.zona.organizacion_id != org.id:
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            org = get_user_org(request)
            if org and obj.zona.organizacion_id != org.id:
                return False
        return super().has_delete_permission(request, obj)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    """
    Administración de perfiles y asignación de organizaciones a usuarios.
    Reservado prioritariamente al superadministrador.
    """
    list_display = ('user', 'rol', 'organizacion', 'telefono')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'organizacion__nombre')
    list_filter = ('rol', 'organizacion')
    ordering = ('user__username',)
    list_select_related = ('user', 'organizacion')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        org = get_user_org(request)
        if org:
            return qs.filter(organizacion=org)
        return qs


# ==============================================================================
# MODELADMINS - TABLAS OPERATIVAS
# ==============================================================================

@admin.register(RegistroConsumo)
class RegistroConsumoAdmin(admin.ModelAdmin):
    """
    Tabla Operativa 1: Registros de telemetría y lecturas de consumo eléctrico.
    Configura columnas, búsqueda, filtros, ordenamiento, optimización FK y scoping.
    """
    list_display = (
        'dispositivo',
        'zona_dispositivo',
        'organizacion_dispositivo',
        'consumo_kwh',
        'voltaje_promedio',
        'fecha_hora',
        'observacion'
    )
    search_fields = (
        'dispositivo__nombre',
        'dispositivo__codigo_inventario',
        'dispositivo__zona__nombre',
        'observacion'
    )
    list_filter = ('fecha_hora', 'dispositivo__zona__organizacion', 'dispositivo__categoria')
    ordering = ('-fecha_hora',)
    list_select_related = ('dispositivo', 'dispositivo__zona', 'dispositivo__zona__organizacion')

    @admin.display(description="Zona")
    def zona_dispositivo(self, obj):
        return obj.dispositivo.zona.nombre

    @admin.display(description="Organización")
    def organizacion_dispositivo(self, obj):
        return obj.dispositivo.zona.organizacion.nombre

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        org = get_user_org(request)
        if org:
            return qs.filter(dispositivo__zona__organizacion=org)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        org = get_user_org(request)
        if org:
            if db_field.name == "dispositivo":
                kwargs["queryset"] = Dispositivo.objects.filter(zona__organizacion=org)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            org = get_user_org(request)
            if org and obj.dispositivo.zona.organizacion_id != org.id:
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            org = get_user_org(request)
            if org and obj.dispositivo.zona.organizacion_id != org.id:
                return False
        return super().has_delete_permission(request, obj)


@admin.register(AlertaConsumo)
class AlertaConsumoAdmin(admin.ModelAdmin):
    """
    Tabla Operativa 2: Alertas e Incidencias operacionales.
    Incluye acción personalizada para resolución en lote, optimización FK y scoping.
    """
    list_display = (
        'dispositivo',
        'zona_dispositivo',
        'organizacion_dispositivo',
        'nivel',
        'mensaje_resumen',
        'resuelta',
        'fecha_hora',
        'resuelta_en'
    )
    search_fields = ('dispositivo__nombre', 'mensaje', 'dispositivo__zona__nombre')
    list_filter = ('resuelta', 'nivel', 'fecha_hora', 'dispositivo__zona__organizacion')
    ordering = ('-fecha_hora',)
    list_select_related = ('dispositivo', 'dispositivo__zona', 'dispositivo__zona__organizacion')
    actions = ['marcar_como_resueltas']

    @admin.display(description="Zona")
    def zona_dispositivo(self, obj):
        return obj.dispositivo.zona.nombre

    @admin.display(description="Organización")
    def organizacion_dispositivo(self, obj):
        return obj.dispositivo.zona.organizacion.nombre

    @admin.display(description="Detalle Alerta")
    def mensaje_resumen(self, obj):
        return (obj.mensaje[:50] + '...') if len(obj.mensaje) > 50 else obj.mensaje

    # --------------------------------------------------------------------------
    # ACCIÓN PERSONALIZADA (Admin Pro)
    # --------------------------------------------------------------------------
    @admin.action(description="Marcar alertas seleccionadas como RESUELTAS")
    def marcar_como_resueltas(self, request, queryset):
        ahora = timezone.now()
        actualizadas = queryset.filter(resuelta=False).update(resuelta=True, resuelta_en=ahora)
        self.message_user(
            request,
            f"Se marcaron {actualizadas} alerta(s) como resueltas exitosamente.",
            messages.SUCCESS
        )

    # --------------------------------------------------------------------------
    # SEGURIDAD Y SCOPING POR ORGANIZACIÓN
    # --------------------------------------------------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        org = get_user_org(request)
        if org:
            return qs.filter(dispositivo__zona__organizacion=org)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        org = get_user_org(request)
        if org:
            if db_field.name == "dispositivo":
                kwargs["queryset"] = Dispositivo.objects.filter(zona__organizacion=org)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            org = get_user_org(request)
            if org and obj.dispositivo.zona.organizacion_id != org.id:
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            org = get_user_org(request)
            if org and obj.dispositivo.zona.organizacion_id != org.id:
                return False
        return super().has_delete_permission(request, obj)
