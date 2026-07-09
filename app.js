// app.js - Versión definitiva con soporte para comunidades, plantas y cargas

// ============================================================
// DATOS Y CONFIGURACIÓN INICIAL
// ============================================================

const COMUNIDADES_PREDEFINIDAS = [
    "El Bachiller", "La Mirandera", "Guaribito", "Los Samanes",
    "Santa Rosa", "Santa Rosa de Lima", "Las Delicias", "Delicias Norte",
    "Sectores Unidos", "Chivirital", "Terrazas de Guaribe", "El Acueducto",
    "San Luis", "Cañicito", "El Centro", "San Pascual", "El Delirio",
    "Caraquita", "El Quizando", "Samán Gacho", "Inavi", "Colinas de Inavi",
    "Aserradero", "19 de Abril", "El Cedro", "Las Aguaditas", "Las Lajas",
    "Uveral", "El Cinco", "Arenita",
    "Abasto el Llanero", "Distribuidora Caridad", "Queseras", "Galpón"
];

const PLANTAS_PREDEFINIDAS = [
    { id: 'planta1', nombre: 'Puerto La Cruz', costos: { pequeno: 2.00, mediano: 3.00, grande: 4.50 }, gastos: { combustible: 50, peaje: 10, viaticos: 30 } },
    { id: 'planta2', nombre: 'Altagracia', costos: { pequeno: 2.20, mediano: 3.30, grande: 4.80 }, gastos: { combustible: 60, peaje: 15, viaticos: 35 } },
    { id: 'planta3', nombre: 'Valle de la Pascua', costos: { pequeno: 2.50, mediano: 3.80, grande: 5.20 }, gastos: { combustible: 70, peaje: 20, viaticos: 40 } }
];

const CONFIG_DEFAULT = {
    plantas: PLANTAS_PREDEFINIDAS,
    precios_venta: {
        comunidad: { pequeno: 3.50, mediano: 5.00, grande: 7.50 },
        comercio: { pequeno: 3.00, mediano: 4.50, grande: 6.50 },
        galpon: { pequeno: 2.50, mediano: 3.80, grande: 5.20 }
    },
    capacidad_camion: 50
};

let datos = {
    comunidades: [...COMUNIDADES_PREDEFINIDAS],
    config: CONFIG_DEFAULT,
    recogidas: [],      // { id, comunidad, planta, pequenos, medianos, grandes, fecha, observaciones, estado: 'pendiente'|'parcial'|'completa', enviado: {p,m,g} }
    cargas: [],         // { id, planta, fecha, items: [{ recogidaId, pequenos, medianos, grandes }], estado: 'activa'|'completada' }
    entregas: [],
    ventas: [],
    gastos: []
};

// ============================================================
// FUNCIONES DE PERSISTENCIA (usando localStorage)
// ============================================================

function guardarDatos() {
    localStorage.setItem('gasguaribe_datos_v2', JSON.stringify(datos));
}

function cargarDatos() {
    const saved = localStorage.getItem('gasguaribe_datos_v2');
    if (saved) {
        try {
            datos = JSON.parse(saved);
            // Asegurar propiedades nuevas
            if (!datos.config) datos.config = CONFIG_DEFAULT;
            if (!datos.comunidades) datos.comunidades = [...COMUNIDADES_PREDEFINIDAS];
            if (!datos.recogidas) datos.recogidas = [];
            if (!datos.cargas) datos.cargas = [];
            if (!datos.entregas) datos.entregas = [];
            if (!datos.ventas) datos.ventas = [];
            if (!datos.gastos) datos.gastos = [];
            if (!datos.config.capacidad_camion) datos.config.capacidad_camion = 50;
            datos.recogidas = datos.recogidas.map(r => {
                if (!r.estado) r.estado = 'pendiente';
                if (!r.enviado) r.enviado = { p: 0, m: 0, g: 0 };
                return r;
            });
        } catch(e) {
            resetearDatos();
        }
    } else {
        resetearDatos();
    }
}

function resetearDatos() {
    datos = {
        comunidades: [...COMUNIDADES_PREDEFINIDAS],
        config: CONFIG_DEFAULT,
        recogidas: [],
        cargas: [],
        entregas: [],
        ventas: [],
        gastos: []
    };
    guardarDatos();
}

// ============================================================
// FUNCIONES PARA COMUNIDADES
// ============================================================

function obtenerComunidades() {
    return datos.comunidades || COMUNIDADES_PREDEFINIDAS;
}

