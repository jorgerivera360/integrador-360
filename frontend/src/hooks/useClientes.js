import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
    getClients,
    getClient,
    createClient,
    updateClient,
    deleteClient,
    testErp,
    testOdoo,
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
    const params = {}
    if (filtros.search?.trim()) params.search = filtros.search.trim()
    if (filtros.erpType) params.erp_type = filtros.erpType
    if (filtros.isActive !== null && filtros.isActive !== undefined) {
        params.is_active = filtros.isActive
    }

    return useQuery({
        queryKey: CLAVES_CLIENTES.lista(params),
        queryFn: () => getClients(params),
        select: (respuesta) => respuesta.data,
        placeholderData: (previo) => previo, // evita el parpadeo al filtrar
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

/** Mensaje legible de un error de axios contra esta API. */
export function mensajeDeError(error, porDefecto = 'Ocurrió un error inesperado') {
    return error?.response?.data?.detail || error?.message || porDefecto
}
