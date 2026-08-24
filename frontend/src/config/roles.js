/**
 * roles.js — Roles del panel.
 *
 * Los tres valores son los del CHECK de la tabla `users` y de la validación
 * en api/routes/users.py:51. Aquí viven además su nombre visible, su
 * descripción y sus colores, que son presentación y el backend no provee.
 *
 * Es la fuente única: navigation.jsx importa ROLES de aquí para filtrar el
 * menú, y la pantalla de Usuarios usa ROLES_INFO para pintar las etiquetas.
 */

export const ROLES = {
    SUPERADMIN: 'superadmin',
    ADMIN: 'admin',
    VIEWER: 'viewer',
}

export const ROLES_INFO = {
    superadmin: {
        label: 'Super Admin',
        descripcion: 'Acceso completo: usuarios, clientes, flujos, ejecuciones',
        color: '#cf1322',
        fondo: '#fff1f0',
        borde: '#ffa39e',
    },
    admin: {
        label: 'Admin',
        descripcion: 'Clientes, flujos y ejecuciones. Sin gestión de usuarios',
        color: '#096dd9',
        fondo: '#e6f7ff',
        borde: '#91d5ff',
    },
    viewer: {
        label: 'Viewer',
        descripcion: 'Solo lectura en todo el panel',
        color: '#389e0d',
        fondo: '#f6ffed',
        borde: '#b7eb8f',
    },
}

/** Nombre visible ('admin' → 'Admin'). Desconocido: se devuelve tal cual. */
export function etiquetaRol(rol) {
    return ROLES_INFO[rol]?.label || rol || ''
}

/** Opciones para Select, en orden de más a menos privilegios. */
export const OPCIONES_ROL = [ROLES.SUPERADMIN, ROLES.ADMIN, ROLES.VIEWER].map((valor) => ({
    value: valor,
    label: ROLES_INFO[valor].label,
}))

/** Dominio corporativo que exige /auth/login para dejar entrar. */
export const DOMINIO_CORPORATIVO = '@360software.com.co'
