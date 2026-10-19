import { useMemo } from 'react'
import { Select, Tooltip } from 'antd'
import { InfoCircleOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons'

const TIPOS = [
    { value: 'texto', label: 'Texto' },
    { value: 'decimal', label: 'Decimal' },
    { value: 'entero', label: 'Entero' },
    { value: 'fecha', label: 'Fecha' },
]

function esNumerico(tipo) {
    return tipo === 'decimal' || tipo === 'entero'
}

/**
 * Convierte 6 arrays del backend → tabla unificada para la UI.
 */
export function camposATabla(fc) {
    const campos = new Map()

    const asegurar = (nombre) => {
        if (!campos.has(nombre)) {
            campos.set(nombre, {
                campo: nombre, tipo: 'texto',
                obligatorio: false, default_cero: false, mayor_cero: false,
            })
        }
        return campos.get(nombre)
    }

    for (const c of (fc.campos_obligatorios || [])) asegurar(c).obligatorio = true
    for (const c of (fc.campos_float || [])) { asegurar(c).tipo = 'decimal' }
    for (const c of (fc.campos_int || [])) { asegurar(c).tipo = 'entero' }
    for (const c of (fc.campos_fecha || [])) { asegurar(c).tipo = 'fecha' }
    for (const c of (fc.campos_default_cero || [])) { if (campos.has(c)) campos.get(c).default_cero = true }
    for (const c of (fc.campos_mayor_cero || [])) { if (campos.has(c)) campos.get(c).mayor_cero = true }

    return Array.from(campos.values())
}

/**
 * Convierte tabla unificada → 6 arrays para el backend.
 */
export function tablaACampos(tabla) {
    const r = {
        campos_float: [], campos_int: [], campos_fecha: [],
        campos_obligatorios: [], campos_default_cero: [], campos_mayor_cero: [],
    }
    for (const row of (tabla || [])) {
        if (!row.campo) continue
        if (row.tipo === 'decimal') r.campos_float.push(row.campo)
        if (row.tipo === 'entero') r.campos_int.push(row.campo)
        if (row.tipo === 'fecha') r.campos_fecha.push(row.campo)
        if (row.obligatorio) r.campos_obligatorios.push(row.campo)
        if (row.default_cero) r.campos_default_cero.push(row.campo)
        if (row.mayor_cero) r.campos_mayor_cero.push(row.campo)
    }
    return r
}

/**
 * Extrae campos disponibles del mapping y hardcodes para el selector "Agregar campo".
 */
function extraerCamposDisponibles(config, camposExistentes) {
    const usados = new Set(camposExistentes.map((c) => c.campo))
    const disponibles = new Set()

    for (const fila of (config.mapping_tabla || [])) {
        const alias = (fila.valor || '').trim()
        if (alias && !usados.has(alias)) disponibles.add(alias)
    }
    for (const fila of (config.hardcodes_tabla || [])) {
        const clave = (fila.clave || '').trim()
        if (clave && !usados.has(clave)) disponibles.add(clave)
    }

    return Array.from(disponibles).sort((a, b) => a.localeCompare(b, 'es'))
}

const Check = ({ activo, deshabilitado, onChange, titulo }) => {
    const cls = deshabilitado
        ? 'validacion__check validacion__check--off'
        : activo
            ? 'validacion__check validacion__check--on'
            : 'validacion__check'

    return (
        <Tooltip title={deshabilitado ? 'Solo aplica a campos numéricos (Decimal o Entero)' : titulo}>
            <span
                className={cls}
                onClick={deshabilitado ? undefined : onChange}
            >
                {activo && !deshabilitado && (
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3.4" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M20 6L9 17l-5-5" />
                    </svg>
                )}
            </span>
        </Tooltip>
    )
}

const SeccionValidacion = ({ config, onChange }) => {
    const tabla = config.campos_validacion_tabla || []

    const disponibles = useMemo(
        () => extraerCamposDisponibles(config, tabla),
        [config.mapping_tabla, config.hardcodes_tabla, tabla]
    )

    const actualizar = (indice, campo, valor) => {
        const nuevas = tabla.map((row, i) => {
            if (i !== indice) return row
            const nueva = { ...row, [campo]: valor }
            // Si cambió el tipo a no-numérico, limpiar checkboxes numéricos
            if (campo === 'tipo' && !esNumerico(valor)) {
                nueva.default_cero = false
                nueva.mayor_cero = false
            }
            return nueva
        })
        onChange({ ...config, campos_validacion_tabla: nuevas })
    }

    const eliminar = (indice) => {
        onChange({
            ...config,
            campos_validacion_tabla: tabla.filter((_, i) => i !== indice),
        })
    }

    const agregar = (nombre) => {
        if (!nombre || tabla.some((r) => r.campo === nombre)) return
        onChange({
            ...config,
            campos_validacion_tabla: [
                ...tabla,
                { campo: nombre, tipo: 'texto', obligatorio: false, default_cero: false, mayor_cero: false },
            ],
        })
    }

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Validaci&oacute;n y tipado de campos{' '}
                <Tooltip title="Define c&oacute;mo se interpreta y valida cada campo antes de enviarlo al WMS. Las filas que no pasen la validaci&oacute;n se reportan como descartadas en la ejecuci&oacute;n. Si no se configura nada, el sistema usa valores por defecto seg&uacute;n el tipo de flujo.">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            {tabla.length > 0 ? (
                <div className="validacion__tabla-wrap">
                    <table className="validacion__tabla">
                        <thead>
                            <tr>
                                <th>Campo</th>
                                <th>Tipo de dato</th>
                                <th className="validacion__th-check">
                                    Obligatorio
                                    <Tooltip title="El campo debe tener un valor. Si est&aacute; vac&iacute;o o ausente, el registro completo se descarta.">
                                        <InfoCircleOutlined className="flujo-seccion__info" />
                                    </Tooltip>
                                </th>
                                <th className="validacion__th-check">
                                    Si vac&iacute;o &rarr; 0
                                    <Tooltip title="Si el campo viene vac&iacute;o o nulo, se reemplaza autom&aacute;ticamente por 0 en vez de descartar el registro. &Uacute;til para campos como precio donde no siempre viene valor. Solo aplica a Decimal y Entero.">
                                        <InfoCircleOutlined className="flujo-seccion__info" />
                                    </Tooltip>
                                </th>
                                <th className="validacion__th-check">
                                    Requiere &gt; 0
                                    <Tooltip title="El campo debe ser un n&uacute;mero mayor a cero. Si es 0, negativo o no num&eacute;rico, el registro se descarta. &Uacute;til para cantidad. Solo aplica a Decimal y Entero.">
                                        <InfoCircleOutlined className="flujo-seccion__info" />
                                    </Tooltip>
                                </th>
                                <th style={{ width: 40 }}></th>
                            </tr>
                        </thead>
                        <tbody>
                            {tabla.map((row, i) => {
                                const num = esNumerico(row.tipo)
                                return (
                                    <tr key={row.campo + i}>
                                        <td className="validacion__campo">{row.campo}</td>
                                        <td>
                                            <Select
                                                size="small"
                                                style={{ width: 120 }}
                                                value={row.tipo}
                                                options={TIPOS}
                                                onChange={(v) => actualizar(i, 'tipo', v)}
                                            />
                                        </td>
                                        <td className="validacion__td-check">
                                            <Check
                                                activo={row.obligatorio}
                                                onChange={() => actualizar(i, 'obligatorio', !row.obligatorio)}
                                                titulo="Marcar como obligatorio"
                                            />
                                        </td>
                                        <td className="validacion__td-check">
                                            <Check
                                                activo={row.default_cero}
                                                deshabilitado={!num}
                                                onChange={() => actualizar(i, 'default_cero', !row.default_cero)}
                                                titulo="Si viene vacío, usar 0"
                                            />
                                        </td>
                                        <td className="validacion__td-check">
                                            <Check
                                                activo={row.mayor_cero}
                                                deshabilitado={!num}
                                                onChange={() => actualizar(i, 'mayor_cero', !row.mayor_cero)}
                                                titulo="Debe ser mayor a cero"
                                            />
                                        </td>
                                        <td className="validacion__td-check">
                                            <button
                                                className="validacion__eliminar"
                                                onClick={() => eliminar(i)}
                                                title="Quitar campo"
                                            >
                                                <DeleteOutlined />
                                            </button>
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </div>
            ) : (
                <p className="validacion__vacio">
                    Sin campos configurados &mdash; el sistema usar&aacute; los valores por defecto del tipo de flujo.
                </p>
            )}

            <div className="validacion__agregar">
                <Select
                    style={{ width: 220 }}
                    size="small"
                    placeholder="Elegir campo..."
                    showSearch
                    value={null}
                    onChange={agregar}
                    options={disponibles.map((c) => ({ value: c, label: c }))}
                    notFoundContent="Sin campos disponibles"
                />
                <span className="validacion__agregar-o">o</span>
                <Select
                    style={{ width: 200 }}
                    size="small"
                    mode="tags"
                    placeholder="Escribir nombre libre"
                    value={[]}
                    onChange={(vals) => { if (vals.length) agregar(vals[vals.length - 1]) }}
                    maxCount={1}
                    open={false}
                    suffixIcon={null}
                    tokenSeparators={[',']}
                />
            </div>
        </div>
    )
}

export default SeccionValidacion
