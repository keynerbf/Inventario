from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "clave_secreta"


def get_db():
    conn = sqlite3.connect("inventario.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        documento = request.form["documento"].strip()
        password = request.form["password"].strip()

        db = get_db()
        user = db.execute(
            "SELECT * FROM usuarios WHERE documento = ? AND estado = 1",
            (documento,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["nombre"] = user['nombre']
            session["rol"] = user["rol"]
            
            return redirect("/")
        else:
            return "Credenciales incorrectas"

    return render_template("login.html")

@app.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    return redirect("/bienvenida")

@app.route("/bienvenida")
def bienvenida():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("bienvenida.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/usuarios")
def usuarios():
    db = get_db()

    if session.get('rol')=='admin':
        usuarios = db.execute("""
            SELECT * FROM usuarios
        """).fetchall()
    else:
        usuarios = []

    return render_template("usuarios.html", usuarios=usuarios)

@app.route("/editar_usuario/<int:id>", methods=["GET", "POST"])
def editar_usuario(id):
    if session.get('rol') != "admin":
        return redirect("/")

    db = get_db()

    if request.method == "POST":
        documento = request.form["documento"].strip()
        nombre = request.form["nombre"].strip()
        apellido_1 = request.form["apellido_1"].strip() or None
        apellido_2 = request.form["apellido_2"].strip() or None
        estado = int(request.form.get("estado", 1))

        db.execute("""
            UPDATE usuarios 
            SET documento=?, nombre=?, apellido_1=?, apellido_2=?, estado=?
            WHERE id=?
        """, (documento, nombre, apellido_1, apellido_2, estado, id))

        db.commit()
        return redirect("/usuarios")

    usuario = db.execute(
        "SELECT * FROM usuarios WHERE id=?",
        (id,)
    ).fetchone()

    return render_template("editar_usuario.html", usuario=usuario)            

@app.route("/crear_usuario", methods=["GET", "POST"])
def crear_usuario():
    if session.get('rol') != "admin":
        return redirect("/")
    
    db = get_db()
    if request.method == "POST":
        documento = request.form["documento"].strip()
        nombre = request.form["nombre"].strip()
        apellido_1 = request.form["apellido_1"].strip() or None
        apellido_2 = request.form["apellido_2"].strip() or None
        password = generate_password_hash(request.form["password"])

        db.execute("""
            INSERT INTO usuarios 
            (documento, nombre, apellido_1, apellido_2, password, rol)
            VALUES (?, ?, ?, ?, ?, 'empleado')
        """, (documento, nombre, apellido_1, apellido_2, password))
        db.commit()
        return redirect("/usuarios")
    return render_template("crear_usuario.html")

@app.route("/eliminar_usuario/<int:id>")
def eliminar_usuario(id):
    if "user_id" not in session:
        return redirect("/")

    if session["rol"] != "admin":
        return "No autorizado"

    db = get_db()
    db.execute("UPDATE usuarios SET estado = 1 - estado WHERE id = ?", (id,))
    db.commit()

    return redirect("/usuarios")

@app.route("/productos")
def productos():
    db = get_db()

    if session.get('rol') in ['admin', 'empleado']:
        productos = db.execute("""
            SELECT *,
            CASE 
                WHEN estado = 1 THEN 'Disponible'
                ELSE 'No disponible'
            END AS estado
            FROM productos
        """).fetchall()
    else:
        productos = db.execute("""
            SELECT *,
            CASE 
                WHEN estado = 1 THEN 'Disponible'
                ELSE 'No disponible'
            END AS estado
            FROM productos
            WHERE estado = 1 AND stock > 0
        """).fetchall()

    return render_template("productos.html", productos=productos)

@app.route("/agregar_producto", methods=["GET", "POST"])
def agregar_producto():
    if "user_id" not in session:
        return redirect("/")

    if session["rol"] != "admin":
        return "No autorizado"
    
    db = get_db()
    
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        categoria = request.form["categoria"].strip()
        stock = request.form["stock"]
        precio_user = request.form["precio_user"]
        precio_in = request.form["precio_in"]
        descripcion = request.form["descripcion"]

        db.execute("""
            INSERT INTO productos 
            (nombre, categoria, stock, precio_user, precio_in, descripcion)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (nombre, categoria, stock, precio_user, precio_in, descripcion))
        db.commit()
        return redirect("/productos")

    return render_template("agregar_producto.html")

@app.route("/editar_producto/<int:id>", methods=["GET", "POST"])
def editar_producto(id):
    if "user_id" not in session:
        return redirect("/")

    db = get_db()

    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        categoria = request.form["categoria"].strip()
        stock = request.form["stock"]
        precio_user = request.form["precio_user"]
        precio_in = request.form["precio_in"]
        descripcion = request.form.get("descripcion") or None

        db.execute("""
            UPDATE productos 
            SET nombre=?, categoria=?, stock=?, precio_user=?, precio_in=?, descripcion=?
            WHERE id=?
        """, (nombre, categoria, stock, precio_user, precio_in, descripcion, id))

        db.commit()
        return redirect("/productos")

    producto = db.execute(
        "SELECT * FROM productos WHERE id=?",
        (id,)
    ).fetchone()

    return render_template("editar_producto.html", producto=producto)

@app.route("/eliminar_producto/<int:id>")
def eliminar_producto(id):
    if "user_id" not in session:
        return redirect("/")

    if session["rol"] != "admin":
        return "No autorizado"

    db = get_db()
    db.execute("UPDATE productos SET estado = 1 - estado WHERE id = ?", (id,))
    db.commit()

    return redirect("/productos")


if __name__ == "__main__":
    app.run(debug=True)