import { InputNumber, Select, Space } from 'antd'

export const FILTROS_VACIOS = {
    tableName: null,
    action: null,
    changedBy: null,
    recordId: null,
}

/**
 * Filtros del historial de cambios.
 *
 * `recordId` va al servidor; los otros tres filtran en memoria sobre lo ya
 * cargado. Por eso sus opciones se reciben ya derivadas de los datos: así
 * solo aparecen tablas, acciones y usuarios que existen de verdad en el
 * historial, y la lista no se vacía al aplicar un filtro.
 */
const FiltrosAuditoria = ({ valor, onChange, tablas = [], acciones = [], usuarios = [] }) => {
    const cambiar = (campo) => (nuevo) => onChange({ ...valor, [campo]: nuevo ?? null })

    return (
        <Space className="auditoria-filtros" wrap size={12}>
            <Select
                className="auditoria-filtros__select"
                placeholder="Tabla: todas"
                value={valor.tableName}
                onChange={cambiar('tableName')}
                options={tablas}
                allowClear
            />

            <Select
                className="auditoria-filtros__select"
                placeholder="Acción: todas"
                value={valor.action}
                onChange={cambiar('action')}
                options={acciones}
                allowClear
            />

            <Select
                className="auditoria-filtros__select"
                placeholder="Usuario: todos"
                value={valor.changedBy}
                onChange={cambiar('changedBy')}
                options={usuarios}
                allowClear
                showSearch
                optionFilterProp="label"
            />

            <div>
                <InputNumber
                    className="auditoria-filtros__registro"
                    placeholder="ID de registro..."
                    value={valor.recordId}
                    onChange={cambiar('recordId')}
                    min={1}
                    precision={0}
                />
                <p className="auditoria-filtros__ayuda">Filtrar por ID del registro modificado</p>
            </div>
        </Space>
    )
}

export default FiltrosAuditoria
