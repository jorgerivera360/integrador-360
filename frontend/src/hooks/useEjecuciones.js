import { useQuery } from '@tanstack/react-query'
import { getFlowExecutions } from '@/services/executions'
import { getClients } from '@/services/clients'
import { getFlows } from '@/services/flows'

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
    const params = {}
    if (filtros.search?.trim()) params.search = filtros.search.trim()
    if (filtros.erpType) params.erp_type = filtros.erpType
    if (filtros.isActive !== null && filtros.isActive !== undefined) {
        params.is_active = filtros.isActive
    }

    return useQuery({
        queryKey: CLAVES_EJECUCIONES.clientes(params),
        queryFn: () => getClients(params),
        select: (respuesta) => respuesta.data,
        placeholderData: (previo) => previo,
    })
}

export function useFlowsCliente(clienteId) {
    return useQuery({
        queryKey: CLAVES_EJECUCIONES.flows(clienteId, {}),
        queryFn: () => getFlows(clienteId),
        select: (respuesta) => respuesta.data,
        enabled: Boolean(clienteId),
    })
}

export function mensajeDeError(error, porDefecto = 'Ocurrió un error inesperado') {
    return error?.response?.data?.detail || error?.message || porDefecto
}

export function useHistorialEjecuciones(flowId, filtros = {}) {
    const params = {}
    if (filtros.status) params.status = filtros.status
    if (filtros.triggeredBy) params.triggered_by = filtros.triggeredBy
    params.limit = filtros.limit || 50

    return useQuery({
        queryKey: CLAVES_EJECUCIONES.historial(flowId, params),
        queryFn: () => getFlowExecutions(flowId, params),
        select: (respuesta) => {
            const data = respuesta.data
            return data?.result ?? data ?? []
        },
        enabled: Boolean(flowId),
    })
}
