from flask import Flask, render_template, request, redirect, session, url_for, flash
import os
from werkzeug.utils import secure_filename
from babel.numbers import format_currency
from datetime import datetime
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Conexión a la base de datos
database = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    db="nattgo"
)


# Directorio donde se guardarán las imágenes
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER = 'C:/Users/esant/OneDrive/Escritorio/Gono/src/static/uploads'


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def obtener_productos():
    cursor = database.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    cursor.close()
    return productos

# Rutas adicionales


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/index_urs')
def index_urs():
     if 'user_id' not in session:
         return redirect(url_for('inicioSesion'))

     user_name = session['user_name']
     return render_template('/clients/index_urs.html', user_name=user_name)


@app.route('/productos')
def productos():
    productos = obtener_productos()

    for producto in productos:
        if isinstance(producto['imgproductos'], bytes):
            producto['imgproductos'] = producto['imgproductos'].decode('utf-8')
        
        # Formatear el precio a pesos colombianos
        producto['valorproducto'] = format_currency(producto['valorproducto'], 'COP', locale='es_CO')

    return render_template('productos.html', productos=productos)

@app.route('/productos_urs', methods=['GET', 'POST'])
def productos_urs():
    if request.method == 'POST':
        if 'carrito' not in session:
            session['carrito'] = []

        producto_id = request.form['id_producto']
        nombre_producto = request.form['nombre_producto']
        precio_producto = request.form['precio_producto']

        item_carrito = {
            'id': producto_id,
            'nombre': nombre_producto,
            'precio': precio_producto,
            'cantidad': 1
        }

        session['carrito'].append(item_carrito)
        session.modified = True

        return 'Producto agregado al carrito'

    else:
        productos = obtener_productos()
        for producto in productos:
            if isinstance(producto['imgproductos'], bytes):
                producto['imgproductos'] = producto['imgproductos'].decode('utf-8')
            # Formatear el precio a pesos colombianos
            producto['valorproducto'] = format_currency(producto['valorproducto'], 'COP', locale='es_CO')

        return render_template('/clients/productos_urs.html', productos=productos)

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')


@app.route('/nosotros_urs')
def nosotros_urs():
    return render_template('/clients/nosotros_urs.html')


@app.route('/contacto')
def contacto():
    return render_template('contacto.html')


@app.route('/contacto_urs')
def contacto_urs():
    return render_template('/clients/contacto_urs.html')


@app.route('/inicioSesion', methods=['GET', 'POST'])
def inicioSesion():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']

        cursor = database.cursor()
        sql = "SELECT idusuario, contraseñausuario, idrol, nombreusuario FROM usuarios WHERE emailusuario = %s"
        cursor.execute(sql, (usuario,))
        user = cursor.fetchone()
        cursor.close()

        if user and user[1] == contrasena:
            session['user_id'] = user[0]
            session['user_name'] = user[3]

            if user[2] == 2:
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('index_urs'))
        else:
            return render_template('inicioSesion.html', error="Usuario o contraseña incorrectos")

    return render_template('inicioSesion.html')


@app.route('/registrarse', methods=['GET', 'POST'])
def registrar():

    if request.method == 'POST':

        idciudad = request.form['id_ciudad']
        correo = request.form['correo']
        contraseña = request.form['password']
        nombre_usuario = request.form['nombres']
        fechanacimientousuario = request.form['fechanacimientousuario']
        apellidos_usuario = request.form['apellidos']
        telefono_usuario = request.form['telefono']
        id_rol = 1

        cursor = database.cursor()
        sql = "INSERT INTO usuarios (nombreusuario, apellidousuario, telefonousuario, emailusuario, fechanacimientousuario, contraseñausuario, idrol, idciudad) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        data = (nombre_usuario, apellidos_usuario, telefono_usuario,
                correo, fechanacimientousuario, contraseña, id_rol, idciudad)
        cursor.execute(sql, data)
        database.commit()
        cursor.close()

        return render_template('iniciosesion.html')
    else:
        cursor = database.cursor()
        cursor.execute("SELECT idciudad, nombreciudad FROM ciudades")
        ciudades = cursor.fetchall()

        cursor.close()
    return render_template('registrar.html', ciudades=ciudades)


@app.route('/contraseña')
def contraseña():
    return render_template('contraseña.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/ventas')
def ventas():
    
    
    
    
    
    
    
    
    
    
    return render_template('ventas.html')


