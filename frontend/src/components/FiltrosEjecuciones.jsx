import { useMemo } from 'react'
import { Button, DatePicker, Select, Space } from 'antd'
import './filtros-ejecuciones.css'

const { RangePicker } = DatePicker

export const FILTROS_VACIOS = {
    cliente: [],
    flujo: [],
    estado: [],
    rango: null,
}

/** ¿Hay al menos un filtro puesto? */
export function hayFiltros(filtros) {
    return Boolean(
        filtros.cliente?.length ||
        filtros.flujo?.length ||
        filtros.estado?.length ||
        filtros.rango
    )
}

const OPCIONES_ESTADO = [
    { value: 'success', label: 'Exitosa' },
    { value: 'partial', label: 'Parcial' },
    { value: 'error', label: 'Error' },
    { value: 'running', label: 'En curso' },
]

/**
 * Barra de filtros para listados de ejecuciones.
 * Recibe `ejecuciones` para extraer las opciones únicas de clientes y flujos.
 */
const FiltrosEjecuciones = ({ valor, onChange, ejecuciones = [], mostrarFecha = true }) => {
    const cambiar = (campo) => (nuevo) => onChange({ ...valor, [campo]: nuevo ?? [] })
    const cambiarRango = (rango) => onChange({ ...valor, rango: rango ?? null })

    const opcionesCliente = useMemo(() => {
        const unicos = [...new Set(ejecuciones.map((e) => e.client_name || e.client_slug).filter(Boolean))]
        return unicos.sort((a, b) => a.localeCompare(b, 'es')).map((c) => ({ value: c, label: c }))
    }, [ejecuciones])

    const opcionesFlujo = useMemo(() => {
        const unicos = [...new Set(ejecuciones.map((e) => e.flow_name).filter(Boolean))]
        return unicos.sort((a, b) => a.localeCompare(b, 'es')).map((f) => ({ value: f, label: f }))
    }, [ejecuciones])

    return (
        <Space className="filtros-ejecuciones" wrap size={8}>
            {mostrarFecha && (
                <RangePicker
                    value={valor.rango}
                    onChange={cambiarRango}
                    format="YYYY-MM-DD"
                    placeholder={['Desde', 'Hasta']}
                    allowClear
                />
            )}

            <Select
                className="filtros-ejecuciones__campo"
                placeholder="Cliente"
                mode="multiple"
                showSearch
                optionFilterProp="label"
                value={valor.cliente}
                onChange={cambiar('cliente')}
                options={opcionesCliente}
                allowClear
            />

            <Select
                className="filtros-ejecuciones__campo"
                placeholder="Flujo"
                mode="multiple"
                showSearch
                optionFilterProp="label"
                value={valor.flujo}
                onChange={cambiar('flujo')}
                options={opcionesFlujo}
                allowClear
            />

            <Select
                className="filtros-ejecuciones__campo filtros-ejecuciones__campo--corto"
                placeholder="Estado"
                mode="multiple"
                showSearch
                optionFilterProp="label"
                value={valor.estado}
                onChange={cambiar('estado')}
                options={OPCIONES_ESTADO}
                allowClear
            />

            {hayFiltros(valor) && (
                <Button type="link" size="small" onClick={() => onChange(FILTROS_VACIOS)}>
                    Limpiar
                </Button>
            )}
        </Space>
    )
}

export default FiltrosEjecuciones
