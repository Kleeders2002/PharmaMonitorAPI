# PharmaMonitor API - Deploy en Render

## 🚀 Deploy Rápido en Render (Gratis)

### Pasos:

1. **Conectar GitHub a Render**
   - Ve a https://render.com
   - Sign up/Login con GitHub
   - Click "New +" → "Web Service"
   - Conecta tu repo `Kleeders2002/PharmaMonitorAPI`

2. **Configuración automática con `render.yaml`**
   - Render detectará automáticamente el archivo `render.yaml`
   - Configurará:
     - Python 3.11
     - PostgreSQL 15
     - Variables de entorno
     - Comando de inicio

3. **Deploy inicial**
   - Click "Create Web Service"
   - Render instalará dependencias (`pip install -r requirements.txt`)
   - Iniciará el servidor con `uvicorn main:app`
   - Tu backend estará en: `https://pharmamonitor-api.onrender.com`

4. **Configurar NodeMCU**
   - Actualiza la URL en el código Arduino:
   ```cpp
   const char* BACKEND_URL = "https://pharmamonitor-api.onrender.com/nodemcu/data";
   ```
   - Sube el código al NodeMCU

5. **¡Listo!**
   - NodeMCU enviará datos a tu backend en Render
   - NO necesitas ngrok ni túneles
   - LED se actualizará automáticamente

---

## ⚠️ Limitaciones del Plan GRATIS:

| Recurso | Límite | Solución |
|---------|--------|----------|
| **Inactividad** | 15 min | El backend se "duerme" si no recibe tráfico |
| **Spin-up** | ~30-60 seg | Primer request después de dormir tarda más |
| **PostgreSQL** | 90 días | BD se borra después de 90 días |
| **RAM** | 512 MB | Suficiente para FastAPI + SQLModel |

---

## 🔧 Solución al problema de inactividad (15 min):

El backend de Render se "duerme" después de 15 minutos sin recibir tráfico.

### Opción 1: Configurar un cron job externo (RECOMENDADO)

Usa **cron-job.org** (gratis) para hacer un ping cada 5 minutos:

```
URL: https://pharmamonitor-api.onrender.com/nodemcu/health
Frequency: Every 5 minutes
```

### Opción 2: Uptimerobot (alternativa gratis)

https://uptimerobot.com/

- Monitorea tu servicio cada 5 minutos
- Mantiene el backend despierto
- Gratis hasta 50 monitors

---

## 📊 Monitoreo del Deploy:

### Ver logs en Render:
1. Ve a tu servicio en Render dashboard
2. Click "Logs"
3. Verás logs del NodeMCU enviando datos:
```
INFO:     192.168.0.117:12345 - "POST /nodemcu/data HTTP/1.1"
INFO:adapters.api.nodemcu:📥 Datos recibidos del NodeMCU: {...}
INFO:adapters.api.nodemcu:📤 Respuesta al NodeMCU: LED: VERDE
```

### Base de datos:
- Render provee PostgreSQL 15 gratis
- Para acceder: `psql $DATABASE_URL` (desde CLI)
- O usa TablePlus/DBeaver para conectar

---

## 🔄 Actualizar el backend:

Automático desde GitHub:
```bash
git add .
git commit -m "feat: nueva funcionalidad"
git push
```

Render detectará el push y redeployará automáticamente (~1-2 min).

---

## 🆘 Troubleshooting:

### Error: "Sleeping" en Render dashboard
**Causa:** Backend sin tráfico por 15 min
**Solución:** Configura cron-job.org o uptimerobot.com

### Error: 502 Bad Gateway desde NodeMCU
**Causa:** Backend despertando (cold start)
**Solución:** El NodeMCU ya reintentará automáticamente, espera 30-60 seg

### Error: 90 días alcanzado en PostgreSQL
**Causa:** BD gratuita expira a los 90 días
**Solución:**
1. Exporta datos: `pg_dump $DATABASE_URL > backup.sql`
2. Borra servicio BD en Render
3. Crea nueva BD
4. Importa datos: `psql $NEW_DATABASE_URL < backup.sql`

---

## 💡 Upgrade a Render Paid ($7/mes):

Si necesitas producción permanente:
- Sin límite de 90 días
- Sin sleep por inactividad
- Más RAM/CPU
- https://render.com/pricing

---

## 📱 Actualizar NodeMCU para Producción:

En el código Arduino (`sketch_oct1b.ino`):

```cpp
// Cambiar URL a producción
const char* BACKEND_URL = "https://pharmamonitor-api.onrender.com/nodemcu/data";

// Reducir intervalo de envío para ahorrar datos
#define INTERVALO_ENVIO 30000  // 30 segundos (en lugar de 10)
```

---

## ✅ Checklist antes del deploy:

- [ ] `requirements.txt` actualizado
- [ ] `render.yaml` configurado
- [ ] `NODEMCU_IP` eliminado de variables de entorno
- [ ] `USE_REAL_SENSORS=true` configurado
- [ ] Código Arduino actualizado con URL de Render
- [ ] Probar localmente: `uvicorn main:app --port 8000`
- [ ] Verificar que POST /nodemcu/data funciona

---

## 🎯 URLs Importantes:

- **Backend:** `https://pharmamonitor-api.onrender.com`
- **API Docs:** `https://pharmamonitor-api.onrender.com/docs`
- **Health Check:** `https://pharmamonitor-api.onrender.com/nodemcu/health`
- **Dashboard:** https://dashboard.render.com

---

## 📞 Soporte:

- Render docs: https://render.com/docs
- FastAPI docs: https://fastapi.tiangolo.com/deployment/render/
