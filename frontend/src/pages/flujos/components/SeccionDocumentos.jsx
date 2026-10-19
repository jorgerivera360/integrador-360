import { useState } from 'react'
import { Button, Input, InputNumber, Select, Switch, Tooltip } from 'antd'
import { InfoCircleOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import TablaClaveValor from './TablaClaveValor'

const OPERADORES = [
    { value: '=', label: 'es igual a' },
    { value: '!=', label: 'es distinto de' },
    { value: 'in', label: 'est\u00e1 en la lista' },
    { value: 'contiene', label: 'contiene' },
    { value: 'empieza_con', label: 'empieza con' },
]

function getLabelOrden(flowType) {
    return flowType === 'purchases' ? 'Orden de compra' : 'Orden de venta'
}

function getResumenRegla(regla, flowType) {
    const estado = regla.estado || 'draft'
    if (regla.crear_como === 'picking_direct') {
        return { tipo: 'picking', texto: `Picking directo \u00b7 ${estado}` }
    }
    return { tipo: 'orden', texto: `${getLabelOrden(flowType)} \u00b7 ${estado}` }
}

// ─── Iconos ───

const IconChevron = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 6l6 6-6 6" />
    </svg>
)

const IconOrden = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <path d="M7 3h10l2 3v15H5V6z" /><path d="M9 10h6M9 14h6M9 18h3" />
    </svg>
)

const IconPicking = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 8l-9-5-9 5v8l9 5 9-5z" /><path d="M3 8l9 5 9-5M12 13v8" />
    </svg>
)

// ─── Pill de resumen ───

const PillResumen = ({ regla, flowType }) => {
    const { tipo, texto } = getResumenRegla(regla, flowType)
    return <span className={`doc-pill doc-pill--${tipo}`}>{texto}</span>
}

// ─── L\u00ednea de condici\u00f3n ───

const LineaCondicion = ({ condicion, onChange, onEliminar }) => (
    <div className="doc-cond">
        <Input
            size="small"
            className="doc-cond__campo"
            value={condicion.campo}
            onChange={(e) => onChange({ ...condicion, campo: e.target.value })}
            placeholder="campo"
        />
        <Select
            size="small"
            className="doc-cond__op"
            popupMatchSelectWidth={false}
            value={condicion.operador || '='}
            options={OPERADORES}
            onChange={(v) => onChange({ ...condicion, operador: v })}
        />
        <Input
            size="small"
            className="doc-cond__valor"
            value={condicion.valor}
            onChange={(e) => onChange({ ...condicion, valor: e.target.value })}
            placeholder={condicion.operador === 'in' ? 'val1, val2, val3' : 'valor'}
        />
        {onEliminar && (
            <button className="doc-btn-x doc-btn-x--borrar" onClick={onEliminar} type="button" title="Quitar">
                <DeleteOutlined />
            </button>
        )}
    </div>
)

// ─── Tarjetas de destino ───

const TarjetaDestino = ({ tipo, seleccionado, onSelect, flowType }) => {
    const esOrden = tipo === 'order'
    return (
        <button
            type="button"
            className={`doc-destino-card ${seleccionado ? 'doc-destino-card--sel' : ''}`}
            onClick={onSelect}
        >
            <span className="doc-destino-card__ico">
                {esOrden ? <IconOrden /> : <IconPicking />}
            </span>
            <div style={{ textAlign: 'left' }}>
                <div className="doc-destino-card__titulo">
                    {esOrden ? getLabelOrden(flowType) : 'Picking directo'}
                </div>
                <div className="doc-destino-card__desc">
                    {esOrden
                        ? 'El WMS genera los movimientos cuando la orden se confirma'
                        : 'Se crea el movimiento de inventario sin pasar por una orden'}
                </div>
            </div>
        </button>
    )
}

// ─── Bloque de una regla ───

