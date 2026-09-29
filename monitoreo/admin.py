from django.contrib import admin, messages
from django.utils import timezone
from .models import (
    Organization,
    DeviceCategory,
    Supplier,
    EnergyTariff,
    Zone,
    Device,
    ConsumptionRecord,
    EnergyAlert,
    MaintenanceOrder,
    MonthlyZoneBudget,
)


def get_user_organization(request):
    """
    Retorna la Organización asignada al usuario a través de su perfil (accounts.UserProfile).
    Retorna None si el usuario es superusuario o no posee organización asociada (acceso global).
    """
    if request.user.is_superuser:
        return None
    profile = getattr(request.user, 'profile', None)
    if profile and profile.organization:
        return profile.organization
    return None


# ==============================================================================
# INLINES
# ==============================================================================

class DeviceInline(admin.TabularInline):
    model = Device
    extra = 0
    fields = ('name', 'serial_number', 'category', 'nominal_power_kw', 'status')
    show_change_link = True


class ConsumptionRecordInline(admin.TabularInline):
    model = ConsumptionRecord
    extra = 0
    fields = ('recorded_at', 'consumption_kwh', 'average_voltage', 'notes')
    readonly_fields = ('recorded_at',)
    can_delete = False
    max_num = 5


class MaintenanceOrderInline(admin.TabularInline):
    model = MaintenanceOrder
    extra = 0
    fields = ('title', 'scheduled_date', 'status', 'cost')
    show_change_link = True


# ==============================================================================
# TABLAS MAESTRAS (ADMIN)
# ==============================================================================

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'tax_id', 'contact_email', 'phone', 'is_active', 'created_at', 'deleted_at')
    search_fields = ('name', 'tax_id', 'contact_email')
    list_filter = ('is_active', 'created_at')
    ordering = ('name',)

    def get_queryset(self, request):
        qs = Organization.all_objects.all()
        org = get_user_organization(request)
        if org:
            return qs.filter(id=org.id)
        return qs


@admin.register(DeviceCategory)
class DeviceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short', 'is_critical', 'devices_count', 'deleted_at')
    search_fields = ('name', 'description')
    list_filter = ('is_critical',)
    ordering = ('name',)

    def get_queryset(self, request):
        return DeviceCategory.all_objects.all()

    @admin.display(description="Descripción")
    def description_short(self, obj):
        return (obj.description[:50] + '...') if len(obj.description) > 50 else obj.description

    @admin.display(description="Equipos Asociados")
    def devices_count(self, obj):
        return obj.devices.count()


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'contract_number', 'deleted_at')
    search_fields = ('name', 'contact_person', 'contract_number')
    ordering = ('name',)

    def get_queryset(self, request):
        return Supplier.all_objects.all()


@admin.register(EnergyTariff)
class EnergyTariffAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'cost_per_kwh', 'peak_cost_per_kwh', 'currency', 'is_active', 'deleted_at')
    search_fields = ('name', 'organization__name')
    list_filter = ('is_active', 'organization')
    ordering = ('organization__name', 'name')
    list_select_related = ('organization',)

    def get_queryset(self, request):
        qs = EnergyTariff.all_objects.all()
        org = get_user_organization(request)
        if org:
            return qs.filter(organization=org)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        org = get_user_organization(request)
        if org and db_field.name == "organization":
            kwargs["queryset"] = Organization.objects.filter(id=org.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'monthly_limit_kwh', 'floor_area_sqm', 'responsible_person', 'is_active', 'deleted_at')
    search_fields = ('name', 'responsible_person', 'organization__name')
    list_filter = ('is_active', 'organization')
    ordering = ('organization__name', 'name')
    list_select_related = ('organization',)
    inlines = [DeviceInline]

    def get_queryset(self, request):
        qs = Zone.all_objects.all()
        org = get_user_organization(request)
        if org:
            return qs.filter(organization=org)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        org = get_user_organization(request)
        if org and db_field.name == "organization":
            kwargs["queryset"] = Organization.objects.filter(id=org.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        org = get_user_organization(request)
        if org and not request.user.is_superuser:
            obj.organization = org
        super().save_model(request, obj, form, change)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'serial_number', 'zone', 'organization_name', 'category', 'nominal_power_kw', 'status', 'deleted_at')
    search_fields = ('name', 'serial_number', 'zone__name', 'zone__organization__name')
    list_filter = ('status', 'category', 'zone__organization')
    ordering = ('zone__organization__name', 'name')
    list_select_related = ('zone', 'zone__organization', 'category', 'supplier')
    inlines = [ConsumptionRecordInline, MaintenanceOrderInline]
    actions = ['mark_in_maintenance', 'mark_active', 'soft_delete_selected']

    @admin.display(description="Organización")
    def organization_name(self, obj):
        return obj.zone.organization.name

    @admin.action(description="Marcar seleccionados: EN MANTENIMIENTO")
    def mark_in_maintenance(self, request, queryset):
        count = queryset.update(status='MAINTENANCE')
        self.message_user(request, f"{count} dispositivo(s) puesto(s) en mantenimiento.", messages.SUCCESS)

    @admin.action(description="Marcar seleccionados: ACTIVO")
    def mark_active(self, request, queryset):
        count = queryset.update(status='ACTIVE')
        self.message_user(request, f"{count} dispositivo(s) activado(s).", messages.SUCCESS)

    @admin.action(description="Borrado lógico de elementos seleccionados")
    def soft_delete_selected(self, request, queryset):
        count = queryset.update(deleted_at=timezone.now())
        self.message_user(request, f"{count} dispositivo(s) marcado(s) como eliminados lógicamente.", messages.WARNING)

    def get_queryset(self, request):
        qs = Device.all_objects.all()
        org = get_user_organization(request)
        if org:
            return qs.filter(zone__organization=org)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        org = get_user_organization(request)
        if org and db_field.name == "zone":
            kwargs["queryset"] = Zone.objects.filter(organization=org)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ==============================================================================
