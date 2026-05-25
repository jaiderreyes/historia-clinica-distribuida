# app.py - Sistema de Historia Clínica Distribuida con FHIR
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import middleware
import psycopg2
from fastapi_mcp import FastApiMCP

# Agregar backend al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from fhir_app.models.patient_model import PatientIdentificationData
from fhir_app.transformers.fhir_transformer import FHIRTransformer
from fhir_app.services.fhir_service import FHIRService
from fhir_app.services.db_service import DBService

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cargar HTML de FIRH al iniciar
FIRH_HTML = None
_firh_path = os.path.join(BASE_DIR, "templates", "firh.html")
if os.path.isfile(_firh_path):
    with open(_firh_path, "r", encoding="utf-8") as _f:
        FIRH_HTML = _f.read()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de nodos (usar nombres de contenedores en Docker)
USE_DOCKER_NAMES = os.getenv("USE_DOCKER_NAMES", "false").lower() == "true"

if USE_DOCKER_NAMES:
    NODES_CONFIG = [
        {"id": "pg_nodo1", "host": "pg_nodo1", "port": 5432, "display_port": "5433"},
        {"id": "pg_nodo2", "host": "pg_nodo2", "port": 5432, "display_port": "5434"},
        {"id": "pg_nodo3", "host": "pg_nodo3", "port": 5432, "display_port": "5435"},
    ]
else:
    NODES_CONFIG = [
        {"id": "pg_nodo1", "host": "localhost", "port": 5433, "display_port": "5433"},
        {"id": "pg_nodo2", "host": "localhost", "port": 5434, "display_port": "5434"},
        {"id": "pg_nodo3", "host": "localhost", "port": 5435, "display_port": "5435"},
    ]


from fastapi.responses import HTMLResponse, RedirectResponse


@app.get("/", response_class=RedirectResponse)
async def root_redirect():
    return RedirectResponse(url="/home", status_code=302)


