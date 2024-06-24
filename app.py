from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask import jsonify
import json
import os
from werkzeug.utils import secure_filename
from babel.numbers import format_currency
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import mysql.connector
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Conexión a la base de datos
database = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    db="nattgo"
)
# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'nattgou@gmail.com'
app.config['MAIL_PASSWORD'] = 'MVLV EE ZS VZCF Q KOJ'
app.config['MAIL_DEFAULT_SENDER'] = 'nattgou@gmail.com'

mail = Mail(app)

def get_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="",
            db="nattgo"
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print("Error al conectar a la base de datos:", e)
        return None

# Directorio donde se guardarán las imágenes
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = os.path.join('src', 'static', 'uploads')

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

        producto_id = request.form.get('id_producto')
        nombre_producto = request.form.get('nombre_producto')
        precio_producto = request.form.get('precio_producto')

        if not producto_id or not nombre_producto or not precio_producto:
            return jsonify({"success": False, "message": "Faltan campos necesarios en la solicitud."}), 400

        try:
            producto_id = int(producto_id)
        except ValueError:
            return jsonify({"success": False, "message": "ID de producto inválido."}), 400

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT stockinventario FROM inventario WHERE idproducto = %s", (producto_id,))
            stock = cursor.fetchone()

            if stock is None:
                return jsonify({"success": False, "message": "Producto no encontrado en el inventario."}), 404

            stock_disponible = stock['stockinventario']
            if stock_disponible < 1:
                return jsonify({"success": False, "message": f"No hay suficiente stock para el producto {nombre_producto}. Stock actual: {stock_disponible}"}), 400

            item_carrito = {
                'id': producto_id,
                'nombre': nombre_producto,
                'precio': precio_producto,
                'cantidad': 1
            }

            session['carrito'].append(item_carrito)
            session.modified = True

            return jsonify({'success': True, 'producto': item_carrito})

        except Error as e:
            return jsonify({"success": False, "message": f"Error al consultar la base de datos: {str(e)}"}), 500

    elif request.method == 'GET':
        try:
            productos = obtener_productos()
            for producto in productos:
                if isinstance(producto['imgproductos'], bytes):
                    producto['imgproductos'] = producto['imgproductos'].decode('utf-8')
                producto['valorproducto'] = format_currency(producto['valorproducto'], 'COP', locale='es_CO')

            return render_template('/clients/productos_urs.html', productos=productos)

        except Exception as e:
            print(f"Error al cargar productos: {str(e)}")
            return jsonify({"success": False, "message": f"Error al cargar productos: {str(e)}"}), 500

    else:
        return jsonify({"success": False, "message": "Método no permitido."}), 405

