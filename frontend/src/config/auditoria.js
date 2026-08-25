/**
 * auditoria.js — Acciones registradas en change_history.
 *
 * Los tres valores son los del CHECK de la tabla. El texto y los colores son
 * presentación; el backend solo devuelve el slug.
 */

export const ACCIONES = {
    create: {
        label: 'Creación',
        color: '#389e0d',
        fondo: '#f6ffed',
        borde: '#b7eb8f',
    },
    update: {
        label: 'Actualización',
        color: '#096dd9',
        fondo: '#e6f7ff',
        borde: '#91d5ff',
    },
    delete: {
        label: 'Eliminación',
        color: '#cf1322',
        fondo: '#fff1f0',
        borde: '#ffa39e',
    },
}

/** Texto visible ('update' → 'Actualización'). Desconocido: se devuelve tal cual. */
export function etiquetaAccion(accion) {
    return ACCIONES[accion]?.label || accion || ''
}
