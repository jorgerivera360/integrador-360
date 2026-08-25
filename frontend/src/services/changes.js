import api from './api'

export const getChanges = (params = {}) => {
    return api.get('/changes/', { params })
}

export const getRecordHistory = (tableName, recordId) => {
    return api.get(`/changes/record/${tableName}/${recordId}`)
}