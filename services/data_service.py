from sqlmodel import Session
from core.repositories import dato_monitoreo_repository, alerta_repository
from typing import AsyncGenerator, Optional
from core.models.datomonitoreo import DatoMonitoreo
from adapters.arduino_adapter import sensor_manager

async def procesar_datos(datos: AsyncGenerator[Optional[DatoMonitoreo], None], session: Session):
    """
    Procesa datos de monitoreo y maneja alertas de sistema con detección por sensor.

    Args:
        datos: Generador async que yield DatoMonitoreo o None
        session: Sesión de base de datos
    """
    nodemcu_fallado_completamente = False
    sensores_fallados_anteriormente = set()

    async for dato in datos:
        try:
            if dato is None:
                # NodeMCU completo no responde
                if not nodemcu_fallado_completamente:
                    print("⚠️ NodeMCU no detectado - Creando alertas críticas...")
                    alerta_repository.crear_alerta_sensor_no_disponible(session, sensores_fallidos=['temperatura', 'humedad'])
                    nodemcu_fallado_completamente = True
                else:
                    print("⚠️ NodeMCU sigue sin responder - Esperando recuperación...")
                continue

            # NodeMCU responde, verificar sensores individuales
            if nodemcu_fallado_completamente:
                # NodeMCU se restauró
                print("✅ NodeMCU restaurado - Cerrando alertas de sistema...")
                alertas_cerradas = alerta_repository.cerrar_alerta_sensor_no_disponible(session)
                print(f"✅ {alertas_cerradas} alerta(s) cerrada(s)")
                nodemcu_fallado_completamente = False
                sensores_fallados_anteriormente.clear()

            # Verificar estado de sensores individuales
            sensor_status = sensor_manager.get_sensor_status()
            sensores_fallados = sensor_status.get_failed_sensors()

            if sensores_fallados:
                # Hay sensores específicos fallidos
                if sensores_fallados != sensores_fallados_anteriormente:
                    print(f"⚠️ Sensores fallidos detectados: {sensores_fallados}")
                    alerta_repository.crear_alerta_sensor_no_disponible(session, sensores_fallidos=sensores_fallidos)
                    sensores_fallados_anteriormente = set(sensores_fallados)
            elif sensores_fallados_anteriormente:
                # Sensores se restauraron
                print(f"✅ Sensores restaurados: {sensores_fallados_anteriormente}")
                alertas_cerradas = alerta_repository.cerrar_alerta_sensor_no_disponible(session)
                print(f"✅ {alertas_cerradas} alerta(s) de sensor cerrada(s)")
                sensores_fallados_anteriormente.clear()

            # Guardar dato en DB (solo si hay datos válidos)
            if dato.temperatura is not None or dato.humedad is not None:
                db_dato = dato_monitoreo_repository.create_dato_monitoreo(session, dato)

                # Generar alertas si valores están fuera de rango
                alerta_repository.crear_alerta(session, db_dato)

        except Exception as e:
            print(f"Error procesando dato: {str(e)}")