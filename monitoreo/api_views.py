from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Device
from .serializers import DeviceSerializer
from .permissions import AccesoRecursoPorRol


class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet REST para el recurso Device, protegido según los estándares de la Unidad 3:
    1. Autenticación: JWTAuthentication (Token Bearer en header Authorization).
    2. Autorización: IsAuthenticated + AccesoRecursoPorRol (AdministradorAPI vs OperadorAPI).
    3. Alcance (Scoping): get_queryset() filtra los dispositivos por la organización del usuario autenticado.
    4. Borrado Lógico: perform_destroy() ejecuta SoftDeleteModel.delete().
    """
    serializer_class = DeviceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, AccesoRecursoPorRol]

    def get_queryset(self):
        """
        Aplica scoping multi-empresa (Slide 12):
        - Superusuarios y Administradores Globales ven todos los registros.
        - Usuarios pertenecientes a una organización solo consultan sus propios dispositivos.
        """
        user = self.request.user
        qs = Device.objects.all().order_by("id")
        if user.is_authenticated and not user.is_superuser:
            profile = getattr(user, 'profile', None)
            if profile and profile.organization:
                qs = qs.filter(zone__organization=profile.organization)
        return qs

    def perform_destroy(self, instance):
        """
        Aplica borrado lógico mediante deleted_at sin destruir físicamente el registro.
        """
        instance.delete()
