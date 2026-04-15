from flask import Flask, render_template, request, redirect, session
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
        documento = request.form["documento"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM usuarios WHERE documento = ? AND activo = 1",
            (documento,)
        ).fetchone()

        if user and user["password"] == password:
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
        documento = request.form["documento"]
        nombre = request.form["nombre"]
        apellido1 = request.form["apellido1"]
        if apellido1=="":
            apellido1="None"
            
        apellido2 = request.form["apellido2"]
        if apellido2=="":
            apellido2="None"
            
        estado = request.form["estado"]
        if estado!="0":
            estado=1

        db.execute("""
            UPDATE usuarios 
            SET documento=?, nombre=?, apellido_1=?, apellido_2=?, activo=?
            WHERE id=?
        """, (documento, nombre, apellido1, apellido2, estado, id))

        db.commit()
        return redirect("/usuarios")

    usuario = db.execute(
        "SELECT * FROM usuarios WHERE id=?",
        (id,)
    ).fetchone()

    return render_template("editar_usuario.html", usuario=usuario)            

@app.route("/productos")
def productos():
    db = get_db()

    if session.get('rol') in ['admin', 'empleado']:
        productos = db.execute("""
            SELECT *,
            CASE 
                WHEN activo = 1 THEN 'Disponible'
                ELSE 'No disponible'
            END AS estado
            FROM productos
        """).fetchall()
    else:
        productos = db.execute("""
            SELECT *,
            CASE 
                WHEN activo = 1 THEN 'Disponible'
                ELSE 'No disponible'
            END AS estado
            FROM productos
            WHERE activo = 1 AND stock > 0
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
        nombre = request.form["nombre"]
        categoria = request.form["categoria"]
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
        nombre = request.form["nombre"]
        categoria = request.form["categoria"]
        stock = request.form["stock"]
        precio_user = request.form["precio_user"]
        precio_in = request.form["precio_in"]
        descripcion = request.form["descripcion"]

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
    db.execute("UPDATE productos SET activo=0 WHERE id=?", (id,))
    db.commit()

    return redirect("/productos")


if __name__ == "__main__":
    app.run(debug=True)