function agregarComunidad(nombre) {
    if (!nombre || nombre.trim() === '') return false;
    const limpio = nombre.trim();
    if (!datos.comunidades.includes(limpio)) {
        datos.comunidades.push(limpio);
        guardarDatos();
        return true;
    }
    return false;
}

// ============================================================
// FUNCIONES PARA PLANTAS
// ============================================================

function obtenerPlantas() {
    return datos.config.plantas || PLANTAS_PREDEFINIDAS;
}

function obtenerPlantaPorId(id) {
    return (datos.config.plantas || []).find(p => p.id === id);
}

function obtenerNombrePlanta(plantaId) {
    const plantas = obtenerPlantas();
    const planta = plantas.find(p => p.id === plantaId);
    return planta ? planta.nombre : (plantaId || 'No especificada');
}

// ============================================================
// FUNCIONES PARA RECOGIDAS
// ============================================================

function registrarRecogida(comunidad, planta, pequenos, medianos, grandes, fecha, observaciones) {
    const recogida = {
        id: Date.now(),
        comunidad: comunidad.trim(),
        planta: planta || '',
        pequenos: parseInt(pequenos) || 0,
        medianos: parseInt(medianos) || 0,
        grandes: parseInt(grandes) || 0,
        fecha: fecha || new Date().toISOString(),
        observaciones: observaciones || '',
        estado: 'pendiente',
        enviado: { p: 0, m: 0, g: 0 }
    };
    datos.recogidas.push(recogida);
    guardarDatos();
    return recogida;
}

function actualizarRecogida(id, data) {
    const idx = datos.recogidas.findIndex(r => r.id === id);
    if (idx === -1) return null;
    datos.recogidas[idx] = { ...datos.recogidas[idx], ...data };
    const r = datos.recogidas[idx];
    const totalRecogido = r.pequenos + r.medianos + r.grandes;
    const totalEnviado = (r.enviado?.p || 0) + (r.enviado?.m || 0) + (r.enviado?.g || 0);
    r.estado = totalEnviado === 0 ? 'pendiente' : (totalEnviado >= totalRecogido ? 'completa' : 'parcial');
    guardarDatos();
    return datos.recogidas[idx];
}

function eliminarRecogida(id) {
    datos.recogidas = datos.recogidas.filter(r => r.id !== id);
    guardarDatos();
}

function obtenerSaldoRecogida(recogida) {
    return {
        p: recogida.pequenos - (recogida.enviado?.p || 0),
        m: recogida.medianos - (recogida.enviado?.m || 0),
        g: recogida.grandes - (recogida.enviado?.g || 0),
        total: (recogida.pequenos + recogida.medianos + recogida.grandes) - ((recogida.enviado?.p || 0) + (recogida.enviado?.m || 0) + (recogida.enviado?.g || 0))
    };
}

// ============================================================
// FUNCIONES PARA CARGAS A PLANTA
// ============================================================

function crearCarga(planta, fecha, items) {
    const carga = {
        id: Date.now(),
        planta: planta || '',
        fecha: fecha || new Date().toISOString(),
        items: items.map(item => ({
            recogidaId: item.recogidaId,
            pequenos: parseInt(item.pequenos) || 0,
            medianos: parseInt(item.medianos) || 0,
            grandes: parseInt(item.grandes) || 0
        })),
        estado: 'activa'
    };
    datos.cargas.push(carga);

    // Actualizar recogidas (sumar lo enviado)
    items.forEach(item => {
        const recogida = datos.recogidas.find(r => r.id === item.recogidaId);
        if (recogida) {
            if (!recogida.enviado) recogida.enviado = { p: 0, m: 0, g: 0 };
            recogida.enviado.p += parseInt(item.pequenos) || 0;
            recogida.enviado.m += parseInt(item.medianos) || 0;
            recogida.enviado.g += parseInt(item.grandes) || 0;
            const totalRecogido = recogida.pequenos + recogida.medianos + recogida.grandes;
            const totalEnviado = recogida.enviado.p + recogida.enviado.m + recogida.enviado.g;
            recogida.estado = totalEnviado === 0 ? 'pendiente' : (totalEnviado >= totalRecogido ? 'completa' : 'parcial');
        }
    });
    guardarDatos();
    return carga;
}

function actualizarCarga(id, data) {
    const idx = datos.cargas.findIndex(c => c.id === id);
    if (idx === -1) return null;
    datos.cargas[idx] = { ...datos.cargas[idx], ...data };
    guardarDatos();
    return datos.cargas[idx];
}

