import api from './api'

export const uploadExcel = (clientId, tipo, archivo) => {
    const formData = new FormData()
    formData.append('tipo', tipo)
    formData.append('archivo', archivo)
    return api.post(`/clients/${clientId}/upload-excel`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })
}

export const getExcelFiles = (clientId) => {
    return api.get(`/clients/${clientId}/excel-files`)
}
