/**
 * Formateadores compartidos.
 * Sin dependencias: las fechas de la API llegan como ISO 8601 con zona
 * (TIMESTAMPTZ de PostgreSQL) y Date las interpreta bien.
 */

const VACIO = '—'

const dosDigitos = (n) => String(n).padStart(2, '0')

/**
 * '2026-08-20T15:16:04-05:00' → '2026-08-20 15:16:04'
 * Se muestra en la zona horaria del navegador, no en UTC.
 */
export function formatFechaHora(iso) {
    if (!iso) return VACIO
    const fecha = new Date(iso)
    if (Number.isNaN(fecha.getTime())) return VACIO

    const dia = `${fecha.getFullYear()}-${dosDigitos(fecha.getMonth() + 1)}-${dosDigitos(fecha.getDate())}`
    const hora = `${dosDigitos(fecha.getHours())}:${dosDigitos(fecha.getMinutes())}:${dosDigitos(fecha.getSeconds())}`
    return `${dia} ${hora}`
}

/** '2026-08-20T15:16:04-05:00' → '2026-08-20' (sin hora). */
export function formatFecha(iso) {
    if (!iso) return VACIO
    const fecha = new Date(iso)
    if (Number.isNaN(fecha.getTime())) return VACIO

    return `${fecha.getFullYear()}-${dosDigitos(fecha.getMonth() + 1)}-${dosDigitos(fecha.getDate())}`
}

/**
 * Duración entre dos marcas de tiempo: '840ms', '3.2s', '2m 05s'.
 * Sin fin (ejecución en curso) retorna '—'.
 */
export function formatDuracion(inicio, fin) {
    if (!inicio || !fin) return VACIO

    const ms = new Date(fin).getTime() - new Date(inicio).getTime()
    if (!Number.isFinite(ms) || ms < 0) return VACIO

    if (ms < 1000) return `${ms}ms`

    const segundos = ms / 1000
    if (segundos < 60) return `${segundos.toFixed(1)}s`

    const minutos = Math.floor(segundos / 60)
    const resto = Math.round(segundos % 60)
    return `${minutos}m ${dosDigitos(resto)}s`
}

const RELATIVO = new Intl.RelativeTimeFormat('es', { numeric: 'auto' })

const UNIDADES = [
    ['year', 31536000],
    ['month', 2592000],
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60],
]

/**
 * Tiempo transcurrido en lenguaje natural: 'hace 5 minutos', 'hace 3 días'.
 * Sin fecha devuelve `vacio` — para 'último acceso' eso significa 'Nunca'.
 */
export function formatDesde(iso, vacio = 'Nunca') {
    if (!iso) return vacio
    const fecha = new Date(iso)
    if (Number.isNaN(fecha.getTime())) return VACIO

    // Negativo = pasado, que es lo que RelativeTimeFormat espera.
    const segundos = Math.round((fecha.getTime() - Date.now()) / 1000)
    const absolutos = Math.abs(segundos)

    if (absolutos < 60) return 'hace un momento'

    for (const [unidad, factor] of UNIDADES) {
        if (absolutos >= factor) return RELATIVO.format(Math.round(segundos / factor), unidad)
    }

    return 'hace un momento'
}

/** Porcentaje entero. Con total 0 retorna '—' en vez de NaN. */
export function formatPorcentaje(parte, total) {
    if (!total) return VACIO
    return `${Math.round((parte / total) * 100)}%`
}

/** Separador de miles en formato colombiano. */
export function formatNumero(valor) {
    if (valor === null || valor === undefined) return VACIO
    return new Intl.NumberFormat('es-CO').format(valor)
}
