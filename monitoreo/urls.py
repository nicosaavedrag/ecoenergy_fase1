from django.urls import path
from . import views

urlpatterns = [
    path('zonas/', views.lista_zonas, name='lista_zonas'),
    path('zonas/<int:zona_id>/', views.detalle_zona, name='detalle_zona'),
]