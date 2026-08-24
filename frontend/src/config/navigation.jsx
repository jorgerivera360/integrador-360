/**
 * navigation.jsx — Definición única del menú lateral.
 *
 * Fuente de verdad para: ítems del sidebar, visibilidad por rol,
 * ítem seleccionado y breadcrumb del header.
 *
 * Los roles reflejan lo que la API permite (GET). La API valida de forma
 * autoritativa; esto solo controla qué se muestra.
 */
import {
    IconTablero,
    IconFlujos,
    IconEjecuciones,
    IconAuditoria,
    IconAdmin,
    IconClientes,
    IconUsuarios,
} from '@/layouts/icons'

import { ROLES } from '@/config/roles'

// Se reexporta para no obligar a cada pantalla a saber de dónde salen.
export { ROLES }

const TODOS = [ROLES.SUPERADMIN, ROLES.ADMIN, ROLES.VIEWER]

export const NAV_ITEMS = [
    {
        key: 'tablero',
        label: 'Tablero',
        path: '/tablero',
        icon: IconTablero,
        roles: TODOS,
    },
    {
        key: 'flujos',
        label: 'Flujos',
        path: '/flujos',
        icon: IconFlujos,
        roles: TODOS,
    },
    {
        key: 'ejecuciones',
        label: 'Ejecuciones',
        path: '/ejecuciones',
        icon: IconEjecuciones,
        roles: TODOS,
    },
    {
        key: 'auditoria',
        label: 'Auditoría',
        path: '/auditoria',
        icon: IconAuditoria,
        roles: TODOS,
    },
    {
        key: 'admin',
        label: 'Admin',
        icon: IconAdmin,
        children: [
            {
                key: 'clientes',
                label: 'Clientes',
                path: '/admin/clientes',
                icon: IconClientes,
                roles: TODOS,
            },
            {
                key: 'usuarios',
                label: 'Usuarios',
                path: '/admin/usuarios',
                icon: IconUsuarios,
                roles: [ROLES.SUPERADMIN],
            },
        ],
    },
]

/**
 * Filtra el árbol de navegación según el rol.
 * Un ítem padre se muestra solo si le queda al menos un hijo visible.
 */
export function filterNavByRole(items, role) {
    return items.reduce((visibles, item) => {
        if (item.children) {
            const hijos = filterNavByRole(item.children, role)
            if (hijos.length > 0) {
                visibles.push({ ...item, children: hijos })
            }
            return visibles
        }

        if (!item.roles || item.roles.includes(role)) {
            visibles.push(item)
        }
        return visibles
    }, [])
}

/** Aplana el árbol a una lista de hojas, conservando el padre de cada una. */
function aplanar(items, padre = null) {
    return items.flatMap((item) =>
        item.children ? aplanar(item.children, item) : [{ ...item, padre }]
    )
}

/**
 * Resuelve la ruta actual contra la navegación.
 * Usa el prefijo más largo, para que /flujos/5/items siga marcando "Flujos".
 * Retorna { item, padre } o null si la ruta no pertenece al menú.
 */
export function resolveNav(pathname) {
    const hojas = aplanar(NAV_ITEMS)

    const coincidencias = hojas
        .filter((hoja) => pathname === hoja.path || pathname.startsWith(`${hoja.path}/`))
        .sort((a, b) => b.path.length - a.path.length)

    if (coincidencias.length === 0) return null

    const item = coincidencias[0]
    return { item, padre: item.padre }
}

/** Migas de pan para el header: ['Admin', 'Usuarios'] o ['Tablero']. */
export function resolveBreadcrumb(pathname) {
    const nav = resolveNav(pathname)
    if (!nav) return []
    return nav.padre ? [nav.padre.label, nav.item.label] : [nav.item.label]
}

/** Ruta por defecto a la que entra el usuario tras iniciar sesión. */
export const RUTA_INICIAL = '/tablero'
