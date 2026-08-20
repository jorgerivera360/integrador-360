import api from './api'

export const getFlowExecutions = (flowId, params = {}) => {
    return api.get(`/flows/${flowId}/executions`, { params })
}

export const getRecentExecutions = (params = {}) => {
    return api.get('/executions/recent', { params })
}

export const getErrorExecutions = (params = {}) => {
    return api.get('/executions/errors', { params })
}