/** Íconos de la pantalla de Usuarios — extraídos del mockup usuarios.html */

const base = {
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
}

export const IconMas = (props) => (
    <svg {...base} width={15} height={15} strokeWidth={2.2} {...props}>
        <path d="M12 5v14M5 12h14" />
    </svg>
)

export const IconFlecha = (props) => (
    <svg {...base} width={15} height={15} strokeWidth={2} {...props}>
        <path d="M9 6l6 6-6 6" />
    </svg>
)

export const IconEditar = (props) => (
    <svg {...base} width={14} height={14} strokeWidth={1.8} {...props}>
        <path d="M16 3l5 5-11 11H5v-5z" />
    </svg>
)

export const IconPapelera = (props) => (
    <svg {...base} width={14} height={14} strokeWidth={1.8} {...props}>
        <path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6" />
    </svg>
)

export const IconAdvertencia = (props) => (
    <svg {...base} width={22} height={22} strokeWidth={1.9} {...props}>
        <path d="M12 3l9 16H3z" />
        <path d="M12 9v5M12 16h.01" />
    </svg>
)
