import { useState } from 'react'
import { Button, Checkbox, Collapse, Input, InputNumber, Select, Tooltip } from 'antd'
import { InfoCircleOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import TablaClaveValor from './TablaClaveValor'

const OPERADORES = [
    { value: 'contiene', label: 'contiene' },
    { value: 'empieza_con', label: 'empieza con' },
    { value: '=', label: 'es igual a' },
    { value: '!=', label: 'es distinto de' },
    { value: 'in', label: 'está en la lista' },
]

const OPCIONES_CREAR_COMO = [
    { value: 'order', label: 'Orden de compra/venta' },
    { value: 'picking_direct', label: 'Picking directo' },
]

const ESTADOS_POR_CREAR_COMO = {
    order: [
        { value: 'draft', label: 'Borrador' },
        { value: 'purchase', label: 'Confirmado (compra)' },
        { value: 'sale', label: 'Confirmado (venta)' },
    ],
    picking_direct: [
        { value: 'draft', label: 'Borrador' },
        { value: 'confirmed', label: 'Confirmado (en espera)' },
        { value: 'assigned', label: 'Listo' },
    ],
}

const ANCHO_CAMPO = 200
const ANCHO_OPERADOR = 150
const ANCHO_VALOR = 200

// ─── Componente de línea de condición (reutilizado en filtros e identificación) ───

const LineaCondicion = ({ condicion, onChange, onEliminar }) => (
    <div className="flujo-regla-linea">
        <Input
            size="small"
            style={{ width: ANCHO_CAMPO }}
            value={condicion.campo}
            onChange={(e) => onChange({ ...condicion, campo: e.target.value })}
            placeholder="campo"
        />
        <Select
            size="small"
            style={{ width: ANCHO_OPERADOR }}
            value={condicion.operador || '='}
            options={OPERADORES}
            onChange={(valor) => onChange({ ...condicion, operador: valor })}
        />
        <Input
            size="small"
            style={{ width: ANCHO_VALOR }}
            value={condicion.valor}
            onChange={(e) => onChange({ ...condicion, valor: e.target.value })}
            placeholder="valor"
        />
        {onEliminar ? (
            <button className="flujo-tcv__eliminar" onClick={onEliminar} type="button" title="Eliminar">
                <DeleteOutlined />
            </button>
        ) : (
            <span style={{ width: 32 }} />
        )}
    </div>
)

// ─── Bloque de configuración WMS (usado tanto en modo simple como en cada regla) ───

const BloqueConfigWMS = ({ datos, onChange, flowType }) => {
    const crearComo = datos.crear_como || 'order'
    const estadosDisponibles = ESTADOS_POR_CREAR_COMO[crearComo] || ESTADOS_POR_CREAR_COMO.order
    const esPicking = crearComo === 'picking_direct'

    // Si el estado actual no es válido para el crear_como seleccionado, resetear a draft
    const estadoActual = estadosDisponibles.some(e => e.value === datos.estado) ? datos.estado : 'draft'

    return (
        <div className="flujo-doc__config-wms">
            <div className="flujo-campos" style={{ gap: 12 }}>
                <div className="flujo-campo">
                    <label className="flujo-campo__label">Crear como</label>
                    <Select
                        size="small"
                        style={{ width: 220 }}
                        value={crearComo}
                        options={OPCIONES_CREAR_COMO}
                        onChange={(v) => onChange({
                            ...datos,
                            crear_como: v,
                            estado: 'draft',
                            operacion_id: v === 'picking_direct' ? datos.operacion_id : '',
                        })}
                    />
                </div>
                <div className="flujo-campo">
                    <label className="flujo-campo__label">Estado en WMS</label>
                    <Select
                        size="small"
                        style={{ width: 220 }}
                        value={estadoActual}
                        options={estadosDisponibles}
                        onChange={(v) => onChange({ ...datos, estado: v })}
                    />
                </div>
                {esPicking && (
                    <div className="flujo-campo">
                        <label className="flujo-campo__label">
                            ID Operación{' '}
                            <Tooltip title="ID del tipo de operación en WMS (stock.picking.type). Se obtiene en Inventario > Configuración > Tipos de operación. El picking se creará con las ubicaciones origen/destino de esta operación.">
                                <InfoCircleOutlined style={{ color: '#bfbfbf', fontSize: 13 }} />
                            </Tooltip>
                        </label>
                        <InputNumber
                            size="small"
                            style={{ width: 100 }}
                            min={1}
                            value={datos.operacion_id || undefined}
                            onChange={(v) => onChange({ ...datos, operacion_id: v })}
                            placeholder="ej: 9"
                        />
                    </div>
                )}
            </div>
        </div>
    )
}

// ─── Bloque de filtros (condiciones de entrada) ───

const BloqueFiltros = ({ filtros, onChange }) => {
    const cambiarFiltro = (i, nuevo) => onChange(filtros.map((f, j) => (j === i ? nuevo : f)))
    const eliminarFiltro = (i) => onChange(filtros.filter((_, j) => j !== i))
    const agregarFiltro = () => onChange([...filtros, { campo: '', operador: '=', valor: '' }])

    return (
        <div className="flujo-doc__bloque">
            <div className="flujo-doc__etiqueta">
                Condiciones de entrada{' '}
                <Tooltip title="Solo se procesan las filas que cumplan todas las condiciones. Las que no cumplan se descartan y quedan registradas en el log.">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </div>
            {filtros.length > 0 && filtros.map((f, i) => (
                <LineaCondicion
                    key={i}
                    condicion={f}
                    onChange={(nuevo) => cambiarFiltro(i, nuevo)}
                    onEliminar={() => eliminarFiltro(i)}
                />
            ))}
            {filtros.length === 0 && (
                <div className="flujo-doc__vacio">Sin condiciones: todas las filas pasan</div>
            )}
            <div className="flujo-condicional__acciones">
                <Button type="dashed" size="small" onClick={agregarFiltro} icon={<PlusOutlined />}>
                    Condición
                </Button>
            </div>
        </div>
    )
}

// ─── Bloque de warehouse mapping ───

const BloqueWarehouseMapping = ({ datos, onChange, flowType }) => {
    const esEntrada = flowType === 'purchases'
    const columnaOdoo = esEntrada ? 'ID Operación recepción' : 'ID Almacén WMS'

    return (
        <div className="flujo-doc__bloque">
            <div className="flujo-doc__etiqueta">
                Mapeo de almacenes{' '}
                <Tooltip title={esEntrada
                    ? 'Relaciona cada bodega del ERP con la operación de recepción en WMS. Si una bodega no está en la tabla, se usa la operación por defecto.'
                    : 'Relaciona cada bodega del ERP con el almacén en WMS. Si una bodega no está en la tabla, se usa el almacén principal.'
                }>
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </div>
            <div style={{ maxWidth: 450 }}>
                <TablaClaveValor
                    columnas={['Bodega ERP', columnaOdoo]}
                    datos={datos}
                    onChange={onChange}
                    placeholders={['M0101', '1']}
                />
            </div>
        </div>
    )
}

// ─── Bloque de una regla (dentro del modo variantes) ───

const BloqueRegla = ({ regla, indice, total, onChange, onEliminar, flowType }) => {
    const [camposFijosAbiertos, setCamposFijosAbiertos] = useState(
        (regla.hardcodes || []).length > 0
    )

    const cambiar = (campo, valor) => onChange({ ...regla, [campo]: valor })

    const etiqueta = indice === 0 ? 'Regla 1' : `Regla ${indice + 1} (si no entró en la anterior)`

    return (
        <div className="flujo-doc__regla">
            <div className="flujo-doc__regla-header">
                <span className="flujo-doc__regla-etiqueta">{etiqueta}</span>
                {total > 1 && (
                    <button className="flujo-tcv__eliminar" onClick={onEliminar} type="button" title="Eliminar regla">
                        <DeleteOutlined />
                    </button>
                )}
            </div>

            <BloqueFiltros
                filtros={regla.filtros || []}
                onChange={(v) => cambiar('filtros', v)}
            />

            <BloqueConfigWMS
                datos={regla}
                onChange={(nuevos) => onChange(nuevos)}
                flowType={flowType}
            />

            {regla.crear_como !== 'picking_direct' && (
                <BloqueWarehouseMapping
                    datos={regla.warehouse_mapping || []}
                    onChange={(v) => cambiar('warehouse_mapping', v)}
                    flowType={flowType}
                />
            )}

            <div className="flujo-doc__bloque">
                <Button
                    type="link"
                    size="small"
                    onClick={() => setCamposFijosAbiertos(!camposFijosAbiertos)}
                    style={{ padding: 0, fontSize: 13 }}
                >
                    {camposFijosAbiertos ? '▾' : '▸'} Campos fijos
                </Button>
                {camposFijosAbiertos && (
                    <div style={{ maxWidth: 450, marginTop: 8 }}>
                        <TablaClaveValor
                            columnas={['Campo', 'Valor']}
                            datos={regla.hardcodes || []}
                            onChange={(v) => cambiar('hardcodes', v)}
                        />
                    </div>
                )}
            </div>
        </div>
    )
}

// ─── Bloque de un documento completo ───

const BloqueDocumento = ({ documento, indice, onChange, onEliminar, flowType }) => {
    const cambiar = (campo, valor) => onChange(indice, { ...documento, [campo]: valor })
    const tieneVariantes = documento.tiene_variantes || false
    const [camposFijosAbiertos, setCamposFijosAbiertos] = useState(
        (documento.hardcodes || []).length > 0
    )

    const toggleVariantes = (checked) => {
        if (checked && (!documento.reglas || documento.reglas.length === 0)) {
            // Crear primera regla con los datos actuales del documento
            const primeraRegla = {
                filtros: documento.filtros || [],
                warehouse_mapping: documento.warehouse_mapping || [],
                hardcodes: documento.hardcodes || [],
                crear_como: documento.crear_como || 'order',
                estado: documento.estado || 'draft',
                operacion_id: documento.operacion_id || '',
            }
            cambiar('reglas', [primeraRegla])
        }
        cambiar('tiene_variantes', checked)
    }

    const cambiarRegla = (i, nueva) => {
        const reglas = [...(documento.reglas || [])]
        reglas[i] = nueva
        cambiar('reglas', reglas)
    }

    const eliminarRegla = (i) => {
        const reglas = (documento.reglas || []).filter((_, j) => j !== i)
        cambiar('reglas', reglas)
        if (reglas.length === 0) cambiar('tiene_variantes', false)
    }

    const agregarRegla = () => {
        cambiar('reglas', [...(documento.reglas || []), {
            filtros: [],
            warehouse_mapping: [],
            hardcodes: [],
            crear_como: 'order',
            estado: 'draft',
            operacion_id: '',
        }])
    }

    return (
        <div className="flujo-condicional flujo-condicional--documento">
            {/* Identificación */}
            <div className="flujo-doc__bloque">
                <div className="flujo-doc__cabecera">
                    <h4 className="flujo-seccion__subtitulo">
                        📌 Identificar{' '}
                        <Tooltip title="Identifica cuáles filas del flujo pertenecen a este documento. El campo usa el nombre después del mapeo. Si coincide con varios documentos, se aplica el primero de la lista.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </h4>
                    <button
                        className="flujo-tcv__eliminar"
                        onClick={() => onEliminar(indice)}
                        type="button"
                        title="Eliminar documento"
                    >
                        <DeleteOutlined />
                    </button>
                </div>
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

            {/* Modo simple (sin variantes) */}
            {!tieneVariantes && (
                <div className="flujo-doc__grupo">
                    <BloqueFiltros
                        filtros={documento.filtros || []}
                        onChange={(v) => cambiar('filtros', v)}
                    />

                    <BloqueConfigWMS
                        datos={documento}
                        onChange={(nuevos) => onChange(indice, { ...documento, ...nuevos })}
                        flowType={flowType}
                    />

                    {documento.crear_como !== 'picking_direct' && (
                        <BloqueWarehouseMapping
                            datos={documento.warehouse_mapping || []}
                            onChange={(v) => cambiar('warehouse_mapping', v)}
                            flowType={flowType}
                        />
                    )}

                    <div className="flujo-doc__bloque">
                        <Button
                            type="link"
                            size="small"
                            onClick={() => setCamposFijosAbiertos(!camposFijosAbiertos)}
                            style={{ padding: 0, fontSize: 13 }}
                        >
                            {camposFijosAbiertos ? '▾' : '▸'} Campos fijos
                        </Button>
                        {camposFijosAbiertos && (
                            <div style={{ maxWidth: 450, marginTop: 8 }}>
                                <TablaClaveValor
                                    columnas={['Campo', 'Valor']}
                                    datos={documento.hardcodes || []}
                                    onChange={(v) => cambiar('hardcodes', v)}
                                />
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Modo variantes (reglas if/elif) */}
            {tieneVariantes && (
                <div className="flujo-doc__grupo">
                    <div className="flujo-doc__vacio" style={{ color: '#8c8c8c', marginBottom: 8 }}>
                        Las reglas se evalúan en orden. La primera que coincida captura la fila. Si ninguna coincide, la fila se descarta.
                    </div>
                    {(documento.reglas || []).map((regla, i) => (
                        <BloqueRegla
                            key={i}
                            regla={regla}
                            indice={i}
                            total={(documento.reglas || []).length}
                            onChange={(nueva) => cambiarRegla(i, nueva)}
                            onEliminar={() => eliminarRegla(i)}
                            flowType={flowType}
                        />
                    ))}
                    <div className="flujo-condicional__acciones">
                        <Button type="dashed" size="small" onClick={agregarRegla} icon={<PlusOutlined />}>
                            Agregar regla
                        </Button>
                    </div>
                </div>
            )}

            {/* Toggle variantes */}
            <div style={{ padding: '8px 0 4px 0' }}>
                <Checkbox
                    checked={tieneVariantes}
                    onChange={(e) => toggleVariantes(e.target.checked)}
                >
                    Este documento tiene variantes (reglas avanzadas)
                </Checkbox>
            </div>
        </div>
    )
}

// ─── Sección principal ───

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
                ident_campo: '',
                ident_operador: 'contiene',
                ident_valor: '',
                filtros: [],
                warehouse_mapping: [],
                hardcodes: [],
                crear_como: 'order',
                estado: 'draft',
                operacion_id: '',
                tiene_variantes: false,
                reglas: [],
            }],
        })
    }

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Tipos de documento{' '}
                <Tooltip title="Cada tipo de documento define cómo se procesan sus filas: condiciones de entrada, mapeo de almacenes, método de creación en WMS, estado destino y campos fijos. Si un documento tiene variantes, se pueden definir múltiples reglas donde cada una puede crear de forma distinta (orden vs picking directo). Las filas que no coincidan con ningún documento configurado se cargan sin modificación.">
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
                        flowType={flowType}
                    />
                ))}

                {documentos.length === 0 && (
                    <div className="flujo-doc__vacio">Sin documentos configurados</div>
                )}

                <div className="flujo-condicional__acciones">
                    <Button type="dashed" size="small" onClick={agregar} icon={<PlusOutlined />}>
                        Agregar tipo de documento
                    </Button>
                </div>
            </div>
        </div>
    )
}

export default SeccionDocumentos
