import { useQuery } from '@tanstack/react-query'
import { getChanges } from '@/services/changes'

const LIMITE = 200

export const CLAVES_CAMBIOS = {
    todos: ['cambios'],
    lista: (filtros) => ['cambios', 'lista', filtros],
}

export function useCambios(filtros = {}) {
    const params = { limit: LIMITE }
    if (filtros.changedBy) params.changed_by = filtros.changedBy

    return useQuery({
        queryKey: CLAVES_CAMBIOS.lista(params),
        queryFn: () => getChanges(params),
        select: (respuesta) => {
            let data = respuesta.data.result
            if (filtros.tableName?.length) {
                data = data.filter((c) => filtros.tableName.includes(c.table_name))
            }
            if (filtros.action?.length) {
                data = data.filter((c) => filtros.action.includes(c.action))
            }
            return data
        },
        placeholderData: (previo) => previo,
    })
}

export const LIMITE_CAMBIOS = LIMITE
