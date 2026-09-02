from django.urls import path
from . import views

urlpatterns = [
    # Rutas originales de la Fase 1
    path('zonas/', views.lista_zonas, name='lista_zonas'),
    path('zonas/<int:zona_id>/', views.detalle_zona, name='detalle_zona'),
    
    # Ruta nueva de la Fase 2 (Tal como pide el PDF)
    path('resumen-zonas/', views.resumen_zonas, name='resumen_zonas'),
]