@app.get("/home", response_class=HTMLResponse)
@app.get("/home/", response_class=HTMLResponse)
async def home_page():
    """Pantalla de inicio — hub de navegación entre módulos"""
    with open(os.path.join(BASE_DIR, "templates", "home.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/dashboard", response_class=HTMLResponse)
@app.get("/dashboard/", response_class=HTMLResponse)
async def dashboard_page():
    """Nodes Monitor — estado de los nodos PostgreSQL y simulador de queries"""
    with open(os.path.join(BASE_DIR, "templates", "index.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/health")
async def health():
    return {"status": "ok", "home": "/home", "medico": "/medico", "admision": "/admision", "carga_hc": "/carga-hc", "hc": "/hc"}


@app.get("/hc", response_class=HTMLResponse)
@app.get("/hc/", response_class=HTMLResponse)
@app.get("/firh", response_class=HTMLResponse)
@app.get("/firh/", response_class=HTMLResponse)
@app.get("/carga-hc", response_class=HTMLResponse)
@app.get("/carga-hc/", response_class=HTMLResponse)
async def firh_page():
    if FIRH_HTML is None:
        raise HTTPException(status_code=500, detail="Plantilla firh.html no encontrada")
    return HTMLResponse(content=FIRH_HTML)


@app.get("/api/nodes")
async def get_nodes():
    """Obtiene el estado de los nodos verificando conectividad a PostgreSQL"""
    nodes_status = []
    
    for node_config in NODES_CONFIG:
        node_info = {
            "id": node_config["id"],
            "port": node_config["display_port"],
            "status": "unknown"
        }
        
        try:
            # Intentar conectar a PostgreSQL para verificar el estado
            conn = psycopg2.connect(
                host=node_config["host"],
                port=node_config["port"],
                user="admin",
                password="admin",
                dbname="historia_clinica",
                connect_timeout=3
            )
            conn.close()
            node_info["status"] = "running"
        except Exception as e:
            node_info["status"] = "exited"
            node_info["error"] = str(e)
        
        nodes_status.append(node_info)
    
    return nodes_status


@app.post("/api/nodes/{node_id}/{action}")
async def control_node(node_id: str, action: str):
    """
    Endpoint simplificado para control de nodos.
    En la versión Dockerizada, el control se hace desde el host con docker compose.
    """
    return {
        "message": f"Para controlar nodos en Docker, usa: docker compose {action} {node_id}",
        "note": "Control de contenedores disponible desde el host"
    }


class QueryRequest(BaseModel):
    query: str


@app.post("/api/execute-query")
async def execute_query(request: QueryRequest):
    try:
        resultado = middleware.ejecutar_query_en_todos_los_nodos(request.query)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS FHIR - MVP
# ============================================================================

# Inicializar servicios
fhir_service = FHIRService()
db_service = DBService()


# ============================================================================
# ENDPOINTS DE ADMISIÓN — Flujo de llegada de nuevo paciente
# Estándar HL7 FHIR R4 + DB Distribuida
# ============================================================================

@app.get("/admision", response_class=HTMLResponse)
@app.get("/admision/", response_class=HTMLResponse)
async def admision_page():
    """Vista de admisión: verifica si el paciente existe antes de registrarlo"""
    try:
        with open(os.path.join(BASE_DIR, "templates", "admision-paciente.html"), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Plantilla admision-paciente.html no encontrada")


@app.get("/api/v1/admision/verificar/{documento_id}")
async def verificar_paciente(documento_id: str):
    """
    Punto de entrada principal del flujo de admisión.

    Estrategia de búsqueda (HL7 Patient Matching):
    1. Busca en la DB local distribuida (PostgreSQL, nodo según fragmentación)
    2. Si no está en DB, busca en HAPI FHIR por identifier
    3. Retorna: encontrado_local, encontrado_fhir, datos_paciente

    Basado en IHE PIX/PDQ y HL7 FHIR R4 Patient $match.
    """
    try:
        doc_id_int = int(documento_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="documento_id debe ser numérico")

    resultado = {
        "documento_id": documento_id,
        "encontrado_local": False,
        "encontrado_fhir": False,
        "paciente_local": None,
        "paciente_fhir": None,
        "nodo_asignado": None,
        "accion_recomendada": "registrar",
    }

    # 1. Buscar en DB local
    try:
        paciente_local = DBService.buscar_paciente(doc_id_int)
        if paciente_local:
            resultado["encontrado_local"] = True
            resultado["paciente_local"] = paciente_local
            resultado["accion_recomendada"] = "admitir_existente"
    except Exception as e:
        resultado["error_local"] = str(e)

    # 2. Buscar en HAPI FHIR si no está en local o para enriquecer
    try:
        bundle = await fhir_service.search_patient_by_identifier(documento_id)
        entries = bundle.get("entry", [])
        if entries:
            resultado["encontrado_fhir"] = True
            resultado["paciente_fhir"] = entries[0]["resource"]
            if not resultado["encontrado_local"]:
                resultado["accion_recomendada"] = "importar_de_fhir"
    except Exception as e:
        resultado["error_fhir"] = str(e)

    # 3. Determinar nodo asignado
    if doc_id_int < 4_000_000_000:
        resultado["nodo_asignado"] = "nodo1 (doc < 4.000.000.000)"
    elif doc_id_int < 7_000_000_000:
        resultado["nodo_asignado"] = "nodo2 (4B – 7B)"
    else:
        resultado["nodo_asignado"] = "nodo3 (doc ≥ 7.000.000.000)"

    return resultado


@app.post("/api/v1/admision/registrar")
async def registrar_admision(data: PatientIdentificationData):
    """
    Registra un paciente nuevo en el sistema de forma dual:
    1. Crea el recurso FHIR Patient en HAPI FHIR (estándar HL7 R4)
    2. Persiste en la DB local distribuida con el fhir_patient_id vinculado

    Si el paciente ya existe en alguno de los dos sistemas, retorna
    su información sin duplicar (idempotente).
    """
    data_dict = data.dict()
    doc_id = int(data_dict["numeroDocumento"])

    # 1. Verificar si ya existe localmente
    existente_local = None
    try:
        existente_local = DBService.buscar_paciente(doc_id)
    except Exception:
        pass

    fhir_id = None
    fhir_result = None

    # 2. Crear/buscar en HAPI FHIR
    try:
        # Primero verificar si ya existe en FHIR
        bundle = await fhir_service.search_patient_by_identifier(str(doc_id))
        entries = bundle.get("entry", [])
        if entries:
            fhir_result = entries[0]["resource"]
            fhir_id = fhir_result.get("id")
        else:
            # Crear en FHIR
            patient_resource = FHIRTransformer.to_fhir_patient(data_dict)
            fhir_result = await fhir_service.create_patient(patient_resource)
            fhir_id = fhir_result.get("id")
    except Exception as e:
        # FHIR no disponible — continuar solo con DB local
        fhir_result = {"error": str(e), "nota": "HAPI FHIR no disponible, registrado solo en DB local"}

    # 3. Persistir en DB local
    try:
        db_resultado = DBService.insertar_paciente(data_dict, fhir_patient_id=fhir_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en DB local: {str(e)}")

    return {
        "success": True,
        "accion": db_resultado["accion"],
        "nodo": db_resultado["nodo"],
        "fhir_patient_id": fhir_id,
        "paciente_local": db_resultado["paciente"],
        "fhir_resource": fhir_result,
        "mensaje": (
            f"Paciente {'encontrado' if db_resultado['accion'] == 'existente' else 'creado'} "
            f"en {db_resultado['nodo']} con FHIR ID: {fhir_id}"
        )
    }


@app.get("/api/v1/admision/tablas/estado")
async def estado_tablas_db():
    """
    Verifica si las tablas del esquema clínico existen en los 3 nodos.
    Útil para diagnóstico en la vista de admisión.
    """
    return {"nodos": DBService.estado_tablas()}


@app.post("/api/v1/admision/tablas/inicializar")
async def inicializar_tablas_db():
    """
    Crea las tablas (CREATE TABLE IF NOT EXISTS) en todos los nodos.
    Operación idempotente — segura de ejecutar múltiples veces.
    """
    resultado = DBService.inicializar_tablas()
    return resultado


@app.get("/api/v1/admision/buscar")
async def buscar_pacientes(
    nombre: str = "",
    documento: str = ""
):
    """
    Búsqueda unificada de pacientes:
    - Por nombre: busca en todos los nodos (LIKE)
    - Por documento: va directamente al nodo correcto + FHIR
    """
    if not nombre and not documento:
        raise HTTPException(status_code=400, detail="Proporciona 'nombre' o 'documento'")

    resultados_db = []
    resultados_fhir = []

    if documento:
        try:
            doc_int = int(documento)
            p = DBService.buscar_paciente(doc_int)
            if p:
                resultados_db.append(p)
        except Exception:
            pass

        try:
            bundle = await fhir_service.search_patient_by_identifier(documento)
            if bundle.get("entry"):
                resultados_fhir = [e["resource"] for e in bundle["entry"]]
        except Exception:
            pass

    if nombre:
        try:
            resultados_db.extend(DBService.buscar_por_nombre(nombre))
        except Exception:
            pass

        try:
            async with __import__('httpx').AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    f"{fhir_service.base_url}/Patient",
                    params={"name": nombre},
                    headers={"Accept": "application/fhir+json"}
                )
                if r.status_code == 200 and r.json().get("entry"):
                    resultados_fhir.extend([e["resource"] for e in r.json()["entry"]])
        except Exception:
            pass

    return {
        "total_local": len(resultados_db),
        "total_fhir": len(resultados_fhir),
        "resultados_local": resultados_db,
        "resultados_fhir": resultados_fhir,
    }

@app.get("/registro-paciente", response_class=HTMLResponse)
@app.get("/registro-paciente/", response_class=HTMLResponse)
async def registro_paciente_page():
    """Sirve el formulario de registro de paciente"""
    try:
        with open(os.path.join(BASE_DIR, "templates", "registro-paciente.html"), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Formulario no encontrado")


@app.post("/api/v1/fhir/patient")
async def create_fhir_patient(data: PatientIdentificationData):
    """
    Crea un paciente en HAPI FHIR Server
    
    Recibe los 15 campos de identificación y los transforma a recurso FHIR Patient
    """
    try:
        # 1. Transformar datos a recurso FHIR Patient
        patient_resource = FHIRTransformer.to_fhir_patient(data.dict())
        
        # 2. Enviar a HAPI FHIR Server
        result = await fhir_service.create_patient(patient_resource)
        
        # 3. Extraer ID del paciente creado
        patient_id = result.get("id")
        
        return {
            "success": True,
            "message": "Paciente creado exitosamente en HAPI FHIR",
            "patient_id": patient_id,
            "fhir_resource": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear paciente: {str(e)}"
        )


@app.get("/api/v1/fhir/patient/{patient_id}")
async def get_fhir_patient(patient_id: str):
    """Obtiene un paciente por ID desde HAPI FHIR"""
    try:
        patient = await fhir_service.get_patient(patient_id)
        
        if patient is None:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        
        return patient
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener paciente: {str(e)}"
        )


@app.get("/api/v1/fhir/patient/search/{identifier}")
async def search_fhir_patient(identifier: str):
    """Busca pacientes por número de documento"""
    try:
        results = await fhir_service.search_patient_by_identifier(identifier)
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar paciente: {str(e)}"
        )


@app.get("/api/v1/fhir/health")
async def fhir_server_health():
    """Verifica el estado del servidor HAPI FHIR"""
    try:
        metadata = await fhir_service.check_server_health()
        return {
            "status": "ok",
            "fhir_version": metadata.get("fhirVersion"),
            "server": "HAPI FHIR",
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"HAPI FHIR Server no disponible: {str(e)}"
        )


@app.get("/consulta-hc", response_class=HTMLResponse)
@app.get("/consulta-hc/", response_class=HTMLResponse)
async def consulta_hc_page():
    """Sirve la página de consulta de historias clínicas"""
    try:
        with open(os.path.join(BASE_DIR, "templates", "consulta-hc.html"), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Página de consulta no encontrada")


@app.get("/api/v1/fhir/patients")
async def list_patients(page: int = 1, size: int = 10):
    """
    Lista todos los pacientes con paginación
    
    Query params:
    - page: Número de página (default: 1)
    - size: Tamaño de página (default: 10)
    """
    try:
        # Buscar todos los pacientes en HAPI FHIR
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"http://hapi-fhir:8080/fhir/Patient",
                params={
                    "_count": size,
                    "_page": page
                },
                headers={"Accept": "application/fhir+json"}
            )
            
            response.raise_for_status()
            bundle = response.json()
            
            # Extraer pacientes del bundle
            patients = []
            if bundle.get("entry"):
                patients = [entry["resource"] for entry in bundle["entry"]]
            
            total = bundle.get("total", 0)
            total_pages = (total + size - 1) // size if total > 0 else 1
            
            return {
                "patients": patients,
                "total": total,
                "page": page,
                "size": size,
                "total_pages": total_pages
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar pacientes: {str(e)}"
        )


@app.get("/api/v1/fhir/patients/search")
async def search_patients_query(q: str):
    """
    Busca pacientes por nombre o documento
    
    Query params:
    - q: Término de búsqueda
    """
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Buscar por nombre
            response_name = await client.get(
                f"http://hapi-fhir:8080/fhir/Patient",
                params={"name": q},
                headers={"Accept": "application/fhir+json"}
            )
            
            # Buscar por identificador
            response_id = await client.get(
                f"http://hapi-fhir:8080/fhir/Patient",
                params={"identifier": q},
                headers={"Accept": "application/fhir+json"}
            )
            
            patients = []
            
            # Combinar resultados
            if response_name.status_code == 200:
                bundle = response_name.json()
                if bundle.get("entry"):
                    patients.extend([entry["resource"] for entry in bundle["entry"]])
            
            if response_id.status_code == 200:
                bundle = response_id.json()
                if bundle.get("entry"):
                    for entry in bundle["entry"]:
                        resource = entry["resource"]
                        # Evitar duplicados
                        if not any(p["id"] == resource["id"] for p in patients):
                            patients.append(resource)
            
            return {
                "patients": patients,
                "total": len(patients),
                "query": q
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en la búsqueda: {str(e)}"
        )


@app.get("/paciente/{patient_id}", response_class=HTMLResponse)
async def patient_detail_page(patient_id: str):
    """Página de detalle de un paciente"""
    try:
        # Obtener paciente desde HAPI FHIR
        patient = await fhir_service.get_patient(patient_id)
        
        if patient is None:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        
        # Generar HTML de detalle
        html = generate_patient_detail_html(patient)
        return html
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener detalle del paciente: {str(e)}"
        )


def generate_patient_detail_html(patient: dict) -> str:
    """Genera HTML para mostrar detalle de un paciente"""
    identifier = patient.get("identifier", [{}])[0].get("value", "N/A")
    name = patient.get("name", [{}])[0].get("text", "Sin nombre")
    gender = patient.get("gender", "unknown")
    birth_date = patient.get("birthDate", "N/A")
    
    gender_map = {
        "male": "Masculino",
        "female": "Femenino",
        "other": "Otro",
        "unknown": "No especificado"
    }
    
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Detalle Paciente - {name}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
        <script src="https://unpkg.com/@phosphor-icons/web"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Inter', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 2rem; }}
            .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; }}
            .header h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
            .header p {{ opacity: 0.9; }}
            .content {{ padding: 2rem; }}
            .section {{ margin-bottom: 2rem; }}
            .section h2 {{ font-size: 1.25rem; color: #333; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #667eea; }}
            .field {{ display: grid; grid-template-columns: 200px 1fr; gap: 1rem; padding: 0.75rem 0; border-bottom: 1px solid #e2e8f0; }}
            .field:last-child {{ border-bottom: none; }}
            .field-label {{ font-weight: 600; color: #555; }}
            .field-value {{ color: #333; }}
            .btn-back {{ display: inline-block; margin-top: 2rem; padding: 0.75rem 1.5rem; background: #667eea; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; }}
            .btn-back:hover {{ background: #5568d3; }}
            .fhir-json {{ background: #f7fafc; padding: 1rem; border-radius: 8px; overflow-x: auto; }}
            .fhir-json pre {{ margin: 0; font-size: 0.875rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><i class="ph ph-user-circle"></i> {name}</h1>
                <p>ID FHIR: {patient.get("id", "N/A")}</p>
            </div>
            <div class="content">
                <div class="section">
                    <h2>Datos de Identificación</h2>
                    <div class="field">
                        <div class="field-label">Número de Documento:</div>
                        <div class="field-value">{identifier}</div>
                    </div>
                    <div class="field">
                        <div class="field-label">Nombre Completo:</div>
                        <div class="field-value">{name}</div>
                    </div>
                    <div class="field">
                        <div class="field-label">Sexo:</div>
                        <div class="field-value">{gender_map.get(gender, gender)}</div>
                    </div>
                    <div class="field">
                        <div class="field-label">Fecha de Nacimiento:</div>
                        <div class="field-value">{birth_date}</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Recurso FHIR Completo</h2>
                    <div class="fhir-json">
                        <pre>{str(patient)}</pre>
                    </div>
                </div>
                
                <a href="/consulta-hc" class="btn-back">
                    <i class="ph ph-arrow-left"></i> Volver a la lista
                </a>
            </div>
        </div>
    </body>
    </html>
    """


# ============================================================================
# ENDPOINTS FIRH ORIGINALES
# ============================================================================

FIRH_CAMPOS = {
    "usuario": [
        {"nombre": "documento_id", "tipo": "number", "etiqueta": "Documento ID", "requerido": True, "pk": True},
        {"nombre": "nombre_completo", "tipo": "text", "etiqueta": "Nombre completo", "requerido": True},
        {"nombre": "pais_nacionalidad", "tipo": "text", "etiqueta": "País nacionalidad"},
        {"nombre": "fecha_nacimiento", "tipo": "date", "etiqueta": "Fecha nacimiento"},
        {"nombre": "edad", "tipo": "number", "etiqueta": "Edad"},
        {"nombre": "sexo", "tipo": "text", "etiqueta": "Sexo"},
        {"nombre": "genero", "tipo": "text", "etiqueta": "Género"},
        {"nombre": "ocupacion", "tipo": "text", "etiqueta": "Ocupación"},
        {"nombre": "voluntad_anticipada", "tipo": "boolean", "etiqueta": "Voluntad anticipada"},
        {"nombre": "categoria_discapacidad", "tipo": "text", "etiqueta": "Categoría discapacidad"},
        {"nombre": "pais_residencia", "tipo": "text", "etiqueta": "País residencia"},
        {"nombre": "municipio_residencia", "tipo": "text", "etiqueta": "Municipio residencia"},
        {"nombre": "etnia", "tipo": "text", "etiqueta": "Etnia"},
        {"nombre": "comunidad_etnica", "tipo": "text", "etiqueta": "Comunidad étnica"},
        {"nombre": "zona_residencia", "tipo": "text", "etiqueta": "Zona residencia"},
    ],
    "atencion": [
        {"nombre": "documento_id", "tipo": "number", "etiqueta": "Documento ID (paciente)", "requerido": True},
        {"nombre": "entidad_salud", "tipo": "text", "etiqueta": "Entidad salud"},
        {"nombre": "fecha_ingreso", "tipo": "datetime-local", "etiqueta": "Fecha ingreso"},
        {"nombre": "modalidad_entrega", "tipo": "text", "etiqueta": "Modalidad entrega"},
        {"nombre": "entorno_atencion", "tipo": "text", "etiqueta": "Entorno atención"},
        {"nombre": "via_ingreso", "tipo": "text", "etiqueta": "Vía ingreso"},
        {"nombre": "causa_atencion", "tipo": "textarea", "etiqueta": "Causa atención"},
        {"nombre": "fecha_triage", "tipo": "datetime-local", "etiqueta": "Fecha triage"},
        {"nombre": "clasificacion_triage", "tipo": "text", "etiqueta": "Clasificación triage"},
    ],
    "tecnologia_salud": [
        {"nombre": "documento_id", "tipo": "number", "etiqueta": "Documento ID (para enrutar)", "requerido": True},
        {"nombre": "tecnologia_id", "tipo": "text", "etiqueta": "UUID tecnología", "requerido": True},
        {"nombre": "atencion_id", "tipo": "number", "etiqueta": "Atención ID", "requerido": True},
        {"nombre": "descripcion_medicamento", "tipo": "text", "etiqueta": "Descripción medicamento"},
        {"nombre": "dosis", "tipo": "text", "etiqueta": "Dosis"},
        {"nombre": "via_administracion", "tipo": "text", "etiqueta": "Vía administración"},
        {"nombre": "frecuencia", "tipo": "text", "etiqueta": "Frecuencia"},
        {"nombre": "dias_tratamiento", "tipo": "number", "etiqueta": "Días tratamiento"},
        {"nombre": "unidades_aplicadas", "tipo": "number", "etiqueta": "Unidades aplicadas"},
        {"nombre": "id_personal_salud", "tipo": "text", "etiqueta": "UUID profesional"},
        {"nombre": "finalidad_tecnologia", "tipo": "text", "etiqueta": "Finalidad tecnología"},
    ],
    "diagnostico": [
        {"nombre": "documento_id", "tipo": "number", "etiqueta": "Documento ID (para enrutar)", "requerido": True},
        {"nombre": "atencion_id", "tipo": "number", "etiqueta": "Atención ID", "requerido": True},
        {"nombre": "tipo_diagnostico_ingreso", "tipo": "text", "etiqueta": "Tipo diagnóstico ingreso"},
        {"nombre": "diagnostico_ingreso", "tipo": "text", "etiqueta": "Diagnóstico ingreso"},
        {"nombre": "tipo_diagnostico_egreso", "tipo": "text", "etiqueta": "Tipo diagnóstico egreso"},
        {"nombre": "diagnostico_egreso", "tipo": "text", "etiqueta": "Diagnóstico egreso"},
        {"nombre": "diagnostico_rel1", "tipo": "text", "etiqueta": "Diagnóstico rel 1"},
        {"nombre": "diagnostico_rel2", "tipo": "text", "etiqueta": "Diagnóstico rel 2"},
        {"nombre": "diagnostico_rel3", "tipo": "text", "etiqueta": "Diagnóstico rel 3"},
    ],
    "egreso": [
        {"nombre": "documento_id", "tipo": "number", "etiqueta": "Documento ID (para enrutar)", "requerido": True},
        {"nombre": "atencion_id", "tipo": "number", "etiqueta": "Atención ID", "requerido": True},
        {"nombre": "fecha_salida", "tipo": "datetime-local", "etiqueta": "Fecha salida"},
        {"nombre": "condicion_salida", "tipo": "text", "etiqueta": "Condición salida"},
        {"nombre": "diagnostico_muerte", "tipo": "text", "etiqueta": "Diagnóstico muerte"},
        {"nombre": "codigo_prestador", "tipo": "text", "etiqueta": "Código prestador"},
        {"nombre": "tipo_incapacidad", "tipo": "text", "etiqueta": "Tipo incapacidad"},
        {"nombre": "dias_incapacidad", "tipo": "number", "etiqueta": "Días incapacidad"},
        {"nombre": "dias_lic_maternidad", "tipo": "number", "etiqueta": "Días lic. maternidad"},
        {"nombre": "alergias", "tipo": "textarea", "etiqueta": "Alergias"},
        {"nombre": "antecedente_familiar", "tipo": "textarea", "etiqueta": "Antecedente familiar"},
        {"nombre": "riesgos_ocupacionales", "tipo": "textarea", "etiqueta": "Riesgos ocupacionales"},
        {"nombre": "responsable_egreso", "tipo": "text", "etiqueta": "Responsable egreso"},
    ],
    "profesional_salud": [
        {"nombre": "id_personal_salud", "tipo": "text", "etiqueta": "UUID profesional", "requerido": True},
        {"nombre": "nombre", "tipo": "text", "etiqueta": "Nombre", "requerido": True},
        {"nombre": "especialidad", "tipo": "text", "etiqueta": "Especialidad"},
    ],
}


@app.get("/api/firh/campos")
async def firh_campos():
    return FIRH_CAMPOS


class FirhCargarBody(BaseModel):
    tabla: str
    datos: dict


@app.post("/api/firh/cargar")
async def firh_cargar(body: FirhCargarBody):
    try:
        resultado = middleware.insertar_registro_firh(body.tabla, body.datos)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MÓDULO MÉDICO
# ============================================================================

@app.get("/medico", response_class=HTMLResponse)
@app.get("/medico/", response_class=HTMLResponse)
async def medico_page():
    """Dashboard del médico: búsqueda, historia clínica, atención, diagnóstico y prescripción"""
    try:
        with open(os.path.join(BASE_DIR, "templates", "medico.html"), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Módulo médico no encontrado")


class AtencionRequest(BaseModel):
    documento_id: int
    entidad_salud: str = ""
    fecha_ingreso: str
    modalidad_entrega: str = ""
    entorno_atencion: str = ""
    via_ingreso: str = ""
    causa_atencion: str = ""
    fecha_triage: str = None
    clasificacion_triage: str = None


class DiagnosticoRequest(BaseModel):
    documento_id: int
    atencion_id: int
    tipo_diagnostico_ingreso: str = None
    diagnostico_ingreso: str = None
    tipo_diagnostico_egreso: str = None
    diagnostico_egreso: str = None
    diagnostico_rel1: str = None
    diagnostico_rel2: str = None
    diagnostico_rel3: str = None


class MedicamentoItem(BaseModel):
    documento_id: int
    atencion_id: int
    tecnologia_id: str = None
    descripcion_medicamento: str = None
    dosis: str = None
    via_administracion: str = None
    frecuencia: str = None
    dias_tratamiento: int = None
    unidades_aplicadas: int = None


class PrescripcionRequest(BaseModel):
    medicamentos: list[MedicamentoItem]


def _conectar_nodo(doc_id: int):
    """Retorna una conexión psycopg2 al nodo correcto según doc_id."""
    USE_DOCKER = os.getenv("USE_DOCKER_NAMES", "false").lower() == "true"
    if doc_id < 4_000_000_000:
        host, port = ("pg_nodo1", 5432) if USE_DOCKER else ("localhost", 5433)
        nodo_name = "nodo1 (pg_nodo1)"
    elif doc_id < 7_000_000_000:
        host, port = ("pg_nodo2", 5432) if USE_DOCKER else ("localhost", 5434)
        nodo_name = "nodo2 (pg_nodo2)"
    else:
        host, port = ("pg_nodo3", 5432) if USE_DOCKER else ("localhost", 5435)
        nodo_name = "nodo3 (pg_nodo3)"
    conn = psycopg2.connect(host=host, port=port, user="admin", password="admin",
                            dbname="historia_clinica", connect_timeout=5)
    return conn, nodo_name


@app.get("/api/v1/medico/historia/{documento_id}")
async def historia_clinica(documento_id: int):
    """
    Retorna la historia clínica completa de un paciente desde la DB distribuida:
    atenciones, diagnósticos y medicamentos.
    """
    try:
        conn, nodo = _conectar_nodo(documento_id)
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Atenciones
            cur.execute(
                "SELECT * FROM atencion WHERE documento_id = %s ORDER BY fecha_ingreso DESC;",
                (documento_id,)
            )
            atenciones = [dict(r) for r in cur.fetchall()]

            # IDs de atenciones para joins
            ids = [a["atencion_id"] for a in atenciones]

            diagnosticos = []
            medicamentos = []
            if ids:
                cur.execute(
                    "SELECT * FROM diagnostico WHERE atencion_id = ANY(%s);", (ids,)
                )
                diagnosticos = [dict(r) for r in cur.fetchall()]

                cur.execute(
                    "SELECT * FROM tecnologia_salud WHERE atencion_id = ANY(%s);", (ids,)
                )
                medicamentos = [dict(r) for r in cur.fetchall()]

        conn.close()

        # serializar campos no JSON-serializable (fechas, UUID)
        import json
        from datetime import date, datetime
        from uuid import UUID

        def serial(obj):
            if isinstance(obj, (datetime, date)): return obj.isoformat()
            if isinstance(obj, UUID): return str(obj)
            raise TypeError(f"{type(obj)} not serializable")

        return {
            "documento_id": documento_id,
            "nodo": nodo,
            "total_atenciones": len(atenciones),
            "total_diagnosticos": len(diagnosticos),
            "total_medicamentos": len(medicamentos),
            "atenciones":   json.loads(json.dumps(atenciones, default=serial)),
            "diagnosticos": json.loads(json.dumps(diagnosticos, default=serial)),
            "medicamentos": json.loads(json.dumps(medicamentos, default=serial)),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando historia: {str(e)}")


@app.post("/api/v1/medico/atencion")
async def registrar_atencion(data: AtencionRequest):
    """Registra una nueva atención en el nodo distribuido correcto."""
    try:
        conn, nodo = _conectar_nodo(data.documento_id)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO atencion
                  (documento_id, entidad_salud, fecha_ingreso, modalidad_entrega,
                   entorno_atencion, via_ingreso, causa_atencion, fecha_triage, clasificacion_triage)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING atencion_id;
            """, (
                data.documento_id,
                data.entidad_salud or None,
                data.fecha_ingreso,
                data.modalidad_entrega or None,
                data.entorno_atencion or None,
                data.via_ingreso or None,
                data.causa_atencion or None,
                data.fecha_triage or None,
                data.clasificacion_triage or None,
            ))
            atencion_id = cur.fetchone()[0]
            conn.commit()
        conn.close()
        return {"success": True, "atencion_id": atencion_id, "nodo": nodo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registrando atención: {str(e)}")


@app.post("/api/v1/medico/diagnostico")
async def registrar_diagnostico(data: DiagnosticoRequest):
    """Guarda un diagnóstico vinculado a una atención en el nodo correcto."""
    try:
        conn, nodo = _conectar_nodo(data.documento_id)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO diagnostico
                  (atencion_id, tipo_diagnostico_ingreso, diagnostico_ingreso,
                   tipo_diagnostico_egreso, diagnostico_egreso,
                   diagnostico_rel1, diagnostico_rel2, diagnostico_rel3)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING diagnostico_id;
            """, (
                data.atencion_id,
                data.tipo_diagnostico_ingreso,
                data.diagnostico_ingreso,
                data.tipo_diagnostico_egreso,
                data.diagnostico_egreso,
                data.diagnostico_rel1,
                data.diagnostico_rel2,
                data.diagnostico_rel3,
            ))
            dx_id = cur.fetchone()[0]
            conn.commit()
        conn.close()
        return {"success": True, "diagnostico_id": dx_id, "nodo": nodo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando diagnóstico: {str(e)}")


@app.post("/api/v1/medico/prescripcion")
async def guardar_prescripcion(body: PrescripcionRequest):
    """Guarda uno o más medicamentos (tecnologia_salud) en el nodo correcto."""
    if not body.medicamentos:
        raise HTTPException(status_code=400, detail="Sin medicamentos")
    doc_id = body.medicamentos[0].documento_id
    try:
        conn, nodo = _conectar_nodo(doc_id)
        inserted = 0
        with conn.cursor() as cur:
            for m in body.medicamentos:
                import uuid
                tid = m.tecnologia_id or str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO tecnologia_salud
                      (tecnologia_id, atencion_id, descripcion_medicamento, dosis,
                       via_administracion, frecuencia, dias_tratamiento, unidades_aplicadas)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s);
                """, (
                    tid, m.atencion_id, m.descripcion_medicamento, m.dosis,
                    m.via_administracion, m.frecuencia, m.dias_tratamiento, m.unidades_aplicadas,
                ))
                inserted += 1
            conn.commit()
        conn.close()
        return {"success": True, "total": inserted, "nodo": nodo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando prescripción: {str(e)}")


# ============================================================================
# ENDPOINTS DE GESTIÓN DE PROFESIONALES DE SALUD (MÉDICOS)
# ============================================================================

from fhir_app.models.patient_model import ProfesionalSaludData, ProfesionalSaludUpdate


@app.get("/api/v1/profesionales")
async def listar_profesionales(
    activos: bool = True,
    especialidad: str = None,
    limite: int = 100
):
    """
    Lista todos los profesionales de salud.

    Query params:
    - activos: Filtrar solo activos (default: true)
    - especialidad: Filtrar por especialidad (opcional)
    - limite: Límite de resultados (default: 100)
    """
    try:
        profesionales = DBService.listar_profesionales(
            activos_only=activos,
            especialidad=especialidad,
            limite=limite
        )
        return {
            "success": True,
            "total": len(profesionales),
            "profesionales": profesionales
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando profesionales: {str(e)}")


@app.get("/api/v1/profesionales/{profesional_id}")
async def obtener_profesional(profesional_id: str):
    """Obtiene un profesional por su ID."""
    try:
        profesional = DBService.obtener_profesional(profesional_id)
        if not profesional:
            raise HTTPException(status_code=404, detail="Profesional no encontrado")
        return {
            "success": True,
            "profesional": profesional
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo profesional: {str(e)}")


@app.post("/api/v1/profesionales")
async def crear_profesional(data: ProfesionalSaludData):
    """
    Crea un nuevo profesional de salud.

    Campos requeridos:
    - nombre: Nombre completo del profesional

    Campos opcionales:
    - especialidad, registroMedico, entidadSalud, email, telefono, activo
    """
    try:
        resultado = DBService.crear_profesional(data.dict())
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando profesional: {str(e)}")


@app.put("/api/v1/profesionales/{profesional_id}")
async def actualizar_profesional(profesional_id: str, data: ProfesionalSaludUpdate):
    """
    Actualiza un profesional existente.
    Solo actualiza los campos proporcionados.
    """
    try:
        resultado = DBService.actualizar_profesional(profesional_id, data.dict(exclude_unset=True))
        if not resultado:
            raise HTTPException(status_code=404, detail="Profesional no encontrado")
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando profesional: {str(e)}")


@app.delete("/api/v1/profesionales/{profesional_id}")
async def eliminar_profesional(profesional_id: str):
    """Elimina un profesional de la base de datos."""
    try:
        deleted = DBService.eliminar_profesional(profesional_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Profesional no encontrado")
        return {
            "success": True,
            "mensaje": "Profesional eliminado correctamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando profesional: {str(e)}")


@app.get("/api/v1/profesionales/buscar/{nombre}")
async def buscar_profesionales(nombre: str, limite: int = 20):
    """Busca profesionales por nombre (búsqueda parcial)."""
    try:
        profesionales = DBService.buscar_profesionales_por_nombre(nombre, limite)
        return {
            "success": True,
            "total": len(profesionales),
            "query": nombre,
            "profesionales": profesionales
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error buscando profesionales: {str(e)}")


# Estáticos al final para no tapar rutas
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ============================================================================
# MCP - Model Context Protocol
# Expone todos los endpoints de la API como herramientas para agentes de IA
# ============================================================================
mcp = FastApiMCP(
    app,
    name="Historia Clínica Distribuida MCP",
    description=(
        "Servidor MCP del sistema de Historia Clínica Distribuida. "
        "Permite a agentes de IA consultar y gestionar pacientes FHIR, "
        "ejecutar queries SQL distribuidas, y monitorear el estado de los nodos PostgreSQL."
    ),
)
mcp.mount()  # Disponible en /mcp

PORT = 8001

if __name__ == "__main__":
    import uvicorn
    print("\n  → Dashboard:  http://localhost:{}".format(PORT))
    print("  → Admisión:   http://localhost:{}/admision".format(PORT))
    print("  → Médico:     http://localhost:{}/medico".format(PORT))
    print("  → Consulta:   http://localhost:{}/consulta-hc".format(PORT))
    print("  → Carga HC:   http://localhost:{}/carga-hc".format(PORT))
    print("  → Health:     http://localhost:{}/api/health".format(PORT))
    print("  → MCP Server: http://localhost:{}/mcp\n".format(PORT))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
