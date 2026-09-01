import { useEffect, useState } from 'react'
import { Alert, Button, Spin, message } from 'antd'
import ErpTag from '@/components/ErpTag'
import useHasRole from '@/hooks/useHasRole'
import { useFlowDetalle, useCrearFlow, useActualizarFlow, mensajeDeError } from '@/hooks/useFlujos'
import { IconVolver } from '../icons'
import SeccionBase from './SeccionBase'
import SeccionSQL from './SeccionSQL'
import SeccionOrigenConnekta from './SeccionOrigenConnekta'
import SeccionOrigenSAP from './SeccionOrigenSAP'
import SeccionMapping from './SeccionMapping'
import SeccionConfigItems from './SeccionConfigItems'
import SeccionConfigPartners from './SeccionConfigPartners'
import SeccionConfigTransacciones from './SeccionConfigTransacciones'
import SeccionConditionals from './SeccionConditionals'
import SeccionDocumentos from './SeccionDocumentos'
import SeccionResolve from './SeccionResolve'

const TITULOS_TIPO = {
    items: 'Productos',
    customer: 'Clientes',
    supplier: 'Proveedores',
    purchases: 'Entrada',
    sales: 'Salida',
}

function dictATabla(obj) {
    if (!obj || typeof obj !== 'object') return []
    return Object.entries(obj).map(([clave, valor]) => ({ clave, valor: String(valor) }))
}

function tablaADict(tabla) {
    const dict = {}
    for (const fila of tabla) {
        if (fila.clave?.trim()) {
            dict[fila.clave.trim()] = fila.valor
        }
    }
    return dict
}

function condicionalesATabla(condiciones) {
    if (!Array.isArray(condiciones)) return []
    return condiciones.map((cond) => {
        if (cond.tipo === 'funcion' || cond.funcion) {
            return {
                tipo: 'funcion',
                campo_destino: cond.campo_destino || '',
                nombre: cond.funcion || '',
                params: cond.params || {},
            }
        }
        // El backend guarda `reglas` como lista de {si, entonces}.
        // Se tolera tambien el formato dict que pudo quedar guardado antes de esta correccion.
        const crudas = cond.reglas || []
        const reglas = Array.isArray(crudas)
            ? crudas.map((r) => ({ clave: String(r.si ?? ''), valor: String(r.entonces ?? '') }))
            : Object.entries(crudas).map(([clave, valor]) => ({ clave, valor: String(valor) }))
        return {
            tipo: 'regla',
            campo_destino: cond.campo_destino || '',
            campo_origen: cond.campo_origen || '',
            reglas,
            valor_por_defecto: cond.default ?? cond.valor_por_defecto ?? '',
        }
    })
}

function tablaACondicionales(tabla) {
    return tabla.map((item) => {
        if (item.tipo === 'funcion') {
            return {
                tipo: 'funcion',
                campo_destino: item.campo_destino,
                funcion: item.nombre,
                params: item.params || {},
            }
        }
        const reglas = (item.reglas || [])
            .filter((r) => r.clave?.trim())
            .map((r) => ({ si: r.clave.trim(), entonces: r.valor }))
        return {
            tipo: 'reglas',
            campo_destino: item.campo_destino,
            campo_origen: item.campo_origen,
            reglas,
            default: item.valor_por_defecto || '',
        }
    })
}

function documentosATabla(documentos) {
    if (!Array.isArray(documentos)) return []
    return documentos.map((doc) => {
        const ident = doc.identificar_por || {}
        return {
            ident_campo: ident.campo || '',
            ident_operador: ident.operador || 'contiene',
            ident_valor: String(ident.valor ?? ''),
            filtros: (doc.filtros || []).map((f) => ({
                campo: f?.campo || '',
                operador: f?.operador || '=',
                // el operador `in` guarda una lista; en el formulario se edita separado por comas
                valor: Array.isArray(f?.valor) ? f.valor.join(', ') : String(f?.valor ?? ''),
            })),
            hardcodes: dictATabla(doc.hardcodes),
        }
    })
}

