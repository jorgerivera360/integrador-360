/** Utilidades de búsqueda de texto. */

/** Minúsculas y sin tildes, para comparar sin que el acento estorbe. */
export function normalizar(valor) {
    return String(valor ?? '')
        .normalize('NFD')
        .replace(/\p{Diacritic}/gu, '')
        .toLowerCase()
        .trim()
}

/**
 * ¿`texto` contiene `busqueda`?
 * Ignora mayúsculas, tildes y espacios sobrantes. Una búsqueda vacía
 * siempre coincide, para que un filtro sin usar no descarte nada.
 */
export function contiene(texto, busqueda) {
    const aguja = normalizar(busqueda)
    if (!aguja) return true
    return normalizar(texto).includes(aguja)
}
