from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # CRUD 1: Zonas
    path('zones/', views.zone_list, name='zone_list'),
    path('zones/new/', views.zone_create, name='zone_create'),
    path('zones/<int:pk>/edit/', views.zone_edit, name='zone_edit'),
    path('zones/<int:pk>/delete/', views.zone_delete, name='zone_delete'),

    # CRUD 2: Dispositivos
    path('devices/', views.device_list, name='device_list'),
    path('devices/new/', views.device_create, name='device_create'),
    path('devices/<int:pk>/edit/', views.device_edit, name='device_edit'),
    path('devices/<int:pk>/delete/', views.device_delete, name='device_delete'),

    # CRUD 3: Mediciones de Consumo + Exportación Excel
    path('consumption/', views.consumption_list, name='consumption_list'),
    path('consumption/new/', views.consumption_create, name='consumption_create'),
    path('consumption/<int:pk>/edit/', views.consumption_edit, name='consumption_edit'),
    path('consumption/<int:pk>/delete/', views.consumption_delete, name='consumption_delete'),

    # CRUD 4: Alertas de Consumo
    path('alerts/', views.alert_list, name='alert_list'),
    path('alerts/new/', views.alert_create, name='alert_create'),
    path('alerts/<int:pk>/resolve/', views.alert_resolve, name='alert_resolve'),
    path('alerts/<int:pk>/delete/', views.alert_delete, name='alert_delete'),

    # Cliente Interactivo Demo API REST (Unidad 3 - JWT y CRUD)
    path('api-demo/', views.api_demo_client, name='api_demo_client'),
]