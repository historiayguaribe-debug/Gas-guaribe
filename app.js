// ============================================================
// 13. FUNCIONES DE PRECIOS POR TIPO DE CLIENTE
// ============================================================

function obtenerPrecioVenta(tipoCliente, plantaId, tamanio) {
    const datos = obtenerDatos();
    const config = datos.config || {};
    const precios = config.precios_venta || { comunidad: { pequeno: 3.50, mediano: 5.00, grande: 7.50 }, comercio: { pequeno: 3.00, mediano: 4.50, grande: 6.50 }, galpon: { pequeno: 2.50, mediano: 3.80, grande: 5.20 } };
    // Si no existe el tipo, usar el de comunidad
    const tipo = precios[tipoCliente] || precios.comunidad;
    return tipo[tamanio] || 0;
}

function obtenerCostoPlanta(plantaId, tamanio) {
    const datos = obtenerDatos();
    const plantas = datos.config.plantas || PLANTAS_PREDEFINIDAS;
    const planta = plantas.find(p => p.id === plantaId);
    if (!planta) return 0;
    return planta.costos[tamanio] || 0;
}

function calcularGananciaEstimada(items, plantaId) {
    let totalIngreso = 0;
    let totalCosto = 0;
    items.forEach(item => {
        const tipoCliente = item.tipoCliente || 'comunidad';
        const precios = {
            pequeno: obtenerPrecioVenta(tipoCliente, plantaId, 'pequeno'),
            mediano: obtenerPrecioVenta(tipoCliente, plantaId, 'mediano'),
            grande: obtenerPrecioVenta(tipoCliente, plantaId, 'grande')
        };
        const costos = {
            pequeno: obtenerCostoPlanta(plantaId, 'pequeno'),
            mediano: obtenerCostoPlanta(plantaId, 'mediano'),
            grande: obtenerCostoPlanta(plantaId, 'grande')
        };
        totalIngreso += (item.pequenos * precios.pequeno) + (item.medianos * precios.mediano) + (item.grandes * precios.grande);
        totalCosto += (item.pequenos * costos.pequeno) + (item.medianos * costos.mediano) + (item.grandes * costos.grande);
    });
    return { ingreso: totalIngreso, costo: totalCosto, ganancia: totalIngreso - totalCosto };
}

// Función para obtener el tipo de cliente de una recogida
function obtenerTipoClienteRecogida(recogida) {
    // Si la recogida tiene un campo 'tipoCliente' usarlo, sino inferir
    if (recogida.tipoCliente) return recogida.tipoCliente;
    // Si la comunidad está en la lista de comercios, es comercio
    const comercios = ['Abasto el Llanero', 'Distribuidora Caridad', 'Queseras'];
    if (comercios.includes(recogida.comunidad)) return 'comercio';
    if (recogida.comunidad === 'Galpón') return 'galpon';
    return 'comunidad';
}
