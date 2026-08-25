import { Input, Select, Space } from 'antd'
import { OPCIONES_ERP } from '@/config/erp'
import { IconLupa } from '../icons'

export const FILTROS_VACIOS = {
    search: '',
    erpType: null,
    isActive: null,
}

/**
 * Filtros del listado de clientes.
 *
 * A diferencia del tablero, estos van al servidor: GET /clients/ acepta
 * search, erp_type e is_active. Por eso el estado y el debounce del
 * buscador los maneja la página, no este componente.
 */
const FiltrosClientes = ({ valor, onChange }) => {
    const cambiar = (campo) => (nuevo) => onChange({ ...valor, [campo]: nuevo ?? null })

    return (
        <Space className="clientes-filtros" wrap size={12}>
            <Input
                className="clientes-filtros__buscador"
                placeholder="Buscar por nombre o ID..."
                prefix={<IconLupa style={{ color: 'rgba(0,0,0,.3)' }} />}
                value={valor.search}
                onChange={(evento) => onChange({ ...valor, search: evento.target.value })}
                allowClear
            />

            <Select
                className="clientes-filtros__select"
                placeholder="ERP: todos"
                value={valor.erpType}
                onChange={cambiar('erpType')}
                options={OPCIONES_ERP}
                allowClear
            />

            <Select
                className="clientes-filtros__select clientes-filtros__select--corto"
                placeholder="Estado: todos"
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
