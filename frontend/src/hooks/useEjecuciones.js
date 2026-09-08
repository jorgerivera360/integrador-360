import { useQuery } from '@tanstack/react-query'
import { getFlowExecutions } from '@/services/executions'
import { getClientsSummary } from '@/services/clients'
import { getFlows, getFlowsSummary } from '@/services/flows'

/**
 * Hooks de datos para la pantalla de Ejecuciones.
 *
 * /clients/ y /clients/{id}/flows/ devuelven el arreglo pelado.
 * /flows/{id}/executions devuelve { code, result }.
 */

export const CLAVES_EJECUCIONES = {
    clientes: (filtros) => ['ejecuciones', 'clientes', filtros],
    flows: (clienteId, filtros) => ['ejecuciones', 'flows', String(clienteId), filtros],
    historial: (flowId, filtros) => ['ejecuciones', 'historial', String(flowId), filtros],
}

export function useClientesEjecuciones(filtros = {}) {
    return useQuery({
        queryKey: CLAVES_EJECUCIONES.clientes({}),
        queryFn: () => getClientsSummary({}),
        select: (respuesta) => {
            let data = respuesta.data
            if (filtros.search?.length) {
                data = data.filter((c) => filtros.search.includes(c.name))
            }
            if (filtros.erpType?.length) {
                data = data.filter((c) => filtros.erpType.includes(c.erp_type))
            }
            if (filtros.isActive?.length) {
                data = data.filter((c) => filtros.isActive.includes(c.is_active))
            }
            return data
        },
        placeholderData: (previo) => previo,
    })
}

export function useFlowsCliente(clienteId) {
    return useQuery({
        queryKey: CLAVES_EJECUCIONES.flows(clienteId, {}),
        queryFn: () => getFlowsSummary(clienteId),
        select: (respuesta) => respuesta.data,
        enabled: Boolean(clienteId),
    })
}

export function mensajeDeError(error, porDefecto = 'Ocurrió un error inesperado') {
    return error?.response?.data?.detail || error?.message || porDefecto
}

export function useHistorialEjecuciones(flowId, filtros = {}) {
    const params = { limit: filtros.limit || 2000 }

    return useQuery({
        queryKey: CLAVES_EJECUCIONES.historial(flowId, params),
        queryFn: () => getFlowExecutions(flowId, params),
        select: (respuesta) => {
            let data = respuesta.data
            data = data?.result ?? data ?? []
            if (filtros.status?.length) {
                data = data.filter((e) => filtros.status.includes(e.status))
            }
            if (filtros.triggeredBy?.length) {
                data = data.filter((e) => filtros.triggeredBy.includes(e.triggered_by))
            }
            return data
        },
        enabled: Boolean(flowId),
    })
}
