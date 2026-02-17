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

# Agregar backend al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from fhir_app.models.patient_model import PatientIdentificationData
from fhir_app.transformers.fhir_transformer import FHIRTransformer
from fhir_app.services.fhir_service import FHIRService

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


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(os.path.join(BASE_DIR, "templates", "index.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/health")
async def health():
    return {"status": "ok", "carga_hc": "/carga-hc", "hc": "/hc"}


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

# Inicializar servicio FHIR
fhir_service = FHIRService()

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


# Estáticos al final para no tapar rutas
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

PORT = 8001

if __name__ == "__main__":
    import uvicorn
    print("\n  → Dashboard: http://localhost:{}".format(PORT))
    print("  → Carga HC:  http://localhost:{}/carga-hc".format(PORT))
    print("  → Health:    http://localhost:{}/api/health\n".format(PORT))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
