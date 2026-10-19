import api from './api'

export const getWmsFields = (params) =>
    api.get('/wms-fields', { params }).then((r) => r.data)

export const getWmsField = (id) =>
    api.get(`/wms-fields/${id}`).then((r) => r.data)

export const createWmsField = (data) =>
    api.post('/wms-fields', data).then((r) => r.data)

export const updateWmsField = (id, data) =>
    api.put(`/wms-fields/${id}`, data).then((r) => r.data)

export const deleteWmsField = (id) =>
    api.delete(`/wms-fields/${id}`).then((r) => r.data)
