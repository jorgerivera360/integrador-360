import api from './api'

export const getFlows = (clientId, params = {}) => {
    return api.get(`/clients/${clientId}/flows/`, { params })
}

export const getFlow = (clientId, flowId) => {
    return api.get(`/clients/${clientId}/flows/${flowId}`)
}

export const createFlow = (clientId, data) => {
    return api.post(`/clients/${clientId}/flows/`, data)
}

export const updateFlow = (clientId, flowId, data) => {
    return api.put(`/clients/${clientId}/flows/${flowId}`, data)
}

export const deleteFlow = (clientId, flowId) => {
    return api.delete(`/clients/${clientId}/flows/${flowId}`)
}

export const executeFlow = (flowId) => {
    return api.post(`/flows/${flowId}/execute`)
}