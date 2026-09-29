from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Zone, Device, ConsumptionRecord, EnergyAlert, Organization


class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ['organization', 'name', 'monthly_limit_kwh', 'floor_area_sqm', 'responsible_person', 'is_active']
        widgets = {
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Planta de Producción B'}),
            'monthly_limit_kwh': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'floor_area_sqm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'responsible_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del supervisor'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user_org = kwargs.pop('user_org', None)
        super().__init__(*args, **kwargs)
        if user_org:
            self.fields['organization'].queryset = Organization.objects.filter(id=user_org.id)
            self.fields['organization'].initial = user_org
            self.fields['organization'].widget = forms.HiddenInput()


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['zone', 'category', 'supplier', 'name', 'serial_number', 'nominal_power_kw', 'status', 'installation_date', 'image']
        widgets = {
            'zone': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Torno CNC Haas'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. NOR-CNC-009'}),
            'nominal_power_kw': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'installation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': '.jpg,.jpeg,.png,.webp'}),
        }

    def __init__(self, *args, **kwargs):
        user_org = kwargs.pop('user_org', None)
        super().__init__(*args, **kwargs)
        if user_org:
            self.fields['zone'].queryset = Zone.objects.filter(organization=user_org)


class ConsumptionRecordForm(forms.ModelForm):
    class Meta:
        model = ConsumptionRecord
        fields = ['device', 'recorded_at', 'consumption_kwh', 'average_voltage', 'notes']
        widgets = {
            'device': forms.Select(attrs={'class': 'form-select'}),
            'recorded_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'consumption_kwh': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'average_voltage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Observaciones'}),
        }

    def __init__(self, *args, **kwargs):
        user_org = kwargs.pop('user_org', None)
        super().__init__(*args, **kwargs)
        if user_org:
            self.fields['device'].queryset = Device.objects.filter(zone__organization=user_org)


class EnergyAlertForm(forms.ModelForm):
    class Meta:
        model = EnergyAlert
        fields = ['device', 'severity', 'message', 'is_resolved']
        widgets = {
            'device': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalle de la anomalía...'}),
            'is_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user_org = kwargs.pop('user_org', None)
        super().__init__(*args, **kwargs)
        if user_org:
            self.fields['device'].queryset = Device.objects.filter(zone__organization=user_org)
