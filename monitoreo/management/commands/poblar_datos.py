from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from monitoreo.models import (
    Organizacion,
    CategoriaDispositivo,
    Zona,
    Dispositivo,
    PerfilUsuario,
    RegistroConsumo,
    AlertaConsumo,
)


class Command(BaseCommand):
    help = "Puebla la base de datos con datos reproducibles para la Evaluación Sumativa II (EcoEnergy)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina datos existentes antes de poblar la base de datos',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Iniciando carga de datos reproducibles EcoEnergy ==="))

        if options['limpiar']:
            self.stdout.write(self.style.WARNING("Limpiando registros antiguos..."))
            AlertaConsumo.objects.all().delete()
            RegistroConsumo.objects.all().delete()
            Dispositivo.objects.all().delete()
            Zona.objects.all().delete()
            CategoriaDispositivo.objects.all().delete()
            PerfilUsuario.objects.all().delete()
            Organizacion.objects.all().delete()
            User.objects.filter(username__in=['admin', 'operador_norte', 'operador_sur']).delete()

        # ----------------------------------------------------------------------
        # 1. PERMISOS Y GRUPO DE OPERADORES
        # ----------------------------------------------------------------------
        grupo_operadores, _ = Group.objects.get_or_create(name="Operadores de Monitoreo")
        modelos_monitoreo = [Organizacion, CategoriaDispositivo, Zona, Dispositivo, RegistroConsumo, AlertaConsumo]
        
        for modelo in modelos_monitoreo:
            ct = ContentType.objects.get_for_model(modelo)
            permisos = Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f'view_{modelo._meta.model_name}',
                    f'change_{modelo._meta.model_name}',
                    f'add_{modelo._meta.model_name}',
                ]
            )
            for p in permisos:
                grupo_operadores.permissions.add(p)

        # ----------------------------------------------------------------------
        # 2. CREACIÓN DE USUARIOS DE PRUEBA DOCUMENTADOS
        # ----------------------------------------------------------------------
        # 2.1 Superusuario Global (Admin)
        u_admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@ecoenergy.cl',
                'first_name': 'Administrador',
                'last_name': 'Global',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        u_admin.set_password('AdminPassword123!')
        u_admin.is_staff = True
        u_admin.is_superuser = True
        u_admin.save()

        # 2.2 Operador Limitado Contexto 1 (EcoIndustrias Norte S.A.)
        u_norte, _ = User.objects.get_or_create(
            username='operador_norte',
            defaults={
                'email': 'operador.norte@ecoenergy.cl',
                'first_name': 'Rodrigo',
                'last_name': 'Vega',
                'is_staff': True,
                'is_superuser': False,
            }
        )
        u_norte.set_password('OperadorNorte123!')
        u_norte.is_staff = True
        u_norte.is_superuser = False
        u_norte.save()
        u_norte.groups.add(grupo_operadores)

        # 2.3 Operador Limitado Contexto 2 (EcoRetail Sur SpA)
        u_sur, _ = User.objects.get_or_create(
            username='operador_sur',
            defaults={
                'email': 'operador.sur@ecoenergy.cl',
                'first_name': 'Camila',
                'last_name': 'Miranda',
                'is_staff': True,
                'is_superuser': False,
            }
        )
        u_sur.set_password('OperadorSur123!')
        u_sur.is_staff = True
        u_sur.is_superuser = False
        u_sur.save()
        u_sur.groups.add(grupo_operadores)

        # ----------------------------------------------------------------------
        # 3. CREACIÓN DE TABLAS MAESTRAS: ORGANIZACIONES
        # ----------------------------------------------------------------------
        org_norte, _ = Organizacion.objects.get_or_create(
            rut="76.123.456-7",
            defaults={
                "nombre": "EcoIndustrias Norte S.A.",
                "direccion": "Av. Balmaceda 4500, La Serena",
                "email_contacto": "contacto@econorte.cl",
                "telefono": "+56 51 223344",
                "activa": True,
            }
        )

        org_sur, _ = Organizacion.objects.get_or_create(
            rut="77.987.654-3",
            defaults={
                "nombre": "EcoRetail Sur SpA",
                "direccion": "Ruta 5 Norte Km 460, Coquimbo",
                "email_contacto": "contacto@ecosur.cl",
                "telefono": "+56 51 255667",
                "activa": True,
            }
        )

        # Asignar perfiles para Scoping
        PerfilUsuario.objects.update_or_create(
            user=u_admin,
            defaults={'rol': 'ADMIN_GLOBAL', 'organizacion': None, 'telefono': '+56 9 1111 2222'}
        )
        PerfilUsuario.objects.update_or_create(
            user=u_norte,
            defaults={'rol': 'OPERADOR', 'organizacion': org_norte, 'telefono': '+56 9 3333 4444'}
        )
        PerfilUsuario.objects.update_or_create(
            user=u_sur,
            defaults={'rol': 'OPERADOR', 'organizacion': org_sur, 'telefono': '+56 9 5555 6666'}
        )

        # ----------------------------------------------------------------------
        # 4. CREACIÓN DE TABLAS MAESTRAS: CATEGORÍAS
        # ----------------------------------------------------------------------
        cat_maquinaria, _ = CategoriaDispositivo.objects.get_or_create(
            nombre="Maquinaria Pesada",
            defaults={
                "descripcion": "Tornos CNC, fresadoras y motores industriales de alto caballaje.",
                "es_critica": True,
            }
        )
        cat_clima, _ = CategoriaDispositivo.objects.get_or_create(
            nombre="Climatización Industrial",
            defaults={
                "descripcion": "Chillers, bombas de calor y ventilación mecánica centralizada.",
                "es_critica": False,
            }
        )
        cat_ofimatica, _ = CategoriaDispositivo.objects.get_or_create(
            nombre="Iluminación y Ofimática",
            defaults={
                "descripcion": "Luminarias LED de alta eficiencia, servidores y puestos de trabajo.",
                "es_critica": False,
            }
        )
        cat_refrig, _ = CategoriaDispositivo.objects.get_or_create(
            nombre="Sistemas de Refrigeración",
            defaults={
                "descripcion": "Cámaras frigoríficas y compresores para cadena de frío.",
                "es_critica": True,
            }
        )

        # ----------------------------------------------------------------------
        # 5. CREACIÓN DE TABLAS MAESTRAS: ZONAS
        # ----------------------------------------------------------------------
        # Zonas Organización Norte
        z_norte_1, _ = Zona.objects.get_or_create(
            organizacion=org_norte,
            nombre="Planta de Fundición y Maestranza",
            defaults={
                "limite_kwh": Decimal("1500.00"),
                "descripcion": "Sector industrial principal para moldeado y mecanizado.",
                "responsable": "Carlos Gómez",
                "activa": True,
            }
        )
        z_norte_2, _ = Zona.objects.get_or_create(
            organizacion=org_norte,
            nombre="Línea de Ensamble Automatizado",
            defaults={
                "limite_kwh": Decimal("900.00"),
                "descripcion": "Brazos robóticos y cintas transportadoras.",
                "responsable": "Rodrigo Vega",
                "activa": True,
            }
        )
        z_norte_3, _ = Zona.objects.get_or_create(
            organizacion=org_norte,
            nombre="Oficinas Administrativas Norte",
            defaults={
                "limite_kwh": Decimal("350.00"),
                "descripcion": "Edificio corporativo de 2 pisos y sala de servidores.",
                "responsable": "Andrea Rojas",
                "activa": True,
            }
        )

        # Zonas Organización Sur
        z_sur_1, _ = Zona.objects.get_or_create(
            organizacion=org_sur,
            nombre="Sala de Ventas Principal",
            defaults={
                "limite_kwh": Decimal("800.00"),
                "descripcion": "Área de atención a público con iluminación continua.",
                "responsable": "Camila Miranda",
                "activa": True,
            }
        )
        z_sur_2, _ = Zona.objects.get_or_create(
            organizacion=org_sur,
            nombre="Cámaras de Congelado",
            defaults={
                "limite_kwh": Decimal("1200.00"),
                "descripcion": "Almacenamiento de productos perecibles bajo 0°C.",
                "responsable": "Marcelo Bravo",
                "activa": True,
            }
        )

        # ----------------------------------------------------------------------
        # 6. CREACIÓN DE TABLAS MAESTRAS: DISPOSITIVOS
        # ----------------------------------------------------------------------
        # Dispositivos para Norte
        d_norte_1, _ = Dispositivo.objects.get_or_create(
            codigo_inventario="NOR-CNC-01",
            defaults={
                "zona": z_norte_1,
                "categoria": cat_maquinaria,
                "nombre": "Torno CNC Haas ST-30",
                "potencia_nominal_kw": Decimal("30.00"),
                "estado": "ACTIVO",
                "fecha_instalacion": timezone.now().date() - timedelta(days=200),
            }
        )
        d_norte_2, _ = Dispositivo.objects.get_or_create(
            codigo_inventario="NOR-FRES-02",
            defaults={
                "zona": z_norte_1,
                "categoria": cat_maquinaria,
                "nombre": "Fresadora Universal 5 Ejes",
                "potencia_nominal_kw": Decimal("22.50"),
                "estado": "ACTIVO",
                "fecha_instalacion": timezone.now().date() - timedelta(days=150),
            }
        )
        d_norte_3, _ = Dispositivo.objects.get_or_create(
            codigo_inventario="NOR-CHILL-03",
            defaults={
                "zona": z_norte_2,
                "categoria": cat_clima,
                "nombre": "Chiller Daikin 50TR",
                "potencia_nominal_kw": Decimal("45.00"),
                "estado": "MANTENIMIENTO",
                "fecha_instalacion": timezone.now().date() - timedelta(days=300),
            }
        )
        d_norte_4, _ = Dispositivo.objects.get_or_create(
            codigo_inventario="NOR-SRV-04",
            defaults={
                "zona": z_norte_3,
                "categoria": cat_ofimatica,
                "nombre": "Rack Servidores & UPS Central",
                "potencia_nominal_kw": Decimal("12.00"),
                "estado": "ACTIVO",
                "fecha_instalacion": timezone.now().date() - timedelta(days=400),
            }
        )

        # Dispositivos para Sur
        d_sur_1, _ = Dispositivo.objects.get_or_create(
            codigo_inventario="SUR-LUM-01",
            defaults={
                "zona": z_sur_1,
                "categoria": cat_ofimatica,
                "nombre": "Circuito LED Sala de Ventas",
                "potencia_nominal_kw": Decimal("15.00"),
                "estado": "ACTIVO",
                "fecha_instalacion": timezone.now().date() - timedelta(days=90),
            }
        )
        d_sur_2, _ = Dispositivo.objects.get_or_create(
            codigo_inventario="SUR-FRIG-02",
            defaults={
                "zona": z_sur_2,
                "categoria": cat_refrig,
                "nombre": "Compresor Bitzer Doble Etapa",
                "potencia_nominal_kw": Decimal("55.00"),
                "estado": "ACTIVO",
                "fecha_instalacion": timezone.now().date() - timedelta(days=180),
            }
        )

        # ----------------------------------------------------------------------
        # 7. CREACIÓN DE TABLAS OPERATIVAS: REGISTROS DE CONSUMO
        # ----------------------------------------------------------------------
        ahora = timezone.now()
        lecturas_base = [
            (d_norte_1, Decimal("185.40"), Decimal("380.5"), ahora - timedelta(hours=2), "Turno mañana normal"),
            (d_norte_1, Decimal("192.10"), Decimal("379.8"), ahora - timedelta(hours=6), "Operación a plena carga"),
            (d_norte_2, Decimal("110.30"), Decimal("381.2"), ahora - timedelta(hours=3), "Mecanizado de piezas de acero"),
            (d_norte_3, Decimal("45.00"), Decimal("380.0"), ahora - timedelta(hours=12), "Prueba de ciclado post-mantenimiento"),
            (d_norte_4, Decimal("28.75"), Decimal("220.1"), ahora - timedelta(hours=1), "Carga continua de servidores"),
            (d_sur_1, Decimal("85.60"), Decimal("220.0"), ahora - timedelta(hours=4), "Horario alta afluencia público"),
            (d_sur_2, Decimal("430.80"), Decimal("382.4"), ahora - timedelta(hours=2), "Enfriamiento rápido de cámaras"),
        ]

        for disp, kwh, v, dt, obs in lecturas_base:
            RegistroConsumo.objects.get_or_create(
                dispositivo=disp,
                fecha_hora=dt,
                defaults={
                    "consumo_kwh": kwh,
                    "voltaje_promedio": v,
                    "observacion": obs,
                }
            )

        # ----------------------------------------------------------------------
        # 8. CREACIÓN DE TABLAS OPERATIVAS: ALERTAS DE CONSUMO
        # ----------------------------------------------------------------------
        alertas_base = [
            (
                d_norte_1,
                "MEDIA",
                "Consumo horario 15% superior al promedio histórico durante el turno matutino.",
                False,
                ahora - timedelta(hours=2),
                None
            ),
            (
                d_norte_3,
                "ALTA",
                "Dispositivo detenido inesperadamente por elevación de temperatura en compresor.",
                True,
                ahora - timedelta(days=1),
                ahora - timedelta(hours=10)
            ),
            (
                d_sur_2,
                "CRITICA",
                "Consumo de energía sostenido sobre el 95% del límite de la zona por más de 4 horas.",
                False,
                ahora - timedelta(minutes=45),
                None
            ),
        ]

        for disp, severidad, msg, res, dt, dt_res in alertas_base:
            AlertaConsumo.objects.get_or_create(
                dispositivo=disp,
                mensaje=msg,
                defaults={
                    "nivel": severidad,
                    "resuelta": res,
                    "fecha_hora": dt,
                    "resuelta_en": dt_res,
                }
            )

        self.stdout.write(self.style.SUCCESS("[OK] Tablas maestras y operativas pobladas correctamente."))
        self.stdout.write(self.style.SUCCESS("[OK] Organizaciones creadas: 2 (EcoIndustrias Norte S.A., EcoRetail Sur SpA)"))
        self.stdout.write(self.style.SUCCESS("[OK] Usuarios de prueba configurados:"))
        self.stdout.write(self.style.SUCCESS("    1. Superusuario Global: 'admin' / 'AdminPassword123!' (Acceso completo)"))
        self.stdout.write(self.style.SUCCESS("    2. Operador Norte:      'operador_norte' / 'OperadorNorte123!' (Scoping EcoIndustrias Norte)"))
        self.stdout.write(self.style.SUCCESS("    3. Operador Sur:        'operador_sur' / 'OperadorSur123!' (Scoping EcoRetail Sur)"))
        self.stdout.write(self.style.SUCCESS("=== Carga finalizada con exito ==="))
