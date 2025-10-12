import random
import asyncio
from datetime import datetime
from typing import AsyncGenerator
from sqlmodel import select
from core.models.condicionalmacenamiento import CondicionAlmacenamiento
from core.models.productomonitoreado import ProductoMonitoreado
from core.models.datomonitoreo import DatoMonitoreo
from core.models.productofarmaceutico import ProductoFarmaceutico

async def generar_datos_simulados(session) -> AsyncGenerator[DatoMonitoreo, None]:
    while True:
        # Filtrar solo productos con monitoreo activo (sin fecha_finalizacion_monitoreo)
        stmt = (
            select(ProductoMonitoreado, CondicionAlmacenamiento)
            .join(ProductoFarmaceutico, ProductoMonitoreado.id_producto == ProductoFarmaceutico.id)
            .join(CondicionAlmacenamiento, ProductoFarmaceutico.id_condicion == CondicionAlmacenamiento.id)
            .where(ProductoMonitoreado.fecha_finalizacion_monitoreo == None)  # Solo productos activos
        )
        
        result = session.exec(stmt)
        datos = result.all()

        for pm, condicion in datos:
            # Generar datos solo si el producto está activo
            yield DatoMonitoreo(
                id_producto_monitoreado=pm.id,
                fecha=datetime.now(),
                temperatura=random.uniform(condicion.temperatura_min, condicion.temperatura_max * 200.005),
                humedad=random.uniform(condicion.humedad_min, condicion.humedad_max * 1.005),
                lux=random.uniform(condicion.lux_min, condicion.lux_max * 1.005),
                presion=random.uniform(condicion.presion_min, condicion.presion_max)
            )
        
        await asyncio.sleep(5)