import './tags.css'

const ACTIVO = { texto: 'Activo', color: '#389e0d', fondo: '#f6ffed', borde: '#b7eb8f', punto: '#52c41a' }
const INACTIVO = { texto: 'Inactivo', color: '#595959', fondo: '#fafafa', borde: '#d9d9d9', punto: '#bfbfbf' }

/** Etiqueta activo/inactivo con punto de color. */
const ActivoTag = ({ activo }) => {
    const estilo = activo ? ACTIVO : INACTIVO

    return (
        <span
            className="tag-base"
            style={{
                color: estilo.color,
                background: estilo.fondo,
                borderColor: estilo.borde,
            }}
        >
            <span className="tag-base__punto" style={{ background: estilo.punto }} />
            {estilo.texto}
        </span>
    )
}

export default ActivoTag
