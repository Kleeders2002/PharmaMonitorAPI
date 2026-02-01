"""
API Endpoints para comunicación bidireccional con NodeMCU.

Nueva arquitectura:
- NodeMCU → Backend (POST /nodemcu/data con sensores)
- Backend → NodeMCU (RESPONSE: {"led_color": "verde|amarillo|rojo"})
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from schemas.nodemcu import NodeMCUDataSchema, LEDResponseSchema
from adapters.db.sqlmodel_database import get_session
from services.data_service import procesar_datos_entrantes
from services.led_service import determinar_color_led_solo
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nodemcu", tags=["NodeMCU"])


@router.post("/data", response_model=LEDResponseSchema)
async def recibir_datos_nodemcu(
    datos: NodeMCUDataSchema,
    session: Session = Depends(get_session)
) -> LEDResponseSchema:
    """
    Recibe datos del NodeMCU, procesa, genera alertas, y retorna comando LED.

    **Nueva Arquitectura Bidireccional:**
    - NodeMCU envía datos de sensores en POST
    - Backend procesa datos, guarda en BD, genera alertas
    - Backend retorna color LED en la misma respuesta

    **Prioridad de LED:**
    1. 🔴 ROJO - Alertas PENDIENTES (bloqueo total hasta resolución manual)
    2. 🔴 ROJO - Sensores fallados
    3. 🟡 AMARILLO - Sensores en umbral de advertencia (90% del rango)
    4. 🟢 VERDE - Todo normal

    **Ejemplo de uso:**
    ```bash
    curl -X POST http://localhost:8000/nodemcu/data \\
      -H "Content-Type: application/json" \\
      -d '{"temperatura": 5.2, "humedad": 65, "lux": 150, "presion": 1013}'
    ```

    **Args:**
    - datos: Objeto con temperatura, humedad, lux, presion (todos opcionales)

    **Returns:**
    - LEDResponseSchema con led_color y status message
    """
    try:
        logger.info(f"📥 Datos recibidos del NodeMCU: {datos.model_dump()}")

        # ============================================================
        # PASO 1: Procesar datos entrantes
        # - Guardar en BD
        # - Generar alertas si corresponde
        # - Actualizar estado de sensores
        # ============================================================
        datos_guardados, sensores_fallados = procesar_datos_entrantes(
            temperatura=datos.temperatura,
            humedad=datos.humedad,
            lux=datos.lux,
            presion=datos.presion,
            session=session
        )

        if sensores_fallados:
            logger.warning(f"⚠️ Sensores fallados: {sensores_fallados}")

        if datos_guardados:
            logger.info(f"✅ {len(datos_guardados)} dato(s) guardado(s) en BD")
        else:
            logger.warning("⚠️ No se guardaron datos (posible fallo total de NodeMCU)")

        # ============================================================
        # PASO 2: Determinar color del LED
        # - Evaluar alertas pendientes (prioridad máxima)
        # - Evaluar sensores fallados
        # - Evaluar umbrales de advertencia
        # ============================================================
        sensor_data = {
            'temperatura': datos.temperatura,
            'humedad': datos.humedad,
            'lux': datos.lux,
            'presion': datos.presion
        }

        color_led = determinar_color_led_solo(session, sensor_data)

        # ============================================================
        # PASO 3: Retornar respuesta al NodeMCU
        # ============================================================
        status_msg = f"LED: {color_led.upper()}"
        if sensores_fallados:
            status_msg += f" | Sensores fallados: {', '.join(sensores_fallados)}"
        if datos_guardados:
            status_msg += f" | {len(datos_guardados)} dato(s) procesado(s)"

        logger.info(f"📤 Respuesta al NodeMCU: {status_msg}")

        return LEDResponseSchema(
            led_color=color_led,
            status=status_msg
        )

    except Exception as e:
        logger.error(f"❌ Error procesando datos del NodeMCU: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno procesando datos: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Endpoint simple para verificar que el servicio NodeMCU está activo.
    """
    return {
        "status": "ok",
        "service": "nodemcu-endpoint",
        "message": "NodeMCU bidirectional communication endpoint is running"
    }
