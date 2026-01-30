# Guía de Deployment en Render.com

## 🚀 Preparación del Repositorio

Los siguientes archivos ya fueron creados/actualizados:

### ✅ Archivos Configurados:
- `render.yaml` - Configuración automática del servicio
- `.env.example` - Plantilla de variables de entorno
- `requirements.txt` - Dependencias actualizadas
- `.gitignore` - Archivos excluidos del repositorio
- `config.py` - Configuración centralizada

## 📋 Pasos para Deployment en Render

### 1. Crear cuenta en Render
- Ve a [render.com](https://render.com)
- Regístrate con tu cuenta de GitHub

### 2. Crear New Web Service
1. Click en "New +" → "Web Service"
2. Conecta tu repositorio `PharmaMonitorAPI`
3. Render detectará automáticamente `render.yaml`

### 3. Configurar Variables de Entorno
En el dashboard de Render, agrega estas variables:

```bash
# Database (automática desde render.yaml)
DATABASE_URL=(automática desde la base de datos de Render)

# NodeMCU - SOLO FUNCIONA EN RED LOCAL
NODEMCU_IP=192.168.0.117
USE_REAL_SENSORS=false  # ⚠️ Cambiar a false en producción

# JWT
JWT_SECRET=tu-clave-secreta-super-segura-aqui

# Environment
ENVIRONMENT=production
```

### 4. Crear Base de Datos PostgreSQL
1. En Render, click "New +" → "PostgreSQL"
2. Nombre: `pharmamonitor-db`
3. Región: Más cercana a tus usuarios
4. Plan: **Free** (hasta 90 días)

## ⚠️ PROBLEMA CRÍTICO: NodeMCU en Red Local

### El Problema:
```
Tu API en Render (nube)  ←→  NodeMCU en tu casa (192.168.0.117)
         ❌ NO PUEDEN CONECTARSE
```

### Soluciones:

#### Opción A: MODO SIMULADO (Recomendado para empezar)
Usar datos simulados en la nube:

```bash
# En variables de entorno de Render:
USE_REAL_SENSORS=false
```

El sistema generará datos simulados automáticamente.

#### Opción B: Tunnel a NodeMCU (Avanzado)
Exponer tu NodeMCU a internet con **ngrok** o **Cloudflare Tunnel**:

1. Instalar ngrok en tu casa:
```bash
# En la PC donde está el NodeMCU
ngrok http 80
```

2. ngrok te dará una URL pública: `https://abc123.ngrok.io`

3. Configurar en Render:
```bash
NODEMCU_IP=abc123.ngrok.io
NODEMCU_PORT=443
USE_REAL_SENSORS=true
```

⚠️ **Limitaciones de ngrok free:**
- La URL cambia cada vez que reinicias ngrok
- Límite de conexiones por mes
- No es ideal para producción

#### Opción C: Servidor Propio (Ideal)
Desplegar todo en tu propio servidor:
- Comprar un VPS ($3-5/mes)
- Desplegar API + NodeMCU en misma red
- O usar Raspberry Pi + NodeMCU

## 🧪 Testing Local con Variables de Entorno

Crea un archivo `.env` local:

```bash
# .env
DATABASE_URL=postgresql://postgres:kleeders2002@localhost/PharmaMonitorDB
JWT_SECRET=secreto-local
NODEMCU_IP=192.168.0.117
USE_REAL_SENSORS=true
ENVIRONMENT=development
```

## 📊 Planes de Render

| Plan | Precio | RAM | CPU | Límite |
|------|--------|-----|-----|--------|
| **Free** | $0 | 512MB | 0.1 | Sleep después de 15min inactividad |
| **Starter** | $7/mes | 512MB | 0.5 | Siempre activo |
| **Standard** | $25/mes | 2GB | 1 | Mejor performance |

⚠️ **Plan Free tiene limitaciones:**
- La API se "duerme" después de 15 min sin uso
- Tarda ~30 seg en "despertar"
- NO es ideal para background tasks continuas

**Recomendación:** Mínimo plan **Starter ($7/mes)** para producción.

## 🔍 Verificar Deployment

Después del deployment:

1. **Ver logs** en Render Dashboard
2. **Probar health check:** `https://tu-api.onrender.com/docs`
3. **Monitorear** las background tasks en los logs

## 📝 URLs Importantes

- API Docs: `https://tu-api.onrender.com/docs`
- API Redoc: `https://tu-api.onrender.com/redoc`
- Health Check: `https://tu-api.onrender.com/`

## ❌ Problemas Comunes

### Error: "Database connection failed"
→ Verificar que `DATABASE_URL` esté correcta en Render

### Error: "NodeMCU not responding"
→ Normal en producción (nube no puede conectar a red local)
→ Usar `USE_REAL_SENSORS=false`

### Error: "Port already in use"
→ Render asigna puerto automáticamente con `$PORT`

### Background tasks no corren
→ Plan Free "duerme" la API
→ Necesitas plan Starter o superior

## ✅ Checklist Pre-Deployment

- [ ] Actualizar `requirements.txt`
- [ ] Configurar variables de entorno
- [ ] Crear base de datos en Render
- [ ] Configurar `USE_REAL_SENSORS=false` en producción
- [ ] Probar API localmente con `.env`
- [ ] Hacer commit y push de cambios
- [ ] Conectar repositorio a Render
- [ ] Verificar logs después del deployment

## 🎯 Alternativas a Render

Si Render no funciona, prueba:

| Plataforma | Gratis | Background Tasks | Dificultad |
|------------|--------|------------------|------------|
| **Railway.app** | $5 crédito | ✅ Sí | Fácil |
| **Fly.io** | Sí (limitado) | ✅ Sí | Media |
| **Koyeb** | Sí | ✅ Sí | Fácil |
| **Heroku** | $5/mes | ✅ Sí | Fácil |
