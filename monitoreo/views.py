from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q

from accounts.models import UserProfile
from .models import (
    Organization,
    Zone,
    Device,
    ConsumptionRecord,
    EnergyAlert,
    MaintenanceOrder,
    MonthlyZoneBudget,
)
from .forms import ZoneForm, DeviceForm, ConsumptionRecordForm, EnergyAlertForm
from .exports import export_consumption_records_xlsx


# ==============================================================================
# HELPERS DE SEGURIDAD, SCOPING Y SESIÓN
# ==============================================================================

def get_user_org(request):
    """Retorna la Organización asignada al usuario o None si tiene acceso global."""
    if request.user.is_superuser:
        return None
    profile = getattr(request.user, 'profile', None)
    return profile.organization if profile else None


def user_can_edit(request):
    """Verifica si el usuario tiene rol de Administrador u Operador para realizar cambios."""
    if request.user.is_superuser:
        return True
    profile = getattr(request.user, 'profile', None)
    return profile is not None and profile.role in ['ADMIN', 'OPERATOR']


def get_session_page_size(request, default=15):
    """
    Gestiona la paginación con persistencia en request.session.
    Acepta únicamente 5, 15 o 30 registros por página, normalizando cualquier otro valor.
    """
    allowed_sizes = [5, 15, 30]
    param = request.GET.get('page_size')
    if param is not None:
        try:
            val = int(param)
            if val in allowed_sizes:
                request.session['page_size'] = val
        except (ValueError, TypeError):
            pass

    size = request.session.get('page_size', default)
    return size if size in allowed_sizes else default


# ==============================================================================
# DASHBOARD PRINCIPAL
# ==============================================================================

@login_required
def dashboard(request):
    org = get_user_org(request)
    zones_qs = Zone.objects.filter(organization=org) if org else Zone.objects.all()
    devices_qs = Device.objects.filter(zone__organization=org) if org else Device.objects.all()
    records_qs = ConsumptionRecord.objects.filter(device__zone__organization=org) if org else ConsumptionRecord.objects.all()
    alerts_qs = EnergyAlert.objects.filter(device__zone__organization=org) if org else EnergyAlert.objects.all()

    total_kwh = records_qs.aggregate(total=Sum('consumption_kwh'))['total'] or Decimal("0.00")
    active_alerts_count = alerts_qs.filter(is_resolved=False).count()

    context = {
        'total_zones': zones_qs.count(),
        'total_devices': devices_qs.count(),
        'total_consumption_kwh': round(total_kwh, 2),
        'active_alerts_count': active_alerts_count,
        'recent_alerts': alerts_qs.select_related('device', 'device__zone')[:5],
        'recent_records': records_qs.select_related('device', 'device__zone')[:8],
        'user_org': org,
    }
    return render(request, 'monitoreo/dashboard.html', context)


# ==============================================================================
# CRUD 1: ZONAS (Zone)
# ==============================================================================

@login_required
def zone_list(request):
    org = get_user_org(request)
    qs = Zone.objects.filter(organization=org) if org else Zone.objects.all()
    qs = qs.select_related('organization').annotate(devices_count=Count('devices', filter=Q(devices__deleted_at__isnull=True)))

    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(Q(name__icontains=search_query) | Q(responsible_person__icontains=search_query))

    qs = qs.order_by('name')

    page_size = get_session_page_size(request, default=15)
    paginator = Paginator(qs, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'monitoreo/zones/zone_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'page_size': page_size,
        'can_edit': user_can_edit(request),
    })


@login_required
def zone_create(request):
    if not user_can_edit(request):
        return HttpResponseForbidden("No tiene permisos para crear zonas.")

    org = get_user_org(request)
    if request.method == 'POST':
        form = ZoneForm(request.POST, user_org=org)
        if form.is_valid():
            zone = form.save(commit=False)
            if org and not request.user.is_superuser:
                zone.organization = org
            zone.save()
            messages.success(request, f"Zona '{zone.name}' creada exitosamente.")
            return redirect('zone_list')
    else:
        form = ZoneForm(user_org=org)

    return render(request, 'monitoreo/zones/zone_form.html', {'form': form, 'title': 'Nueva Zona'})


@login_required
def zone_edit(request, pk):
    if not user_can_edit(request):
        return HttpResponseForbidden("No tiene permisos para editar zonas.")

    org = get_user_org(request)
    zone = get_object_or_404(Zone, pk=pk)
    if org and zone.organization_id != org.id:
        return HttpResponseForbidden("Acceso denegado: la zona pertenece a otra organización.")

    if request.method == 'POST':
        form = ZoneForm(request.POST, instance=zone, user_org=org)
        if form.is_valid():
            form.save()
            messages.success(request, f"Zona '{zone.name}' actualizada con éxito.")
            return redirect('zone_list')
    else:
        form = ZoneForm(instance=zone, user_org=org)

    return render(request, 'monitoreo/zones/zone_form.html', {'form': form, 'title': f'Editar Zona: {zone.name}', 'zone': zone})


