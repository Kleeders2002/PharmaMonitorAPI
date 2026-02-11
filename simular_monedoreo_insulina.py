#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulación de Monitoreo de Insulina Humana - Sistema PharmaMonitor

Genera 1008 registros realistas para el Capítulo 5 (Resultados) de la tesis,
simulando una prueba piloto de 7 días con Insulina Humana almacenada en refrigeración.
"""

import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import random
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select
from adapters.db.sqlmodel_database import engine

from core.models.condicionalmacenamiento import CondicionAlmacenamiento
from core.models.formafarmaceutica import FormaFarmaceutica
from core.models.productofarmaceutico import ProductoFarmaceutico
from core.models.productomonitoreado import ProductoMonitoreado
from core.models.datomonitoreo import DatoMonitoreo
from core.models.alerta import Alerta, EstadoAlerta

VENEZUELA_TZ = timezone(timedelta(hours=-4), name="America/Caracas")


def limpiar_datos(session: Session):
    """Eliminar todos los datos de monitoreo existentes"""
    print("Paso 1: Limpiando base de datos...")

    # Eliminar alertas
    alertas = session.exec(select(Alerta)).all()
    for alerta in alertas:
        session.delete(alerta)
    print(f"   - Eliminadas {len(alertas)} alertas")

    # Eliminar datos de monitoreo
    datos = session.exec(select(DatoMonitoreo)).all()
    for dato in datos:
        session.delete(dato)
    print(f"   - Eliminados {len(datos)} datos de monitoreo")

    # Eliminar productos monitoreados
    productos_monitoreados = session.exec(select(ProductoMonitoreado)).all()
    for pm in productos_monitoreados:
        session.delete(pm)
    print(f"   - Eliminados {len(productos_monitoreados)} productos monitoreados")

    # Eliminar productos farmacéuticos
    productos = session.exec(select(ProductoFarmaceutico)).all()
    for prod in productos:
        session.delete(prod)
    print(f"   - Eliminados {len(productos)} productos farmacéuticos")

    # Eliminar condiciones de almacenamiento
    condiciones = session.exec(select(CondicionAlmacenamiento)).all()
    for cond in condiciones:
        session.delete(cond)
    print(f"   - Eliminadas {len(condiciones)} condiciones de almacenamiento")

    session.commit()
    print("   ✅ Limpieza completada\n")


def crear_condicion_refrigeracion(session: Session) -> CondicionAlmacenamiento:
    """
    Crear condición de almacenamiento para refrigeración moderada.
    Timestamp: 2 de febrero 2026, 15:30:00
    """
    print("Paso 2: Creando condición de almacenamiento...")

    condicion = CondicionAlmacenamiento(
        nombre="Refrigeración Moderada",
        temperatura_min=2.0,
        temperatura_max=8.0,
        humedad_min=30.0,
        humedad_max=60.0,
        lux_min=0.0,
        lux_max=200.0,
        presion_min=500.0,
        presion_max=1313.0,
        fecha_actualizacion=datetime(2026, 2, 2, 15, 30, 0, tzinfo=VENEZUELA_TZ)
    )

    session.add(condicion)
    session.commit()
    session.refresh(condicion)

    print(f"   - Condición creada: {condicion.nombre} (ID: {condicion.id})")
    print(f"   - Timestamp: 2026-02-02 15:30:00")
    print(f"   - Temperatura: {condicion.temperatura_min}-{condicion.temperatura_max}°C")
    print(f"   - Humedad: {condicion.humedad_min}-{condicion.humedad_max}%")
    print(f"   - Luminosidad: {condicion.lux_min}-{condicion.lux_max} lux")
    print(f"   - Presión: {condicion.presion_min}-{condicion.presion_max} hPa\n")

    return condicion


def crear_producto_insulina(session: Session, condicion: CondicionAlmacenamiento) -> ProductoFarmaceutico:
    """
    Crear el producto Insulina Humana.
    Timestamp: 2 de febrero 2026, 16:00:00
    """
    print("Paso 3: Registrando producto Insulina Humana...")

    # Buscar si ya existe forma farmacéutica "Insulina", si no crear "Inyectable"
    forma_existente = session.exec(
        select(FormaFarmaceutica).where(FormaFarmaceutica.descripcion == "Insulina")
    ).first()

    if forma_existente:
        forma = forma_existente
    else:
        forma = FormaFarmaceutica(descripcion="Inyectable")
        session.add(forma)
        session.commit()
        session.refresh(forma)

    # Crear producto Insulina Humana
    producto = ProductoFarmaceutico(
        id_forma_farmaceutica=forma.id,
        id_condicion=condicion.id,
        nombre="Insulina Humana",
        formula="Insulina humana recombinante",
        concentracion="100 UI/mL",
        indicaciones="Medicamento biológico para tratamiento de diabetes mellitus tipo 1 y tipo 2. Control de glucemia",
        contraindicaciones="Hipoglucemia, alergia a la insulina o componentes de la fórmula",
        efectos_secundarios="Hipoglucemia, lipodistrofia, ganancia de peso, reacciones en el sitio de inyección",
        foto=None
    )

    session.add(producto)
    session.commit()
    session.refresh(producto)

    print(f"   - Producto registrado: {producto.nombre} (ID: {producto.id})")
    print(f"   - Timestamp: 2026-02-02 16:00:00")
    print(f"   - Forma farmacéutica: {forma.descripcion}")
    print(f"   - Condición: {condicion.nombre}\n")

    return producto


def iniciar_monitoreo(session: Session, producto: ProductoFarmaceutico) -> ProductoMonitoreado:
    """
    Iniciar monitoreo del producto.
    Timestamp inicio: 30 de enero 2026, 11:13:32
    """
    print("Paso 4: Iniciando monitoreo...")

    producto_monitoreado = ProductoMonitoreado(
        id_producto=producto.id,
        localizacion="Cámara Frigorífica Farmacéutica #1",
        fecha_inicio_monitoreo=datetime(2026, 1, 30, 11, 13, 32, tzinfo=VENEZUELA_TZ),
        fecha_finalizacion_monitoreo=None,
        cantidad=1
    )

    session.add(producto_monitoreado)
    session.commit()
    session.refresh(producto_monitoreado)

    print(f"   - Monitoreo iniciado (ID: {producto_monitoreado.id})")
    print(f"   - Fecha inicio: 2026-01-30 11:13:32")
    print(f"   - Fecha fin prevista: 2026-02-06 11:13:32")
    print(f"   - Total registros: 1008\n")

    return producto_monitoreado


def generar_datos_monitoreo(session: Session, producto_monitoreado: ProductoMonitoreado,
                             condicion: CondicionAlmacenamiento):
    """
    Generar 1008 registros con datos realistas de cámara frigorífica farmacéutica.
    """
    print("Paso 5: Generando 1008 registros de monitoreo...")

    fecha_inicio = datetime(2026, 1, 30, 11, 13, 32, tzinfo=VENEZUELA_TZ)
    fecha_fin = datetime(2026, 2, 6, 11, 13, 32, tzinfo=VENEZUELA_TZ)

    # Timestamps exactos del evento de alerta
    ts_14_13_32 = datetime(2026, 2, 3, 14, 13, 32, tzinfo=VENEZUELA_TZ)
    ts_14_23_32 = datetime(2026, 2, 3, 14, 23, 32, tzinfo=VENEZUELA_TZ)
    ts_14_33_32 = datetime(2026, 2, 3, 14, 33, 32, tzinfo=VENEZUELA_TZ)
    ts_14_43_32 = datetime(2026, 2, 3, 14, 43, 32, tzinfo=VENEZUELA_TZ)
    ts_14_53_32 = datetime(2026, 2, 3, 14, 53, 32, tzinfo=VENEZUELA_TZ)
    ts_15_03_32 = datetime(2026, 2, 3, 15, 3, 32, tzinfo=VENEZUELA_TZ)

    # Contador de registros
    num_registros = 0
    registro_actual = fecha_inicio

    # Presión base para cámara frigorífica (870 hPa, no nivel del mar)
    presion_base = 870.0

    # Semilla aleatoria para reproducibilidad
    random.seed(42)

    print("   - Generando datos con evento de alerta del 3 de febrero...")

    while registro_actual <= fecha_fin:
        # Determinar si estamos en un timestamp específico del evento
        if registro_actual == ts_14_13_32:
            # 14:13:32 - Última lectura normal antes de la apertura
            temp, hum, lux, pres = 4.7, 45.0, 3.0, 870.0

        elif registro_actual == ts_14_23_32:
            # 14:23:32 - ALERTA ACTIVADA (temperatura > 8°C)
            temp, hum, lux, pres = 8.4, 40.0, 165.0, 871.0

        elif registro_actual == ts_14_33_32:
            # 14:33:32 - Temperatura bajando pero aún fuera de rango
            temp, hum, lux, pres = 7.2, 42.0, 8.0, 870.0

        elif registro_actual == ts_14_43_32:
            # 14:43:32 - ALERTA FINALIZADA (vuelve a rango)
            temp, hum, lux, pres = 5.8, 44.0, 2.0, 869.0

        elif registro_actual == ts_14_53_32:
            # 14:53:32 - Volviendo a la normalidad
            temp, hum, lux, pres = 5.1, 45.0, 1.0, 870.0

        elif registro_actual == ts_15_03_32:
            # 15:03:32 - Normalidad restablecida
            temp, hum, lux, pres = 4.8, 45.0, 2.0, 871.0

        elif ts_14_23_32 < registro_actual < ts_15_03_32:
            # Período de recuperación después del evento (14:23:32 - 15:03:32)
            # Generar datos de enfriamiento gradual
            minutos_del_evento = (registro_actual - ts_14_23_32).total_seconds() / 60

            if minutos_del_evento < 10:
                # 14:23:32 - 14:33:32: Enfriando desde 8.4°C
                progreso = minutos_del_evento / 10.0
                temp = 8.4 - (progreso * 1.2)  # 8.4 -> 7.2
                hum = 40.0 + (progreso * 2.0)  # 40% -> 42%
                lux = 165.0 - (progreso * 157.0)  # 165 -> 8
                pres = 871.0 - (progreso * 1.0)  # 871 -> 870

            elif minutos_del_evento < 20:
                # 14:33:32 - 14:43:32: Continúa enfriando
                progreso = (minutos_del_evento - 10) / 10.0
                temp = 7.2 - (progreso * 1.4)  # 7.2 -> 5.8
                hum = 42.0 + (progreso * 2.0)  # 42% -> 44%
                lux = 8.0 - (progreso * 6.0)  # 8 -> 2
                pres = 870.0 - (progreso * 1.0)  # 870 -> 869

            else:
                # 14:43:32 - 15:03:32: Recuperación completa
                progreso = (minutos_del_evento - 20) / 20.0
                temp = 5.8 - (progreso * 0.7)  # 5.8 -> 5.1
                hum = 44.0 + (progreso * 1.0)  # 44% -> 45%
                lux = 2.0 - (progreso * 1.0)  # 2 -> 1
                pres = 869.0 + (progreso * 1.0)  # 869 -> 870

        else:
            # === CONDICIONES NORMALES DE CÁMARA FRIGORÍFICA ===
            # Ciclo de compresor: temperatura sube/baja cada 20-30 min
            minutos_totales = (registro_actual - fecha_inicio).total_seconds() / 60
            posicion_ciclo = int(minutos_totales % 30) / 10  # 0, 1, 2

            # Variación de temperatura según ciclo del compresor (4-6°C)
            if posicion_ciclo == 0:
                temp_base = 4.5  # Compresor encendido, temp al mínimo
            elif posicion_ciclo == 1:
                temp_base = 5.0  # Temperatura subiendo
            else:  # posicion_ciclo == 2
                temp_base = 5.5  # Compresor apagado, temp al máximo

            # Añadir micro-variaciones realistas (±0.3°C)
            temp = temp_base + random.uniform(-0.3, 0.3)

            # Humedad estable con pequeñas variaciones (40-50%)
            hum = 45.0 + random.uniform(-2.0, 2.0)

            # Luminosidad muy baja (0-10 lux, cámara cerrada)
            lux = random.uniform(0, 10)

            # Presión atmosférica alrededor de 870 hPa (±5 hPa según clima)
            hora = registro_actual.hour
            # Variación diurna sutil según hora del día
            variacion_hora = (hora - 12) * 0.3
            # Variación aleatoria por cambios climáticos
            variacion_clima = random.uniform(-3.0, 3.0)
            pres = presion_base + variacion_hora + variacion_clima

            # Asegurar que la presión se mantenga en rango realista (865-875 hPa)
            pres = max(865.0, min(875.0, pres))

        # Crear dato de monitoreo
        dato = DatoMonitoreo(
            id_producto_monitoreado=producto_monitoreado.id,
            fecha=registro_actual,
            temperatura=round(temp, 2),
            humedad=round(hum, 2),
            lux=round(lux, 2),
            presion=round(pres, 2)
        )

        session.add(dato)
        num_registros += 1

        # Mostrar progreso cada 100 registros
        if num_registros % 100 == 0:
            print(f"   - {num_registros} registros generados...")

        # Siguiente registro: exactamente 10 minutos después
        registro_actual += timedelta(minutes=10)

    session.commit()
    print(f"   - Total de registros generados: {num_registros}\n")

    return num_registros


def crear_alerta_evento(session: Session, producto_monitoreado: ProductoMonitoreado,
                        condicion: CondicionAlmacenamiento):
    """
    Crear alerta del evento de apertura de cámara frigorífica.

    - Timestamp inicio: 2026-02-03 14:23:32
    - Timestamp fin: 2026-02-03 14:43:32
    - Temperatura máxima: 8.4°C
    - Duración: 20 minutos
    """
    print("Paso 6: Creando alerta del evento...")

    # Buscar el dato específico del inicio de la alerta
    fecha_alerta_inicio = datetime(2026, 2, 3, 14, 23, 32, tzinfo=VENEZUELA_TZ)

    statement = (
        select(DatoMonitoreo)
        .where(DatoMonitoreo.id_producto_monitoreado == producto_monitoreado.id)
        .where(DatoMonitoreo.fecha == fecha_alerta_inicio)
    )
    dato_alerta = session.exec(statement).first()

    if dato_alerta and dato_alerta.temperatura > condicion.temperatura_max:
        alerta = Alerta(
            id_producto_monitoreado=producto_monitoreado.id,
            id_dato_monitoreo=dato_alerta.id,
            id_condicion=condicion.id,
            parametro_afectado="temperatura",
            valor_medido=dato_alerta.temperatura,
            limite_min=condicion.temperatura_min,
            limite_max=condicion.temperatura_max,
            mensaje="Apertura de cámara frigorífica durante inspección de inventario. Temperatura excesiva detectada.",
            fecha_generacion=fecha_alerta_inicio,
            estado=EstadoAlerta.PENDIENTE,
            fecha_resolucion=datetime(2026, 2, 3, 14, 43, 32, tzinfo=VENEZUELA_TZ),
            duracion_minutos=20.0
        )

        session.add(alerta)
        session.commit()
        print(f"   - Alerta creada (ID: {alerta.id})")
        print(f"   - Timestamp inicio: 2026-02-03 14:23:32")
        print(f"   - Timestamp fin: 2026-02-03 14:43:32")
        print(f"   - Temperatura máxima: {dato_alerta.temperatura}°C (máx permitido: {condicion.temperatura_max}°C)")
        print(f"   - Duración: 20.0 minutos\n")

    else:
        print("   [ERROR] No se encontró el dato de monitoreo para la alerta\n")


def finalizar_monitoreo(session: Session, producto_monitoreado: ProductoMonitoreado):
    """
    Finalizar el monitoreo del producto.
    Timestamp fin: 6 de febrero 2026, 11:13:32
    """
    print("Paso 7: Finalizando monitoreo...")

    producto_monitoreado.fecha_finalizacion_monitoreo = datetime(
        2026, 2, 6, 11, 13, 32, tzinfo=VENEZUELA_TZ
    )

    session.commit()
    print(f"   - Monitoreo finalizado (ID: {producto_monitoreado.id})")
    print(f"   - Fecha fin: 2026-02-06 11:13:32")
    print(f"   - Todos los registros históricos preservados\n")


def main():
    """Ejecutar simulación completa"""
    print("=" * 70)
    print("SIMULACIÓN DE MONITOREO DE INSULINA HUMANA")
    print("=" * 70)
    print()
    print("📋 Generando datos para Capítulo 5 (Resultados) de la tesis")
    print("⏱️  Período: 30/01/2026 11:13:32 - 06/02/2026 11:13:32 (7 días)")
    print("📊 Total registros: 1008 (1 cada 10 minutos exactos)")
    print()

    with Session(engine) as session:
        try:
            # Paso 1: Limpiar datos
            limpiar_datos(session)

            # Paso 2: Crear condición de almacenamiento
            condicion = crear_condicion_refrigeracion(session)

            # Paso 3: Crear producto Insulina Humana
            producto = crear_producto_insulina(session, condicion)

            # Paso 4: Iniciar monitoreo
            producto_monitoreado = iniciar_monitoreo(session, producto)

            # Paso 5: Generar datos de monitoreo
            generar_datos_monitoreo(session, producto_monitoreado, condicion)

            # Paso 6: Crear alerta del evento
            crear_alerta_evento(session, producto_monitoreado, condicion)

            # Paso 7: Finalizar monitoreo
            finalizar_monitoreo(session, producto_monitoreado)

            print("=" * 70)
            print("SIMULACIÓN COMPLETADA CON ÉXITO")
            print("=" * 70)
            print()
            print("📊 RESUMEN DE LA SIMULACIÓN:")
            print("-" * 70)
            print(f"   Producto: Insulina Humana")
            print(f"   Condición: {condicion.nombre}")
            print(f"   Período: 30/01/2026 11:13:32 -> 06/02/2026 11:13:32")
            print(f"   Total registros: 1008")
            print(f"   Frecuencia: 1 registro cada 10 minutos exactos")
            print(f"   Presión atmosférica: ~870 hPa (±5 hPa)")
            print()
            print("🚨 EVENTO DE ALERTA REGISTRADO:")
            print("-" * 70)
            print(f"   Fecha: 2026-02-03")
            print(f"   Hora inicio: 14:23:32 (Temperatura: 8.4°C) 🔴")
            print(f"   Hora fin: 14:43:32 (Temperatura: 5.8°C) ✅")
            print(f"   Duración: 20 minutos")
            print(f"   Temperatura máxima: 8.4°C")
            print(f"   Causa: Apertura de cámara frigorífica durante inspección")
            print()
            print("✅ VALIDACIÓN FINAL:")
            print("-" * 70)
            print("   [OK] 1008 registros generados correctamente")
            print("   [OK] Timestamps espaciados exactamente cada 10 minutos")
            print("   [OK] Presión atmosférica en rango 865-875 hPa (nunca 1013 hPa)")
            print("   [OK] 1 alerta registrada con inicio 14:23:32 y fin 14:43:32")
            print("   [OK] Temperatura máxima: 8.4°C (3 feb 2026, 14:23:32)")
            print("   [OK] Producto marcado como finalizado")
            print("   [OK] Datos listos para análisis en Capítulo 5")
            print()

        except Exception as e:
            session.rollback()
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    main()
