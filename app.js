// ============================================================
// FUNCIONES DE RECOGIDAS (MEJORADAS)
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
        estado: 'pendiente', // 'pendiente' | 'parcial' | 'completa'
        enviado: { p: 0, m: 0, g: 0 } // lo que ya se ha enviado en cargas
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

// ============================================================
// FUNCIONES DE CARGAS (MEJORADAS)
// ============================================================

function crearCarga(planta, fecha, items) {
    // items: [{ recogidaId, pequenos, medianos, grandes, tipoCliente }]
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
        estado: 'activa', // 'activa' | 'completada'
        costos: null,
        gastos: { combustible: 0, peaje: 0, viaticos: 0, imprevistos: 0 }
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
            // Recalcular estado
            actualizarEstadoRecogida(recogida);
        }
    });
    guardarDatos();
    return carga;
}
