/** Íconos de las tarjetas de estadística del tablero (mockup tablero.html). */

const base = {
    width: 21,
    height: 21,
    viewBox: '0 0 24 24',
    fill: 'none',
    strokeWidth: 1.7,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
}

export const IconClientesActivos = () => (
    <svg {...base} stroke="#1890ff">
        <path d="M4 21V7l7-4v18M11 21h9V11h-9M14 15h3M14 18h3M7 11h1M7 15h1" />
    </svg>
)

export const IconFlujosActivos = () => (
    <svg {...base} stroke="#2f54eb">
        <path d="M4 6h5M15 6h5M4 18h5M15 18h5M9 6a3 3 0 003 3h0a3 3 0 013 3M9 18a3 3 0 013-3" />
    </svg>
)

export const IconEjecuciones24h = () => (
    <svg {...base} stroke="#722ed1">
        <path d="M8 5l11 7-11 7z" />
    </svg>
)

export const IconTasaExito = () => (
    <svg {...base} stroke="#52c41a" strokeWidth={2}>
        <path d="M20 6L9 17l-5-5" />
    </svg>
)