function tablaADocumentos(tabla) {
    return tabla
        .filter((d) => d.ident_campo?.trim())
        .map((d, i) => ({
            // el nombre del documento se deriva del valor que lo identifica;
            // el backend lo usa para el resumen por documento en los logs
            codigo: String(d.ident_valor ?? '').trim() || `#${i}`,
            identificar_por: {
                campo: (d.ident_campo || '').trim(),
                operador: d.ident_operador || 'contiene',
                valor: d.ident_valor ?? '',
            },
            filtros: (d.filtros || [])
                .filter((f) => f.campo?.trim())
                .map((f) => ({
                    campo: f.campo.trim(),
                    operador: f.operador || '=',
                    valor: f.operador === 'in'
                        ? String(f.valor ?? '').split(',').map((v) => v.trim()).filter(Boolean)
                        : f.valor,
                })),
            hardcodes: tablaADict(d.hardcodes || []),
        }))
}

function filterStringACondiciones(filterStr) {
    if (!filterStr) return []
    return filterStr.split(' and ').map((parte) => {
        const match = parte.trim().match(/^(\S+)\s+(eq|ne|gt|ge|lt|le)\s+'?([^']*)'?$/)
        if (match) return { campo: match[1], operador: match[2], valor: match[3] }
        return { campo: parte.trim(), operador: 'eq', valor: '' }
    })
}

function condicionesAFilterString(condiciones) {
    return condiciones
        .filter((c) => c.campo && c.valor)
        .map((c) => `${c.campo} ${c.operador} '${c.valor}'`)
        .join(' and ')
}

function parametrosStringATabla(str) {
    if (!str) return []
    return str.split('|').filter(Boolean).map((par) => {
        const [clave, ...resto] = par.split('=')
        return { clave: (clave || '').trim(), valor: (resto.join('=') || '').trim() }
    })
}

function tablaAParametrosString(tabla) {
    return tabla
        .filter((f) => f.clave?.trim())
        .map((f) => `${f.clave.trim()} = ${f.valor}`)
        .join('|')
}

function deserializar(flow, erpType, flowType) {
    const fc = flow?.flow_config || {}

    const estado = {
        base: {
            flow_name: flow?.flow_name || '',
            flow_type: flow?.flow_type || flowType || '',
            schedule_cron: flow?.schedule_cron || '',
            is_active: flow?.is_active ?? true,
        },
        config: {},
    }

    if (erpType === 'ws') {
        estado.config.sql = fc.sql || ''
    }

    if (erpType === 'connekta') {
        estado.config.query_desc = fc.query_desc || ''
        estado.config.parametros_tabla = parametrosStringATabla(fc.parametros)
        estado.config.paginacion = fc.paginacion !== false
    }

    if (erpType === 'sap') {
        estado.config.endpoint = fc.endpoint || ''
        estado.config.filter_condiciones = filterStringACondiciones(fc.filter)
    }

    if (erpType === 'connekta' || erpType === 'sap') {
        estado.config.mapping_tabla = dictATabla(fc.mapping)
        estado.config.hardcodes_tabla = dictATabla(fc.hardcodes)
        estado.config.conditionals_tabla = condicionalesATabla(fc.conditionals)
    }

    if (erpType === 'sap' && flowType !== 'items') {
        // El backend espera { origen: "DocumentLines", campos: { campo: alias } }.
        // Se tolera tambien el formato { "DocumentLines": { campo: alias } } que
        // pudo quedar guardado antes de esta correccion.
        const ml = fc.mapping_lineas || {}
        let origen = ''
        let campos = {}
        if (typeof ml.origen === 'string') {
            origen = ml.origen
            campos = ml.campos || {}
        } else {
            const primera = Object.keys(ml)[0]
            if (primera) {
                origen = primera
                campos = ml[primera] || {}
            }
        }
        estado.config.mapping_lineas_campo = origen
        estado.config.mapping_lineas_tabla = dictATabla(campos)
    }

    if (flowType === 'items') {
        estado.config.uom_mapping_tabla = dictATabla(fc.uom_mapping)
    }

    if (flowType === 'customer' || flowType === 'supplier') {
        estado.config.sucursal_hierarchy = fc.sucursal_hierarchy || false
        estado.config.sucursal_padre = fc.sucursal_padre || '001'
        estado.config.country_id = fc.country_id ?? 49
        estado.config.identification_type_id = fc.identification_type_id ?? 5
    }

    if (flowType === 'purchases' || flowType === 'sales') {
        estado.config.warehouse_mapping_tabla = dictATabla(fc.warehouse_mapping)
    }

    estado.config.documentos_tabla = documentosATabla(fc.documentos)

    if (flowType === 'items' || flowType === 'customer' || flowType === 'supplier') {
        estado.config.resolve_enabled = fc.resolve_enabled !== false

        if (erpType === 'sap' || erpType === 'connekta') {
            estado.config.resolve_filter_field = fc.resolve_filter_field || ''
            estado.config.resolve_filter_template = fc.resolve_filter_template || ''
        }

        if (erpType === 'ws') {
            estado.config.resolve_sql_inject = fc.resolve_sql_inject || ''
        }
    }

    return estado
}

