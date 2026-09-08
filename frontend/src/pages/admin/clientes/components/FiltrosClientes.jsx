import { Select, Space } from 'antd'
import { OPCIONES_ERP } from '@/config/erp'

export const FILTROS_VACIOS = {
    search: [],
    erpType: [],
    isActive: [],
}

/**
 * Filtros del listado de clientes.
 *
 * A diferencia del tablero, estos van al servidor: GET /clients/ acepta
 * search, erp_type e is_active. Por eso el estado y el debounce del
 * buscador los maneja la página, no este componente.
 */
const FiltrosClientes = ({ valor, onChange, opcionesCliente = [] }) => {
    const cambiar = (campo) => (nuevo) => onChange({ ...valor, [campo]: nuevo ?? [] })

    return (
        <Space className="clientes-filtros" wrap size={12}>
            <Select
                className="clientes-filtros__buscador"
                placeholder="Cliente: todos"
                mode="multiple"
                showSearch
                optionFilterProp="label"
                value={valor.search}
                onChange={cambiar('search')}
                options={opcionesCliente}
                allowClear
            />

            <Select
                className="clientes-filtros__select"
                placeholder="ERP: todos"
                mode="multiple"
                showSearch
                optionFilterProp="label"
                value={valor.erpType}
                onChange={cambiar('erpType')}
                options={OPCIONES_ERP}
                allowClear
            />

            <Select
                className="clientes-filtros__select clientes-filtros__select--corto"
                placeholder="Estado: todos"
                mode="multiple"
                showSearch
                optionFilterProp="label"
                value={valor.isActive}
                onChange={cambiar('isActive')}
                options={[
                    { value: true, label: 'Activo' },
                    { value: false, label: 'Inactivo' },
                ]}
                allowClear
            />
        </Space>
    )
}

export default FiltrosClientes
