// ============================================================
// GAS GUARIBE v3.0 - app.js
// Lógica simplificada y robusta
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
    { id: 'planta1', nombre: 'Puerto La Cruz' },
    { id: 'planta2', nombre: 'Altagracia' },
    { id: 'planta3', nombre: 'Valle de la Pascua' }
];

const CONFIG_DEFAULT = {
    plantas: PLANTAS_PREDEFINIDAS,
    capacidad_camion: 50
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

// Persistencia
function guardarDatos() {
    localStorage.setItem('gasguaribe_datos_v2', JSON.stringify(datos));
}

function cargarDatos() {
    const saved = localStorage.getItem('gasguaribe_datos_v2');
    if (saved) {
        try {
            datos = JSON.parse(saved);
            if (!datos.config) datos.config = CONFIG_DEFAULT;
            if (!datos.comunidades) datos.comunidades = [...COMUNIDADES_PREDEFINIDAS];
            if (!datos.recogidas) datos.recogidas = [];
            if (!datos.cargas) datos.cargas = [];
            if (!datos.entregas) datos.entregas = [];
            if (!datos.ventas) datos.ventas = [];
            if (!datos.gastos) datos.gastos = [];
            datos.recogidas = datos.recogidas.map(r => {
                if (!r.estado) r.estado = 'pendiente';
                if (!r.enviado) r.enviado = { p: 0, m: 0, g: 0 };
                if (!r.exonerados_planificados) r.exonerados_planificados = [];
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

// Comunidades
function obtenerComunidades() { return datos.comunidades || COMUNIDADES_PREDEFINIDAS; }
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

// Plantas
function obtenerPlantas() { return datos.config.plantas || PLANTAS_PREDEFINIDAS; }
function obtenerNombrePlanta(id) {
    const plantas = obtenerPlantas();
    const p = plantas.find(p => p.id === id);
    return p ? p.nombre : (id || 'No especificada');
}

// Recogidas
function registrarRecogida(comunidad, planta, pequenos, medianos, grandes, fecha, observaciones, exonerados_planificados) {
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
        enviado: { p: 0, m: 0, g: 0 },
        exonerados_planificados: exonerados_planificados || []
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

// Cargas
function crearCarga(planta, fecha, items) {
    const carga = {
        id: Date.now(),
        planta: planta || '',
        fecha: fecha || new Date().toISOString(),
        items: items.map(item => ({
            recogidaId: item.recogidaId,
            pequenos: parseInt(item.pequenos) || 0,
            medianos: parseInt(item.medianos) || 0,
            grandes: parseInt(item.grandes) || 0,
            exonerados: (item.exonerados || []).map(ex => ({
                destino: ex.destino || 'comunidad',
                institucion: ex.institucion || '',
                pequenos: parseInt(ex.pequenos) || 0,
                medianos: parseInt(ex.medianos) || 0,
                grandes: parseInt(ex.grandes) || 0
            }))
        })),
        estado: 'activa'
    };
    datos.cargas.push(carga);

    items.forEach(item => {
        const recogida = datos.recogidas.find(r => r.id === item.recogidaId);
        if (recogida) {
            if (!recogida.enviado) recogida.enviado = { p: 0, m: 0, g: 0 };
            recogida.enviado.p += parseInt(item.pequenos) || 0;
            recogida.enviado.m += parseInt(item.medianos) || 0;
            recogida.enviado.g += parseInt(item.grandes) || 0;
        }
    });
    guardarDatos();
    return carga;
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
            }
        });
    }
    datos.cargas = datos.cargas.filter(c => c.id !== id);
    guardarDatos();
}

// Entregas
function registrarEntrega(comunidad, pequenos, medianos, grandes, pago_efectivo, pago_transferencia, pago_punto, exonerados, fecha) {
    const entrega = {
        id: Date.now(),
        comunidad: comunidad.trim(),
        pequenos: parseInt(pequenos) || 0,
        medianos: parseInt(medianos) || 0,
        grandes: parseInt(grandes) || 0,
        pago_efectivo: parseFloat(pago_efectivo) || 0,
        pago_transferencia: parseFloat(pago_transferencia) || 0,
        pago_punto: parseFloat(pago_punto) || 0,
        exonerados: exonerados || [],
        fecha: fecha || new Date().toISOString()
    };
    datos.entregas.push(entrega);
    guardarDatos();
    return entrega;
}

// Ventas
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

// Gastos
function registrarGasto(categoria, descripcion, monto, fecha) {
    const gasto = {
        id: Date.now(),
        categoria: categoria.trim(),
        descripcion: descripcion || categoria,
        monto: parseFloat(monto) || 0,
        fecha: fecha || new Date().toISOString()
    };
    datos.gastos.push(gasto);
    guardarDatos();
    return gasto;
}

// Inicializar
cargarDatos();

// Exportar globalmente
window.obtenerComunidades = obtenerComunidades;
window.agregarComunidad = agregarComunidad;
window.obtenerPlantas = obtenerPlantas;
window.obtenerNombrePlanta = obtenerNombrePlanta;
window.registrarRecogida = registrarRecogida;
window.obtenerSaldoRecogida = obtenerSaldoRecogida;
window.crearCarga = crearCarga;
window.eliminarCarga = eliminarCarga;
window.registrarEntrega = registrarEntrega;
window.registrarVenta = registrarVenta;
window.registrarGasto = registrarGasto;
window.guardarDatos = guardarDatos;
window.cargarDatos = cargarDatos;
window.datos = datos;
