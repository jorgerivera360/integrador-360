import { useQuery } from '@tanstack/react-query'
import { getChanges } from '@/services/changes'

/**
 * Historial de cambios (change_history).
 *
 * /changes/ acepta table_name, record_id, action, changed_by, limit y offset,
 * pero **no devuelve un total**, así que no se puede paginar de verdad: no hay
 * forma de saber cuántas páginas existen.
 *
 * Por eso se traen los últimos LIMITE registros de una vez y se paginan en
 * memoria. Para buscar más atrás está el filtro por ID de registro, que sí va
 * al servidor y es preciso.
 */

const LIMITE = 200

export const CLAVES_CAMBIOS = {
    todos: ['cambios'],
    lista: (filtros) => ['cambios', 'lista', filtros],
}

export function useCambios({ recordId } = {}) {
    const params = { limit: LIMITE }
    if (recordId) params.record_id = recordId

    return useQuery({
        queryKey: CLAVES_CAMBIOS.lista(params),
        // /changes/ envuelve la respuesta en {code, result}, a diferencia de
        // /clients o /users que devuelven el arreglo pelado.
        queryFn: () => getChanges(params),
        select: (respuesta) => respuesta.data.result,
        placeholderData: (previo) => previo,
    })
}

export const LIMITE_CAMBIOS = LIMITE
