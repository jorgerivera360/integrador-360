/** Íconos de la pantalla de Clientes — extraídos del mockup clientes.html */

const base = {
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
}

export const IconLupa = (props) => (
    <svg {...base} width={15} height={15} strokeWidth={1.9} {...props}>
        <circle cx="11" cy="11" r="7" />
        <path d="M16.5 16.5L21 21" />
    </svg>
)

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

export const IconPapelera = (props) => (
    <svg {...base} width={15} height={15} strokeWidth={1.8} {...props}>
        <path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6" />
    </svg>
)

export const IconRayo = (props) => (
    <svg {...base} width={14} height={14} strokeWidth={1.8} {...props}>
        <path d="M13 2L3 14h7l-1 8 10-12h-7z" />
    </svg>
)

export const IconServidor = (props) => (
    <svg {...base} width={26} height={26} strokeWidth={1.6} stroke="#1677ff" {...props}>
        <rect x="3" y="4" width="18" height="6" rx="2" />
        <rect x="3" y="14" width="18" height="6" rx="2" />
        <path d="M7 7h.01M7 17h.01" />
    </svg>
)

export const IconNube = (props) => (
    <svg {...base} width={26} height={26} strokeWidth={1.6} stroke="#52c41a" {...props}>
        <path d="M6 18a4 4 0 01.4-8A5.5 5.5 0 0117 9.5a3.5 3.5 0 011 6.9" />
        <path d="M6 18h11.5" />
    </svg>
)

export const IconCheck = (props) => (
    <svg {...base} width={15} height={15} strokeWidth={2.2} {...props}>
        <path d="M20 6L9 17l-5-5" />
    </svg>
)

export const IconEquis = (props) => (
    <svg {...base} width={15} height={15} strokeWidth={2.2} {...props}>
        <path d="M6 6l12 12M18 6L6 18" />
    </svg>
)

export const IconAdvertencia = (props) => (
    <svg {...base} width={14} height={14} strokeWidth={1.9} {...props}>
        <path d="M12 3l9 16H3z" />
        <path d="M12 9v5M12 16h.01" />
    </svg>
)

export const IconInfo = (props) => (
    <svg {...base} width={17} height={17} strokeWidth={1.9} {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 11v5M12 8h.01" />
    </svg>
)
