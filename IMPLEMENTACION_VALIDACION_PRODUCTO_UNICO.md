# Implementación: Validación de Producto Monitoreado Único

## Resumen de Cambios

Se implementó la **Opción A**: Validación al crear un `ProductoMonitoreado` para asegurar que solo exista un producto con monitoreo activo a la vez, alineándose con la lógica de negocio de un solo circuito Arduino/NodeMCU.

## Archivos Modificados

### 1. `core/repositories/producto_monitoreado_repository.py`

**Función modificada**: `create_producto_monitoreado()`

**Cambios**:
- Agregada validación al inicio de la función
- Verifica si existe algún `ProductoMonitoreado` con `fecha_finalizacion_monitoreo == None`
- Si existe un producto activo, lanza `HTTPException` con:
  - **Status Code**: 400
  - **Mensaje de error**: Estructurado con información detallada del producto activo
  - **Detalles incluidos**:
    - `error`: "producto_activo_existe"
    - `message`: Mensaje descriptivo para el usuario
    - `producto_activo_id`: ID del producto que está activo
    - `producto_activo_nombre`: Nombre del producto activo

**Ejemplo de respuesta de error**:
```json
{
  "detail": {
    "error": "producto_activo_existe",
    "message": "Ya existe un producto en monitoreo activo: 'Insulina Glargina' (ID: 5). Solo se puede monitorear un producto a la vez. Detén el monitoreo actual antes de comenzar uno nuevo.",
    "producto_activo_id": 5,
    "producto_activo_nombre": "Insulina Glargina"
  }
}
```

### 2. `services/data_service.py`

**Función modificada**: `procesar_datos_entrantes()`

**Cambios**:
- Optimizada la lógica de procesamiento de datos del NodeMCU
- Cambió de iterar sobre "todos los productos activos" a procesar "el único producto activo"
- Ahora usa `.first()` en lugar de `.all()` (más eficiente)
- Agregado manejo de caso cuando no hay producto activo (warning en logs, no es error)
- Removido el bucle `for` innecesario

**Beneficios**:
- Mejor rendimiento: una sola consulta en lugar de iterar
- Código más limpio y alineado con la lógica de negocio
- Log warning cuando no hay producto activo (visibilidad)

## Archivos Creados

### `test_validacion_producto_unico.py`

Script de prueba para validar la funcionalidad:

**Características**:
- Conecta a la base de datos configurada
- Verifica si existe un producto activo
- Intenta crear un segundo producto
- Muestra el resultado de la validación
- Proporciona instrucciones si no hay datos de prueba

**Uso**:
```bash
python test_validacion_producto_unico.py
```

## Lógica de Negocio Implementada

### Restricción
✅ **Solo un producto con monitoreo activo simultáneamente**

### Motivación
1. **Un solo circuito Arduino/NodeMCU** = una ubicación física de monitoreo
2. **Consistencia de datos**: Los sensores leen una sola ubicación
3. **Claridad**: 1:1 entre circuito y producto monitoreado
4. **Evita duplicación**: Anteriormente se creaban múltiples registros idénticos

### Flujo de Usuario

1. **Usuario activa monitoreo del Producto A** ✅
   ```
   POST /productosmonitoreados/
   → Creado exitosamente
   ```

2. **Usuario intenta activar monitoreo del Producto B** ❌
   ```
   POST /productosmonitoreados/
   → 400 Bad Request
   → "Ya existe un producto en monitoreo activo: 'Producto A' (ID: X).
      Solo se puede monitorear un producto a la vez.
      Detén el monitoreo actual antes de comenzar uno nuevo."
   ```

3. **Usuario detiene monitoreo del Producto A** ✅
   ```
   PATCH /productosmonitoreados/{id}/detener
   → Monitoreo detenido
   ```

4. **Usuario ahora puede activar monitoreo del Producto B** ✅
   ```
   POST /productosmonitoreados/
   → Creado exitosamente
   ```

## Impacto en el Sistema

### ✅ Mejoras
- **Integridad de datos**: Elimina duplicación de registros de monitoreo
- **Rendimiento**: Reduce consultas y procesamiento innecesario
- **Claridad**: La lógica del código refleja la realidad física
- **Experiencia de usuario**: Mensajes de error claros y accionables

### ⚠️ Consideraciones
- Los usuarios deben detener explícitamente el monitoreo actual antes de activar otro
- El frontend debería mostrar claramente el producto activo actual
- Considerar agregar un endpoint para "reemplazar" monitoreo (detener + activar en una operación)

## Próximas Mejoras Sugeridas

1. **Endpoint de reemplazo**: `PUT /productosmonitoreados/reemplazar`
   - Detiene el monitoreo actual y activa el nuevo en una sola operación
   - Más conveniente para el usuario

2. **Indicator en el frontend**: Mostrar claramente el producto activo
   - Badge o indicador visible
   - Botón "Detener monitoreo" prominent

3. **Log de auditoría**: La validación actual no rompa el monitoreo
   - Registrar intentos fallidos de crear segundo monitoreo
   - Métricas de uso

## Testing

### Manual
1. Activar monitoreo de un producto
2. Intentar activar monitoreo de otro producto
3. Verificar que recibe error 400 con mensaje descriptivo
4. Detener monitoreo del primer producto
5. Verificar que ahora puede activar el segundo

### Automático
```bash
python test_validacion_producto_unico.py
```

## Conclusión

La implementación alinea el sistema con la realidad física del hardware (un circuito Arduino) y mejora la integridad de datos, el rendimiento y la claridad del código.
