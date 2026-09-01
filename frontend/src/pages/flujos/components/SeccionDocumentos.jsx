import { Button, Input, Select, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import { IconEliminar } from '../icons'
import TablaClaveValor from './TablaClaveValor'

const OPERADORES = [
    { value: 'contiene', label: 'contiene' },
    { value: 'empieza_con', label: 'empieza con' },
    { value: '=', label: 'es igual a' },
    { value: '!=', label: 'es distinto de' },
    { value: 'in', label: 'está en la lista' },
]

const ANCHO_CAMPO = 220
const ANCHO_OPERADOR = 150
const ANCHO_VALOR = 220

const LineaCondicion = ({ condicion, onChange, onEliminar }) => (
    <div className="flujo-regla-linea">
        <Input
            size="small"
            style={{ width: ANCHO_CAMPO }}
            value={condicion.campo}
            onChange={(e) => onChange({ ...condicion, campo: e.target.value })}
        />
        <Select
            size="small"
            style={{ width: ANCHO_OPERADOR }}
            value={condicion.operador || 'contiene'}
            options={OPERADORES}
            onChange={(valor) => onChange({ ...condicion, operador: valor })}
        />
        <Input
            size="small"
            style={{ width: ANCHO_VALOR }}
            value={condicion.valor}
            onChange={(e) => onChange({ ...condicion, valor: e.target.value })}
        />
        {onEliminar ? (
            <button className="flujo-tcv__eliminar" onClick={onEliminar} type="button" title="Eliminar filtro">
                <IconEliminar />
            </button>
        ) : (
            <span style={{ width: 32 }} />
        )}
    </div>
)

const EncabezadoCondicion = () => (
    <div className="flujo-regla-linea">
        <span className="flujo-regla-etiqueta" style={{ width: ANCHO_CAMPO }}>Campo</span>
        <span className="flujo-regla-etiqueta" style={{ width: ANCHO_OPERADOR }}>Operador</span>
        <span className="flujo-regla-etiqueta" style={{ width: ANCHO_VALOR }}>Valor</span>
        <span style={{ width: 32 }} />
    </div>
)

const BloqueDocumento = ({ documento, indice, onChange, onEliminar }) => {
    const cambiar = (campo, valor) => onChange(indice, { ...documento, [campo]: valor })
    const filtros = documento.filtros || []

    const cambiarFiltro = (i, nuevo) => {
        cambiar('filtros', filtros.map((f, j) => (j === i ? nuevo : f)))
    }
    const eliminarFiltro = (i) => {
        cambiar('filtros', filtros.filter((_, j) => j !== i))
    }
    const agregarFiltro = () => {
        cambiar('filtros', [...filtros, { campo: '', operador: '=', valor: '' }])
    }

    return (
        <div className="flujo-condicional flujo-condicional--documento">
            <div className="flujo-doc__bloque">
                <div className="flujo-doc__cabecera">
                    <h4 className="flujo-seccion__subtitulo">
                        Documento a personalizar{' '}
                        <Tooltip title="Identifica cuáles de las filas que trae el flujo pertenecen a este documento. En Campo va el nombre del campo que contiene el tipo de documento, tal como queda después del mapeo; si el flujo no tiene mapeo configurado, se usa el nombre original que envía el ERP. En Valor va el tipo de documento que se quiere personalizar, por ejemplo CPV o CDC. Cuando una fila cumple la condición de varios documentos, se aplica el primero de la lista.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </h4>
                    <button
                        className="flujo-tcv__eliminar"
                        onClick={() => onEliminar(indice)}
                        type="button"
                        title="Eliminar documento"
                    >
                        <IconEliminar />
                    </button>
                </div>
                <EncabezadoCondicion />
                <LineaCondicion
                    condicion={{
                        campo: documento.ident_campo || '',
                        operador: documento.ident_operador || 'contiene',
                        valor: documento.ident_valor || '',
                    }}
                    onChange={(c) => onChange(indice, {
                        ...documento,
                        ident_campo: c.campo,
                        ident_operador: c.operador,
                        ident_valor: c.valor,
                    })}
                />
            </div>

            <div className="flujo-doc__grupo">
                <h4 className="flujo-seccion__subtitulo">
                    Acciones de personalización{' '}
                    <Tooltip title="Define qué se hace con las filas identificadas arriba. Los filtros deciden cuáles de esas filas llegan al WMS y cuáles se descartan; los valores fijos cambian el contenido de sus campos antes de enviarlas. Ambas cosas aplican únicamente a este documento: el resto de las filas del flujo no se ve afectado.">
                        <InfoCircleOutlined className="flujo-seccion__info" />
                    </Tooltip>
                </h4>

                <div className="flujo-doc__bloque">
                    <div className="flujo-doc__etiqueta">
                        Filtros{' '}
                        <Tooltip title="Condiciones que las filas de este documento deben cumplir para llegar al WMS. Se evalúan todas: si alguna no se cumple, la fila se descarta y queda registrada en el log con el motivo del descarte. Sin filtros configurados, todas las filas del documento se cargan.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </div>

                    {filtros.length > 0 && <EncabezadoCondicion />}
                    {filtros.map((f, i) => (
                        <LineaCondicion
                            key={i}
                            condicion={f}
                            onChange={(nuevo) => cambiarFiltro(i, nuevo)}
                            onEliminar={() => eliminarFiltro(i)}
                        />
                    ))}
                    {filtros.length === 0 && (
                        <div className="flujo-doc__vacio">
                            Sin filtros configurados: se cargan todas las filas de este documento
                        </div>
                    )}

                    <div className="flujo-condicional__acciones">
                        <Button type="dashed" size="small" onClick={agregarFiltro}>
                            + Agregar filtro
                        </Button>
                    </div>
                </div>

                <div className="flujo-doc__bloque">
                    <div className="flujo-doc__etiqueta">
                        Valores fijos{' '}
                        <Tooltip title="Valores que se fijan en los campos indicados para todas las filas de este documento. Sobreescriben lo que traiga el ERP y también los valores fijos generales del flujo. Es lo que permite, por ejemplo, que un tipo de documento llegue al WMS en estado sale mientras el resto llega en draft.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </div>
                    <div className="flujo-doc__tabla">
                        <TablaClaveValor
                            columnas={['Campo', 'Valor']}
                            datos={documento.hardcodes || []}
                            onChange={(nuevos) => cambiar('hardcodes', nuevos)}
                        />
                    </div>
                </div>
            </div>
        </div>
    )
}

const SeccionDocumentos = ({ config, onChange }) => {
    const documentos = config.documentos_tabla || []

    const cambiar = (indice, nuevo) => {
        onChange({
            ...config,
            documentos_tabla: documentos.map((d, i) => (i === indice ? nuevo : d)),
        })
    }

    const eliminar = (indice) => {
        onChange({
            ...config,
            documentos_tabla: documentos.filter((_, i) => i !== indice),
        })
    }

    const agregar = () => {
        onChange({
            ...config,
            documentos_tabla: [...documentos, {
                ident_campo: '',
                ident_operador: 'contiene',
                ident_valor: '',
                filtros: [],
                hardcodes: [],
            }],
        })
    }

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Personalización por tipo de documento{' '}
                <Tooltip title="Un mismo flujo suele traer varios tipos de documento que necesitan un tratamiento distinto: unos deben cargarse solo bajo ciertas condiciones y otros deben llegar al WMS con valores diferentes. Esta sección define ese tratamiento sin duplicar el flujo ni la consulta al ERP: se hace una sola consulta y cada fila se clasifica según el tipo de documento al que pertenece. Las filas que no coincidan con ningún documento configurado se cargan sin ninguna modificación, de modo que personalizar un tipo no excluye a los demás.">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            <div>
                {documentos.map((doc, i) => (
                    <BloqueDocumento
                        key={i}
                        documento={doc}
                        indice={i}
                        onChange={cambiar}
                        onEliminar={eliminar}
                    />
                ))}

                {documentos.length === 0 && (
                    <div className="flujo-doc__vacio">Sin documentos configurados</div>
                )}

                <div className="flujo-condicional__acciones">
                    <Button type="dashed" size="small" onClick={agregar}>
                        + Agregar documento
                    </Button>
                </div>
            </div>
        </div>
    )
}

export default SeccionDocumentos