function serializar(base, config, erpType, flowType) {
    const fc = {}

    if (erpType === 'ws') {
        fc.sql = config.sql || ''
    }

    if (erpType === 'connekta') {
        fc.query_desc = config.query_desc || ''
        fc.parametros = tablaAParametrosString(config.parametros_tabla || [])
        fc.paginacion = config.paginacion !== false
    }

    if (erpType === 'sap') {
        fc.endpoint = config.endpoint || ''
        fc.filter = condicionesAFilterString(config.filter_condiciones || [])
    }

    if (erpType === 'connekta' || erpType === 'sap') {
        fc.mapping = tablaADict(config.mapping_tabla || [])
        fc.hardcodes = tablaADict(config.hardcodes_tabla || [])
        fc.conditionals = tablaACondicionales(config.conditionals_tabla || [])
    }

    if (erpType === 'sap' && flowType !== 'items') {
        const campo = config.mapping_lineas_campo?.trim()
        if (campo) {
            fc.mapping_lineas = {
                origen: campo,
                campos: tablaADict(config.mapping_lineas_tabla || []),
            }
        }
    }

    if (flowType === 'items') {
        fc.uom_mapping = tablaADict(config.uom_mapping_tabla || [])
    }

    if (flowType === 'customer' || flowType === 'supplier') {
        fc.sucursal_hierarchy = config.sucursal_hierarchy || false
        fc.sucursal_padre = config.sucursal_padre || '001'
        fc.country_id = config.country_id ?? 49
        fc.identification_type_id = config.identification_type_id ?? 5
    }

    if (flowType === 'purchases' || flowType === 'sales') {
        fc.warehouse_mapping = tablaADict(config.warehouse_mapping_tabla || [])
    }

    // Solo se escribe la clave si hay al menos un documento: un flujo sin
    // documentos debe guardar exactamente el mismo JSON que antes.
    if (config.documentos_tabla?.length) {
        const documentos = tablaADocumentos(config.documentos_tabla)
        if (documentos.length) fc.documentos = documentos
    }

    if (flowType === 'items' || flowType === 'customer' || flowType === 'supplier') {
        fc.resolve_enabled = config.resolve_enabled !== false

        if ((erpType === 'sap' || erpType === 'connekta') && fc.resolve_enabled) {
            if (config.resolve_filter_field) fc.resolve_filter_field = config.resolve_filter_field
            if (config.resolve_filter_template) fc.resolve_filter_template = config.resolve_filter_template
        }

        if (erpType === 'ws' && fc.resolve_enabled) {
            if (config.resolve_sql_inject) fc.resolve_sql_inject = config.resolve_sql_inject
        }
    }

    return {
        flow_name: base.flow_name,
        flow_type: base.flow_type,
        flow_config: fc,
        schedule_cron: base.schedule_cron || null,
        is_active: base.is_active ?? true,
    }
}

