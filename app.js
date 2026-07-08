// ============================================================
// GAS GUARIBE - app.js
// Lógica completa para gestión de gas comunitaria
// ============================================================

// ------------------- CONFIGURACIÓN INICIAL -------------------
const CONFIG = {
    preciosVenta: {
        pequeño: 3.50,
        mediano: 5.00,
        grande: 7.50
    },
    costosPlanta: {
        pequeño: 2.00,
        mediano: 3.00,
        grande: 4.50
    },
    gastosFijos: {
        combustible: 50,
        peaje: 10,
        viaticos: 30
    }
};

// Lista de comunidades (se puede editar manualmente)
const COMUNIDADES = [
    "El Bachiller", "La Mirandera", "Guaribito", "Los Samanes",
    "Santa Rosa", "Santa Rosa de Lima", "Las Delicias", "Delicias Norte",
    "Sectores Unidos", "Chivirital", "Terrazas de Guaribe", "El Acueducto",
    "San Luis", "Cañicito", "El Centro", "San Pascual", "El Delirio",
    "Caraquita", "El Quizando", "Samán Gacho", "Inavi", "Colinas de Inavi",
    "Aserradero", "19 de Abril", "El Cedro", "Las Aguaditas", "Las Lajas",
    "Uveral", "El Cinco", "Arenita"
];

// ------------------- FUNCIONES DE ALMACENAMIENTO -------------------
function guardarDatos(clave, datos) {
    localStorage.setItem(clave, JSON.stringify(datos));
}

function obtenerDatos(clave) {
    const data = localStorage.getItem(clave);
    return data ? JSON.parse(data) : null;
}

function obtenerOCrear(clave, valorDefecto) {
    const data = localStorage.getItem(clave);
    if (data) {
        try {
            return JSON.parse(data);
        } catch (e) {
            return valorDefecto;
        }
    }
    return valorDefecto;
}

// ------------------- ESTRUCTURA DE DATOS -------------------
function inicializarDatos() {
    if (!localStorage.getItem('recogidas')) {
        guardarDatos('recogidas', []);
    }
    if (!localStorage.getItem('entregas')) {
        guardarDatos('entregas', []);
    }
    if (!localStorage.getItem('ventas')) {
        guardarDatos('ventas', []);
    }
    if (!localStorage.getItem('gastos')) {
        guardarDatos('gastos', []);
    }
    if (!localStorage.getItem('config')) {
        guardarDatos('config', CONFIG);
    }
    if (!localStorage.getItem('cargas')) {
        guardarDatos('cargas', []);
    }
}

// ------------------- RECOGIDAS -------------------
function registrarRecogida(comunidad, pequeños, medianos, grandes, observaciones = '') {
    const recogidas = obtenerOCrear('recogidas', []);
    const nueva = {
        id: Date.now(),
        fecha: new Date().toISOString(),
        comunidad,
        pequeños: parseInt(pequeños) || 0,
        medianos: parseInt(medianos) || 0,
        grandes: parseInt(grandes) || 0,
        observaciones,
        sincronizado: false
    };
    recogidas.push(nueva);
    guardarDatos('recogidas', recogidas);
    return nueva;
}

function obtenerRecogidas() {
    return obtenerOCrear('recogidas', []);
}

function obtenerRecogidasPendientes() {
    const recogidas = obtenerRecogidas();
    const entregas = obtenerEntregas();
    const idsEntregados = entregas.map(e => e.recogidaId);
    return recogidas.filter(r => !idsEntregados.includes(r.id));
}

