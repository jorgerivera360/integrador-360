import api from './api'

export const getSqlBlocks = (params) =>
    api.get('/sql-blocks', { params }).then((r) => r.data)

export const getSqlBlock = (id) =>
    api.get(`/sql-blocks/${id}`).then((r) => r.data)

export const createSqlBlock = (data) =>
    api.post('/sql-blocks', data).then((r) => r.data)

export const updateSqlBlock = (id, data) =>
    api.put(`/sql-blocks/${id}`, data).then((r) => r.data)

export const deleteSqlBlock = (id) =>
    api.delete(`/sql-blocks/${id}`).then((r) => r.data)

export const previewSql = (data) =>
    api.post('/sql-blocks/preview', data).then((r) => r.data)