function eliminarCarga(id) {
    const carga = datos.cargas.find(c => c.id === id);
    if (carga) {
        carga.items.forEach(item => {
            const recogida = datos.recogidas.find(r => r.id === item.recogidaId);
            if (recogida && recogida.enviado) {
                recogida.enviado.p -= item.pequenos || 0;
                recogida.enviado.m -= item.medianos || 0;
                recogida.enviado.g -= item.grandes || 0;
                const totalRecogido = recogida.pequenos + recogida.medianos + recogida.grandes;
                const totalEnviado = recogida.enviado.p + recogida.enviado.m + recogida.enviado.g;
                recogida.estado = totalEnviado === 0 ? 'pendiente' : (totalEnviado >= totalRecogido ? 'completa' : 'parcial');
            }
        });
    }
    datos.cargas = datos.cargas.filter(c => c.id !== id);
    guardarDatos();
}

function obtenerResumenCarga(cargaId) {
    const carga = datos.cargas.find(c => c.id === cargaId);
    if (!carga) return null;
    const resumen = {
        totalP: 0,
        totalM: 0,
        totalG: 0,
        comunidades: []
    };
    carga.items.forEach(item => {
        const recogida = datos.recogidas.find(r => r.id === item.recogidaId);
        if (recogida) {
            resumen.comunidades.push({
                comunidad: recogida.comunidad,
                pequenos: item.pequenos,
                medianos: item.medianos,
                grandes: item.grandes
            });
            resumen.totalP += item.pequenos;
            resumen.totalM += item.medianos;
            resumen.totalG += item.grandes;
        }
    });
    return resumen;
}

// ============================================================
// FUNCIONES DE PRECIOS Y COSTOS
// ============================================================

function obtenerPrecioVenta(tipoCliente, tamanio) {
    const config = datos.config || {};
    const precios = config.precios_venta || CONFIG_DEFAULT.precios_venta;
    const tipo = precios[tipoCliente] || precios.comunidad;
    return tipo[tamanio] || 0;
}

function obtenerCostoPlanta(plantaId, tamanio) {
    const plantas = obtenerPlantas();
    const planta = plantas.find(p => p.id === plantaId);
    if (!planta) return 0;
    return planta.costos[tamanio] || 0;
}

function obtenerTipoClienteRecogida(recogida) {
    if (recogida.tipoCliente) return recogida.tipoCliente;
    const comercios = ['Abasto el Llanero', 'Distribuidora Caridad', 'Queseras'];
    if (comercios.includes(recogida.comunidad)) return 'comercio';
    if (recogida.comunidad === 'Galpón') return 'galpon';
    return 'comunidad';
}

