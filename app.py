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


@app.route("/productos")
def productos():
    db = get_db()

    if session.get('rol') in ['admin', 'empleado']:
        productos = db.execute("SELECT * FROM productos").fetchall()
    else:
        productos = db.execute("SELECT * FROM productos WHERE activo=1").fetchall()

    return render_template("productos.html", productos=productos)


@app.route("/agregar_producto", methods=["GET", "POST"])
def agregar_producto():
    if "user_id" not in session:
        return redirect("/")

    if session["rol"] != "admin":
        return "No autorizado"

    if request.method == "POST":
        nombre = request.form["nombre"]
        stock = request.form["stock"]
        precio = request.form["precio"]

        db = get_db()
        db.execute(
            "INSERT INTO productos (nombre, stock, precio_user) VALUES (?, ?, ?)",
            (nombre, stock, precio)
        )
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
        stock = request.form["stock"]

        db.execute(
            "UPDATE productos SET nombre=?, stock=? WHERE id=?",
            (nombre, stock, id)
        )
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