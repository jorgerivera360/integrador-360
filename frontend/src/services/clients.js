import api from './api'

export const getClients = (params = {}) => {
    return api.get('/clients/', { params })
}

export const getClientsSummary = (params = {}) => {
    return api.get('/clients/summary', { params })
}

export const getClient = (id) => {
    return api.get(`/clients/${id}`)
}

export const createClient = (data) => {
    return api.post('/clients/', data)
}

export const updateClient = (id, data) => {
    return api.put(`/clients/${id}`, data)
}

export const deleteClient = (id) => {
    return api.delete(`/clients/${id}`)
}

export const testErp = (id) => {
    return api.post(`/clients/${id}/test/erp`)
}

export const testOdoo = (id) => {
    return api.post(`/clients/${id}/test/odoo`)
}