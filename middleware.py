
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Configuración de los nodos
# Usar nombres de contenedores cuando se ejecuta en Docker, localhost cuando se ejecuta localmente
USE_DOCKER_NAMES = os.getenv("USE_DOCKER_NAMES", "false").lower() == "true"

if USE_DOCKER_NAMES:
    NODOS = [
        {"host": "pg_nodo1", "port": 5432, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
        {"host": "pg_nodo2", "port": 5432, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
        {"host": "pg_nodo3", "port": 5432, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
    ]
else:
    NODOS = [
        {"host": "localhost", "port": 5433, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
        {"host": "localhost", "port": 5434, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
        {"host": "localhost", "port": 5435, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
    ]

def ejecutar_query_en_todos_los_nodos(query):
    resultados = []
    nodos_estado = []
    
    for nodo in NODOS:
        nodo_info = {"nodo": f"nodo_{nodo['port']}", "estado": "DOWN", "error": None}
        try:
            conn = psycopg2.connect(
                host=nodo["host"],
                port=nodo["port"],
                user=nodo["user"],
                password=nodo["password"],
                dbname=nodo["dbname"]
            )
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                filas = cur.fetchall()
                resultados.extend(filas)
            conn.close()
            nodo_info["estado"] = "UP"
        except Exception as e:
            nodo_info["error"] = str(e)
            print(f"Error en nodo {nodo['port']}: {e}")
        
        nodos_estado.append(nodo_info)
            
    return {"resultados": resultados, "nodos_estado": nodos_estado}


def insertar_registro_firh(tabla, datos):
    """
    Inserta un registro en la tabla especificada en el nodo correcto
    basado en el documento_id (fragmentación horizontal)
    """
    if "documento_id" not in datos:
        raise ValueError("documento_id es requerido para enrutar el registro")
    
    documento_id = int(datos["documento_id"])
    
    # Determinar el nodo según el rango de documento_id
    if documento_id < 4000000000:
        nodo_idx = 0  # Nodo 1
    elif documento_id < 7000000000:
        nodo_idx = 1  # Nodo 2
    else:
        nodo_idx = 2  # Nodo 3
    
    nodo = NODOS[nodo_idx]
    
    # Construir la consulta INSERT
    columnas = ", ".join(datos.keys())
    placeholders = ", ".join(["%s"] * len(datos))
    valores = list(datos.values())
    
    query = f"INSERT INTO {tabla} ({columnas}) VALUES ({placeholders})"
    
    try:
        conn = psycopg2.connect(
            host=nodo["host"],
            port=nodo["port"],
            user=nodo["user"],
            password=nodo["password"],
            dbname=nodo["dbname"]
        )
        with conn.cursor() as cur:
            cur.execute(query, valores)
            conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Registro insertado en {tabla} en nodo {nodo_idx + 1}",
            "nodo": f"nodo_{nodo['port']}",
            "documento_id": documento_id
        }
    except Exception as e:
        raise Exception(f"Error al insertar en nodo {nodo_idx + 1}: {str(e)}")


if __name__ == "__main__":
    consulta = "SELECT documento_id, nombre_completo, edad FROM usuario;"
    resultados = ejecutar_query_en_todos_los_nodos(consulta)
    for fila in resultados:
        print(fila)
