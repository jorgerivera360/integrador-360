import { Input, InputNumber, Select, Switch } from 'antd'

const OPCIONES_FLOW_TYPE = [
    { value: 'items', label: 'Productos (items)' },
    { value: 'customer', label: 'Clientes (customer)' },
    { value: 'supplier', label: 'Proveedores (supplier)' },
    { value: 'purchases', label: 'Compras (purchases)' },
    { value: 'sales', label: 'Ventas (sales)' },
]

const SeccionBase = ({ datos, onChange, esEdicion }) => {
    const cambiar = (campo) => (valor) => {
        onChange({ ...datos, [campo]: valor })
    }

    const cambiarInput = (campo) => (e) => {
        onChange({ ...datos, [campo]: e.target.value })
    }

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">Informacion del flujo</h3>

            <div className="flujo-campos">
                <div className="flujo-campo">
                    <label className="flujo-campo__label">Nombre del flujo</label>
                    <Input
                        value={datos.flow_name || ''}
                        onChange={cambiarInput('flow_name')}
                        placeholder="ej: compras, items, facturas"
                    />
                </div>

                <div className="flujo-campo">
                    <label className="flujo-campo__label">Tipo de flujo</label>
                    <Select
                        value={datos.flow_type || undefined}
                        onChange={cambiar('flow_type')}
                        options={OPCIONES_FLOW_TYPE}
                        placeholder="Seleccionar tipo"
                        disabled={esEdicion}
                        style={{ width: '100%' }}
                    />
                </div>

                <div className="flujo-campo">
                    <label className="flujo-campo__label">Cron (schedule)</label>
                    <Input
                        className="flujo-input-mono"
                        value={datos.schedule_cron || ''}
                        onChange={cambiarInput('schedule_cron')}
                        placeholder="ej: */2 * * * *"
                    />
                </div>

                <div className="flujo-campo">
                    <label className="flujo-campo__label">Orden de ejecucion</label>
                    <InputNumber
                        value={datos.execution_order}
                        onChange={cambiar('execution_order')}
                        min={1}
                        max={999}
                        style={{ width: '100%' }}
                    />
                </div>

                <div className="flujo-campo flujo-campo--switch">
                    <label className="flujo-campo__label">Activo</label>
                    <Switch
                        checked={datos.is_active}
                        onChange={cambiar('is_active')}
                    />
                </div>
            </div>
        </div>
    )
}

export default SeccionBase