// ------------------- ENTREGAS -------------------
function registrarEntrega(recogidaId, comunidad, entregados, precios, exonerados, pago, monto) {
    const entregas = obtenerOCrear('entregas', []);
    const recogida = obtenerRecogidas().find(r => r.id === recogidaId);
    if (!recogida) {
        throw new Error('No se encontró la recogida asociada');
    }

    const config = obtenerOCrear('config', CONFIG);
    const costosPlanta = config.costosPlanta || CONFIG.costosPlanta;

    // Calcular costos y ganancias
    const costos = {
        pequeño: (entregados.pequeño || 0) * (costosPlanta.pequeño || 0),
        mediano: (entregados.mediano || 0) * (costosPlanta.mediano || 0),
        grande: (entregados.grande || 0) * (costosPlanta.grande || 0)
    };
    const totalCostoPlanta = costos.pequeño + costos.mediano + costos.grande;

    const ingresos = {
        pequeño: (entregados.pequeño || 0) * (precios.pequeño || 0),
        mediano: (entregados.mediano || 0) * (precios.mediano || 0),
        grande: (entregados.grande || 0) * (precios.grande || 0)
    };
    const totalIngreso = ingresos.pequeño + ingresos.mediano + ingresos.grande;

    // Gastos operativos (se pueden asignar manualmente después)
    const gastosOperativos = obtenerGastosPorCarga(recogidaId);

    const nueva = {
        id: Date.now(),
        recogidaId,
        fecha: new Date().toISOString(),
        comunidad,
        entregados,
        precios,
        exonerados: exonerados || { institucion: '', cantidad: 0 },
        pago,
        monto: parseFloat(monto) || 0,
        costosPlanta: costos,
        totalCostoPlanta,
        ingresos,
        totalIngreso,
        gastosOperativos: gastosOperativos || { combustible: 0, peaje: 0, viaticos: 0, imprevistos: 0 },
        ganancia: totalIngreso - totalCostoPlanta - (gastosOperativos ? gastosOperativos.combustible + gastosOperativos.peaje + gastosOperativos.viaticos + gastosOperativos.imprevistos : 0),
        sincronizado: false
    };
    entregas.push(nueva);
    guardarDatos('entregas', entregas);
    return nueva;
}

function obtenerEntregas() {
    return obtenerOCrear('entregas', []);
}

// ------------------- GASTOS OPERATIVOS POR CARGA -------------------
function registrarGastosCarga(cargaId, combustible, peaje, viaticos, imprevistos) {
    const gastos = obtenerOCrear('gastosCarga', {});
    gastos[cargaId] = {
        combustible: parseFloat(combustible) || 0,
        peaje: parseFloat(peaje) || 0,
        viaticos: parseFloat(viaticos) || 0,
        imprevistos: parseFloat(imprevistos) || 0
    };
    guardarDatos('gastosCarga', gastos);
}

function obtenerGastosPorCarga(cargaId) {
    const gastos = obtenerOCrear('gastosCarga', {});
    return gastos[cargaId] || null;
}

// ------------------- GASTOS GENERALES -------------------
function registrarGastoGeneral(categoria, descripcion, monto, fecha = null) {
    const gastos = obtenerOCrear('gastosGenerales', []);
    gastos.push({
        id: Date.now(),
        fecha: fecha || new Date().toISOString(),
        categoria,
        descripcion,
        monto: parseFloat(monto) || 0
    });
    guardarDatos('gastosGenerales', gastos);
}

function obtenerGastosGenerales() {
    return obtenerOCrear('gastosGenerales', []);
}

// ------------------- VENTAS DE ALMACÉN -------------------
function registrarVentaAlmacen(cliente, pequeños, medianos, grandes, precioUnitario, pago, monto) {
    const ventas = obtenerOCrear('ventas', []);
    const total = (pequeños * precioUnitario.pequeño || 0) + (medianos * precioUnitario.mediano || 0) + (grandes * precioUnitario.grande || 0);
    ventas.push({
        id: Date.now(),
        fecha: new Date().toISOString(),
        cliente,
        pequeños: parseInt(pequeños) || 0,
        medianos: parseInt(medianos) || 0,
        grandes: parseInt(grandes) || 0,
        precioUnitario,
        total,
        pago,
        monto: parseFloat(monto) || 0
    });
    guardarDatos('ventas', ventas);
}

function obtenerVentasAlmacen() {
    return obtenerOCrear('ventas', []);
}

// ------------------- REPORTES -------------------
function generarReporteCarga(recogidaId) {
    const recogida = obtenerRecogidas().find(r => r.id === recogidaId);
    if (!recogida) return null;
    const entrega = obtenerEntregas().find(e => e.recogidaId === recogidaId);
    if (!entrega) return null;

    return {
        recogida,
        entrega,
        resumen: {
            recogidos: {
                pequeños: recogida.pequeños,
                medianos: recogida.medianos,
                grandes: recogida.grandes
            },
            entregados: entrega.entregados,
            exonerados: entrega.exonerados,
            totalIngreso: entrega.totalIngreso,
            totalCostoPlanta: entrega.totalCostoPlanta,
            gastosOperativos: entrega.gastosOperativos,
            ganancia: entrega.ganancia
        }
    };
}

