// ============================================================
// GAS GUARIBE v2.0 - app.js (OPTIMIZADO)
// ============================================================

// ------------------------------------------------------------
// 1. CONFIGURACIÓN INICIAL
// ------------------------------------------------------------

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
    capacidad_camion: 50,
    gastos_generales: { nomina: 0, alquiler: 0, mantenimiento: 0, repuestos: 0, varios: 0 }
};

let datos = {
    comunidades: [...COMUNIDADES_PREDEFINIDAS],
    config: CONFIG_DEFAULT,
    recogidas: [],
    cargas: [],
    entregas: [],
    ventas: [],
    gastos: []
};

// ------------------------------------------------------------
// 2. PERSISTENCIA
// ------------------------------------------------------------

function guardarDatos() {
    localStorage.setItem('gasguaribe_datos_v2', JSON.stringify(datos));
}

function cargarDatos() {
    const saved = localStorage.getItem('gasguaribe_datos_v2');
    if (saved) {
        try {
            datos = JSON.parse(saved);
            // Asegurar propiedades
            if (!datos.config) datos.config = CONFIG_DEFAULT;
            if (!datos.comunidades) datos.comunidades = [...COMUNIDADES_PREDEFINIDAS];
            if (!datos.recogidas) datos.recogidas = [];
            if (!datos.cargas) datos.cargas = [];
            if (!datos.entregas) datos.entregas = [];
            if (!datos.ventas) datos.ventas = [];
            if (!datos.gastos) datos.gastos = [];
            if (!datos.config.capacidad_camion) datos.config.capacidad_camion = 50;
            // Asegurar campos en recogidas
            datos.recogidas = datos.recogidas.map(r => {
                if (!r.enviado) r.enviado = { p: 0, m: 0, g: 0 };
                if (!r.estado) r.estado = 'pendiente';
                return r;
            });
            // Asegurar campos en cargas
            datos.cargas = datos.cargas.map(c => {
                if (!c.estado) c.estado = 'activa';
                return c;
            });
        } catch(e) {
            console.warn('Error al cargar datos, usando default');
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

// ------------------------------------------------------------
// 3. FUNCIONES DE COMUNIDADES Y PLANTAS
// ------------------------------------------------------------

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

function guardarPlantas(plantas) {
    datos.config.plantas = plantas;
    guardarDatos();
}

// ------------------------------------------------------------
// 4. FUNCIONES DE RECOGIDAS
// ------------------------------------------------------------

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

function obtenerSaldoRecogida(recogida) {
    const enviado = recogida.enviado || { p: 0, m: 0, g: 0 };
    return {
        p: recogida.pequenos - enviado.p,
        m: recogida.medianos - enviado.m,
        g: recogida.grandes - enviado.g,
        total: (recogida.pequenos - enviado.p) + (recogida.medianos - enviado.m) + (recogida.grandes - enviado.g)
    };
}

function actualizarEstadoRecogida(recogida) {
    const saldo = obtenerSaldoRecogida(recogida);
    if (saldo.total === 0) {
        recogida.estado = 'completa';
    } else if (recogida.enviado.p === 0 && recogida.enviado.m === 0 && recogida.enviado.g === 0) {
        recogida.estado = 'pendiente';
    } else {
        recogida.estado = 'parcial';
    }
    return recogida;
}

function actualizarRecogida(id, data) {
    const idx = datos.recogidas.findIndex(r => r.id === id);
    if (idx === -1) return null;
    datos.recogidas[idx] = { ...datos.recogidas[idx], ...data };
    actualizarEstadoRecogida(datos.recogidas[idx]);
    guardarDatos();
    return datos.recogidas[idx];
}

function eliminarRecogida(id) {
    datos.recogidas = datos.recogidas.filter(r => r.id !== id);
    guardarDatos();
}

function obtenerTipoClienteRecogida(recogida) {
    if (recogida.tipoCliente) return recogida.tipoCliente;
    const comercios = ['Abasto el Llanero', 'Distribuidora Caridad', 'Queseras'];
    if (comercios.includes(recogida.comunidad)) return 'comercio';
    if (recogida.comunidad === 'Galpón') return 'galpon';
    return 'comunidad';
}

// ------------------------------------------------------------
// 5. FUNCIONES DE CARGAS
// ------------------------------------------------------------

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
        estado: 'activa',
        costos: null,
        gastos: { combustible: 0, peaje: 0, viaticos: 0, imprevistos: 0 }
    };
    datos.cargas.push(carga);

    items.forEach(item => {
        const recogida = datos.recogidas.find(r => r.id === item.recogidaId);
        if (recogida) {
            if (!recogida.enviado) recogida.enviado = { p: 0, m: 0, g: 0 };
            recogida.enviado.p += parseInt(item.pequenos) || 0;
            recogida.enviado.m += parseInt(item.medianos) || 0;
            recogida.enviado.g += parseInt(item.grandes) || 0;
            actualizarEstadoRecogida(recogida);
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
                actualizarEstadoRecogida(recogida);
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

// ------------------------------------------------------------
// 6. FUNCIONES DE PRECIOS Y FINANZAS
// ------------------------------------------------------------

function obtenerPrecioVenta(tipoCliente, plantaId, tamanio) {
    const config = datos.config || {};
    const precios = config.precios_venta || CONFIG_DEFAULT.precios_venta;
    const tipo = precios[tipoCliente] || precios.comunidad;
    return tipo[tamanio] || 0;
}

function obtenerCostoPlanta(plantaId, tamanio) {
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

function calcularTotalEntrega(entrega) {
    const p = entrega.precios || { pequeno: 3.50, mediano: 5.00, grande: 7.50 };
    return (entrega.pequenos * p.pequeno) + (entrega.medianos * p.mediano) + (entrega.grandes * p.grande);
}

function calcularPagoTotal(entrega) {
    return (entrega.pago_efectivo || 0) + (entrega.pago_transferencia || 0) + (entrega.pago_punto_venta || 0);
}

// ------------------------------------------------------------
// 7. FUNCIONES DE ENTREGAS
// ------------------------------------------------------------

function registrarEntrega(comunidad, pequenos, medianos, grandes, precios, pago_efectivo, pago_transferencia, pago_punto_venta, exonerados, planta, fecha, cargaId) {
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
        fecha: fecha || new Date().toISOString(),
        cargaId: cargaId || null,
        estado: 'entregado'
    };
    datos.entregas.push(entrega);
    guardarDatos();
    return entrega;
}

function actualizarEntrega(id, data) {
    const idx = datos.entregas.findIndex(e => e.id === id);
    if (idx === -1) return null;
    datos.entregas[idx] = { ...datos.entregas[idx], ...data };
    guardarDatos();
    return datos.entregas[idx];
}

function eliminarEntrega(id) {
    datos.entregas = datos.entregas.filter(e => e.id !== id);
    guardarDatos();
}

// ------------------------------------------------------------
// 8. FUNCIONES DE VENTAS Y GASTOS
// ------------------------------------------------------------

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

function eliminarVenta(id) {
    datos.ventas = datos.ventas.filter(v => v.id !== id);
    guardarDatos();
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

function eliminarGasto(id) {
    datos.gastos = datos.gastos.filter(g => g.id !== id);
    guardarDatos();
}

// ------------------------------------------------------------
// 9. DESHACER
// ------------------------------------------------------------

function setUltimo(tipo, id) {
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
        case 'entrega':
            eliminarEntrega(id);
            eliminado = true;
            break;
        case 'venta':
            eliminarVenta(id);
            eliminado = true;
            break;
        case 'gasto':
            eliminarGasto(id);
            eliminado = true;
            break;
        case 'carga':
            eliminarCarga(id);
            eliminado = true;
            break;
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

// ------------------------------------------------------------
// 10. DASHBOARD
// ------------------------------------------------------------

function actualizarDashboard() {
    cargarDatos();
    const recogidas = datos.recogidas || [];
    const cargas = datos.cargas || [];
    const entregas = datos.entregas || [];

    const pendientes = recogidas.filter(r => r.estado === 'pendiente');
    const parciales = recogidas.filter(r => r.estado === 'parcial');
    const activas = cargas.filter(c => c.estado === 'activa');

    document.getElementById('recogidasPendientes').textContent = pendientes.length;
    document.getElementById('recogidasParciales').textContent = parciales.length;
    document.getElementById('cargasActivas').textContent = activas.length;

    const hoy = new Date().toDateString();
    const entregasHoy = entregas.filter(e => new Date(e.fecha).toDateString() === hoy);
    const totalEntregadosHoy = entregasHoy.reduce((sum, e) => sum + e.pequenos + e.medianos + e.grandes, 0);
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

// ------------------------------------------------------------
// 11. INICIALIZACIÓN
// ------------------------------------------------------------

cargarDatos();

// Exportar funciones al ámbito global
window.obtenerComunidades = obtenerComunidades;
window.agregarComunidad = agregarComunidad;
window.obtenerPlantas = obtenerPlantas;
window.obtenerPlantaPorId = obtenerPlantaPorId;
window.obtenerNombrePlanta = obtenerNombrePlanta;
window.guardarPlantas = guardarPlantas;
window.registrarRecogida = registrarRecogida;
window.obtenerSaldoRecogida = obtenerSaldoRecogida;
window.actualizarRecogida = actualizarRecogida;
window.eliminarRecogida = eliminarRecogida;
window.obtenerTipoClienteRecogida = obtenerTipoClienteRecogida;
window.crearCarga = crearCarga;
window.actualizarCarga = actualizarCarga;
window.eliminarCarga = eliminarCarga;
window.obtenerResumenCarga = obtenerResumenCarga;
window.registrarEntrega = registrarEntrega;
window.actualizarEntrega = actualizarEntrega;
window.eliminarEntrega = eliminarEntrega;
window.registrarVenta = registrarVenta;
window.eliminarVenta = eliminarVenta;
window.registrarGasto = registrarGasto;
window.eliminarGasto = eliminarGasto;
window.obtenerPrecioVenta = obtenerPrecioVenta;
window.obtenerCostoPlanta = obtenerCostoPlanta;
window.calcularGananciaEstimada = calcularGananciaEstimada;
window.calcularTotalEntrega = calcularTotalEntrega;
window.calcularPagoTotal = calcularPagoTotal;
window.setUltimo = setUltimo;
window.deshacerUltimo = deshacerUltimo;
window.actualizarDashboard = actualizarDashboard;
window.datos = datos;
window.guardarDatos = guardarDatos;
window.cargarDatos = cargarDatos;
