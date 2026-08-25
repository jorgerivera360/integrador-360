import { useQuery } from '@tanstack/react-query'
import { getDashboardStatus, getDashboardErrors } from '@/services/dashboard'

/**
 * Hooks de datos del tablero.
 *
 * Nota sobre la forma de la respuesta: /dashboard/* devuelve
 * { code, result }, a diferencia de /clients o /flows que devuelven el
 * arreglo pelado. El `select` desenvuelve aquí para que los componentes
 * no tengan que saberlo.
 */

export const CLAVES_DASHBOARD = {
    status: ['dashboard', 'status'],
    errors: (limite) => ['dashboard', 'errors', limite],
}

/** Contadores + últimas 10 ejecuciones. Se refresca solo cada 30 s. */
export function useDashboardStatus() {
    return useQuery({
        queryKey: CLAVES_DASHBOARD.status,
        queryFn: getDashboardStatus,
        select: (respuesta) => respuesta.data.result,
        refetchInterval: 30_000,
    })
}

/** Ejecuciones con error o parciales. */
export function useDashboardErrors(limite = 20) {
    return useQuery({
        queryKey: CLAVES_DASHBOARD.errors(limite),
        queryFn: () => getDashboardErrors({ limit: limite }),
        select: (respuesta) => respuesta.data.result,
    })
}