@login_required
def zone_delete(request, pk):
    """Eliminación lógica protegida mediante POST y CSRF."""
    if not user_can_edit(request):
        return HttpResponseForbidden("No tiene permisos para eliminar registros.")

    if request.method != 'POST':
        return HttpResponseForbidden("Método no permitido. La eliminación debe enviarse mediante POST.")

    org = get_user_org(request)
    zone = get_object_or_404(Zone, pk=pk)
    if org and zone.organization_id != org.id:
        return HttpResponseForbidden("Acceso denegado: la zona pertenece a otra organización.")

    zone_name = zone.name
    zone.delete()  # Soft delete
    messages.success(request, f"Zona '{zone_name}' eliminada lógicamente del sistema.")
    return redirect('zone_list')


# ==============================================================================
# CRUD 2: DISPOSITIVOS (Device) - CON IMAGEN Y PILLOW
# ==============================================================================

@login_required
def device_list(request):
    org = get_user_org(request)
    qs = Device.objects.filter(zone__organization=org) if org else Device.objects.all()
    qs = qs.select_related('zone', 'zone__organization', 'category', 'supplier')

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        qs = qs.filter(status=status_filter)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(Q(name__icontains=search_query) | Q(serial_number__icontains=search_query) | Q(zone__name__icontains=search_query))

    page_size = get_session_page_size(request, default=15)
    paginator = Paginator(qs, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'monitoreo/devices/device_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'page_size': page_size,
        'can_edit': user_can_edit(request),
    })


@login_required
def device_create(request):
    if not user_can_edit(request):
        return HttpResponseForbidden("No tiene permisos para registrar dispositivos.")

    org = get_user_org(request)
    if request.method == 'POST':
        form = DeviceForm(request.POST, request.FILES, user_org=org)
        if form.is_valid():
            device = form.save()
            messages.success(request, f"Dispositivo '{device.name}' registrado exitosamente.")
            return redirect('device_list')
    else:
        form = DeviceForm(user_org=org)

    return render(request, 'monitoreo/devices/device_form.html', {'form': form, 'title': 'Nuevo Dispositivo'})


@login_required
def device_edit(request, pk):
    if not user_can_edit(request):
        return HttpResponseForbidden("No tiene permisos para modificar dispositivos.")

    org = get_user_org(request)
    device = get_object_or_404(Device, pk=pk)
    if org and device.zone.organization_id != org.id:
        return HttpResponseForbidden("Acceso denegado: el dispositivo pertenece a otra organización.")

    if request.method == 'POST':
        form = DeviceForm(request.POST, request.FILES, instance=device, user_org=org)
        if form.is_valid():
            form.save()
            messages.success(request, f"Dispositivo '{device.name}' actualizado correctamente.")
            return redirect('device_list')
    else:
        form = DeviceForm(instance=device, user_org=org)

    return render(request, 'monitoreo/devices/device_form.html', {'form': form, 'title': f'Editar Dispositivo: {device.name}', 'device': device})


@login_required
def device_delete(request, pk):
    if not user_can_edit(request):
        return HttpResponseForbidden("No tiene permisos para eliminar dispositivos.")

    if request.method != 'POST':
        return HttpResponseForbidden("Método no permitido.")

    org = get_user_org(request)
    device = get_object_or_404(Device, pk=pk)
    if org and device.zone.organization_id != org.id:
        return HttpResponseForbidden("Acceso denegado.")

    dev_name = device.name
    device.delete()  # Soft delete
    messages.success(request, f"Dispositivo '{dev_name}' eliminado lógicamente.")
    return redirect('device_list')


# ==============================================================================
# CRUD 3: REGISTROS DE CONSUMO (ConsumptionRecord) + EXCEL
# ==============================================================================

@login_required
def consumption_list(request):
    org = get_user_org(request)
    qs = ConsumptionRecord.objects.filter(device__zone__organization=org) if org else ConsumptionRecord.objects.all()
    qs = qs.select_related('device', 'device__zone', 'device__zone__organization')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(Q(device__name__icontains=search_query) | Q(device__serial_number__icontains=search_query) | Q(notes__icontains=search_query))

    # Exportación a Excel
    if request.GET.get('export') == 'xlsx':
        return export_consumption_records_xlsx(qs, filename_prefix="consumo_ecoenergy")

    page_size = get_session_page_size(request, default=15)
    paginator = Paginator(qs, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'monitoreo/consumption/consumption_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'page_size': page_size,
        'can_edit': user_can_edit(request),
    })


