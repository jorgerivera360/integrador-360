import { Select, Space } from 'antd'
import useHasRole from '@/hooks/useHasRole'
import { useUsuarios } from '@/hooks/useUsuarios'

export const FILTROS_VACIOS = {
    tableName: null,
    action: null,
    changedBy: null,
}

const OPCIONES_MODULO = [
    { value: 'flows', label: 'Flujos' },
    { value: 'clients', label: 'Clientes' },
    { value: 'users', label: 'Usuarios' },
]

const OPCIONES_ACCION = [
    { value: 'create', label: 'Creación' },
    { value: 'update', label: 'Actualización' },
    { value: 'delete', label: 'Eliminación' },
]

const SelectUsuario = ({ value, onChange }) => {
    const { data: usuarios } = useUsuarios()

    const opciones = (usuarios || []).map((u) => ({
        value: u.id,
        label: u.name,
    }))

    return (
        <Select
            className="auditoria-filtros__select"
            placeholder="Usuario: todos"
            value={value}
            onChange={onChange}
            options={opciones}
            allowClear
            showSearch
            optionFilterProp="label"
        />
    )
}

const FiltrosAuditoria = ({ valor, onChange }) => {
    const cambiar = (campo) => (nuevo) => onChange({ ...valor, [campo]: nuevo ?? null })
    const esSuperadmin = useHasRole(['superadmin'])

    return (
        <Space className="auditoria-filtros" wrap size={12}>
            <Select
                className="auditoria-filtros__select"
                placeholder="Módulo: todos"
                value={valor.tableName}
                onChange={cambiar('tableName')}
                options={OPCIONES_MODULO}
                allowClear
            />

            <Select
                className="auditoria-filtros__select"
                placeholder="Acción: todas"
                value={valor.action}
                onChange={cambiar('action')}
                options={OPCIONES_ACCION}
                allowClear
            />

            {esSuperadmin && (
                <SelectUsuario
                    value={valor.changedBy}
                    onChange={cambiar('changedBy')}
                />
            )}
        </Space>
    )
}

export default FiltrosAuditoria
