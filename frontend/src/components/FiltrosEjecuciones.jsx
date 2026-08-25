import { Button, DatePicker, Input, Space } from 'antd'
import './filtros-ejecuciones.css'

const { RangePicker } = DatePicker

export const FILTROS_VACIOS = {
    cliente: '',
    flujo: '',
    estado: '',
    rango: null,
}

/** ¿Hay al menos un filtro puesto? */
export function hayFiltros(filtros) {
    return Boolean(
        filtros.cliente?.trim() ||
        filtros.flujo?.trim() ||
        filtros.estado?.trim() ||
        filtros.rango
    )
}

/**
 * Barra de filtros para listados de ejecuciones.
 *
 * Cliente, flujo y estado son búsqueda libre por texto: filtran a medida
 * que se escribe, sin listas de opciones que mantener sincronizadas con
 * el backend. El estado se busca por su texto visible ('parcial'), no por
 * el valor interno.
 *
 * Componente controlado: no guarda estado, lo recibe y lo notifica.
 */
const FiltrosEjecuciones = ({ valor, onChange }) => {
    const escribir = (campo) => (evento) =>
        onChange({ ...valor, [campo]: evento.target.value })

    const cambiarRango = (rango) => onChange({ ...valor, rango: rango ?? null })

    return (
        <Space className="filtros-ejecuciones" wrap size={8}>
            <Input
                className="filtros-ejecuciones__campo"
                placeholder="Cliente"
                value={valor.cliente}
                onChange={escribir('cliente')}
                allowClear
            />

            <Input
                className="filtros-ejecuciones__campo"
                placeholder="Flujo"
                value={valor.flujo}
                onChange={escribir('flujo')}
                allowClear
            />

            <Input
                className="filtros-ejecuciones__campo filtros-ejecuciones__campo--corto"
                placeholder="Estado"
                value={valor.estado}
                onChange={escribir('estado')}
                allowClear
            />

            <RangePicker
                value={valor.rango}
                onChange={cambiarRango}
                format="YYYY-MM-DD"
                placeholder={['Desde', 'Hasta']}
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
