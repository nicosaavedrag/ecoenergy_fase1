import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.http import HttpResponse
from django.utils import timezone
from .models import ConsumptionRecord


def export_consumption_records_xlsx(queryset, filename_prefix="reporte_consumo"):
    """
    Genera un archivo Excel (.xlsx) nativo utilizando openpyxl a partir de un QuerySet
    de ConsumptionRecord, respetando scoping y borrado lógico.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Consumo Energético"

    # Estilos visuales
    header_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='E0E0E0'),
        right=Side(style='thin', color='E0E0E0'),
        top=Side(style='thin', color='E0E0E0'),
        bottom=Side(style='thin', color='E0E0E0')
    )

    # Encabezados
    headers = [
        "ID Medición",
        "Dispositivo",
        "N° de Serie",
        "Zona",
        "Organización",
        "Fecha y Hora",
        "Consumo (kWh)",
        "Voltaje Promedio (V)",
        "Observaciones"
    ]
    ws.append(headers)

    # Formato a la fila de encabezados
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center

    # Datos
    for record in queryset.select_related('device', 'device__zone', 'device__zone__organization'):
        row = [
            record.id,
            record.device.name,
            record.device.serial_number,
            record.device.zone.name,
            record.device.zone.organization.name,
            record.recorded_at.strftime('%Y-%m-%d %H:%M'),
            float(record.consumption_kwh),
            float(record.average_voltage) if record.average_voltage else None,
            record.notes or ""
        ]
        ws.append(row)
        current_row = ws.max_row
        for c_idx in range(1, len(row) + 1):
            c = ws.cell(row=current_row, column=c_idx)
            c.font = data_font
            c.border = thin_border
            if c_idx in [1, 6]:
                c.alignment = align_center
            elif c_idx in [7, 8]:
                c.alignment = align_right
            else:
                c.alignment = align_left

    # Autoajuste del ancho de columnas
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # Respuesta HTTP descargable
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{filename_prefix}_{timestamp}.xlsx"

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
