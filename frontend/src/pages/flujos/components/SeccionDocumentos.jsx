import { useState } from 'react'
import { Button, Input, InputNumber, Select, Tooltip } from 'antd'
import { InfoCircleOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import TablaClaveValor from './TablaClaveValor'

const OPERADORES = [
    { value: 'contiene', label: 'contiene' },
    { value: 'empieza_con', label: 'empieza con' },
    { value: '=', label: 'es igual a' },
    { value: '!=', label: 'es distinto de' },
    { value: 'in', label: 'está en la lista' },
]

function getOpcionesCrearComo(flowType) {
    if (flowType === 'purchases') {
        return [
            { value: 'order', label: 'Orden de compra' },
            { value: 'picking_direct', label: 'Picking directo' },
        ]
    }
    return [
        { value: 'order', label: 'Orden de venta' },
        { value: 'picking_direct', label: 'Picking directo' },
    ]
}

function getOpcionesEstado(crearComo, flowType) {
    if (crearComo === 'picking_direct') {
        return [
            { value: 'draft', label: 'Borrador' },
            { value: 'confirmed', label: 'Confirmado' },
            { value: 'assigned', label: 'Listo' },
        ]
    }
    return [
        { value: 'draft', label: 'Borrador' },
        { value: flowType === 'purchases' ? 'purchase' : 'sale', label: 'Confirmado' },
    ]
}

const ANCHO_CAMPO = 200
const ANCHO_OPERADOR = 150
const ANCHO_VALOR = 200

// ─── Línea de condición ───

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
            onChange={(v) => onChange({ ...condicion, operador: v })}
        />
        <Input
            size="small"
            style={{ width: ANCHO_VALOR }}
            value={condicion.valor}
            onChange={(e) => onChange({ ...condicion, valor: e.target.value })}
            placeholder="valor"
        />
        {onEliminar && (
            <button className="flujo-tcv__eliminar" onClick={onEliminar} type="button" title="Eliminar">
                <DeleteOutlined />
            </button>
        )}
    </div>
)

// ─── Configuración de destino (crear como + estado + operación/bodega) ───

const ConfigDestino = ({ datos, onChange, flowType }) => {
    const crearComo = datos.crear_como || 'order'
    const estadosDisponibles = getOpcionesEstado(crearComo, flowType)
    const estadoActual = estadosDisponibles.some(e => e.value === datos.estado) ? datos.estado : 'draft'
    const esPicking = crearComo === 'picking_direct'
    const esEntrada = flowType === 'purchases'

    return (
        <div className="flujo-doc__destino">
            <div className="flujo-doc__destino-fila">
                <div className="flujo-campo">
                    <label className="flujo-campo__label">Crear como</label>
                    <Select
                        size="small"
                        style={{ width: 180 }}
                        value={crearComo}
                        options={getOpcionesCrearComo(flowType)}
                        onChange={(v) => onChange({
                            ...datos,
                            crear_como: v,
                            estado: 'draft',
                            operacion_id: v === 'picking_direct' ? (datos.operacion_id || '') : '',
                        })}
                    />
                </div>
                <div className="flujo-campo">
                    <label className="flujo-campo__label">Estado en WMS</label>
                    <Select
                        size="small"
                        style={{ width: 150 }}
                        value={estadoActual}
                        options={estadosDisponibles}
                        onChange={(v) => onChange({ ...datos, estado: v })}
                    />
                </div>
                {esPicking && (
                    <div className="flujo-campo">
                        <label className="flujo-campo__label">
                            ID Tipo de operacion{' '}
                            <Tooltip title="ID del tipo de operacion en WMS (Inventario > Configuracion > Tipos de operacion). El picking usara las ubicaciones origen/destino de esta operacion.">
                                <InfoCircleOutlined style={{ color: '#bfbfbf', fontSize: 12 }} />
                            </Tooltip>
                        </label>
                        <InputNumber
                            size="small"
                            style={{ width: 90 }}
                            min={1}
                            value={datos.operacion_id || undefined}
                            onChange={(v) => onChange({ ...datos, operacion_id: v })}
                            placeholder="ID"
                        />
                    </div>
                )}
            </div>

            {!esPicking && (
                <div className="flujo-doc__bodega-mapping">
                    <label className="flujo-campo__label" style={{ marginTop: 10 }}>
                        Bodega ERP → {esEntrada ? 'ID Tipo de operacion' : 'ID Almacen'}{' '}
                        <Tooltip title={esEntrada
                            ? 'Relaciona cada bodega del ERP con el tipo de operacion en WMS. Si una bodega no esta en la tabla, se usa el tipo de operacion por defecto.'
                            : 'Relaciona cada bodega del ERP con el almacen en WMS. Si una bodega no esta en la tabla, se usa el almacen principal.'
                        }>
                            <InfoCircleOutlined style={{ color: '#bfbfbf', fontSize: 12 }} />
                        </Tooltip>
                    </label>
                    <div style={{ maxWidth: 400 }}>
                        <TablaClaveValor
                            columnas={['Bodega ERP', esEntrada ? 'ID Tipo de operacion' : 'ID Almacen']}
                            datos={datos.warehouse_mapping || []}
                            onChange={(v) => onChange({ ...datos, warehouse_mapping: v })}
                            placeholders={['M0101', '1']}
                        />
                    </div>
                </div>
            )}
        </div>
    )
}

// ─── Bloque de una regla ───