# TABLAS OPERACIONALES (ADMIN)
# ==============================================================================

@admin.register(ConsumptionRecord)
class ConsumptionRecordAdmin(admin.ModelAdmin):
    list_display = ('device', 'zone_name', 'organization_name', 'consumption_kwh', 'average_voltage', 'recorded_at', 'deleted_at')
    search_fields = ('device__name', 'device__serial_number', 'notes')
    list_filter = ('recorded_at', 'device__zone__organization', 'device__category')
    ordering = ('-recorded_at',)
    list_select_related = ('device', 'device__zone', 'device__zone__organization')

    @admin.display(description="Zona")
    def zone_name(self, obj):
        return obj.device.zone.name

    @admin.display(description="Organización")
    def organization_name(self, obj):
        return obj.device.zone.organization.name

    def get_queryset(self, request):
        qs = ConsumptionRecord.all_objects.all()
        org = get_user_organization(request)
        if org:
            return qs.filter(device__zone__organization=org)
        return qs


@admin.register(EnergyAlert)
class EnergyAlertAdmin(admin.ModelAdmin):
    list_display = ('device', 'severity', 'message_short', 'is_resolved', 'triggered_at', 'resolved_at', 'deleted_at')
    search_fields = ('device__name', 'message')
    list_filter = ('is_resolved', 'severity', 'triggered_at', 'device__zone__organization')
    ordering = ('-triggered_at',)
    list_select_related = ('device', 'device__zone', 'device__zone__organization')
    actions = ['resolve_alerts']

    @admin.display(description="Detalle Alerta")
    def message_short(self, obj):
        return (obj.message[:50] + '...') if len(obj.message) > 50 else obj.message

    @admin.action(description="Marcar alertas seleccionadas como RESUELTAS")
    def resolve_alerts(self, request, queryset):
        count = queryset.filter(is_resolved=False).update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f"{count} alerta(s) resuelta(s) exitosamente.", messages.SUCCESS)

    def get_queryset(self, request):
        qs = EnergyAlert.all_objects.all()
        org = get_user_organization(request)
        if org:
            return qs.filter(device__zone__organization=org)
        return qs


@admin.register(MaintenanceOrder)
class MaintenanceOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'device', 'scheduled_date', 'status', 'cost', 'deleted_at')
    search_fields = ('title', 'device__name', 'technician_notes')
    list_filter = ('status', 'scheduled_date', 'device__zone__organization')
    ordering = ('-scheduled_date',)
    list_select_related = ('device', 'device__zone', 'device__zone__organization')

    def get_queryset(self, request):
        qs = MaintenanceOrder.all_objects.all()
        org = get_user_organization(request)
        if org:
            return qs.filter(device__zone__organization=org)
        return qs


@admin.register(MonthlyZoneBudget)
class MonthlyZoneBudgetAdmin(admin.ModelAdmin):
    list_display = ('zone', 'year', 'month', 'budgeted_kwh', 'actual_kwh', 'is_closed', 'deleted_at')
    search_fields = ('zone__name', 'zone__organization__name')
    list_filter = ('year', 'month', 'is_closed', 'zone__organization')
    ordering = ('-year', '-month')
    list_select_related = ('zone', 'zone__organization')

    def get_queryset(self, request):
        qs = MonthlyZoneBudget.all_objects.all()
        org = get_user_organization(request)
        if org:
            return qs.filter(zone__organization=org)
        return qs