@login_required
def consumption_create(request):
    if not user_can_edit(request):
        return HttpResponseForbidden("No tiene permisos para registrar consumos.")

    org = get_user_org(request)
    if request.method == 'POST':
        form = ConsumptionRecordForm(request.POST, user_org=org)
        if form.is_valid():
            rec = form.save()
            messages.success(request, f"Medición de {rec.consumption_kwh} kWh registrada correctamente.")
            return redirect('consumption_list')
    else:
        form = ConsumptionRecordForm(user_org=org, initial={'recorded_at': timezone.now().strftime('%Y-%m-%dT%H:%M')})

    return render(request, 'monitoreo/consumption/consumption_form.html', {'form': form, 'title': 'Registrar Medición de Consumo'})


@login_required
def consumption_edit(request, pk):
    if not user_can_edit(request):
        return HttpResponseForbidden("No tiene permisos para modificar registros de consumo.")

    org = get_user_org(request)
    rec = get_object_or_404(ConsumptionRecord, pk=pk)
    if org and rec.device.zone.organization_id != org.id:
        return HttpResponseForbidden("Acceso denegado.")

    if request.method == 'POST':
        form = ConsumptionRecordForm(request.POST, instance=rec, user_org=org)
        if form.is_valid():
            form.save()
            messages.success(request, "Medición actualizada correctamente.")
            return redirect('consumption_list')
    else:
        form = ConsumptionRecordForm(instance=rec, user_org=org)

    return render(request, 'monitoreo/consumption/consumption_form.html', {'form': form, 'title': 'Editar Medición de Consumo', 'record': rec})


@login_required
def consumption_delete(request, pk):
    if not user_can_edit(request):
        return HttpResponseForbidden("No tiene permisos para eliminar registros.")

    if request.method != 'POST':
        return HttpResponseForbidden("Método no permitido.")

    org = get_user_org(request)
    rec = get_object_or_404(ConsumptionRecord, pk=pk)
    if org and rec.device.zone.organization_id != org.id:
        return HttpResponseForbidden("Acceso denegado.")

    rec.delete()
    messages.success(request, "Registro de consumo eliminado lógicamente.")
    return redirect('consumption_list')


# ==============================================================================
# CRUD 4: ALERTAS DE CONSUMO (EnergyAlert)
# ==============================================================================

@login_required
def alert_list(request):
    org = get_user_org(request)
    qs = EnergyAlert.objects.filter(device__zone__organization=org) if org else EnergyAlert.objects.all()
    qs = qs.select_related('device', 'device__zone', 'device__zone__organization')

    severity = request.GET.get('severity', '').strip()
    if severity:
        qs = qs.filter(severity=severity)

    resolved_param = request.GET.get('resolved', '').strip()
    if resolved_param in ['0', 'false']:
        qs = qs.filter(is_resolved=False)
    elif resolved_param in ['1', 'true']:
        qs = qs.filter(is_resolved=True)

    page_size = get_session_page_size(request, default=15)
    paginator = Paginator(qs, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'monitoreo/alerts/alert_list.html', {
        'page_obj': page_obj,
        'severity': severity,
        'resolved_param': resolved_param,
        'page_size': page_size,
        'can_edit': user_can_edit(request),
    })


@login_required
def alert_create(request):
    if not user_can_edit(request):
        return HttpResponseForbidden("No tiene permisos para crear alertas.")

    org = get_user_org(request)
    if request.method == 'POST':
        form = EnergyAlertForm(request.POST, user_org=org)
        if form.is_valid():
            al = form.save()
            messages.success(request, "Alerta registrada correctamente.")
            return redirect('alert_list')
    else:
        form = EnergyAlertForm(user_org=org)

    return render(request, 'monitoreo/alerts/alert_form.html', {'form': form, 'title': 'Registrar Alerta Manual'})


@login_required
def alert_resolve(request, pk):
    """Acción rápida para marcar una alerta como resuelta."""
    if not user_can_edit(request):
        return HttpResponseForbidden("No tiene permisos para modificar alertas.")

    if request.method != 'POST':
        return HttpResponseForbidden("Método no permitido.")

    org = get_user_org(request)
    alert = get_object_or_404(EnergyAlert, pk=pk)
    if org and alert.device.zone.organization_id != org.id:
        return HttpResponseForbidden("Acceso denegado.")

    alert.is_resolved = True
    alert.resolved_at = timezone.now()
    alert.save()
    messages.success(request, f"Alerta #{alert.id} marcada como resuelta.")
    return redirect('alert_list')


@login_required
def alert_delete(request, pk):
    if not user_can_edit(request):
        return HttpResponseForbidden("No tiene permisos para eliminar alertas.")

    if request.method != 'POST':
        return HttpResponseForbidden("Método no permitido.")

    org = get_user_org(request)
    alert = get_object_or_404(EnergyAlert, pk=pk)
    if org and alert.device.zone.organization_id != org.id:
        return HttpResponseForbidden("Acceso denegado.")

    alert.delete()
    messages.success(request, f"Alerta #{alert.id} eliminada lógicamente.")
    return redirect('alert_list')
