/**
 * erp.js — Tipos de ERP que el integrador puede ejecutar.
 *
 * Son los mismos cuatro en los tres lugares: build_connector() en main.py,
 * la validación de api/routes/clients.py y GET /catalog/erp-types. Cuando
 * exista connection/kubapp.py hay que agregarlo en los tres.
 *
 * Ojo: la columna clients.erp_type NO tiene CHECK en la base de datos; la
 * única validación vive en la API. Un INSERT por SQL puede meter cualquier
 * valor, y por eso erpPorValor() tolera desconocidos en vez de romper.
 *
 * GET /catalog/erp-types ya expone estos valores y sus nombres. Este archivo
 * se conserva por los colores, que son presentación, y como respaldo si el
 * catálogo no responde.
 */

export const ERP_TYPES = [
    {
        value: 'ws',
        label: 'Siesa Web Service',
        color: '#0958d9',
        fondo: '#e6f4ff',
        borde: '#91caff',
    },
    {
        value: 'connekta',
        label: 'Siesa Connekta',
        color: '#389e0d',
        fondo: '#f6ffed',
        borde: '#b7eb8f',
    },
    {
        value: 'sap',
        label: 'SAP B1',
        color: '#d46b08',
        fondo: '#fff7e6',
        borde: '#ffd591',
    },
    {
        value: 'excel',
        label: 'Excel',
        color: '#595959',
        fondo: '#fafafa',
        borde: '#d9d9d9',
    },
]

const POR_VALOR = Object.fromEntries(ERP_TYPES.map((erp) => [erp.value, erp]))

/** Configuración de un ERP, o null si el valor no está en el catálogo. */
export function erpPorValor(valor) {
    return POR_VALOR[valor] || null
}

/** Nombre visible ('ws' → 'Siesa Web Service'). Desconocido: se devuelve tal cual. */
export function etiquetaErp(valor) {
    return POR_VALOR[valor]?.label || valor || ''
}

/** Opciones para Select de antd, con el valor técnico entre paréntesis. */
export const OPCIONES_ERP = ERP_TYPES.map((erp) => ({
    value: erp.value,
    label: `${erp.label} (${erp.value})`,
}))