const BloqueRegla = ({ regla, indice, total, onChange, onEliminar, flowType }) => {
    const [camposFijos, setCamposFijos] = useState((regla.hardcodes || []).length > 0)

    const cambiar = (campo, valor) => onChange({ ...regla, [campo]: valor })

    const filtros = regla.filtros || []
    const cambiarFiltro = (i, nuevo) => cambiar('filtros', filtros.map((f, j) => j === i ? nuevo : f))
    const eliminarFiltro = (i) => cambiar('filtros', filtros.filter((_, j) => j !== i))
    const agregarFiltro = () => cambiar('filtros', [...filtros, { campo: '', operador: '=', valor: '' }])

    return (
        <div className="flujo-doc__regla">
            <div className="flujo-doc__regla-header">
                <span className="flujo-doc__regla-etiqueta">
                    {total > 1 ? (indice === 0 ? 'Regla 1' : `Regla ${indice + 1} (si no entro en la anterior)`) : 'Configuracion'}
                </span>
                {total > 1 && (
                    <button className="flujo-tcv__eliminar" onClick={onEliminar} type="button" title="Eliminar regla">
                        <DeleteOutlined />
                    </button>
                )}
            </div>

            {/* Criterios */}
            <div className="flujo-doc__sub">
                <label className="flujo-campo__label">Criterios para traer documento</label>
                {filtros.map((f, i) => (
                    <LineaCondicion
                        key={i}
                        condicion={f}
                        onChange={(n) => cambiarFiltro(i, n)}
                        onEliminar={() => eliminarFiltro(i)}
                    />
                ))}
                {filtros.length === 0 && (
                    <div className="flujo-doc__vacio">Sin criterios: todas las filas de este documento pasan</div>
                )}
                <Button type="dashed" size="small" onClick={agregarFiltro} icon={<PlusOutlined />} style={{ marginTop: 4 }}>
                    Criterio
                </Button>
            </div>

            {/* Destino */}
            <ConfigDestino
                datos={regla}
                onChange={(nuevos) => onChange(nuevos)}
                flowType={flowType}
            />

            {/* Campos fijos */}
            <div className="flujo-doc__sub" style={{ marginTop: 8 }}>
                <Button
                    type="link"
                    size="small"
                    onClick={() => setCamposFijos(!camposFijos)}
                    style={{ padding: 0, fontSize: 12, color: '#8c8c8c' }}
                >
                    {camposFijos ? '▾' : '▸'} Valores fijos adicionales
                </Button>
                {camposFijos && (
                    <div style={{ maxWidth: 400, marginTop: 6 }}>
                        <TablaClaveValor
                            columnas={['Campo destino', 'Valor fijo']}
                            datos={regla.hardcodes || []}
                            onChange={(v) => cambiar('hardcodes', v)}
                            placeholders={['cliente', '800007355']}
                        />
                    </div>
                )}
            </div>
        </div>
    )
}

// ─── Bloque de un documento ───

const BloqueDocumento = ({ documento, indice, onChange, onEliminar, flowType }) => {
    const cambiar = (campo, valor) => onChange(indice, { ...documento, [campo]: valor })

    // Si tiene 0 reglas, crear una con los datos del documento
    const reglas = documento.reglas && documento.reglas.length > 0
        ? documento.reglas
        : [{
            filtros: documento.filtros || [],
            warehouse_mapping: documento.warehouse_mapping || [],
            hardcodes: documento.hardcodes || [],
            crear_como: documento.crear_como || 'order',
            estado: documento.estado || 'draft',
            operacion_id: documento.operacion_id || '',
        }]

    const cambiarRegla = (i, nueva) => {
        const nuevas = [...reglas]
        nuevas[i] = nueva
        cambiar('reglas', nuevas)
        cambiar('tiene_variantes', nuevas.length > 1)
    }

    const eliminarRegla = (i) => {
        const nuevas = reglas.filter((_, j) => j !== i)
        cambiar('reglas', nuevas.length > 0 ? nuevas : [])
        cambiar('tiene_variantes', nuevas.length > 1)
    }

    const agregarRegla = () => {
        cambiar('reglas', [...reglas, {
            filtros: [],
            warehouse_mapping: [],
            hardcodes: [],
            crear_como: 'order',
            estado: 'draft',
            operacion_id: '',
        }])
        cambiar('tiene_variantes', true)
    }

    return (
        <div className="flujo-doc__documento">
            {/* Cabecera: identificación */}
            <div className="flujo-doc__cabecera">
                <h4 className="flujo-seccion__subtitulo" style={{ margin: 0 }}>
                    Documento a identificar{' '}
                    <Tooltip title="Identifica cuales filas del flujo pertenecen a este tipo de documento. Usa el nombre del campo despues del mapeo. Si coincide con varios documentos, se aplica el primero.">
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

            {/* Reglas */}
            <div className="flujo-doc__reglas-container">
                {reglas.length > 1 && (
                    <div className="flujo-doc__reglas-info">
                        Las reglas se evaluan en orden. La primera que coincida captura la fila.
                    </div>
                )}
                {reglas.map((regla, i) => (
                    <BloqueRegla
                        key={i}
                        regla={regla}
                        indice={i}
                        total={reglas.length}
                        onChange={(nueva) => cambiarRegla(i, nueva)}
                        onEliminar={() => eliminarRegla(i)}
                        flowType={flowType}
                    />
                ))}
                <Button
                    type="dashed"
                    size="small"
                    onClick={agregarRegla}
                    icon={<PlusOutlined />}
                    style={{ marginTop: 6 }}
                >
                    Agregar regla
                </Button>
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
                <Tooltip title="Define como se procesan las filas segun su tipo de documento. Cada tipo puede tener sus propios criterios de filtrado, metodo de creacion en WMS y configuracion de destino. Las filas que no coincidan con ningun documento configurado se cargan sin modificacion.">
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

                <div style={{ marginTop: 10 }}>
                    <Button type="dashed" size="small" onClick={agregar} icon={<PlusOutlined />}>
                        Agregar tipo de documento
                    </Button>
                </div>
            </div>
        </div>
    )
}

export default SeccionDocumentos
