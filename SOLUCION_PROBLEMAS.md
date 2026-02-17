# 🔧 Solución de Problemas - Sistema FHIR

## Problema Resuelto: "Not Found" en `/consulta-hc`

### ❌ Error Original
```json
{"detail":"Not Found"}
```

### 🔍 Causa
El código actualizado no estaba en el contenedor Docker. Los cambios en `app.py` y `templates/consulta-hc.html` no se habían copiado a la imagen.

### ✅ Solución
```bash
# Reconstruir la imagen de la aplicación
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
docker compose up -d --build app
```

### 📊 Verificación
```bash
# Verificar que el endpoint funciona
curl http://localhost:8001/consulta-hc

# Verificar API de pacientes
curl http://localhost:8001/api/v1/fhir/patients
```

---

## 🚨 Problemas Comunes y Soluciones

### 1. Error "Not Found" en endpoints nuevos

**Síntoma**: Endpoint devuelve 404 después de agregar código nuevo

**Causa**: Código no actualizado en el contenedor

**Solución**:
```bash
# Reconstruir la imagen
docker compose up -d --build app

# O reiniciar todo
docker compose down
docker compose up -d --build
```

---

### 2. HAPI FHIR Server "unhealthy"

**Síntoma**: `docker compose ps` muestra HAPI FHIR como "unhealthy"

**Causa**: El servidor tarda en iniciar (puede tomar 60-90 segundos)

**Solución**:
```bash
# Esperar y verificar logs
docker compose logs -f hapi-fhir

# Verificar metadata
curl http://localhost:8080/fhir/metadata
```

**Nota**: El sistema puede funcionar aunque HAPI FHIR esté "unhealthy" inicialmente.

---

### 3. Error "Connection refused" al crear paciente

**Síntoma**: Error al enviar POST a `/api/v1/fhir/patient`

**Causa**: HAPI FHIR Server no está listo

**Solución**:
```bash
# Verificar que HAPI FHIR responde
curl http://localhost:8080/fhir/metadata

# Si no responde, esperar más tiempo
sleep 30
curl http://localhost:8080/fhir/metadata
```

---

### 4. Base de datos FHIR no existe

**Síntoma**: Error "database fhir_db does not exist"

**Causa**: Script de inicialización no se ejecutó

**Solución**:
```bash
# Ejecutar script de inicialización
./init-databases.sh

# O crear manualmente
docker exec -i pg_nodo1 psql -U admin -d postgres -c "CREATE DATABASE fhir_db;"
```

---

### 5. Módulo Python no encontrado

**Síntoma**: `ModuleNotFoundError: No module named 'fhir_app'`

**Causa**: Estructura de carpetas incorrecta o falta `__init__.py`

**Solución**:
```bash
# Verificar estructura
ls -la backend/fhir_app/

# Crear __init__.py si falta
touch backend/fhir_app/__init__.py
touch backend/fhir_app/models/__init__.py
touch backend/fhir_app/transformers/__init__.py
touch backend/fhir_app/services/__init__.py

# Reconstruir
docker compose up -d --build app
```

---

### 6. Página en blanco o sin estilos

**Síntoma**: La página carga pero sin estilos CSS

**Causa**: Archivos estáticos no se copiaron

**Solución**:
```bash
# Verificar que el archivo existe
ls -la templates/consulta-hc.html

# Reconstruir imagen
docker compose up -d --build app
```

---

### 7. Error "httpx.ConnectError"

**Síntoma**: Error al conectar con HAPI FHIR desde la app

**Causa**: Nombre de host incorrecto o red no configurada

**Solución**:
```bash
# Verificar que ambos están en la misma red
docker network inspect historia-clinica-distribuida_historia_clinica_net

# Verificar que pueden comunicarse
docker exec historia_clinica_app ping -c 2 hapi-fhir
```

---

### 8. Pacientes no aparecen en la lista

**Síntoma**: La página de consulta muestra "No hay pacientes"

**Causa**: No hay pacientes creados o error en la consulta

**Solución**:
```bash
# Verificar directamente en HAPI FHIR
curl http://localhost:8080/fhir/Patient

# Crear paciente de prueba
./test-mvp-fhir.sh

# Verificar API
curl http://localhost:8001/api/v1/fhir/patients
```

---

## 🔄 Comandos de Diagnóstico

### Verificar Estado General
```bash
# Ver todos los servicios
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
docker compose ps

# Ver logs de la app
docker compose logs app --tail 50

# Ver logs de HAPI FHIR
docker compose logs hapi-fhir --tail 50
```

### Verificar Conectividad
```bash
# Desde el host
curl http://localhost:8001/api/health
curl http://localhost:8080/fhir/metadata

# Desde el contenedor de la app
docker exec historia_clinica_app curl http://hapi-fhir:8080/fhir/metadata
```

### Verificar Base de Datos
```bash
# Conectar a PostgreSQL
docker exec -it pg_nodo1 psql -U admin -d fhir_db

# Listar tablas FHIR
\dt

# Salir
\q
```

---

## 🧪 Script de Verificación Completa

Usa el script de prueba para verificar todo:

```bash
./test-mvp-fhir.sh
```

Este script verifica:
- ✅ Docker Compose
- ✅ Servicios activos
- ✅ API principal
- ✅ HAPI FHIR Server
- ✅ Creación de paciente
- ✅ Búsqueda de paciente
- ✅ Base de datos FHIR

---

## 🔧 Reinicio Completo

Si nada funciona, reinicia todo:

```bash
# Detener todo
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
docker compose down

# Eliminar volúmenes (CUIDADO: borra datos)
docker compose down -v

# Reconstruir todo
docker compose up -d --build

# Esperar a que todo inicie
sleep 30

# Inicializar bases de datos
./init-databases.sh

# Verificar
./test-mvp-fhir.sh
```

---

## 📞 Checklist de Verificación

Cuando algo no funciona, verifica en orden:

1. [ ] ¿Docker está corriendo?
   ```bash
   docker ps
   ```

2. [ ] ¿Los servicios están up?
   ```bash
   docker compose ps
   ```

3. [ ] ¿La app responde?
   ```bash
   curl http://localhost:8001/api/health
   ```

4. [ ] ¿HAPI FHIR responde?
   ```bash
   curl http://localhost:8080/fhir/metadata
   ```

5. [ ] ¿La base de datos FHIR existe?
   ```bash
   docker exec pg_nodo1 psql -U admin -l | grep fhir_db
   ```

6. [ ] ¿Los archivos están actualizados en el contenedor?
   ```bash
   docker exec historia_clinica_app ls -la templates/
   ```

7. [ ] ¿Hay errores en los logs?
   ```bash
   docker compose logs app --tail 20
   ```

---

## ✅ Estado Actual del Sistema

Después de la solución:

```bash
# Verificar endpoints
curl http://localhost:8001/consulta-hc          # ✅ OK
curl http://localhost:8001/registro-paciente    # ✅ OK
curl http://localhost:8001/api/v1/fhir/patients # ✅ OK

# Total de pacientes: 4
```

---

**Última actualización**: 2026-02-14 14:35  
**Estado**: ✅ TODOS LOS PROBLEMAS RESUELTOS
