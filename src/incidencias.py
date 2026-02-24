from __future__ import annotations

from mysql.connector.connection import MySQLConnection

from db import execute, fetch_all


def listar_incidencias_activas(conn: MySQLConnection) -> list[dict]:
    """
    Devuelve incidencias cuyo estado NO sea 'cerrada'.

    Requisitos:
    - Debe devolver una lista de diccionarios (una fila por dict).
    - Debe ordenar primero por prioridad (alta > media > baja) y luego por fecha_apertura ascendente.
    - Debe usar fetch_all(conn, sql, params) para ejecutar el SELECT.

    Pista: se puede ordenar por prioridad usando CASE en SQL.
    """
    query = """
        SELECT * FROM incidencias
        WHERE estado <> 'cerrada'
        ORDER BY 
            CASE prioridad 
                WHEN 'alta' THEN 1 
                WHEN 'media' THEN 2 
                WHEN 'baja' THEN 3 
            END ASC,
            fecha_apertura ASC
    """
    return fetch_all(conn, query)


def listar_incidencias_sin_tecnico(conn: MySQLConnection) -> list[dict]:
    """
    Devuelve incidencias activas sin técnico asignado.

    Requisitos:
    - tecnico_id IS NULL
    - estado <> 'cerrada'
    - ordenar por fecha_apertura ascendente
    """
    query = """
        SELECT * FROM incidencias
        WHERE tecnico_id IS NULL AND estado <> 'cerrada'
        ORDER BY fecha_apertura ASC
    """
    return fetch_all(conn, query)


def crear_incidencia(conn: MySQLConnection, equipo_id: int, descripcion: str, prioridad: str = "media") -> int:
    """
    Crea una incidencia nueva en estado 'abierta'.

    Validaciones:
    - descripcion no puede ser vacía ni solo espacios (ValueError)
    - prioridad debe ser 'baja', 'media' o 'alta' (ValueError)
    - equipo_id debe ser entero positivo (ValueError)

    Requisitos SQL:
    - INSERT en tabla incidencias
    - tecnico_id debe ser NULL
    - estado debe ser 'abierta'
    - fecha_apertura debe ser NOW()
    - fecha_cierre debe ser NULL

    Debe devolver el número de filas afectadas (normalmente 1).
    """
    if not descripcion or not descripcion.strip():
        raise ValueError("La descripción no puede estar vacía.")
    
    if prioridad not in ("baja", "media", "alta"):
        raise ValueError("La prioridad debe ser 'baja', 'media' o 'alta'.")
        
    if type(equipo_id) is not int or equipo_id <= 0:
        raise ValueError("El equipo_id debe ser un entero positivo.")

    query = """
        INSERT INTO incidencias 
            (equipo_id, descripcion, prioridad, estado, fecha_apertura, tecnico_id, fecha_cierre)
        VALUES 
            (%s, %s, %s, 'abierta', NOW(), NULL, NULL)
    """
    return execute(conn, query, (equipo_id, descripcion, prioridad))


def asignar_tecnico(conn: MySQLConnection, incidencia_id: int, tecnico_id: int) -> int:
    """
    Asigna un técnico a una incidencia y la marca como 'en_proceso' si la incidencia no está cerrada.

    Validaciones:
    - incidencia_id y tecnico_id deben ser enteros positivos (ValueError)

    Requisitos:
    - UPDATE sobre incidencias
    - Solo debe actualizar si estado <> 'cerrada'
    - Debe devolver filas afectadas (0 si no existe o ya está cerrada)
    """
    if type(incidencia_id) is not int or incidencia_id <= 0:
        raise ValueError("El incidencia_id debe ser un entero positivo.")
        
    if type(tecnico_id) is not int or tecnico_id <= 0:
        raise ValueError("El tecnico_id debe ser un entero positivo.")

    query = """
        UPDATE incidencias
        SET tecnico_id = %s, estado = 'en_proceso'
        WHERE id = %s AND estado <> 'cerrada'
    """
    return execute(conn, query, (tecnico_id, incidencia_id))


def cerrar_incidencia(conn: MySQLConnection, incidencia_id: int) -> int:
    """
    Cierra una incidencia.

    Validaciones:
    - incidencia_id debe ser entero positivo (ValueError)

    Requisitos:
    - UPDATE sobre incidencias
    - estado='cerrada'
    - fecha_cierre=NOW()
    - Solo debe cerrar si estado <> 'cerrada'
    - Devuelve filas afectadas
    """
    if type(incidencia_id) is not int or incidencia_id <= 0:
        raise ValueError("El incidencia_id debe ser un entero positivo.")

    query = """
        UPDATE incidencias
        SET estado = 'cerrada', fecha_cierre = NOW()
        WHERE id = %s AND estado <> 'cerrada'
    """
    return execute(conn, query, (incidencia_id,))


def detalle_incidencias_join(conn: MySQLConnection) -> list[dict]:
    """
    Devuelve una vista enriquecida con datos de equipo y técnico.

    Columnas mínimas esperadas:
    - i.id, i.descripcion, i.prioridad, i.estado, i.fecha_apertura, i.fecha_cierre
    - e.tipo, e.modelo, e.ubicacion, e.estado AS estado_equipo
    - t.nombre AS tecnico (puede ser NULL si no hay técnico)

    Requisitos:
    - JOIN equipos (obligatorio)
    - LEFT JOIN tecnicos (opcional)
    - Ordenar por estado, prioridad DESC, fecha_apertura ASC
    """
    query = """
        SELECT 
            i.id, i.descripcion, i.prioridad, i.estado, i.fecha_apertura, i.fecha_cierre,
            e.tipo, e.modelo, e.ubicacion, e.estado AS estado_equipo,
            t.nombre AS tecnico
        FROM incidencias i
        JOIN equipos e ON i.equipo_id = e.id
        LEFT JOIN tecnicos t ON i.tecnico_id = t.id
        ORDER BY i.estado, i.prioridad DESC, i.fecha_apertura ASC
    """
    return fetch_all(conn, query)