@app.route('/inventario', methods=['GET', 'POST'])
def inventario():
    cursor = database.cursor(dictionary=True)

    if request.method == 'POST':
        form_data = request.form

        if 'nombreproducto' in form_data:
            # Manejar la creación de un nuevo producto con imagen
            file = request.files.get('imgproductos')
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                # Crear el directorio si no existe
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])

                file.save(filepath)

                nombreproducto = form_data['nombreproducto']
                valorproducto = form_data['valorproducto']
                idproveedor = form_data['proveedor']
                idcategoria = form_data['categoria']
                idtalla = form_data['talla']

                cursor.execute("START TRANSACTION")

                # Insertar producto
                cursor.execute("""
                    INSERT INTO productos (nombreproducto, valorproducto, idproveedor, idcategoria, idtalla, imgproductos)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (nombreproducto, valorproducto, idproveedor, idcategoria, idtalla, filename))

                idproducto = cursor.lastrowid

                # Insertar inventario
                cursor.execute("""
                    INSERT INTO inventario (idproducto, stockinventario, fechastock)
                    VALUES (%s, %s, NOW())
                """, (idproducto, 0))

                idinventario = cursor.lastrowid

                # Insertar entrada con cantidad inicial 0
                cursor.execute("""
                    INSERT INTO entrada (cantidadentrada, fechaentrada, idinventario)
                    VALUES (%s, NOW(), %s)
                """, (0, idinventario))

                database.commit()
                flash('Producto, inventario y entrada creados con éxito')
            else:
                flash('Archivo de imagen no válido o faltante')

        elif 'producto' in form_data:
            # Manejar la actualización del stock
            idproducto = form_data['producto']
            cantidadentrada = int(form_data['cantidadentrada'])
            fechaentrada = form_data['fechaentrada']

            # Verificar si el producto ya está en el inventario
            cursor.execute("""
                SELECT idinventario FROM inventario WHERE idproducto = %s
            """, (idproducto,))
            inventario_record = cursor.fetchone()

            if inventario_record:
                idinventario = inventario_record['idinventario']

                # Actualizar stock del inventario
                cursor.execute("""
                    UPDATE inventario
                    SET stockinventario = stockinventario + %s, fechastock = %s
                    WHERE idinventario = %s
                """, (cantidadentrada, fechaentrada, idinventario))

                # Insertar nueva entrada
                cursor.execute("""
                    INSERT INTO entrada (cantidadentrada, fechaentrada, idinventario)
                    VALUES (%s, %s, %s)
                """, (cantidadentrada, fechaentrada, idinventario))

                database.commit()
                flash('Entrada de inventario agregada con éxito')
            else:
                flash('El producto no está en el inventario')

        elif 'nombrecategoria' in form_data:
            # Manejar la creación de una nueva categoría
            nombrecategoria = form_data['nombrecategoria']

            cursor.execute(
                "INSERT INTO categorias (nombrecategoria) VALUES (%s)", (nombrecategoria,))
            database.commit()
            flash('Categoría creada con éxito')

        elif 'nombreproveedor' in form_data:
            nombreproveedor = form_data['nombreproveedor']
            direccionproveedor = form_data['direccionproveedor']
            telefonoproveedor = form_data['telefonoproveedor']

            cursor.execute("""
            INSERT INTO proveedor (nombreproveedor, direccionproveedor, telefonoproveedor)
            VALUES (%s, %s, %s)
            """, (nombreproveedor, direccionproveedor, telefonoproveedor))

            database.commit()
            flash('Proveedor creado con éxito')

        elif 'idproducto' in form_data:
            # Manejar la edición de un producto
            idproducto = form_data['idproducto']
            nombreproducto = form_data['nombreproducto']
            valorproducto = form_data['valorproducto']
            imagen_producto = request.files.get('imgproductos')

            # Verificar si se cargó una nueva imagen
            if imagen_producto and allowed_file(imagen_producto.filename):
                # Guardar la nueva imagen en el servidor
                filename = secure_filename(imagen_producto.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                imagen_producto.save(filepath)
            else:
                # Conservar la imagen existente
                cursor.execute("SELECT imgproductos FROM productos WHERE idproducto = %s", (idproducto,))
                imagen_actual = cursor.fetchone()['imgproductos']
                filename = imagen_actual

            # Actualizar los datos del producto en la base de datos
            cursor.execute("""
                UPDATE productos 
                SET nombreproducto = %s, valorproducto = %s, imgproductos = %s
                WHERE idproducto = %s
            """, (nombreproducto, valorproducto, filename, idproducto))

            database.commit()
            flash('Producto actualizado con éxito')

    cursor.execute("SELECT * FROM proveedor")
    proveedores = cursor.fetchall()
    cursor.execute("SELECT * FROM categorias")
    categorias = cursor.fetchall()
    cursor.execute("SELECT * FROM tallas")
    tallas = cursor.fetchall()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    cursor.execute("""
    SELECT DISTINCT
        i.idinventario,
        i.stockinventario,
        i.fechastock,
        p.idproducto,
        p.nombreproducto,
        p.valorproducto,
        c.idcategoria,
        c.nombrecategoria,
        t.numerotalla,
        t.letratalla,
        e.fechaentrada
    FROM 
        inventario i
    JOIN 
        productos p ON i.idproducto = p.idproducto
    LEFT JOIN 
        categorias c ON p.idcategoria = c.idcategoria
    LEFT JOIN 
        tallas t ON p.idtalla = t.idtalla
    LEFT JOIN 
        (SELECT idinventario, MAX(fechaentrada) AS fechaentrada
         FROM entrada
         GROUP BY idinventario) e1 ON i.idinventario = e1.idinventario
    LEFT JOIN 
        entrada e ON e1.idinventario = e.idinventario AND e1.fechaentrada = e.fechaentrada
    """)
    inventario = cursor.fetchall()
    cursor.close()
    for item in inventario:
        item['valorproducto'] = format_currency(item['valorproducto'], 'COP', locale='es_CO')
    return render_template('inventario.html', data=inventario, proveedores=proveedores, categorias=categorias, tallas=tallas, productos=productos)

if __name__ == '__main__':
    app.run(debug=True, port=4000)
