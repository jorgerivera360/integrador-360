/** Íconos de Auditoría — extraídos del mockup auditoria.html */

const base = {
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
}

/** Se usa junto al nombre de la tabla en la columna correspondiente. */
export const IconTabla = (props) => (
    <svg {...base} width={15} height={15} strokeWidth={1.7} {...props}>
        <path d="M4 6h5M15 6h5M4 18h5M15 18h5M9 6a3 3 0 003 3h0a3 3 0 013 3M9 18a3 3 0 013-3" />
    </svg>
)

export const IconCrear = (props) => (
    <svg {...base} width={11} height={11} strokeWidth={2} {...props}>
        <path d="M12 5v14M5 12h14" />
    </svg>
)

export const IconEditar = (props) => (
    <svg {...base} width={11} height={11} strokeWidth={2} {...props}>
        <path d="M16 3l5 5-11 11H5v-5z" />
    </svg>
)

export const IconBorrar = (props) => (
    <svg {...base} width={11} height={11} strokeWidth={2} {...props}>
        <path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" />
    </svg>
)

export const IconAntes = (props) => (
    <svg {...base} width={14} height={14} strokeWidth={2} {...props}>
        <path d="M11 6l-6 6 6 6M19 12H5" />
    </svg>
)

export const IconDespues = (props) => (
    <svg {...base} width={14} height={14} strokeWidth={2} {...props}>
        <path d="M13 6l6 6-6 6M5 12h14" />
    </svg>
)

export const IconCheck = (props) => (
    <svg {...base} width={14} height={14} strokeWidth={2.2} {...props}>
        <path d="M20 6L9 17l-5-5" />
    </svg>
)

export const IconEquis = (props) => (
    <svg {...base} width={14} height={14} strokeWidth={2.2} {...props}>
        <path d="M6 6l12 12M18 6L6 18" />
    </svg>
)
