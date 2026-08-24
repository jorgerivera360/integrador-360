/**
 * Etiqueta de estado de una ejecución.
 * Los cuatro estados son los del CHECK de la tabla executions:
 * running · success · partial · error.
 *
 * Compartido: lo usan el tablero y la pantalla de ejecuciones.
 */
import './estado-tag.css'

export const ESTADOS = {
    success: { texto: 'Éxito', simbolo: '●', color: '#389e0d', fondo: '#f6ffed', borde: '#b7eb8f' },
    partial: { texto: 'Parcial', simbolo: '◐', color: '#d46b08', fondo: '#fff7e6', borde: '#ffd591' },
    error: { texto: 'Error', simbolo: '✖', color: '#cf1322', fondo: '#fff1f0', borde: '#ffa39e' },
    running: { texto: 'En curso', simbolo: '◌', color: '#096dd9', fondo: '#e6f7ff', borde: '#91d5ff' },
}

const DESCONOCIDO = {
    simbolo: '?',
    color: 'rgba(0,0,0,.45)',
    fondo: '#fafafa',
    borde: '#d9d9d9',
}

/**
 * Texto visible de un estado ('success' → 'Éxito').
 * Si llega uno que no conocemos, se devuelve tal cual: así la búsqueda
 * por texto sigue encontrándolo aunque no tenga color asignado.
 */
export function etiquetaEstado(estado) {
    return ESTADOS[estado]?.texto || estado || ''
}

const EstadoTag = ({ estado }) => {
    const config = ESTADOS[estado] || { ...DESCONOCIDO, texto: estado || 'Sin estado' }

    return (
        <span
            className="estado-tag"
            style={{
                color: config.color,
                background: config.fondo,
                borderColor: config.borde,
            }}
        >
            <span aria-hidden="true">{config.simbolo}</span>
            {config.texto}
        </span>
    )
}

export default EstadoTag
