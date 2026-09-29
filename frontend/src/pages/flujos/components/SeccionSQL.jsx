import { useEffect, useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Tooltip, Radio, Select, Checkbox, Input, InputNumber, Modal, Tag, Empty, Spin, message } from 'antd'
import { InfoCircleOutlined, EyeOutlined } from '@ant-design/icons'
import { getSqlBlocks, previewSql } from '@/services/sqlBlocks'

/**
 * SeccionSQL — Editor de consulta SQL para flujos SIESA WS.
 *
 * Dos modos:
 * - "visual": el admin elige consulta base + activa campos + agrega filtros
 * - "libre": textarea para SQL crudo (como antes)
 *
 * Props:
 *   sql        — string SQL (modo libre)
 *   config     — objeto completo del config del flow (contiene sql_mode, sql_base_id, etc.)
 *   flowType   — "items", "customer", etc. (para filtrar bloques por entidad)
 *   onChange   — fn(sql) — se llama cuando cambia el SQL en modo libre
 *   onConfigChange — fn(config) — se llama cuando cambia la config visual
 */
const SeccionSQL = ({ sql, config, flowType, onChange, onConfigChange }) => {
    const modo = config?.sql_mode || 'libre'
    const [previewOpen, setPreviewOpen] = useState(false)
    const [previewText, setPreviewText] = useState('')

    const { data: bloques = [], isLoading } = useQuery({
        queryKey: ['sql-blocks-activos'],
        queryFn: () => getSqlBlocks({ is_active: true }),
    })

    const preview = useMutation({
        mutationFn: previewSql,
        onSuccess: (data) => {
            setPreviewText(data.sql || '')
            setPreviewOpen(true)
        },
        onError: (err) => message.error(err.response?.data?.detail || 'Error generando vista previa'),
    })

    const bases = bloques.filter((b) => b.block_type === 'base' && matchEntity(b, flowType))
    const campos = bloques.filter((b) => b.block_type === 'campo' && matchEntity(b, flowType))
    const filtros = bloques.filter((b) => b.block_type === 'filtro' && matchEntity(b, flowType))

    const baseSeleccionada = config?.sql_base_id || null
    const camposActivos = config?.sql_campos || []
    const filtrosActivos = config?.sql_filtros || []
    const baseVariables = config?.sql_base_variables || {}

    const setModo = (nuevoModo) => {
        if (nuevoModo === 'visual' && modo === 'libre' && sql?.trim()) {
            Modal.confirm({
                title: 'Cambiar a modo visual',
                content: 'El SQL escrito manualmente se perdera al cambiar a modo visual. Continuar?',
                okText: 'Cambiar',
                cancelText: 'Cancelar',
                onOk: () => onConfigChange({ ...config, sql_mode: 'visual' }),
            })
        } else {
            onConfigChange({ ...config, sql_mode: nuevoModo })
        }
    }

    const setBaseId = (id) => {
        const nuevosActivos = camposActivos.filter((c) => {
            const bloque = bloques.find((b) => b.id === c.block_id)
            return bloque && (!bloque.requires_block_id || bloque.requires_block_id === id)
        })
        onConfigChange({ ...config, sql_base_id: id, sql_campos: nuevosActivos, sql_base_variables: {} })
    }

    const toggleCampo = (blockId, checked) => {
        if (checked) {
            const bloque = bloques.find((b) => b.id === blockId)
            const defaults = {}
            for (const v of (bloque?.variables || [])) {
                defaults[v.name] = v.default || ''
            }
            onConfigChange({
                ...config,
                sql_campos: [...camposActivos, { block_id: blockId, variables: defaults }],
            })
        } else {
            onConfigChange({
                ...config,
                sql_campos: camposActivos.filter((c) => c.block_id !== blockId),
            })
        }
    }

    const setCampoVariable = (blockId, varName, value) => {
        const nuevos = camposActivos.map((c) => {
            if (c.block_id !== blockId) return c
            return { ...c, variables: { ...c.variables, [varName]: value } }
        })
        onConfigChange({ ...config, sql_campos: nuevos })
    }

    const toggleFiltro = (blockId, checked) => {
        if (checked) {
            const bloque = bloques.find((b) => b.id === blockId)
            const defaults = {}
            for (const v of (bloque?.variables || [])) {
                defaults[v.name] = v.default || ''
            }
            onConfigChange({
                ...config,
                sql_filtros: [...filtrosActivos, { block_id: blockId, variables: defaults }],
            })
        } else {
            onConfigChange({
                ...config,
                sql_filtros: filtrosActivos.filter((f) => f.block_id !== blockId),
            })
        }
    }

    const setFiltroVariable = (blockId, varName, value) => {
        const nuevos = filtrosActivos.map((f) => {
            if (f.block_id !== blockId) return f
            return { ...f, variables: { ...f.variables, [varName]: value } }
        })
        onConfigChange({ ...config, sql_filtros: nuevos })
    }

    const setBaseVariable = (varName, value) => {
        onConfigChange({ ...config, sql_base_variables: { ...baseVariables, [varName]: value } })
    }

    const handlePreview = () => {
        preview.mutate({
            sql_base_id: baseSeleccionada,
            sql_base_variables: baseVariables,
            sql_campos: camposActivos,
            sql_filtros: filtrosActivos,
        })
    }

    const camposFiltrados = baseSeleccionada
        ? campos.filter((b) => !b.requires_block_id || b.requires_block_id === baseSeleccionada)
        : campos

    const baseBlock = bases.find((b) => b.id === baseSeleccionada)

    if (isLoading) {
        return (
            <div className="flujo-seccion">
                <h3 className="flujo-seccion__titulo">Consulta SQL</h3>
                <Spin size="small" />
            </div>
        )
    }

    return (
        <div className="flujo-seccion">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h3 className="flujo-seccion__titulo" style={{ margin: 0 }}>
                    Consulta SQL{' '}
                    <Tooltip title="Modo visual: arma la consulta desde bloques preconfigurados. Modo SQL libre: escribe el query completo a mano.">
                        <InfoCircleOutlined className="flujo-seccion__info" />
                    </Tooltip>
                </h3>
                <Radio.Group value={modo} onChange={(e) => setModo(e.target.value)} size="small">
                    <Radio.Button value="visual">Visual</Radio.Button>
                    <Radio.Button value="libre">SQL libre</Radio.Button>
                </Radio.Group>
            </div>

            {modo === 'libre' && (
                <textarea
                    className="flujo-sql"
                    value={sql || ''}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder="SELECT ... FROM ... WHERE ..."
                    spellCheck={false}
                />
            )}

            {modo === 'visual' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                    {/* Consulta base */}
                    <div>
                        <label style={{ fontWeight: 500, fontSize: 13, marginBottom: 6, display: 'block' }}>
                            Consulta base
                        </label>
                        <Select
                            value={baseSeleccionada}
                            onChange={setBaseId}
                            placeholder="Selecciona una consulta base"
                            style={{ width: '100%' }}
                            allowClear
                            options={bases.map((b) => ({
                                value: b.id,
                                label: b.name,
                                desc: b.description,
                            }))}
                            optionRender={(opt) => (
                                <div>
                                    <div style={{ fontWeight: 500 }}>{opt.label}</div>
                                    {opt.data.desc && <div style={{ fontSize: 11, color: '#888' }}>{opt.data.desc}</div>}
                                </div>
                            )}
                        />
                        {baseBlock?.variables?.length > 0 && (
                            <div style={{ marginTop: 8, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                                {baseBlock.variables.map((v) => (
                                    <VariableInput
                                        key={v.name}
                                        variable={v}
                                        value={baseVariables[v.name]}
                                        onChange={(val) => setBaseVariable(v.name, val)}
                                    />
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Campos adicionales */}
                    {camposFiltrados.length > 0 && (
                        <div>
                            <label style={{ fontWeight: 500, fontSize: 13, marginBottom: 8, display: 'block' }}>
                                Campos adicionales
                            </label>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                {camposFiltrados.map((bloque) => {
                                    const activo = camposActivos.find((c) => c.block_id === bloque.id)
                                    return (
                                        <CampoToggle
                                            key={bloque.id}
                                            bloque={bloque}
                                            checked={Boolean(activo)}
                                            variables={activo?.variables || {}}
                                            onToggle={(checked) => toggleCampo(bloque.id, checked)}
                                            onVariableChange={(varName, val) => setCampoVariable(bloque.id, varName, val)}
                                        />
                                    )
                                })}
                            </div>
                        </div>
                    )}

                    {/* Filtros */}
                    {filtros.length > 0 && (
                        <div>
                            <label style={{ fontWeight: 500, fontSize: 13, marginBottom: 8, display: 'block' }}>
                                Filtros
                            </label>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                {filtros.map((bloque) => {
                                    const activo = filtrosActivos.find((f) => f.block_id === bloque.id)
                                    return (
                                        <CampoToggle
                                            key={bloque.id}
                                            bloque={bloque}
                                            checked={Boolean(activo)}
                                            variables={activo?.variables || {}}
                                            onToggle={(checked) => toggleFiltro(bloque.id, checked)}
                                            onVariableChange={(varName, val) => setFiltroVariable(bloque.id, varName, val)}
                                        />
                                    )
                                })}
                            </div>
                        </div>
                    )}

                    {!baseSeleccionada && campos.length === 0 && filtros.length === 0 && (
                        <Empty
                            description="No hay bloques SQL configurados para esta entidad"
                            style={{ margin: '20px 0' }}
                        />
                    )}

                    {/* Vista previa */}
                    {baseSeleccionada && (
                        <div>
                            <button
                                onClick={handlePreview}
                                disabled={preview.isPending}
                                style={{
                                    display: 'inline-flex', alignItems: 'center', gap: 6,
                                    padding: '6px 14px', border: '1px solid #d9d9d9', borderRadius: 6,
                                    background: '#fafafa', cursor: 'pointer', fontSize: 13,
                                }}
                            >
                                <EyeOutlined /> {preview.isPending ? 'Generando...' : 'Vista previa SQL'}
                            </button>
                        </div>
                    )}
                </div>
            )}

            <Modal
                title="Vista previa SQL"
                open={previewOpen}
                onCancel={() => setPreviewOpen(false)}
                footer={null}
                width={800}
            >
                <pre style={{
                    background: '#1e1e1e', color: '#d4d4d4', padding: 16,
                    borderRadius: 8, fontSize: 13, fontFamily: 'monospace',
                    maxHeight: 500, overflow: 'auto', whiteSpace: 'pre-wrap',
                }}>
                    {previewText || 'Sin resultado'}
                </pre>
            </Modal>
        </div>
    )
}

function matchEntity(bloque, flowType) {
    if (!flowType) return true
    const tipos = (bloque.entity_types || '').split(',').map((s) => s.trim())
    return tipos.includes(flowType)
}

function CampoToggle({ bloque, checked, variables, onToggle, onVariableChange }) {
    const tieneVars = bloque.variables?.length > 0

    return (
        <div style={{
            display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8,
            padding: '6px 10px', borderRadius: 6,
            background: checked ? '#f0f7ff' : '#fafafa',
            border: `1px solid ${checked ? '#91caff' : '#f0f0f0'}`,
            transition: 'all 0.2s',
        }}>
            <Checkbox checked={checked} onChange={(e) => onToggle(e.target.checked)}>
                <span style={{ fontWeight: 500, fontSize: 13 }}>{bloque.name}</span>
            </Checkbox>
            {bloque.description && (
                <Tooltip title={bloque.description}>
                    <InfoCircleOutlined style={{ color: '#999', fontSize: 12 }} />
                </Tooltip>
            )}
            {checked && tieneVars && (
                <div style={{ display: 'flex', gap: 10, marginLeft: 'auto', flexWrap: 'wrap' }}>
                    {bloque.variables.map((v) => (
                        <VariableInput
                            key={v.name}
                            variable={v}
                            value={variables[v.name]}
                            onChange={(val) => onVariableChange(v.name, val)}
                        />
                    ))}
                </div>
            )}
        </div>
    )
}

function VariableInput({ variable, value, onChange }) {
    const { name, label, type } = variable
    const displayLabel = label || name

    if (type === 'number') {
        return (
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ fontSize: 12, color: '#666' }}>{displayLabel}:</span>
                <InputNumber
                    size="small"
                    value={value != null ? Number(value) : undefined}
                    onChange={(v) => onChange(String(v ?? ''))}
                    style={{ width: 80 }}
                />
            </div>
        )
    }

    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ fontSize: 12, color: '#666' }}>{displayLabel}:</span>
            <Input
                size="small"
                value={value ?? ''}
                onChange={(e) => onChange(e.target.value)}
                style={{ width: type === 'list' ? 200 : 120 }}
                placeholder={type === 'list' ? 'val1, val2, ...' : ''}
            />
        </div>
    )
}

export default SeccionSQL