const BloqueRegla = ({ regla, indice, total, onChange, onEliminar, onSubir, onBajar, flowType }) => {
    const [extrasAbierto, setExtrasAbierto] = useState((regla.hardcodes || []).length > 0)
    const cambiar = (campo, valor) => onChange({ ...regla, [campo]: valor })

    const esPicking = (regla.crear_como || 'order') === 'picking_direct'

    const filtros = regla.filtros || []
    const cambiarFiltro = (i, nuevo) => {
        const nuevos = filtros.map((f, j) => j === i ? nuevo : f)
        cambiar('filtros', nuevos)
    }
    const eliminarFiltro = (i) => {
        cambiar('filtros', filtros.filter((_, j) => j !== i))
    }
    const agregarFiltro = () => {
        cambiar('filtros', [...filtros, { campo: '', operador: '=', valor: '' }])
    }

    const cantExtras = (regla.hardcodes || []).filter((h) => h.clave?.trim()).length

    const seleccionarDestino = (tipo) => {
        cambiar('crear_como', tipo)
    }

    return (
        <div className="doc-regla">
            <div className="doc-regla__riel">
                <span className="doc-regla__conector">{indice === 0 ? 'SI' : 'SI NO'}</span>
                <span className="doc-regla__linea" />
            </div>
            <div className="doc-regla__caja">
                <div className="doc-regla__top">
                    <span className="doc-regla__frase">
                        Traer la fila cuando se cumpla <strong>todo</strong> esto:
                    </span>
                    <div className="doc-regla__botones">
                        {total > 1 && (
                            <>
                                <button type="button" className="doc-btn-x" onClick={onSubir} disabled={indice === 0} title="Subir">&#x25B2;</button>
                                <button type="button" className="doc-btn-x" onClick={onBajar} disabled={indice === total - 1} title="Bajar">&#x25BC;</button>
                                <button type="button" className="doc-btn-x doc-btn-x--borrar" onClick={onEliminar} title="Eliminar regla">
                                    <DeleteOutlined />
                                </button>
                            </>
                        )}
                    </div>
                </div>

                {/* Criterios */}
                <div className="doc-regla__criterios">
                    {filtros.map((f, i) => (
                        <LineaCondicion
                            key={i}
                            condicion={f}
                            onChange={(n) => cambiarFiltro(i, n)}
                            onEliminar={filtros.length > 1 ? () => eliminarFiltro(i) : undefined}
                        />
                    ))}
                    {filtros.length === 0 && (
                        <div className="doc-vacio">Sin criterios: todas las filas de este documento pasan</div>
                    )}
                    <Button type="dashed" size="small" onClick={agregarFiltro} icon={<PlusOutlined />} style={{ marginTop: 6 }}>
                        Agregar condici&oacute;n
                    </Button>
                </div>

                <div className="doc-regla__sep" />

                {/* Destino */}
                <div className="doc-label">Crear en el WMS como</div>
                <div className="doc-destinos">
                    <TarjetaDestino
                        tipo="order"
                        seleccionado={!esPicking}
                        onSelect={() => seleccionarDestino('order')}
                        flowType={flowType}
                    />
                    <TarjetaDestino
                        tipo="picking_direct"
                        seleccionado={esPicking}
                        onSelect={() => seleccionarDestino('picking_direct')}
                        flowType={flowType}
                    />
                </div>

                {/* Estado + Tipo de operaci\u00f3n */}
                <div className="doc-config-fila">
                    <div className="doc-config-campo">
                        <label className="doc-label">
                            Estado inicial{' '}
                            <Tooltip title="Estado con el que se crea el documento en WMS. Ejemplos: draft (borrador), assigned (listo para despachar), confirmed (confirmado). El valor se env&iacute;a tal cual al WMS.">
                                <InfoCircleOutlined className="flujo-seccion__info" />
                            </Tooltip>
                        </label>
                        <Input
                            size="small"
                            style={{ width: 150 }}
                            value={regla.estado || ''}
                            onChange={(e) => cambiar('estado', e.target.value)}
                            placeholder="draft"
                        />
                    </div>
                    <div className="doc-config-campo">
                        <label className="doc-label">
                            Tipo de operaci&oacute;n (ID){' '}
                            <Tooltip title="ID del tipo de operaci&oacute;n en WMS (Inventario &gt; Configuraci&oacute;n &gt; Tipos de operaci&oacute;n). Define las ubicaciones origen/destino del movimiento.">
                                <InfoCircleOutlined className="flujo-seccion__info" />
                            </Tooltip>
                        </label>
                        <InputNumber
                            size="small"
                            style={{ width: 100 }}
                            min={1}
                            value={regla.operacion_id || undefined}
                            onChange={(v) => cambiar('operacion_id', v)}
                            placeholder="ID"
                        />
                    </div>
                    {esPicking && (
                        <div className="doc-config-campo doc-config-campo--switch">
                            <Switch
                                size="small"
                                checked={regla.sin_reserva || false}
                                onChange={(v) => cambiar('sin_reserva', v)}
                            />
                            <label className="doc-label" style={{ marginBottom: 0 }}>
                                Quitar reserva{' '}
                                <Tooltip title="Despu&eacute;s de crear y confirmar el picking, quita la reserva de stock autom&aacute;ticamente (do_unreserve). &Uacute;til para traslados de separaci&oacute;n donde el stock debe quedar bloqueado.">
                                    <InfoCircleOutlined className="flujo-seccion__info" />
                                </Tooltip>
                            </label>
                        </div>
                    )}
                </div>

                {/* Valores fijos */}
                <div className="doc-extras">
                    <span className="doc-extras__toggle" onClick={() => setExtrasAbierto(!extrasAbierto)}>
                        <span className={`doc-extras__chevron ${extrasAbierto ? 'doc-extras__chevron--open' : ''}`}>
                            <IconChevron />
                        </span>
                        Valores fijos adicionales
                        {cantExtras > 0 && <span className="doc-extras__count">{cantExtras}</span>}
                    </span>
                    {extrasAbierto && (
                        <div className="doc-extras__cuerpo">
                            <TablaClaveValor
                                columnas={['Campo', 'Valor fijo']}
                                datos={regla.hardcodes || []}
                                onChange={(v) => cambiar('hardcodes', v)}
                                placeholders={['cliente', '800007355']}
                            />
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

// ─── Bloque de un documento (acorde\u00f3n) ───

const BloqueDocumento = ({ documento, indice, onChange, onEliminar, flowType }) => {
    const [abierto, setAbierto] = useState(!documento.ident_valor)
    const cambiar = (campo, valor) => onChange(indice, { ...documento, [campo]: valor })

    const reglas = documento.reglas && documento.reglas.length > 0
        ? documento.reglas
        : [{
            filtros: documento.filtros || [],
            hardcodes: documento.hardcodes || [],
            crear_como: documento.crear_como || 'order',
            estado: documento.estado || 'draft',
            operacion_id: documento.operacion_id || '',
            sin_reserva: documento.sin_reserva || false,
        }]

    const cambiarRegla = (i, nueva) => {
        const nuevas = reglas.map((r, j) => j === i ? nueva : r)
        cambiar('reglas', nuevas)
        if (nuevas.length > 1) cambiar('tiene_variantes', true)
    }

    const eliminarRegla = (i) => {
        const nuevas = reglas.filter((_, j) => j !== i)
        cambiar('reglas', nuevas)
        cambiar('tiene_variantes', nuevas.length > 1)
    }

    const subirRegla = (i) => {
        if (i === 0) return
        const nuevas = [...reglas]
        ;[nuevas[i - 1], nuevas[i]] = [nuevas[i], nuevas[i - 1]]
        cambiar('reglas', nuevas)
    }

    const bajarRegla = (i) => {
        if (i >= reglas.length - 1) return
        const nuevas = [...reglas]
        ;[nuevas[i], nuevas[i + 1]] = [nuevas[i + 1], nuevas[i]]
        cambiar('reglas', nuevas)
    }

    const agregarRegla = () => {
        cambiar('reglas', [...reglas, {
            filtros: [{ campo: '', operador: '=', valor: '' }],
            hardcodes: [],
            crear_como: 'order',
            estado: 'draft',
            operacion_id: '',
            sin_reserva: false,
        }])
        cambiar('tiene_variantes', true)
    }

    const nombre = documento.doc_nombre || documento.ident_valor || ''
    const codigo = documento.ident_valor || ''

    return (
        <div className={`doc-acordeon ${abierto ? 'doc-acordeon--open' : ''}`}>
            {/* Cabecera colapsable */}
            <div
                className="doc-acordeon__head"
                onClick={(e) => {
                    // No colapsar si clickeó el botón eliminar
                    if (e.target.closest('.doc-btn-x')) return
                    setAbierto(!abierto)
                }}
            >
                <span className="doc-acordeon__chevron"><IconChevron /></span>
                {codigo && <span className="doc-acordeon__code">{codigo}</span>}
                <div className="doc-acordeon__titulos">
                    <div className="doc-acordeon__nombre">{nombre || 'Nuevo documento'}</div>
                    {(documento.ident_campo || codigo) && (
                        <div className="doc-acordeon__ident">
                            {documento.ident_campo || '???'} = {codigo || '???'}
                        </div>
                    )}
                </div>
                <div className="doc-acordeon__resumen">
                    {reglas.map((r, i) => (
                        <PillResumen key={i} regla={r} flowType={flowType} />
                    ))}
                </div>
                <button
                    type="button"
                    className="doc-btn-x doc-btn-x--borrar"
                    onClick={(e) => { e.stopPropagation(); onEliminar(indice) }}
                    title="Eliminar documento"
                >
                    <DeleteOutlined />
                </button>
            </div>

            {/* Cuerpo */}
            {abierto && (
                <div className="doc-acordeon__body">
                    {/* Datos del documento */}
                    <div className="doc-datos">
                        <div className="doc-config-campo">
                            <label className="doc-label">Nombre del documento</label>
                            <Input
                                size="small"
                                value={documento.doc_nombre || ''}
                                onChange={(e) => cambiar('doc_nombre', e.target.value)}
                                placeholder="Ej: Orden Compra Nacional"
                            />
                        </div>
                        <div className="doc-config-campo">
                            <label className="doc-label">
                                Se reconoce cuando{' '}
                                <Tooltip title="Campo del dato (despu&eacute;s del mapeo) que identifica el tipo de documento. Todas las filas donde este campo coincida se procesan con las reglas de abajo.">
                                    <InfoCircleOutlined className="flujo-seccion__info" />
                                </Tooltip>
                            </label>
                            <div className="doc-ident">
                                <Input
                                    size="small"
                                    className="doc-ident__campo"
                                    value={documento.ident_campo || ''}
                                    onChange={(e) => cambiar('ident_campo', e.target.value)}
                                    placeholder="tipo_docto"
                                />
                                <Select
                                    size="small"
                                    className="doc-ident__op"
                                    popupMatchSelectWidth={false}
                                    value={documento.ident_operador || '='}
                                    options={OPERADORES}
                                    onChange={(v) => cambiar('ident_operador', v)}
                                />
                                <Input
                                    size="small"
                                    className="doc-ident__valor"
                                    value={documento.ident_valor || ''}
                                    onChange={(e) => cambiar('ident_valor', e.target.value)}
                                    placeholder="OCN"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Reglas */}
                    <div className="doc-label" style={{ marginTop: 16 }}>
                        Reglas{' '}
                        <Tooltip title="Las reglas se eval&uacute;an de arriba hacia abajo. La primera que se cumpla decide qu&eacute; se crea en el WMS. Las filas que no coincidan con ninguna regla se descartan.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </div>
                    <div className="doc-reglas">
                        {reglas.map((regla, i) => (
                            <BloqueRegla
                                key={i}
                                regla={regla}
                                indice={i}
                                total={reglas.length}
                                onChange={(nueva) => cambiarRegla(i, nueva)}
                                onEliminar={() => eliminarRegla(i)}
                                onSubir={() => subirRegla(i)}
                                onBajar={() => bajarRegla(i)}
                                flowType={flowType}
                            />
                        ))}

                        {/* Conector final */}
                        <div className="doc-regla-fin">
                            <span className="doc-regla__conector doc-regla__conector--fin">FIN</span>
                            <span className="doc-regla-fin__texto">
                                Las filas que no cumplan ninguna regla se descartan
                            </span>
                        </div>

                        <Button
                            type="dashed"
                            size="small"
                            onClick={agregarRegla}
                            icon={<PlusOutlined />}
                            style={{ marginTop: 10, marginLeft: 50 }}
                        >
                            Agregar regla
                        </Button>
                    </div>
                </div>
            )}
        </div>
    )
}

// ─── Secci\u00f3n principal ───

const SeccionDocumentos = ({ config, onChange, flowType }) => {
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
                doc_nombre: '',
                ident_campo: '',
                ident_operador: '=',
                ident_valor: '',
                filtros: [],
                hardcodes: [],
                crear_como: 'order',
                estado: 'draft',
                operacion_id: '',
                sin_reserva: false,
                tiene_variantes: false,
                reglas: [],
            }],
        })
    }

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Tipos de documento{' '}
                <Tooltip title="Un mismo SQL puede traer varios tipos de documento del ERP. Para cada tipo defines c&oacute;mo se reconoce, qu&eacute; filas se traen y qu&eacute; se crea en el WMS. Las filas que no coincidan con ning&uacute;n documento pasan sin modificaci&oacute;n.">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            <div className="doc-lista">
                {documentos.map((doc, i) => (
                    <BloqueDocumento
                        key={i}
                        documento={doc}
                        indice={i}
                        onChange={cambiar}
                        onEliminar={eliminar}
                        flowType={flowType}
                    />
                ))}

                {documentos.length === 0 && (
                    <div className="doc-vacio">
                        Sin tipos de documento configurados &mdash; todas las filas se procesan de la misma forma.
                    </div>
                )}

                <button type="button" className="doc-btn-agregar" onClick={agregar}>
                    <PlusOutlined /> Agregar tipo de documento
                </button>
            </div>
        </div>
    )
}

export default SeccionDocumentos
