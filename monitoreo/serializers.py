from rest_framework import serializers
from .models import Device, Zone, DeviceCategory, Supplier


class DeviceSerializer(serializers.ModelSerializer):
    """
    Serializer para el recurso Device (Dispositivo) en la API REST de EcoEnergy.
    - Campos explícitos publicables.
    - ID de solo lectura (generado por la BD).
    - Validación de regla de negocio energética: potencia > 0 para equipos activos.
    """
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Device
        fields = [
            'id',
            'name',
            'serial_number',
            'nominal_power_kw',
            'status',
            'zone',
            'zone_name',
            'category',
            'category_name',
            'supplier',
            'installation_date',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        """
        Validación de dominio: Un dispositivo activo debe registrar una potencia nominal mayor a 0 kW.
        Retorna HTTP 400 Bad Request si la condición no se cumple.
        """
        status = attrs.get('status', getattr(self.instance, 'status', 'ACTIVE'))
        power = attrs.get('nominal_power_kw', getattr(self.instance, 'nominal_power_kw', None))

        if status == 'ACTIVE' and (power is None or power <= 0):
            raise serializers.ValidationError({
                'nominal_power_kw': 'Un dispositivo activo debe registrar una potencia nominal mayor a 0 kW.'
            })
        return attrs
