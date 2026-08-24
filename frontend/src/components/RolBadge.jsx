import { ROLES_INFO } from '@/config/roles'
import './rol-badge.css'

const DESCONOCIDO = {
    color: 'rgba(0,0,0,.45)',
    fondo: '#fafafa',
    borde: '#d9d9d9',
}

/** Insignia del rol de un usuario. Compartida por el header y la tabla de Usuarios. */
const RolBadge = ({ rol }) => {
    const info = ROLES_INFO[rol]
    const estilo = info || DESCONOCIDO

    return (
        <span
            className="rol-badge"
            style={{
                color: estilo.color,
                background: estilo.fondo,
                borderColor: estilo.borde,
            }}
        >
            {info ? info.label : rol || 'Sin rol'}
        </span>
    )
}

export default RolBadge