const EditorFlow = ({ cliente, flowId, flowType: flowTypeInicial, onVolver }) => {
    const esEdicion = Boolean(flowId)
    const erpType = cliente.erp_type
    const puedeEditar = useHasRole(['superadmin', 'admin'])

    const { data: flowExistente, isPending: cargando } = useFlowDetalle(
        esEdicion ? cliente.id : null,
        esEdicion ? flowId : null
    )

    const crear = useCrearFlow(cliente.id)
    const actualizar = useActualizarFlow(cliente.id, flowId)

    const [base, setBase] = useState({
        flow_name: '',
        flow_type: flowTypeInicial || '',
        schedule_cron: '',
        is_active: true,
    })
    const [config, setConfig] = useState({})
    const [inicializado, setInicializado] = useState(!esEdicion)

    useEffect(() => {
        if (esEdicion && flowExistente && !inicializado) {
            const estado = deserializar(flowExistente, erpType, flowExistente.flow_type)
            setBase(estado.base)
            setConfig(estado.config)
            setInicializado(true)
        }
    }, [esEdicion, flowExistente, erpType, inicializado])

    const flowType = base.flow_type

    const guardar = () => {
        if (!base.flow_name?.trim()) {
            message.warning('El nombre del flujo es obligatorio')
            return
        }
        if (!base.flow_type) {
            message.warning('El tipo de flujo es obligatorio')
            return
        }

        const payload = serializar(base, config, erpType, flowType)

        if (esEdicion) {
            actualizar.mutate(payload, {
                onSuccess: () => {
                    message.success('Flujo actualizado')
                    onVolver()
                },
                onError: (err) => message.error(mensajeDeError(err)),
            })
        } else {
            crear.mutate(payload, {
                onSuccess: () => {
                    message.success('Flujo creado')
                    onVolver()
                },
                onError: (err) => message.error(mensajeDeError(err)),
            })
        }
    }

    if (esEdicion && cargando) {
        return <div className="flujo-cargando"><Spin /></div>
    }

    if (esEdicion && !flowExistente && !cargando) {
        return (
            <Alert
                type="error"
                showIcon
                message="No se encontro el flujo"
                action={<Button size="small" onClick={onVolver}>Volver</Button>}
            />
        )
    }

    const guardando = crear.isPending || actualizar.isPending
    const tituloTipo = TITULOS_TIPO[flowType] || flowType

    return (
        <>
            <div className="flujo-cabecera-nivel">
                <button className="flujo-volver" onClick={onVolver}>
                    <IconVolver /> Volver
                </button>
            </div>

            <div className="flujo-editor-head">
                <div className="flujo-editor-head__izq">
                    <h1 className="flujo-editor-head__titulo">
                        {esEdicion ? base.flow_name : 'Nuevo flujo'}
                    </h1>
                    <div className="flujo-editor-head__tags">
                        {tituloTipo && (
                            <span className="flujo-editor-head__tipo">{tituloTipo}</span>
                        )}
                        <ErpTag erpType={erpType} />
                    </div>
                </div>
                {puedeEditar && (
                    <div className="flujo-editor-head__acciones">
                        <Button onClick={onVolver}>Cancelar</Button>
                        <Button type="primary" onClick={guardar} loading={guardando}>
                            Guardar
                        </Button>
                    </div>
                )}
            </div>

            <div className="flujo-editor-cuerpo">
                <SeccionBase
                    datos={base}
                    onChange={setBase}
                    esEdicion={esEdicion}
                />

                {erpType === 'ws' && (
                    <SeccionSQL
                        sql={config.sql}
                        onChange={(sql) => setConfig({ ...config, sql })}
                    />
                )}

                {erpType === 'connekta' && (
                    <SeccionOrigenConnekta
                        config={config}
                        onChange={setConfig}
                    />
                )}

                {erpType === 'sap' && (
                    <SeccionOrigenSAP
                        config={config}
                        onChange={setConfig}
                    />
                )}

                {(erpType === 'connekta' || erpType === 'sap') && flowType !== 'items' && (
                    <SeccionMapping
                        erpType={erpType}
                        flowType={flowType}
                        config={config}
                        onChange={setConfig}
                    />
                )}

                {flowType === 'items' && (
                    <SeccionConfigItems
                        erpType={erpType}
                        config={config}
                        onChange={setConfig}
                    />
                )}

                {(flowType === 'customer' || flowType === 'supplier') && (
                    <SeccionConfigPartners
                        flowType={flowType}
                        config={config}
                        onChange={setConfig}
                    />
                )}

                {(flowType === 'purchases' || flowType === 'sales') && (
                    <SeccionConfigTransacciones
                        flowType={flowType}
                        config={config}
                        onChange={setConfig}
                    />
                )}

                {(erpType === 'connekta' || erpType === 'sap') && (
                    <SeccionConditionals
                        conditionals={config.conditionals_tabla || []}
                        onChange={(nuevos) => setConfig({ ...config, conditionals_tabla: nuevos })}
                    />
                )}

                <SeccionDocumentos
                    config={config}
                    onChange={setConfig}
                />

                <SeccionResolve
                    erpType={erpType}
                    flowType={flowType}
                    config={config}
                    onChange={setConfig}
                />
            </div>

            {puedeEditar && (
                <div className="flujo-editor-pie">
                    <Button onClick={onVolver}>Cancelar</Button>
                    <Button type="primary" onClick={guardar} loading={guardando}>
                        Guardar
                    </Button>
                </div>
            )}
        </>
    )
}

export default EditorFlow
