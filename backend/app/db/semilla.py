from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import select

from app.core.configuracion import configuracion
from app.core.seguridad import generar_hash_contrasena
from app.db.conexion import SesionLocal, motor_bd
from app.models.entidades import (
    BaseDeclarativa,
    EstadoGrano,
    Finca,
    FrecuenciaSuscripcion,
    LoteCafe,
    MunicipioTolima,
    NivelTueste,
    PerfilSensorial,
    PlanSuscripcion,
    ProcesoBeneficio,
    RolUsuario,
    Usuario,
    VariedadCafe,
)


def sembrar_datos_tolima() -> None:
    """Crea las tablas e inserta productores, lotes, perfiles sensoriales y planes de suscripción."""
    BaseDeclarativa.metadata.create_all(bind=motor_bd)

    with SesionLocal() as sesion:
        existente = sesion.scalar(select(Usuario).limit(1))
        if existente:
            print("La base de datos de Maicofi ya cuenta con datos iniciales.")
            return

        clave_demo = generar_hash_contrasena(configuracion.CLAVE_USUARIO_DEMO)
        hoy = date.today()

        # 1. Sembrar planes de suscripción recurrente (-10% de descuento automático)
        planes_iniciales = [
            PlanSuscripcion(
                codigo="SUB-SEMANAL-10",
                nombre="Suscripción Semanal Frescura de Origen",
                descripcion="Recibe café recién tostado del Tolima cada semana con 10% de descuento.",
                frecuencia=FrecuenciaSuscripcion.SEMANAL,
                porcentaje_descuento=Decimal("10.00"),
            ),
            PlanSuscripcion(
                codigo="SUB-QUINCENAL-10",
                nombre="Suscripción Quincenal Casa Cafetera",
                descripcion="Entrega cada 15 días directo de la finca con 10% de descuento permanente.",
                frecuencia=FrecuenciaSuscripcion.QUINCENAL,
                porcentaje_descuento=Decimal("10.00"),
            ),
            PlanSuscripcion(
                codigo="SUB-MENSUAL-10",
                nombre="Suscripción Mensual Reserva Tolima",
                descripcion="Entrega mensual programada con selección de molienda y 10% de descuento.",
                frecuencia=FrecuenciaSuscripcion.MENSUAL,
                porcentaje_descuento=Decimal("10.00"),
            ),
        ]
        sesion.add_all(planes_iniciales)
        sesion.flush()

        # 2. Sembrar productores, fincas con geolocalización y lotes con PerfilSensorial
        productores_iniciales = [
            {
                "usuario": Usuario(
                    nombre_completo="Don Albeiro Lozano",
                    telefono=configuracion.TELEFONO_CAFICULTOR_DEMO,
                    correo="albeiro.planadas@maicofi.co",
                    contrasena_hash=clave_demo,
                    rol=RolUsuario.CAFICULTOR,
                ),
                "finca": {
                    "nombre_finca": "Finca El Mirador del Nevado",
                    "municipio": MunicipioTolima.PLANADAS,
                    "vereda": "Vereda Gaitania",
                    "altura_msnm": 1920,
                    "historia_productor": (
                        "Tercera generación de caficultores del sur del Tolima. Cultivamos bajo sombrío "
                        "nativo con aguas cristalinas de alta montaña y secado lento en marquesina solar."
                    ),
                    "foto_productor_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80",
                    "latitud": Decimal("3.196400"),
                    "longitud": Decimal("-75.645300"),
                    "urls_fotos": [
                        "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1000&q=80"
                    ],
                },
                "lotes": [
                    {
                        "slug": "microlote-geisha-lavado-planadas",
                        "nombre": "Microlote Geisha Lavado de Alta Montaña",
                        "variedad": VariedadCafe.GEISHA,
                        "proceso": ProcesoBeneficio.LAVADO,
                        "estado_presentacion": EstadoGrano.TOSTADO_GRANO,
                        "puntaje_sca": Decimal("88.50"),
                        "notas_cata": ["Jazmín", "Miel de Abejas", "Mandarina", "Té Negro"],
                        "humedad_porcentaje": Decimal("10.80"),
                        "fecha_tueste": hoy - timedelta(days=3),
                        "valvula_desgasificadora": True,
                        "precio_libra_cop": Decimal("52000"),
                        "precio_arroba_cop": Decimal("1196000"),
                        "precio_carga_cop": Decimal("11050000"),
                        "stock_disponible_kg": Decimal("250.00"),
                        "urls_fotos": [
                            "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=900&q=80"
                        ],
                        "sensorial": {
                            "acidez": 5,
                            "cuerpo": 3,
                            "dulzura": 5,
                            "nivel_tueste": NivelTueste.CLARO,
                            "notas_principales": ["Jazmín", "Miel de Abejas", "Mandarina", "Té Negro"],
                        },
                    },
                    {
                        "slug": "lote-caturra-honey-gaitania",
                        "nombre": "Lote Caturra Honey Seleccionado",
                        "variedad": VariedadCafe.CATURRA,
                        "proceso": ProcesoBeneficio.HONEY,
                        "estado_presentacion": EstadoGrano.TOSTADO_GRANO,
                        "puntaje_sca": Decimal("85.75"),
                        "notas_cata": ["Panela", "Durazno", "Caramelo Dulce", "Chocolate Amargo"],
                        "humedad_porcentaje": Decimal("11.20"),
                        "fecha_tueste": hoy - timedelta(days=5),
                        "valvula_desgasificadora": True,
                        "precio_libra_cop": Decimal("34000"),
                        "precio_arroba_cop": Decimal("782000"),
                        "precio_carga_cop": Decimal("7225000"),
                        "stock_disponible_kg": Decimal("625.00"),
                        "urls_fotos": [
                            "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?auto=format&fit=crop&w=900&q=80"
                        ],
                        "sensorial": {
                            "acidez": 3,
                            "cuerpo": 4,
                            "dulzura": 5,
                            "nivel_tueste": NivelTueste.MEDIO,
                            "notas_principales": ["Panela", "Durazno", "Caramelo Dulce", "Chocolate Amargo"],
                        },
                    },
                ],
            },
            {
                "usuario": Usuario(
                    nombre_completo="Doña Esperanza Trujillo",
                    telefono="+573158923411",
                    correo="esperanza.libano@maicofi.co",
                    contrasena_hash=clave_demo,
                    rol=RolUsuario.CAFICULTOR,
                ),
                "finca": {
                    "nombre_finca": "Finca La Esperanza Real",
                    "municipio": MunicipioTolima.LIBANO,
                    "vereda": "Vereda Santa Teresa",
                    "altura_msnm": 1780,
                    "historia_productor": (
                        "Asociación familiar de mujeres cafeteras en la cordillera central del Tolima. "
                        "Recolección manual grano a grano solo de cereza madura uva."
                    ),
                    "foto_productor_url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=600&q=80",
                    "latitud": Decimal("4.921600"),
                    "longitud": Decimal("-75.063200"),
                    "urls_fotos": [
                        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=1000&q=80"
                    ],
                },
                "lotes": [
                    {
                        "slug": "reserva-tabi-natural-libano",
                        "nombre": "Reserva Tabi Natural Secado al Sol",
                        "variedad": VariedadCafe.TABI,
                        "proceso": ProcesoBeneficio.NATURAL,
                        "estado_presentacion": EstadoGrano.TOSTADO_GRANO,
                        "puntaje_sca": Decimal("87.25"),
                        "notas_cata": ["Frutos Rojos", "Chocolate Amargo", "Vino Tinto", "Panela"],
                        "humedad_porcentaje": Decimal("11.00"),
                        "fecha_tueste": hoy - timedelta(days=2),
                        "valvula_desgasificadora": True,
                        "precio_libra_cop": Decimal("42000"),
                        "precio_arroba_cop": Decimal("966000"),
                        "precio_carga_cop": Decimal("8925000"),
                        "stock_disponible_kg": Decimal("375.00"),
                        "urls_fotos": [
                            "https://images.unsplash.com/photo-1447933601403-0c6688de566e?auto=format&fit=crop&w=900&q=80"
                        ],
                        "sensorial": {
                            "acidez": 4,
                            "cuerpo": 5,
                            "dulzura": 5,
                            "nivel_tueste": NivelTueste.MEDIO,
                            "notas_principales": ["Frutos Rojos", "Chocolate Amargo", "Vino Tinto", "Panela"],
                        },
                    }
                ],
            },
            {
                "usuario": Usuario(
                    nombre_completo="Familia Pava Oviedo",
                    telefono="+573187612390",
                    correo="fincalacumbre.anzoategui@maicofi.co",
                    contrasena_hash=clave_demo,
                    rol=RolUsuario.CAFICULTOR,
                ),
                "finca": {
                    "nombre_finca": "Finca Brisas del Parque Los Nevados",
                    "municipio": MunicipioTolima.ANZOATEGUI,
                    "vereda": "Vereda Palomar",
                    "altura_msnm": 2050,
                    "historia_productor": (
                        "Ubicados en las faldas del Parque Nacional Natural Los Nevados, el clima frío "
                        "de alta montaña concentra azúcares únicos en cada grano de Bourbon Rosado y Castillo."
                    ),
                    "foto_productor_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80",
                    "latitud": Decimal("4.630800"),
                    "longitud": Decimal("-75.095100"),
                    "urls_fotos": [
                        "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=1000&q=80"
                    ],
                },
                "lotes": [
                    {
                        "slug": "bourbon-rosado-anaerobico-anzoategui",
                        "nombre": "Bourbon Rosado Fermentación Anaeróbica 72h",
                        "variedad": VariedadCafe.BOURBON_ROSADO,
                        "proceso": ProcesoBeneficio.ANAEROBICO,
                        "estado_presentacion": EstadoGrano.TOSTADO_GRANO,
                        "puntaje_sca": Decimal("89.00"),
                        "notas_cata": ["Frutos Rojos", "Cítricos", "Flor de Café", "Miel"],
                        "humedad_porcentaje": Decimal("10.90"),
                        "fecha_tueste": hoy - timedelta(days=1),
                        "valvula_desgasificadora": True,
                        "precio_libra_cop": Decimal("48000"),
                        "precio_arroba_cop": Decimal("1104000"),
                        "precio_carga_cop": Decimal("10200000"),
                        "stock_disponible_kg": Decimal("187.50"),
                        "urls_fotos": [
                            "https://images.unsplash.com/photo-1511920170033-f8396924c348?auto=format&fit=crop&w=900&q=80"
                        ],
                        "sensorial": {
                            "acidez": 5,
                            "cuerpo": 4,
                            "dulzura": 5,
                            "nivel_tueste": NivelTueste.CLARO,
                            "notas_principales": ["Frutos Rojos", "Cítricos", "Flor de Café", "Miel"],
                        },
                    }
                ],
            },
        ]

        for registro in productores_iniciales:
            usuario: Usuario = registro["usuario"]
            sesion.add(usuario)
            sesion.flush()

            finca = Finca(usuario_id=usuario.id, **registro["finca"])
            sesion.add(finca)
            sesion.flush()

            for datos_lote in registro["lotes"]:
                datos_sensorial = datos_lote.pop("sensorial")
                lote = LoteCafe(finca_id=finca.id, **datos_lote)
                sesion.add(lote)
                sesion.flush()

                perfil = PerfilSensorial(lote_cafe_id=lote.id, **datos_sensorial)
                sesion.add(perfil)

        comprador_demo = Usuario(
            nombre_completo="Tostadora Tolima Especial",
            telefono=configuracion.TELEFONO_COMPRADOR_DEMO,
            correo="compras@tostadoratolima.co",
            contrasena_hash=clave_demo,
            rol=RolUsuario.COMPRADOR,
        )
        sesion.add(comprador_demo)

        sesion.commit()
        print("Semilla de datos de especialidad del Tolima cargada exitosamente.")


if __name__ == "__main__":
    sembrar_datos_tolima()