function calcularGananciaEstimada(items, plantaId) {
    let totalIngreso = 0;
    let totalCosto = 0;
    items.forEach(item => {
        const tipoCliente = item.tipoCliente || 'comunidad';
        const precios = {
            pequeno: obtenerPrecioVenta(tipoCliente, 'pequeno'),
            mediano: obtenerPrecioVenta(tipoCliente, 'mediano'),
            grande: obtenerPrecioVenta(tipoCliente, 'grande')
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

// ============================================================
// FUNCIONES PARA ENTREGAS, VENTAS Y GASTOS (básicas)
// ============================================================

function registrarEntrega(comunidad, pequenos, medianos, grandes, precios, pago_efectivo, pago_transferencia, pago_punto_venta, exonerados, planta, fecha) {
    const entrega = {
        id: Date.now(),
        comunidad: comunidad.trim(),
        pequenos: parseInt(pequenos) || 0,
        medianos: parseInt(medianos) || 0,
        grandes: parseInt(grandes) || 0,
        precios: precios || { pequeno: 3.50, mediano: 5.00, grande: 7.50 },
        pago_efectivo: parseFloat(pago_efectivo) || 0,
        pago_transferencia: parseFloat(pago_transferencia) || 0,
        pago_punto_venta: parseFloat(pago_punto_venta) || 0,
        exonerados: exonerados || [],
        planta: planta || '',
        fecha: fecha || new Date().toISOString()
    };
    datos.entregas.push(entrega);
    guardarDatos();
    return entrega;
}

function registrarVenta(cliente, pequenos, medianos, grandes, precio_unitario, fecha) {
    const venta = {
        id: Date.now(),
        cliente: cliente.trim(),
        pequenos: parseInt(pequenos) || 0,
        medianos: parseInt(medianos) || 0,
        grandes: parseInt(grandes) || 0,
        precio_unitario: precio_unitario || { pequeno: 3.50, mediano: 5.00, grande: 7.50 },
        fecha: fecha || new Date().toISOString()
    };
    datos.ventas.push(venta);
    guardarDatos();
    return venta;
}

function registrarGasto(categoria, descripcion, monto, planta, fecha) {
    const gasto = {
        id: Date.now(),
        categoria: categoria.trim(),
        descripcion: descripcion || categoria,
        monto: parseFloat(monto) || 0,
        planta: planta || '',
        fecha: fecha || new Date().toISOString()
    };
    datos.gastos.push(gasto);
    guardarDatos();
    return gasto;
}

// ============================================================
// FUNCIONES DE DESHACER (para "último registro")
// ============================================================

let ultimoId = null;
let ultimoTipo = null;

function setUltimo(tipo, id) {
    ultimoTipo = tipo;
    ultimoId = id;
    sessionStorage.setItem('ultimo_tipo', tipo);
    sessionStorage.setItem('ultimo_id', id);
}

function getUltimo() {
    return {
        tipo: sessionStorage.getItem('ultimo_tipo'),
        id: parseInt(sessionStorage.getItem('ultimo_id'))
    };
}

function deshacerUltimo() {
    const { tipo, id } = getUltimo();
    if (!tipo || !id) return false;
    let eliminado = false;
    switch(tipo) {
        case 'recogida':
            eliminarRecogida(id);
            eliminado = true;
            break;
        case 'carga':
            eliminarCarga(id);
            eliminado = true;
            break;
        // Aquí se pueden añadir otros tipos (entrega, venta, gasto)
        default:
            return false;
    }
    if (eliminado) {
        sessionStorage.removeItem('ultimo_tipo');
        sessionStorage.removeItem('ultimo_id');
        return true;
    }
    return false;
}

// ============================================================
// FUNCIONES DE UTILIDAD PARA EL DASHBOARD
// ============================================================

function actualizarDashboard() {
    // Esta función se llama desde index.html
    cargarDatos();
    const recogidas = datos.recogidas || [];
    const cargas = datos.cargas || [];
    const entregas = datos.entregas || [];

    const pendientes = recogidas.filter(r => r.estado === 'pendiente');
    const parciales = recogidas.filter(r => r.estado === 'parcial');
    const activas = cargas.filter(c => c.estado === 'activa');
    const hoy = new Date().toDateString();
    const entregasHoy = entregas.filter(e => new Date(e.fecha).toDateString() === hoy);
    const totalEntregadosHoy = entregasHoy.reduce((sum, e) => sum + e.pequenos + e.medianos + e.grandes, 0);

    document.getElementById('recogidasPendientes').textContent = pendientes.length;
    document.getElementById('recogidasParciales').textContent = parciales.length;
    document.getElementById('cargasActivas').textContent = activas.length;
    document.getElementById('entregasHoy').textContent = totalEntregadosHoy;

    let totalPendiente = 0;
    recogidas.forEach(r => {
        if (r.estado !== 'completa') {
            const saldo = obtenerSaldoRecogida(r);
            totalPendiente += saldo.total;
        }
    });
    document.getElementById('totalPendientes').textContent = totalPendiente;
}

// ============================================================
// INICIALIZACIÓN
// ============================================================

cargarDatos();

// Exponer funciones al ámbito global para usar desde HTML
window.obtenerComunidades = obtenerComunidades;
window.agregarComunidad = agregarComunidad;
window.obtenerPlantas = obtenerPlantas;
window.obtenerPlantaPorId = obtenerPlantaPorId;
window.obtenerNombrePlanta = obtenerNombrePlanta;
window.registrarRecogida = registrarRecogida;
window.actualizarRecogida = actualizarRecogida;
window.eliminarRecogida = eliminarRecogida;
window.obtenerSaldoRecogida = obtenerSaldoRecogida;
window.crearCarga = crearCarga;
window.actualizarCarga = actualizarCarga;
window.eliminarCarga = eliminarCarga;
window.obtenerResumenCarga = obtenerResumenCarga;
window.obtenerTipoClienteRecogida = obtenerTipoClienteRecogida;
window.calcularGananciaEstimada = calcularGananciaEstimada;
window.obtenerPrecioVenta = obtenerPrecioVenta;
window.obtenerCostoPlanta = obtenerCostoPlanta;
window.setUltimo = setUltimo;
window.deshacerUltimo = deshacerUltimo;
window.actualizarDashboard = actualizarDashboard;
window.datos = datos;
window.guardarDatos = guardarDatos;
window.cargarDatos = cargarDatos;
