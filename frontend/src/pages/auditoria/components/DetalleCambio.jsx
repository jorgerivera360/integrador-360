import { useState } from 'react'
import { IconAntes, IconCheck, IconDespues, IconEquis } from '../icons'

/** Formatea un valor para mostrarlo legible en la tabla. */
function formatearValor(valor) {
    if (valor === null || valor === undefined) return '—'
    if (valor === true) return 'Sí'
    if (valor === false) return 'No'
    if (typeof valor === 'object') return null // se maneja aparte como JSON colapsable
    return String(valor)
}

/** Detecta si un valor es un objeto/array complejo. */
function esComplejo(valor) {
    return valor !== null && typeof valor === 'object'
}

/** Bloque colapsable de JSON para valores complejos. */
const JsonColapsable = ({ valor }) => {
    const [abierto, setAbierto] = useState(false)
    const json = JSON.stringify(valor, null, 2)
    const lineas = json.split('\n').length

    if (lineas <= 3) {
        return <pre className="detalle-json-inline">{json}</pre>
    }

    return (
        <div>
            <button
                type="button"
                className="detalle-btn-expandir"
                onClick={() => setAbierto(!abierto)}
            >
                {abierto ? '▾ Ocultar' : `▸ Ver detalle (${lineas} líneas)`}
            </button>
            {abierto && <pre className="detalle-json-bloque">{json}</pre>}
        </div>
    )
}

/** Celda que muestra un valor simple o un JSON colapsable. */
const CeldaValor = ({ valor }) => {
    if (esComplejo(valor)) return <JsonColapsable valor={valor} />
    return <span className={valor === '—' ? 'celda-tenue' : ''}>{formatearValor(valor)}</span>
}

/** Encabezado del panel con ícono y título. */
const Encabezado = ({ tono, icono, titulo, subtitulo }) => (
    <div className={`detalle-header detalle-header--${tono}`}>
        {icono}
        <div>
            <div>{titulo}</div>
            {subtitulo && <div className="detalle-header__sub">{subtitulo}</div>}
        </div>
    </div>
)

/** Tabla de un solo lado: Campo | Valor. */
const TablaSingle = ({ datos, tono, icono, titulo, subtitulo }) => {
    const campos = Object.entries(datos)
    if (!campos.length) return <div className="detalle-cambio__vacio">Sin detalle registrado.</div>

    return (
        <div className={`detalle-panel detalle-panel--${tono}`}>
            <Encabezado tono={tono} icono={icono} titulo={titulo} subtitulo={subtitulo} />
            <table className="detalle-tabla">
                <thead>
                    <tr>
                        <th>Campo</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
                    {campos.map(([campo, valor]) => (
                        <tr key={campo}>
                            <td className="detalle-tabla__campo">{campo}</td>
                            <td><CeldaValor valor={valor} /></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

/** Tabla diff: Campo | Antes | Después. */
const TablaDiff = ({ antes, despues }) => {
    const camposTodos = new Set([
        ...Object.keys(antes || {}),
        ...Object.keys(despues || {}),
    ])
    const campos = [...camposTodos]

    if (!campos.length) return <div className="detalle-cambio__vacio">Sin detalle registrado.</div>

    return (
        <div className="detalle-panel detalle-panel--diff">
            <Encabezado
                tono="diff"
                icono={<IconDespues />}
                titulo="Cambios realizados"
            />
            <table className="detalle-tabla detalle-tabla--diff">
                <thead>
                    <tr>
                        <th>Campo</th>
                        <th className="detalle-tabla__col-antes">Antes</th>
                        <th className="detalle-tabla__col-despues">Después</th>
                    </tr>
                </thead>
                <tbody>
                    {campos.map((campo) => {
                        const valAntes = antes?.[campo]
                        const valDespues = despues?.[campo]
                        return (
                            <tr key={campo}>
                                <td className="detalle-tabla__campo">{campo}</td>
                                <td className="detalle-tabla__celda-antes">
                                    <CeldaValor valor={valAntes ?? '—'} />
                                </td>
                                <td className="detalle-tabla__celda-despues">
                                    <CeldaValor valor={valDespues ?? '—'} />
                                </td>
                            </tr>
                        )
                    })}
                </tbody>
            </table>
        </div>
    )
}

const DetalleCambio = ({ cambio }) => {
    if (cambio.action === 'create') {
        if (!cambio.changed_fields) {
            return <div className="detalle-cambio__vacio">Sin detalle registrado.</div>
        }
        return (
            <div className="detalle-cambio">
                <TablaSingle
                    datos={cambio.changed_fields}
                    tono="despues"
                    icono={<IconCheck />}
                    titulo="Registro creado"
                />
            </div>
        )
    }

    if (cambio.action === 'delete') {
        if (!cambio.previous_values) {
            return <div className="detalle-cambio__vacio">Sin detalle registrado.</div>
        }
        return (
            <div className="detalle-cambio">
                <TablaSingle
                    datos={cambio.previous_values}
                    tono="antes"
                    icono={<IconEquis />}
                    titulo="Registro eliminado"
                    subtitulo="Último estado antes de ser eliminado"
                />
            </div>
        )
    }

    // update
    if (!cambio.previous_values && !cambio.changed_fields) {
        return <div className="detalle-cambio__vacio">Sin detalle registrado.</div>
    }

    return (
        <div className="detalle-cambio">
            <TablaDiff antes={cambio.previous_values} despues={cambio.changed_fields} />
        </div>
    )
}

export default DetalleCambio
