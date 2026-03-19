from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "tareas.db"


# ── Inicializar base de datos ──────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo      TEXT    NOT NULL,
            descripcion TEXT,
            estado      TEXT    NOT NULL DEFAULT 'pendiente',
            creado_en   DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # devuelve filas como dict
    return conn


# ── POST /tareas  →  Crear tarea ───────────────────────────────────────────────
@app.route("/tareas", methods=["POST"])
def crear_tarea():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Se esperaba JSON en el cuerpo de la petición"}), 400

    titulo = data.get("titulo", "").strip()
    if not titulo:
        return jsonify({"error": "El campo 'titulo' es obligatorio"}), 400

    descripcion = data.get("descripcion", "")
    estado = data.get("estado", "pendiente")

    ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
    if estado not in ESTADOS_VALIDOS:
        return jsonify({"error": f"Estado inválido. Opciones: {ESTADOS_VALIDOS}"}), 400

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO tareas (titulo, descripcion, estado) VALUES (?, ?, ?)",
        (titulo, descripcion, estado)
    )
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()

    return jsonify({"mensaje": "Tarea creada", "id": tarea_id}), 201


# ── GET /tareas  →  Consultar todas las tareas ─────────────────────────────────
@app.route("/tareas", methods=["GET"])
def obtener_tareas():
    estado_filtro = request.args.get("estado")        # ?estado=pendiente
    conn = get_db()

    if estado_filtro:
        filas = conn.execute(
            "SELECT * FROM tareas WHERE estado = ? ORDER BY creado_en DESC",
            (estado_filtro,)
        ).fetchall()
    else:
        filas = conn.execute(
            "SELECT * FROM tareas ORDER BY creado_en DESC"
        ).fetchall()

    conn.close()
    tareas = [dict(f) for f in filas]
    return jsonify(tareas), 200


# ── GET /tareas/<id>  →  Consultar una tarea ───────────────────────────────────
@app.route("/tareas/<int:tarea_id>", methods=["GET"])
def obtener_tarea(tarea_id):
    conn = get_db()
    fila = conn.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,)).fetchone()
    conn.close()

    if fila is None:
        return jsonify({"error": "Tarea no encontrada"}), 404

    return jsonify(dict(fila)), 200


# ── PUT /tareas/<id>  →  Actualizar tarea ─────────────────────────────────────
@app.route("/tareas/<int:tarea_id>", methods=["PUT"])
def actualizar_tarea(tarea_id):
    conn = get_db()
    fila = conn.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,)).fetchone()

    if fila is None:
        conn.close()
        return jsonify({"error": "Tarea no encontrada"}), 404

    data = request.get_json(silent=True) or {}

    titulo      = data.get("titulo",      fila["titulo"])
    descripcion = data.get("descripcion", fila["descripcion"])
    estado      = data.get("estado",      fila["estado"])

    ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
    if estado not in ESTADOS_VALIDOS:
        conn.close()
        return jsonify({"error": f"Estado inválido. Opciones: {ESTADOS_VALIDOS}"}), 400

    conn.execute(
        "UPDATE tareas SET titulo=?, descripcion=?, estado=? WHERE id=?",
        (titulo, descripcion, estado, tarea_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Tarea actualizada", "id": tarea_id}), 200


# ── DELETE /tareas/<id>  →  Eliminar tarea ────────────────────────────────────
@app.route("/tareas/<int:tarea_id>", methods=["DELETE"])
def eliminar_tarea(tarea_id):
    conn = get_db()
    fila = conn.execute("SELECT id FROM tareas WHERE id = ?", (tarea_id,)).fetchone()

    if fila is None:
        conn.close()
        return jsonify({"error": "Tarea no encontrada"}), 404

    conn.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Tarea eliminada", "id": tarea_id}), 200


# ── Punto de entrada ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
