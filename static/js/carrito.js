document.addEventListener('DOMContentLoaded', function () {
    var botonesAgregarAlCarrito = document.getElementsByClassName('btn-2');
    for (var i = 0; i < botonesAgregarAlCarrito.length; i++) {
        var button = botonesAgregarAlCarrito[i];
        button.addEventListener('click', function(event) {
            event.preventDefault();
            agregarAlCarritoClicked(event);
        });
    }

    // Manejar el evento submit del formulario de guardar pedido
    document.getElementById('guardar-pedido-form').addEventListener('submit', function(event) {
        event.preventDefault(); // Prevenir la recarga de la página
        pagarClicked();
    });
});

function agregarAlCarritoClicked(event) {
    var button = event.target;
    var form = button.closest('form');
    var formData = new FormData(form);

    fetch('/productos_urs', {
        method: 'POST',
        body: formData
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            agregarItemAlCarrito(data.producto.nombre, data.producto.precio, form.closest('.item').querySelector('.img-item').src);
            actualizarTotalCarrito();

            // Actualizar el carrito en sessionStorage
            let carrito = JSON.parse(sessionStorage.getItem('carrito')) || [];
            carrito.push(data.producto);
            sessionStorage.setItem('carrito', JSON.stringify(carrito));
        } else {
            alert("Error al agregar el producto al carrito: " + data.message);
        }
    }).catch(error => {
        console.error('Error:', error);
        alert('Error al agregar el producto al carrito.');
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
    var carritoItems = document.getElementsByClassName('carrito-items')[0];
    var carritoRows = carritoItems.getElementsByClassName('carrito-item');
    var total = 0;
    for (var i = 0; i < carritoRows.length; i++) {
        var carritoRow = carritoRows[i];
        var precioElemento = carritoRow.getElementsByClassName('carrito-item-precio')[0];
        var cantidadElemento = carritoRow.getElementsByClassName('carrito-item-cantidad')[0];
        var precio = parseFloat(precioElemento.innerText.replace('$', '').replace(',', '.'));
        var cantidad = cantidadElemento.value;
        total += precio * cantidad;
    }
    total = Math.round(total * 100) / 100;
    document.getElementsByClassName('carrito-total-precio')[0].innerText = '$' + total.toFixed(2);
}

function eliminarItemCarrito(event) {
    var buttonClicked = event.target;
    buttonClicked.closest('.carrito-item').remove();
    actualizarTotalCarrito();
}

function restarCantidad(event) {
    var buttonClicked = event.target;
    var input = buttonClicked.parentElement.getElementsByClassName('carrito-item-cantidad')[0];
    var cantidadActual = parseInt(input.value);
    if (cantidadActual > 1) {
        input.value = cantidadActual - 1;
        actualizarTotalCarrito();
    }
}

function sumarCantidad(event) {
    var buttonClicked = event.target;
    var input = buttonClicked.parentElement.getElementsByClassName('carrito-item-cantidad')[0];
    var cantidadActual = parseInt(input.value);
    input.value = cantidadActual + 1;
    actualizarTotalCarrito();
}

function pagarClicked() {
    let carrito = JSON.parse(sessionStorage.getItem('carrito')) || [];

    fetch('/guardar_pedido', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ carrito: JSON.stringify(carrito) })
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Pedido realizado exitosamente");
            
            // Limpiar el carrito en sessionStorage
            sessionStorage.removeItem('carrito');
            
            // Limpiar la visualización del carrito en la página
            var carritoItems = document.getElementsByClassName('carrito-items')[0];
            while (carritoItems.hasChildNodes()) {
                carritoItems.removeChild(carritoItems.firstChild);
            }
            actualizarTotalCarrito();
        } else {
            console.error("Error al realizar el pedido: ", data.message);
            alert("Error al realizar el pedido: " + data.message);
        }
    }).catch(error => {
        console.error('Error:', error);
        alert('Error al realizar el pedido.');
    });
}

