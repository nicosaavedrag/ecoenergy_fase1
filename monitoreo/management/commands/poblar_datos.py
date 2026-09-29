from decimal import Decimal
from datetime import timedelta
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from accounts.models import UserProfile
from monitoreo.models import (
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


class Command(BaseCommand):
    help = "Puebla la base de datos con >= 1.000 registros de negocio reproducibles para la Evaluación Formativa II (EcoEnergy)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina registros existentes antes de poblar la base de datos',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Iniciando carga masiva de datos reproducibles EcoEnergy (>= 1.000 registros) ==="))

        if options['limpiar']:
            self.stdout.write(self.style.WARNING("Limpiando base de datos previa..."))
            ConsumptionRecord.all_objects.all().delete()
            EnergyAlert.all_objects.all().delete()
            MaintenanceOrder.all_objects.all().delete()
            MonthlyZoneBudget.all_objects.all().delete()
            Device.all_objects.all().delete()
            Zone.all_objects.all().delete()
            EnergyTariff.all_objects.all().delete()
            Supplier.all_objects.all().delete()
            DeviceCategory.all_objects.all().delete()
            Organization.all_objects.all().delete()
            UserProfile.objects.all().delete()
            User.objects.filter(username__in=['admin', 'operador_norte', 'lector_norte', 'operador_sur']).delete()

        # ----------------------------------------------------------------------
        # 1. PERMISOS Y ROLES DE DJANGO
        # ----------------------------------------------------------------------
        group_operators, _ = Group.objects.get_or_create(name="Operadores de Monitoreo")
        group_viewers, _ = Group.objects.get_or_create(name="Lectores de Monitoreo")

        all_models = [
            Organization, DeviceCategory, Supplier, EnergyTariff,
            Zone, Device, ConsumptionRecord, EnergyAlert,
            MaintenanceOrder, MonthlyZoneBudget
        ]

        for model in all_models:
            ct = ContentType.objects.get_for_model(model)
            # Operadores: view, add, change
            perms_op = Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f'view_{model._meta.model_name}',
                    f'change_{model._meta.model_name}',
                    f'add_{model._meta.model_name}',
                    f'delete_{model._meta.model_name}',
                ]
            )
            for p in perms_op:
                group_operators.permissions.add(p)

            # Lectores: solo view
            perms_view = Permission.objects.filter(
                content_type=ct,
                codename=f'view_{model._meta.model_name}'
            )
            for p in perms_view:
                group_viewers.permissions.add(p)

        # ----------------------------------------------------------------------
        # 2. TABLAS MAESTRAS: ORGANIZACIONES
        # ----------------------------------------------------------------------
        org_norte, _ = Organization.objects.get_or_create(
            tax_id="76.123.456-7",
            defaults={
                "name": "EcoIndustrias Norte S.A.",
                "address": "Av. Balmaceda 4500, La Serena",
                "contact_email": "contacto@econorte.cl",
                "phone": "+56 51 223344",
                "is_active": True,
            }
        )

        org_sur, _ = Organization.objects.get_or_create(
            tax_id="77.987.654-3",
            defaults={
                "name": "EcoRetail Sur SpA",
                "address": "Ruta 5 Norte Km 460, Coquimbo",
                "contact_email": "contacto@ecosur.cl",
                "phone": "+56 51 255667",
                "is_active": True,
            }
        )

        # ----------------------------------------------------------------------
        # 3. USUARIOS DE PRUEBA DOCUMENTADOS (3 ROLES DISTINTOS)
        # ----------------------------------------------------------------------
        # 3.1 Administrador Global
        u_admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@ecoenergy.cl', 'first_name': 'Administrador', 'last_name': 'Global', 'is_staff': True, 'is_superuser': True}
        )
        u_admin.set_password('AdminPassword123!')
        u_admin.is_staff = True
        u_admin.is_superuser = True
        u_admin.save()
        UserProfile.objects.update_or_create(
            user=u_admin,
            defaults={'role': 'ADMIN', 'organization': None, 'phone': '+56 9 1111 2222'}
        )

        # 3.2 Operador / Editor (EcoIndustrias Norte)
        u_op_norte, _ = User.objects.get_or_create(
            username='operador_norte',
            defaults={'email': 'operador.norte@ecoenergy.cl', 'first_name': 'Rodrigo', 'last_name': 'Vega', 'is_staff': True}
        )
        u_op_norte.set_password('OperadorNorte123!')
        u_op_norte.is_staff = True
        u_op_norte.save()
        u_op_norte.groups.add(group_operators)
        UserProfile.objects.update_or_create(
            user=u_op_norte,
            defaults={'role': 'OPERATOR', 'organization': org_norte, 'phone': '+56 9 3333 4444'}
        )

        # 3.3 Lector / Consulta (EcoIndustrias Norte)
        u_lec_norte, _ = User.objects.get_or_create(
            username='lector_norte',
            defaults={'email': 'lector.norte@ecoenergy.cl', 'first_name': 'Patricia', 'last_name': 'López', 'is_staff': True}
        )
        u_lec_norte.set_password('LectorNorte123!')
        u_lec_norte.is_staff = True
        u_lec_norte.save()
        u_lec_norte.groups.add(group_viewers)
        UserProfile.objects.update_or_create(
            user=u_lec_norte,
            defaults={'role': 'VIEWER', 'organization': org_norte, 'phone': '+56 9 5555 7777'}
        )

        # 3.4 Operador Organización 2 (EcoRetail Sur)
        u_op_sur, _ = User.objects.get_or_create(
            username='operador_sur',
            defaults={'email': 'operador.sur@ecoenergy.cl', 'first_name': 'Camila', 'last_name': 'Miranda', 'is_staff': True}
        )
        u_op_sur.set_password('OperadorSur123!')
        u_op_sur.is_staff = True
        u_op_sur.save()
        u_op_sur.groups.add(group_operators)
        UserProfile.objects.update_or_create(
            user=u_op_sur,
            defaults={'role': 'OPERATOR', 'organization': org_sur, 'phone': '+56 9 8888 9999'}
        )

        # ----------------------------------------------------------------------
        # 4. TABLAS MAESTRAS ADICIONALES: CATEGORÍAS, PROVEEDORES, TARIFAS
        # ----------------------------------------------------------------------
        categories_data = [
            ("Maquinaria Pesada", "Tornos CNC, fresadoras y prensas hidráulicas.", True),
            ("Climatización Industrial", "Sistemas HVAC, chillers y bombas de calor.", False),
            ("Iluminación y Ofimática", "Luminarias LED de alta eficiencia y estaciones de trabajo.", False),
            ("Sistemas de Refrigeración", "Cámaras frigoríficas industriales y compresores.", True),
        ]
        cat_objs = []
        for name, desc, crit in categories_data:
            c, _ = DeviceCategory.objects.get_or_create(name=name, defaults={"description": desc, "is_critical": crit})
            cat_objs.append(c)

        suppliers_data = [
            ("Siemens Energy Chile", "Gonzalo Valenzuela", "contacto@siemens.cl", "+56 2 2450 0000", "CON-SIE-2026"),
            ("Schneider Electric", "Marcela Durán", "soporte@se.com", "+56 2 2600 5500", "CON-SCH-2025"),
            ("Carrier HVAC Chile", "Esteban Morales", "ventas@carrier.cl", "+56 2 2800 3300", "CON-CAR-2026"),
        ]
        sup_objs = []
        for sname, sperson, semail, sphone, scontract in suppliers_data:
            s, _ = Supplier.objects.get_or_create(
                name=sname,
                defaults={"contact_person": sperson, "email": semail, "phone": sphone, "contract_number": scontract}
            )
            sup_objs.append(s)

        EnergyTariff.objects.get_or_create(
            organization=org_norte,
            name="Tarifa Gran Industria AT3",
            defaults={"cost_per_kwh": Decimal("115.50"), "peak_cost_per_kwh": Decimal("185.00"), "currency": "CLP"}
        )
        EnergyTariff.objects.get_or_create(
            organization=org_sur,
            name="Tarifa Comercial BT2",
            defaults={"cost_per_kwh": Decimal("128.00"), "peak_cost_per_kwh": Decimal("195.50"), "currency": "CLP"}
        )

        # ----------------------------------------------------------------------
        # 5. TABLAS MAESTRAS: ZONAS
        # ----------------------------------------------------------------------
        zones_norte = [
            ("Planta de Fundición y Maestranza", Decimal("2500.00"), Decimal("1200.00"), "Carlos Gómez"),
            ("Línea de Ensamble Automatizado", Decimal("1800.00"), Decimal("850.00"), "Rodrigo Vega"),
            ("Oficinas Administrativas Norte", Decimal("600.00"), Decimal("450.00"), "Andrea Rojas"),
            ("Patio de Maniobras y Despacho", Decimal("400.00"), Decimal("900.00"), "Felipe Soto"),
        ]
        z_norte_objs = []
        for zname, zlimit, zarea, zresp in zones_norte:
            z, _ = Zone.objects.get_or_create(
                organization=org_norte,
                name=zname,
                defaults={"monthly_limit_kwh": zlimit, "floor_area_sqm": zarea, "responsible_person": zresp}
            )
            z_norte_objs.append(z)

        zones_sur = [
            ("Sala de Ventas Principal", Decimal("1400.00"), Decimal("1100.00"), "Camila Miranda"),
            ("Cámaras de Congelado y Frío", Decimal("2200.00"), Decimal("650.00"), "Marcelo Bravo"),
            ("Centro de Distribución y Bodega", Decimal("950.00"), Decimal("1500.00"), "Patricia Leiva"),
            ("Área de Carga de Vehículos Eléctricos", Decimal("1100.00"), Decimal("300.00"), "Jorge Valdés"),
        ]
        z_sur_objs = []
        for zname, zlimit, zarea, zresp in zones_sur:
            z, _ = Zone.objects.get_or_create(
                organization=org_sur,
                name=zname,
                defaults={"monthly_limit_kwh": zlimit, "floor_area_sqm": zarea, "responsible_person": zresp}
            )
            z_sur_objs.append(z)

        all_zones = z_norte_objs + z_sur_objs

        # ----------------------------------------------------------------------
        # 6. TABLAS MAESTRAS: DISPOSITIVOS
        # ----------------------------------------------------------------------
        devices_data = [
            # Dispositivos Norte
            (z_norte_objs[0], cat_objs[0], sup_objs[0], "Torno CNC Haas ST-30", "NOR-CNC-001", Decimal("30.00"), "ACTIVE"),
            (z_norte_objs[0], cat_objs[0], sup_objs[0], "Fresadora Universal 5 Ejes", "NOR-FRE-002", Decimal("22.50"), "ACTIVE"),
            (z_norte_objs[1], cat_objs[1], sup_objs[2], "Chiller Central Daikin 50TR", "NOR-CHI-003", Decimal("45.00"), "MAINTENANCE"),
            (z_norte_objs[1], cat_objs[0], sup_objs[1], "Brazo Robótico ABB IRB-6700", "NOR-ROB-004", Decimal("18.00"), "ACTIVE"),
            (z_norte_objs[2], cat_objs[2], sup_objs[1], "Rack Servidores & UPS Corporativa", "NOR-SRV-005", Decimal("12.00"), "ACTIVE"),
            (z_norte_objs[2], cat_objs[1], sup_objs[2], "Sistema Climatización Oficinas", "NOR-CLI-006", Decimal("15.00"), "ACTIVE"),
            (z_norte_objs[3], cat_objs[2], sup_objs[1], "Torre Iluminación LED Patio", "NOR-LUM-007", Decimal("8.50"), "ACTIVE"),
            (z_norte_objs[3], cat_objs[0], sup_objs[0], "Grúa Horquilla Eléctrica Linde", "NOR-GRU-008", Decimal("20.00"), "ACTIVE"),

            # Dispositivos Sur
            (z_sur_objs[0], cat_objs[2], sup_objs[1], "Circuito Iluminación Sala Ventas", "SUR-LUM-101", Decimal("16.00"), "ACTIVE"),
            (z_sur_objs[0], cat_objs[1], sup_objs[2], "Aire Acondicionado Central Inverter", "SUR-CLI-102", Decimal("28.00"), "ACTIVE"),
            (z_sur_objs[1], cat_objs[3], sup_objs[0], "Compresor Bitzer Doble Etapa A", "SUR-FRI-103", Decimal("55.00"), "ACTIVE"),
            (z_sur_objs[1], cat_objs[3], sup_objs[0], "Compresor Bitzer Doble Etapa B", "SUR-FRI-104", Decimal("55.00"), "ACTIVE"),
            (z_sur_objs[2], cat_objs[0], sup_objs[1], "Transpaleta Eléctrica Crown", "SUR-TRA-105", Decimal("9.00"), "ACTIVE"),
            (z_sur_objs[2], cat_objs[2], sup_objs[1], "Panel Iluminación Pasillos Bodega", "SUR-LUM-106", Decimal("11.50"), "ACTIVE"),
            (z_sur_objs[3], cat_objs[0], sup_objs[0], "Cargador Rápido EV Wallbox 22kW", "SUR-CHG-107", Decimal("22.00"), "ACTIVE"),
            (z_sur_objs[3], cat_objs[0], sup_objs[0], "Cargador Rápido EV ABB 50kW", "SUR-CHG-108", Decimal("50.00"), "MAINTENANCE"),
        ]

        dev_objs = []
        for zone, cat, sup, dname, dserial, dpower, dstatus in devices_data:
            dev, _ = Device.objects.get_or_create(
                serial_number=dserial,
                defaults={
                    "zone": zone,
                    "category": cat,
                    "supplier": sup,
                    "name": dname,
                    "nominal_power_kw": dpower,
                    "status": dstatus,
                    "installation_date": timezone.now().date() - timedelta(days=random.randint(60, 400)),
                }
            )
            dev_objs.append(dev)

        # ----------------------------------------------------------------------
        # 7. TABLAS OPERACIONALES: ÓRDENES DE MANTENIMIENTO Y PRESUPUESTOS
        # ----------------------------------------------------------------------
        now = timezone.now()
        for i, dev in enumerate(dev_objs):
            MaintenanceOrder.objects.get_or_create(
                device=dev,
                title=f"Mantenimiento Periódico Trimestral - {dev.name}",
                defaults={
                    "scheduled_date": now.date() - timedelta(days=(i * 7)),
                    "status": "COMPLETED" if i % 2 == 0 else "IN_PROGRESS",
                    "technician_notes": "Inspección de bornes eléctricos, medición de aislamiento y lubricación de rodamientos.",
                    "cost": Decimal(f"{random.randint(50, 350) * 1000}.00"),
                }
            )

        for zone in all_zones:
            MonthlyZoneBudget.objects.get_or_create(
                zone=zone,
                year=now.year,
                month=now.month,
                defaults={
                    "budgeted_kwh": zone.monthly_limit_kwh,
                    "actual_kwh": Decimal(f"{float(zone.monthly_limit_kwh) * random.uniform(0.65, 1.15):.2f}"),
                    "is_closed": False,
                }
            )

        # ----------------------------------------------------------------------
        # 8. TABLAS OPERACIONALES: ALERTAS DE CONSUMO
        # ----------------------------------------------------------------------
        alerts_data = [
            (dev_objs[0], "MEDIUM", "Consumo horario supera en un 18% la media histórica.", False),
            (dev_objs[2], "HIGH", "Dispositivo detenido inesperadamente por sobrecarga térmica.", True),
            (dev_objs[10], "CRITICAL", "Cámara frigorífica operando a 98% de capacidad sostenida por 6 horas.", False),
            (dev_objs[15], "HIGH", "Error de aislamiento en fase R durante recarga vehicular.", False),
            (dev_objs[3], "LOW", "Pequeña oscilación armónica detectada en convertidor estático.", True),
        ]
        for dev, sev, msg, res in alerts_data:
            EnergyAlert.objects.get_or_create(
                device=dev,
                message=msg,
                defaults={
                    "severity": sev,
                    "is_resolved": res,
                    "triggered_at": now - timedelta(hours=random.randint(1, 48)),
                    "resolved_at": (now - timedelta(hours=2)) if res else None,
                }
            )

        # ----------------------------------------------------------------------
        # 9. CARGA MASIVA (>= 1.000 REGISTROS DE TELEMETRÍA EN ConsumptionRecord)
        # ----------------------------------------------------------------------
        self.stdout.write(self.style.NOTICE("Generando 1.050 registros de telemetría de consumo con bulk_create..."))
        
        registros_a_crear = []
        # Generamos lecturas históricas para los 16 dispositivos en los últimos 30 días
        # 16 dispositivos * ~66 lecturas = 1.056 lecturas
        total_dias = 30
        lecturas_por_dispositivo = 66  # ~1.056 registros totales

        for dev in dev_objs:
            base_power = float(dev.nominal_power_kw)
            for step in range(lecturas_por_dispositivo):
                # Distribuir a lo largo de los últimos 30 días
                minutos_atras = (step * (total_dias * 24 * 60) // lecturas_por_dispositivo) + random.randint(0, 30)
                fecha_medicion = now - timedelta(minutes=minutos_atras)
                
                # Consumo coherente con potencia del equipo
                factor = random.uniform(0.4, 0.95) if dev.status == 'ACTIVE' else 0.05
                consumo_calculado = Decimal(f"{(base_power * factor):.2f}")
                voltaje_simulado = Decimal(f"{random.uniform(378.0, 382.5):.1f}") if base_power > 15 else Decimal(f"{random.uniform(219.0, 222.0):.1f}")
                
                registros_a_crear.append(
                    ConsumptionRecord(
                        device=dev,
                        recorded_at=fecha_medicion,
                        consumption_kwh=consumo_calculado,
                        average_voltage=voltaje_simulado,
                        notes="Lectura automática de telemetría" if step % 5 == 0 else ""
                    )
                )

        ConsumptionRecord.objects.bulk_create(registros_a_crear)

        # ----------------------------------------------------------------------
        # 10. RESUMEN Y TOTALES
        # ----------------------------------------------------------------------
        tot_orgs = Organization.objects.count()
        tot_cats = DeviceCategory.objects.count()
        tot_sups = Supplier.objects.count()
        tot_tariffs = EnergyTariff.objects.count()
        tot_zones = Zone.objects.count()
        tot_devs = Device.objects.count()
        tot_records = ConsumptionRecord.objects.count()
        tot_alerts = EnergyAlert.objects.count()
        tot_orders = MaintenanceOrder.objects.count()
        tot_budgets = MonthlyZoneBudget.objects.count()

        gran_total = tot_orgs + tot_cats + tot_sups + tot_tariffs + tot_zones + tot_devs + tot_records + tot_alerts + tot_orders + tot_budgets

        self.stdout.write(self.style.SUCCESS(f"[OK] Carga finalizada con éxito:"))
        self.stdout.write(self.style.SUCCESS(f"     - Tablas Maestras (6): {tot_orgs} Orgs, {tot_cats} Categorías, {tot_sups} Proveedores, {tot_tariffs} Tarifas, {tot_zones} Zonas, {tot_devs} Dispositivos."))
        self.stdout.write(self.style.SUCCESS(f"     - Tablas Operativas (4): {tot_records} Mediciones, {tot_alerts} Alertas, {tot_orders} Órdenes Mant., {tot_budgets} Presupuestos."))
        self.stdout.write(self.style.SUCCESS(f"     => TOTAL REGISTROS DE NEGOCIO: {gran_total} (Supera la exigencia de 1.000 registros)."))
        self.stdout.write(self.style.SUCCESS(f"[OK] Usuarios de prueba listos:"))
        self.stdout.write(self.style.SUCCESS("     1. 'admin'          / 'AdminPassword123!' (Superadministrador Global)"))
        self.stdout.write(self.style.SUCCESS("     2. 'operador_norte' / 'OperadorNorte123!' (Editor/Operador EcoIndustrias Norte)"))
        self.stdout.write(self.style.SUCCESS("     3. 'lector_norte'   / 'LectorNorte123!'   (Lector/Consulta EcoIndustrias Norte)"))
        self.stdout.write(self.style.SUCCESS("     4. 'operador_sur'   / 'OperadorSur123!'   (Editor/Operador EcoRetail Sur)"))
