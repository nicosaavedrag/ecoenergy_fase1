from rest_framework.permissions import BasePermission, SAFE_METHODS


class AccesoRecursoPorRol(BasePermission):
    """
    Control de autorización basado en grupos de Django y métodos HTTP:
    - Superusuario o grupo 'AdministradorAPI': Permiso completo (GET, POST, PATCH, PUT, DELETE).
    - Grupo 'OperadorAPI': Solo métodos seguros de lectura (GET, HEAD, OPTIONS).
    - Usuarios sin grupo o con otro rol: Acceso denegado (HTTP 403 Forbidden).
    """
    message = "Tu rol no permite esta operación."

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if user.groups.filter(name="AdministradorAPI").exists():
            return True
        if request.method in SAFE_METHODS:
            return user.groups.filter(name="OperadorAPI").exists()
        return False
