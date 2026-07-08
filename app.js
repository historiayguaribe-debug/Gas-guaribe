// app.js - GAS GUARIBE v2.0

// ============================================================
// 1. CONFIGURACIÓN INICIAL Y DATOS POR DEFECTO
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
    precios_venta: { pequeno: 3.50, mediano: 5.00, grande: 7.50 },
    gastos_generales: { nomina: 0, alquiler: 0, mantenimiento: 0, repuestos: 0, varios: 0 }
};

let datos = {
    comunidades: [...COMUNIDADES_PREDEFINIDAS],
    config: CONFIG_DEFAULT,
    recogidas: [],
    entregas: [],
    ventas: [],
    gastos: []
};

// ============================================================
// 2. FUNCIONES DE PERSISTENCIA
// ============================================================

function guardarDatos() {
    localStorage.setItem('gasguaribe_datos', JSON.stringify(datos));
}

function cargarDatos() {
    const saved = localStorage.getItem('gasguaribe_datos');
    if (saved) {
        try {
            datos = JSON.parse(saved);
            // Asegurar que existan las propiedades nuevas
            if (!datos.config) datos.config = CONFIG_DEFAULT;
            if (!datos.comunidades) datos.comunidades = [...COMUNIDADES_PREDEFINIDAS];
            if (!datos.recogidas) datos.recogidas = [];
            if (!datos.entregas) datos.entregas = [];
            if (!datos.ventas) datos.ventas = [];
            if (!datos.gastos) datos.gastos = [];
        } catch(e) {
            console.warn('Error al cargar datos, usando default');
            datos = { comunidades: [...COMUNIDADES_PREDEFINIDAS], config: CONFIG_DEFAULT, recogidas: [], entregas: [], ventas: [], gastos: [] };
        }
    }
    // Si no hay plantas configuradas, usar las predeterminadas
    if (!datos.config.plantas || datos.config.plantas.length === 0) {
        datos.config.plantas = PLANTAS_PREDEFINIDAS;
        guardarDatos();
    }
}

function resetDatos() {
    localStorage.removeItem('gasguaribe_datos');
    datos = { comunidades: [...COMUNIDADES_PREDEFINIDAS], config: CONFIG_DEFAULT, recogidas: [], entregas: [], ventas: [], gastos: [] };
    guardarDatos();
}

// ============================================================
// 3. FUNCIONES DE NEGOCIO
// ============================================================

// ---- COMUNIDADES ----
function obtenerComunidades() {
    return datos.comunidades || COMUNIDADES_PREDEFINIDAS;
}

function agregarComunidad(nombre) {
    if (!nombre || nombre.trim() === '') return false;
    const nombreLimpio = nombre.trim();
    if (!datos.comunidades.includes(nombreLimpio)) {
        datos.comunidades.push(nombreLimpio);
        guardarDatos();
        return true;
    }
    return false;
}

// ---- PLANTAS ----
function obtenerPlantas() {
    return datos.config.plantas || PLANTAS_PREDEFINIDAS;
}

function obtenerPlantaPorId(id) {
    return (datos.config.plantas || []).find(p => p.id === id);
}

function guardarPlantas(plantas) {
    datos.config.plantas = plantas;
    guardarDatos();
}

// ---- RECOGIDAS ----
function registrarRecogida(comunidad, pequenos, medianos, grandes, observaciones, planta, fecha) {
    const recogida = {
        id: Date.now(),
        comunidad: comunidad.trim(),
        pequenos: parseInt(pequenos) || 0,
        medianos: parseInt(medianos) || 0,
        grandes: parseInt(grandes) || 0,
        fecha: fecha || new Date().toISOString(),
        observaciones: observaciones || '',
        planta: planta || '',
        estado: 'recogido'
    };
    datos.recogidas.push(recogida);
    guardarDatos();
    return recogida;
}

function actualizarRecogida(id, data) {
    const idx = datos.recogidas.findIndex(r => r.id === id);
    if (idx === -1) return null;
    datos.recogidas[idx] = { ...datos.recogidas[idx], ...data };
    guardarDatos();
    return datos.recogidas[idx];
}

function eliminarRecogida(id) {
    datos.recogidas = datos.recogidas.filter(r => r.id !== id);
    guardarDatos();
}

