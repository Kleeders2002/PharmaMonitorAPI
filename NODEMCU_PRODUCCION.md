# Configuración NodeMCU para Producción (Render)

## 📍 Ubicación del archivo Arduino:

El código Arduino está en:
```
C:\Users\PC\Documents\Arduino\sketch_oct1b\sketch_oct1b.ino
```

## 🔧 Cambios necesarios en el código Arduino:

### 1. Cambiar URL del Backend ( línea 54 )

**Desarrollo (local):**
```cpp
const char* BACKEND_URL = "http://192.168.0.155:8000/nodemcu/data";
```

**Producción (Render):**
```cpp
const char* BACKEND_URL = "https://pharmamonitor-api.onrender.com/nodemcu/data";
```

### 2. Ajustar intervalo de envío (opcional, línea 57)

**Desarrollo (pruebas rápidas):**
```cpp
#define INTERVALO_ENVIO 10000  // 10 segundos
```

**Producción (ahorrar datos):**
```cpp
#define INTERVALO_ENVIO 60000  // 60 segundos (recomendado)
```

---

## 📤 Pasos para subir código al NodeMCU:

### Opción A: Arduino IDE (recomendado)

1. **Abrir el archivo:**
   ```
   File → Open → C:\Users\PC\Documents\Arduino\sketch_oct1b\sketch_oct1b.ino
   ```

2. **Seleccionar placa:**
   ```
   Tools → Board → ESP8266 Boards → NodeMCU 1.0 (ESP-12E Module)
   ```

3. **Seleccionar puerto:**
   ```
   Tools → Port → COM4 (o el puerto que aparezca)
   ```

4. **Subir:**
   ```
   Sketch → Upload (o Ctrl+U)
   ```

5. **Verificar:**
   - Abre el **Monitor Serial** (Ctrl+Shift+M)
   - Baud rate: **9600**
   - Deberías ver: "✅ WiFi conectado exitosamente!"

### Opción B: PlatformIO (alternativa)

Si usas VS Code con PlatformIO:

1. Abre la carpeta del proyecto en VS Code
2. Presiona F1 → "PlatformIO: Upload"
3. Monitor Serial: F1 → "PlatformIO: Open Serial Monitor"

---

## 🧪 Testing del Deploy:

### 1. Verificar que el backend funciona:

```bash
curl https://pharmamonitor-api.onrender.com/nodemcu/health
```

Respuesta esperada:
```json
{
  "status": "ok",
  "service": "nodemcu-endpoint",
  "message": "NodeMCU bidirectional communication endpoint is running"
}
```

### 2. Simular petición del NodeMCU:

```bash
curl -X POST https://pharmamonitor-api.onrender.com/nodemcu/data \
  -H "Content-Type: application/json" \
  -d "{\"temperatura\": 5.0, \"humedad\": 65.0, \"lux\": 200.0, \"presion\": 1013.0}"
```

Respuesta esperada:
```json
{
  "led_color": "verde",
  "status": "LED: VERDE | 1 dato(s) procesado(s)"
}
```

### 3. Verificar Monitor Serial del NodeMCU:

Deberías ver cada 10-60 segundos:
```
📊 Lecturas de los Sensores
---------------------------
🌡️  Temperatura (DHT22): 25.3 °C
💧 Humedad: 60.0 %
💡 Luz: 150.0 lx
🌍 Presión (SIMULADA): 850.12 hPa
---------------------------

========================================
📤 Enviando datos al backend:
{"temperatura":25.3,"humedad":60,"lux":150,"presion":850.12}
✅ Respuesta del backend:
{"led_color": "verde", "status": "..."}
🎨 LED Color: verde
========================================
```

---

## ⚠️ Problemas Comunes:

### Error: "connection refused" o "ECONNREFUSED"

**Causa:** Backend de Render está "durmiendo" (cold start)

**Solución:** Espera 30-60 segundos y el NodeMCU reintentará automáticamente

**Prevención:** Configura https://cron-job.org para hacer ping cada 5 min

---

### Error: "SSL certificate verification failed"

**Causa:** Certificado SSL de Render

**Solución:** El código ya maneja esto correctamente. Si persiste, verifica:
- Fecha/hora correcta en la computadora
- Última versión de la librería ESP8266WiFi

---

### Error: "HTTP Error 404"

**Causa:** URL incorrecta del backend

**Solución:** Verifica que la URL sea:
```
https://pharmamonitor-api.onrender.com/nodemcu/data
```

NOTA: Debe ser **https** (no http)

---

### Error: "HTTP Error 500"

**Causa:** Error interno del servidor

**Solución:**
1. Verifica los logs en Render dashboard
2. Verifica que la base de datos esté inicializada
3. Verifica que las variables de entorno estén configuradas

---

## 📊 Monitoreo en Producción:

### Ver logs en tiempo real:

1. Ve a https://dashboard.render.com
2. Selecciona "pharmamonitor-api"
3. Click "Logs"
4. Verás las peticiones del NodeMCU:
```
INFO:     123.45.67.89:54321 - "POST /nodemcu/data HTTP/1.1"
INFO:adapters.api.nodemcu:📥 Datos recibidos del NodeMCU: {...}
```

### Métricas importantes:

**En Render Dashboard:**
- CPU usage (debe ser < 50%)
- Memory usage (debe ser < 400 MB de 512 MB)
- Response time (debe ser < 500 ms)
- HTTP errors (debe ser 0%)

---

## 🔄 Actualizar NodeMCU en el futuro:

Si cambias el código del backend:

1. **Backend:** Solo haz push a GitHub (Render redeploya automáticamente)
2. **NodeMCU:** No necesita cambios (la URL sigue siendo la misma)

Si cambias la lógica del NodeMCU:

1. Modifica `sketch_oct1b.ino`
2. Sube al NodeMCU con Arduino IDE
3. Verifica en el Monitor Serial que funciona

---

## ✅ Checklist Pre-Producción:

NodeMCU:
- [ ] URL cambiada a `https://pharmamonitor-api.onrender.com/nodemcu/data`
- [ ] Intervalo de envío ajustado (60 seg recomendado)
- [ ] Código subido al NodeMCU
- [ ] Monitor Serial muestra datos correctos
- [ ] LED cambia de color según estado

Backend (Render):
- [ ] Servicio "New +" → "Web Service" conectado
- [ ] Repo GitHub conectado
- [ ] `render.yaml` detectado correctamente
- [ ] PostgreSQL 15 configurado
- [ ] Variables de entorno configuradas
- [ ] Deploy exitoso (check mark verde)
- [ ] Health check endpoint responde 200

Conexión:
- [ ] NodeMCU conecta a WiFi
- [ ] NodeMCU envía datos a Render
- [ ] Render responde con color de LED
- [ ] LED cambia según respuesta

---

## 🎯 URLs Importantes (Guarda estas):

- **Backend:** `https://pharmamonitor-api.onrender.com`
- **Health:** `https://pharmamonitor-api.onrender.com/nodemcu/health`
- **API Docs:** `https://pharmamonitor-api.onrender.com/docs`
- **Logs:** https://dashboard.render.com (→ tu servicio → Logs)
- **Monitor Serial NodeMCU:** `COM4` a 9600 baud
