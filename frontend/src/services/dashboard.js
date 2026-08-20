import api from './api'

export const getDashboardStatus = () => {
    return api.get('/dashboard/status')
}

export const getDashboardErrors = (params = {}) => {
    return api.get('/dashboard/errors', { params })
}