@app.route('/guardar_pedido', methods=['POST'])
def guardar_pedido():
    data = request.get_json()

    # Depuración para verificar el contenido de 'data'
    print(f"Contenido de 'data': {data}")

    if not data or 'carrito' not in data or data['carrito'] is None:
        return jsonify({'success': False, 'message': 'Faltan campos necesarios en la solicitud.'})

    # Depuración para verificar el contenido de 'carrito'
    print(f"Contenido de 'carrito': {data['carrito']}")

    try:
        productos = json.loads(data['carrito'])
    except json.JSONDecodeError as e:
        return jsonify({'success': False, 'message': 'Formato de JSON inválido en el carrito.'}), 400

    if not productos:
        return jsonify({'success': False, 'message': 'El carrito está vacío'})

    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Usuario no autenticado'})

    def normalizar_precio(precio):
        precio_limpio = precio.replace('.', '').replace(',', '.')
        if precio_limpio.startswith('$'):
            precio_limpio = precio_limpio[1:]
        return float(precio_limpio)

    total_venta = sum(normalizar_precio(p['precio']) * int(p['cantidad']) for p in productos)

    conn = get_db()
    cursor = conn.cursor()

    try:
        for producto in productos:
            cursor.execute("SELECT stockinventario FROM inventario WHERE idproducto = %s", (producto['id'],))
            result = cursor.fetchone()
            if result is None:
                return jsonify({'success': False, 'message': f'Producto con ID {producto["id"]} no encontrado en el inventario'})

            stock_actual = result[0]
            if stock_actual < int(producto['cantidad']):
                return jsonify({'success': False, 'message': f'No hay suficiente stock para el producto {producto["nombre"]}. Stock actual: {stock_actual}'})

        cursor.execute("""
            INSERT INTO ventas (fechaventa, precioventa, estadoventa, totalventa, idusuario, idproducto)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (datetime.now().date(), total_venta, 'ESPERA', total_venta, session['user_id'], productos[0]['id']))
        venta_id = cursor.lastrowid

        for producto in productos:
            cursor.execute("""
                INSERT INTO detalleventas (idventa, cantidadproducto, subtotaldetalleventa)
                VALUES (%s, %s, %s)
            """, (venta_id, int(producto['cantidad']), normalizar_precio(producto['precio']) * int(producto['cantidad'])))

            cursor.execute("""
                UPDATE inventario
                SET stockinventario = stockinventario - %s
                WHERE idproducto = %s
            """, (int(producto['cantidad']), producto['id']))

        conn.commit()
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'success': False, 'message': 'Error al guardar el pedido: {}'.format(err)})
    finally:
        cursor.close()

    session.pop('carrito', None)

    return jsonify({'success': True, 'message': 'Pedido guardado correctamente'})

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')


@app.route('/nosotros_urs')
def nosotros_urs():
    return render_template('/clients/nosotros_urs.html')


@app.route('/enviar_contacto', methods=['POST'])
def enviar_contacto():
    if request.method == 'POST':
        nombre = request.form['name']
        email = request.form['email']
        telefono = request.form['phone']
        mensaje = request.form['message']

        msg = Message('Mensaje de Contacto',
                      sender=app.config['MAIL_DEFAULT_SENDER'],
                      recipients=['nattgou@gmail.com'])
        msg.body = f'''
        Nombre: {nombre}
        Email: {email}
        Teléfono: {telefono}
        Mensaje:
        {mensaje}
        '''

        try:
            mail.send(msg)
            flash('Mensaje enviado correctamente', 'success')
        except Exception as e:
            flash(f'Error al enviar el mensaje: {str(e)}', 'danger')

        return redirect(url_for('contacto'))

    return redirect(url_for('contacto'))

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

            # Redirigir con el parámetro de sesión iniciada
            if user[2] == 2:
                return redirect(url_for('dashboard', session_iniciada=True))
            else:
                return redirect(url_for('index_urs', session_iniciada=True))
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
        # Verificar si el correo ya está registrado
        sql_check = "SELECT idusuario FROM usuarios WHERE emailusuario = %s"
        cursor.execute(sql_check, (correo,))
        user = cursor.fetchone()

        if user:
            cursor.close()
            return redirect(url_for('registrar', error="Correo ya registrado"))

        sql = """
        INSERT INTO usuarios (nombreusuario, apellidousuario, telefonousuario, emailusuario, fechanacimientousuario, contraseñausuario, idrol, idciudad)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        data = (nombre_usuario, apellidos_usuario, telefono_usuario, correo, fechanacimientousuario, contraseña, id_rol, idciudad)
        cursor.execute(sql, data)
        database.commit()
        cursor.close()

        return redirect(url_for('registrar', registro_exitoso=True))
    else:
        cursor = database.cursor()
        cursor.execute("SELECT idciudad, nombreciudad FROM ciudades")
        ciudades = cursor.fetchall()
        cursor.close()
        return render_template('registrar.html', ciudades=ciudades)


@app.route('/contraseña', methods=['GET', 'POST'])
def contraseña():
    if request.method == 'POST':
        correo = request.form['correo']
        cursor = database.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE emailusuario = %s", (correo,))
        usuario = cursor.fetchone()

        if usuario:
            # Envía el correo con la contraseña
            msg = Message('Recuperación de Contraseña', recipients=[correo])
            msg.body = f"Tu contraseña es: {usuario['contraseñausuario']}"
            mail.send(msg)
            flash('Correo enviado con la contraseña', 'success')
        else:
            flash('Correo no encontrado en la base de datos', 'danger')

        return redirect(url_for('contraseña'))

    return render_template('contraseña.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/ventas')
def ventas():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT ventas.idventa, usuarios.nombreusuario, ventas.fechaventa, ventas.estadoventa, ventas.totalventa
        FROM ventas
        JOIN usuarios ON ventas.idusuario = usuarios.idusuario
    """)
    ventas = cursor.fetchall()
    cursor.close()
    db.close()  # Asegúrate de cerrar la conexión a la base de datos

    return render_template('ventas.html', ventas=ventas)

@app.route('/comprobante/<int:id>')
def obtener_comprobante(id):
    db = get_db()
    if db is None:
        return jsonify({'success': False, 'message': 'Error de conexión a la base de datos'}), 500

    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT ventas.idventa, usuarios.nombreusuario, ventas.fechaventa, ventas.estadoventa, ventas.totalventa
            FROM ventas
            JOIN usuarios ON ventas.idusuario = usuarios.idusuario
            WHERE ventas.idventa = %s
        """, (id,))
        venta = cursor.fetchone()
        print("Venta obtenida:", venta)  # Mensaje de depuración

        if not venta:
            return jsonify({'success': False, 'message': 'Venta no encontrada'}), 404

        cursor.execute("""
            SELECT productos.nombreproducto, detalleventas.cantidadproducto, detalleventas.subtotaldetalleventa
            FROM detalleventas
            JOIN ventas ON detalleventas.idventa = ventas.idventa
            JOIN productos ON ventas.idproducto = productos.idproducto
            WHERE detalleventas.idventa = %s
        """, (id,))
        detalles = cursor.fetchall()
        print("Detalles obtenidos:", detalles)  # Mensaje de depuración

        return jsonify({'success': True, 'venta': venta, 'detalles': detalles})

    except mysql.connector.Error as err:
        print("Error en la consulta:", err)  # Mensaje de depuración
        return jsonify({'success': False, 'message': 'Error en la consulta: {}'.format(err)}), 500

    finally:
        cursor.close()
        db.close()  # Asegúrate de cerrar la conexión a la base de datos