// ---- ENTREGAS ----
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
        exonerados: exonerados || [], // array de { tipo, institucion, pequenos, medianos, grandes, costo }
        planta: planta || '',
        fecha: fecha || new Date().toISOString(),
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

// ---- VENTAS ----
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

// ---- GASTOS ----
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

// ---- ÚLTIMO REGISTRO (para deshacer) ----
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
// 4. FUNCIONES DE REPORTES Y CÁLCULOS
// ============================================================

function calcularTotalEntrega(entrega) {
    const p = entrega.precios || { pequeno: 3.50, mediano: 5.00, grande: 7.50 };
    return (entrega.pequenos * p.pequeno) + (entrega.medianos * p.mediano) + (entrega.grandes * p.grande);
}

function calcularPagoTotal(entrega) {
    return (entrega.pago_efectivo || 0) + (entrega.pago_transferencia || 0) + (entrega.pago_punto_venta || 0);
}

function calcularCostoExonerados(exonerados, plantaCostos) {
    // plantaCostos: { pequeno, mediano, grande }
    let total = 0;
    exonerados.forEach(ex => {
        total += (ex.pequenos * (plantaCostos.pequeno || 0)) +
                 (ex.medianos * (plantaCostos.mediano || 0)) +
                 (ex.grandes * (plantaCostos.grande || 0));
    });
    return total;
}

function obtenerPlantasMap() {
    const plantas = datos.config.plantas || PLANTAS_PREDEFINIDAS;
    const map = {};
    plantas.forEach(p => {
        map[p.id] = p;
    });
    return map;
}

// ============================================================
// 5. INICIALIZACIÓN
// ============================================================

cargarDatos();
// Si no hay datos, guardar default
if (!localStorage.getItem('gasguaribe_datos')) {
    guardarDatos();
}

// ============================================================
// 6. FUNCIONES PARA EL DASHBOARD (se usan en index.html)
// ============================================================

function actualizarDashboard() {
    cargarDatos();
    const recogidas = datos.recogidas || [];
    const entregas = datos.entregas || [];
    
    let totalRecogidos = { p:0, m:0, g:0 };
    let totalEntregados = { p:0, m:0, g:0 };
    
    recogidas.forEach(r => {
        totalRecogidos.p += r.pequenos || 0;
        totalRecogidos.m += r.medianos || 0;
        totalRecogidos.g += r.grandes || 0;
    });
    entregas.forEach(e => {
        totalEntregados.p += e.pequenos || 0;
        totalEntregados.m += e.medianos || 0;
        totalEntregados.g += e.grandes || 0;
    });
    
    const vacios = {
        p: totalRecogidos.p - totalEntregados.p,
        m: totalRecogidos.m - totalEntregados.m,
        g: totalRecogidos.g - totalEntregados.g
    };
    
    const totalVacios = vacios.p + vacios.m + vacios.g;
    const totalLlenos = totalEntregados.p + totalEntregados.m + totalEntregados.g;
    const enPlanta = recogidas.filter(r => r.estado === 'en_planta').length;
    const entregadosHoy = entregas.filter(e => new Date(e.fecha).toDateString() === new Date().toDateString()).reduce((sum, e) => sum + e.pequenos + e.medianos + e.grandes, 0);
    
    document.getElementById('enRuta').textContent = enPlanta;
    document.getElementById('llenos').textContent = totalLlenos;
    document.getElementById('vacios').textContent = totalVacios;
    document.getElementById('entregados').textContent = entregadosHoy;
    
    // Última carga
    if (entregas.length > 0) {
        const ultima = entregas[entregas.length - 1];
        const fecha = new Date(ultima.fecha).toLocaleDateString();
        const total = calcularTotalEntrega(ultima);
        document.getElementById('ultimaCargaTexto').textContent = `${ultima.comunidad} - ${fecha} - $${total.toFixed(2)}`;
    } else {
        document.getElementById('ultimaCargaTexto').textContent = 'No hay cargas registradas';
    }
}

// ============================================================
// 7. EXPORTAR FUNCIONES PARA USO EN OTROS ARCHIVOS
// ============================================================

// Las funciones ya están en el ámbito global para ser usadas desde HTML
