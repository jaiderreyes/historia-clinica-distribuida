# backend/fhir_app/services/db_service.py
"""
Servicio de base de datos distribuida para el sistema de Historia Clínica.

Responsabilidades:
- Inicializar tablas en cualquier nodo con CREATE TABLE IF NOT EXISTS
- Buscar pacientes en base al fragmento correcto (documento_id)
- Insertar pacientes en la DB local distribu ida y sincronizar con FHIR
- Retornar datos combinados DB local + FHIR
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Configuración de nodos
# ─────────────────────────────────────────────
USE_DOCKER_NAMES = os.getenv("USE_DOCKER_NAMES", "false").lower() == "true"

if USE_DOCKER_NAMES:
    NODOS = [
        {"id": "nodo1", "host": "pg_nodo1", "port": 5432, "user": "admin", "password": "admin", "dbname": "historia_clinica", "range": "< 4.000.000.000"},
        {"id": "nodo2", "host": "pg_nodo2", "port": 5432, "user": "admin", "password": "admin", "dbname": "historia_clinica", "range": "4B – 7B"},
        {"id": "nodo3", "host": "pg_nodo3", "port": 5432, "user": "admin", "password": "admin", "dbname": "historia_clinica", "range": "> 7.000.000.000"},
    ]
else:
    NODOS = [
        {"id": "nodo1", "host": "localhost", "port": 5433, "user": "admin", "password": "admin", "dbname": "historia_clinica", "range": "< 4.000.000.000"},
        {"id": "nodo2", "host": "localhost", "port": 5434, "user": "admin", "password": "admin", "dbname": "historia_clinica", "range": "4B – 7B"},
        {"id": "nodo3", "host": "localhost", "port": 5435, "user": "admin", "password": "admin", "dbname": "historia_clinica", "range": "> 7.000.000.000"},
    ]

# ─────────────────────────────────────────────
# DDL — sentencias CREATE TABLE IF NOT EXISTS
# Cumple estructura HL7/FHIR Colombia RESO 2654/2019
# ─────────────────────────────────────────────
DDL_USUARIO = """
CREATE TABLE IF NOT EXISTS usuario (
    documento_id        BIGINT PRIMARY KEY,
    tipo_documento      VARCHAR(10),
    pais_nacionalidad   VARCHAR(10),
    nombre_completo     VARCHAR(255) NOT NULL,
    fecha_nacimiento    DATE,
    edad                INT,
    unidad_edad         VARCHAR(5)  DEFAULT '1',
    sexo                VARCHAR(10),
    genero              VARCHAR(50),
    ocupacion           VARCHAR(100),
    voluntad_anticipada BOOLEAN     DEFAULT FALSE,
    categoria_discapacidad VARCHAR(50),
    pais_residencia     VARCHAR(10),
    municipio_residencia VARCHAR(10),
    etnia               VARCHAR(50),
    comunidad_etnica    VARCHAR(100),
    zona_residencia     VARCHAR(20),
    fhir_patient_id     VARCHAR(64),
    created_at          TIMESTAMP   DEFAULT NOW(),
    updated_at          TIMESTAMP   DEFAULT NOW()
);
"""

DDL_ATENCION = """
CREATE TABLE IF NOT EXISTS atencion (
    atencion_id         SERIAL PRIMARY KEY,
    documento_id        BIGINT      NOT NULL,
    entidad_salud       VARCHAR(255),
    fecha_ingreso       TIMESTAMP,
    modalidad_entrega   VARCHAR(50),
    entorno_atencion    VARCHAR(50),
    via_ingreso         VARCHAR(50),
    causa_atencion      TEXT,
    fecha_triage        TIMESTAMP,
    clasificacion_triage VARCHAR(10),
    FOREIGN KEY (documento_id) REFERENCES usuario(documento_id)
);
"""

DDL_TECNOLOGIA_SALUD = """
CREATE TABLE IF NOT EXISTS tecnologia_salud (
    tecnologia_id       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    atencion_id         INT,
    descripcion_medicamento VARCHAR(255),
    dosis               VARCHAR(50),
    via_administracion  VARCHAR(50),
    frecuencia          VARCHAR(50),
    dias_tratamiento    INT,
    unidades_aplicadas  INT,
    id_personal_salud   UUID,
    finalidad_tecnologia VARCHAR(255),
    FOREIGN KEY (atencion_id) REFERENCES atencion(atencion_id)
);
"""

DDL_DIAGNOSTICO = """
CREATE TABLE IF NOT EXISTS diagnostico (
    diagnostico_id          SERIAL PRIMARY KEY,
    atencion_id             INT,
    tipo_diagnostico_ingreso VARCHAR(50),
    diagnostico_ingreso     VARCHAR(255),
    tipo_diagnostico_egreso VARCHAR(50),
    diagnostico_egreso      VARCHAR(255),
    diagnostico_rel1        VARCHAR(255),
    diagnostico_rel2        VARCHAR(255),
    diagnostico_rel3        VARCHAR(255),
    FOREIGN KEY (atencion_id) REFERENCES atencion(atencion_id)
);
"""

DDL_EGRESO = """
CREATE TABLE IF NOT EXISTS egreso (
    egreso_id           SERIAL PRIMARY KEY,
    atencion_id         INT,
    fecha_salida        TIMESTAMP,
    condicion_salida    VARCHAR(100),
    diagnostico_muerte  VARCHAR(255),
    codigo_prestador    VARCHAR(20),
    tipo_incapacidad    VARCHAR(100),
    dias_incapacidad    INT,
    dias_lic_maternidad INT,
    alergias            TEXT,
    antecedente_familiar TEXT,
    riesgos_ocupacionales TEXT,
    responsable_egreso  VARCHAR(255),
    FOREIGN KEY (atencion_id) REFERENCES atencion(atencion_id)
);
"""

DDL_PROFESIONAL_SALUD = """
CREATE TABLE IF NOT EXISTS profesional_salud (
    id_personal_salud   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre              VARCHAR(255) NOT NULL,
    especialidad        VARCHAR(100),
    registro_medico     VARCHAR(50),
    entidad_salud       VARCHAR(255),
    email               VARCHAR(255),
    telefono            VARCHAR(50),
    activo              BOOLEAN     DEFAULT TRUE,
    created_at          TIMESTAMP   DEFAULT NOW(),
    updated_at          TIMESTAMP   DEFAULT NOW()
);
"""

ALL_DDL = [
    DDL_USUARIO,
    DDL_ATENCION,
    DDL_TECNOLOGIA_SALUD,
    DDL_DIAGNOSTICO,
    DDL_EGRESO,
    DDL_PROFESIONAL_SALUD,
]


def _conectar(nodo: dict):
    return psycopg2.connect(
        host=nodo["host"],
        port=nodo["port"],
        user=nodo["user"],
        password=nodo["password"],
        dbname=nodo["dbname"],
        connect_timeout=5,
    )


def _nodo_por_documento(documento_id: int) -> dict:
    """Fragmentación horizontal por rango de documento_id."""
    if documento_id < 4_000_000_000:
        return NODOS[0]
    elif documento_id < 7_000_000_000:
        return NODOS[1]
    else:
        return NODOS[2]


class DBService:
    """
    Servicio de acceso a la base de datos distribuida.
    Maneja la inicialización de tablas y operaciones CRUD.
    """

    # ─────────────────────────────────────────────
    # Inicialización de tablas
    # ─────────────────────────────────────────────

    @staticmethod
    def inicializar_tablas(nodo: Optional[dict] = None) -> Dict[str, Any]:
        """
        Ejecuta CREATE TABLE IF NOT EXISTS en el nodo indicado (o en todos).
        Es seguro ejecutar múltiples veces — idempotente.
        """
        nodos_target = [nodo] if nodo else NODOS
        resultados = []

        for n in nodos_target:
            resultado = {"nodo": n["id"], "estado": "OK", "tablas_creadas": [], "error": None}
            try:
                conn = _conectar(n)
                conn.autocommit = False
                with conn.cursor() as cur:
                    for ddl in ALL_DDL:
                        cur.execute(ddl)
                conn.commit()
                conn.close()
                resultado["tablas_creadas"] = [
                    "usuario", "atencion", "tecnologia_salud",
                    "diagnostico", "egreso", "profesional_salud"
                ]
                logger.info(f"Tablas inicializadas en {n['id']}")
            except Exception as e:
                resultado["estado"] = "ERROR"
                resultado["error"] = str(e)
                logger.error(f"Error inicializando tablas en {n['id']}: {e}")
            resultados.append(resultado)

        exitosos = sum(1 for r in resultados if r["estado"] == "OK")
        return {
            "mensaje": f"Inicialización completada: {exitosos}/{len(nodos_target)} nodos OK",
            "nodos": resultados,
        }

    # ─────────────────────────────────────────────
    # Búsqueda de pacientes
    # ─────────────────────────────────────────────

    @staticmethod
    def buscar_paciente(documento_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca un paciente por documento_id en el nodo correcto.
        Retorna None si no existe.
        """
        nodo = _nodo_por_documento(documento_id)
        try:
            conn = _conectar(nodo)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM usuario WHERE documento_id = %s;",
                    (documento_id,)
                )
                row = cur.fetchone()
            conn.close()
            if row:
                paciente = dict(row)
                paciente["_nodo"] = nodo["id"]
                return paciente
            return None
        except psycopg2.errors.UndefinedTable:
            # La tabla no existe aún — inicializar y retornar None
            logger.warning(f"Tabla 'usuario' no existe en {nodo['id']} — inicializando...")
            DBService.inicializar_tablas(nodo)
            return None
        except Exception as e:
            logger.error(f"Error buscando paciente {documento_id} en {nodo['id']}: {e}")
            raise

    @staticmethod
    def buscar_por_nombre(nombre: str, limite: int = 20) -> List[Dict[str, Any]]:
        """Busca pacientes por nombre en todos los nodos."""
        resultados = []
        for nodo in NODOS:
            try:
                conn = _conectar(nodo)
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT documento_id, tipo_documento, nombre_completo, fecha_nacimiento, sexo, fhir_patient_id "
                        "FROM usuario WHERE LOWER(nombre_completo) LIKE LOWER(%s) LIMIT %s;",
                        (f"%{nombre}%", limite)
                    )
                    filas = cur.fetchall()
                conn.close()
                for f in filas:
                    p = dict(f)
                    p["_nodo"] = nodo["id"]
                    resultados.append(p)
            except Exception as e:
                logger.warning(f"Error buscando por nombre en {nodo['id']}: {e}")
        return resultados

    # ─────────────────────────────────────────────
    # Inserción / actualización de pacientes
    # ─────────────────────────────────────────────

    @staticmethod
    def insertar_paciente(data: Dict[str, Any], fhir_patient_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Inserta un paciente nuevo en el nodo correspondiente.
        Si el paciente ya existe retorna su registro sin duplicar.
        """
        documento_id = int(data["numeroDocumento"])
        nodo = _nodo_por_documento(documento_id)

        # Asegurar que la tabla existe
        DBService.inicializar_tablas(nodo)

        # Verificar si ya existe
        existente = DBService.buscar_paciente(documento_id)
        if existente:
            return {"accion": "existente", "paciente": existente, "nodo": nodo["id"]}

        try:
            conn = _conectar(nodo)
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO usuario (
                        documento_id, tipo_documento, pais_nacionalidad,
                        nombre_completo, fecha_nacimiento, edad, unidad_edad,
                        sexo, genero, ocupacion, voluntad_anticipada,
                        categoria_discapacidad, pais_residencia, municipio_residencia,
                        etnia, fhir_patient_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    documento_id,
                    data.get("tipoDocumento"),
                    data.get("paisNacionalidad"),
                    data.get("nombreCompleto"),
                    data.get("fechaNacimiento"),
                    data.get("edad"),
                    data.get("unidadEdad", "1"),
                    data.get("sexo"),
                    data.get("genero"),
                    data.get("ocupacion"),
                    data.get("voluntadAnticipada") == "true",
                    data.get("categoriaDiscapacidad"),
                    data.get("paisResidencia"),
                    data.get("municipioResidencia"),
                    data.get("etnia"),
                    fhir_patient_id,
                ))
                conn.commit()
            conn.close()

            nuevo = DBService.buscar_paciente(documento_id)
            return {"accion": "creado", "paciente": nuevo, "nodo": nodo["id"]}

        except Exception as e:
            logger.error(f"Error insertando paciente en {nodo['id']}: {e}")
            raise

    @staticmethod
    def actualizar_fhir_id(documento_id: int, fhir_patient_id: str) -> bool:
        """Actualiza el campo fhir_patient_id para vincular la DB local con FHIR."""
        nodo = _nodo_por_documento(documento_id)
        try:
            conn = _conectar(nodo)
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE usuario SET fhir_patient_id = %s, updated_at = NOW() WHERE documento_id = %s;",
                    (fhir_patient_id, documento_id)
                )
                conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error actualizando FHIR ID: {e}")
            return False

    # ─────────────────────────────────────────────
    # Utilidades
    # ─────────────────────────────────────────────

    @staticmethod
    def estado_tablas() -> List[Dict[str, Any]]:
        """Verifica si las tablas existen en cada nodo."""
        estados = []
        tablas_esperadas = ["usuario", "atencion", "tecnologia_salud", "diagnostico", "egreso", "profesional_salud"]
        for nodo in NODOS:
            info = {"nodo": nodo["id"], "estado": "DOWN", "tablas": {}}
            try:
                conn = _conectar(nodo)
                with conn.cursor() as cur:
                    for tabla in tablas_esperadas:
                        cur.execute(
                            "SELECT EXISTS (SELECT FROM information_schema.tables "
                            "WHERE table_schema = 'public' AND table_name = %s);",
                            (tabla,)
                        )
                        info["tablas"][tabla] = cur.fetchone()[0]
                conn.close()
                info["estado"] = "UP"
            except Exception as e:
                info["error"] = str(e)
            estados.append(info)
        return estados

    # ─────────────────────────────────────────────
    # CRUD Profesionales de Salud (Médicos)
    # ─────────────────────────────────────────────

    @staticmethod
    def crear_profesional(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo profesional de salud en el nodo 1 (tabla compartida).
        Retorna el profesional creado con su ID.
        """
        nodo = NODOS[0]  # Los profesionales están en el nodo 1

        try:
            conn = _conectar(nodo)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO profesional_salud
                      (nombre, especialidad, registro_medico, entidad_salud, email, telefono, activo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING *;
                """, (
                    data.get("nombre"),
                    data.get("especialidad"),
                    data.get("registroMedico"),
                    data.get("entidadSalud"),
                    data.get("email"),
                    data.get("telefono"),
                    data.get("activo", True),
                ))
                row = cur.fetchone()
                conn.commit()
            conn.close()

            profesional = dict(row)
            profesional["_nodo"] = nodo["id"]
            return {"success": True, "profesional": profesional, "nodo": nodo["id"]}

        except Exception as e:
            logger.error(f"Error creando profesional en {nodo['id']}: {e}")
            raise

    @staticmethod
    def obtener_profesional(profesional_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca un profesional por su UUID.
        Retorna None si no existe.
        """
        nodo = NODOS[0]  # Los profesionales están en el nodo 1
        try:
            conn = _conectar(nodo)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM profesional_salud WHERE id_personal_salud = %s;",
                    (profesional_id,)
                )
                row = cur.fetchone()
            conn.close()

            if row:
                profesional = dict(row)
                profesional["_nodo"] = nodo["id"]
                return profesional
            return None
        except Exception as e:
            logger.error(f"Error buscando profesional {profesional_id}: {e}")
            raise

    @staticmethod
    def listar_profesionales(
        activos_only: bool = True,
        especialidad: Optional[str] = None,
        limite: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Lista todos los profesionales de salud.
        Filtros opcionales: activos_only, especialidad.
        """
        nodo = NODOS[0]  # Los profesionales están en el nodo 1
        resultados = []

        try:
            conn = _conectar(nodo)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM profesional_salud WHERE 1=1"
                params = []

                if activos_only:
                    query += " AND activo = TRUE"

                if especialidad:
                    query += " AND especialidad ILIKE %s"
                    params.append(f"%{especialidad}%")

                query += " ORDER BY nombre LIMIT %s"
                params.append(limite)

                cur.execute(query, params)
                filas = cur.fetchall()
            conn.close()

            for f in filas:
                p = dict(f)
                p["_nodo"] = nodo["id"]
                resultados.append(p)

            return resultados
        except Exception as e:
            logger.error(f"Error listando profesionales: {e}")
            raise

    @staticmethod
    def buscar_profesionales_por_nombre(nombre: str, limite: int = 20) -> List[Dict[str, Any]]:
        """Busca profesionales por nombre (búsqueda parcial)."""
        nodo = NODOS[0]
        resultados = []

        try:
            conn = _conectar(nodo)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """SELECT * FROM profesional_salud
                       WHERE LOWER(nombre) LIKE LOWER(%s) AND activo = TRUE
                       ORDER BY nombre LIMIT %s;""",
                    (f"%{nombre}%", limite)
                )
                filas = cur.fetchall()
            conn.close()

            for f in filas:
                p = dict(f)
                p["_nodo"] = nodo["id"]
                resultados.append(p)
            return resultados
        except Exception as e:
            logger.error(f"Error buscando profesionales: {e}")
            raise

    @staticmethod
    def actualizar_profesional(profesional_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Actualiza un profesional existente.
        Solo actualiza los campos proporcionados.
        """
        nodo = NODOS[0]

        # Verificar que existe
        existente = DBService.obtener_profesional(profesional_id)
        if not existente:
            return None

        # Construir SET dinámico
        campos = []
        valores = []

        if "nombre" in data:
            campos.append("nombre = %s")
            valores.append(data["nombre"])
        if "especialidad" in data:
            campos.append("especialidad = %s")
            valores.append(data["especialidad"])
        if "registroMedico" in data:
            campos.append("registro_medico = %s")
            valores.append(data["registroMedico"])
        if "entidadSalud" in data:
            campos.append("entidad_salud = %s")
            valores.append(data["entidadSalud"])
        if "email" in data:
            campos.append("email = %s")
            valores.append(data["email"])
        if "telefono" in data:
            campos.append("telefono = %s")
            valores.append(data["telefono"])
        if "activo" in data:
            campos.append("activo = %s")
            valores.append(data["activo"])

        if not campos:
            return {"success": True, "profesional": existente, "nodo": nodo["id"], "accion": "sin_cambios"}

        campos.append("updated_at = NOW()")
        valores.append(profesional_id)

        try:
            conn = _conectar(nodo)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = f"UPDATE profesional_salud SET {', '.join(campos)} WHERE id_personal_salud = %s RETURNING *;"
                cur.execute(query, valores)
                row = cur.fetchone()
                conn.commit()
            conn.close()

            profesional = dict(row)
            profesional["_nodo"] = nodo["id"]
            return {"success": True, "profesional": profesional, "nodo": nodo["id"], "accion": "actualizado"}

        except Exception as e:
            logger.error(f"Error actualizando profesional {profesional_id}: {e}")
            raise

    @staticmethod
    def eliminar_profesional(profesional_id: str) -> bool:
        """
        Elimina un profesional de la base de datos.
        Retorna True si se eliminó, False si no existía.
        """
        nodo = NODOS[0]

        try:
            conn = _conectar(nodo)
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM profesional_salud WHERE id_personal_salud = %s;",
                    (profesional_id,)
                )
                deleted = cur.rowcount > 0
                conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            logger.error(f"Error eliminando profesional {profesional_id}: {e}")
            raise

    # ─────────────────────────────────────────────
    # CRUD Profesionales de Salud (Médicos)
    # ─────────────────────────────────────────────

    @staticmethod
    def crear_profesional(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo profesional de salud en TODOS los nodos (tabla replicada).
        Retorna el profesional creado con su UUID.
        """
        import uuid

        profesional_id = data.get("id_personal_salud") or str(uuid.uuid4())
        resultados = []

        for nodo in NODOS:
            resultado = {"nodo": nodo["id"], "estado": "OK", "error": None}
            try:
                conn = _conectar(nodo)
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO profesional_salud
                          (id_personal_salud, nombre, especialidad, registro_medico,
                           entidad_salud, email, telefono, activo, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """, (
                        profesional_id,
                        data["nombre"],
                        data.get("especialidad"),
                        data.get("registro_medico"),
                        data.get("entidad_salud"),
                        data.get("email"),
                        data.get("telefono"),
                        data.get("activo", True),
                    ))
                    conn.commit()
                conn.close()
                logger.info(f"Profesional creado en {nodo['id']}: {profesional_id}")
            except Exception as e:
                resultado["estado"] = "ERROR"
                resultado["error"] = str(e)
                logger.error(f"Error creando profesional en {nodo['id']}: {e}")
            resultados.append(resultado)

        exitosos = sum(1 for r in resultados if r["estado"] == "OK")
        return {
            "success": exitosos > 0,
            "id_personal_salud": profesional_id,
            "mensaje": f"Profesional creado en {exitosos}/{len(NODOS)} nodos",
            "nodos": resultados,
        }

    @staticmethod
    def listar_profesionales(
        solo_activos: bool = True,
        especialidad: Optional[str] = None,
        busqueda: Optional[str] = None,
        limite: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Lista profesionales de salud.
        Busca en el primer nodo disponible (tabla replicada).
        """
        resultados = []

        for nodo in NODOS:
            try:
                conn = _conectar(nodo)
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                        SELECT id_personal_salud, nombre, especialidad, registro_medico,
                               entidad_salud, email, telefono, activo, created_at
                        FROM profesional_salud
                        WHERE 1=1
                    """
                    params = []

                    if solo_activos:
                        query += " AND activo = TRUE"
                    if especialidad:
                        query += " AND LOWER(especialidad) = LOWER(%s)"
                        params.append(especialidad)
                    if busqueda:
                        query += " AND (LOWER(nombre) LIKE LOWER(%s) OR LOWER(registro_medico) LIKE LOWER(%s))"
                        params.append(f"%{busqueda}%")
                        params.append(f"%{busqueda}%")

                    query += " ORDER BY nombre ASC LIMIT %s"
                    params.append(limite)

                    cur.execute(query, params)
                    filas = cur.fetchall()
                conn.close()

                for f in filas:
                    p = dict(f)
                    p["_nodo"] = nodo["id"]
                    resultados.append(p)

                # Solo necesitamos leer de un nodo (tabla replicada)
                break

            except psycopg2.errors.UndefinedTable:
                logger.warning(f"Tabla profesional_salud no existe en {nodo['id']} — inicializando...")
                DBService.inicializar_tablas(nodo)
                continue
            except Exception as e:
                logger.warning(f"Error listando profesionales en {nodo['id']}: {e}")
                continue

        return resultados

    @staticmethod
    def obtener_profesional(id_personal_salud: str) -> Optional[Dict[str, Any]]:
        """Obtiene un profesional por su UUID."""
        for nodo in NODOS:
            try:
                conn = _conectar(nodo)
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """SELECT id_personal_salud, nombre, especialidad, registro_medico,
                                  entidad_salud, email, telefono, activo, created_at
                           FROM profesional_salud WHERE id_personal_salud = %s;""",
                        (id_personal_salud,)
                    )
                    row = cur.fetchone()
                conn.close()
                if row:
                    profesional = dict(row)
                    profesional["_nodo"] = nodo["id"]
                    return profesional
                return None
            except Exception as e:
                logger.warning(f"Error obteniendo profesional en {nodo['id']}: {e}")
                continue
        return None

    @staticmethod
    def actualizar_profesional(id_personal_salud: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un profesional en TODOS los nodos."""
        resultados = []

        for nodo in NODOS:
            resultado = {"nodo": nodo["id"], "estado": "OK", "error": None}
            try:
                conn = _conectar(nodo)
                with conn.cursor() as cur:
                    campos = []
                    valores = []

                    for campo in ["nombre", "especialidad", "registro_medico", "entidad_salud", "email", "telefono", "activo"]:
                        if campo in data and data[campo] is not None:
                            campos.append(f"{campo} = %s")
                            valores.append(data[campo])

                    if not campos:
                        conn.close()
                        continue

                    campos.append("updated_at = NOW()")
                    valores.append(id_personal_salud)

                    query = f"UPDATE profesional_salud SET {', '.join(campos)} WHERE id_personal_salud = %s"
                    cur.execute(query, valores)
                    conn.commit()
                conn.close()
                logger.info(f"Profesional actualizado en {nodo['id']}: {id_personal_salud}")
            except Exception as e:
                resultado["estado"] = "ERROR"
                resultado["error"] = str(e)
                logger.error(f"Error actualizando profesional en {nodo['id']}: {e}")
            resultados.append(resultado)

        exitosos = sum(1 for r in resultados if r["estado"] == "OK")
        return {
            "success": exitosos > 0,
            "mensaje": f"Profesional actualizado en {exitosos}/{len(NODOS)} nodos",
            "nodos": resultados,
        }

    @staticmethod
    def eliminar_profesional(id_personal_salud: str) -> Dict[str, Any]:
        """Elimina un profesional en TODOS los nodos."""
        resultados = []

        for nodo in NODOS:
            resultado = {"nodo": nodo["id"], "estado": "OK", "error": None}
            try:
                conn = _conectar(nodo)
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM profesional_salud WHERE id_personal_salud = %s", (id_personal_salud,))
                    conn.commit()
                conn.close()
                logger.info(f"Profesional eliminado en {nodo['id']}: {id_personal_salud}")
            except Exception as e:
                resultado["estado"] = "ERROR"
                resultado["error"] = str(e)
                logger.error(f"Error eliminando profesional en {nodo['id']}: {e}")
            resultados.append(resultado)

        exitosos = sum(1 for r in resultados if r["estado"] == "OK")
        return {
            "success": exitosos > 0,
            "mensaje": f"Profesional eliminado en {exitosos}/{len(NODOS)} nodos",
            "nodos": resultados,
        }
