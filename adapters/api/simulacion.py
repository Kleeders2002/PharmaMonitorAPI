# TEMPORAL: Endpoint para ejecutar simulación de insulina
# Este archivo se puede eliminar después de usar el script
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from adapters.db.sqlmodel_database import get_session
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/simulacion", tags=["Simulacion - TEMPORAL"])

class SimulacionResponse(BaseModel):
    status: str
    message: str

@router.post("/ejecutar-insulina", response_model=SimulacionResponse)
async def ejecutar_simulacion_insulina(session: Session = Depends(get_session)):
    """
    Endpoint TEMPORAL para ejecutar el script de simulación de insulina.

    POST /simulacion/ejecutar-insulina

    Después de usar este endpoint, puedes eliminar:
    - adapters/api/simulacion.py
    - La importación en main.py
    """
    try:
        # Importar funciones del script de simulación
        import sys
        import os
        from datetime import datetime, timedelta, timezone
        from sqlmodel import select
        import random

        # Importar modelos necesarios
        from core.models.condicionalmacenamiento import CondicionAlmacenamiento
        from core.models.formafarmaceutica import FormaFarmaceutica
        from core.models.productofarmaceutico import ProductoFarmaceutico
        from core.models.productomonitoreado import ProductoMonitoreado
        from core.models.datomonitoreo import DatoMonitoreo
        from core.models.alerta import Alerta, EstadoAlerta

        VENEZUELA_TZ = timezone(timedelta(hours=-4), name="America/Caracas")

        # =====================================================================
        # PASO 1: Limpiar datos existentes de insulina
        # =====================================================================
        alertas = session.exec(select(Alerta)).all()
        for alerta in alertas:
            if alerta.producto_monitoreado and "insulina" in alerta.producto_monitoreado.producto_farmaceutico.nombre.lower():
                session.delete(alerta)

        datos_monitoreo = session.exec(select(DatoMonitoreo)).all()
        for dato in datos_monitoreo:
            prod = session.get(ProductoMonitoreado, dato.producto_monitoreo_id)
            if prod and "insulina" in prod.producto_farmaceutico.nombre.lower():
                session.delete(dato)

        productos_monitoreados = session.exec(select(ProductoMonitoreado)).all()
        for pm in productos_monitoreados:
            if "insulina" in pm.producto_farmaceutico.nombre.lower():
                session.delete(pm)

        productos_farmaceuticos = session.exec(select(ProductoFarmaceutico)).all()
        for pf in productos_farmaceuticos:
            if "insulina" in pf.nombre.lower():
                session.delete(pf)

        condiciones = session.exec(select(CondicionAlmacenamiento)).all()
        for cond in condiciones:
            if cond.nombre == "Refrigeración Insulina":
                session.delete(cond)

        session.commit()

        # =====================================================================
        # PASO 2: Crear condición de almacenamiento
        # =====================================================================
        condicion = CondicionAlmacenamiento(
            nombre="Refrigeración Insulina",
            temperatura_minima=2.0,
            temperatura_maxima=8.0,
            humedad_relativa_minima=30.0,
            humedad_relativa_maxima=60.0,
            iluminancia_minima=0.0,
            iluminancia_maxima=300.0,
            presion_minima=865.0,
            presion_maxima=875.0
        )
        session.add(condicion)
        session.commit()
        session.refresh(condicion)

        # =====================================================================
        # PASO 3: Crear forma farmacéutica (Insulina)
        # =====================================================================
        forma = session.exec(
            select(FormaFarmaceutica).where(FormaFarmaceutica.descripcion == "Insulina")
        ).first()

        if not forma:
            from core.models.formafarmaceutica import FormaFarmaceutica
            forma = FormaFarmaceutica(descripcion="Insulina")
            session.add(forma)
            session.commit()
            session.refresh(forma)

        if not forma:
            forma = FormaFarmaceutica(descripcion="Insulina")
            session.add(forma)
            session.commit()
            session.refresh(forma)

        # =====================================================================
        # PASO 4: Crear producto farmacéutico "Insulina Humana"
        # =====================================================================
        producto = ProductoFarmaceutico(
            nombre="Insulina Humana",
            descripcion="Insulina Humana 100 UI/mL - Monitoreo de cadena de frío para prueba piloto",
            imagen="https://res.cloudinary.com/drlypxphc/image/upload/v1/PharmaMonitor/insulina_humana",
            forma_farmaceutica_id=forma.id,
            condicion_almacenamiento_id=condicion.id
        )
        session.add(producto)
        session.commit()
        session.refresh(producto)

        # =====================================================================
        # PASO 5: Crear producto monitoreado
        # =====================================================================
        producto_monitoreado = ProductoMonitoreado(
            producto_farmaceutico_id=producto.id,
            fecha_inicio=datetime(2026, 2, 2, 15, 30, 0, tzinfo=VENEZUELA_TZ),
            fecha_fin=None,  # Activo
            activo=True
        )
        session.add(producto_monitoreado)
        session.commit()
        session.refresh(producto_monitoreado)

        # =====================================================================
        # PASO 6: Generar 1008 registros de datos de monitoreo
        # =====================================================================
        fecha_inicio = datetime(2026, 1, 30, 11, 13, 32, tzinfo=VENEZUELA_TZ)
        fecha_fin = datetime(2026, 2, 6, 11, 13, 32, tzinfo=VENEZUELA_TZ)
        intervalo = timedelta(minutes=10)

        fecha_actual = fecha_inicio
        registros_creados = 0

        # Fechas del evento de alerta
        fecha_alerta_inicio = datetime(2026, 2, 3, 14, 23, 32, tzinfo=VENEZUELA_TZ)
        fecha_alerta_pico = datetime(2026, 2, 3, 14, 33, 32, tzinfo=VENEZUELA_TZ)
        fecha_alerta_fin = datetime(2026, 2, 3, 14, 43, 32, tzinfo=VENEZUELA_TZ)

        while fecha_actual <= fecha_fin:
            # Determinar valores según la fecha
            if fecha_actual == datetime(2026, 2, 3, 14, 13, 32, tzinfo=VENEZUELA_TZ):
                # Último registro normal antes de la alerta
                temperatura = 4.2
                humedad = 45.0
                lux = 10.0
                presion = 870.0
            elif fecha_actual == fecha_alerta_inicio:
                # Inicio de la alerta - puerta abierta
                temperatura = 8.4
                humedad = 62.0
                lux = 320.0
                presion = 867.0
            elif fecha_actual == fecha_alerta_pico:
                # Pico máximo de temperatura
                temperatura = 8.4
                humedad = 65.0
                lux = 350.0
                presion = 865.0
            elif fecha_actual == fecha_alerta_fin:
                # Alerta finalizada - enfriamiento activo
                temperatura = 6.8
                humedad = 55.0
                lux = 15.0
                presion = 872.0
            elif fecha_alerta_inicio < fecha_actual < fecha_alerta_fin:
                # Dentro del periodo de alerta
                temperatura = 8.4
                humedad = 63.0
                lux = 330.0
                presion = 866.0
            else:
                # Operación normal con variaciones realistas del compresor
                # Ciclo de compresor: 20-30 minutos
                minuto_del_dia = fecha_actual.hour * 60 + fecha_actual.minute
                fase_compresor = minuto_del_dia % 25  # Ciclo de 25 min

                if fase_compresor < 15:  # Compresor ON (enfriando)
                    base_temp = 3.2
                    base_hum = 42.0
                else:  # Compresor OFF (temperatura subiendo)
                    base_temp = 5.8
                    base_hum = 52.0

                temperatura = base_temp + random.uniform(-0.3, 0.3)
                humedad = base_hum + random.uniform(-2.0, 2.0)
                lux = random.uniform(5.0, 15.0)
                presion = 870.0 + random.uniform(-5.0, 5.0)

            # Crear el dato de monitoreo
            dato = DatoMonitoreo(
                producto_monitoreado_id=producto_monitoreado.id,
                temperatura=round(temperatura, 1),
                humedad_relativa=round(humedad, 1),
                iluminancia=round(lux, 1),
                presion_atmosferica=round(presion, 1),
                fecha_hora=fecha_actual
            )
            session.add(dato)
            registros_creados += 1
            fecha_actual += intervalo

        session.commit()

        # =====================================================================
        # PASO 7: Crear alerta del evento
        # =====================================================================
        alerta = Alerta(
            producto_monitoreado_id=producto_monitoreado.id,
            fecha_hora=fecha_alerta_inicio,
            descripcion="ALERTA ACTIVADA: Temperatura fuera de rango (8.4°C). Posible apertura de puerta del refrigerador.",
            estado=EstadoAlerta.PENDIENTE
        )
        session.add(alerta)
        session.commit()
        session.refresh(alerta)

        # Actualizar la alerta a RESUELTA cuando finaliza el evento
        alerta.estado = EstadoAlerta.RESUELTA
        alerta.descripcion = f"ALERTA FINALIZADA: Temperatura normalizada. Evento de apertura de puerta detectado el {fecha_alerta_inicio.strftime('%d/%m/%Y')}. Duración: 20 minutos."
        alerta.fecha_resolucion = fecha_alerta_fin
        session.commit()

        return {
            "status": "success",
            "message": f"✅ Simulación completada con éxito. Se generaron {registros_creados} registros de monitoreo para 'Insulina Humana'."
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al ejecutar la simulación: {str(e)}"
        )
