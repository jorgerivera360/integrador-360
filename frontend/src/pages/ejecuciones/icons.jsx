const base = {
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
}

export const IconProductos = (props) => (
    <svg {...base} width={22} height={22} strokeWidth={1.7} {...props}>
        <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" />
        <path d="M3.27 6.96L12 12.01l8.73-5.05M12 22.08V12" />
    </svg>
)

export const IconClientes = (props) => (
    <svg {...base} width={22} height={22} strokeWidth={1.7} {...props}>
        <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
    </svg>
)

export const IconProveedores = (props) => (
    <svg {...base} width={22} height={22} strokeWidth={1.7} {...props}>
        <rect x="1" y="3" width="15" height="13" rx="2" />
        <path d="M16 8h4l3 3v5h-7V8zM5.5 21a2.5 2.5 0 100-5 2.5 2.5 0 000 5zM18.5 21a2.5 2.5 0 100-5 2.5 2.5 0 000 5z" />
    </svg>
)

export const IconEntrada = (props) => (
    <svg {...base} width={22} height={22} strokeWidth={1.7} {...props}>
        <path d="M12 3v12M5 10l7 7 7-7" />
        <path d="M19 21H5" />
    </svg>
)

export const IconSalida = (props) => (
    <svg {...base} width={22} height={22} strokeWidth={1.7} {...props}>
        <path d="M12 19V7M5 12l7-7 7 7" />
        <path d="M19 21H5" />
    </svg>
)

export const IconFlecha = (props) => (
    <svg {...base} width={15} height={15} strokeWidth={2} {...props}>
        <path d="M9 6l6 6-6 6" />
    </svg>
)

export const IconVolver = (props) => (
    <svg {...base} width={15} height={15} strokeWidth={2} {...props}>
        <path d="M15 6l-6 6 6 6" />
    </svg>
)

export const IconLupa = (props) => (
    <svg {...base} width={15} height={15} strokeWidth={1.9} {...props}>
        <circle cx="11" cy="11" r="7" />
        <path d="M16.5 16.5L21 21" />
    </svg>
)

export const IconReloj = (props) => (
    <svg {...base} width={14} height={14} strokeWidth={1.8} {...props}>
        <circle cx="12" cy="12" r="10" />
        <path d="M12 6v6l4 2" />
    </svg>
)
