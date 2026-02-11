# TEMPORAL: Endpoint para ejecutar simulación de insulina
# Este archivo se puede eliminar después de usar el script
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, delete
from adapters.db.sqlmodel_database import get_session
from pydantic import BaseModel
from typing import Dict, Any
import random
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/simulacion", tags=["Simulacion - TEMPORAL - v2"])

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
        from sqlmodel import select
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
        # Buscar el producto "Insulina Humana"
        productos_insulina = session.exec(
            select(ProductoFarmaceutico).where(ProductoFarmaceutico.nombre.ilike("%insulina%"))
        ).all()

        # Obtener IDs de productos para borrar en cascada con DELETE directo
        producto_ids = [pf.id for pf in productos_insulina]

        if producto_ids:
            # Obtener productos monitoreados relacionados (solo IDs)
            productos_mon = session.exec(
                select(ProductoMonitoreado).where(ProductoMonitoreado.id_producto.in_(producto_ids))
            ).all()
            pm_ids = [pm.id for pm in productos_mon]

            if pm_ids:
                # Borrar alertas relacionadas (DELETE directo)
                session.exec(delete(Alerta).where(Alerta.id_producto_monitoreado.in_(pm_ids)))

                # Borrar datos de monitoreo (DELETE directo)
                session.exec(delete(DatoMonitoreo).where(DatoMonitoreo.id_producto_monitoreado.in_(pm_ids)))

                # Borrar productos monitoreados
                session.exec(delete(ProductoMonitoreado).where(ProductoMonitoreado.id.in_(pm_ids)))

            # Borrar productos farmacéuticos
            session.exec(delete(ProductoFarmaceutico).where(ProductoFarmaceutico.id.in_(producto_ids)))

        # Eliminar condición de almacenamiento "Refrigeración Insulina" si existe
        session.exec(delete(CondicionAlmacenamiento).where(CondicionAlmacenamiento.nombre == "Refrigeración Insulina"))

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
        # PASO 3: Obtener o crear forma farmacéutica "Insulina"
        # =====================================================================
        forma = session.exec(
            select(FormaFarmaceutica).where(FormaFarmaceutica.descripcion == "Insulina")
        ).first()

        if not forma:
            forma = FormaFarmaceutica(descripcion="Insulina")
            session.add(forma)
            session.commit()
            session.refresh(forma)

        # =====================================================================
        # PASO 4: Crear producto farmacéutico "Insulina Humana"
        # =====================================================================
        producto = ProductoFarmaceutico(
            id_forma_farmaceutica=forma.id,
            id_condicion=condicion.id,
            nombre="Insulina Humana",
            formula="C257H383N65O77S6",
            concentracion="100 UI/mL",
            indicaciones="Tratamiento de diabetes mellitus tipo 1 y tipo 2",
            contraindicaciones="Hipoglucemia, hipersensibilidad a la insulina",
            efectos_secundarios="Hipoglucemia, lipodistrofia, reacciones en el sitio de inyección",
            foto="https://res.cloudinary.com/drlypxphc/image/upload/v1/PharmaMonitor/insulina_humana"
        )
        session.add(producto)
        session.commit()
        session.refresh(producto)

        # =====================================================================
        # PASO 5: Crear producto monitoreado
        # =====================================================================
        producto_monitoreado = ProductoMonitoreado(
            id_producto=producto.id,
            localizacion="Refrigerador Farmacia - Estante 2",
            fecha_inicio_monitoreo=datetime(2026, 2, 2, 15, 30, 0, tzinfo=VENEZUELA_TZ),
            fecha_finalizacion_monitoreo=None,
            cantidad=10
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
        dato_alerta_id = None

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
                id_producto_monitoreado=producto_monitoreado.id,
                fecha=fecha_actual,
                temperatura=round(temperatura, 1),
                humedad=round(humedad, 1),
                lux=round(lux, 1),
                presion=round(presion, 1)
            )
            session.add(dato)
            session.flush()  # Para obtener el ID del dato

            # Guardar el ID del dato de la alerta para crear la alerta después
            if fecha_actual == fecha_alerta_inicio:
                dato_alerta_id = dato.id

            registros_creados += 1
            fecha_actual += intervalo

        session.commit()

        # =====================================================================
        # PASO 7: Crear alerta del evento
        # =====================================================================
        # Crear la alerta con el dato de monitoreo que supera el límite
        alerta = Alerta(
            id_producto_monitoreado=producto_monitoreado.id,
            id_dato_monitoreo=dato_alerta_id,
            id_condicion=condicion.id,
            parametro_afectado="temperatura",
            valor_medido=8.4,
            limite_min=condicion.temperatura_minima,
            limite_max=condicion.temperatura_maxima,
            mensaje="ALERTA ACTIVADA: Temperatura fuera de rango (8.4°C). Posible apertura de puerta del refrigerador.",
            fecha_generacion=fecha_alerta_inicio,
            estado=EstadoAlerta.PENDIENTE
        )
        session.add(alerta)
        session.commit()
        session.refresh(alerta)

        # Actualizar la alerta a RESUELTA cuando finaliza el evento
        alerta.estado = EstadoAlerta.RESUELTA
        alerta.mensaje = f"ALERTA FINALIZADA: Temperatura normalizada. Evento de apertura de puerta detectado el {fecha_alerta_inicio.strftime('%d/%m/%Y')}. Duración: 20 minutos."
        alerta.fecha_resolucion = fecha_alerta_fin
        duracion_segundos = (fecha_alerta_fin - fecha_alerta_inicio).total_seconds()
        alerta.duracion_minutos = round(duracion_segundos / 60, 2)
        session.commit()

        return {
            "status": "success",
            "message": f"✅ Simulación completada con éxito. Se generaron {registros_creados} registros de monitoreo para 'Insulina Humana'."
        }

    except Exception as e:
        session.rollback()
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error al ejecutar la simulación: {str(e)}"
        )
