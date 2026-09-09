import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
    getClients,
    getClient,
    createClient,
    updateClient,
    deleteClient,
    testErp,
    testOdoo,
    testErpWithCredentials,
    testOdooWithCredentials,
    saveCredentials,
    provisionContainer,
    getProvisionStatus,
    getCredentials,
    getCredentialsStatus,
    deleteCredentials,
    deleteProvision,
} from '@/services/clients'

/**
 * Hooks de datos de clientes.
 *
 * A diferencia de /dashboard/*, estos endpoints devuelven el arreglo o el
 * objeto pelado (tienen response_model), así que el `select` solo saca
 * `.data`. Los de test sí traen {code, success, msg}.
 */

export const CLAVES_CLIENTES = {
    todos: ['clientes'],
    lista: (filtros) => ['clientes', 'lista', filtros],
    detalle: (id) => ['clientes', 'detalle', String(id)],
}

/**
 * Listado con filtros del servidor.
 * Solo se mandan los filtros con valor: la API acumula condiciones sobre
 * `WHERE 1=1` y un parámetro vacío filtraría de más.
 */
export function useClientes(filtros = {}) {
    return useQuery({
        queryKey: CLAVES_CLIENTES.lista({}),
        queryFn: () => getClients({}),
        select: (respuesta) => {
            let data = respuesta.data
            if (filtros.search?.length) {
                data = data.filter((c) => filtros.search.includes(c.name))
            }
            if (filtros.erpType?.length) {
                data = data.filter((c) => filtros.erpType.includes(c.erp_type))
            }
            if (filtros.isActive?.length) {
                data = data.filter((c) => filtros.isActive.includes(c.is_active))
            }
            return data
        },
        placeholderData: (previo) => previo,
    })
}

export function useCliente(id) {
    return useQuery({
        queryKey: CLAVES_CLIENTES.detalle(id),
        queryFn: () => getClient(id),
        select: (respuesta) => respuesta.data,
        enabled: Boolean(id),
    })
}

export function useCrearCliente() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (datos) => createClient(datos),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: CLAVES_CLIENTES.todos }),
    })
}

export function useActualizarCliente(id) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (datos) => updateClient(id, datos),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: CLAVES_CLIENTES.todos }),
    })
}

export function useEliminarCliente() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (id) => deleteClient(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: CLAVES_CLIENTES.todos }),
    })
}

/**
 * Prueba de conexión. `tipo`: 'erp' | 'odoo'.
 * No invalida caché porque no muta nada.
 *
 * Ojo: estos endpoints atrapan sus excepciones y responden siempre HTTP
 * 200 con {code, success, msg}. El fallo se lee en `success`, no en el
 * estado de la mutación.
 */
export function useProbarConexion(id, tipo) {
    return useMutation({
        mutationFn: async () => {
            const respuesta = await (tipo === 'odoo' ? testOdoo(id) : testErp(id))
            return respuesta.data
        },
    })
}

/**
 * Prueba de conexión con credenciales del formulario (sin GCP).
 * `tipo`: 'erp' | 'odoo'. `credentials`: objeto con { erp, odoo }.
 */
export function useProbarConexionConCredenciales(id, tipo) {
    return useMutation({
        mutationFn: async (credentials) => {
            const fn = tipo === 'odoo' ? testOdooWithCredentials : testErpWithCredentials
            const respuesta = await fn(id, credentials)
            return respuesta.data
        },
    })
}

export function useGuardarCredenciales(id) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async (data) => {
            const respuesta = await saveCredentials(id, data)
            return respuesta.data
        },
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['credentials', 'status', String(id)] }),
    })
}

export function useProvisionarContenedor(id) {
    return useMutation({
        mutationFn: async () => {
            const respuesta = await provisionContainer(id)
            return respuesta.data
        },
    })
}

export function useCredenciales(id) {
    return useQuery({
        queryKey: ['credentials', 'data', String(id)],
        queryFn: async () => {
            const respuesta = await getCredentials(id)
            return respuesta.data
        },
        enabled: Boolean(id),
    })
}

export function useEstadoCredenciales(id) {
    return useQuery({
        queryKey: ['credentials', 'status', String(id)],
        queryFn: async () => {
            const respuesta = await getCredentialsStatus(id)
            return respuesta.data
        },
        enabled: Boolean(id),
    })
}

export function useEliminarCredenciales(id) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async () => {
            const respuesta = await deleteCredentials(id)
            return respuesta.data
        },
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['credentials', 'status', String(id)] }),
    })
}

export function useEliminarContenedor(id) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async () => {
            const respuesta = await deleteProvision(id)
            return respuesta.data
        },
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['provision', 'status', String(id)] }),
    })
}

export function useEstadoProvision(id) {
    return useQuery({
        queryKey: ['provision', 'status', String(id)],
        queryFn: async () => {
            const respuesta = await getProvisionStatus(id)
            return respuesta.data
        },
        enabled: Boolean(id),
        refetchInterval: 10_000,
    })
}

/** Mensaje legible de un error de axios contra esta API. */
export function mensajeDeError(error, porDefecto = 'Ocurrió un error inesperado') {
    return error?.response?.data?.detail || error?.message || porDefecto
}
