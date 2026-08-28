import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getClientsSummary } from '@/services/clients'
import { getFlows, getFlowsSummary, getFlow, createFlow, updateFlow, deleteFlow, executeFlow } from '@/services/flows'

export const CLAVES_FLUJOS = {
    clientes: (filtros) => ['flujos', 'clientes', filtros],
    flows: (clienteId) => ['flujos', 'flows', String(clienteId)],
    flow: (clienteId, flowId) => ['flujos', 'flow', String(clienteId), String(flowId)],
}

export function useClientesFlujos(filtros = {}) {
    const params = {}
    if (filtros.search?.trim()) params.search = filtros.search.trim()
    if (filtros.erpType) params.erp_type = filtros.erpType
    if (filtros.isActive !== null && filtros.isActive !== undefined) {
        params.is_active = filtros.isActive
    }

    return useQuery({
        queryKey: CLAVES_FLUJOS.clientes(params),
        queryFn: () => getClientsSummary(params),
        select: (respuesta) => respuesta.data,
        placeholderData: (previo) => previo,
    })
}

export function useFlowsCliente(clienteId) {
    return useQuery({
        queryKey: CLAVES_FLUJOS.flows(clienteId),
        queryFn: () => getFlows(clienteId),
        select: (respuesta) => respuesta.data,
        enabled: Boolean(clienteId),
    })
}

export function useFlowsClienteSummary(clienteId) {
    return useQuery({
        queryKey: ['flujos', 'flows-summary', String(clienteId)],
        queryFn: () => getFlowsSummary(clienteId),
        select: (respuesta) => respuesta.data,
        enabled: Boolean(clienteId),
    })
}

export function useFlowDetalle(clienteId, flowId) {
    return useQuery({
        queryKey: CLAVES_FLUJOS.flow(clienteId, flowId),
        queryFn: () => getFlow(clienteId, flowId),
        select: (respuesta) => respuesta.data,
        enabled: Boolean(clienteId) && Boolean(flowId),
    })
}

export function useCrearFlow(clienteId) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (datos) => createFlow(clienteId, datos),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: CLAVES_FLUJOS.flows(clienteId) })
        },
    })
}

export function useActualizarFlow(clienteId, flowId) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (datos) => updateFlow(clienteId, flowId, datos),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: CLAVES_FLUJOS.flows(clienteId) })
            queryClient.invalidateQueries({ queryKey: CLAVES_FLUJOS.flow(clienteId, flowId) })
        },
    })
}

export function useEliminarFlow(clienteId) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (flowId) => deleteFlow(clienteId, flowId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: CLAVES_FLUJOS.flows(clienteId) })
        },
    })
}

export function useEjecutarFlow() {
    return useMutation({
        mutationFn: (flowId) => executeFlow(flowId),
    })
}

export function mensajeDeError(error, porDefecto = 'Ocurrio un error inesperado') {
    return error?.response?.data?.detail || error?.message || porDefecto
}
