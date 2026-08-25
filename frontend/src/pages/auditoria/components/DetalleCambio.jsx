import { IconAntes, IconCheck, IconDespues, IconEquis } from '../icons'

const comoJson = (valor) => {
    if (valor === null || valor === undefined) return null
    try {
        return JSON.stringify(valor, null, 2)
    } catch {
        return String(valor)
    }
}

const PanelJson = ({ tono, icono, titulo, subtitulo, contenido, solo }) => (
    <div className={`panel-json panel-json--${tono}${solo ? ' panel-json--solo' : ''}`}>
        <div className="panel-json__head">
            {icono}
            <div>
                <div>{titulo}</div>
                {subtitulo && <div className="panel-json__sub">{subtitulo}</div>}
            </div>
        </div>
        <div className="panel-json__cuerpo">
            <pre>{contenido}</pre>
        </div>
    </div>
)

/**
 * Contenido expandido de una fila del historial.
 *
 * La forma cambia según la acción, porque los datos que guarda la API son
 * distintos en cada caso (api/routes/flows.py):
 *   create → solo changed_fields
 *   update → previous_values y changed_fields, uno al lado del otro
 *   delete → solo previous_values, la instantánea previa al borrado
 */
const DetalleCambio = ({ cambio }) => {
    const antes = comoJson(cambio.previous_values)
    const despues = comoJson(cambio.changed_fields)

    if (cambio.action === 'create') {
        if (!despues) return <div className="detalle-cambio__vacio">Sin detalle registrado.</div>

        return (
            <div className="detalle-cambio">
                <PanelJson
                    tono="despues"
                    solo
                    icono={<IconCheck />}
                    titulo="Registro creado"
                    contenido={despues}
                />
            </div>
        )
    }

    if (cambio.action === 'delete') {
        if (!antes) return <div className="detalle-cambio__vacio">Sin detalle registrado.</div>

        return (
            <div className="detalle-cambio">
                <PanelJson
                    tono="antes"
                    solo
                    icono={<IconEquis />}
                    titulo="Registro eliminado"
                    subtitulo="Instantánea del registro antes de ser eliminado"
                    contenido={antes}
                />
            </div>
        )
    }

    // update — y cualquier acción desconocida que traiga ambos lados
    if (!antes && !despues) {
        return <div className="detalle-cambio__vacio">Sin detalle registrado.</div>
    }

    return (
        <div className="detalle-cambio">
            <div className="diff">
                <PanelJson
                    tono="antes"
                    icono={<IconAntes />}
                    titulo="Antes"
                    contenido={antes ?? '—'}
                />
                <PanelJson
                    tono="despues"
                    icono={<IconDespues />}
                    titulo="Después"
                    contenido={despues ?? '—'}
                />
            </div>
        </div>
    )
}

export default DetalleCambio