@app.route('/actualizarEstadoVenta/<int:id>', methods=['PUT'])
def actualizar_estado_venta(id):
    try:
        # Obtener el estado nuevo de la venta desde los datos enviados por el cliente
        nuevo_estado = request.json.get('estado', None)
        if not nuevo_estado:
            return jsonify({'success': False, 'message': 'Estado no proporcionado'}), 400

        # Actualizar el estado de la venta en la base de datos
        db = get_db()
        if db:
            cursor = db.cursor()
            cursor.execute("""
                UPDATE ventas
                SET estadoventa = %s
                WHERE idventa = %s
            """, (nuevo_estado, id))
            db.commit()
            cursor.close()
            db.close()  # Cerrar la conexión después de usarla

            return jsonify({'success': True, 'message': f'Estado de venta actualizado a {nuevo_estado}'}), 200
        else:
            return jsonify({'success': False, 'message': 'Error de conexión a la base de datos'}), 500

    except Exception as e:
        print(f'Error al actualizar estado de venta: {str(e)}')
        return jsonify({'success': False, 'message': 'Error al actualizar el estado de la venta'}), 500


@app.route('/inventario', methods=['GET', 'POST'])
def inventario():
    cursor = database.cursor(dictionary=True)

    if request.method == 'POST':
        form_data = request.form

        if 'nombreproducto' in form_data and 'idproducto' not in form_data:
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
            print("Editando producto")
            # Manejar la edición de un producto
            idproducto = form_data['idproducto']
            nombreproducto = form_data['nombreproducto']
            valorproducto = form_data['valorproducto']
            imagen_producto = request.files.get('imgproductos')

            # Verificar si se cargó una nueva imagen
            if imagen_producto and allowed_file(imagen_producto.filename):
                print("Nueva imagen cargada")
                # Guardar la nueva imagen en el servidor
                filename = secure_filename(imagen_producto.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                imagen_producto.save(filepath)
            else:
                print("Conservar imagen existente")
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

@app.route('/consultas', methods=['GET'])
def consultas():
    
        cursor = database.cursor(dictionary=True) 
        cursor.execute("SELECT idproveedor, nombreproveedor, direccionproveedor, telefonoproveedor FROM proveedor")
        proveedores = cursor.fetchall()
        cursor.close()
        return render_template('consultas.html', proveedores=proveedores)  

if __name__ == '__main__':
    app.run(debug=True, port=4000)
