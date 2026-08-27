import { useQuery } from '@tanstack/react-query'
import { getChanges } from '@/services/changes'

const LIMITE = 200

export const CLAVES_CAMBIOS = {
    todos: ['cambios'],
    lista: (filtros) => ['cambios', 'lista', filtros],
}

export function useCambios(filtros = {}) {
    const params = { limit: LIMITE }
    if (filtros.tableName) params.table_name = filtros.tableName
    if (filtros.action) params.action = filtros.action
    if (filtros.changedBy) params.changed_by = filtros.changedBy

    return useQuery({
        queryKey: CLAVES_CAMBIOS.lista(params),
        queryFn: () => getChanges(params),
        select: (respuesta) => respuesta.data.result,
        placeholderData: (previo) => previo,
    })
}

export const LIMITE_CAMBIOS = LIMITE
