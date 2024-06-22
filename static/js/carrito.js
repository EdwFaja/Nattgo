document.addEventListener('DOMContentLoaded', function () {
    var botonesAgregarAlCarrito = document.getElementsByClassName('btn-2');
    for (var i = 0; i < botonesAgregarAlCarrito.length; i++) {
        var button = botonesAgregarAlCarrito[i];
        button.addEventListener('click', agregarAlCarritoClicked);
    }

    document.getElementsByClassName('btn-pagar')[0].addEventListener('click', pagarClicked);
});

function agregarAlCarritoClicked(event) {
    var button = event.target;
    var item = button.closest('.item');
    var form = item.querySelector('.agregar-carrito-form');

    var formData = new FormData(form);
    fetch('/productos_urs', {
        method: 'POST',
        body: formData
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            agregarItemAlCarrito(data.producto.nombre, data.producto.precio, item.querySelector('.img-item').src);
            actualizarTotalCarrito();
        } else {
            alert("Error al agregar el producto al carrito: " + data.message);
        }
    }).catch(error => {
        console.error('Error:', error);
        alert('Error al agregar el producto al carrito.');
    });
}

function pagarClicked(event) {
    event.preventDefault(); // Evita que el formulario se envíe de la manera tradicional
    console.log("Botón de pagar clickeado");
    fetch('/guardar_pedido', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    }).then(response => response.json())
    .then(data => {
        console.log('Respuesta recibida:', data);
        if (data.success) {
            alert("Pedido guardado exitosamente");
            // Limpiar el carrito
            document.getElementsByClassName('carrito-items')[0].innerHTML = '';
            actualizarTotalCarrito();
        } else {
            alert("Error al guardar el pedido: " + data.message);
        }
    }).catch(error => {
        console.error('Error:', error);
        alert('Error al guardar el pedido.');
    });
}

function agregarItemAlCarrito(titulo, precio, imagenSrc) {
    var itemCarritoNuevo = document.createElement('div');
    itemCarritoNuevo.classList.add('carrito-item');
    itemCarritoNuevo.innerHTML = `
        <img src="${imagenSrc}" width="80px" alt="">
        <div class="carrito-item-detalles">
            <span class="carrito-item-titulo">${titulo}</span>
            <div class="selector-cantidad">
                <i class="fa-solid fa-minus restar-cantidad"></i>
                <input type="text" value="1" class="carrito-item-cantidad" disabled>
                <i class="fa-solid fa-plus sumar-cantidad"></i>
            </div>
            <span class="carrito-item-precio">${precio}</span>
        </div>
        <button class="btn-eliminar">
            <i class="fa-solid fa-trash"></i>
        </button>
    `;

    var itemsCarrito = document.getElementsByClassName('carrito-items')[0];
    itemsCarrito.append(itemCarritoNuevo);

    itemCarritoNuevo.getElementsByClassName('btn-eliminar')[0].addEventListener('click', eliminarItemCarrito);
    itemCarritoNuevo.getElementsByClassName('restar-cantidad')[0].addEventListener('click', restarCantidad);
    itemCarritoNuevo.getElementsByClassName('sumar-cantidad')[0].addEventListener('click', sumarCantidad);
}

function actualizarTotalCarrito() {
    var carritoItems = document.getElementsByClassName('carrito-item');
    var total = 0;
    for (var i = 0; i < carritoItems.length; i++) {
        var item = carritoItems[i];
        var precioElemento = item.getElementsByClassName('carrito-item-precio')[0];
        var precio = parseFloat(precioElemento.innerText.replace('$', '').replace(/\./g, '').replace(',', '.'));
        var cantidadItem = item.getElementsByClassName('carrito-item-cantidad')[0];
        var cantidad = cantidadItem.value;
        total += precio * cantidad;
    }
    document.getElementsByClassName('carrito-precio-total')[0].innerText = '$' + total.toLocaleString("es") + ",00";
}

function eliminarItemCarrito(event) {
    var buttonClicked = event.target;
    buttonClicked.closest('.carrito-item').remove();
    actualizarTotalCarrito();
}

function restarCantidad(event) {
    var buttonClicked = event.target;
    var selectorCantidad = buttonClicked.closest('.selector-cantidad');
    var inputCantidad = selectorCantidad.querySelector('.carrito-item-cantidad');
    var cantidadActual = parseInt(inputCantidad.value);

    if (cantidadActual > 1) {
        inputCantidad.value = cantidadActual - 1;
        actualizarTotalCarrito();
    }
}

function sumarCantidad(event) {
    var buttonClicked = event.target;
    var selectorCantidad = buttonClicked.closest('.selector-cantidad');
    var inputCantidad = selectorCantidad.querySelector('.carrito-item-cantidad');
    var cantidadActual = parseInt(inputCantidad.value);

    inputCantidad.value = cantidadActual + 1;
    actualizarTotalCarrito();
}
