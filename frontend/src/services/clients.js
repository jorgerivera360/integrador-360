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

// --- Provisioning (onboarding) ---

export const testErpWithCredentials = (id, credentials) => {
    return api.post(`/clients/${id}/test/erp`, credentials)
}

export const testOdooWithCredentials = (id, credentials) => {
    return api.post(`/clients/${id}/test/odoo`, credentials)
}

export const saveCredentials = (id, data) => {
    return api.post(`/clients/${id}/credentials`, data)
}

export const provisionContainer = (id) => {
    return api.post(`/clients/${id}/provision`)
}

export const getProvisionStatus = (id) => {
    return api.get(`/clients/${id}/provision/status`)
}

export const getCredentialsStatus = (id) => {
    return api.get(`/clients/${id}/credentials/status`)
}

export const deleteCredentials = (id) => {
    return api.delete(`/clients/${id}/credentials`)
}

export const deleteProvision = (id) => {
    return api.delete(`/clients/${id}/provision`)
}