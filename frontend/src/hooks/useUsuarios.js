import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getUsers, getUser, createUser, updateUser, deleteUser } from '@/services/users'

/**
 * Hooks de datos de usuarios.
 *
 * Toda la sección es superadmin: los cinco endpoints de /users llevan
 * require_role("superadmin") en api/routes/users.py.
 *
 * GET /users/ solo acepta `is_active`; no hay búsqueda por texto en el
 * servidor, por eso la pantalla no tiene buscador.
 */

export const CLAVES_USUARIOS = {
    todos: ['usuarios'],
    lista: (filtros) => ['usuarios', 'lista', filtros],
    detalle: (id) => ['usuarios', 'detalle', String(id)],
}

export function useUsuarios(filtros = {}) {
    const params = {}
    if (filtros.isActive !== null && filtros.isActive !== undefined) {
        params.is_active = filtros.isActive
    }

    return useQuery({
        queryKey: CLAVES_USUARIOS.lista(params),
        queryFn: () => getUsers(params),
        select: (respuesta) => respuesta.data,
        placeholderData: (previo) => previo,
    })
}

export function useUsuario(id) {
    return useQuery({
        queryKey: CLAVES_USUARIOS.detalle(id),
        queryFn: () => getUser(id),
        select: (respuesta) => respuesta.data,
        enabled: Boolean(id),
    })
}

export function useCrearUsuario() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (datos) => createUser(datos),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: CLAVES_USUARIOS.todos }),
    })
}

export function useActualizarUsuario() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: ({ id, datos }) => updateUser(id, datos),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: CLAVES_USUARIOS.todos }),
    })
}

export function useEliminarUsuario() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (id) => deleteUser(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: CLAVES_USUARIOS.todos }),
    })
}
