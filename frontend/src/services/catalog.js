import api from './api'

export const getDeterminationFunctions = () =>
    api.get('/catalog/determination-functions').then((r) => r.data.result)

export const getFlowTypes = () =>
    api.get('/catalog/flow-types').then((r) => r.data.result)

export const getErpTypes = () =>
    api.get('/catalog/erp-types').then((r) => r.data.result)