function generarResumenMensual(mes, año) {
    const entregas = obtenerEntregas().filter(e => {
        const f = new Date(e.fecha);
        return f.getMonth() === mes && f.getFullYear() === año;
    });
    const gastosGenerales = obtenerGastosGenerales().filter(g => {
        const f = new Date(g.fecha);
        return f.getMonth() === mes && f.getFullYear() === año;
    });

    let totalIngresos = 0;
    let totalCostosPlanta = 0;
    let totalGastosOperativos = 0;
    let totalGanancia = 0;

    entregas.forEach(e => {
        totalIngresos += e.totalIngreso || 0;
        totalCostosPlanta += e.totalCostoPlanta || 0;
        const op = e.gastosOperativos || { combustible: 0, peaje: 0, viaticos: 0, imprevistos: 0 };
        totalGastosOperativos += op.combustible + op.peaje + op.viaticos + op.imprevistos;
        totalGanancia += e.ganancia || 0;
    });

    const totalGastosGenerales = gastosGenerales.reduce((acc, g) => acc + g.monto, 0);

    return {
        entregas,
        gastosGenerales,
        totalIngresos,
        totalCostosPlanta,
        totalGastosOperativos,
        totalGastosGenerales,
        totalGanancia: totalGanancia - totalGastosGenerales
    };
}

// ------------------- INVENTARIO -------------------
function calcularInventario() {
    const recogidas = obtenerRecogidas();
    const entregas = obtenerEntregas();
    const ventas = obtenerVentasAlmacen();

    // Vacíos en resguardo: recogidas no entregadas
    const idsEntregados = entregas.map(e => e.recogidaId);
    const recogidasPendientes = recogidas.filter(r => !idsEntregados.includes(r.id));

    let vaciosResguardo = { pequeño: 0, mediano: 0, grande: 0 };
    recogidasPendientes.forEach(r => {
        vaciosResguardo.pequeño += r.pequeños || 0;
        vaciosResguardo.mediano += r.medianos || 0;
        vaciosResguardo.grande += r.grandes || 0;
    });

    // Llenos en almacén: entregados no vendidos en almacén
    let llenosAlmacen = { pequeño: 0, mediano: 0, grande: 0 };
    entregas.forEach(e => {
        llenosAlmacen.pequeño += e.entregados.pequeño || 0;
        llenosAlmacen.mediano += e.entregados.mediano || 0;
        llenosAlmacen.grande += e.entregados.grande || 0;
    });
    // Restar ventas de almacén
    ventas.forEach(v => {
        llenosAlmacen.pequeño -= v.pequeños || 0;
        llenosAlmacen.mediano -= v.medianos || 0;
        llenosAlmacen.grande -= v.grandes || 0;
    });

    return {
        vaciosResguardo,
        llenosAlmacen,
        totalVacios: vaciosResguardo.pequeño + vaciosResguardo.mediano + vaciosResguardo.grande,
        totalLlenos: llenosAlmacen.pequeño + llenosAlmacen.mediano + llenosAlmacen.grande
    };
}

// ------------------- ACTUALIZAR DASHBOARD -------------------
function actualizarResumen() {
    const inventario = calcularInventario();
    const entregas = obtenerEntregas();
    const hoy = new Date().toISOString().split('T')[0];
    const entregasHoy = entregas.filter(e => e.fecha.split('T')[0] === hoy);

    document.getElementById('vaciosResguardo').textContent = inventario.totalVacios;
    document.getElementById('llenosAlmacen').textContent = inventario.totalLlenos;
    document.getElementById('entregadosHoy').textContent = entregasHoy.length;

    // En ruta a planta (simulado: recogidas pendientes que han sido enviadas)
    // Por simplicidad, asumimos que las recogidas pendientes son las que están en ruta
    document.getElementById('enRuta').textContent = document.getElementById('vaciosResguardo').textContent;
}

function mostrarUltimaCarga() {
    const recogidas = obtenerRecogidas();
    if (recogidas.length === 0) {
        document.getElementById('ultimaCargaInfo').textContent = 'No hay cargas registradas';
        return;
    }
    const ultima = recogidas[recogidas.length - 1];
    const total = (ultima.pequeños || 0) + (ultima.medianos || 0) + (ultima.grandes || 0);
    document.getElementById('ultimaCargaInfo').textContent = `#${ultima.id} - ${ultima.comunidad} - ${total} cilindros (${ultima.fecha.split('T')[0]})`;
}

// ------------------- EXPORTAR (para usar en otros archivos) -------------------
// Las funciones ya están disponibles globalmente porque las declaramos en el scope global.

// Inicializar datos al cargar
inicializarDatos();
