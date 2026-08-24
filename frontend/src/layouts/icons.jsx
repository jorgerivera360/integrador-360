/**
 * Íconos del layout — extraídos del mockup panel.html
 * Usan stroke="currentColor" para heredar el color del contexto
 * (menú inactivo, activo, hover) sin CSS adicional.
 */

const base = {
    width: 16,
    height: 16,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.7,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
}

export const IconTablero = (props) => (
    <svg {...base} {...props}>
        <path d="M3 3h7v7H3zM14 3h7v4h-7zM14 10h7v11h-7zM3 13h7v8H3z" />
    </svg>
)

export const IconFlujos = (props) => (
    <svg {...base} {...props}>
        <path d="M4 6h6M14 6h6M4 18h6M14 18h6M10 6a4 4 0 004 4M10 18a4 4 0 014-4" />
    </svg>
)

export const IconEjecuciones = (props) => (
    <svg {...base} {...props}>
        <path d="M8 5l11 7-11 7z" />
    </svg>
)

export const IconAuditoria = (props) => (
    <svg {...base} {...props}>
        <path d="M7 3h10v18H7zM10 8h4M10 12h4M10 16h2" />
    </svg>
)

export const IconAdmin = (props) => (
    <svg {...base} {...props}>
        <path d="M12 3l7 4v5c0 4-3 7-7 9-4-2-7-5-7-9V7z" />
    </svg>
)

export const IconClientes = (props) => (
    <svg {...base} {...props}>
        <path d="M8 11a3 3 0 100-6 3 3 0 000 6zM2 20c0-3 3-5 6-5s6 2 6 5M17 11a3 3 0 100-6M16 15c3 0 6 2 6 5" />
    </svg>
)

export const IconUsuarios = (props) => (
    <svg {...base} {...props}>
        <path d="M12 12a4 4 0 100-8 4 4 0 000 8zM4 21c0-4 4-6 8-6s8 2 8 6" />
    </svg>
)

export const IconSalir = (props) => (
    <svg {...base} width={15} height={15} strokeWidth={1.8} {...props}>
        <path d="M14 4H6v16h8M17 8l4 4-4 4M21 12H10" />
    </svg>
)

export const IconRueda = (props) => (
    <svg {...base} width={18} height={18} strokeWidth={1.6} strokeLinecap="butt" {...props}>
        <path d="M9.9 2.1h3.2l.5 2.5 1.9.8 2.2-1.3 2.2 2.2-1.3 2.2.8 1.9 2.5.5v3.2l-2.5.5-.8 1.9 1.3 2.2-2.2 2.2-2.2-1.3-1.9.8-.5 2.5H9.9l-.5-2.5-1.9-.8-2.2 1.3-2.2-2.2 1.3-2.2-.8-1.9-2.5-.5v-3.2l2.5-.5.8-1.9-1.3-2.2 2.2-2.2 2.2 1.3 1.9-.8z" />
        <circle cx="11.5" cy="11.5" r="3.1" />
    </svg>
)
